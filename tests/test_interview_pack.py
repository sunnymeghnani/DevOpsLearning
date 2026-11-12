"""Structure/provenance checks only: no lab or server commands are executed."""
import json
from pathlib import Path
import re
import unittest
from source_catalog import safe_url

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'interview'


class InterviewPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PACK / 'manifest.json').read_text())
        cls.modules = cls.manifest['modules']

    def test_every_numbered_module_has_a_matching_pack(self):
        expected = {p.name for p in ROOT.glob('[0-9][0-9]-*.md')}
        self.assertEqual(len(expected), 57)
        self.assertEqual({m['file'] for m in self.modules}, expected)
        self.assertEqual({p.name for p in PACK.glob('[0-9][0-9]-*.md')}, expected)
        self.assertEqual(self.manifest['scenario_count'], len(self.modules))

    def test_questions_and_teaching_contract(self):
        ids = []
        for module in self.modules:
            content = (PACK / module['file']).read_text()
            found = re.findall(r'^## (M\d{2}-Q\d{2}) ', content, re.M)
            self.assertEqual(found, module['question_ids'])
            ids.extend(found)
            for required in ('Expected reasoning', 'Why this order', 'Common trap',
                             'Verification and next practice', 'Sources and limits',
                             'Labs are proposed, not executed', 'Provenance:'):
                self.assertIn(required, content)
            self.assertEqual(content.count('<details>'), 1)
            self.assertEqual(content.count('</details>'), 1)
        self.assertEqual(len(ids), self.manifest['prompt_count'])
        self.assertEqual(len(set(ids)), 114)

    def test_source_ids_and_relative_links_resolve(self):
        ledger = (PACK / 'SOURCES.md').read_text()
        source_ids = set(re.findall(r'^## ([A-Z]\d{2})$', ledger, re.M))
        for module in self.modules:
            self.assertTrue(set(module['sources']) <= source_ids)
        for path in PACK.glob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if target.startswith(('http:', 'https:')):
                    self.assertTrue(safe_url(target), target)
                    continue
                file, _, anchor = target.partition('#')
                resolved = path.parent / file if file else path
                self.assertTrue(resolved.is_file(), (path.name, target))
                if resolved.name == 'SOURCES.md' and anchor:
                    self.assertIn(anchor, {s.lower() for s in source_ids} | {'interview-context'})

    def test_provenance_and_site_integration(self):
        # The pack is now integrated into the website (user request, 2026-10-04):
        # every prompt appears, answers stay collapsed, and nothing records completion.
        adapted = [m['module'] for m in self.modules if m['provenance'] == 'adapted-self-report']
        self.assertEqual(adapted, ['10'])
        self.assertEqual(sum(m['provenance'] == 'original-practice' for m in self.modules), 56)
        for name in ('index.html', 'artifact.html'):
            content = (ROOT / name).read_text()
            for module in self.modules:
                for qid in module['question_ids']:
                    self.assertIn(qid, content, (name, qid))
            self.assertEqual(content.count('<details class="iv-answer"'), self.manifest['scenario_count'])
            self.assertNotIn('interview/manifest.json', content)
        self.assertNotIn('completed', self.manifest)

    def test_each_pack_sits_on_its_declared_stage_page(self):
        from interview_site import STAGE_PAGE, load_packs, section_id_for
        content = (ROOT / 'index.html').read_text()
        sections = {}
        for stage, page in STAGE_PAGE.items():
            start = content.index(f'id="{section_id_for(page)}"')
            end = content.find('<section', start + 1)
            sections[stage] = content[start:end if end > 0 else None]
        packs = load_packs(str(ROOT))
        self.assertEqual(len(packs), self.manifest['scenario_count'])
        for pack in packs:
            for qid in pack['ids']:
                self.assertIn(qid, sections[pack['stage']], (pack['file'], pack['stage']))
                others = [s for s in sections if s != pack['stage']]
                self.assertFalse(any(f'>{qid} —' in sections[s] for s in others), qid)


if __name__ == '__main__':
    unittest.main()
