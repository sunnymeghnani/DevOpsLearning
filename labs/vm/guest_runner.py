#!/usr/bin/env python3
"""Runs the handbook's statements INSIDE the verify VM (never on the host). Python 3 stdlib only.

    guest_runner.py JOBS.json

vmctl.py copies this file and the job list into the guest over SSH and starts it as a transient systemd
unit (`systemd-run --unit vfy-runner`), so it does not depend on the SSH connection: a statement that
breaks networking or sshd cannot cut the run short. Results go to the virtio-serial port
/dev/virtio-ports/vfy.results, which QEMU writes to a file next to the overlay, outside the guest.

JOBS.json: {"timeout": 20, "limit": 4000, "blocks": [{"id": "b3", "statements": [{"id": 17, "text": "..."}]}]}
Records (one JSON object per line):
  {"t": "B", "block": "b3"}                                           a block starts (fresh bash session)
  {"t": "S", "id": 17}                                                statement 17 starts
  {"t": "R", "id": 17, "rc": 0, "dur": 0.03, "timeout": false, "out": "...", "err": "...", "note": "",
   "bg": ["stress-ng"]}                                                bg: still running after it returned
  {"t": "H"}                                                          heartbeat while a statement runs
  {"t": "HINT", "cmd": "kubectl", "text": "..."}                      command-not-found's package hint
  {"t": "DONE"}

Each block runs in ONE bash session (variables and cd carry over), each statement is sourced from a file
with stdin from /dev/null and its own stdout/stderr files. After TIMEOUT seconds the processes the
statement started get SIGTERM, then SIGKILL; if bash itself does not come back (a builtin loop), the
session is replaced. errexit/nounset/pipefail are reset after every statement so one failure does not
end the session. The runner is a child subreaper, so background processes stay its descendants and are
killed at the end of their block.

Before each block the runner clears systemd's failed state of docker/containerd and restarts them if they were
running when it started and an earlier block stopped them (`systemctl stop docker.socket docker.service  # on
dok-02` would otherwise leave every later docker statement of the module with "Cannot connect to the Docker
daemon"). The first statement of that block gets a note saying so.
"""
import ctypes
import json
import os
import re
import select
import signal
import sys
import time

CHANNEL = "/dev/virtio-ports/vfy.results"
BASE = "/root/vfy"
WORK = "/root/work"
MARK_FD = 9
FLOOD = 8 * 1024 * 1024          # stop a statement whose output passes 8 MB
HEAL_UNITS = ("containerd.service", "docker.socket", "docker.service")
TICK = os.sysconf("SC_CLK_TCK")
ENV = {
    "HOME": "/root", "USER": "root", "LOGNAME": "root", "SHELL": "/bin/bash", "LANG": "C.UTF-8",
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin",
    "TERM": "xterm", "COLUMNS": "160", "LINES": "50", "PAGER": "cat", "MANPAGER": "cat", "GIT_PAGER": "cat",
    "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0", "EDITOR": "true", "VISUAL": "true", "SYSTEMD_EDITOR": "true",
    "SUDO_EDITOR": "true", "DEBIAN_FRONTEND": "noninteractive", "LESS": "-FRX",
}

_out = None


def emit(rec):
    global _out
    line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8", "replace")
    try:
        os.write(_out, line)
    except OSError:
        pass


def uptime_ticks():
    with open("/proc/uptime") as f:
        return float(f.read().split()[0]) * TICK


def proc_table():
    """pid -> (ppid, starttime ticks)"""
    t = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                s = f.read()
        except OSError:
            continue
        rest = s[s.rfind(")") + 2:].split()
        t[int(d)] = (int(rest[1]), int(rest[19]))
    return t


def descendants(root, since=None, exclude=()):
    t = proc_table()
    kids = {}
    for pid, (ppid, _) in t.items():
        kids.setdefault(ppid, []).append(pid)
    out, todo = [], [root]
    while todo:
        for c in kids.get(todo.pop(), []):
            todo.append(c)
            if c in exclude:
                continue
            if since is None or t[c][1] >= since:
                out.append(c)
    return out


def kill_all(pids, sig):
    for p in pids:
        try:
            os.kill(p, sig)
        except OSError:
            pass


def new_procs(root, old, through):
    """Processes under `root` that are not in `old`, walking through `through` (the bash session) but not into
    the children of an `old` process (what an earlier background job forks is not this statement's doing)."""
    t = proc_table()
    kids = {}
    for pid, (ppid, _) in t.items():
        kids.setdefault(ppid, []).append(pid)
    out, todo = [], [root]
    while todo:
        for c in kids.get(todo.pop(), []):
            if c in through:
                todo.append(c)
            elif c not in old:
                out.append(c)
                todo.append(c)
    return out


def running_names(pids):
    """Command names of the pids that are still running (not zombies), at most 5."""
    names = []
    for p in pids:
        try:
            with open(f"/proc/{p}/stat") as f:
                s = f.read()
        except OSError:
            continue
        if s[s.rfind(")") + 2:].split()[0] not in ("Z", "X"):
            names.append(s[s.find("(") + 1:s.rfind(")")])
    return sorted(set(names))[:5]


def systemctl(*args, timeout=60):
    import subprocess
    try:
        return subprocess.run(["systemctl", *args], capture_output=True, text=True, timeout=timeout, env=ENV)
    except (OSError, subprocess.TimeoutExpired):
        return None


def active_units(units):
    p = systemctl("is-active", *units, timeout=20)
    states = p.stdout.split() if p is not None else []
    return {u for u, st in zip(units, states) if st == "active"}


def heal(baseline):
    """Restart the baseline units an earlier block stopped. Returns (note, still_healing)."""
    systemctl("reset-failed", *baseline, timeout=20)        # also resets systemd's start rate limit
    down = sorted(set(baseline) - active_units(baseline))
    if not down:
        return "", True
    systemctl("start", *[u for u in baseline if u.endswith(".service")], timeout=90)
    still = sorted(set(baseline) - active_units(baseline))
    if still:
        return f"an earlier block stopped {', '.join(down)}; the runner could not restart {', '.join(still)} " \
               "(it stops trying)", False
    return f"an earlier block stopped {', '.join(down)}; the runner restarted it before this block", True


def reap(session=None):
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return
        if session is not None and pid == session.pid:
            session.status = os.waitstatus_to_exitcode(status)


class Session:
    def __init__(self):
        r, w = os.pipe()            # commands -> bash stdin
        mr, mw = os.pipe()          # bash -> markers (fd 9 inside bash)
        devnull = os.open(os.devnull, os.O_RDWR)
        fa = [(os.POSIX_SPAWN_DUP2, r, 0), (os.POSIX_SPAWN_DUP2, devnull, 1), (os.POSIX_SPAWN_DUP2, devnull, 2),
              (os.POSIX_SPAWN_DUP2, mw, MARK_FD)]
        # its own process group: `kill 0` / `kill -- -$$` in a statement must not reach the runner
        self.pid = os.posix_spawn("/bin/bash", ["bash", "--noprofile", "--norc"], ENV, file_actions=fa, setpgroup=0)
        for fd in (r, mw, devnull):
            os.close(fd)
        self.cmd, self.mark, self.status, self.buf = w, mr, None, b""
        try:
            with open(f"/proc/{self.pid}/oom_score_adj", "w") as f:
                f.write("0")        # the runner is -1000; statements must not inherit that
        except OSError:
            pass
        self.send(f"cd {WORK} 2>/dev/null || cd /root")

    def send(self, text):
        try:
            os.write(self.cmd, (text + "\n").encode())
            return True
        except OSError:
            return False

    def alive(self):
        reap(self)
        return self.status is None

    def read_marker(self, wait):
        """The next marker line within `wait` seconds: ('rc', int), ('dead', code) or None."""
        end = time.monotonic() + wait
        while True:
            if b"\n" in self.buf:
                line, self.buf = self.buf.split(b"\n", 1)
                m = re.match(rb"__VFY (\d+) ", line)
                if m:
                    return ("rc", int(m.group(1)))
                continue
            left = end - time.monotonic()
            if left <= 0:
                return None
            r, _, _ = select.select([self.mark], [], [], min(left, 0.25))
            if r:
                chunk = os.read(self.mark, 4096)
                if not chunk:                       # bash exited (exit, exec, a fatal error)
                    deadline = time.monotonic() + 2
                    while self.alive() and time.monotonic() < deadline:
                        time.sleep(0.05)
                    return ("dead", self.status if self.status is not None else -1)
                self.buf += chunk
            elif not self.alive():
                return ("dead", self.status)

    def close(self):
        kill_all(descendants(os.getpid(), exclude={self.pid}), signal.SIGKILL)
        kill_all([self.pid], signal.SIGKILL)
        for fd in (self.cmd, self.mark):
            try:
                os.close(fd)
            except OSError:
                pass
        deadline = time.monotonic() + 3
        while self.alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        reap()


def tail(path, limit):
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(limit)
        os.unlink(path)
    except OSError:
        return "", 0
    text = data.decode("utf-8", "replace")
    if size > limit:
        text += f"\n[... {size - limit} more bytes]"
    return text, size


def run_statement(sess, sid, text, timeout, limit, pre_note=""):
    sfile, ofile, efile = f"{BASE}/s/{sid}.sh", f"{BASE}/o/{sid}.out", f"{BASE}/o/{sid}.err"
    with open(sfile, "w") as f:
        f.write(text + "\n")
    emit({"t": "S", "id": sid})
    before = set(descendants(os.getpid()))
    since = uptime_ticks() - 1
    t0 = time.monotonic()
    sess.send(f"{{ . {sfile}; }} </dev/null >{ofile} 2>{efile} {MARK_FD}>&-; __vfy=$?; "
              f"set +e +u +o pipefail; echo \"__VFY $__vfy {sid}\" >&{MARK_FD}")
    rc, timed_out, note, replace = None, False, "", False
    beat = time.monotonic()
    while True:
        got = sess.read_marker(0.5)
        if got:
            kind, val = got
            rc = val
            if kind == "dead":
                note, replace = "the statement ended the bash session (exit, exec or a fatal error)", True
            break
        now = time.monotonic()
        if now - beat >= 5:
            emit({"t": "H"})
            beat = now
        size = sum(os.path.getsize(p) for p in (ofile, efile) if os.path.exists(p))
        if size > FLOOD:
            note = "output passed 8 MB: stopped"
            kill_all(descendants(os.getpid(), since, {sess.pid}), signal.SIGKILL)
        elif now - t0 >= timeout:
            timed_out = True
            kill_all(descendants(os.getpid(), since, {sess.pid}), signal.SIGTERM)
            got = sess.read_marker(2)
            if not got:
                kill_all(descendants(os.getpid(), since, {sess.pid}), signal.SIGKILL)
                got = sess.read_marker(2)
            if got:
                rc = 124
                if got[0] == "dead":
                    replace = True
            else:
                rc, replace, note = 124, True, "bash itself did not return (a builtin loop): session replaced"
            break
    dur = time.monotonic() - t0
    bg = [] if replace else running_names(new_procs(os.getpid(), before, {sess.pid}))
    out, _ = tail(ofile, limit)
    err, _ = tail(efile, limit)
    try:
        os.unlink(sfile)
    except OSError:
        pass
    note = "; ".join(n for n in (pre_note, note) if n)
    emit({"t": "R", "id": sid, "rc": rc, "dur": round(dur, 3), "timeout": timed_out, "out": out, "err": err,
          "note": note, "bg": bg})
    return err, replace


NOT_FOUND = re.compile(r"(?:^|\n)(?:[^\n:]*: )*(?:line \d+: )?([A-Za-z0-9_.+-]+): (?:command )?not found\s*$"
                       r"|(?:^|\n)(?:env|nice|nohup|timeout|stdbuf|ionice|setsid|chroot|xargs|taskset|chrt|numactl|"
                       r"strace|ltrace|watch): [‘'`\"]?([A-Za-z0-9_.+-]+)[’'`\"]?: No such file or directory\s*$", re.M)


def hint(cmd):
    import subprocess
    try:
        p = subprocess.run(["/usr/lib/command-not-found", "--", cmd], capture_output=True, text=True, timeout=20,
                           env=ENV)
        return (p.stderr or p.stdout).strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def main():
    global _out
    jobs = json.load(open(sys.argv[1]))
    try:
        _out = os.open(CHANNEL, os.O_WRONLY)
    except OSError:
        _out = os.open(f"{BASE}/results.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl(36, 1, 0, 0, 0)                      # PR_SET_CHILD_SUBREAPER
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    for d in (f"{BASE}/s", f"{BASE}/o", WORK):
        os.makedirs(d, exist_ok=True)
    timeout, limit = jobs.get("timeout", 20), jobs.get("limit", 4000)
    missing = set()
    baseline, healing = tuple(u for u in HEAL_UNITS if u in active_units(HEAL_UNITS)), True
    for block in jobs["blocks"]:
        emit({"t": "B", "block": block["id"]})
        pre_note = ""
        if baseline and healing:
            pre_note, healing = heal(baseline)
        sess = Session()
        for st in block["statements"]:
            if not sess.alive():
                sess.close()
                sess = Session()
            err, replace = run_statement(sess, st["id"], st["text"], timeout, limit, pre_note)
            pre_note = ""
            missing.update(a or b for a, b in NOT_FOUND.findall(err))
            if replace:
                sess.close()
                sess = Session()
        sess.close()
    for cmd in sorted(missing):
        if "/" not in cmd:
            emit({"t": "HINT", "cmd": cmd, "text": hint(cmd)[:600]})
    emit({"t": "DONE"})


if __name__ == "__main__":
    main()
