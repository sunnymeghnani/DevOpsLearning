"""Run after building: python3 -m unittest discover -s tests -v."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest

from source_catalog import CATALOGS, LABELS, case_anchor, community_threads, load_catalog, safe_url, source_anchor, source_status

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = Counter()
        self.links = []
        self.scripts = []
        self.script = None
        self.script_type = None
        self.statuses = Counter()
        self.entries = 0
        self.external_loads = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids[attrs['id']] += 1
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if 'data-source-status' in attrs:
            self.statuses[attrs['data-source-status']] += 1
        if 'source-entry' in attrs.get('class', '').split():
            self.entries += 1
        if tag == 'script':
            self.script = ''
            self.script_type = attrs.get('type', '')
        if tag in ('script', 'img', 'iframe', 'link'):
            url = attrs.get('src', attrs.get('href', ''))
            if url.startswith(('https:', 'http:', '//')):
                self.external_loads.append(url)

    def handle_data(self, text):
        if self.script is not None:
            self.script += text

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append((self.script_type, self.script))
            self.script = None


class SourceSemantics(unittest.TestCase):
    def test_discovery_is_not_promoted_by_visited_flag(self):
        for kind, url in [('search', 'https://example.com/search?q=tls'),
                          ('github-issues-list', 'https://github.com/example/repo/issues'),
                          ('postmortem-collection', 'https://example.com/incidents')]:
            with self.subTest(kind=kind):
                self.assertEqual(source_status({'type': kind, 'url': url, 'verified': True}, {url: {}}), 'discovery')

    def test_recorded_is_distinct_from_a_scoped_check(self):
        source = {'type': 'docs', 'url': 'https://example.com/doc', 'verified': True}
        self.assertEqual(source_status(source, {}), 'recorded')
        self.assertEqual(source_status(source, {source['url']: {}}), 'reviewed')
        source['verified'] = False
        self.assertEqual(source_status(source, {}), 'unverified')

    def test_reject_active_or_credential_urls(self):
        for url in ['javascript:alert(1)', '//example.com', 'file:///tmp/file',
                    'https://user:secret@example.com', 'https://example.com\n', 'https://[bad']:
            self.assertFalse(safe_url(url), url)
        self.assertTrue(safe_url('https://example.com/?q=tls&tag=proxy'))

    def test_reading_a_thread_does_not_verify_its_fix(self):
        for access in ('thread', 'excerpt', 'report'):
            source = {'url': 'https://example.com/thread', 'access': access, 'verified': True}
            self.assertEqual(source_status(source, {source['url']: {}}), access)

    def test_curated_readings_cover_domains_with_explicit_limits(self):
        records = community_threads(ROOT)
        self.assertEqual({r['domain'] for r in records}, {d for d, _, _ in CATALOGS})
        self.assertEqual(len({r['url'] for r in records}), len(records))
        for record in records:
            for field in ('report', 'outcome', 'lesson', 'next', 'environment', 'read_on'):
                self.assertTrue(record[field], (record['domain'], field))


class BuiltSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {name: Page((ROOT / name).read_text()) for name in ('index.html', 'artifact.html')}
        cls.checks = json.loads((ROOT / 'research/source-checks.json').read_text())

    def test_ids_links_and_offline_assets(self):
        for name, page in self.pages.items():
            with self.subTest(name=name):
                self.assertFalse([key for key, n in page.ids.items() if n > 1])
                # Map-node hashes are virtual routes, not element IDs.
                broken = [url for url in page.links if url.startswith('#') and not url.startswith(('#map.', '#map/')) and url[1:] not in page.ids]
                self.assertEqual(broken, [])
                self.assertEqual(page.external_loads, [])
                self.assertFalse([url for url in page.links if url.endswith('.md') and not url.startswith(('https://', 'http://'))])
                for domain, _, _ in CATALOGS:
                    self.assertIn(source_anchor(domain), page.ids)

    def test_all_saved_problems_and_source_statuses_survive_build(self):
        expected = Counter()
        entries = 0
        for domain, _, _ in CATALOGS:
            data = load_catalog(ROOT, domain)
            for problem in data['problems']:
                entries += 1
                seen = set()
                for source in problem.get('sources', []):
                    self.assertTrue(safe_url(source['url']))
                    if source['url'] not in seen:
                        seen.add(source['url'])
                        expected[source_status(source, self.checks)] += 1
        for page in self.pages.values():
            self.assertEqual(page.entries, entries)
            self.assertEqual(page.statuses, expected)
            self.assertLessEqual(set(page.statuses), set(LABELS))

    def test_community_cases_are_in_libraries_and_source_index(self):
        for page in self.pages.values():
            for domain, _, module in CATALOGS:
                anchor = 'm' + module.split('-', 1)[0] + '-community-case-reading'
                self.assertIn(anchor, page.ids)
                self.assertIn('#' + anchor, page.links)
            for record in community_threads(ROOT):
                self.assertGreaterEqual(page.links.count(record['url']), 2)

    def test_expanded_incidents_have_exact_links_and_scoped_solutions(self):
        additions = json.loads((ROOT / 'research/community-incidents.json').read_text())
        self.assertEqual(len(additions), 16)
        self.assertEqual(sum(r['kind'] == 'postmortem' for r in additions), 6)
        self.assertEqual(sum(r['access'] == 'report' for r in additions), 7)
        terraform = next(r for r in additions if r['domain'] == 'cloudiac')
        self.assertEqual(terraform['resolution'], 'partial-improvement')
        self.assertIn('unresolved', terraform['outcome'])
        for name, page in self.pages.items():
            text = (ROOT / name).read_text()
            self.assertEqual(text.count('class="incident-solution"'), len(additions))
            self.assertIn('m56-incident-questions-and-documented-resolutions', page.ids)
            for record in additions:
                self.assertIn(case_anchor(record), page.ids)
                self.assertGreaterEqual(page.links.count('#' + case_anchor(record)), 2)
                for field in ('question', 'evidence', 'fix', 'verification', 'prevention', 'resolution'):
                    self.assertTrue(record[field])

    def test_scripts_parse_and_map_links_resolve(self):
        for name, page in self.pages.items():
            for typ, script in page.scripts:
                if typ == 'application/json':
                    graph = json.loads(script)
                    if not isinstance(graph, dict) or 'path' not in graph:
                        continue  # other embedded data (#drill-data) is checked by test_drills.py
                    order = {nid: i for i, nid in enumerate(graph['path'])}
                    self.assertEqual(len(order), len(graph['nodes']))
                    for node in graph['nodes']:
                        for parent in node.get('prereqs', []):
                            self.assertLess(order[parent], order[node['id']])
                        for kind in ('study', 'links'):
                            for item in node.get(kind, []):
                                if 'file' in item:
                                    self.assertIn(item['anchor'], page.ids)
                else:
                    result = subprocess.run(['node', '--check'], input=script, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, f'{name}: {result.stderr}')


if __name__ == '__main__':
    unittest.main()
