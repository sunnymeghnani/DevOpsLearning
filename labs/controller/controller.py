#!/usr/bin/env python3
"""Labs controller: starts disposable lab machines for the handbook's hands-on rooms.

Python 3 standard library only, plus the docker CLI (through /var/run/docker.sock, the one
privileged piece; see DOCKER.md). It runs as the compose service `labs-controller` under the
`labs` profile and answers JSON on :8080 under /api/labs/ (nginx in the handbook container
proxies it; the controller publishes no port).

What it may do with Docker, and nothing else:
  * `docker run` ONLY the image devops-handbook-lab:base, ONLY with the options in labs/SPEC.md
    (see lab_run_argv; tests compare it with the SPEC);
  * `docker exec` into its labs (wait for systemd, feed setup.sh and checks to `bash -s` as root,
    start ttyd), `docker rm -f` containers labelled devlab=1, list and inspect them;
  * devlab-net: inspect it, attach the handbook container (nginx proxies the terminals) while labs
    run, and on shutdown detach the handbook and itself and delete the network.

Lifecycle of a lab: start -> wait until systemd is up -> setup.sh -> ttyd on :7681 with a per-session
basic-auth credential that only nginx gets (the page embeds it through nginx at /lab-term/<sid>/) -> answers and checks (task gating) -> Finish (destroyed,
progress recorded, walkthrough returned) / Reset (destroyed, a fresh one started) / 30 min idle or 3 h after it started
(destroyed by the reaper). At start the controller removes every container labelled devlab=1
(leftovers). On SIGTERM (`docker compose --profile labs down`, or removing this container) it
removes every devlab=1 container and devlab-net: labs off leaves nothing behind. At most two labs
run at once.

Never served: solve.sh, answers.test.json (they are not even in the image), answer hashes,
plaintext answers, check scripts. Walkthroughs are returned only by Finish.
"""
import base64
import hashlib
import hmac
import html
import ipaddress
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOMS_DIR = os.environ.get("LABS_ROOMS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "rooms"))
DATA_DIR = os.environ.get("LABS_DATA_DIR", "/data")
PORT = int(os.environ.get("LABS_PORT", "8080"))
IMAGE = "devops-handbook-lab:base"
NETWORK = "devlab-net"
HANDBOOK = os.environ.get("LABS_HANDBOOK", "devops-handbook")        # nginx container: joins devlab-net while labs run
SELF = os.environ.get("LABS_SELF", "devops-handbook-labs")           # this controller's container name
MAX_LABS = max(1, min(2, int(os.environ.get("LABS_MAX", "2"))))      # never more than 2
IDLE_SECONDS = int(os.environ.get("LABS_IDLE_SECONDS", str(30 * 60)))
# Hard lifetime: a lab machine is destroyed this long after it started, busy or not (0 = no limit).
MAX_SECONDS = max(0, int(os.environ.get("LABS_MAX_SECONDS", str(3 * 3600))))
REAP_EVERY = 30
BOOT_TIMEOUT = 90
SETUP_TIMEOUT = 120
CHECK_TIMEOUT = 40
ALLOWED_HOSTS = {h.strip().lower() for h in os.environ.get(
    "LABS_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],::1").split(",") if h.strip()}

SID_RE = re.compile(r"^[a-f0-9]{12}$")
ROOM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")

# The exact lab options from labs/SPEC.md. Nothing else is ever passed to `docker run`.
LAB_CAPS = ("SYS_ADMIN", "CHOWN", "DAC_OVERRIDE", "FOWNER", "SETUID", "SETGID", "KILL",
            "NET_BIND_SERVICE", "SYS_CHROOT", "AUDIT_WRITE", "NET_RAW")
LAB_ENTRY_CMD = "mount -o remount,rw /sys/fs/cgroup && exec /sbin/init"


def lab_run_argv(sid, room_id):
    """`docker run` argv for one lab: exactly the SPEC options, with the session and room filled in."""
    if not SID_RE.match(sid) or not ROOM_ID_RE.match(room_id):
        raise ValueError("bad session or room id")
    argv = ["docker", "run", "-d", "-t", "--name", f"devlab-{sid}", "--hostname", "lab",
            "--label", "devlab=1", "--label", f"devlab.room={room_id}",
            "--cgroupns=private", "--tmpfs", "/run", "--tmpfs", "/run/lock", "--tmpfs", "/tmp",
            "--cap-drop", "ALL"]
    for cap in LAB_CAPS:
        argv += ["--cap-add", cap]
    argv += ["--security-opt", "apparmor=unconfined",
             "--memory", "768m", "--cpus", "1", "--pids-limit", "512",
             "--network", NETWORK,
             "--entrypoint", "sh", IMAGE, "-c", LAB_ENTRY_CMD]
    return argv


TTYD_ARGV = ["ttyd", "-W", "-p", "7681", "-m", "3", "-c", "lab:<token>",
             "-t", "fontSize=14", "-t", "disableLeaveAlert=true",
             "-t", 'theme={"background":"#0e1621","foreground":"#d9e4ef","cursor":"#4ade80"}',
             "login", "-f", "lab"]
TERM_USER = "lab"
TOKEN_RE = re.compile(r"^[a-f0-9]{32,64}$")


def ttyd_argv(token):
    """TTYD_ARGV with this session's terminal credential filled in. Labs share devlab-net, so
    without basic auth lab A could open http://devlab-<B>:7681 and get a shell in lab B. Only nginx
    knows the credential (the controller hands it over on /api/labs/term-auth); it is never sent
    in the API JSON or the page, and never logged."""
    if not TOKEN_RE.match(token or ""):
        raise ValueError("bad terminal token")
    return [f"{TERM_USER}:{token}" if a == "lab:<token>" else a for a in TTYD_ARGV]


def basic_auth(token):
    """The Authorization value ttyd expects for `-c lab:<token>` (it checks the HTTP page, /token
    and the websocket upgrade)."""
    return "Basic " + base64.b64encode(f"{TERM_USER}:{token}".encode()).decode("ascii")


def log(*parts):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *parts, flush=True)


# --------------------------------------------------------------------------- answers
def normalise_answer(text):
    """SPEC: lower-case, trimmed, inner whitespace collapsed."""
    return " ".join(str(text).lower().split())


def answer_sha256(text):
    return hashlib.sha256(normalise_answer(text).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- rooms
def validate_room(room, room_dir):
    """List of problems (empty when the room can be served)."""
    p = []
    rid = room.get("id", "")
    if not isinstance(rid, str) or not ROOM_ID_RE.match(rid):
        p.append(f"bad id {rid!r}")
    for key in ("title", "level", "path", "brief"):
        if not isinstance(room.get(key), str) or not room.get(key).strip():
            p.append(f"missing {key}")
    if not isinstance(room.get("order"), int):
        p.append("order must be an integer")
    src = room.get("source")
    if not isinstance(src, dict) or not str(src.get("url", "")).startswith("https://"):
        p.append("source.url must be an https URL")
    if not os.path.isfile(os.path.join(room_dir, "setup.sh")):
        p.append("setup.sh missing")
    tasks = room.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        p.append("no tasks")
        tasks = []
    seen, qids = set(), set()
    for t in tasks:
        tid = t.get("id")
        if not tid or tid in seen:
            p.append(f"task id {tid!r} missing or repeated")
        seen.add(tid)
        if not isinstance(t.get("points", 0), int):
            p.append(f"{tid}: points must be an integer")
        if not t.get("questions") and not t.get("checks"):
            p.append(f"{tid}: a task needs a question or a check")
        for q in t.get("questions", []):
            if q.get("id") in qids:
                p.append(f"{tid}: question id {q.get('id')!r} repeated (ids are unique per room)")
            qids.add(q.get("id"))
            if not q.get("id") or not HASH_RE.match(str(q.get("answer_sha256", ""))):
                p.append(f"{tid}: question {q.get('id')!r} needs an id and a sha256 answer hash")
            for leak in ("answer", "answers", "solution"):
                if leak in q:
                    p.append(f"{tid}: question {q.get('id')!r} has a plaintext '{leak}' field")
        for c in t.get("checks", []):
            script = str(c.get("script", ""))
            full = os.path.normpath(os.path.join(room_dir, script))
            if not c.get("id") or not script or not full.startswith(os.path.normpath(room_dir) + os.sep) \
                    or not os.path.isfile(full):
                p.append(f"{tid}: check {c.get('id')!r} script {script!r} missing or outside the room")
    return p


def load_rooms(root=ROOMS_DIR):
    rooms = {}
    if not os.path.isdir(root):
        log("rooms folder not found:", root)
        return rooms
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        rj = os.path.join(d, "room.json")
        if not os.path.isfile(rj):
            continue
        try:
            with open(rj, encoding="utf-8") as f:
                room = json.load(f)
        except (OSError, ValueError) as e:
            log(f"room {name}: unreadable room.json ({e}), skipped")
            continue
        problems = validate_room(room, d)
        if problems:
            log(f"room {name}: skipped: " + "; ".join(problems))
            continue
        if room["id"] in rooms:
            log(f"room {name}: duplicate id {room['id']}, skipped")
            continue
        room["_dir"] = d
        rooms[room["id"]] = room
    return rooms


def ordered_paths(rooms):
    """{path: [room ids sorted by order]}"""
    paths = {}
    for r in sorted(rooms.values(), key=lambda r: (r["order"], r["id"])):
        paths.setdefault(r["path"], []).append(r["id"])
    return paths


def public_task(t):
    return {
        "id": t["id"], "title": t.get("title", ""), "text": t.get("text", ""),
        "points": t.get("points", 0), "hints": list(t.get("hints", [])),
        "questions": [{"id": q["id"], "prompt": q.get("prompt", ""), "format": q.get("format", "")}
                      for q in t.get("questions", [])],
        "checks": [{"id": c["id"], "describe": c.get("describe", "")} for c in t.get("checks", [])],
    }


def public_room(room):
    """What the browser may see: no answer hashes, no scripts, no walkthrough."""
    out = {k: room.get(k) for k in ("id", "title", "level", "map_node", "path", "order",
                                    "minutes", "difficulty", "source", "brief")}
    out["tasks"] = [public_task(t) for t in room["tasks"]]
    out["total_points"] = sum(t.get("points", 0) for t in room["tasks"])
    return out


# --------------------------------------------------------------------------- tiny markdown (walkthroughs)
def _inline(s):
    """Inline Markdown on escaped text; code spans are kept verbatim (no emphasis or links inside)."""
    parts = re.split(r"(`[^`]+`)", s)
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append("<code>" + html.escape(part[1:-1], quote=False) + "</code>")
            continue
        t = html.escape(part, quote=False)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<![*\w])\*([^*\s][^*]*)\*(?!\w)", r"<em>\1</em>", t)

        def link(m):
            url = html.unescape(m.group(2))
            if not re.match(r"^https?://", url):
                return m.group(1)
            return (f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
                    f"{m.group(1)}</a>")
        out.append(re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t))
    return "".join(out)


def markdown_html(text):
    """Small, safe Markdown subset: headings, paragraphs, lists, fenced code, inline code/bold/links."""
    out, para, items, kind = [], [], [], None
    lines = str(text or "").replace("\r\n", "\n").split("\n")

    def flush():
        nonlocal para, items, kind
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
        if items:
            out.append(f"<{kind}>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + f"</{kind}>")
        para, items, kind = [], [], None

    i = 0
    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^\s*```(\w*)\s*$", line)
        if fence:
            flush()
            j, code = i + 1, []
            while j < len(lines) and not re.match(r"^\s*```\s*$", lines[j]):
                code.append(lines[j])
                j += 1
            lang = fence.group(1)
            attr = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{attr}>" + html.escape("\n".join(code), quote=False) + "</code></pre>")
            i = j + 1
            continue
        h = re.match(r"^(#{1,4})\s+(.*)$", line)
        li = re.match(r"^\s*(?:[-*]|(\d+)[.)])\s+(.*)$", line)
        if not line.strip():
            flush()
        elif h:
            flush()
            level = min(6, len(h.group(1)) + 2)          # walkthrough headings sit under the room title
            out.append(f"<h{level}>{_inline(h.group(2))}</h{level}>")
        elif li:
            k = "ol" if li.group(1) else "ul"
            if para or (kind and kind != k):
                flush()
            kind = k
            items.append(li.group(2))
        elif items and line.startswith(("  ", "\t")):
            items[-1] += " " + line.strip()
        else:
            if items:
                flush()
            para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


# --------------------------------------------------------------------------- docker
def docker(args, input_bytes=None, timeout=60):
    """Run the docker CLI; returns (rc, stdout, stderr). Never raises on a non-zero exit."""
    try:
        p = subprocess.run(["docker", *args], input=input_bytes, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", f"docker {args[0]} timed out after {timeout}s"
    except OSError as e:
        return 127, "", f"docker CLI unavailable: {e}"
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def run_lab(argv, timeout=60):
    """Only ever called with lab_run_argv() output."""
    assert argv[:2] == ["docker", "run"] and IMAGE in argv
    return docker(argv[1:], timeout=timeout)


def exec_script(container, path, timeout):
    """Run a room script inside the lab as root, fed on stdin: `docker exec -i <lab> bash -s`."""
    with open(path, "rb") as f:
        data = f.read()
    return docker(["exec", "-i", container, "bash", "-s"], input_bytes=data, timeout=timeout)


def remove_container(name):
    rc, _, err = docker(["rm", "-f", "-v", name], timeout=60)
    if rc != 0 and "No such container" not in err:
        log(f"remove {name}: {err.strip()}")


def devlab_containers():
    rc, out, _ = docker(["ps", "-a", "--filter", "label=devlab=1", "--format", "{{.Names}}\t{{.State}}"])
    if rc != 0:
        return {}
    res = {}
    for line in out.splitlines():
        if "\t" in line:
            n, s = line.split("\t", 1)
            res[n.strip()] = s.strip()
    return res


class LabNet:
    """devlab-net subnets and the addresses of lab containers on it (to refuse requests from labs)."""
    def __init__(self):
        self.subnets, self.lab_ips, self.names, self.stamp = [], set(), set(), 0.0
        self.handbook_ip = ""              # the handbook's (nginx's) address on devlab-net
        self.lock = threading.Lock()

    def refresh(self, force=False, min_age=0.0):
        """Re-read devlab-net (at most every 15 s, or every `min_age` s when forced)."""
        with self.lock:
            age = time.time() - self.stamp
            if (not force and age < 15) or (force and age < min_age):
                return
            rc, out, _ = docker(["network", "inspect", NETWORK, "--format",
                                 "{{json .IPAM.Config}}\t{{json .Containers}}"], timeout=20)
            self.stamp = time.time()
            if rc != 0 or "\t" not in out:
                return
            cfg, conts = out.strip().split("\t", 1)
            try:
                members = list((json.loads(conts) or {}).values())
                nets = [ipaddress.ip_network(c["Subnet"], strict=False) for c in json.loads(cfg) or [] if c.get("Subnet")]
                ips = {c["IPv4Address"].split("/")[0] for c in members
                       if str(c.get("Name", "")).startswith("devlab-") and c.get("IPv4Address")}
            except (ValueError, KeyError, TypeError, AttributeError):
                return
            self.subnets, self.lab_ips = nets, ips
            self.names = {str(c.get("Name", "")) for c in members}
            self.handbook_ip = next((str(c.get("IPv4Address", "")).split("/")[0] for c in members
                                     if c.get("Name") == HANDBOOK and c.get("IPv4Address")), "")

    def attach_handbook(self):
        """The handbook's nginx proxies /lab-term/<sid>/ to devlab-<sid>:7681, so it joins devlab-net
        while labs run (and leaves it on shutdown: when labs are off, the network does not exist)."""
        self.refresh()
        if HANDBOOK in self.names:
            return
        rc, out, _ = docker(["inspect", "-f", "{{.State.Running}}", HANDBOOK], timeout=15)
        if rc != 0 or out.strip() != "true":
            return
        rc, _, err = docker(["network", "connect", NETWORK, HANDBOOK], timeout=30)
        if rc == 0 or "already exists" in err:
            log(f"{HANDBOOK} joined {NETWORK}")
        else:
            log(f"could not attach {HANDBOOK} to {NETWORK}: {err.strip()}")
        self.refresh(force=True)

    def in_subnet(self, ip):
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(a in n for n in self.subnets)

    def is_handbook(self, ip):
        """True when `ip` is the handbook container's devlab-net address. On a miss the network is
        re-read (at most every 2 s): the handbook may have been recreated or attached since."""
        if ip and ip == self.handbook_ip:
            return True
        self.refresh(force=True, min_age=2.0)
        return bool(ip) and ip == self.handbook_ip


LABNET = LabNet()


# --------------------------------------------------------------------------- progress
class Progress:
    def __init__(self, data_dir=DATA_DIR):
        self.path = os.path.join(data_dir, "progress.json")
        self.lock = threading.Lock()
        self.data = {"version": 1, "rooms": {}}
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("rooms"), dict):
                self.data = d
        except (OSError, ValueError):
            pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=1, sort_keys=True)
        os.replace(tmp, self.path)

    def room(self, rid):
        return self.data["rooms"].get(rid, {})

    def completed(self, rid):
        return bool(self.room(rid).get("completed"))

    def record_finish(self, rid, points, total, completed, tasks_passed):
        with self.lock:
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            r = self.data["rooms"].setdefault(rid, {})
            r["attempts"] = r.get("attempts", 0) + 1
            r["last_finished_at"] = now
            r["last_points"] = points
            r["total_points"] = total
            r["best_points"] = max(points, r.get("best_points", 0))
            r["tasks_passed"] = sorted(set(r.get("tasks_passed", [])) | set(tasks_passed))
            if completed and not r.get("completed"):
                r["completed"] = True
                r["completed_at"] = now
            self.save()
            return dict(r)


# --------------------------------------------------------------------------- sessions
class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class Session:
    def __init__(self, sid, room):
        self.sid, self.room = sid, room
        self.container = f"devlab-{sid}"
        self.state = "starting"            # starting -> ready | stopped
        self.created = self.last_seen = time.time()
        self.ip = ""
        self.term_token = secrets.token_hex(24)   # ttyd basic auth (-c lab:<token>); only nginx gets it
        self.closing = False               # set by _drop: no check runs once the lab is being removed
        self.lock = threading.RLock()      # one check at a time per lab; _drop takes it too
        self.tasks = {t["id"]: {"answers": {q["id"]: False for q in t.get("questions", [])},
                                "checks": {c["id"]: None for c in t.get("checks", [])},
                                "passed": False} for t in room["tasks"]}

    def touch(self):
        self.last_seen = time.time()

    def __repr__(self):                    # never the terminal token
        return f"<Session {self.sid} {self.room['id']} {self.state}>"

    def task_open(self, tid):
        for t in self.room["tasks"]:
            if t["id"] == tid:
                return True
            if not self.tasks[t["id"]]["passed"]:
                return False
        return False

    def current_task(self):
        return next((t["id"] for t in self.room["tasks"] if not self.tasks[t["id"]]["passed"]), None)

    def points(self):
        return sum(t.get("points", 0) for t in self.room["tasks"] if self.tasks[t["id"]]["passed"])

    def update_pass(self, tid):
        st = self.tasks[tid]
        st["passed"] = all(st["answers"].values()) and all(c is not None and c["pass"] for c in st["checks"].values())
        return st["passed"]

    def view(self):
        total = sum(t.get("points", 0) for t in self.room["tasks"])
        return {"session": self.sid, "room": self.room["id"], "state": self.state,
                "terminal": f"/lab-term/{self.sid}/", "current_task": self.current_task(),
                "points": self.points(), "total_points": total,
                "complete": self.current_task() is None,
                "idle_left": max(0, int(IDLE_SECONDS - (time.time() - self.last_seen))),
                "max_left": max(0, int(MAX_SECONDS - (time.time() - self.created))) if MAX_SECONDS else None,
                "tasks": {tid: {"passed": st["passed"], "open": self.task_open(tid),
                                "answers": dict(st["answers"]),
                                "checks": {cid: c for cid, c in st["checks"].items()}}
                          for tid, st in self.tasks.items()}}


class Controller:
    def __init__(self, rooms, progress):
        self.rooms, self.progress = rooms, progress
        self.sessions = {}
        self.lock = threading.RLock()
        self.stopping = False

    # ---- gating
    def room_open(self, rid):
        for ids in ordered_paths(self.rooms).values():
            if rid in ids:
                i = ids.index(rid)
                return i == 0 or self.progress.completed(ids[i - 1]) or self.progress.completed(rid)
        return False

    def blocker(self, rid):
        for ids in ordered_paths(self.rooms).values():
            if rid in ids and ids.index(rid) > 0:
                return ids[ids.index(rid) - 1]
        return None

    def room_list(self):
        active = {s.room["id"]: s.sid for s in self.sessions.values() if s.state != "stopped"}
        out = []
        for ids in ordered_paths(self.rooms).values():
            for rid in ids:
                r = public_room(self.rooms[rid])
                pr = self.progress.room(rid)
                r.update(locked=not self.room_open(rid), requires=None if self.room_open(rid) else self.blocker(rid),
                         completed=bool(pr.get("completed")), best_points=pr.get("best_points", 0),
                         session=active.get(rid))
                out.append(r)
        return out

    def session(self, sid):
        if not SID_RE.match(sid or ""):
            raise ApiError(404, "no-session", "Unknown session.")
        with self.lock:
            s = self.sessions.get(sid)
        if not s:
            raise ApiError(404, "no-session", "This lab session no longer exists (finished, reset, idle for 30 min or past its lifetime limit).")
        s.touch()
        return s

    def live_sessions(self):
        """Sessions that hold (or are starting) a lab machine; "stopped" ones do not."""
        with self.lock:
            return [s for s in self.sessions.values() if s.state != "stopped"]

    # ---- lifecycle
    def start(self, rid):
        room = self.rooms.get(rid)
        if not room:
            raise ApiError(404, "no-room", "Unknown room.")
        if not self.room_open(rid):
            raise ApiError(403, "locked", f"Finish '{self.rooms[self.blocker(rid)]['title']}' first.")
        with self.lock:
            if self.stopping:
                raise ApiError(503, "stopping", "The lab server is shutting down.")
            for s in list(self.sessions.values()):
                if s.room["id"] == rid and s.state == "stopped":
                    self.sessions.pop(s.sid, None)            # its machine is already gone
                elif s.room["id"] == rid:
                    s.touch()
                    return s                                  # one lab per room: resume it
            live = self.live_sessions()
            if len(live) >= MAX_LABS:                         # a stopped lab holds no machine, no slot
                names = ", ".join(s.room["title"] for s in live)
                raise ApiError(429, "limit", f"At most {MAX_LABS} labs run at once. Finish or reset one first ({names}).")
            sid = secrets.token_hex(6)
            s = Session(sid, room)
            self.sessions[sid] = s
        try:
            self._boot(s)
        except ApiError:
            self._drop(s)
            raise
        except Exception as e:                                  # noqa: BLE001 - report, clean up
            self._drop(s)
            raise ApiError(500, "start-failed", f"The lab did not start: {e}")
        return s

    def _boot(self, s):
        t0 = time.time()
        LABNET.attach_handbook()
        rc, _, err = run_lab(lab_run_argv(s.sid, s.room["id"]), timeout=90)
        if rc != 0:
            raise ApiError(500, "start-failed", "docker run failed: " + err.strip()[-400:])
        # 1. wait until systemd has finished booting
        state, deadline = "", time.time() + BOOT_TIMEOUT
        while time.time() < deadline:
            rc, out, _ = docker(["exec", s.container, "systemctl", "is-system-running", "--wait"], timeout=60)
            state = out.strip().splitlines()[-1] if out.strip() else ""
            if state in ("running", "degraded"):
                break
            time.sleep(0.5)
        else:
            raise ApiError(500, "boot-timeout", f"systemd did not finish booting in {BOOT_TIMEOUT}s (state: {state or 'unknown'}).")
        if state == "degraded":
            log(f"{s.container}: systemd is degraded")
        # 2. room setup: setup.sh as root, fed on stdin (nothing of it stays in the lab)
        self._exec_setup(s)
        # 3. the terminal
        rc, _, err = docker(["exec", "-d", s.container, *ttyd_argv(s.term_token)], timeout=30)
        if rc != 0:
            err = err.replace(s.term_token, "***")
            raise ApiError(500, "terminal-failed", "ttyd did not start: " + err.strip()[-300:])
        for _ in range(40):
            rc, _, _ = docker(["exec", s.container, "sh", "-c", "ss -Htln 'sport = :7681' | grep -q ."], timeout=15)
            if rc == 0:
                break
            time.sleep(0.25)
        else:
            raise ApiError(500, "terminal-failed", "ttyd is not listening on :7681.")
        rc, out, _ = docker(["inspect", "-f", '{{with index .NetworkSettings.Networks "devlab-net"}}{{.IPAddress}}{{end}}',
                             s.container], timeout=15)
        s.ip = out.strip()
        LABNET.refresh(force=True)
        s.state = "ready"
        s.touch()
        log(f"{s.container}: room {s.room['id']} ready in {time.time() - t0:.1f}s")

    def _exec_setup(self, s):
        """setup.sh runs as root, fed on stdin (`docker exec -i <lab> bash -s`), exactly like
        labs/test_rooms.py runs it, so the tested path is the served path. Nothing is left in the lab."""
        rc, out, err = exec_script(s.container, os.path.join(s.room["_dir"], "setup.sh"), SETUP_TIMEOUT)
        if rc != 0:
            tail = (out + err).strip().splitlines()[-3:]
            raise ApiError(500, "setup-failed", f"setup.sh exited {rc}: " + " | ".join(tail)[-400:])

    def _drop(self, s, blocking=True):
        """Remove the session and its lab. Takes s.lock, so a running check finishes first and no
        check starts on a container that is being removed (check() honours s.closing). The reaper
        passes blocking=False: when a check holds the lock it skips the lab and retries next round.
        Lock order is always s.lock -> self.lock (nothing takes them the other way round)."""
        if not s.lock.acquire(blocking=blocking):
            return False
        try:
            s.closing = True
            with self.lock:
                self.sessions.pop(s.sid, None)
            remove_container(s.container)
        finally:
            s.lock.release()
        LABNET.refresh(force=True)
        return True

    def answer(self, sid, qid, answer):
        s = self.session(sid)
        for t in s.room["tasks"]:
            for q in t.get("questions", []):
                if q["id"] == qid:
                    if not s.task_open(t["id"]):
                        raise ApiError(403, "task-locked", "Pass the earlier tasks first.")
                    if not isinstance(answer, str) or len(answer) > 500:
                        raise ApiError(400, "bad-answer", "The answer must be text (at most 500 characters).")
                    ok = hmac.compare_digest(answer_sha256(answer), q["answer_sha256"])
                    with s.lock:
                        if s.closing:
                            raise ApiError(404, "no-session", "This lab session no longer exists (finished or reset).")
                        s.tasks[t["id"]]["answers"][qid] = s.tasks[t["id"]]["answers"][qid] or ok
                        passed = s.update_pass(t["id"])
                    return {"question": qid, "task": t["id"], "correct": ok, "task_passed": passed,
                            "message": "Correct." if ok else "Not quite. Check the format and look again.",
                            **{"state": s.view()}}
        raise ApiError(404, "no-question", "Unknown question.")

    def check(self, sid, tid):
        s = self.session(sid)
        task = next((t for t in s.room["tasks"] if t["id"] == tid), None)
        if not task:
            raise ApiError(404, "no-task", "Unknown task.")
        if not s.task_open(tid):
            raise ApiError(403, "task-locked", "Pass the earlier tasks first.")
        results = []
        with s.lock:
            if s.closing:
                raise ApiError(404, "no-session", "This lab session no longer exists (finished or reset).")
            if s.state != "ready":
                raise ApiError(409, "not-ready", "The lab machine is not running. Reset it to get a fresh one.")
            for c in task.get("checks", []):
                rc, out, err = exec_script(s.container, os.path.join(s.room["_dir"], c["script"]), CHECK_TIMEOUT)
                lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
                reason = (lines[-1] if lines else ("passed" if rc == 0 else f"check exited {rc}"))[:300]
                res = {"pass": rc == 0, "reason": reason}
                s.tasks[tid]["checks"][c["id"]] = res
                results.append({"id": c["id"], "describe": c.get("describe", ""), **res})
            passed = s.update_pass(tid)
        s.touch()
        return {"task": tid, "results": results, "task_passed": passed,
                "questions_ok": all(s.tasks[tid]["answers"].values()), "state": s.view()}

    def finish(self, sid):
        s = self.session(sid)
        room = s.room
        total = sum(t.get("points", 0) for t in room["tasks"])
        with s.lock:                       # waits for a running check; a second Finish gets 404
            if s.closing:
                raise ApiError(404, "no-session", "This lab session no longer exists (finished or reset).")
            passed = [tid for tid, st in s.tasks.items() if st["passed"]]
            complete = len(passed) == len(room["tasks"])
            self._drop(s)
        rec = self.progress.record_finish(room["id"], s.points(), total, complete, passed)
        nxt = None
        ids = ordered_paths(self.rooms).get(room["path"], [])
        if room["id"] in ids and ids.index(room["id"]) + 1 < len(ids):
            nxt = ids[ids.index(room["id"]) + 1]
        log(f"{s.container}: finished room {room['id']} ({s.points()}/{total}, complete={complete})")
        return {"room": room["id"], "complete": complete, "points": s.points(), "total_points": total,
                "progress": rec, "next_room": nxt, "next_open": bool(nxt and self.room_open(nxt)),
                "walkthrough_html": markdown_html(room.get("walkthrough", "")),
                "source": room.get("source")}

    def reset(self, sid):
        s = self.session(sid)
        rid = s.room["id"]
        with s.lock:
            if s.closing:
                raise ApiError(404, "no-session", "This lab session no longer exists (finished or reset).")
            self._drop(s)
        log(f"{s.container}: reset")
        return self.start(rid)

    # ---- reaper and shutdown
    def reap(self):
        now = time.time()
        with self.lock:
            sessions = list(self.sessions.values())
        if not sessions:
            return
        live = devlab_containers()
        for s in sessions:
            idle = now - s.last_seen
            if MAX_SECONDS and s.state == "ready" and now - s.created > MAX_SECONDS:
                if self._drop(s, blocking=False):           # a running check: retry next round
                    log(f"{s.container}: reached the {MAX_SECONDS // 60} min lifetime limit, destroyed")
            elif s.state == "ready" and idle > IDLE_SECONDS:
                if self._drop(s, blocking=False):           # a running check: retry next round
                    log(f"{s.container}: idle for {int(idle // 60)} min, destroyed")
            elif s.state == "starting" and now - s.created > BOOT_TIMEOUT + SETUP_TIMEOUT + 60:
                if self._drop(s, blocking=False):
                    log(f"{s.container}: stuck while starting, destroyed")
            elif s.state == "ready" and live.get(s.container) != "running":
                if not s.lock.acquire(blocking=False):
                    continue
                try:
                    if s.closing or s.state != "ready":
                        continue
                    log(f"{s.container}: the lab machine stopped ({live.get(s.container, 'gone')})")
                    s.state = "stopped"                     # holds no MAX_LABS slot (live_sessions)
                    remove_container(s.container)
                finally:
                    s.lock.release()
            elif s.state == "stopped" and idle > IDLE_SECONDS:
                with self.lock:
                    self.sessions.pop(s.sid, None)

    def shutdown(self):
        """Full cleanup (SPEC): every devlab=1 container, then devlab-net itself."""
        with self.lock:
            self.stopping = True
            sessions = list(self.sessions.values())
            self.sessions.clear()
        names = {s.container for s in sessions} | set(devlab_containers())
        for n in sorted(names):
            remove_container(n)
        log(f"shutdown: removed {len(names)} lab container(s)")
        remove_network()


def remove_network():
    """Detach the handbook and this controller, then delete devlab-net (labs off = no lab network)."""
    rc, out, _ = docker(["network", "inspect", NETWORK, "--format",
                         "{{range .Containers}}{{.Name}}\n{{end}}"], timeout=20)
    if rc != 0:
        return
    for name in [n.strip() for n in out.splitlines() if n.strip()]:
        if name in (HANDBOOK, SELF) or name.startswith("devlab-"):
            docker(["network", "disconnect", "-f", NETWORK, name], timeout=30)
    rc, _, err = docker(["network", "rm", NETWORK], timeout=30)
    log(f"shutdown: removed network {NETWORK}" if rc == 0 else f"shutdown: {NETWORK} kept: {err.strip()}")


def remove_leftovers():
    """At start: remove EVERY container labelled devlab=1 (SPEC)."""
    names = sorted(devlab_containers())
    for n in names:
        remove_container(n)
    if names:
        log(f"start: removed {len(names)} leftover lab container(s): {', '.join(names)}")


# --------------------------------------------------------------------------- HTTP
ROUTES = [
    ("GET", re.compile(r"^/api/labs/health$"), "health"),
    ("GET", re.compile(r"^/api/labs/rooms$"), "rooms"),
    ("GET", re.compile(r"^/api/labs/progress$"), "progress"),
    ("GET", re.compile(r"^/api/labs/term-auth$"), "term_auth"),
    ("POST", re.compile(r"^/api/labs/rooms/([a-z0-9-]{2,63})/start$"), "start"),
    ("GET", re.compile(r"^/api/labs/sessions/([a-f0-9]{12})$"), "session"),
    ("POST", re.compile(r"^/api/labs/sessions/([a-f0-9]{12})/(answer|check|finish|reset|ping)$"), "session_post"),
]
CTL = None


def host_ok(value):
    host = (value or "").strip().lower()
    if not host:
        return False
    if host.startswith("["):
        name = host.split("]")[0] + "]"
    else:
        name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    return name in ALLOWED_HOSTS or name.endswith(".localhost")


def origin_ok(origin, host):
    if not origin:
        return True
    try:
        return urlsplit(origin).netloc.lower() == (host or "").strip().lower()
    except ValueError:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "devlab-controller"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):            # quiet: one line per request, no bodies
        if not self.path.endswith(("/health", "/ping", "/term-auth")):
            log(f"{self.command} {self.path.split('?')[0]} -> {args[1] if len(args) > 1 else ''}")

    def _send(self, status, obj=None, headers=None):
        body = b"" if obj is None else json.dumps(obj).encode("utf-8")
        self.send_response(status)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if obj is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _from_lab(self):
        """True when the request comes from a lab machine (directly, or through nginx on devlab-net).

        Any peer inside devlab-net is a lab unless it is exactly the handbook's (nginx's) devlab-net
        address: a lab that is still booting has no s.ip yet and may not be in lab_ips (refreshed
        every 15 s), so the subnet decides, not those lists. Only for a request that really came
        from nginx (on devlab-net or on the default network) is X-Lab-Via looked at: nginx sets it
        to the address the client reached nginx on, so a lab going through nginx is refused too."""
        LABNET.refresh()
        peer = self.client_address[0]
        with CTL.lock:
            own = {s.ip for s in CTL.sessions.values() if s.ip}
        if peer in own or peer in LABNET.lab_ips:
            return True
        if LABNET.in_subnet(peer) and not LABNET.is_handbook(peer):
            return True
        via = self.headers.get("X-Lab-Via", "")
        return bool(via and LABNET.in_subnet(via))

    def _guard(self, post):
        if self._from_lab():
            raise ApiError(403, "from-lab", "The lab API is not reachable from inside a lab machine.")
        host = self.headers.get("Host", "")          # nginx passes the browser's Host (also to term-auth)
        if not host_ok(host):
            raise ApiError(403, "bad-host", "Open the handbook at http://localhost:8173 or http://127.0.0.1:8173.")
        if not origin_ok(self.headers.get("Origin"), host) or self.headers.get("Sec-Fetch-Site", "") == "cross-site":
            raise ApiError(403, "cross-site", "Cross-site requests are refused.")
        if post and "application/json" not in self.headers.get("Content-Type", ""):
            raise ApiError(415, "json-only", "Send JSON (Content-Type: application/json).")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 16384:
            raise ApiError(413, "too-large", "Request body too large.")
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except ValueError:
            raise ApiError(400, "bad-json", "The body is not valid JSON.")
        if not isinstance(data, dict):
            raise ApiError(400, "bad-json", "Send a JSON object.")
        return data

    def _dispatch(self, method):
        path = urlsplit(self.path).path
        for m, rx, name in ROUTES:
            mt = rx.match(path)
            if mt and m == method:
                try:
                    self._guard(method == "POST")
                    if name == "term_auth":
                        return self._term_auth()
                    body = self._body() if method == "POST" else {}
                    status, obj = getattr(self, "r_" + name)(*mt.groups(), body=body)
                    return self._send(status, obj)
                except ApiError as e:
                    if name == "term_auth":
                        return self._send(e.status if e.status in (401, 403) else 403)
                    return self._send(e.status, {"error": e.code, "message": e.message})
                except Exception as e:                       # noqa: BLE001
                    log(f"error on {method} {path}: {e!r}")
                    return self._send(500, {"error": "internal", "message": "The controller hit an error; see `docker compose logs labs-controller`."})
        if any(rx.match(path) for _, rx, _ in ROUTES):
            return self._send(405, {"error": "method", "message": "Method not allowed."})
        return self._send(404, {"error": "not-found", "message": "No such API route."})

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    # ---- routes
    def r_health(self, body):
        rc, _, _ = docker(["image", "inspect", "-f", "{{.Id}}", IMAGE], timeout=15)
        n = len(CTL.live_sessions())
        return 200, {"ok": True, "rooms": len(CTL.rooms), "labs_running": n, "max_labs": MAX_LABS,
                     "idle_minutes": IDLE_SECONDS // 60, "image": IMAGE, "image_present": rc == 0}

    def r_rooms(self, body):
        with CTL.lock:
            return 200, {"rooms": CTL.room_list(), "max_labs": MAX_LABS}

    def r_progress(self, body):
        rooms = CTL.progress.data.get("rooms", {})
        return 200, {"rooms": rooms, "points": sum(r.get("best_points", 0) for r in rooms.values()),
                     "completed": sorted(r for r, v in rooms.items() if v.get("completed"))}

    def r_start(self, rid, body):
        s = CTL.start(rid)
        return 200, s.view()

    def r_session(self, sid, body):
        return 200, CTL.session(sid).view()

    def r_session_post(self, sid, action, body):
        if action == "answer":
            return 200, CTL.answer(sid, str(body.get("question", "")), body.get("answer"))
        if action == "check":
            return 200, CTL.check(sid, str(body.get("task", "")))
        if action == "finish":
            return 200, CTL.finish(sid)
        if action == "reset":
            return 200, CTL.reset(sid).view()
        s = CTL.session(sid)                       # ping: the page is open and the learner is active
        return 200, {"ok": True, "state": s.state, "idle_left": s.view()["idle_left"]}

    def _term_auth(self):
        """nginx auth_request for /lab-term/<sid>/...: only live sessions, never from a lab.
        On success it hands nginx this lab's ttyd credential in X-Lab-Auth; nginx sends it on as
        Authorization (auth_request_set, docker/nginx.conf) and never shows it to the browser."""
        m = re.match(r"^/lab-term/([a-f0-9]{12})/", self.headers.get("X-Original-URI", ""))
        if not m:
            return self._send(403)
        with CTL.lock:
            s = CTL.sessions.get(m.group(1))
        if not s or s.state != "ready" or s.closing:
            return self._send(403)
        s.touch()
        return self._send(204, headers={"X-Lab-Auth": basic_auth(s.term_token), "Cache-Control": "no-store"})


def main():
    global CTL
    rooms = load_rooms()
    log(f"loaded {len(rooms)} room(s) from {ROOMS_DIR}: {', '.join(rooms) or '-'}")
    remove_leftovers()
    LABNET.refresh(force=True)
    LABNET.attach_handbook()
    CTL = Controller(rooms, Progress())
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    httpd.daemon_threads = True

    def reaper():
        while not CTL.stopping:
            time.sleep(REAP_EVERY)
            try:
                CTL.reap()
                if CTL.sessions:
                    LABNET.attach_handbook()
            except Exception as e:                   # noqa: BLE001 - keep reaping
                log(f"reaper: {e!r}")

    threading.Thread(target=reaper, daemon=True).start()

    def stop(signum, _frame):
        log(f"signal {signum}: removing labs and stopping")
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log(f"listening on :{PORT} (max {MAX_LABS} labs, idle limit {IDLE_SECONDS // 60} min, "
        f"lifetime limit {(str(MAX_SECONDS // 60) + ' min') if MAX_SECONDS else 'off'})")
    try:
        httpd.serve_forever(poll_interval=0.5)
    finally:
        CTL.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
