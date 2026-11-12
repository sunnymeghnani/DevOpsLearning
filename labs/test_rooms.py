#!/usr/bin/env python3
"""Room tests for the hands-on labs (see labs/SPEC.md, "Room test").

For every room in labs/rooms/<NN-id>/ this script:
  1. validates room.json (format, ids, hashes, sizes, files);
  2. starts a lab with EXACTLY the docker run options from SPEC.md;
  3. waits for systemd;
  4. runs setup.sh twice (it must be idempotent and fast);
  5. asserts that every check FAILS;
  6. runs solve.sh;
  7. asserts that every check PASSES;
  8. verifies every answer hash against answers.test.json
     (and against "ANSWER <qid>=<value>" lines printed by solve.sh, if any);
  9. destroys the lab (always, also on errors and Ctrl-C).

Scripts are fed to `docker exec -i <lab> bash -s` on stdin, so they work
whether the controller pipes them or copies them in.

Usage:
  python3 labs/test_rooms.py                 # all rooms
  python3 labs/test_rooms.py 03 07-text-tools # some rooms (prefix match)
  python3 labs/test_rooms.py -j 2             # two labs at a time (SPEC max)

Needs: docker, the image devops-handbook-lab:base, and the internal network
devlab-net with compose's labels, so a later `docker compose --profile labs up`
adopts it instead of failing with "incorrect label" (see DOCKER.md):
  docker network create --internal --label com.docker.compose.project=troubleshooting \
    --label com.docker.compose.network=devlab-net devlab-net
Do not run this while the labs are in use: the controller removes every devlab=1
container when it starts and stops. Nothing runs on the host except the docker CLI.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

LABS = Path(__file__).resolve().parent
ROOMS = LABS / "rooms"
IMAGE = "devops-handbook-lab:base"
NETWORK = "devlab-net"
SETUP_BUDGET_S = 10.0
BOOT_TIMEOUT_S = 90
SCRIPT_TIMEOUT_S = 120

_live: set[str] = set()
_live_lock = threading.Lock()
_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def normalise(answer: str) -> str:
    """SPEC: lower-case, trimmed, inner whitespace collapsed."""
    return " ".join(answer.strip().lower().split())


def sha256(answer: str) -> str:
    return hashlib.sha256(normalise(answer).encode()).hexdigest()


def run_args(session: str, room_id: str) -> list[str]:
    """The ONLY way a lab is started (SPEC.md, 'Lab machine')."""
    return [
        "docker", "run", "-d", "-t", "--name", f"devlab-{session}", "--hostname", "lab",
        "--label", "devlab=1", "--label", f"devlab.room={room_id}",
        "--cgroupns=private", "--tmpfs", "/run", "--tmpfs", "/run/lock", "--tmpfs", "/tmp",
        "--cap-drop", "ALL", "--cap-add", "SYS_ADMIN", "--cap-add", "CHOWN",
        "--cap-add", "DAC_OVERRIDE", "--cap-add", "FOWNER",
        "--cap-add", "SETUID", "--cap-add", "SETGID", "--cap-add", "KILL",
        "--cap-add", "NET_BIND_SERVICE", "--cap-add", "SYS_CHROOT",
        "--cap-add", "AUDIT_WRITE", "--cap-add", "NET_RAW",
        "--security-opt", "apparmor=unconfined",
        "--memory", "768m", "--cpus", "1", "--pids-limit", "512",
        "--network", NETWORK,
        "--entrypoint", "sh", IMAGE, "-c",
        "mount -o remount,rw /sys/fs/cgroup && exec /sbin/init",
    ]


def destroy(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
    with _live_lock:
        _live.discard(name)


def exec_script(name: str, script: Path, timeout: int = SCRIPT_TIMEOUT_S):
    """Run a room script inside the lab as root, fed on stdin."""
    with script.open("rb") as fh:
        t0 = time.monotonic()
        try:
            p = subprocess.run(["docker", "exec", "-i", name, "bash", "-s"], stdin=fh,
                               capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {timeout}s", time.monotonic() - t0
    return (p.returncode, p.stdout.decode(errors="replace"),
            p.stderr.decode(errors="replace"), time.monotonic() - t0)


def wait_for_systemd(name: str) -> str:
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    state = ""
    while time.monotonic() < deadline:
        p = subprocess.run(["docker", "exec", name, "systemctl", "is-system-running"],
                           capture_output=True, text=True)
        state = p.stdout.strip()
        if state in ("running", "degraded"):
            return state
        time.sleep(1)
    raise RuntimeError(f"systemd did not finish booting (last state: {state or 'none'})")


# ---------------------------------------------------------------- validation
def validate_room(room_dir: Path) -> tuple[dict, dict, list[str]]:
    """Static checks of room.json and its files. Returns (room, answers, problems)."""
    problems: list[str] = []
    room = json.loads((room_dir / "room.json").read_text())
    answers = json.loads((room_dir / "answers.test.json").read_text())
    for key in ("id", "title", "level", "map_node", "path", "order", "minutes", "difficulty",
                "source", "brief", "tasks", "walkthrough"):
        if key not in room:
            problems.append(f"room.json: missing '{key}'")
    src = room.get("source", {})
    if not (src.get("title") and str(src.get("url", "")).startswith("https://")
            and src.get("note") == "adapted"):
        problems.append("room.json: source needs title, https url and note 'adapted'")
    m = re.match(r"(\d\d)-(.+)$", room_dir.name)
    if not m or room.get("order") != int(m.group(1)):
        problems.append("room.json: 'order' does not match the directory number")
    for f in ("setup.sh", "solve.sh"):
        if not (room_dir / f).is_file():
            problems.append(f"missing {f}")
    tasks = room.get("tasks", [])
    if not 1 <= len(tasks) <= 3:
        problems.append("room.json: needs 1-3 tasks")
    qids: list[str] = []
    for t in tasks:
        if len(t.get("hints", [])) != 2:
            problems.append(f"{t.get('id')}: needs exactly 2 hints")
        qs = t.get("questions", [])
        if not 1 <= len(qs) <= 2:
            problems.append(f"{t.get('id')}: needs 1-2 questions")
        for q in qs:
            qids.append(q["id"])
            if not re.fullmatch(r"[0-9a-f]{64}", q.get("answer_sha256", "")):
                problems.append(f"{q['id']}: answer_sha256 is not a sha256 hex digest")
            if q["id"] not in answers:
                problems.append(f"{q['id']}: no entry in answers.test.json")
        if not t.get("checks"):
            problems.append(f"{t.get('id')}: has no checks")
        for c in t.get("checks", []):
            if not (room_dir / c["script"]).is_file():
                problems.append(f"{t.get('id')}: missing {c['script']}")
        words = len(t.get("text", "").split())
        if not 40 <= words <= 140:
            problems.append(f"{t.get('id')}: task text is {words} words (aim 60-120)")
    if len(set(qids)) != len(qids):
        problems.append("room.json: question ids must be unique within the room")
    words = len(room.get("brief", "").split())
    if not 70 <= words <= 170:
        problems.append(f"brief is {words} words (aim 80-150)")
    # plaintext answers must not sit in room.json as a field value
    blob = json.dumps(room)
    for qid, ans in answers.items():
        if f'"{ans}"' in blob:
            problems.append(f"{qid}: plaintext answer appears as a value in room.json")
    if "solve.sh" in blob or "answers.test.json" in blob:
        problems.append("room.json mentions solve.sh/answers.test.json (never served)")
    return room, answers, problems


# ---------------------------------------------------------------- one room
def test_room(room_dir: Path) -> tuple[str, bool, list[str]]:
    lines: list[str] = []
    ok = True

    def bad(msg: str) -> None:
        nonlocal ok
        ok = False
        lines.append(f"  FAIL {msg}")

    try:
        room, answers, problems = validate_room(room_dir)
    except Exception as exc:  # noqa: BLE001
        return room_dir.name, False, [f"  FAIL cannot read room: {exc}"]
    for p in problems:
        bad(p)

    checks = [(t["id"], c["id"], room_dir / c["script"]) for t in room["tasks"] for c in t["checks"]]
    session = f"t{uuid.uuid4().hex[:10]}"
    name = f"devlab-{session}"
    try:
        p = subprocess.run(run_args(session, room["id"]), capture_output=True, text=True)
        if p.returncode != 0:
            bad(f"docker run failed: {p.stderr.strip()}")
            return room_dir.name, False, lines
        with _live_lock:
            _live.add(name)
        state = wait_for_systemd(name)
        lines.append(f"  lab {name} booted ({state})")

        for attempt in (1, 2):
            rc, out, err, dt = exec_script(name, room_dir / "setup.sh")
            if rc != 0:
                bad(f"setup.sh run {attempt} exited {rc}: {(err or out).strip()[-400:]}")
                return room_dir.name, False, lines
            lines.append(f"  setup.sh run {attempt}: {dt:.1f}s")
            if dt > SETUP_BUDGET_S:
                bad(f"setup.sh run {attempt} took {dt:.1f}s (budget {SETUP_BUDGET_S:.0f}s)")

        for tid, cid, script in checks:
            rc, out, err, _ = exec_script(name, script)
            reason = out.strip().splitlines()[-1] if out.strip() else ""
            if rc == 0:
                bad(f"{tid}/{cid} PASSED before solve.sh: {reason}")
            else:
                lines.append(f"  before: {tid}/{cid} fails as expected: {reason}")
            if not reason:
                bad(f"{tid}/{cid} printed no reason line")
            elif len(out.strip().splitlines()) > 1:
                bad(f"{tid}/{cid} printed more than one line")

        rc, out, err, dt = exec_script(name, room_dir / "solve.sh")
        if rc != 0:
            bad(f"solve.sh exited {rc}: {(err or out).strip()[-600:]}")
        lines.append(f"  solve.sh: {dt:.1f}s")
        printed = dict(re.findall(r"^ANSWER (\S+?)=(.*)$", out, re.M))

        for tid, cid, script in checks:
            rc, out, err, _ = exec_script(name, script)
            reason = out.strip().splitlines()[-1] if out.strip() else ""
            if rc != 0:
                bad(f"{tid}/{cid} still FAILS after solve.sh: {reason} {err.strip()[-300:]}")
            else:
                lines.append(f"  after:  {tid}/{cid} passes: {reason}")

        for t in room["tasks"]:
            for q in t["questions"]:
                expected = answers.get(q["id"])
                if expected is None:
                    continue
                if sha256(expected) != q["answer_sha256"]:
                    bad(f"{q['id']}: hash does not match answers.test.json")
                if q["id"] in printed and normalise(printed[q["id"]]) != normalise(expected):
                    bad(f"{q['id']}: solve.sh found '{printed[q['id']]}', answers.test.json says '{expected}'")
        lines.append(f"  answers: {len(answers)} checked"
                     + (f" ({len(printed)} re-derived on the lab by solve.sh)" if printed else ""))
    except Exception as exc:  # noqa: BLE001
        bad(f"error: {exc}")
    finally:
        destroy(name)
    return room_dir.name, ok, lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rooms", nargs="*", help="room directory names or prefixes (default: all)")
    ap.add_argument("-j", "--jobs", type=int, default=1, help="labs in parallel (max 2)")
    args = ap.parse_args()

    if subprocess.run(["docker", "network", "inspect", NETWORK], capture_output=True).returncode:
        print(f"network {NETWORK} is missing: docker network create --internal "
              f"--label com.docker.compose.project=troubleshooting "
              f"--label com.docker.compose.network={NETWORK} {NETWORK}")
        return 2
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode:
        print(f"image {IMAGE} is missing: build labs/base first")
        return 2

    dirs = sorted(d for d in ROOMS.iterdir() if d.is_dir() and (d / "room.json").exists())
    if args.rooms:
        dirs = [d for d in dirs if any(d.name.startswith(r) for r in args.rooms)]
    if not dirs:
        print("no rooms selected")
        return 2

    results = []
    jobs = max(1, min(2, args.jobs))
    try:
        with cf.ThreadPoolExecutor(max_workers=jobs) as pool:
            futs = {pool.submit(test_room, d): d for d in dirs}
            for fut in cf.as_completed(futs):
                name, ok, lines = fut.result()
                results.append((name, ok))
                log(f"{'PASS' if ok else 'FAIL'} {name}\n" + "\n".join(lines))
    except KeyboardInterrupt:
        log("interrupted")
    finally:
        with _live_lock:
            leftovers = list(_live)
        for n in leftovers:
            destroy(n)

    results.sort()
    log("\nSummary")
    for name, ok in results:
        log(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 0 if results and all(ok for _, ok in results) and len(results) == len(dirs) else 1


if __name__ == "__main__":
    sys.exit(main())
