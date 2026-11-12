#!/usr/bin/env python3
"""Live smoke test of the hands-on labs platform (Docker; nothing runs on the host itself).

    python3 labs/smoke_platform.py            # full run, about 3-6 minutes
    python3 labs/smoke_platform.py --no-build # reuse the images that are already built

What it does, in order (every lab scenario runs only inside lab containers):
   1. preflight: waits for a quiet minute without anyone else's lab containers (labs/test_rooms.py
      shares the label), removes an unused devlab-net that compose did not create, and leaves a fake
      leftover container (alpine, created, never started) for the controller to remove at start;
   2. builds the images (`docker compose --profile labs build`: handbook with its test gate,
      controller, lab base) and starts the profile;
   3. checks the controller through nginx (127.0.0.1:8173): health, rooms without answers/scripts/
      walkthroughs, the leftover is gone, the handbook joined devlab-net, cross-site / bad Host /
      non-JSON requests are refused;
   4. runs the pilot room 00-start-here: start -> the lab has exactly the SPEC options -> terminal
      page and websocket through nginx -> isolation from inside the lab (no internet, no controller,
      no terminals) -> task gating -> wrong answer and failing check -> reset -> solve.sh (test-only,
      fed from this folder) -> answers and checks pass -> path gating -> finish -> container gone;
   5. starts two labs, then `docker compose --profile labs down`: no devlab container, no devlab-net;
      then the profile again with one lab, and only the controller removed: its own shutdown removes
      the lab and devlab-net while the handbook keeps running;
   6. restarts the handbook alone (`docker compose up -d`): it serves, /api/labs/health answers
      200 {"ok": false, "labs": "off"} (JSON), every other /api/labs/ route answers 502, and no
      devlab-net is created;
   7. labs/clean.sh (with --all when this run created the progress volume): no devlab container,
      network or lab image remains, and the handbook container is still running.
Exit code 0 when every step passed.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LABS = Path(__file__).resolve().parent
ROOT = LABS.parent
BASE = "http://127.0.0.1:8173"
PILOT_DIR = LABS / "rooms" / "00-start-here"
PILOT = "l0-start-here"
VOLUME = "devops-handbook-labs-progress"
LEFTOVER = "devlab-smoke-leftover"
RESULTS = []


def log(msg):
    print(msg, flush=True)


def ok(cond, what, detail=""):
    RESULTS.append((bool(cond), what))
    log(f"  {'PASS' if cond else 'FAIL'}  {what}" + (f"  ({detail})" if detail and not cond else ""))
    return bool(cond)


def sh(*args, check=False, timeout=900, input_bytes=None, cwd=ROOT):
    p = subprocess.run(list(args), capture_output=True, timeout=timeout, cwd=cwd, input=input_bytes)
    out, err = p.stdout.decode(errors="replace"), p.stderr.decode(errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:4])}... exited {p.returncode}: {(err or out).strip()[-800:]}")
    return p.returncode, out, err


def http(method, path, body=None, headers=None, timeout=200):
    h = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    except (urllib.error.URLError, OSError) as e:
        return 0, {"error": str(e)}, b""
    try:
        return status, json.loads(raw.decode()), raw
    except ValueError:
        return status, None, raw


def ws_handshake(path):
    """Raw websocket upgrade through nginx; returns the HTTP status line."""
    key = "c21va2UtdGVzdC1rZXkxMg=="
    s = socket.create_connection(("127.0.0.1", 8173), timeout=10)
    s.sendall((f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:8173\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: tty\r\n"
               "Origin: http://127.0.0.1:8173\r\n\r\n").encode())
    data = s.recv(1024).decode(errors="replace")
    s.close()
    return data.split("\r\n", 1)[0]


def devlab_containers():
    return sh("docker", "ps", "-a", "--filter", "label=devlab=1", "--format", "{{.Names}}")[1].split()


def network_exists():
    return sh("docker", "network", "inspect", "devlab-net")[0] == 0


def wait_for(fn, timeout, step=1.0):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(step)
    return fn()


def controller_up():
    """/api/labs/health answers 200 either way; {"ok": true} only comes from the controller."""
    st, h, _ = http("GET", "/api/labs/health", timeout=5)
    return st == 200 and bool(h) and h.get("ok") is True


def foreign_labs():
    return [n for n in devlab_containers() if n != LEFTOVER]


def wait_quiet(quiet_s=45, timeout=1800):
    """Labs are a shared resource (labs/test_rooms.py starts labs too, and the controller removes
    every devlab=1 container when it starts and stops): wait until nobody else runs a lab."""
    end, since = time.time() + timeout, None
    while time.time() < end:
        if foreign_labs():
            since = None
        elif since is None:
            since = time.time()
        elif time.time() - since >= quiet_s:
            return True
        time.sleep(3)
    raise SystemExit(f"other lab containers kept running for {timeout // 60} min: {', '.join(foreign_labs())}")


def drop_hand_made_network():
    """compose refuses a devlab-net it did not create (no compose labels); remove it when unused."""
    if not network_exists():
        return
    rc, labels, _ = sh("docker", "network", "inspect", "-f", '{{index .Labels "com.docker.compose.network"}}', "devlab-net")
    if labels.strip():
        return
    rc, members, _ = sh("docker", "network", "inspect", "-f", "{{range .Containers}}{{.Name}} {{end}}", "devlab-net")
    if members.strip():
        raise RuntimeError(f"devlab-net was created outside compose and is in use by: {members.strip()}")
    sh("docker", "network", "rm", "devlab-net", check=True)
    log("  removed a devlab-net that compose did not create (compose refuses to adopt it)")


def preflight():
    log("1. preflight")
    if foreign_labs():
        log(f"  other lab containers are running ({', '.join(foreign_labs())}): waiting for a quiet minute")
    wait_quiet()
    return sh("docker", "volume", "inspect", VOLUME)[0] == 0


def start_profile(build):
    log("2. build and start the labs profile")
    if build:
        t0 = time.time()
        sh("docker", "compose", "--profile", "labs", "build", check=True, timeout=1800)
        log(f"  built handbook (test gate on), controller and lab base in {time.time() - t0:.0f}s")
    for ref in ("devops-handbook-lab:base", "devops-handbook-labs-controller"):
        ok(sh("docker", "image", "inspect", ref)[0] == 0, f"image {ref} exists")
    for attempt in range(5):
        wait_quiet(quiet_s=20)
        drop_hand_made_network()
        sh("docker", "rm", "-f", LEFTOVER)
        sh("docker", "create", "--name", LEFTOVER, "--label", "devlab=1", "--network", "none", "alpine:latest", "true", check=True)
        rc, out, err = sh("docker", "compose", "--profile", "labs", "up", "-d", timeout=600)
        if rc == 0:
            break
        if "incorrect label" not in err:
            raise RuntimeError(f"compose up failed: {err.strip()[-600:]}")
        log("  devlab-net was re-created by hand meanwhile; retrying")
    else:
        raise RuntimeError("compose up kept failing: devlab-net keeps being created outside compose")
    ok(True, "a fake leftover lab container existed when the controller started")
    health = wait_for(lambda: controller_up(), 90, 1)
    ok(health, "controller answers /api/labs/health through nginx")


def api_checks():
    log("3. controller, nginx and request guards")
    st, h, _ = http("GET", "/api/labs/health")
    ok(st == 200 and h.get("ok") and h.get("image_present") and h.get("max_labs") == 2, "health: ok, image present, max 2 labs", h)
    ok(LEFTOVER not in devlab_containers(), "the controller removed the leftover devlab=1 container at start")
    st, d, raw = http("GET", "/api/labs/rooms")
    ok(st == 200 and any(r["id"] == PILOT for r in d.get("rooms", [])), "rooms list includes the pilot")
    text = raw.decode()
    ok(not any(w in text for w in ("answer_sha256", "walkthrough", "solve.sh", "answers.test.json", "checks/t")),
       "rooms list has no answer hashes, walkthroughs or scripts")
    answers = json.loads((PILOT_DIR / "answers.test.json").read_text())
    ok("OPS-4127" not in text and answers["q-note-path"] not in text, "rooms list has no plaintext answers")
    rc, nets, _ = sh("docker", "inspect", "-f", "{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}", "devops-handbook")
    ok("devlab-net" in nets.split(), "the handbook container joined devlab-net while labs run", nets)
    ok(http("GET", "/api/labs/health", headers={"Origin": "http://evil.example"})[0] == 403, "cross-site Origin refused (403)")
    ok(http("GET", "/api/labs/health", headers={"Host": "evil.example"})[0] == 403, "foreign Host refused (403)")
    req = urllib.request.Request(BASE + f"/api/labs/rooms/{PILOT}/start", data=b"x=1", method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        urllib.request.urlopen(req, timeout=10)
        code = 200
    except urllib.error.HTTPError as e:
        code = e.code
    ok(code == 415, "form POST (no JSON) refused (415)")
    ok(http("GET", "/lab-term/000000000000/")[0] == 403, "terminal of an unknown session refused (403)")
    ok(http("GET", "/api/labs/term-auth", headers={"X-Original-URI": "/lab-term/000000000000/"})[0] == 404,
       "term-auth is not reachable through /api/labs/ (404): only nginx's auth_request uses it")


def inspect_lab(name):
    rc, out, _ = sh("docker", "inspect", name)
    return json.loads(out)[0] if rc == 0 else None


def pilot_run():
    log("4. pilot room through the API")
    room = json.loads((PILOT_DIR / "room.json").read_text())
    answers = json.loads((PILOT_DIR / "answers.test.json").read_text())
    st, v, _ = http("POST", f"/api/labs/rooms/{PILOT}/start", {})
    if not ok(st == 200 and v.get("state") == "ready", "start: lab ready", v):
        return None
    sid = v["session"]
    name = f"devlab-{sid}"
    info = inspect_lab(name)
    hc = info["HostConfig"]
    ok(info["Config"]["Labels"].get("devlab") == "1" and info["Config"]["Labels"].get("devlab.room") == PILOT, "labels devlab=1, devlab.room")
    ok(hc["Privileged"] is False and hc["CapDrop"] == ["ALL"] and len(hc["CapAdd"]) == 11, "not privileged; caps: drop ALL + 11 from the SPEC", hc["CapAdd"])
    ok(hc["Memory"] == 768 * 1024 * 1024 and hc["NanoCpus"] == 1_000_000_000 and hc["PidsLimit"] == 512, "memory 768m, 1 CPU, 512 pids")
    ok(hc["NetworkMode"] == "devlab-net" and not hc.get("PortBindings") and list(info["NetworkSettings"]["Networks"]) == ["devlab-net"],
       "only on devlab-net, no published ports")
    ok(hc["CgroupnsMode"] == "private" and "apparmor=unconfined" in hc["SecurityOpt"], "private cgroupns, SPEC security opts")
    ok(hc["RestartPolicy"]["Name"] in ("", "no"), "no restart policy")
    ok(sh("docker", "exec", name, "systemctl", "is-system-running")[1].strip() == "running", "systemd inside the lab: running (not degraded)")
    ok(sh("docker", "exec", name, "id", "-un", "lab")[0] == 0 and
       sh("docker", "exec", "-u", "lab", name, "sudo", "-n", "true")[0] == 0, "user lab with passwordless sudo")
    # terminal through nginx
    st, _, raw = http("GET", f"/lab-term/{sid}/")
    ok(st == 200 and b"ttyd" in raw, "terminal page served through nginx at /lab-term/<sid>/")
    ok(ws_handshake(f"/lab-term/{sid}/ws").startswith("HTTP/1.1 101"), "terminal websocket upgrade through nginx (101)")
    # isolation from inside the lab
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5", "https://example.com/")
    ok(out.strip() in ("000", ""), "no internet from the lab", out)
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5", "http://labs-controller:8080/api/labs/health")
    ok(out.strip() == "403", "controller refuses the lab directly (403)", out)
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5", "-H", "Host: 127.0.0.1:8173",
                    "http://devops-handbook:8080/api/labs/health")
    ok(out.strip() == "403", "controller refuses the lab through nginx (403)", out)
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5", "-H", "Host: 127.0.0.1:8173",
                    f"http://devops-handbook:8080/lab-term/{sid}/")
    ok(out.strip() == "403", "terminals refuse the lab through nginx (403)", out)
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5",
                    f"http://{name}:7681/")
    ok(out.strip() == "401", "ttyd needs the per-session credential on devlab-net (401 without it)", out)
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5",
                    "-H", "Host: 127.0.0.1:8173", "-H", "X-Lab-Via: 127.0.0.1",
                    "http://labs-controller:8080/api/labs/health")
    ok(out.strip() == "403", "controller refuses the lab directly even with a forged X-Lab-Via (403)", out)
    rc, out, _ = sh("docker", "exec", name, "curl", "-s", "-D", "-", "-o", "/dev/null", "-m", "5",
                    "-H", "Host: 127.0.0.1:8173", "-H", f"X-Original-URI: /lab-term/{sid}/",
                    "http://labs-controller:8080/api/labs/term-auth")
    ok(" 403" in out.split("\r\n", 1)[0] and "x-lab-auth" not in out.lower(),
       "term-auth refuses the lab and never hands it the credential", out[:200])
    # gating, wrong answers, failing checks
    st, r, _ = http("POST", f"/api/labs/sessions/{sid}/check", {"task": "t2"})
    ok(st == 403 and r.get("error") == "task-locked", "task 2 is locked until task 1 passes")
    st, r, _ = http("POST", f"/api/labs/sessions/{sid}/answer", {"question": "q-hostname", "answer": "wrong-host"})
    ok(st == 200 and r["correct"] is False, "a wrong answer is refused")
    st, r, _ = http("POST", f"/api/labs/sessions/{sid}/check", {"task": "t1"})
    ok(st == 200 and not r["task_passed"] and not r["results"][0]["pass"], "check t1 fails before the fix",
       r.get("results"))
    log(f"    reason shown: {r['results'][0]['reason'] if st == 200 else r}")
    rooms = {x["id"]: x for x in http("GET", "/api/labs/rooms")[1]["rooms"]}
    nxt = next((x for x in sorted(rooms.values(), key=lambda x: x["order"]) if x["path"] == "fresher" and x["order"] > 0), None)
    if nxt and not nxt["completed"]:
        ok(nxt["locked"], f"path gating: {nxt['id']} is locked before the pilot is finished")
    # reset: new machine, old one gone
    st, v2, _ = http("POST", f"/api/labs/sessions/{sid}/reset", {})
    ok(st == 200 and v2["session"] != sid and v2["state"] == "ready", "reset starts a fresh lab")
    ok(inspect_lab(name) is None, "reset destroyed the old lab container")
    sid = v2["session"]
    name = f"devlab-{sid}"
    # solve (test-only file, fed from this folder, never served)
    rc, out, err = sh("docker", "exec", "-i", name, "bash", "-s", input_bytes=(PILOT_DIR / "solve.sh").read_bytes())
    ok(rc == 0, "solve.sh applied inside the lab", err[-300:])
    for t in room["tasks"]:
        for q in t["questions"]:
            st, r, _ = http("POST", f"/api/labs/sessions/{sid}/answer", {"question": q["id"], "answer": answers[q["id"]]})
            ok(st == 200 and r["correct"], f"answer {q['id']} accepted", r)
        st, r, _ = http("POST", f"/api/labs/sessions/{sid}/check", {"task": t["id"]})
        ok(st == 200 and r["task_passed"], f"check {t['id']} passes after the fix", r.get("results") if r else st)
    st, v, _ = http("GET", f"/api/labs/sessions/{sid}")
    ok(st == 200 and v["complete"] and v["points"] == v["total_points"] == 100, "all tasks passed, 100/100 points", v.get("points") if v else st)
    st, f, _ = http("POST", f"/api/labs/sessions/{sid}/finish", {})
    ok(st == 200 and f["complete"] and f["points"] == 100 and "<p>" in f.get("walkthrough_html", ""),
       "finish: complete, 100 points, walkthrough returned")
    ok(inspect_lab(name) is None, "finish destroyed the lab container")
    st, p, _ = http("GET", "/api/labs/progress")
    ok(st == 200 and PILOT in p["completed"], "progress records the pilot as completed")
    if nxt:
        rooms = {x["id"]: x for x in http("GET", "/api/labs/rooms")[1]["rooms"]}
        ok(not rooms[nxt["id"]]["locked"], f"path gating: {nxt['id']} opens after the pilot")
    return nxt


def two_labs_then_down(nxt):
    log("5. two labs running, then `docker compose --profile labs down`")
    a = http("POST", f"/api/labs/rooms/{PILOT}/start", {})[1]
    started = [a.get("session")]
    if nxt:
        b = http("POST", f"/api/labs/rooms/{nxt['id']}/start", {})[1]
        started.append(b.get("session"))
    mine = [n for n in devlab_containers() if n in {f"devlab-{x}" for x in started if x}]
    ok(all(started) and len(mine) == len(started), f"{len(started)} labs running", devlab_containers())
    if len(mine) == 2:
        rc, out, _ = sh("docker", "exec", mine[0], "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5",
                        f"http://{mine[1]}:7681/")
        ok(out.strip() == "401", "a lab cannot open another lab's terminal directly (401)", out)
        rc, out, _ = sh("docker", "exec", mine[0], "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5",
                        "-u", "lab:", f"http://{mine[1]}:7681/token")
        ok(out.strip() == "401", "nor its /token with a guessed credential (401)", out)
    others = [n for n in foreign_labs() if n not in mine]
    if others:
        log(f"    note: someone else's lab containers are running too and will be removed by down: {', '.join(others)}")
    rc, _, err = sh("docker", "compose", "--profile", "labs", "down", timeout=300)
    ok(rc == 0, "compose --profile labs down", err[-300:])
    ok(devlab_containers() == [], "no devlab=1 container after down", devlab_containers())
    ok(not network_exists(), "devlab-net removed by down")
    ok(sh("docker", "inspect", "devops-handbook-labs")[0] != 0, "controller container removed")


def controller_stop_alone():
    log("5b. labs up again, one lab, then remove only the controller (its own shutdown cleans up)")
    sh("docker", "compose", "--profile", "labs", "up", "-d", check=True, timeout=600)
    ok(wait_for(lambda: controller_up(), 90, 1), "controller back up")
    st, v, _ = http("POST", f"/api/labs/rooms/{PILOT}/start", {})
    ok(st == 200 and v.get("state") == "ready" and f"devlab-{v.get('session')}" in devlab_containers(), "one lab running")
    rc, _, err = sh("docker", "compose", "--profile", "labs", "rm", "--stop", "--force", "labs-controller", timeout=300)
    ok(rc == 0, "compose rm --stop --force labs-controller", err[-300:])
    ok(devlab_containers() == [], "the controller removed every lab container on shutdown", devlab_containers())
    ok(not network_exists(), "the controller detached the handbook and deleted devlab-net on shutdown")
    rc, out, _ = sh("docker", "inspect", "-f", "{{.State.Running}}", "devops-handbook")
    ok(out.strip() == "true", "the handbook kept running")


def handbook_alone():
    log("6. the handbook alone (labs off)")
    sh("docker", "compose", "up", "-d", check=True, timeout=300)
    up = wait_for(lambda: http("GET", "/healthz", timeout=5)[0] == 200, 60, 1)
    ok(up, "handbook serves /healthz")
    st, _, raw = http("GET", "/", timeout=30)
    ok(st == 200 and b'id="lab-app"' in raw, "handbook page with the labs page is served")
    st, h, raw = http("GET", "/api/labs/health")
    ok(st == 200 and h == {"ok": False, "labs": "off"}, "/api/labs/health answers 200 {ok: false, labs: off} with the labs off", (st, raw[:120]))
    with urllib.request.urlopen(BASE + "/api/labs/health", timeout=10) as r:
        ctype = r.headers.get("Content-Type", "")
    ok(ctype.startswith("application/json"), "that answer is application/json", ctype)
    for path in ("/api/labs/rooms", "/api/labs/progress"):
        ok(http("GET", path)[0] == 502, f"{path} still answers 502 with the labs off")
    ok(http("POST", f"/api/labs/rooms/{PILOT}/start", {})[0] == 502, "starting a lab answers 502 with the labs off")
    ok(not network_exists(), "no devlab-net while the labs are off")


def clean(volume_existed):
    log("7. labs/clean.sh")
    args = [str(LABS / "clean.sh")] + ([] if volume_existed else ["--all"])
    rc, out, err = sh(*args, timeout=600)
    log("    " + "\n    ".join(out.strip().splitlines()))
    ok(rc == 0, "clean.sh exited 0", err[-300:])
    ok(devlab_containers() == [], "no devlab=1 container")
    ok(not network_exists(), "no devlab-net")
    for ref in ("devops-handbook-lab:base", "devops-handbook-labs-controller"):
        ok(sh("docker", "image", "inspect", ref)[0] != 0, f"image {ref} removed")
    ok(sh("docker", "images", "-aq", "--filter", "label=devops-handbook.labs")[1].strip() == "", "no image with the labs label left")
    if not volume_existed:
        ok(sh("docker", "volume", "inspect", VOLUME)[0] != 0, "progress volume created by this run removed (--all)")
    rc, out, _ = sh("docker", "inspect", "-f", "{{.State.Running}}", "devops-handbook")
    ok(out.strip() == "true", "the handbook container is still running")
    ok(sh("docker", "image", "inspect", "devops-handbook:local")[0] == 0, "the handbook image is untouched")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-build", action="store_true", help="reuse the built images")
    args = ap.parse_args()
    os.chdir(ROOT)
    t0 = time.time()
    volume_existed = preflight()
    nxt = None
    try:
        start_profile(not args.no_build)
        api_checks()
        nxt = pilot_run()
        two_labs_then_down(nxt)
        controller_stop_alone()
        handbook_alone()
    except Exception as e:                                     # noqa: BLE001 - always clean up
        ok(False, f"unexpected error: {e}")
        sh("docker", "compose", "--profile", "labs", "down", timeout=300)
        sh("docker", "compose", "up", "-d", timeout=300)
    finally:
        sh("docker", "rm", "-f", LEFTOVER)
    clean(volume_existed)
    failed = [w for good, w in RESULTS if not good]
    log(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed in {time.time() - t0:.0f}s")
    for w in failed:
        log(f"  FAILED: {w}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
