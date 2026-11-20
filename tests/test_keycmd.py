"""Key commands explained (keycmd_site.py + keycmd_notes.tsv): every command in a map topic's "Key commands"
list has a one-line summary and a safety level, a "read-only" badge never contradicts its decoder card, and
both pages carry the data and the rendering.

Run after building: python3 -m unittest tests.test_keycmd -v
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import command_decoder as cd  # noqa: E402
import keycmd_site as kc  # noqa: E402

PAGES = ("index.html", "artifact.html")
# card safety wording that allows a "read-only" (or "adds load") badge for the invocation
READISH = re.compile(r"read-only|only read|only list|only prints|creates nothing|installs nothing|predicts without changing|"
                     r"pure calculation|generates load")
# reviewed by hand: the card covers changing uses too, but this exact invocation only reads
REVIEWED_RO = {
    "bash -n health.sh": "-n parses the script and runs nothing",
    "sudo nft list ruleset | sudo tee /root/nft-before.txt >/dev/null": "tee writes only the ruleset copy, its own output file",
    "docker exec uptime-kuma du -h /app/data/kuma.db": "docker exec runs du, which only reads",
    "sudo iptables -L DOCKER-USER -n -v": "-L only lists the chain",
    "sudo nsenter -t PID -n ss -ltn": "nsenter runs ss, which only reads",
    "kubectl create deploy web --image=nginx --dry-run=client -o yaml": "--dry-run=client creates nothing",
    "strace -f -e trace=openat,connect curl -so /dev/null https://example.com": "traces a curl GET it starts itself",
    "docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers": "wget -qO- prints, saves nothing",
    "sudo nsenter -t PID -n ip addr": "nsenter runs ip addr, which only reads",
    "docker exec alertmanager amtool --alertmanager.url=http://localhost:9093 silence query": "silence query only reads",
    "sudo auditctl -l": "-l only lists the loaded rules",
    "docker exec CROWDSEC cscli metrics": "cscli metrics only reads",
    "ansible-lint site.yml": "lints files, never runs the playbook",
    "sudo unattended-upgrade --dry-run --debug": "--dry-run installs nothing (it may download packages)",
}
# the 7 commands without a decoder card: summary and safety written by hand
# ("tofu plan" has the terraform plan card since the decoder's OpenTofu alias)
NO_CARD = {"sudo -l -U deploy", "yamllint .gitlab-ci.yml", "sudo /usr/share/gitlab-runner/clear-docker-cache",
           "alias k=kubectl", "pvesm status", "sudo /var/ossec/bin/agent_control -l",
           "sudo /var/ossec/bin/wazuh-logtest"}


def roadmap_of(text):
    m = re.search(r'<script type="application/json" id="roadmap-data">(.*?)</script>', text, re.S)
    return json.loads(m.group(1))


class KeyCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = kc.load_notes(str(ROOT))
        with open(ROOT / "roadmap.json", encoding="utf-8-sig") as f:
            cls.raw = json.load(f)
        _, cls.cards = cd.load_cards(str(ROOT))
        cls.index, cls.sub = cd.key_index(cls.cards)
        cls.text = {n: (ROOT / n).read_text(encoding="utf-8") for n in PAGES}

    def test_every_key_command_has_a_line(self):
        cmds = [c for n in self.raw["nodes"] for c in n.get("commands", [])]
        self.assertGreater(len(cmds), 400)
        missing = sorted({c for c in cmds if c not in self.notes})
        self.assertEqual(missing, [], "add these to keycmd_notes.tsv")
        self.assertEqual(sorted(set(self.notes) - set(cmds)), [], "lines no topic uses")

    def test_lines_are_short_learner_sentences(self):
        for cmd, (level, summary) in self.notes.items():
            with self.subTest(cmd=cmd):
                self.assertIn(level, kc.LEVELS)
                self.assertLessEqual(len(summary), kc.MAX_SUMMARY)
                self.assertGreater(len(summary), 12)
                self.assertNotEqual(summary.strip(), cmd.strip())
                self.assertFalse(summary.endswith("."), "no full stop at the end")
                self.assertNotRegex(summary, r"/home/|sunny", "no personal paths")

    def test_safety_never_contradicts_the_card(self):
        """'ro'/'load' only where every card the command uses says it can only read, or a reviewed exception."""
        for cmd, (level, _) in self.notes.items():
            cards = kc.command_cards(cmd, self.index, self.sub)
            with self.subTest(cmd=cmd):
                if not cards:
                    self.assertIn(cmd, NO_CARD)
                    continue
                if level in ("ro", "load") and cmd not in REVIEWED_RO:
                    for c in cards:
                        self.assertRegex(c["safety"], READISH, f"{c['id']}: {c['safety']}")
        self.assertEqual({c for c in self.notes if not kc.command_cards(c, self.index, self.sub)}, NO_CARD)
        for cmd in REVIEWED_RO:
            self.assertEqual(self.notes[cmd][0], "ro", cmd)

    def test_tofu_plan_uses_the_terraform_plan_card(self):
        """The decoder's OpenTofu alias: `tofu plan` is decoded by the terraform plan card."""
        self.assertEqual([c["name"].split(" — ")[0] for c in kc.command_cards("tofu plan -out=tfplan", self.index, self.sub)],
                         ["terraform plan"])
        self.assertIs(self.index["tofu plan"], self.index["terraform plan"])

    def test_obvious_safety_levels(self):
        """Spot checks of the badge for invocations whose effect is clear from their own words."""
        lv = {c: v[0] for c, v in self.notes.items()}
        for cmd in ("terraform apply tf.plan", "kubectl drain NODE --ignore-daemonsets", "sudo systemctl disable --now apache2",
                    "aws iam update-access-key --access-key-id ACCESS_KEY_ID --status Inactive"):
            self.assertEqual(lv[cmd], "dg", cmd)
        for cmd, level in lv.items():
            if re.search(r"\b(prune|rollback|undo|register|apply|init|push|edit|encrypt|update|hold|allow|restore|revert|rebase|"
                         r"mask|reload|kill|cp|mkdir|silence add|terminate-op|use-context)\b", cmd) and not re.search(
                    r"--dry-run|--check|-d /etc/logrotate|history|validate|status|certificates", cmd):
                with self.subTest(cmd=cmd):
                    self.assertIn(level, ("ch", "dg"))

    def test_main_card_first(self):
        """The Decode link goes to the command the line is about, not to the head/grep/jq that shapes its output."""
        first = lambda c: kc.command_cards(c, self.index, self.sub)[0]["id"]
        self.assertEqual(first("ps -eo pid,ppid,stat,etime,cmd --sort=-%cpu | head"), "cmd-ps")
        self.assertEqual(first("echo | openssl s_client -connect app.example.com:443 -servername app.example.com "
                               "2>/dev/null | openssl x509 -noout -enddate"), "cmd-openssl-s-client")
        self.assertEqual(first("history | tail -30"), "cmd-cd-pwd-type-which-history")
        self.assertEqual(first("docker inspect CONTAINER | jq '.[0].State'"), "cmd-docker-inspect")

    def test_build_fails_loudly_without_a_line(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / kc.NOTES_FILE).write_text("ls -l\tro\tlong listing of the current directory\n", encoding="utf-8")
            (Path(d) / "commands").mkdir()
            missing, unused = kc.annotate({"nodes": [{"id": "x", "commands": ["ls -l", "df -h"]}]}, d)
            self.assertEqual(missing, [("x", "df -h")])
            (Path(d) / kc.NOTES_FILE).write_text("ls -l\tsafe\tlong listing\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                kc.load_notes(d)
        src = (ROOT / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("have no line in keycmd_notes.tsv", src)
        self.assertRegex(src, r"for topic, cmd in no_line:\n.*\n\s+return 1")

    def test_pages_carry_summaries_and_rendering(self):
        for name, t in self.text.items():
            with self.subTest(page=name):
                rm = roadmap_of(t)
                n_cmd = 0
                for node in rm["nodes"]:
                    cmds = node.get("commands", [])
                    if not cmds:
                        continue
                    self.assertEqual(len(node["cmdx"]), len(cmds), node["id"])
                    for c, (summary, level, ids) in zip(cmds, node["cmdx"]):
                        n_cmd += 1
                        self.assertEqual((level, summary), self.notes[c])
                        for i in ids.split():
                            self.assertIn(f'id="cmd-{i}"', t, i)    # every Decode link lands on a card
                self.assertGreater(n_cmd, 450)
                self.assertIn(kc.KEYCMD_CSS, t)
                for needle in ('function cmdList(n)', 'class: "kc-b kc-" + x[1]', '"Decode ›"', 'jumpTo("cmd-" + id)',
                               'section("Key commands", cmdList(n))', "homeView, cmdList,", '"read-only"', '"changes state"',
                               '"dangerous"', '"adds load"'):
                    self.assertIn(needle, t, needle)
        css = kc.KEYCMD_CSS
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,6}\b")        # theme tokens only: both themes
        self.assertIn("@media print", css)


if __name__ == "__main__":
    unittest.main()
