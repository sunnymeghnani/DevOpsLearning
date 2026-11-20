# Verify VM: design

A throwaway Ubuntu 24.04 VM that runs the handbook's shell commands and every lab room, writes a pass/fail
checklist (`reports/verify/verify-YYYY-MM-DD.md` + `.json`) and deletes its disks. Nothing the handbook
says to run ever runs on the host.

```bash
python3 labs/vm/vmctl.py check              # docker, /dev/kvm, >= 15 GB free, KVM inside the runner
python3 labs/vm/vmctl.py prepare            # once: download + verify the cloud image, build the prepared image
python3 labs/vm/vmctl.py verify             # all modules + all 25 rooms (about 2 hours)
python3 labs/vm/vmctl.py verify --modules 27,41          # some modules only (implies --commands)
python3 labs/vm/vmctl.py verify --rooms 13,19            # some rooms only
python3 labs/vm/vmctl.py verify --commands               # the commands pass only
python3 labs/vm/vmctl.py report [--run STAMP]            # rewrite a report from a run's saved raw results
python3 labs/vm/vmctl.py clean [--runs]                  # remove the volume and the image (and local logs)
```

## Files

| File | What it is |
|---|---|
| `Dockerfile` | the runner image `devops-handbook-vm:local`: ubuntu:24.04 + qemu-system-x86, qemu-utils, genisoimage, openssh-client, gpgv, ubuntu-keyring, curl, python3. First step `RUN : devops-handbook-vm`, label `devops-handbook.project="vm"` (the janitor recognises both) |
| `vmctl.py` | the host orchestrator (Python stdlib + the docker CLI) |
| `verifylib.py` | pure rules: block extraction, statement splitter, placeholders, denylist, classifier, package-list parser. Tested by `tests/test_vm_verify.py` |
| `provision.sh` | the single source of truth for the prepared image (runs once, inside the VM) |
| `guest_runner.py` | runs the statements inside the guest (never on the host) |
| `runs/` | local run logs: serial consoles, raw results, provisioning log (git-ignored) |

## Where things run

- **Host:** only the docker CLI (for objects named `devops-handbook-vm` with label `devops-handbook.vm=1`
  or `devops-handbook.project=vm`), reading files, and `bash -n` (parse only) to split statements.
- **Runner container** `devops-handbook-vm`: `docker run --device /dev/kvm --cap-drop ALL
  --security-opt no-new-privileges:true --read-only --tmpfs /tmp --init --memory 3g --pids-limit 512`, the
  volume on `/vm`, **no published ports**, not privileged. Only `prepare` runs it on the default bridge
  (outbound, for the cloud image and the Ubuntu archive); during `verify` it runs with `--network none`, so the
  container has nothing but loopback. It runs as root so it can open `/dev/kvm` (660 root:kvm on the host) as its owner.
  QEMU needs **no** capabilities: `check` proves it with KVM's API ioctl and a QEMU `query-kvm` in a
  container with every capability dropped and no network.
- **Guest:** QEMU/KVM, q35, 2 vCPU, 2 GB RAM, virtio disk and NIC, `-display none -serial file:...`
  (the headless equivalent of `-nographic`, which cannot be combined with `-daemonize`), serial console
  captured per VM. User-mode networking with `hostfwd=tcp:127.0.0.1:2222-:22` (inside the container);
  vmctl reaches the guest with `docker exec devops-handbook-vm ssh -p 2222 lab@127.0.0.1`.
  During `verify` the guest is **offline** twice over: `restrict=on` (slirp drops or resets everything that is
  not the SSH forward, even when a statement adds a default route) inside a container with no network. Only
  `prepare` lets it reach the Ubuntu archive.

## Disks (one named volume `devops-handbook-vm`, label `devops-handbook.vm=1`)

```
/vm/cache/ubuntu-24.04-server-cloudimg-amd64.img   the official image, verified (~600 MB)
/vm/cache/SHA256SUMS, SHA256SUMS.gpg               checked with gpgv against ubuntu-cloudimage-keyring.gpg
/vm/prepared/prepared.qcow2                        overlay on the cloud image: packages installed
/vm/prepared/prepared.json                         provisioning hash (provision.sh + the lab package list + seed)
/vm/keys/id_ed25519                                ephemeral key, new with every prepared image
/vm/runs/<stamp>/*.qcow2                           per-VM overlays on prepared.qcow2: deleted after each VM
```

Every overlay is created with a **10G virtual size**. One VM runs at a time (a lock file in `runs/` and the
fixed container name). `prepare` and `verify` refuse to start below **15 GB free** on the filesystem that holds
Docker's data root, stop a run if it falls below 8 GB, and stop a VM whose overlay grows past 6.5 GB.
At rest the volume holds the cloud image and the prepared image only.

## prepare

1. Fetch `SHA256SUMS` and `SHA256SUMS.gpg` from `https://cloud-images.ubuntu.com/releases/noble/release/`,
   verify the signature with `gpgv --keyring /usr/share/keyrings/ubuntu-cloudimage-keyring.gpg`, download the
   image only if the cached one does not match, check its sha256 **before** use (a mismatch is deleted).
2. If `prepared.json` holds the current hash, stop. Otherwise boot a 10G overlay of the cloud image with a
   cloud-init NoCloud seed (user `lab`, uid 1000, groups sudo/adm/systemd-journal, the new SSH key, no
   password, hostname `lab`), wait for SSH, and pipe `provision.sh` to `sudo bash -s` with
   `BASE_PACKAGES` parsed from `labs/base/Dockerfile` (so the VM always has the lab machine's tools).
3. `provision.sh` installs those packages plus the tools the modules use that Ubuntu's archive has
   (docker.io, nmap, iperf3, sysstat, smartmontools, nftables, wireguard-tools, restic, mysql-client, ...),
   `linux-tools-$(uname -r)` for perf, and builds command-not-found's database. Boot-time services follow
   the lab image (nginx, apache2, dnsmasq, postgresql, cron off; ttyd masked), except what a VM needs:
   ssh and systemd-resolved stay on, and the container-only masks (udevd, logind, getty, ...) are not
   applied. docker/containerd are off at boot so rooms see one NIC; cloud-init is disabled for later boots.
4. Power off; the overlay becomes `prepared.qcow2`.

## verify: pass 1, commands

- **Extraction** (`verifylib.py`): every ` ```bash ` block of the `NN-*.md` modules except 17 (Windows) and
  20 (macOS); a block that is mostly sample output is skipped. Lines are joined into complete statements:
  accumulate until no heredoc is open, the chunk does not end in `\`, `|`, `&&` or `||`, and `bash -n`
  accepts it; a line that never parses is emitted alone (the guest then reports its syntax error).
- **Skipped, never run:** placeholders (`<...>`, `...`, `…`, stand-ins such as `CONTAINER`, `PID`, `NS`,
  `OLD_IP`, `USER@HOST`), text that is not shell (SQL, YAML, INI), a whole block whose first line is the
  handbook's macOS label (`# macOS (Terminal), not Linux`, `# macOS client ...`), and a denylist of VM-killers and run-breakers
  (reboot/poweroff/isolate, stopping ssh or networkd, mkfs/wipefs/fdisk/dd onto the VM's own disk, rm -rf of
  system dirs, firewall rule changes, link down / address flush / route changes, netplan apply/try, tc
  netem, kill -1, pkill sshd/python, SysRq, swapoff -a, recursive chmod/chown of /, changes to the lab or
  root account, fork bombs, disk fillers, and removing docker.io: the VM is offline, so a lab that swaps it for
  Docker CE would leave the rest of the module without docker). The rules and their tests are in one place.
- **Running:** one fresh VM per module. A prelude starts containerd, docker, cron, nginx and postgresql and
  loads an nft table `vfy_offline` that refuses outbound connections at once (otherwise every offline curl
  or ssh would wait for its own timeout). `guest_runner.py` is started as a transient systemd unit, so it
  survives anything a statement does to SSH. One bash session per block (variables and `cd` carry over),
  as root, in `/root/work`, stdin `/dev/null`, 20 s per statement (then SIGTERM and SIGKILL of what it
  started), output truncated to 4 KB per stream. Each session is its own process group, so `kill 0` (for
  example `kill -9 "$(systemctl show -p MainPID --value app)"` when the unit does not exist) ends only that
  session. Results leave the guest through a **virtio-serial port**
  that QEMU writes to a file in the container, not through the network. Before each block the runner resets
  docker/containerd's failed state and restarts them if an earlier block stopped them (multi-host labs such as
  `systemctl stop docker.socket docker.service   # on dok-02` would otherwise leave the rest of the module with
  "Cannot connect to the Docker daemon"); the first statement of that block carries a note. Each result lists
  the processes the statement left running in the background (`bg`).
- **A broken VM:** if no record arrives for 75 s, QEMU exits, or the overlay passes 6.5 GB, the statement
  that was running is recorded as `BROKE_VM`, the VM is destroyed and the rest of the module continues in a
  fresh VM. If an earlier statement of the same block left a job running in the background (`stress-ng ... &`),
  the BROKE_VM detail names it: the statement that was running is often only the victim.
- **Classes** (`verifylib.classify`): `PASS` (exit 0), `USAGE` (unknown/invalid option, usage text, bash
  syntax error: a candidate doc error), `MISSING` (command not found, with command-not-found's package hint),
  `EXTERNAL` (cloud/Kubernetes/IaC clients and other platforms' tools, e.g. kubectl, aws, terraform, helm,
  ansible, dnf, qm), `CONTEXT` (non-zero for lack of a service/file/host/cluster/network: informational),
  `TIMEOUT`, `SKIPPED(reason)`. A "command not found" or usage complaint on stderr counts even when a
  pipeline turned the exit status into 0. Refinements: usage text printed after a context error (no such
  pid/file/user, not a git repository, an empty `$(...)` or `xargs` input) is CONTEXT; a "command" that is
  config or list text (`Host *`, `- echo`, `Unattended-Upgrade::...`, a list of sysctl keys) is USAGE; a
  shell function defined in another block is CONTEXT; `env: 'x': No such file or directory` is MISSING x; an
  exit 127 whose error went to a file is EXTERNAL when the command is, else CONTEXT; `git diff --staged` outside
  a repository (git falls back to `--no-index`) is CONTEXT.
- **Report** (`reports/verify/verify-YYYY-MM-DD.md` + `.json`; `-partial` when only some modules or rooms ran):
  summary counts, a rooms checklist, a modules checklist, then every USAGE, MISSING and BROKE_VM item with
  file, nearest heading, line, statement, stderr excerpt and package hint. The raw results stay in
  `runs/<stamp>/run.json`, so `vmctl.py report` re-applies changed classifier rules without a new run (the
  default is the newest run directory, which may be a partial one: pass `--run STAMP` for the full run). The
  report is named after the run's date. Skip decisions are not re-applied: they decided what ran.
  Host paths and the host user name are scrubbed from everything written.

## verify: pass 2, rooms

For every room in `labs/rooms`, on a fresh VM: `labs/test_rooms.py`'s `validate_room` and
`run_room_steps` (shared with the container test): setup.sh twice, every check fails, solve.sh, every check
passes, answer hashes match. Scripts are piped to `sudo bash -s` over SSH as `lab`. Rooms were written for
the container lab; a step that behaves differently on a real VM is reported as **DIFFERS** with the failing
step, not patched (for example room 14 uses a stand-in for systemd-resolved's stub, which a real VM runs).

## Cleanup

Every VM's overlay is deleted when the VM stops; the run directory and the runner container are removed at
the end, on errors and on Ctrl-C/SIGTERM (try/finally, signal handlers). A container left by a `kill -9` is
removed by the next run. `clean` removes the volume (only if it carries `devops-handbook.vm=1`) and the image
(only if it carries `devops-handbook.project=vm`); old untagged builds and the build cache are removed by the
janitor (`docker/janitor/janitor.py` recognises `RUN : devops-handbook-vm`). Nothing else is selected:
no prune, no other container, image, volume or network.
