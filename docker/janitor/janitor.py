#!/usr/bin/env python3
"""Handbook janitor: removes only what THIS project created, on a timer (DOCKER.md, "Automatic cleanup").

Runs as the compose service `janitor` (no network, read-only, every capability dropped; it talks to the
Docker Engine API over /var/run/docker.sock), or by hand on the host:

    python3 docker/janitor/janitor.py --once --dry-run     show what would be removed, remove nothing
    python3 docker/janitor/janitor.py --once               one cleanup pass now
    python3 docker/janitor/janitor.py --once --now         ignore the keep windows (remove all of ours that is unused)
    python3 docker/janitor/janitor.py --labs-cache         only the labs' build cache, now (used by labs/clean.sh)

What counts as "ours" (anything else on the machine is never selected):
  * containers: label devlab=1 (lab machines) only. They are removed when the labs controller is not running
    (a crash left them behind) or when they outlive the lab lifetime limit plus an hour (safety net).
  * images: label devops-handbook.project or devops-handbook.labs (set by our Dockerfiles, including the verify VM
    runner labs/vm/Dockerfile, devops-handbook.project="vm"), or the labels
    Compose put on images it built for this compose project's own services. Untagged (superseded) builds
    go at once; the tagged lab images go after IMAGE_KEEP_DAYS without labs use. The running handbook image
    and this janitor's image are never removed, and nothing is ever force-removed: an image any
    container still uses (even a stopped one, even another project's) is kept.
  * build cache: every stage of our Dockerfiles starts with a no-op `RUN : devops-handbook-<stage>` or
    `RUN : devlab-<stage>`; that record is unique to our Dockerfiles, and so is every record built on
    top of it. Stage names are not used: BuildKit shares generic steps between Dockerfiles.
    Base-image records ("pulled from ...") and generic steps such as `WORKDIR /src` are shared with other
    projects and are never selected. A record goes once it has not been used for CACHE_KEEP_HOURS.
Time is never judged by an image's CREATED date for images someone else built: that is the publisher's
build time, not when it arrived here (a base image pulled today can show "3 weeks ago").
"""
import argparse
import http.client
import json
import os
import re
import socket
import sys
import time
import urllib.parse
from datetime import datetime, timezone

SOCK = os.environ.get("DOCKER_SOCK", "/var/run/docker.sock")


def _num(name, default):
    try:
        return max(0.0, float(os.environ.get(name, default)))
    except ValueError:
        return float(default)


EVERY_MIN = max(5.0, _num("JANITOR_EVERY_MINUTES", "60"))
CACHE_KEEP_H = _num("JANITOR_CACHE_KEEP_HOURS", "48")
IMAGE_KEEP_D = _num("JANITOR_IMAGE_KEEP_DAYS", "7")
LAB_MAX_H = _num("LABS_MAX_SECONDS", str(3 * 3600)) / 3600
STATE_FILE = os.environ.get("JANITOR_STATE", "/state/janitor.json")
DEFAULT_PROJECT = os.environ.get("JANITOR_COMPOSE_PROJECT", "troubleshooting")

CONTROLLER = "devops-handbook-labs"
HANDBOOK_IMAGE = "devops-handbook:local"
JANITOR_IMAGE = "devops-handbook-janitor:local"
OUR_SERVICES = {"handbook", "labs-controller", "lab-base", "janitor"}
OUR_LABELS = ("devops-handbook.project", "devops-handbook.labs")
LAB_TAGS = {"devops-handbook-lab:base", "devops-handbook-labs-controller:latest"}
GRACE_S = 10 * 60          # never touch anything younger than this (a build or start may be in progress)

# Build-cache roots that only our Dockerfiles produce. Every stage of ours starts with a no-op
# `RUN : devops-handbook-<stage>` / `RUN : devlab-<stage>` straight after FROM: that command is in the
# record's cache key, so no other Dockerfile shares the record, and everything after it in the stage
# descends from it. Stage names in "[stage N/M]" are NOT used: BuildKit shares a generic step such as
# `WORKDIR /src` between Dockerfiles and keeps whichever description came first. The export stage is
# FROM scratch (no shell), so its one COPY is matched by its source stage name.
CACHE_MARKS = re.compile(
    r"^mount / from exec /bin/sh -c : (?:devops-handbook-(?:build|serve|janitor|vm)|devlab-(?:base|controller))\s*$"
    r"|^\[[^\]]*\] COPY --from=handbook-build /src/index\.html /src/artifact\.html /$")
LAB_ROOTS = re.compile(r"^mount / from exec /bin/sh -c : devlab-(?:base|controller)\s*$")
TICK_S = 5 * 60            # how often the service looks for running labs between passes


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "janitor:", msg, flush=True)


# --------------------------------------------------------------------------- Docker Engine API
class _UnixConn(http.client.HTTPConnection):
    def __init__(self, path, timeout):
        super().__init__("localhost", timeout=timeout)
        self._path = path

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect(self._path)
        self.sock = s


def api(method, path, query=None, timeout=120):
    q = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in (query or {}).items()}
    url = path + ("?" + urllib.parse.urlencode(q) if q else "")
    conn = _UnixConn(SOCK, timeout)
    try:
        conn.request(method, url)
        r = conn.getresponse()
        body = r.read()
    finally:
        conn.close()
    data = None
    if body:
        try:
            data = json.loads(body)
        except ValueError:
            data = body.decode("utf-8", "replace")
    return r.status, data


def ts(value):
    """Docker timestamps (RFC 3339 with nanoseconds, or unix seconds) -> unix seconds; None if unknown."""
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.match(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?(Z|[+-]\d\d:\d\d)?", value)
    if not m or m.group(1).startswith("0001"):
        return None
    frac = (m.group(2) or ".0")[:7]
    tz = m.group(3) or "Z"
    dt = datetime.fromisoformat(m.group(1) + frac + ("+00:00" if tz == "Z" else tz))
    return dt.astimezone(timezone.utc).timestamp()


def snapshot():
    """Everything plan() needs, read from the Engine API."""
    _, containers = api("GET", "/containers/json", {"all": 1})
    _, images = api("GET", "/images/json", {"all": 0})
    st, df = api("GET", "/system/df", {"type": "build-cache"}, timeout=300)
    cache = ((df or {}).get("BuildCache") or []) if st == 200 else []
    project, self_image = DEFAULT_PROJECT, None
    st, me = api("GET", f"/containers/{socket.gethostname()}/json")      # inside the compose service
    if st == 200 and isinstance(me, dict):
        labels = (me.get("Config") or {}).get("Labels") or {}
        project = labels.get("com.docker.compose.project", project)
        self_image = me.get("Image")
    return {"containers": containers or [], "images": images or [], "cache": cache,
            "project": project, "self_image": self_image}



# --------------------------------------------------------------------------- what is ours
def image_is_ours(img, project):
    """Our Dockerfile labels, or the labels Compose sets on images it builds for our services. An image
    built FROM one of ours inherits our labels, so one that Compose built for another project is not ours."""
    labels = img.get("Labels") or {}
    compose_project = labels.get("com.docker.compose.project")
    if compose_project is not None and compose_project != project:
        return False
    if any(k in labels for k in OUR_LABELS):
        return True
    return compose_project == project and labels.get("com.docker.compose.service") in OUR_SERVICES


def parents(rec):
    """Parent record ids. Docker 29.2's API spells the key " Parents" (leading space); older ones "Parents",
    and before API 1.42 a single "Parent"."""
    for key in ("Parents", " Parents"):
        if rec.get(key):
            return list(rec[key])
    return [rec["Parent"]] if rec.get("Parent") else []


def our_cache_ids(records, roots=None):
    """Records with a step only our Dockerfiles have, plus every record that descends from one."""
    roots = roots or CACHE_MARKS
    children = {}
    for r in records:
        for p in parents(r):
            children.setdefault(p, []).append(r["ID"])
    ours = {r["ID"] for r in records if roots.search(r.get("Description") or "")}
    todo = list(ours)
    while todo:
        for c in children.get(todo.pop(), []):
            if c not in ours:
                ours.add(c)
                todo.append(c)
    return ours


def labs_running(containers):
    return any(("/" + CONTROLLER in (c.get("Names") or []) or (c.get("Labels") or {}).get("devlab") == "1")
               and c.get("State") == "running" for c in containers)


def cache_plan(records, now, keep_cache_h, roots=None):
    """Our records unused for keep_cache_h. BuildKit does not refresh a parent's LastUsedAt when a child is
    used, and cannot remove a record that still has children, so a record is selected only if every
    child of it is selected too."""
    ours = our_cache_ids(records, roots)
    pick = set()
    for r in records:
        if r["ID"] not in ours or r.get("InUse"):
            continue
        last = ts(r.get("LastUsedAt")) or ts(r.get("CreatedAt")) or now
        if now - last > keep_cache_h * 3600:
            pick.add(r["ID"])
    children = {}
    for r in records:
        for p in parents(r):
            children.setdefault(p, set()).add(r["ID"])
    changed = True
    while changed:
        changed = False
        for rid in list(pick):
            if not children.get(rid, set()) <= pick:
                pick.discard(rid)
                changed = True
    return [("cache", r["ID"], (r.get("Description") or "")[:70], f"unused for {keep_cache_h:g} h",
             int(r.get("Size") or 0)) for r in records if r["ID"] in pick]


def plan(snap, now, state, keep_cache_h=CACHE_KEEP_H, keep_image_d=IMAGE_KEEP_D, lab_max_h=LAB_MAX_H):
    """Pure: the list of (kind, id, label, reason) to remove. Never selects anything that is not ours."""
    actions = []
    project = snap["project"]
    ctl_running = any("/" + CONTROLLER in (c.get("Names") or []) and c.get("State") == "running"
                      for c in snap["containers"])
    labs = [c for c in snap["containers"] if (c.get("Labels") or {}).get("devlab") == "1"]
    labs_in_use = labs_running(snap["containers"])
    if labs_in_use:
        state["labs_last_seen"] = now

    # 1. lab machines (label devlab=1 only)
    for c in labs:
        age = now - (ts(c.get("Created")) or now)
        name = (c.get("Names") or ["?"])[0].lstrip("/")
        if age < GRACE_S:
            continue
        if not ctl_running:
            actions.append(("container", c["Id"], name, "lab machine left behind (the labs controller is not running)"))
        elif lab_max_h and age > (lab_max_h + 1) * 3600:
            actions.append(("container", c["Id"], name, f"lab machine older than the {lab_max_h:g} h lifetime limit"))

    # 2. images: superseded builds at once, tagged lab images after keep_image_d without labs use
    #    (keep_image_d None: no record of labs use is available, so tagged lab images are left alone)
    used = {c.get("ImageID") for c in snap["containers"]}
    protected = {snap.get("self_image")}
    for img in snap["images"]:
        tags = [t for t in (img.get("RepoTags") or []) if t != "<none>:<none>"]
        if (img["Id"] in protected or img["Id"] in used or HANDBOOK_IMAGE in tags or JANITOR_IMAGE in tags
                or not image_is_ours(img, project)):
            continue
        created = ts(img.get("Created")) or now          # ours: we built it, so CREATED is our build time
        if now - created < GRACE_S:
            continue
        if not tags:
            actions.append(("image", img["Id"], "untagged", "an older build of this project's image"))
        elif set(tags) <= LAB_TAGS and not labs_in_use and keep_image_d is not None:
            last = max(created, state.get("labs_last_seen") or 0)
            if now - last > keep_image_d * 86400:
                actions.append(("image", img["Id"], ",".join(tags), f"labs not used for {keep_image_d:g} days"))

    # 3. build cache records of our Dockerfiles, unused for keep_cache_h
    actions += cache_plan(snap["cache"], now, keep_cache_h)
    return actions


# --------------------------------------------------------------------------- doing it
def execute(actions, dry):
    done = freed = 0
    for a in actions:
        kind, oid, label, reason = a[:4]
        if dry:
            log(f"would remove {kind} {oid[:19]} {label} ({reason})")
            continue
        if kind == "container":
            st, _ = api("DELETE", f"/containers/{oid}", {"force": 1, "v": 1})
            ok = st in (204, 404)
        elif kind == "image":
            st, _ = api("DELETE", f"/images/{oid}")       # never force: in use anywhere -> 409, kept
            ok = st in (200, 404)
        else:
            continue                                      # cache is pruned below, leaves first
        if ok:
            done += 1
            log(f"removed {kind} {oid[:19]} {label} ({reason})")
        else:
            log(f"kept {kind} {oid[:19]} {label}: Docker answered {st} (still in use?)")
    ids = [a[1] for a in actions if a[0] == "cache"]
    if ids and dry:
        size = sum(a[4] for a in actions if a[0] == "cache")
        log(f"would prune {len(ids)} build cache record(s) of this project, about {size / 1e9:.2f} GB")
    elif ids:
        left, errors = set(ids), {}
        for _ in range(8):                                # leaves first: a parent goes once its children have
            before = len(left)
            for oid in list(left):
                st, body = api("POST", "/build/prune", {"all": 1, "filters": {"id": [oid]}}, timeout=300)
                if st == 200:
                    for gone in (body or {}).get("CachesDeleted") or []:
                        left.discard(gone)
                    freed += int((body or {}).get("SpaceReclaimed") or 0)
                else:
                    errors[oid] = f"{st} {str(body)[:120]}"
            if not left or len(left) == before:
                break
        done += len(ids) - len(left)
        log(f"pruned {len(ids) - len(left)} build cache record(s) of this project, {freed / 1e9:.2f} GB freed"
            + (f"; {len(left)} not removed" if left else ""))
        for oid in sorted(left)[:5]:
            log(f"  not removed: cache {oid[:19]}: " + (f"Docker answered {errors[oid]}" if oid in errors
                else "Docker kept it (in use by a build, or it still has children)"))
    return done


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, STATE_FILE)
    except OSError:
        pass                                              # host runs without /state: Created is the fallback


def one_pass(dry=False, now_mode=False):
    state = load_state()
    persistent = os.path.isdir(os.path.dirname(STATE_FILE) or ".")
    now = time.time()
    snap = snapshot()
    if now_mode:
        kw = {"keep_cache_h": 0, "keep_image_d": 0}
    elif not persistent:                                  # a host run has no record of labs use: leave lab images
        kw = {"keep_image_d": None}
    else:
        kw = {}
    actions = plan(snap, now, state, **kw)
    state["last_pass"] = now
    if persistent and not dry:
        save_state(state)
    if not actions:
        log("nothing of this project to remove")
        return 0
    return execute(actions, dry)


def note_labs_use():
    """Between passes: remember when labs were last seen running (a cheap filtered container list)."""
    st, running = api("GET", "/containers/json", {"filters": {"status": ["running"]}}, timeout=30)
    if st == 200 and labs_running(running or []):
        state = load_state()
        state["labs_last_seen"] = time.time()
        save_state(state)


def labs_cache_now(dry):
    """labs/clean.sh: remove the labs' build cache (records under the `: devlab-*` roots) now."""
    st, df = api("GET", "/system/df", {"type": "build-cache"}, timeout=300)
    records = ((df or {}).get("BuildCache") or []) if st == 200 else []
    actions = cache_plan(records, time.time(), 0, LAB_ROOTS)
    if not actions:
        log("no build cache of the labs to remove")
        return 0
    return execute(actions, dry)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--once", action="store_true", help="one pass, then exit (default: a pass every "
                    f"{EVERY_MIN} min)")
    ap.add_argument("--dry-run", "-n", action="store_true", help="print what would be removed, remove nothing")
    ap.add_argument("--now", action="store_true", help="ignore the keep windows")
    ap.add_argument("--labs-cache", action="store_true", help="only remove the labs' build cache, now, then exit")
    a = ap.parse_args(argv)
    if not os.path.exists(SOCK):
        log(f"no Docker socket at {SOCK}")
        return 1
    if a.labs_cache:
        try:
            labs_cache_now(a.dry_run)
            return 0
        except Exception as e:                            # noqa: BLE001
            log(f"failed: {e!r}")
            return 1
    log(f"keep: build cache {CACHE_KEEP_H:g} h, lab images {IMAGE_KEEP_D:g} days, labs lifetime "
        f"{LAB_MAX_H:g} h; pass every {EVERY_MIN:g} min" + (" (dry run)" if a.dry_run else ""))
    time.sleep(0 if a.once else 120)                      # let `up --build` finish replacing containers
    while True:
        try:
            one_pass(a.dry_run, a.now)
        except Exception as e:                            # noqa: BLE001 - keep going next round
            log(f"pass failed: {e!r}")
            if a.once:
                return 1
        if a.once:
            return 0
        deadline = time.time() + EVERY_MIN * 60
        while time.time() < deadline:                     # look for running labs every 5 min
            time.sleep(max(1.0, min(TICK_S, deadline - time.time())))
            try:
                note_labs_use()
            except Exception as e:                        # noqa: BLE001
                log(f"labs check failed: {e!r}")


if __name__ == "__main__":
    sys.exit(main())
