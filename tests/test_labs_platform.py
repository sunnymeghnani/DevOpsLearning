"""Hands-on labs platform: static wiring checks only (no Docker, nothing is started).

Covers compose.yaml, docker/nginx.conf, the controller's lab options and API rules, the base
image, labs/clean.sh, and the generated pages: the labs page is wired in, and no answer, answer
hash, solve script, check script or walkthrough reaches index.html / artifact.html.
The live test is labs/smoke_platform.py; the per-room test is labs/test_rooms.py.
"""
import base64
import contextlib
import hashlib
import html
import http.client
import importlib.util
import io
import json
import re
import shlex
import shutil
import subprocess
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABS = ROOT / "labs"
ROOMS = LABS / "rooms"


def load_controller():
    spec = importlib.util.spec_from_file_location("labs_controller", LABS / "controller" / "controller.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def service_block(compose, name):
    """Text of one top-level service in compose.yaml (2-space indented keys)."""
    m = re.search(rf"^  {re.escape(name)}:\n(.*?)(?=^  \S|^\S|\Z)", compose, re.M | re.S)
    return m.group(1) if m else ""


def room_dirs():
    return sorted(d for d in ROOMS.iterdir() if (d / "room.json").is_file()) if ROOMS.is_dir() else []


class ComposeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "compose.yaml"
        if not path.is_file():   # the Docker build context leaves compose.yaml out
            raise unittest.SkipTest("compose.yaml is not in this build context")
        cls.compose = path.read_text()

    def test_handbook_has_no_profile_and_keeps_its_hardening(self):
        hb = service_block(self.compose, "handbook")
        self.assertNotIn("profiles:", hb)
        for needle in ('"127.0.0.1:8173:8080"', "read_only: true", "- ALL", "no-new-privileges:true",
                       "restart: unless-stopped", "container_name: devops-handbook"):
            self.assertIn(needle, hb)
        # no lab network in the handbook's static config: the controller attaches it while labs run,
        # so with the labs off there is no devlab-net at all (SPEC "Full cleanup")
        self.assertNotIn("devlab-net", re.sub(r"#.*", "", hb))

    def test_controller_service(self):
        c = service_block(self.compose, "labs-controller")
        self.assertIn('profiles: ["labs"]', c)
        self.assertIn('restart: "no"', c)
        self.assertIn("/var/run/docker.sock:/var/run/docker.sock", c)
        self.assertIn("labs-progress:/data", c)
        self.assertIn("image: devops-handbook-labs-controller", c)
        self.assertIn("dockerfile: controller/Dockerfile", c)
        self.assertRegex(c, r"networks:\n\s+- default\n\s+- devlab-net")
        self.assertNotIn("ports:", c)                 # reachable only through the handbook's nginx
        self.assertNotIn("privileged", re.sub(r"#.*", "", c))
        for needle in ("read_only: true", "- ALL", "no-new-privileges:true", "stop_grace_period"):
            self.assertIn(needle, c)

    def test_lab_image_is_build_only(self):
        b = service_block(self.compose, "lab-base")
        self.assertIn('profiles: ["labs"]', b)
        self.assertIn("image: devops-handbook-lab:base", b)
        self.assertIn("context: labs/base", b)
        self.assertIn("scale: 0", b)                  # compose builds it but never runs it

    def test_network_and_volume(self):
        net = self.compose[self.compose.index("\nnetworks:"):]
        self.assertRegex(net, r"devlab-net:\n\s+name: devlab-net\n\s+internal: true")
        self.assertIn("name: devops-handbook-labs-progress", self.compose)
        self.assertNotIn("privileged: true", self.compose)


class NginxWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conf = (ROOT / "docker" / "nginx.conf").read_text()

    def test_resolver_and_variables_so_nginx_starts_without_labs(self):
        self.assertIn("resolver 127.0.0.11 valid=10s", self.conf)
        self.assertIn("set $labs_ctl labs-controller;", self.conf)
        self.assertIn("proxy_pass http://$labs_ctl:8080;", self.conf)
        # no literal upstream host names that nginx would resolve at start-up
        literal = re.findall(r"proxy_pass\s+http://(?!\$)([^;]+);", self.conf)
        self.assertEqual(literal, [])
        self.assertNotIn("upstream ", self.conf)

    def test_api_and_terminal_routes(self):
        self.assertIn("location /api/labs/ {", self.conf)
        self.assertIn('location ~ "^/lab-term/([a-f0-9]{12})/(.*)$" {', self.conf)
        self.assertIn("set $lab_host devlab-$1;", self.conf)
        self.assertIn("proxy_pass http://$lab_host:7681/$lab_path$is_args$args;", self.conf)
        self.assertIn("proxy_set_header Upgrade $http_upgrade;", self.conf)
        self.assertIn("proxy_set_header Connection $lab_connection;", self.conf)
        self.assertIn("auth_request /_lab_term_auth;", self.conf)
        self.assertIn("proxy_set_header X-Lab-Via $server_addr;", self.conf)
        self.assertIn("location = /healthz", self.conf)       # the health check is unchanged

    def block(self, header):
        """Text of one `location ... {` block (4-space indented, closed by a 4-space `}`)."""
        i = self.conf.index(header)
        return self.conf[i:self.conf.index("\n    }", i)]

    def test_terminal_gets_the_ttyd_credential_from_the_controller(self):
        term = self.block('location ~ "^/lab-term/([a-f0-9]{12})/(.*)$" {')
        self.assertIn("auth_request /_lab_term_auth;", term)
        self.assertIn("auth_request_set $lab_auth $upstream_http_x_lab_auth;", term)
        # proxy_set_header replaces the client's Authorization: a client-supplied one never reaches ttyd
        self.assertIn("proxy_set_header Authorization $lab_auth;", term)
        self.assertEqual(len(re.findall(r"proxy_set_header Authorization", term)), 1)
        self.assertIn("proxy_set_header Upgrade $http_upgrade;", term)      # same location: the websocket too
        self.assertIn("proxy_hide_header WWW-Authenticate;", term)
        auth = self.block("location = /_lab_term_auth {")
        self.assertIn("internal;", auth)
        self.assertIn('proxy_set_header Authorization "";', auth)            # nor to the controller
        # the credential endpoint is not reachable through /api/labs/, and its header never leaks
        self.assertRegex(self.conf, r"location = /api/labs/term-auth \{\s+return 404;\s+\}")
        self.assertIn("proxy_hide_header X-Lab-Auth;", self.block("location /api/labs/ {"))

    def test_health_says_labs_off_instead_of_502(self):
        # the page probes /api/labs/health on every load: with the labs off it gets a JSON answer
        health = self.block("location = /api/labs/health {")
        self.assertIn("proxy_pass http://$labs_ctl:8080;", health)
        self.assertIn("proxy_set_header X-Lab-Via $server_addr;", health)   # labs are still refused
        self.assertIn("proxy_hide_header X-Lab-Auth;", health)
        self.assertIn("error_page 502 504 = @labs_off;", health)
        self.assertNotIn("proxy_intercept_errors", self.conf)              # the controller's own answers pass
        off = self.block("location @labs_off {")
        self.assertIn("default_type application/json;", off)
        self.assertIn("""return 200 '{"ok":false,"labs":"off"}\\n';""", off)
        # every other /api/labs/ route keeps answering 502 with the labs off
        self.assertEqual(len(re.findall(r"error_page", self.conf)), 1)
        self.assertNotIn("error_page", self.block("location /api/labs/ {"))

    def test_page_treats_labs_off_as_not_running(self):
        import labs_site
        js = labs_site.LABS_SCRIPT
        self.assertIn('return api("health", undefined, 4000).then(function (h) {', js)
        self.assertIn('if (!h || !h.ok) throw new Error("bad health");', js)
        self.assertIn('.catch(function () { setOffline("down"); });', js)

    def test_room_view_history_and_focus(self):
        import labs_site
        js = labs_site.LABS_SCRIPT
        # a room opened from a card gets its own history entry: Back closes it, Close/Esc pops it
        self.assertIn('history.pushState({ lab: 1 }, "", "#lab." + id)', js)
        self.assertIn("history.state && history.state.lab) { S.land = land; history.back(); return; }", js)
        self.assertIn("else if (S.view && !S.view.hidden) closeView(2);", js)
        self.assertIn("else if (l) l(1);", js)
        self.assertNotIn('history.replaceState(null, "", "#lab."', js)
        # double-click guard, and a focus trap that leaves the terminal iframe its own keys
        self.assertIn("if (e.detail > 1) return;", js)
        self.assertIn("if (e.detail < 2) { S.opener = b; openRoom(", js)
        self.assertIn('querySelectorAll("button,a[href],summary,input,iframe")', js)


class Controller(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctl = load_controller()
        cls.spec = (LABS / "SPEC.md").read_text()

    def test_docker_run_is_exactly_the_spec(self):
        block = re.search(r"```\n(docker run -d -t .*?)```", self.spec, re.S).group(1)
        lines = [ln.split("#", 1)[0] if "--network" in ln else ln for ln in block.splitlines()]
        cmd = " ".join(lines).replace("<session>", "abcdef012345").replace("<room-id>", "l0-start-here")
        self.assertEqual(self.ctl.lab_run_argv("abcdef012345", "l0-start-here"), shlex.split(cmd))
        with self.assertRaises(ValueError):
            self.ctl.lab_run_argv("../x", "l0-start-here")
        with self.assertRaises(ValueError):
            self.ctl.lab_run_argv("abcdef012345", "bad id; rm")

    def test_only_the_lab_image_is_ever_run(self):
        src = (LABS / "controller" / "controller.py").read_text()
        self.assertEqual(src.count('docker(argv[1:]'), 1)      # run_lab is the only `docker run`
        self.assertNotIn('"run",', src.replace('["docker", "run", "-d"', ""))
        self.assertNotIn("--privileged", src)
        self.assertEqual(self.ctl.MAX_LABS, 2)
        self.assertEqual(self.ctl.IDLE_SECONDS, 30 * 60)

    def test_answer_normalisation(self):
        h = hashlib.sha256(b"ops-4127 x").hexdigest()
        self.assertEqual(self.ctl.answer_sha256("  OPS-4127 \t  X \n"), h)

    def test_public_room_hides_answers_scripts_and_walkthrough(self):
        for d in room_dirs():
            room = json.loads((d / "room.json").read_text())
            public = json.dumps(self.ctl.public_room(room))
            self.assertNotIn("answer_sha256", public, d.name)
            self.assertNotIn("walkthrough", public, d.name)
            self.assertNotIn("checks/", public, d.name)
            self.assertNotIn("solve.sh", public, d.name)

    def test_rooms_validate(self):
        for d in room_dirs():
            room = json.loads((d / "room.json").read_text())
            self.assertEqual(self.ctl.validate_room(room, str(d)), [], d.name)

    def test_pilot_room_answers_match(self):
        d = ROOMS / "00-start-here"
        room = json.loads((d / "room.json").read_text())
        answers = json.loads((d / "answers.test.json").read_text())
        qs = {q["id"]: q for t in room["tasks"] for q in t["questions"]}
        self.assertEqual(set(qs), set(answers))
        for qid, ans in answers.items():
            self.assertEqual(self.ctl.answer_sha256(ans), qs[qid]["answer_sha256"], qid)
        self.assertEqual(room["order"], 0)
        self.assertEqual(room["source"]["note"], "adapted")

    def fake_controller(self, n_paths=3):
        ctl = self.ctl
        rooms = {}
        for i in range(n_paths):          # one room per path: every room is open
            rooms[f"r{i}-room"] = {"id": f"r{i}-room", "title": f"Room {i}", "path": f"p{i}", "order": 0,
                                   "tasks": [{"id": "t1", "points": 10, "questions": [], "checks": []}], "_dir": "/nonexistent"}

        class Prog:
            data = {"rooms": {}}

            def completed(self, rid):
                return False

            def room(self, rid):
                return {}
        c = ctl.Controller(rooms, Prog())
        c._boot = lambda s: setattr(s, "state", "ready")
        return c

    def test_at_most_two_labs(self):
        c = self.fake_controller()
        dropped = []
        c._drop = lambda s, blocking=True: bool((dropped.append(s.sid), c.sessions.pop(s.sid, None)))
        a, b = c.start("r0-room"), c.start("r1-room")
        self.assertIs(c.start("r0-room"), a)                       # same room: resumed, not a new lab
        with self.assertRaises(self.ctl.ApiError) as e:
            c.start("r2-room")
        self.assertEqual(e.exception.status, 429)
        self.assertEqual(len(c.sessions), 2)
        self.assertNotEqual(a.sid, b.sid)

    def test_reaper_destroys_idle_labs(self):
        c = self.fake_controller()
        s = c.start("r0-room")
        dropped = []
        c._drop = lambda sess, blocking=True: bool((dropped.append(sess.sid), c.sessions.pop(sess.sid, None)))
        orig = self.ctl.devlab_containers
        self.ctl.devlab_containers = lambda: {s.container: "running"}
        try:
            c.reap()
            self.assertEqual(dropped, [])                          # active: kept
            s.last_seen -= self.ctl.IDLE_SECONDS + 1
            c.reap()
            self.assertEqual(dropped, [s.sid])                     # idle 30 min: destroyed
        finally:
            self.ctl.devlab_containers = orig

    def test_task_gating(self):
        room = {"id": "r-gate", "title": "g", "path": "p", "order": 0, "_dir": "/nonexistent",
                "tasks": [{"id": "t1", "points": 10, "questions": [{"id": "q1", "answer_sha256": self.ctl.answer_sha256("yes")}], "checks": []},
                          {"id": "t2", "points": 20, "questions": [{"id": "q2", "answer_sha256": self.ctl.answer_sha256("two")}], "checks": []}]}
        c = self.fake_controller()
        c.rooms = {"r-gate": room}
        s = c.start("r-gate")
        with self.assertRaises(self.ctl.ApiError) as e:
            c.answer(s.sid, "q2", "two")                           # task 2 is locked until task 1 passes
        self.assertEqual(e.exception.status, 403)
        self.assertFalse(c.answer(s.sid, "q1", "no")["correct"])
        r = c.answer(s.sid, "q1", "  YES ")
        self.assertTrue(r["correct"] and r["task_passed"])
        self.assertTrue(c.answer(s.sid, "q2", "Two")["state"]["complete"])
        self.assertEqual(s.points(), 30)

    def test_markdown_is_escaped(self):
        out = self.ctl.markdown_html("<script>x</script> [a](javascript:alert(1)) [b](https://example.com)")
        self.assertNotIn("<script>", out)
        self.assertNotIn("javascript:", out.replace("[a](javascript:alert(1))", ""))
        self.assertIn('href="https://example.com"', out)

    def test_host_and_origin_rules(self):
        self.assertTrue(self.ctl.host_ok("127.0.0.1:8173"))
        self.assertTrue(self.ctl.host_ok("localhost:8173"))
        self.assertTrue(self.ctl.host_ok("[::1]:8173"))
        self.assertFalse(self.ctl.host_ok("evil.example:8173"))
        self.assertTrue(self.ctl.origin_ok("http://127.0.0.1:8173", "127.0.0.1:8173"))
        self.assertFalse(self.ctl.origin_ok("http://evil.example", "127.0.0.1:8173"))

    def test_image_never_holds_test_only_files(self):
        ignore = (LABS / "controller" / "Dockerfile.dockerignore").read_text()
        self.assertIn("**/solve.sh", ignore)
        self.assertIn("**/answers.test.json", ignore)
        dockerfile = (LABS / "controller" / "Dockerfile").read_text()
        self.assertIn("find /app -name solve.sh -o -name answers.test.json", dockerfile)
        self.assertIn('LABEL devops-handbook.labs="controller"', dockerfile)


class ControllerReviewFixes(unittest.TestCase):
    """Findings of the independent review: the from-lab guard, the ttyd credential, the session
    lock on removal, and stopped labs not holding a slot. Docker is faked; nothing is started."""
    DEVLAB = "172.30.0.0/16"
    HANDBOOK_IP = "172.30.0.2"
    LAB_IP = "172.30.0.9"                  # a lab still booting: not in lab_ips, no s.ip yet
    DEFAULT_NET_HANDBOOK = "172.18.0.2"    # the handbook on compose's default network

    def setUp(self):
        self.ctl = load_controller()       # a fresh module: patches never leak into other tests
        self.docker_calls = []
        self.removed = []
        self.net_members = {"a": {"Name": "devops-handbook", "IPv4Address": self.HANDBOOK_IP + "/16"},
                            "b": {"Name": "devops-handbook-labs", "IPv4Address": "172.30.0.3/16"}}

        def fake_docker(args, input_bytes=None, timeout=60):
            self.docker_calls.append(list(args))
            if args[:2] == ["network", "inspect"]:
                cfg = json.dumps([{"Subnet": self.DEVLAB}])
                return 0, cfg + "\t" + json.dumps(self.net_members) + "\n", ""
            return 0, "", ""
        self.ctl.docker = fake_docker
        self.ctl.remove_container = lambda name: self.removed.append((name, self.lock_held_elsewhere()))
        self.ctl.LABNET.refresh(force=True)
        rooms = {}
        for i in range(3):
            rooms[f"r{i}-room"] = {"id": f"r{i}-room", "title": f"Room {i}", "path": f"p{i}", "order": 0,
                                   "_dir": "/nonexistent",
                                   "tasks": [{"id": "t1", "points": 10, "questions": [],
                                              "checks": [{"id": "c1", "script": "checks/t1.sh"}]}]}

        class Prog:
            data = {"rooms": {}}

            def completed(self, rid):
                return False

            def room(self, rid):
                return {}

            def record_finish(self, *a):
                return {}
        self.c = self.ctl.Controller(rooms, Prog())
        self.c._boot = lambda s: setattr(s, "state", "ready")
        self.ctl.CTL = self.c
        self.current = None

    def lock_held_elsewhere(self):
        """True when the session under test's lock is held (probed from another thread)."""
        s = self.current
        if s is None:
            return None
        res = []
        t = threading.Thread(target=lambda: res.append(s.lock.acquire(blocking=False)))
        t.start()
        t.join()
        if res[0]:
            s.lock.release()
        return not res[0]

    # ---- finding 1: the from-lab guard
    def handler(self, peer, headers):
        h = self.ctl.Handler.__new__(self.ctl.Handler)
        h.client_address = (peer, 40000)
        raw = "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n"
        h.headers = http.client.parse_headers(io.BytesIO(raw.encode()))
        return h

    def test_forged_via_from_an_in_subnet_peer_is_refused(self):
        for via in ("127.0.0.1", self.DEFAULT_NET_HANDBOOK, ""):
            h = self.handler(self.LAB_IP, {"Host": "127.0.0.1:8173", "X-Lab-Via": via})
            self.assertTrue(h._from_lab(), via)
            with self.assertRaises(self.ctl.ApiError) as e:
                h._guard(False)
            self.assertEqual((e.exception.status, e.exception.code), (403, "from-lab"))
        # the controller's own address on devlab-net is not the handbook either
        self.assertTrue(self.handler("172.30.0.3", {"X-Lab-Via": "127.0.0.1"})._from_lab())

    def test_handbook_is_accepted_and_x_lab_via_still_counts(self):
        for peer in (self.HANDBOOK_IP, self.DEFAULT_NET_HANDBOOK):
            self.assertFalse(self.handler(peer, {"X-Lab-Via": "172.18.0.2"})._from_lab(), peer)
            self.assertFalse(self.handler(peer, {"X-Lab-Via": "127.0.0.1"})._from_lab(), peer)
            # a lab that went through nginx: nginx reports the devlab-net address it was reached on
            self.assertTrue(self.handler(peer, {"X-Lab-Via": self.HANDBOOK_IP})._from_lab(), peer)
        self.handler(self.HANDBOOK_IP, {"Host": "127.0.0.1:8173", "X-Lab-Via": "127.0.0.1"})._guard(False)

    def test_handbook_ip_is_refreshed_on_a_miss(self):
        self.net_members["a"]["IPv4Address"] = "172.30.0.7/16"      # the handbook was recreated
        self.ctl.LABNET.stamp = time.time() - 5                       # cache fresh, but older than 2 s
        n = len(self.docker_calls)
        self.assertFalse(self.handler("172.30.0.7", {"X-Lab-Via": "127.0.0.1"})._from_lab())
        self.assertEqual(self.ctl.LABNET.handbook_ip, "172.30.0.7")
        self.assertGreater(len(self.docker_calls), n)
        # the old address is now just another devlab-net peer
        self.assertTrue(self.handler(self.HANDBOOK_IP, {"X-Lab-Via": "127.0.0.1"})._from_lab())
        # misses re-read the network at most every 2 s (a lab cannot make it spin on docker)
        n = len(self.docker_calls)
        for _ in range(5):
            self.handler(self.LAB_IP, {"X-Lab-Via": "127.0.0.1"})._from_lab()
        self.assertEqual(len(self.docker_calls), n)

    # ---- finding 2: the ttyd credential
    def request(self, peer, path, headers):
        h = self.handler(peer, headers)
        h.path, h.command, h.request_version, h.requestline = path, "GET", "HTTP/1.1", f"GET {path} HTTP/1.1"
        h.wfile = io.BytesIO()
        h._dispatch("GET")
        head = h.wfile.getvalue().decode("latin-1").split("\r\n\r\n", 1)[0].split("\r\n")
        return int(head[0].split()[1]), {k.lower(): v for k, v in (ln.split(": ", 1) for ln in head[1:])}

    def test_term_auth_hands_nginx_the_ttyd_credential(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            s = self.c.start("r0-room")
            hdr = {"Host": "127.0.0.1:8173", "X-Lab-Via": "127.0.0.1", "X-Original-URI": f"/lab-term/{s.sid}/ws"}
            status, headers = self.request(self.HANDBOOK_IP, "/api/labs/term-auth", hdr)
            self.assertEqual(status, 204)
            self.assertEqual(headers["x-lab-auth"],
                             "Basic " + base64.b64encode(f"lab:{s.term_token}".encode()).decode())
            # ttyd runs with exactly that credential (it checks the page, /token and the websocket)
            argv = self.ctl.ttyd_argv(s.term_token)
            self.assertEqual(argv[argv.index("-c") + 1], f"lab:{s.term_token}")
            self.assertGreaterEqual(len(s.term_token), 32)
            self.assertNotEqual(s.term_token, self.c.start("r1-room").term_token)   # per session
            # never from a lab, never for an unknown session
            status, headers = self.request(self.LAB_IP, "/api/labs/term-auth", hdr)
            self.assertEqual(status, 403)
            self.assertNotIn("x-lab-auth", headers)
            status, headers = self.request(self.HANDBOOK_IP, "/api/labs/term-auth",
                                           dict(hdr, **{"X-Original-URI": "/lab-term/000000000000/"}))
            self.assertEqual((status, "x-lab-auth" in headers), (403, False))
            # the API answers that the page sees
            status, headers = self.request(self.HANDBOOK_IP, f"/api/labs/sessions/{s.sid}",
                                           {"Host": "127.0.0.1:8173", "X-Lab-Via": "127.0.0.1"})
            self.assertEqual(status, 200)
            self.assertNotIn("x-lab-auth", headers)
            room_list = json.dumps(self.c.room_list())
        for leak in (json.dumps(s.view()), room_list, repr(s), out.getvalue()):
            self.assertNotIn(s.term_token, leak)
            self.assertNotIn(base64.b64encode(f"lab:{s.term_token}".encode()).decode(), leak)
        with self.assertRaises(ValueError):
            self.ctl.ttyd_argv("x; rm -rf /")

    def test_ttyd_command_is_exactly_the_spec(self):
        spec = (LABS / "SPEC.md").read_text()
        block = re.search(r"\*\*Terminal:\*\*.*?```text\n(.*?)\n\s*```", spec, re.S).group(1)
        token = "ab" * 24
        cmd = " ".join(ln.strip() for ln in block.splitlines()).replace("<token>", token)
        self.assertEqual(self.ctl.ttyd_argv(token), shlex.split(cmd))
        self.assertIn("-c", self.ctl.TTYD_ARGV)

    # ---- finding 3: finish, reset and the reaper take the session lock
    def test_finish_reset_and_reaper_remove_the_lab_under_the_lock(self):
        s = self.current = self.c.start("r0-room")
        self.c.finish(s.sid)
        self.assertEqual(self.removed[-1], (s.container, True))
        self.assertTrue(s.closing)
        with self.assertRaises(self.ctl.ApiError) as e:              # a second Finish: gone, not recorded twice
            self.c.finish(s.sid)
        self.assertEqual(e.exception.status, 404)

        s = self.current = self.c.start("r0-room")
        new = self.c.reset(s.sid)
        self.assertEqual(self.removed[-1], (s.container, True))
        self.assertNotEqual(new.sid, s.sid)

        s = self.current = new
        self.ctl.devlab_containers = lambda: {s.container: "running"}
        s.last_seen -= self.ctl.IDLE_SECONDS + 1
        holder = threading.Event()
        release = threading.Event()

        def running_check():                                           # a check holds the lock
            with s.lock:
                holder.set()
                release.wait(5)
        t = threading.Thread(target=running_check)
        t.start()
        holder.wait(5)
        t0 = time.time()
        self.c.reap()                                                  # does not block, does not remove
        self.assertLess(time.time() - t0, 1)
        self.assertIn(s.sid, self.c.sessions)
        release.set()
        t.join()
        self.c.reap()                                                  # next round: removed under the lock
        self.assertNotIn(s.sid, self.c.sessions)
        self.assertEqual(self.removed[-1], (s.container, True))

    def test_finish_waits_for_a_running_check_and_check_honours_closing(self):
        s = self.current = self.c.start("r0-room")
        events = []

        def slow_exec(container, path, timeout):
            events.append("check-start")
            time.sleep(0.3)
            events.append("check-end")
            return 0, "ok\n", ""
        self.ctl.exec_script = slow_exec
        self.ctl.remove_container = lambda name: events.append("remove")
        t = threading.Thread(target=lambda: self.c.check(s.sid, "t1"))
        t.start()
        while "check-start" not in events:
            time.sleep(0.01)
        self.c.finish(s.sid)
        t.join()
        self.assertEqual(events, ["check-start", "check-end", "remove"])
        s2 = self.c.start("r1-room")
        s2.closing = True                                              # being removed: no new check
        with self.assertRaises(self.ctl.ApiError) as e:
            self.c.check(s2.sid, "t1")
        self.assertEqual(e.exception.status, 404)
        self.assertEqual(events.count("check-start"), 1)

    # ---- finding 5: a stopped lab holds no slot
    def test_stopped_sessions_do_not_block_a_new_start(self):
        a, b = self.c.start("r0-room"), self.c.start("r1-room")
        with self.assertRaises(self.ctl.ApiError):
            self.c.start("r2-room")
        self.ctl.devlab_containers = lambda: {b.container: "running"}   # lab a died (OOM, stopped)
        self.c.reap()
        self.assertEqual(a.state, "stopped")
        self.assertIn(a.sid, self.c.sessions)                          # the page can still show "stopped"
        c3 = self.c.start("r2-room")                                   # the slot is free at once
        self.assertEqual(c3.state, "ready")
        self.assertEqual(len(self.c.live_sessions()), 2)
        # starting the dead lab's room again drops the stopped session for a fresh one
        self.c.finish(c3.sid)
        fresh = self.c.start("r0-room")
        self.assertNotEqual(fresh.sid, a.sid)
        self.assertNotIn(a.sid, self.c.sessions)


class BaseImageAndCleanup(unittest.TestCase):
    def test_base_image(self):
        df = (LABS / "base" / "Dockerfile").read_text()
        self.assertIn("lab ALL=(ALL:ALL) NOPASSWD: ALL", df)
        self.assertIn("useradd -m -u 1000 -s /bin/bash", df)
        self.assertIn("CapabilityBoundingSet=CAP_CHOWN", df)        # the "degraded" fix
        self.assertIn("systemctl mask ttyd.service", df)
        self.assertIn('LABEL devops-handbook.labs="base"', df)
        self.assertNotIn("privileged", re.sub(r"#.*", "", df).lower())

    def test_clean_script(self):
        sh = (LABS / "clean.sh").read_text()
        self.assertTrue((LABS / "clean.sh").stat().st_mode & 0o111)
        self.assertIn('--filter "label=devlab=1"', sh)
        self.assertIn('NETWORK="devlab-net"', sh)
        self.assertIn('LAB_IMAGE="devops-handbook-lab:base"', sh)
        self.assertIn('CTL_IMAGE="devops-handbook-labs-controller"', sh)
        self.assertIn('VOLUME="devops-handbook-labs-progress"', sh)
        self.assertRegex(sh, r'if \[ "\$ALL" = 1 \]; then\n\s+if run docker volume rm')
        for bad in ("system prune", "volume prune", "image prune", "container prune", "network prune",
                    "rmi devops-handbook:local", "rm -f devops-handbook\n"):
            self.assertNotIn(bad, sh)
        self.assertNotIn("builder prune", sh)                         # cache goes through the janitor, by id
        self.assertIn('"$JANITOR" --labs-cache', sh)

    def test_clean_cache_goes_through_the_janitors_lab_roots(self):
        """clean.sh removes only records under the `RUN : devlab-*` roots that start every lab stage."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("janitor", ROOT / "docker" / "janitor" / "janitor.py")
        j = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(j)
        base = (LABS / "base" / "Dockerfile").read_text()
        ctl = (LABS / "controller" / "Dockerfile").read_text()
        self.assertIn("RUN : devlab-base", base)
        self.assertIn("RUN : devlab-controller", ctl)
        self.assertTrue(j.LAB_ROOTS.search("mount / from exec /bin/sh -c : devlab-base"))
        self.assertTrue(j.LAB_ROOTS.search("mount / from exec /bin/sh -c : devlab-controller"))
        for theirs in ("[devlab-controller 2/6] COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker",
                       "mount / from exec /bin/sh -c : devops-handbook-build",
                       "mount / from exec /bin/sh -c apt-get install -y nginx-light ttyd",
                       "[build 2/6] WORKDIR /src",
                       "mount / from exec /bin/sh -c : devlab-base && rm -rf /"):
            self.assertFalse(j.LAB_ROOTS.search(theirs), theirs)
        recs = [{"ID": "r", "Description": "mount / from exec /bin/sh -c : devlab-base", "LastUsedAt": None,
                 "CreatedAt": "2026-01-01T00:00:00Z"},
                {"ID": "c", " Parents": ["r"], "Description": "[2/9] COPY x /y", "CreatedAt": "2026-01-01T00:00:00Z"},
                {"ID": "hb", "Description": "mount / from exec /bin/sh -c : devops-handbook-build",
                 "CreatedAt": "2026-01-01T00:00:00Z"}]
        self.assertEqual({a[1] for a in j.cache_plan(recs, 2_000_000_000, 0, j.LAB_ROOTS)}, {"r", "c"})

class GeneratedPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {n: (ROOT / n).read_text(encoding="utf-8") for n in ("index.html", "artifact.html")}

    def section(self, page):
        start = page.index('id="m-labs"')
        end = page.find("<section", start + 1)
        return page[start:end if end > 0 else None]

    def test_sidebar_group_and_page(self):
        import build_site
        from site_ui import GROUP_TONES
        self.assertIn(("labs.md", "Hands-on labs", "🧪", "Labs"), build_site.MODULES)
        self.assertIn("Labs", GROUP_TONES)
        for name, page in self.pages.items():
            self.assertIn('<li class="nav-group" data-tone="teal">Labs</li>', page, name)
            self.assertIn('id="lab-app"', page, name)
            self.assertIn("docker compose --profile labs up -d --build", page, name)
            self.assertIn('var API = "/api/labs/";', page, name)
            self.assertIn('id="map-canvas"', page, name)                     # the 3D map is still there

    def test_every_room_is_on_the_page(self):
        for name, page in self.pages.items():
            sec = self.section(page)
            for d in room_dirs():
                room = json.loads((d / "room.json").read_text())
                self.assertIn(f'<template data-room="{room["id"]}">', sec, (name, d.name))
                self.assertIn(f'data-room="{room["id"]}"', sec)
                self.assertIn(room["source"]["url"].replace("&", "&amp;"), sec, (name, d.name))

    @staticmethod
    def room_html(sec, rid):
        """The room's card and its <template>: everything the page holds about one room."""
        card = re.search(rf'<article class="lab-card" data-room="{rid}".*?</article>', sec, re.S)
        tpl = re.search(rf'<template data-room="{rid}">.*?</template>', sec, re.S)
        return (card.group(0) if card else "") + (tpl.group(0) if tpl else "")

    @staticmethod
    def strings(obj):
        if isinstance(obj, str):
            return [obj]
        if isinstance(obj, dict):
            return [x for v in obj.values() for x in GeneratedPages.strings(v)]
        if isinstance(obj, list):
            return [x for v in obj for x in GeneratedPages.strings(v)]
        return []

    def test_no_answers_solutions_or_walkthroughs_in_the_pages(self):
        for name, page in self.pages.items():
            self.assertNotIn("answer_sha256", page)
            self.assertNotIn("answers.test.json", self.section(page))
            for d in room_dirs():
                room = json.loads((d / "room.json").read_text())
                sec = html.unescape(self.room_html(self.section(page), room["id"]))
                self.assertTrue(sec, (name, d.name))
                # what the room itself shows (brief, tasks, prompts, hints): anything else is a leak
                public = "\n".join(self.strings({k: room.get(k) for k in ("title", "brief", "tasks", "source")}))
                for t in room["tasks"]:
                    for q in t.get("questions", []):
                        self.assertNotIn(q["answer_sha256"], page, (name, d.name))
                ans_file = d / "answers.test.json"
                answers = json.loads(ans_file.read_text()) if ans_file.is_file() else {}
                for qid, ans in answers.items():
                    if len(str(ans)) >= 4 and str(ans) not in public:
                        self.assertNotIn(str(ans), sec, (name, d.name, qid))
                for script in [d / "solve.sh"] + sorted((d / "checks").glob("*.sh")):
                    if not script.is_file():
                        continue
                    for line in script.read_text().splitlines():
                        line = line.strip()
                        if len(line) > 30 and not line.startswith("#") and line not in public:
                            self.assertNotIn(line, sec, (name, script.name))
                for para in re.split(r"\n\s*\n|\n(?=\d+\. |### )", room.get("walkthrough", "")):
                    para = para.strip()
                    if len(para) > 60 and para not in public:
                        self.assertNotIn(para, sec, (name, d.name))

    def test_page_stays_under_the_artifact_limit(self):
        self.assertLess(len(self.pages["artifact.html"].encode("utf-8")), 16_000_000)


if __name__ == "__main__":
    unittest.main()
