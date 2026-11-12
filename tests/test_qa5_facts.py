"""Facts corrected in the Version 12 pre-publish QA (QA5, 10 November 2026).

- live-restore on a Swarm node: dockerd refuses to start ("--live-restore daemon configuration is
  incompatible with swarm mode", docker/docs#26424), so module 57 and the hint under 30's daemon.json
  section must not say it merely "skips" or "does not apply" to Swarm services.
- The PROTECT card's one-box line: a DHCP client learns a shorter lease only at its next renewal, at
  half the OLD lease (RFC 2131 4.4.5), so "lowered the day before" is wrong for a 7-day lease.
- Wikimedia 2022-05-24: an extra `Listen 443` is valid syntax, so `apachectl configtest` would not
  have caught it; the drill must not present configtest as the guard for this incident.
- Interview pack 57: PostgreSQL's max_connections cannot be raised without a restart.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M57 = (ROOT / "57-method-protect-risk-ladder.md").read_text(encoding="utf-8")


class LiveRestoreOnSwarm(unittest.TestCase):
    def test_module_57_says_dockerd_refuses_it(self):
        self.assertNotIn("live-restore skips Swarm services", M57)
        self.assertNotIn("will not keep its services up", M57)
        self.assertIn("dockerd refuses to start with it", M57)
        self.assertIn("incompatible with swarm mode", M57)
        self.assertIn("https://github.com/docker/docs/issues/26424", M57)

    def test_docker_hint_says_it_is_refused(self):
        rows = [l.split("\t") for l in (ROOT / "hints/safest-step.tsv").read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
        text = [r[3] for r in rows if r[0] == "30-learn-docker.md" and r[1] == "daemon.json keys that matter on-prem"]
        self.assertEqual(len(text), 1)
        self.assertNotIn("does not apply", text[0])
        self.assertIn("refuses live-restore", text[0])


class LeaseAndTtlLeadTime(unittest.TestCase):
    def test_card_uses_half_an_old_lease_not_the_day_before(self):
        card = M57.split("```text\n")[1].split("\n```")[0]
        self.assertNotIn("the day before", card)
        self.assertIn("half an old lease", card)
        self.assertIn("one old TTL ahead", card)
        self.assertLessEqual(max(len(l) for l in card.splitlines()), 90, "the card must stay one A4 page wide")


class WikimediaApacheDrill(unittest.TestCase):
    def test_configtest_is_not_sold_as_the_guard(self):
        d = json.loads((ROOT / "drills/wikimedia-2022-apache-listen-443.json").read_text(encoding="utf-8"))
        ch = [c for s in d["steps"] for c in s["choices"] if c["text"].startswith("Add apachectl configtest")]
        self.assertEqual(len(ch), 1)
        self.assertIn("valid syntax", ch[0]["why"])
        self.assertNotIn("A good guard", ch[0]["why"])


class InterviewPack57(unittest.TestCase):
    def test_raising_the_limit_is_only_a_live_move_where_it_can_be(self):
        text = (ROOT / "interview/57-method-protect-risk-ladder.md").read_text(encoding="utf-8")
        self.assertIn("PostgreSQL's needs a restart", text)


if __name__ == "__main__":
    unittest.main()
