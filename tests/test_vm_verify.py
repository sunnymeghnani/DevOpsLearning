"""Verify VM (labs/vm/): statement splitter, placeholder detection, denylist, classifier, package-list parsing
and the runner Dockerfile's janitor mark. Pure tests: no Docker, no VM, nothing from the handbook is executed
(the splitter only calls `bash -n`, which parses and never runs)."""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VMDIR = ROOT / "labs" / "vm"
sys.path.insert(0, str(VMDIR))
import verifylib as V  # noqa: E402


def vmctl():
    spec = importlib.util.spec_from_file_location("vmctl", VMDIR / "vmctl.py")
    X = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(X)                  # constants and functions only: nothing starts on import
    return X


def split(text, first=1):
    return V.split_statements(text.split("\n"), first)


class Blocks(unittest.TestCase):
    def test_bash_blocks_with_heading_and_line(self):
        md = "# Mod\n\n## Disk full\n\n```bash\ndf -h\n```\n\n```text\nnot bash\n```\n\n- item\n  ```bash\n  du -sh /var\n  ```\n"
        blocks = list(V.iter_blocks(md, "01-x.md"))
        self.assertEqual([(b.line, b.heading, b.lines) for b in blocks],
                         [(6, "Disk full", ["df -h"]), (15, "Disk full", ["du -sh /var"])])

    def test_skipped_modules_and_output_blocks(self):
        self.assertIn("17-windows.md", V.SKIP_MODULES)
        self.assertIn("20-macos.md", V.SKIP_MODULES)
        self.assertTrue(V.is_output_block(["● nginx.service - A high performance web server",
                                           "     Loaded: loaded (/lib/systemd/system/nginx.service)",
                                           "     Active: active (running) since Mon"]))
        self.assertFalse(V.is_output_block(["systemctl status nginx", "journalctl -u nginx -n 50"]))

    def test_macos_labelled_block_is_skipped_whole(self):
        self.assertEqual(V.platform_reason(["", "# macOS (Terminal), not Linux", "top -l 2 -o cpu"]),
                         "other platform: macOS block")
        self.assertTrue(V.platform_reason(["# macOS client (Terminal), not Linux", "route -n get 1.1.1.1"]))
        # only the block's first line counts: a Linux block that mentions macOS further down still runs
        self.assertIsNone(V.platform_reason(["# Linux client", "ip route get 1.1.1.1", "# macOS does it too"]))
        self.assertIsNone(V.platform_reason(["df -h"]))


class Splitter(unittest.TestCase):
    def test_one_statement_per_line(self):
        self.assertEqual(split("df -h\n# a comment\n\nfree -m   # inline\n", 10),
                         [(10, "df -h"), (13, "free -m   # inline")])

    def test_continuations(self):
        got = split("docker run -d \\\n  --name web \\\n  nginx\nps aux |\n  grep nginx\ntrue &&\n  echo ok")
        self.assertEqual([ln for ln, _ in got], [1, 4, 6])
        self.assertEqual(got[0][1], "docker run -d \\\n  --name web \\\n  nginx")

    def test_compound_commands(self):
        text = "for f in /etc/*.conf; do\n  echo \"$f\"\ndone\nif [ -f /etc/hosts ]; then\n  cat /etc/hosts\nfi\nf() {\n  echo hi\n}"
        self.assertEqual([ln for ln, _ in split(text)], [1, 4, 7])

    def test_heredocs(self):
        text = ("cat > /tmp/a.yaml <<'EOF'\nkey: value   # not a comment\nif: [x\nEOF\n"
                "cat <<-END\n\tindented\n\tEND\necho after")
        got = split(text)
        self.assertEqual([ln for ln, _ in got], [1, 5, 8])
        self.assertIn("if: [x", got[0][1])

    def test_heredoc_marker_inside_quotes_is_not_a_heredoc(self):
        self.assertEqual(len(split("echo 'a <<EOF b'\necho two")), 2)
        self.assertEqual(len(split("echo $(( 1 << 2 ))\necho two")), 2)

    def test_quoted_newlines(self):
        got = split("echo 'one\ntwo'\nls")
        self.assertEqual([ln for ln, _ in got], [1, 3])

    def test_a_broken_line_is_emitted_alone(self):
        got = split("echo (broken\nls -l\ndf")
        self.assertEqual(got, [(1, "echo (broken"), (2, "ls -l"), (3, "df")])


class NotShell(unittest.TestCase):
    def test_sql_yaml_ini(self):
        self.assertTrue(V.not_shell_reason("SELECT count(*) FROM pg_stat_activity;"))
        self.assertTrue(V.not_shell_reason("[Service]"))
        self.assertTrue(V.not_shell_reason("services:\n  web:"))
        self.assertIsNone(V.not_shell_reason("psql -c 'SELECT 1'"))
        self.assertIsNone(V.not_shell_reason("http://example.com: is not shell either way"[:0] or "ls"))


class Placeholders(unittest.TestCase):
    def test_stand_ins(self):
        for stmt in ("kill -TERM PID", "docker logs CONTAINER", "kubectl -n NS get pods", "ssh USER@HOST uptime",
                     "ip link show dev IFACE", "aws ec2 describe-vpcs --vpc-ids VPC_ID", "ping -c 3 OLD_IP",
                     "curl -H 'Authorization: Bearer <token>' https://api.example.com",
                     "kubectl describe pod <pod-name>", "docker run ... nginx", "ssh -N -f -L …"):
            self.assertTrue(V.placeholder_reason(stmt), stmt)
        self.assertTrue(V.placeholder_reason("docker run --dns GOODDNS ubuntu"))

    def test_not_stand_ins(self):
        for stmt in ("echo $PID", "PID=$(pgrep nginx); kill -0 $PID", "export VM_IP=10.0.0.5",
                     "unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY", "dig example.com NS", "sar -n DEV 1 3",
                     "lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS", "grep -E 'ERROR|WARN' /var/log/syslog",
                     "iptables -L INPUT -n", "echo '<h1>hello</h1>' > /var/www/html/index.html",
                     "sort <in.txt >out.txt", "cat <<EOF > /tmp/x\nhello\nEOF", "echo 'waiting...'",
                     "for HOST in a b; do echo $HOST; done", "docker run -e POSTGRES_PASSWORD=x postgres",
                     "ls /usr/lib/x86_64-linux-gnu/ | head", "psql -c 'CREATE TABLE t (id int)'",
                     "ps aux | grep '<defunct>'", "printenv DATABASE_URL"):
            self.assertIsNone(V.placeholder_reason(stmt), stmt)


class Denylist(unittest.TestCase):
    def test_vm_killers_are_denied(self):
        for stmt in ("sudo reboot", "shutdown -h now", "systemctl poweroff", "sudo init 6", "systemctl isolate rescue.target",
                     "sudo systemctl stop ssh", "systemctl disable --now systemd-networkd", "mkfs.ext4 /dev/vda1",
                     "sudo wipefs -a /dev/vdb", "dd if=/dev/zero of=/dev/sda bs=1M", "sudo fdisk /dev/vda",
                     "rm -rf /", "sudo rm -rf /etc", "rm -rf --no-preserve-root /", "sudo iptables -P INPUT DROP",
                     "iptables -F", "sudo ufw enable", "ufw allow 22/tcp", "nft flush ruleset",
                     "ip link set ens3 down", "sudo ip addr flush dev ens3", "ip route del default",
                     "sudo netplan apply", "ifdown eth0", "kill -9 -1", "sudo pkill sshd", "killall -9 python3",
                     "echo b > /proc/sysrq-trigger", "swapoff -a", "chmod -R 777 /", "chown -R nobody /usr",
                     "sudo userdel lab", "passwd -l root", ":(){ :|:& };:", "tc qdisc add dev ens3 root netem loss 50%",
                     "sudo nmcli connection down eth0", "fallocate -l 50G /bigfile", "yes > /tmp/fill",
                     "sudo bash -c 'reboot'", "sudo apt-get remove -y docker.io containerd runc",
                     'for pkg in docker.io docker-doc containerd runc; do\n  sudo apt-get remove -y "$pkg"\ndone', "echo 'AllowUsers deploy' | sudo tee -a /etc/ssh/sshd_config"):
            self.assertTrue(V.deny_reason(stmt), stmt)

    def test_harmless_lookalikes_run(self):
        for stmt in ("last -x reboot | head", "journalctl --list-boots", "systemctl status ssh", "sudo systemctl restart ssh",
                     "iptables -L -n -v", "sudo iptables -S", "iptables -t nat -L -n", "nft list ruleset",
                     "ufw status verbose", "ip link show", "ip -br addr", "ip route get 1.1.1.1", "fdisk -l",
                     "sudo hdparm -tT /dev/sda", "mdadm --detail /dev/md0", "mkfs.ext4 -F /tmp/disk.img",
                     'sudo mkfs.ext4 -L labdata "${LOOP}p1"', "rm -rf /tmp/lab", "rm -rf ./build",
                     "chmod -R g+w /srv/app", "kill -9 1234", "kill -1 1234", "pkill -f myapp", "yes > /dev/null &",
                     "fallocate -l 1G /tmp/test.img", "dd if=/dev/zero of=/tmp/test bs=1M count=100",
                     "netplan get", "sudo netplan generate", "nmcli device status", "tc qdisc show dev ens3",
                     "ethtool ens3", "echo 'reboot is not run here'"[:0] or "uptime",
                     "echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab", "cat /etc/ssh/sshd_config",
                     "sudo apt-get remove -y nginx", "apt purge apache2"):
            self.assertIsNone(V.deny_reason(stmt), stmt)

    def test_skip_reason_order(self):
        self.assertTrue(V.skip_reason("sudo reboot").startswith("denylist"))
        self.assertTrue(V.skip_reason("docker logs CONTAINER").startswith("placeholder"))
        self.assertTrue(V.skip_reason("SELECT 1;").startswith("not shell"))
        self.assertIsNone(V.skip_reason("uname -a"))


class Classifier(unittest.TestCase):
    def c(self, rc, out="", err="", to=False):
        return V.classify(rc, out, err, to).cls

    def test_classes(self):
        self.assertEqual(self.c(0, "ok"), "PASS")
        self.assertEqual(self.c(124, to=True), "TIMEOUT")
        self.assertEqual(self.c(127, err="bash: line 1: nmap: command not found"), "MISSING")
        self.assertEqual(self.c(127, err="/root/vfy/s/9.sh: line 1: kubectl: command not found"), "EXTERNAL")
        self.assertEqual(self.c(1, err="sudo: terraform: command not found"), "EXTERNAL")
        self.assertEqual(self.c(1, err="ls: unrecognized option '--colour-me'\nTry 'ls --help' for more information."),
                         "USAGE")
        self.assertEqual(self.c(2, err="grep: invalid option -- 'Q'\nUsage: grep [OPTION]... PATTERNS [FILE]..."), "USAGE")
        self.assertEqual(self.c(1, err='Object "lnk" is unknown, try "ip help".'), "USAGE")
        self.assertEqual(self.c(1, err="Unknown command verb 'stauts'."), "USAGE")
        self.assertEqual(self.c(2, err="bash: -c: line 1: syntax error near unexpected token `)'"), "USAGE")
        self.assertEqual(self.c(1, err="date: invalid argument 'x' for '--iso-8601'"), "USAGE")
        self.assertEqual(self.c(3, err="Unit nginx.service could not be found."), "CONTEXT")
        self.assertEqual(self.c(1, err="RTNETLINK answers: Invalid argument"), "CONTEXT")
        self.assertEqual(self.c(7, err="curl: (7) Failed to connect to 192.0.2.10 port 80"), "CONTEXT")
        self.assertEqual(self.c(1), "CONTEXT")
        # usage text printed after a context failure (no such pid / file / user) is not a doc error
        self.assertEqual(self.c(1, err="lsof: can't get UID for appuser\nlsof 4.95.0\n usage: [-?abhKlnNoOPRtUvVX]"),
                         "CONTEXT")
        self.assertEqual(self.c(255, err="Problems finding threads of monitor\n\n Usage: perf stat [<options>]"),
                         "CONTEXT")
        self.assertEqual(self.c(1, err="Usage: perf stat [<options>] [<command>]"), "USAGE")
        # an empty $(...) leaves a command without its argument: context, not a doc error
        err = "docker: 'docker inspect' requires at least 1 argument\n\nUsage:  docker inspect [OPTIONS] NAME|ID"
        self.assertEqual(V.classify(1, "", err, False, "docker inspect -f '{{.Name}}' $(docker ps -aq)").cls, "CONTEXT")
        self.assertEqual(V.classify(1, "", err, False, "docker inspect").cls, "USAGE")

    def test_context_not_usage(self):
        self.assertEqual(self.c(129, err="warning: Not a git repository. Use --no-index to compare two paths\n"
                                          "error: unknown option `staged'\nusage: git diff --no-index"), "CONTEXT")
        self.assertEqual(self.c(2, err="usage: python -m json.tool [-h] [infile]\npython -m json.tool: error: "
                                       "argument infile: can't open '/etc/docker/daemon.json'"), "CONTEXT")
        err = "docker: 'docker inspect' requires at least 1 argument\nUsage:  docker inspect [OPTIONS] NAME|ID"
        self.assertEqual(V.classify(1, "", err, False, "docker ps -q | xargs docker inspect -f x").cls, "CONTEXT")
        self.assertEqual(V.classify(1, "usage: app start|stop", "", False,
                                    'case $1 in\n  *) echo "usage: app start|stop"; exit 1 ;;\nesac').cls, "CONTEXT")

    def test_missing_refinements(self):
        err = "/root/vfy/s/9.sh: line 1: q: command not found"
        self.assertEqual(V.classify(127, "", err, False, "q 'up'", V.defined_functions(["q() { curl -s x; }"])).cls,
                         "CONTEXT")
        self.assertEqual(V.classify(127, "", err).cls, "MISSING")
        self.assertEqual(V.classify(127, "", "line 1: ServerAliveInterval: command not found").cls, "USAGE")
        self.assertEqual(V.classify(127, "", "line 1: -: command not found").cls, "USAGE")

    def test_config_text_and_hidden_errors(self):
        # APT config typed into a bash block: the name holds '::'
        err = "/root/vfy/s/1.sh: line 1: Unattended-Upgrade::Automatic-Reboot: command not found"
        self.assertEqual(V.classify(127, "", err, False, 'Unattended-Upgrade::Automatic-Reboot "true";').cls, "USAGE")
        # a list of sysctl keys typed into a bash block, but a real dotted command name stays MISSING
        err = ("/root/vfy/s/1.sh: line 1: kernel.pid_max: command not found\n"
               "/root/vfy/s/1.sh: line 1: kernel.threads-max: command not found")
        self.assertEqual(V.classify(127, "", err, False, "kernel.pid_max ; kernel.threads-max").cls, "USAGE")
        self.assertEqual(V.classify(127, "", "x: line 1: fs.file-max: command not found", False,
                                    "fs.file-max      # system-wide fd limit").cls, "USAGE")
        self.assertEqual(V.classify(127, "", "x: line 1: python3.12: command not found", False, "python3.12 -V").cls,
                         "MISSING")
        # GNU wrappers name the missing program differently
        v = V.classify(127, "", "env: ‘cgi-fcgi’: No such file or directory", False, "sudo env A=1 cgi-fcgi -bind")
        self.assertEqual((v.cls, v.commands), ("MISSING", ["cgi-fcgi"]))
        self.assertEqual(V.classify(127, "", "nice: ‘./batch.sh’: No such file or directory", False,
                                    "nice -n 19 ./batch.sh").cls, "CONTEXT")
        # exit 127 with stderr sent elsewhere: an EXTERNAL head is still EXTERNAL
        self.assertEqual(V.classify(127, "", "", False, "TF_LOG=DEBUG terraform apply 2> tf.log").cls, "EXTERNAL")
        self.assertEqual(V.classify(127, "", "", False, "tuned-adm active 2>/dev/null").cls, "CONTEXT")
        # `git diff --staged` outside a repository becomes `git diff --no-index`: context, not a doc error
        err = "error: unknown option `staged'\nusage: git diff --no-index [<options>] <path> <path>"
        self.assertEqual(V.classify(129, "", err, False, "git diff --staged").cls, "CONTEXT")

    def test_stderr_counts_even_behind_a_pipeline(self):
        err = "grep: /var/log/apache2/error.log: No such file or directory\n"
        self.assertEqual(V.classify(0, "", err, False, "grep -c AH0 /var/log/apache2/error.log | sort").cls, "CONTEXT")
        self.assertEqual(V.classify(0, "", "Error response from daemon: No such container: hc", False,
                                    "docker rm -f hc").cls, "PASS")                   # no pipeline: rc 0 is a pass
        self.assertEqual(V.classify(0, "x", "WARNING: apt does not have a stable CLI interface.", False,
                                    "apt list --installed | grep nginx").cls, "PASS")  # a warning is not a failure
        self.assertEqual(V.classify(0, "", err, False, "grep -c AH0 /var/log/x || echo none").cls, "PASS")
        self.assertEqual(self.c(0, err="bash: line 1: iotop: command not found"), "MISSING")
        self.assertEqual(self.c(0, err="ss: invalid option -- 'Z'"), "USAGE")
        self.assertEqual(V.classify(127, "", "bash: line 1: foo: command not found\n"
                                    "bash: line 1: kubectl: command not found").commands, ["foo"])


class Packages(unittest.TestCase):
    def test_parse_inline(self):
        df = ("FROM ubuntu:24.04\nRUN : devlab-base\nRUN apt-get update && apt-get install -y --no-install-recommends \\\n"
              "      systemd sudo \\\n      nginx-light netplan.io \\\n && apt-get clean\n")
        self.assertEqual(V.base_packages(df), ["systemd", "sudo", "nginx-light", "netplan.io"])

    @unittest.skipUnless((ROOT / "labs" / "base" / "Dockerfile").is_file(), "Dockerfiles are not in the build context")
    def test_parse_the_lab_image(self):
        pkgs = V.base_packages((ROOT / "labs" / "base" / "Dockerfile").read_text())
        for p in ("systemd", "openssh-server", "nginx-light", "apache2", "postgresql", "dnsmasq", "netplan.io"):
            self.assertIn(p, pkgs)
        self.assertNotIn("&&", pkgs)


class RunnerImage(unittest.TestCase):
    @unittest.skipUnless((VMDIR / "Dockerfile").is_file(), "Dockerfiles are not in the image build context")
    def test_marker_and_label(self):
        text = (VMDIR / "Dockerfile").read_text()
        for block in re.split(r"^(?=FROM )", text, flags=re.M)[1:]:
            steps = [ln for ln in block.splitlines()[1:] if re.match(r"(RUN|COPY|ADD|WORKDIR)\b", ln)]
            self.assertEqual(steps[0], "RUN : devops-handbook-vm")
        self.assertIn('LABEL devops-handbook.project="vm"', text)
        spec = importlib.util.spec_from_file_location("janitor", ROOT / "docker" / "janitor" / "janitor.py")
        J = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(J)
        self.assertTrue(J.CACHE_MARKS.search("mount / from exec /bin/sh -c : devops-handbook-vm"))

    def test_runner_container_and_qemu_args(self):
        X = vmctl()
        for network in (True, False):
            args = X.container_args(network)
            self.assertIn("--cap-drop", args)
            self.assertEqual(args[args.index("--cap-drop") + 1], "ALL")
            self.assertIn("no-new-privileges:true", args)
            self.assertIn("--read-only", args)
            self.assertNotIn("--privileged", args)
            for flag in ("-p", "--publish", "-P", "--publish-all", "--net=host"):
                self.assertNotIn(flag, args)
            mounts = [args[i + 1] for i, a in enumerate(args) if a in ("-v", "--volume", "--mount")]
            self.assertEqual(mounts, [f"{X.VOLUME}:/vm"])               # the named volume only, no host path
        self.assertEqual(X.container_args(False)[X.container_args(False).index("--network") + 1], "none")
        self.assertNotIn("--network", X.container_args(True))      # only prepare downloads
        src = (VMDIR / "vmctl.py").read_text()
        self.assertIn("start_container(network=True)", re.search(r"def cmd_prepare[\s\S]*?\n\n\n", src).group(0))
        self.assertIn("start_container(network=False)", re.search(r"def cmd_verify[\s\S]*?\n\n\n", src).group(0))
        vm = X.VM("/vm/runs/x", "m01-1", X.PREPARED)
        net = vm.qemu_args()[vm.qemu_args().index("-netdev") + 1]
        self.assertEqual(net, "user,id=n0,hostfwd=tcp:127.0.0.1:2222-:22,restrict=on")
        self.assertNotIn("restrict=on", " ".join(X.VM("/vm/runs/p", "prepare", X.BASE_IMG, restrict=False).qemu_args()))

    def test_report_names_each_missing_commands_own_hint(self):
        import tempfile
        X = vmctl()
        stmts = [{"id": 1, "module": "07-x.md", "line": 3, "heading": "h", "block": "07-x.md#0",
                  "text": "stop nginx; restart nginx", "skip": None, "cls": "MISSING", "detail": "stop, restart",
                  "hint": "stop: no package for stop; restart: no package for restart", "rc": 127}]
        old = X.REPORTS
        with tempfile.TemporaryDirectory() as d:
            X.REPORTS = Path(d)
            try:
                path = X.write_report({"Date": "2026-01-02 03:04"}, stmts, [], partial=True)
            finally:
                X.REPORTS = old
            md = path.read_text()
        self.assertEqual(path.name, "verify-2026-01-02-partial.md")          # the run's day, not today's
        self.assertIn("| `restart` | 1 | no package for restart |", md)
        self.assertIn("| `stop` | 1 | no package for stop |", md)

    # A real-format join token, assembled at run time so that no token-shaped literal sits in this public file.
    FAKE_SWARM_TOKEN = "SWMTKN-1-" + "a1" * 25 + "-" + "b2" * 12 + "c"

    def test_scrub_masks_swarm_join_tokens(self):
        X = vmctl()
        out = X.scrub(f"    docker swarm join --token {self.FAKE_SWARM_TOKEN} 192.168.56.11:2377\n")
        self.assertEqual(out, "    docker swarm join --token SWMTKN-1-REDACTED 192.168.56.11:2377\n")

    def test_scrub_masks_a_token_cut_short_by_the_excerpt_limit(self):
        X = vmctl()
        cut = self.FAKE_SWARM_TOKEN[:-20]                      # the JSON keeps only the first 300 characters
        self.assertEqual(X.scrub(f"--token {cut} [...]"), "--token SWMTKN-1-REDACTED [...]")
        self.assertEqual(X.scrub(f"--token {cut[:30]} [...]"), "--token SWMTKN-1-REDACTED [...]")

    def test_scrub_keeps_the_handbooks_placeholder_tokens(self):
        X = vmctl()
        for text in ("docker swarm join --token SWMTKN-1-TOKEN 192.168.56.11:2377",
                     "--token SWMTKN-1-WORKERTOKEN 10.10.0.10:2377",
                     "--token SWMTKN-WORKER-TOKEN 10.0.0.11:2377",
                     "`docker swarm join --token SWMTKN-1-… 192.168.56.11:2377`"):
            self.assertEqual(X.scrub(text), text)

    def test_report_files_carry_no_swarm_join_token(self):
        import tempfile
        X = vmctl()
        printed = f"Swarm initialized.\n\n    docker swarm join --token {self.FAKE_SWARM_TOKEN} 10.0.2.15:2377\n"
        stmts = [{"id": 1, "module": "44-x.md", "line": 9, "heading": "h", "block": "44-x.md#0",
                  "text": "docker swarm init", "skip": None, "cls": "PASS", "detail": "", "rc": 0, "out": printed,
                  "err": ""},
                 {"id": 2, "module": "44-x.md", "line": 10, "heading": "h", "block": "44-x.md#0",
                  "text": "docker swarm join-token --bogus", "skip": None, "cls": "USAGE", "detail": "unknown flag",
                  "rc": 125, "out": "", "err": printed}]
        old = X.REPORTS
        with tempfile.TemporaryDirectory() as d:
            X.REPORTS = Path(d)
            try:
                path = X.write_report({"Date": "2026-01-02 03:04"}, stmts, [], partial=True)
            finally:
                X.REPORTS = old
            md, js = path.read_text(), path.with_suffix(".json").read_text()
        for name, text in (("md", md), ("json", js)):
            self.assertNotIn(self.FAKE_SWARM_TOKEN, text, name)
            self.assertIn("SWMTKN-1-REDACTED", text, name)

    def test_guest_runner_hint_pattern(self):
        spec = importlib.util.spec_from_file_location("guest_runner", VMDIR / "guest_runner.py")
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)              # defines functions only; main() runs in the guest
        err = "bash: line 1: iotop: command not found\nenv: ‘cgi-fcgi’: No such file or directory\n"
        self.assertEqual(sorted(a or b for a, b in G.NOT_FOUND.findall(err)), ["cgi-fcgi", "iotop"])
        self.assertEqual(G.HEAL_UNITS, ("containerd.service", "docker.socket", "docker.service"))

    def test_orchestrator_rules(self):
        src = (VMDIR / "vmctl.py").read_text()
        code = re.sub(r'"""[\s\S]*?"""', "", src)
        self.assertIn('"--cap-drop", "ALL"', code)
        self.assertIn('"--device", "/dev/kvm"', code)
        self.assertNotIn("--privileged", code)
        self.assertNotRegex(code, r'"-p",|"--publish"|"-P"')            # no published ports
        self.assertIn("restrict=on", code)                                # the guest is offline during a run
        # an OOM kill of a statement's process must not make systemd stop the runner's unit (default: stop)
        self.assertRegex(code, r"systemd-run[^\n]*\n[^\n]*OOMPolicy=continue|systemd-run[^\n]*OOMPolicy=continue")
        self.assertIn("127.0.0.1:{SSH_PORT}", code)
        for banned in ("system prune", "volume prune", "image prune", "container prune", "network prune"):
            self.assertNotIn(banned, code)
        self.assertIn("MIN_FREE = 15e9", code)
        self.assertIn('DISK_SIZE = "10G"', code)
        self.assertIn("ubuntu-cloudimage-keyring.gpg", code)
        self.assertIn("https://cloud-images.ubuntu.com/releases/noble/release/", code)


if __name__ == "__main__":
    unittest.main()
