#!/usr/bin/env python3
"""Verify VM: a throwaway Ubuntu 24.04 VM that runs the handbook's shell commands and all lab rooms,
writes a pass/fail checklist, and deletes its disks (labs/vm/README.md, DOCKER.md "Verify VM").

    python3 labs/vm/vmctl.py check                       prerequisites: docker, /dev/kvm, free space, KVM in QEMU
    python3 labs/vm/vmctl.py prepare                     download + verify the cloud image, build the prepared image
    python3 labs/vm/vmctl.py verify                      commands pass + rooms pass, then the report
    python3 labs/vm/vmctl.py verify --commands --modules 27,41
    python3 labs/vm/vmctl.py verify --rooms 13,19
    python3 labs/vm/vmctl.py report [--run STAMP]        rewrite the report from a run's saved raw results
    python3 labs/vm/vmctl.py clean [--runs]              remove the volume and the image (and local run logs)

Nothing the handbook says to run ever runs on this machine. On the host this script only uses the docker
CLI (for its own objects, selected by name and label), reads files, and parses statements with `bash -n`.
QEMU runs inside the container devops-handbook-vm (--device /dev/kvm, all capabilities dropped, no
published ports, no network at all during `verify`); the guest's SSH is forwarded to 127.0.0.1 inside that
container only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import getpass
import hashlib
import importlib.util
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

VMDIR = Path(__file__).resolve().parent
ROOT = VMDIR.parent.parent
RUNS = VMDIR / "runs"                          # local run logs (git-ignored)
REPORTS = ROOT / "reports" / "verify"
sys.path.insert(0, str(VMDIR))
import verifylib as V  # noqa: E402

IMAGE = "devops-handbook-vm:local"
CONTAINER = "devops-handbook-vm"
VOLUME = "devops-handbook-vm"
LABEL_K, LABEL_V = "devops-handbook.vm", "1"
CLOUD_URL = "https://cloud-images.ubuntu.com/releases/noble/release/"
IMG_NAME = "ubuntu-24.04-server-cloudimg-amd64.img"
KEYRING = "/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"
BASE_IMG = f"/vm/cache/{IMG_NAME}"
PREPARED = "/vm/prepared/prepared.qcow2"
PREP_META = "/vm/prepared/prepared.json"
KEY = "/vm/keys/id_ed25519"
PREP_FORMAT = 1
MIN_FREE = 15e9                                # refuse to start below this
ABORT_FREE = 8e9                               # stop a run if free space falls below this
OVERLAY_MAX = 6.5e9                            # a run overlay larger than this is stopped (disk-filling statement)
DISK_SIZE = "10G"
MEM_MB, CPUS = 2048, 2
SSH_PORT = 2222
STMT_TIMEOUT = 20
STALL_S = 75                                   # no record from the guest for this long: the VM is gone
BOOT_TIMEOUT = 240
EXTERNAL_HINT = "not in Ubuntu's archive / another platform"

USER_DATA = """#cloud-config
hostname: lab
manage_etc_hosts: true
users:
  - name: lab
    uid: 1000
    shell: /bin/bash
    groups: [sudo, adm, systemd-journal]
    sudo: "ALL=(ALL:ALL) NOPASSWD: ALL"
    lock_passwd: true
    ssh_authorized_keys: [{key}]
ssh_pwauth: false
disable_root: true
package_update: false
package_upgrade: false
growpart: {{mode: auto, devices: ["/"]}}
"""
META_DATA = "instance-id: devops-handbook-vm-prepare\nlocal-hostname: lab\n"

# commands pass, once per module VM before the runner starts: the services most modules talk to, and an
# nft table that refuses outbound connections at once (the VM is offline: QEMU's restrict=on drops them,
# which would make every curl/ssh/dig wait for its own timeout)
COMMANDS_PRELUDE = r"""
for u in containerd docker cron nginx postgresql; do systemctl start "$u" >/dev/null 2>&1 || true; done
nft -f - <<'NFT'
table inet vfy_offline {
  chain out {
    type filter hook output priority 0; policy accept;
    ct state established,related accept
    tcp sport 22 accept
    oif "lo" accept
    ip daddr { 127.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 10.0.2.15 } accept
    ip6 daddr { ::1, fe80::/10, fd00::/8 } accept
    meta l4proto tcp reject with tcp reset
    reject with icmpx admin-prohibited
  }
}
NFT
install -d -m 700 /root/vfy /root/work
"""

_state = {"container": False, "vms": [], "runs": []}
_peak = {"free_min": None, "vol_max": 0}


class Abort(Exception):
    pass


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# --------------------------------------------------------------------------- docker helpers (our objects only)
def run(args, input=None, timeout=None, check=False):
    p = subprocess.run(args, input=input, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise Abort(f"{' '.join(args[:4])}... failed: {(p.stderr or p.stdout).strip()[-500:]}")
    return p


def dx(cmd: str, input=None, timeout=600, check=False):
    """A shell command inside the runner container (never on the host)."""
    return run(["docker", "exec", "-i", CONTAINER, "bash", "-c", cmd], input=input, timeout=timeout, check=check)


def free_bytes() -> float:
    root = run(["docker", "info", "-f", "{{.DockerRootDir}}"], check=True).stdout.strip() or "/var/lib/docker"
    for path in (root, os.path.dirname(root), "/"):
        try:
            s = os.statvfs(path)
            free = s.f_bavail * s.f_frsize
            if _peak["free_min"] is None or free < _peak["free_min"]:
                _peak["free_min"] = free
            return free
        except OSError:
            continue
    raise Abort("cannot read the free space of Docker's data root")


def volume_bytes() -> int:
    p = dx("du -s -B1 /vm 2>/dev/null | cut -f1", timeout=120)             # allocated bytes
    try:
        n = int(p.stdout.strip())
    except ValueError:
        return 0
    _peak["vol_max"] = max(_peak["vol_max"], n)
    return n


def ensure_image(rebuild=False):
    have = run(["docker", "image", "inspect", "-f", "{{index .Config.Labels \"devops-handbook.project\"}}", IMAGE])
    if have.returncode == 0 and have.stdout.strip() == "vm" and not rebuild:
        p = run(["docker", "build", "-q", "-t", IMAGE, str(VMDIR)], timeout=1800)   # cached: a no-op unless it changed
    else:
        log(f"building {IMAGE}")
        p = run(["docker", "build", "-t", IMAGE, str(VMDIR)], timeout=1800)
    if p.returncode != 0:
        raise Abort("docker build failed:\n" + p.stderr[-2000:])


def ensure_volume():
    p = run(["docker", "volume", "inspect", "-f", "{{index .Labels \"devops-handbook.vm\"}}", VOLUME])
    if p.returncode == 0:
        if p.stdout.strip() != LABEL_V:
            raise Abort(f"volume {VOLUME} exists but is not ours (no {LABEL_K}={LABEL_V} label): not touching it")
        return
    run(["docker", "volume", "create", "--label", f"{LABEL_K}={LABEL_V}", VOLUME], check=True)


def container_exists():
    p = run(["docker", "ps", "-aq", "--filter", f"name=^/{CONTAINER}$", "--filter", f"label={LABEL_K}={LABEL_V}"])
    return p.stdout.strip()


def container_args(network: bool):
    """`docker run` for the runner. Only `prepare` gets a network (the default bridge, outbound, for the cloud
    image and the Ubuntu archive); during `verify` the container has none, so the guest stays offline even if
    QEMU's restrict=on were bypassed. The guest's SSH forward is on the container's loopback either way."""
    return ["docker", "run", "-d", "--name", CONTAINER, "--label", f"{LABEL_K}={LABEL_V}",
            "--device", "/dev/kvm", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
            "--read-only", "--tmpfs", "/tmp:rw,size=64m", "--init", "--memory", "3g", "--pids-limit", "512",
            *([] if network else ["--network", "none"]),
            "-e", "HOME=/tmp", "-v", f"{VOLUME}:/vm", IMAGE, "sleep", "infinity"]


def start_container(network: bool = False):
    if container_exists():
        log(f"removing a leftover {CONTAINER} container (an earlier run was killed)")
        run(["docker", "rm", "-f", CONTAINER])
    ensure_volume()
    run(container_args(network), check=True)
    _state["container"] = True
    dx("mkdir -p /vm/cache /vm/keys /vm/prepared /vm/runs && chmod 700 /vm/keys", check=True)


def stop_container():
    for run_dir in list(_state["runs"]):
        dx(f"rm -rf {shlex.quote(run_dir)}", timeout=120)
        _state["runs"].remove(run_dir)
    if container_exists():
        run(["docker", "rm", "-f", CONTAINER], timeout=120)
    _state["container"] = False


# --------------------------------------------------------------------------- base image
def verify_base(download: bool) -> str:
    """Check SHA256SUMS.gpg with the Ubuntu cloud-image keyring, then the image's sha256. Returns the sha."""
    q = shlex.quote
    if download:
        log("fetching SHA256SUMS and SHA256SUMS.gpg from cloud-images.ubuntu.com")
        dx(f"cd /vm/cache && curl -fsSL --retry 3 -o SHA256SUMS.new {q(CLOUD_URL + 'SHA256SUMS')} "
           f"&& curl -fsSL --retry 3 -o SHA256SUMS.gpg.new {q(CLOUD_URL + 'SHA256SUMS.gpg')}", check=True, timeout=300)
        p = dx(f"cd /vm/cache && gpgv --keyring {KEYRING} SHA256SUMS.gpg.new SHA256SUMS.new 2>&1", timeout=60)
        if p.returncode != 0:
            raise Abort("SHA256SUMS signature does NOT verify against the Ubuntu cloud-image keyring:\n" + p.stdout)
        dx("cd /vm/cache && mv SHA256SUMS.new SHA256SUMS && mv SHA256SUMS.gpg.new SHA256SUMS.gpg", check=True)
    p = dx(f"cd /vm/cache && gpgv --keyring {KEYRING} SHA256SUMS.gpg SHA256SUMS 2>&1", timeout=60)
    if p.returncode != 0:
        raise Abort("cached SHA256SUMS does not verify (run prepare): " + p.stdout[-300:])
    want = dx(f"cd /vm/cache && awk '$2==\"*{IMG_NAME}\"||$2==\"{IMG_NAME}\"{{print $1}}' SHA256SUMS").stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{64}", want):
        raise Abort(f"{IMG_NAME} is not listed in SHA256SUMS")
    have = dx(f"test -f {BASE_IMG} && sha256sum {BASE_IMG} | cut -d' ' -f1", timeout=300).stdout.strip()
    if have != want:
        if not download:
            raise Abort("the cached cloud image does not match the signed SHA256SUMS (run prepare)")
        log(f"downloading {IMG_NAME} (~600 MB) into the volume")
        dx(f"cd /vm/cache && rm -f {IMG_NAME}.part && curl -fL --retry 3 -s -o {IMG_NAME}.part {q(CLOUD_URL + IMG_NAME)}",
           check=True, timeout=3600)
        have = dx(f"sha256sum /vm/cache/{IMG_NAME}.part | cut -d' ' -f1", timeout=300).stdout.strip()
        if have != want:
            dx(f"rm -f /vm/cache/{IMG_NAME}.part")
            raise Abort(f"downloaded image sha256 {have} != signed {want}: deleted, not used")
        dx(f"mv /vm/cache/{IMG_NAME}.part {BASE_IMG}", check=True)
    log(f"cloud image verified: SHA256SUMS signed by Ubuntu, {IMG_NAME} sha256 {want[:16]}...")
    return want


# --------------------------------------------------------------------------- the VM
def ssh_cmd(boot_id: str, extra: str = "") -> str:
    return (f"ssh -i {KEY} -p {SSH_PORT} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            f"-o LogLevel=ERROR -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 "
            f"-o ServerAliveCountMax=4 -o ControlMaster=auto -o ControlPath=/tmp/cm-{boot_id} -o ControlPersist=900 "
            f"{extra} lab@127.0.0.1")


class VM:
    """One QEMU process inside the runner container, on its own qcow2 overlay."""

    def __init__(self, run_dir: str, name: str, backing: str, restrict: bool = True, seed: str | None = None,
                 cache: str = "unsafe"):
        self.dir, self.name = run_dir, name
        self.overlay = f"{run_dir}/{name}.qcow2"
        self.pidfile = f"{run_dir}/{name}.pid"
        self.serial = f"{run_dir}/{name}.serial.log"
        self.results = f"{run_dir}/{name}.results.jsonl"
        self.boot_id = f"{name}-{os.getpid()}-{int(time.time())}"
        self.backing, self.restrict, self.seed, self.cache = backing, restrict, seed, cache

    def start(self):
        q = shlex.quote
        dx(f"mkdir -p {q(self.dir)} && rm -f {q(self.overlay)} {q(self.results)} && "
           f"qemu-img create -q -f qcow2 -F qcow2 -b {q(self.backing)} {q(self.overlay)} {DISK_SIZE} && "
           f": > {q(self.results)}", check=True)
        p = dx(" ".join(q(a) for a in self.qemu_args()), timeout=60)
        if p.returncode != 0:
            raise Abort(f"QEMU did not start: {(p.stderr or p.stdout).strip()[-800:]}")
        _state["vms"].append(self)

    def qemu_args(self):
        net = f"user,id=n0,hostfwd=tcp:127.0.0.1:{SSH_PORT}-:22" + (",restrict=on" if self.restrict else "")
        args = ["qemu-system-x86_64", "-name", self.name, "-machine", "q35,accel=kvm", "-cpu", "host",
                "-smp", str(CPUS), "-m", str(MEM_MB), "-nodefaults", "-display", "none", "-vga", "none",
                "-drive", f"file={self.overlay},if=virtio,format=qcow2,discard=unmap,cache={self.cache}",
                "-netdev", net, "-device", "virtio-net-pci,netdev=n0,romfile=",
                "-device", "virtio-rng-pci",
                "-device", "virtio-serial-pci",
                "-chardev", f"file,id=vfyres,path={self.results}",
                "-device", "virtserialport,chardev=vfyres,name=vfy.results",
                "-serial", f"file:{self.serial}", "-daemonize", "-pidfile", self.pidfile]
        if self.seed:
            args += ["-drive", f"file={self.seed},if=virtio,format=raw,readonly=on"]
        return args

    def alive(self) -> bool:
        return dx(f"kill -0 $(cat {self.pidfile} 2>/dev/null) 2>/dev/null").returncode == 0

    def ssh(self, remote: str, input=None, timeout=300):
        return dx(f"{ssh_cmd(self.boot_id)} {shlex.quote(remote)}", input=input, timeout=timeout)

    def wait_ssh(self, timeout=BOOT_TIMEOUT):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self.alive():
                raise Abort(f"{self.name}: QEMU exited during boot; serial log tail:\n{self.serial_tail()}")
            try:
                if self.ssh("true", timeout=30).returncode == 0:
                    return
            except subprocess.TimeoutExpired:
                pass
            time.sleep(3)
        raise Abort(f"{self.name}: no SSH after {timeout}s; serial log tail:\n{self.serial_tail()}")

    def serial_tail(self, n=25) -> str:
        return dx(f"tail -n {n} {shlex.quote(self.serial)} 2>/dev/null | tr -d '\\r'").stdout

    def size(self) -> int:
        try:
            return int(dx(f"du -B1 {shlex.quote(self.overlay)} | cut -f1").stdout.strip() or 0)   # allocated bytes
        except ValueError:
            return 0

    def stop(self, delete=True):
        dx(f"p=$(cat {self.pidfile} 2>/dev/null); [ -n \"$p\" ] && kill $p 2>/dev/null; "
           f"for i in $(seq 50); do kill -0 $p 2>/dev/null || break; sleep 0.2; done; "
           f"kill -9 $p 2>/dev/null; ssh -O exit -o ControlPath=/tmp/cm-{self.boot_id} x 2>/dev/null; "
           f"rm -f /tmp/cm-{self.boot_id}", timeout=60)
        if delete:
            dx(f"rm -f {shlex.quote(self.overlay)}", timeout=60)
        if self in _state["vms"]:
            _state["vms"].remove(self)

    def copy_logs(self, host_dir: Path, results=True):
        host_dir.mkdir(parents=True, exist_ok=True)
        names = [self.serial] + ([self.results] if results else [])
        for path in names:
            p = run(["docker", "exec", CONTAINER, "cat", path], timeout=120)
            if p.returncode == 0:
                (host_dir / Path(path).name).write_text(scrub(p.stdout.replace("\r", "")))


# --------------------------------------------------------------------------- keys, hash, prepare
def provision_text() -> str:
    pkgs = V.base_packages((ROOT / "labs" / "base" / "Dockerfile").read_text())
    if not pkgs:
        raise Abort("no package list found in labs/base/Dockerfile")
    return f'BASE_PACKAGES={shlex.quote(" ".join(pkgs))}\n' + (VMDIR / "provision.sh").read_text()


def prep_hash(base_sha: str) -> str:
    h = hashlib.sha256()
    for part in (str(PREP_FORMAT), provision_text(), USER_DATA, META_DATA, base_sha):
        h.update(part.encode())
        h.update(b"\0")
    return h.hexdigest()


def prepared_ok(base_sha: str) -> bool:
    p = dx(f"cat {PREP_META} 2>/dev/null && test -f {PREPARED}")
    if p.returncode != 0:
        return False
    try:
        meta = json.loads(p.stdout)
    except ValueError:
        return False
    return meta.get("hash") == prep_hash(base_sha)


def ensure_key():
    dx(f"test -f {KEY} || ssh-keygen -q -t ed25519 -N '' -C devops-handbook-vm -f {KEY}", check=True)
    return dx(f"cat {KEY}.pub", check=True).stdout.strip()


def prepare(force=False) -> str:
    base_sha = verify_base(download=True)
    if prepared_ok(base_sha) and not force:
        log("prepared image is up to date (provisioning hash matches)")
        return base_sha
    log("building the prepared image (boot the cloud image once, install packages, shut down)")
    dx(f"rm -f {PREPARED} {PREP_META} && rm -rf /vm/keys/* && ls /vm", check=True)
    pub = ensure_key()                       # a new keypair for every prepared image
    run_dir = "/vm/runs/prepare"
    _state["runs"].append(run_dir)
    dx(f"rm -rf {run_dir} && mkdir -p {run_dir}/seed", check=True)
    dx(f"cat > {run_dir}/seed/user-data", input=USER_DATA.format(key=json.dumps(pub)), check=True)
    dx(f"cat > {run_dir}/seed/meta-data", input=META_DATA, check=True)
    dx(f"cd {run_dir}/seed && genisoimage -quiet -output ../seed.iso -volid cidata -joliet -rock user-data meta-data",
       check=True)
    vm = VM(run_dir, "prepare", BASE_IMG, restrict=False, seed=f"{run_dir}/seed.iso", cache="writeback")
    host_log = RUNS / f"prepare-{time.strftime('%Y%m%d-%H%M%S')}"
    host_log.mkdir(parents=True, exist_ok=True)
    try:
        vm.start()
        vm.wait_ssh(timeout=420)
        log("guest is up; provisioning (apt inside the VM, several minutes)")
        p = vm.ssh("sudo bash -s", input=provision_text(), timeout=3600)
        (host_log / "provision.log").write_text(scrub(p.stdout + "\n--- stderr ---\n" + p.stderr))
        notes = [ln for ln in p.stdout.splitlines() if ln.startswith("VFY-NOTE")]
        for n in notes:
            log("  " + n)
        if p.returncode != 0 or "VFY-PROVISION-OK" not in p.stdout:
            raise Abort(f"provisioning failed (exit {p.returncode}); log: {rel(host_log / 'provision.log')}\n"
                        + p.stderr[-1500:])
        log("provisioned; shutting the VM down")
        vm.ssh("sudo systemctl poweroff", timeout=60)
        deadline = time.monotonic() + 180
        while vm.alive() and time.monotonic() < deadline:
            time.sleep(2)
        if vm.alive():
            raise Abort("the prepare VM did not power off")
        vm.copy_logs(host_log, results=False)
        vm.stop(delete=False)
        dx(f"mv {vm.overlay} {PREPARED} && qemu-img check -q {PREPARED}", check=True)
        meta = {"hash": prep_hash(base_sha), "base_sha256": base_sha, "created": dt.datetime.now().isoformat(),
                "notes": notes}
        dx(f"cat > {PREP_META}", input=json.dumps(meta, indent=1), check=True)
        size = dx(f"du -b {PREPARED} | cut -f1").stdout.strip()
        log(f"prepared image ready: {int(size) / 1e9:.2f} GB on top of the cloud image")
    finally:
        if vm in _state["vms"]:
            vm.copy_logs(host_log, results=False)
            vm.stop(delete=True)
        dx(f"rm -rf {run_dir}")
        if run_dir in _state["runs"]:
            _state["runs"].remove(run_dir)
    return base_sha


# --------------------------------------------------------------------------- statements
def module_files(filter_nums=None):
    files = sorted(p for p in ROOT.iterdir() if V.MODULE_RE.match(p.name) and p.name not in V.SKIP_MODULES)
    if filter_nums:
        files = [p for p in files if p.name[:2] in filter_nums]
    return files


def collect(filter_nums=None):
    """All statements of the selected modules: list of dicts (id, module, line, heading, block, text, skip)."""
    stmts, sid = [], 0
    for path in module_files(filter_nums):
        for b in V.iter_blocks(path.read_text(), path.name):
            output = V.is_output_block(b.lines)
            other = V.platform_reason(b.lines)
            for line, text in V.split_statements(b.lines, b.line):
                sid += 1
                reason = "sample output block" if output else other or V.skip_reason(text)
                stmts.append({"id": sid, "module": path.name, "line": line, "heading": b.heading,
                              "block": f"{path.name}#{b.index}", "text": text, "skip": reason})
    return stmts


def jobs_for(stmts):
    blocks, order = {}, []
    for s in stmts:
        if s["block"] not in blocks:
            blocks[s["block"]] = []
            order.append(s["block"])
        blocks[s["block"]].append({"id": s["id"], "text": s["text"]})
    return {"timeout": STMT_TIMEOUT, "limit": 4000,
            "blocks": [{"id": b, "statements": blocks[b]} for b in order]}


def commands_module(run_dir, module, todo, results, hints, host_dir, keep_going):
    """Run one module's statements in fresh VMs until all have a result (a VM that dies is replaced)."""
    remaining = list(todo)
    attempt = 0
    while remaining:
        attempt += 1
        if attempt > 6:
            for s in remaining:
                results[s["id"]] = {"cls": "BROKE_VM", "detail": "not run: the VM kept dying"}
            return
        vm = VM(run_dir, f"m{module[:2]}-{attempt}", PREPARED, restrict=True)
        try:
            vm.start()
            vm.wait_ssh()
            p = vm.ssh("sudo bash -s", input=COMMANDS_PRELUDE, timeout=300)
            if p.returncode != 0:
                raise Abort(f"prelude failed (exit {p.returncode}): {(p.stderr or p.stdout)[-400:]}")
            vm.ssh("sudo tee /root/vfy/guest_runner.py >/dev/null", input=(VMDIR / "guest_runner.py").read_text())
            vm.ssh("sudo tee /root/vfy/jobs.json >/dev/null", input=json.dumps(jobs_for(remaining)))
            # OOMPolicy=continue: when the kernel OOM-kills a statement's process (stress-ng --vm ...), systemd's
            # default policy (stop) would stop the whole unit, runner included
            p = vm.ssh("sudo systemd-run --quiet --unit vfy-runner --collect -p OOMScoreAdjust=-1000 "
                       "-p OOMPolicy=continue /usr/bin/python3 /root/vfy/guest_runner.py /root/vfy/jobs.json")
            if p.returncode != 0:
                raise Abort(f"could not start the guest runner: {p.stderr[-400:]}")
        except Abort as exc:
            log(f"  {module}: VM attempt {attempt} failed to start: {str(exc)[:300]}")
            vm.copy_logs(host_dir / module, results=False)
            vm.stop()
            if not keep_going and attempt >= 2:
                raise
            continue
        offset, buf, last, started, done = 0, "", time.monotonic(), None, False
        last_check = 0.0
        broke = None
        block_bg = []                 # (statement, names) of this block's statements that left processes running
        while True:
            time.sleep(2)
            p = dx(f"tail -c +{offset + 1} {shlex.quote(vm.results)}", timeout=60)
            chunk = p.stdout
            if chunk:
                offset += len(chunk.encode("utf-8"))
                buf += chunk
                last = time.monotonic()
            *lines, buf = buf.split("\n")
            for ln in lines:
                try:
                    rec = json.loads(ln)
                except ValueError:
                    continue
                t = rec.get("t")
                if t == "B":
                    block_bg = []
                elif t == "S":
                    started = rec["id"]
                elif t == "R":
                    results[rec["id"]] = rec
                    started = None
                    if rec.get("bg"):
                        block_bg.append((rec["id"], rec["bg"]))
                elif t == "HINT":
                    hints[rec["cmd"]] = rec.get("text", "")
                elif t == "DONE":
                    done = True
            if done:
                break
            now = time.monotonic()
            if now - last_check > 30:
                last_check = now
                if free_bytes() < ABORT_FREE:
                    vm.stop()
                    raise Abort(f"free space fell below {ABORT_FREE / 1e9:.0f} GB: stopped")
                volume_bytes()                                # peak disk use includes the live overlay
                if vm.size() > OVERLAY_MAX:
                    broke = "the VM's disk grew past the run limit"
                    break
                if not vm.alive():
                    broke = "the VM powered off or crashed"
                    break
            if now - last > STALL_S:
                try:
                    up = vm.ssh("systemctl is-active vfy-runner", timeout=30).stdout.strip()
                except subprocess.TimeoutExpired:
                    up = ""
                broke = (f"the guest runner died during this statement (the VM still answers; runner {up})"
                         if up in ("inactive", "failed") else f"no sign of life from the VM for {STALL_S}s")
                break
        if broke:
            sid = started
            log(f"  {module}: {broke}" + (f" (statement {sid})" if sid else ""))
            if sid is not None:
                detail = broke
                if block_bg:          # the statement may be a victim: name what an earlier one left running
                    bid, names = block_bg[-1]
                    src = next((s for s in todo if s["id"] == bid), None)
                    detail += (f"; still running in the background: {', '.join(names)}, started by line "
                               f"{(src or {}).get('line', '?')} `{((src or {}).get('text') or '?').splitlines()[0][:80]}`")
                results[sid] = {"cls": "BROKE_VM", "detail": detail, "rc": None, "out": "",
                                "err": vm.serial_tail(15)}
        vm.copy_logs(host_dir / module, results=True)
        vm.stop()
        remaining = [s for s in remaining if s["id"] not in results]
        if remaining and not broke:
            log(f"  {module}: runner ended with {len(remaining)} statements unrun; retrying in a fresh VM")


def classify_all(stmts, results, hints):
    funcs = {}
    for s in stmts:
        funcs.setdefault(s["module"], []).append(s["text"])
    funcs = {m: V.defined_functions(t) for m, t in funcs.items()}
    for s in stmts:
        if s["skip"]:
            s["cls"], s["detail"] = "SKIPPED", s["skip"]
            continue
        r = results.get(s["id"])
        if r is None:
            s["cls"], s["detail"] = "NOT_RUN", "no result"
            continue
        if r.get("cls") == "BROKE_VM":
            s.update(cls="BROKE_VM", detail=r.get("detail", ""), rc=None, out="", err=r.get("err", ""))
            continue
        v = V.classify(r.get("rc"), r.get("out", ""), r.get("err", ""), r.get("timeout", False), s["text"],
                       funcs.get(s["module"], frozenset()))
        s.update(cls=v.cls, detail=v.detail, rc=r.get("rc"), dur=r.get("dur"), out=r.get("out", ""),
                 err=r.get("err", ""), note=r.get("note", ""))
        if v.cls == "MISSING":
            s["hint"] = "; ".join(f"{c}: {hint_line(hints.get(c))}" for c in v.commands)
        if v.cls == "EXTERNAL":
            s["hint"] = EXTERNAL_HINT


def hint_line(text) -> str:
    if text is None:                 # the guest never asked command-not-found about this name
        return "no package hint recorded"
    text = " ".join(ln.strip() for ln in text.splitlines() if ln.strip())
    m = re.search(r"(?:can be installed with|is in the package|Command '[^']+' not found, (?:but|did you)).*", text)
    return (m.group(0) if m else text or "no package in Ubuntu's archive provides it")[:300]


# --------------------------------------------------------------------------- rooms
def load_test_rooms():
    spec = importlib.util.spec_from_file_location("test_rooms", ROOT / "labs" / "test_rooms.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rooms_pass(run_dir, filter_nums, host_dir, keep_going, out):
    """Every selected room on a fresh VM; appends one entry per room to `out`."""
    TR = load_test_rooms()
    dirs = sorted(d for d in (ROOT / "labs" / "rooms").iterdir() if (d / "room.json").is_file())
    if filter_nums:
        dirs = [d for d in dirs if d.name[:2] in filter_nums]
    for d in dirs:
        t0 = time.monotonic()
        entry = {"room": d.name, "result": "", "lines": [], "problems": []}
        try:
            room, answers, problems = TR.validate_room(d)
        except Exception as exc:  # noqa: BLE001
            entry.update(result="FAIL", problems=[f"cannot read room: {exc}"])
            out.append(entry)
            continue
        entry["problems"] = problems
        vm = VM(run_dir, f"r{d.name[:2]}", PREPARED, restrict=True)
        try:
            vm.start()
            vm.wait_ssh()
            st = vm.ssh("timeout 120 systemctl is-system-running --wait", timeout=180).stdout.strip()
            entry["lines"].append(f"  VM booted (systemd: {st or 'unknown'})")

            def run_script(path, _vm=vm):
                t1 = time.monotonic()
                try:
                    p = _vm.ssh("sudo bash -s", input=Path(path).read_text(), timeout=TR.SCRIPT_TIMEOUT_S)
                except subprocess.TimeoutExpired:
                    return 124, "", f"timeout after {TR.SCRIPT_TIMEOUT_S}s", time.monotonic() - t1
                return p.returncode, p.stdout, p.stderr, time.monotonic() - t1

            ok, lines = TR.run_room_steps(d, room, answers, run_script, setup_budget=TR.SETUP_BUDGET_S)
            entry["lines"] += lines
            if problems:
                entry["result"] = "FAIL"
            elif ok:
                entry["result"] = "PASS"
            elif all("took" in ln and "budget" in ln for ln in lines if ln.lstrip().startswith("FAIL")):
                entry["result"] = "PASS"
                entry["lines"].append("  note: only the setup.sh time budget was exceeded")
            else:
                entry["result"] = "DIFFERS"
        except Abort as exc:
            entry["result"] = "ERROR"
            entry["lines"].append(f"  FAIL infrastructure: {str(exc)[:600]}")
            if not keep_going:
                vm.copy_logs(host_dir / "rooms" / d.name, results=False)
                vm.stop()
                out.append(entry)
                raise
        finally:
            if vm in _state["vms"]:
                vm.copy_logs(host_dir / "rooms" / d.name, results=False)
                vm.stop()
        entry["seconds"] = round(time.monotonic() - t0, 1)
        log(f"  room {d.name}: {entry['result']} ({entry['seconds']:.0f}s)")
        out.append(entry)


# --------------------------------------------------------------------------- report
def scrub(text: str) -> str:
    """Never let the host's home path or user name into a report or a kept log."""
    if not text:
        return text
    home = str(Path.home())
    text = text.replace(home, "~")
    try:
        user = getpass.getuser()
    except Exception:  # noqa: BLE001
        user = ""
    if user and user not in ("root", "lab"):
        text = re.sub(rf"\b{re.escape(user)}\b", "user", text)
    return text


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return scrub(str(p))


CLASSES = ["PASS", "USAGE", "MISSING", "EXTERNAL", "CONTEXT", "TIMEOUT", "BROKE_VM", "NOT_RUN", "SKIPPED"]


def excerpt(text: str, n=6, width=200) -> str:
    rows = [ln[:width] for ln in (text or "").strip().splitlines() if ln.strip()]
    return "\n".join(rows[:n]) + ("\n…" if len(rows) > n else "")


def fence(text: str, lang="") -> str:
    ticks = "````" if "```" in text else "```"
    return f"{ticks}{lang}\n{text}\n{ticks}"


def write_report(meta, stmts, rooms, partial: bool):
    REPORTS.mkdir(parents=True, exist_ok=True)
    m = re.match(r"\d{4}-\d\d-\d\d", str(meta.get("Date", "")))
    day = m.group(0) if m else dt.date.today().isoformat()      # the run's day (`report` may run days later)
    stem = f"verify-{day}" + ("-partial" if partial else "")
    counts = {c: 0 for c in CLASSES}
    per_mod = {}
    for s in stmts:
        counts[s["cls"]] += 1
        m = per_mod.setdefault(s["module"], {c: 0 for c in CLASSES})
        m[s["cls"]] += 1
    rcount = {}
    for r in rooms:
        rcount[r["result"]] = rcount.get(r["result"], 0) + 1
    L = [f"# Verify VM report, {day}", "",
         "A throwaway Ubuntu 24.04 VM ran the handbook's shell commands and the hands-on lab rooms, then its disks "
         "were deleted. Generated by `python3 labs/vm/vmctl.py verify` (labs/vm/README.md).", "",
         "| | |", "|---|---|"]
    for k, v in meta.items():
        L.append(f"| {k} | {v} |")
    L += ["", "## Summary", ""]
    if stmts:
        ran = sum(counts[c] for c in CLASSES if c not in ("SKIPPED", "NOT_RUN"))
        L += [f"**Commands:** {len(stmts)} statements from {len(per_mod)} modules; {ran} ran in the VM.", "",
              "| " + " | ".join(CLASSES) + " |", "|" + "---|" * len(CLASSES),
              "| " + " | ".join(str(counts[c]) for c in CLASSES) + " |", ""]
    if rooms:
        L += [f"**Rooms:** {len(rooms)} rooms: " + ", ".join(f"{v} {k}" for k, v in sorted(rcount.items())), ""]
    L += ["What the classes mean: **PASS** exit 0. **USAGE** the tool rejected the command line (unknown option, "
          "usage text, bash syntax error): a candidate documentation error. **MISSING** command not found on Ubuntu "
          "24.04 with the VM's packages (hint from command-not-found). **EXTERNAL** a tool that is not part of "
          "Ubuntu (cloud/Kubernetes/IaC clients, other platforms). **CONTEXT** non-zero exit because a service, "
          "file, host, cluster or the network is not there: informational. **TIMEOUT** still running after "
          f"{STMT_TIMEOUT}s (often follow-mode commands such as `tail -f`). **BROKE_VM** the VM stopped answering "
          "during this statement; the run continued in a fresh VM. **SKIPPED** not run: a placeholder to fill in, "
          "a VM-killer on the denylist, or not shell (SQL/YAML typed into another program).", ""]
    if rooms:
        L += ["## Rooms checklist", "", "| | Room | Result | Notes |", "|---|---|---|---|"]
        for r in rooms:
            fails = [ln.strip()[5:] for ln in r["lines"] if ln.strip().startswith("FAIL")] + r["problems"]
            note = "; ".join(fails)[:400].replace("|", "/").replace("\n", " ")
            box = "x" if r["result"] == "PASS" else " "
            L.append(f"| [{box}] | `{r['room']}` | {r['result']} | {note} |")
        L += ["", "PASS: setup.sh twice, every check fails, solve.sh, every check passes, answer hashes match. "
              "DIFFERS: the room was written for the container lab and a step behaves differently on a real VM "
              "(the failing step is in Notes and in the details below). FAIL: room.json/answers problems.", ""]
    if stmts:
        L += ["## Modules checklist", "",
              "[x] = no USAGE, MISSING or BROKE_VM result.", "",
              "| | Module | " + " | ".join(CLASSES) + " |", "|---|---|" + "---|" * len(CLASSES)]
        for mod in sorted(per_mod):
            m = per_mod[mod]
            box = "x" if not (m["USAGE"] or m["MISSING"] or m["BROKE_VM"]) else " "
            L.append(f"| [{box}] | `{mod}` | " + " | ".join(str(m[c]) for c in CLASSES) + " |")
        L.append("")
        for cls, title in (("USAGE", "USAGE: candidate documentation errors"),
                           ("MISSING", "MISSING: commands Ubuntu 24.04 did not have"),
                           ("BROKE_VM", "BROKE_VM: statements the VM did not survive")):
            items = [s for s in stmts if s["cls"] == cls]
            L += [f"## {title} ({len(items)})", ""]
            if cls == "MISSING" and items:
                by = {}
                for s in items:
                    for c in (s.get("detail") or "").split(", "):
                        by.setdefault(c, []).append(s)
                L += ["| Command | Statements | Package hint |", "|---|---|---|"]
                for c, ss in sorted(by.items(), key=lambda kv: -len(kv[1])):
                    h = next((part[len(c) + 2:] for x in ss for part in (x.get("hint") or "").split("; ")
                              if part.startswith(f"{c}: ")), "")         # this command's hint, not the first one's
                    L.append(f"| `{c}` | {len(ss)} | {h.replace('|', '/')} |")
                L.append("")
            for s in items:
                L += [f"### `{s['module']}` line {s['line']}: {s['heading'] or '(no heading)'}", "",
                      fence(s["text"][:1500], "bash"), "",
                      f"exit {s.get('rc')}; {s.get('detail', '')}", ""]
                err = excerpt(s.get("err", "")) or excerpt(s.get("out", ""))
                if err:
                    L += [fence(err), ""]
                if s.get("hint"):
                    L += [f"Package hint: {s['hint']}", ""]
        ext = {}
        for s in stmts:
            if s["cls"] == "EXTERNAL":
                for c in (s.get("detail") or "").split(", "):
                    ext[c] = ext.get(c, 0) + 1
        L += [f"## EXTERNAL tools ({counts['EXTERNAL']} statements)", "",
              ", ".join(f"`{c}` {n}" for c, n in sorted(ext.items(), key=lambda kv: -kv[1])) or "none", ""]
        to = [s for s in stmts if s["cls"] == "TIMEOUT"]
        L += [f"## TIMEOUT ({len(to)})", "", "<details><summary>list</summary>", ""]
        L += [f"- `{s['module']}`:{s['line']} `{s['text'].splitlines()[0][:120]}`" for s in to]
        L += ["", "</details>", ""]
        sk = {}
        for s in stmts:
            if s["cls"] == "SKIPPED":
                key = re.sub(r"^(placeholder): .*", r"\1 (a stand-in to fill in)", s["detail"])
                sk[key] = sk.get(key, 0) + 1
        L += [f"## SKIPPED ({counts['SKIPPED']})", "", "| Reason | Statements |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in sorted(sk.items(), key=lambda kv: -kv[1])]
        L.append("")
    if rooms:
        L += ["## Room details", ""]
        for r in rooms:
            L += [f"### `{r['room']}`: {r['result']}", "", fence("\n".join(r["problems"] + r["lines"])[:6000]), ""]
    md = scrub("\n".join(L))
    (REPORTS / f"{stem}.md").write_text(md)
    slim = []                       # keep the JSON small: full excerpts only where a reader needs them
    for s in stmts:
        s = dict(s)
        if s["cls"] in ("PASS", "CONTEXT", "EXTERNAL", "SKIPPED"):
            for k in ("out", "err"):
                if len(s.get(k) or "") > 300:
                    s[k] = s[k][:300] + " [...]"
        slim.append(s)
    data = {"meta": meta, "counts": counts, "rooms": rooms, "statements": slim}
    (REPORTS / f"{stem}.json").write_text(scrub(json.dumps(data, indent=1, ensure_ascii=False)))
    return REPORTS / f"{stem}.md"


# --------------------------------------------------------------------------- commands
def parse_nums(val):
    if val in (None, True):
        return None
    return {f"{int(x):02d}" for x in str(val).split(",") if x.strip()}


def take_lock():
    RUNS.mkdir(parents=True, exist_ok=True)
    fh = open(RUNS / ".lock", "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise Abort("another vmctl.py is running (one VM at a time)")
    return fh


def check_space():
    free = free_bytes()
    if free < MIN_FREE:
        raise Abort(f"only {free / 1e9:.1f} GB free on Docker's data root; the verify VM needs {MIN_FREE / 1e9:.0f} GB")
    return free


def cmd_check(_args):
    ok = True
    p = run(["docker", "version", "-f", "{{.Server.Version}}"])
    print(f"docker engine: {p.stdout.strip() or 'NOT reachable'}")
    ok &= p.returncode == 0
    kvm = os.path.exists("/dev/kvm")
    print(f"/dev/kvm: {'present' if kvm else 'MISSING (enable virtualisation in the BIOS / load kvm_intel or kvm_amd)'}")
    ok &= kvm
    free = free_bytes()
    print(f"free on Docker's data root: {free / 1e9:.1f} GB (needs {MIN_FREE / 1e9:.0f} GB) "
          f"{'ok' if free >= MIN_FREE else 'TOO LOW'}")
    ok &= free >= MIN_FREE
    ensure_image()
    print(f"image {IMAGE}: ok")
    probe = ("python3 -c \"import os,fcntl; fd=os.open('/dev/kvm', os.O_RDWR); print('KVM API', fcntl.ioctl(fd, 0xAE00))\" && "
             "printf '{\"execute\":\"qmp_capabilities\"}\\n{\"execute\":\"query-kvm\"}\\n{\"execute\":\"quit\"}\\n' | "
             "timeout 30 qemu-system-x86_64 -accel kvm -M q35 -nodefaults -display none -m 64 -S -qmp stdio 2>&1 | "
             "grep -o '\"enabled\": true, \"present\": true'")
    p = run(["docker", "run", "--rm", "--label", f"{LABEL_K}={LABEL_V}", "--device", "/dev/kvm", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges:true", "--read-only", "--tmpfs", "/tmp", "--network", "none",
             IMAGE, "bash", "-c", probe], timeout=120)
    print("KVM inside the runner (no capabilities, no network): " + ("ok" if p.returncode == 0 else
          "FAILED\n" + (p.stdout + p.stderr)[-800:]))
    ok &= p.returncode == 0
    v = run(["docker", "volume", "inspect", VOLUME])
    print(f"volume {VOLUME}: {'exists' if v.returncode == 0 else 'not created yet (prepare creates it)'}")
    print("result: " + ("ready" if ok else "NOT ready"))
    return 0 if ok else 1


def cmd_prepare(args):
    check_space()
    ensure_image()
    start_container(network=True)            # the only networked step: cloud image + Ubuntu archive
    prepare(force=args.force)
    log(f"volume {VOLUME} now holds {volume_bytes() / 1e9:.2f} GB")
    return 0


def cmd_verify(args):
    t_start = time.time()
    check_space()
    want_cmds = args.commands is not None or args.modules is not None or args.rooms is None
    want_rooms = args.rooms is not None or (args.commands is None and args.modules is None)
    mod_filter = parse_nums(args.modules)
    room_filter = parse_nums(args.rooms)
    ensure_image()
    start_container(network=False)           # no network at all during verify (verify_base reads the cache only)
    base_sha = verify_base(download=False)
    if not prepared_ok(base_sha):
        raise Abort("the prepared image is missing or out of date: run `python3 labs/vm/vmctl.py prepare`")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = f"/vm/runs/{stamp}"
    _state["runs"].append(run_dir)
    host_dir = RUNS / stamp
    host_dir.mkdir(parents=True, exist_ok=True)
    vol0 = volume_bytes()
    stmts, rooms, results, hints = [], [], {}, {}
    failure = None
    try:
        if want_cmds:
            stmts = collect(mod_filter)
            by_mod = {}
            for s in stmts:
                if not s["skip"]:
                    by_mod.setdefault(s["module"], []).append(s)
            total = sum(len(v) for v in by_mod.values())
            log(f"commands pass: {len(stmts)} statements, {total} to run in {len(by_mod)} module VMs")
            for i, (mod, todo) in enumerate(sorted(by_mod.items()), 1):
                t0 = time.monotonic()
                commands_module(run_dir, mod, todo, results, hints, host_dir / "modules", args.keep_going)
                got = sum(1 for s in todo if s["id"] in results)
                log(f"[{i}/{len(by_mod)}] {mod}: {got}/{len(todo)} results in {time.monotonic() - t0:.0f}s")
                volume_bytes()
                (host_dir / "results.partial.json").write_text(scrub(json.dumps({"results": results, "hints": hints})))
        if want_rooms:
            log("rooms pass")
            rooms_pass(run_dir, room_filter, host_dir, args.keep_going, rooms)
    except (Abort, KeyboardInterrupt) as exc:
        failure = exc
        log(f"run stopped early ({exc}); writing a partial report")
    finally:
        try:
            volume_bytes()
        except Exception:  # noqa: BLE001
            pass
    classify_all(stmts, results, hints)
    image_size = run(["docker", "image", "inspect", "-f", "{{.Size}}", IMAGE]).stdout.strip() or "0"
    meta = {
        "Date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Duration": f"{(time.time() - t_start) / 60:.0f} min",
        "Guest": f"Ubuntu 24.04 cloud image `{IMG_NAME}` (sha256 {base_sha[:16]}…, signature checked), "
                 f"{CPUS} vCPU, {MEM_MB // 1024} GB RAM, KVM, {DISK_SIZE} qcow2 overlay per VM",
        "Network": "offline (the runner container has no network, `--network none`; QEMU user networking with "
                   "restrict=on; outbound connections refused at once by an nft table `vfy_offline` in the commands pass)",
        "Selection": ("modules " + ",".join(sorted(mod_filter)) if mod_filter else "all modules") if want_cmds
        else "no commands pass",
        "Rooms": ("rooms " + ",".join(sorted(room_filter)) if room_filter else "all rooms") if want_rooms else "none",
        "Statement limit": f"{STMT_TIMEOUT}s each, as root, stdin /dev/null, one bash session per block",
        "Disk": f"volume {vol0 / 1e9:.2f} GB at start, peak {_peak['vol_max'] / 1e9:.2f} GB; runner image "
                f"{int(image_size) / 1e9:.2f} GB; lowest free space on Docker's data root "
                f"{(_peak['free_min'] or 0) / 1e9:.1f} GB",
    }
    if failure is not None:
        meta["Status"] = f"INCOMPLETE: stopped early ({str(failure)[:200]})"
    partial = bool(mod_filter or room_filter or not (want_cmds and want_rooms) or failure is not None)
    raw = [{k: v for k, v in s.items() if k in ("id", "module", "line", "heading", "block", "text", "skip")}
           for s in stmts]
    (host_dir / "run.json").write_text(scrub(json.dumps({"meta": meta, "partial": partial, "statements": raw,
                                                          "results": results, "hints": hints, "rooms": rooms})))
    path = write_report(meta, stmts, rooms, partial)
    log(f"report: {rel(path)} (+ .json); run logs: {rel(host_dir)}")
    if isinstance(failure, KeyboardInterrupt):
        raise failure
    return 1 if failure is not None else 0


def cmd_report(args):
    """Rewrite a report from a finished run's raw results (labs/vm/runs/<stamp>/run.json), e.g. after a
    classifier rule changed. Nothing is started."""
    runs = sorted(p for p in RUNS.glob("*/run.json"))
    path = RUNS / args.run / "run.json" if args.run else (runs[-1] if runs else None)
    if not path or not path.is_file():
        raise Abort("no run.json found in labs/vm/runs/")
    data = json.loads(path.read_text())
    results = {int(k): v for k, v in data["results"].items()}
    stmts = data["statements"]
    classify_all(stmts, results, data["hints"])
    out = write_report(data["meta"], stmts, data["rooms"], data["partial"])
    log(f"report rewritten from {rel(path)}: {rel(out)}")
    return 0


def cmd_clean(args):
    removed = []
    if container_exists():
        run(["docker", "rm", "-f", CONTAINER])
        removed.append(f"container {CONTAINER}")
    v = run(["docker", "volume", "inspect", "-f", "{{index .Labels \"devops-handbook.vm\"}}", VOLUME])
    if v.returncode == 0:
        if v.stdout.strip() == LABEL_V:
            run(["docker", "volume", "rm", VOLUME], check=True)
            removed.append(f"volume {VOLUME}")
        else:
            print(f"volume {VOLUME} has no {LABEL_K} label: left alone")
    img = run(["docker", "image", "inspect", "-f", "{{index .Config.Labels \"devops-handbook.project\"}}", IMAGE])
    if img.returncode == 0 and img.stdout.strip() == "vm":
        run(["docker", "image", "rm", IMAGE])
        removed.append(f"image {IMAGE}")
    old = run(["docker", "images", "-q", "--filter", "label=devops-handbook.project=vm", "--filter", "dangling=true"])
    for iid in old.stdout.split():
        if run(["docker", "image", "rm", iid]).returncode == 0:
            removed.append(f"old build {iid}")
    if args.runs and RUNS.exists():
        import shutil
        for p in RUNS.iterdir():
            if p.name != ".lock":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        removed.append(f"local run logs in {rel(RUNS)}")
    print("removed: " + (", ".join(removed) if removed else "nothing (already clean)"))
    print("build cache of this image is removed by the janitor after JANITOR_CACHE_KEEP_HOURS (DOCKER.md)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="prerequisites: docker, /dev/kvm, free space, KVM inside the runner")
    pp = sub.add_parser("prepare", help="download + verify the cloud image, build the prepared image")
    pp.add_argument("--force", action="store_true", help="rebuild the prepared image even if it is up to date")
    pv = sub.add_parser("verify", help="run the commands pass and/or the rooms pass, write the report")
    pv.add_argument("--commands", nargs="?", const=True, default=None, help="run the commands pass")
    pv.add_argument("--modules", help="only these modules, e.g. 27,41 (implies --commands)")
    pv.add_argument("--rooms", nargs="?", const=True, default=None, help="run the rooms pass (optionally: 13,19)")
    pv.add_argument("--keep-going", action="store_true", help="continue after a VM fails to boot")
    pr = sub.add_parser("report", help="rewrite the report from a finished run's raw results")
    pr.add_argument("--run", help="run directory name in labs/vm/runs/ (default: the latest)")
    pc = sub.add_parser("clean", help="remove the volume and the image")
    pc.add_argument("--runs", action="store_true", help="also delete local run logs in labs/vm/runs/")
    args = ap.parse_args(argv)

    def on_signal(signum, _frame):
        raise KeyboardInterrupt(f"signal {signum}")

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, on_signal)
    lock = None
    try:
        if args.cmd in ("prepare", "verify", "clean"):
            lock = take_lock()
        return {"check": cmd_check, "prepare": cmd_prepare, "verify": cmd_verify, "report": cmd_report,
                "clean": cmd_clean}[args.cmd](args)
    except Abort as exc:
        log(f"ERROR: {exc}")
        return 1
    except KeyboardInterrupt:
        log("interrupted: cleaning up")
        return 130
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)       # cleanup must not be interrupted half-way
        try:
            for vm in list(_state["vms"]):
                vm.stop()
            if _state["container"] or (args.cmd in ("prepare", "verify") and container_exists()):
                stop_container()
        finally:
            if lock:
                lock.close()


if __name__ == "__main__":
    sys.exit(main())
