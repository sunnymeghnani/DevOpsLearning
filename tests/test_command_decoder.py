"""Command Decoder: card format, matcher behaviour and site integration (parses files only)."""
import re
import unittest
from pathlib import Path

from command_decoder import (REQUIRED_PARTS, candidate_keys, command_lines, family_files,
                             key_index, load_cards, match_text, segments)

ROOT = Path(__file__).resolve().parents[1]


def words_of(line):
    return [w for w in segments(line)]


class Matcher(unittest.TestCase):
    def test_wrappers_and_assignments_are_stripped(self):
        self.assertEqual(words_of("sudo -u postgres psql -c 'select 1'")[0][0], "psql")
        self.assertEqual(words_of("LC_ALL=C sudo ss -tlnp")[0][0], "ss")
        self.assertEqual(words_of("timeout 5 curl -sv https://example.com")[0][0], "curl")
        self.assertEqual(words_of("watch -n 1 'ss -s'")[0][0], "ss")
        self.assertEqual([w[0] for w in words_of("sudo sh -c 'journalctl -u app'")], ["sh", "journalctl"])

    def test_pipelines_and_nested_commands(self):
        heads = [w[0] for w in words_of("ss -tlnp | grep :443 && journalctl -u app")]
        self.assertEqual(heads, ["ss", "grep", "journalctl"])
        heads = [w[0] for w in words_of("sudo ip netns exec client ping -c 3 10.0.0.2")]
        self.assertEqual(heads, ["ip", "ping"])
        heads = [w[0] for w in words_of("kubectl exec -n shop web-0 -- ss -tlnp")]
        self.assertEqual(heads, ["kubectl", "ss"])
        heads = [w[0] for w in words_of("docker exec -u root app curl -sI http://127.0.0.1:8080")]
        self.assertEqual(heads, ["docker", "curl"])

    def test_most_specific_key_first(self):
        subs = {"docker", "kubectl"}
        self.assertEqual(candidate_keys("docker compose logs -f web".split(), subs),
                         ["docker compose logs", "docker compose", "docker"])
        self.assertEqual(candidate_keys("kubectl -n prod get pods".split(), subs),
                         ["kubectl get pods", "kubectl get", "kubectl"])
        self.assertEqual(candidate_keys("mtr -rwc 50 host".split(), subs), ["mtr"])

    def test_only_commands_in_command_blocks_or_behind_prompts(self):
        md = ("```bash\n# a comment line\nss -tlnp   # trailing comment\ncat <<'EOF' > x.yaml\nkubectl: no\nEOF\n```\n"
              "```\n$ ping -c 1 192.0.2.1\n64 bytes from 192.0.2.1\n```\n"
              "```yaml\nimage: mtr\n```\n")
        self.assertEqual(list(command_lines(md)), ["ss -tlnp", "cat <<'EOF' > x.yaml", "ping -c 1 192.0.2.1"])


class Cards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families, cls.cards = load_cards(str(ROOT))

    def test_order_file_lists_existing_families(self):
        order = [l.strip() for l in (ROOT / "commands" / "ORDER").read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
        on_disk = family_files(str(ROOT))
        self.assertEqual(set(order) - set(on_disk), set(), "ORDER names a missing family file")

    def test_every_card_is_complete_and_unique(self):
        self.assertGreater(len(self.cards), 0)
        ids, keys = {}, {}
        for c in self.cards:
            self.assertTrue(c["keys"], c["name"])
            self.assertTrue(c["tagline"], c["name"])
            for part in REQUIRED_PARTS:
                self.assertIn(part, c["body_md"], (c["file"], c["name"], part))
            self.assertNotIn(c["id"], ids, (c["name"], ids.get(c["id"])))
            ids[c["id"]] = c["file"]
            for k in c["keys"]:
                self.assertNotIn(k, keys, (k, c["name"], keys.get(k)))
                keys[k] = c["name"]
            self.assertNotRegex(c["body_md"], r"(?m)^## ", c["name"])

    def test_the_users_example_is_decoded(self):
        index, subs = key_index(self.cards)
        names = [c["name"] for c in match_text("```bash\nping -c 4 8.8.8.8\nmtr -rwbzc 100 8.8.8.8\n```\n", index, subs)]
        self.assertEqual(names, ["ping", "mtr"])
        mtr = next(c for c in self.cards if c["name"] == "mtr")
        self.assertIn("ping", mtr["instead"])

    def test_no_escaped_pipes_inside_code_spans(self):
        # Python-Markdown prints "\\|" inside backticks literally; a plain "|" stays in its table cell
        for path in (ROOT / "commands").glob("*.md"):
            fence = False
            for n, line in enumerate(path.read_text().split("\n"), 1):
                if line.lstrip().startswith(("```", "~~~")):
                    fence = not fence
                    continue
                if not fence:
                    for code in re.findall(r"(`+)(.+?)\1", line):
                        self.assertNotIn("\\|", code[1], f"{path.name}:{n}")

    def test_samples_stay_generic(self):
        for path in (ROOT / "commands").glob("*.md"):
            text = path.read_text()
            # the real account name and home path must never appear; placeholders like /home/USER are fine
            self.assertNotRegex(text, r"(?i)\bsunny\b|/home/sunny", path.name)
            self.assertNotRegex(text, r"(?i)(aws_secret_access_key|BEGIN [A-Z ]*PRIVATE KEY)\s*[=:-]*\s*[A-Za-z0-9/+]{20,}", path.name)


class SiteIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text()
        cls.families, cls.cards = load_cards(str(ROOT))

    def section(self, sec_id):
        start = self.html.index(f'id="{sec_id}"')
        end = self.html.find('<section', start + 1)
        return self.html[start:end if end > 0 else None]

    def test_decoder_page_holds_every_card_once(self):
        page = self.section("m-command-decoder")
        for c in self.cards:
            self.assertEqual(self.html.count(f'id="{c["id"]}"'), 1, c["id"])
            self.assertIn(f'id="{c["id"]}"', page)

    def test_boxes_point_at_existing_cards_and_skip_generated_pages(self):
        ids = {c["id"] for c in self.cards}
        boxes = re.findall(r'<details class="cmd-sec[^"]*" data-cmds="([^"]+)"', self.html)
        self.assertGreater(len(boxes), 20)
        for b in boxes:
            self.assertTrue({"cmd-" + k for k in b.split()} <= ids, b)
        for sec in ("m-command-decoder", "m-interview-fresher", "m-interview-guide"):
            self.assertNotIn('class="cmd-sec', self.section(sec), sec)
        reach = re.search(r'id="m02-1-reachability">.*?</h2><details class="cmd-sec[^"]*" data-cmds="([^"]+)"',
                          self.html, re.S)
        self.assertTrue(reach and {"ping", "mtr"} <= set(reach.group(1).split()))

    def test_artifact_matches_index(self):
        art = (ROOT / "artifact.html").read_text()
        self.assertEqual(art.count('class="cmd-card"'), self.html.count('class="cmd-card"'))
        self.assertEqual(art.count('<details class="cmd-sec'), self.html.count('<details class="cmd-sec'))


if __name__ == "__main__":
    unittest.main()
