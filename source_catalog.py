"""Offline source index built from the saved research, never by fetching URLs."""
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit
from markdown.extensions.toc import slugify

CATALOGS = (
    ("linux", "Linux & systems", "41-problems-linux-systems.md"),
    ("network", "Network, DNS, TLS & VPN", "42-problems-network-dns-tls-vpn.md"),
    ("proxy", "Traefik & reverse proxies", "43-traefik-and-reverse-proxies.md"),
    ("docker", "Docker, Swarm & registries", "44-problems-docker-swarm-registry.md"),
    ("paas", "Dokploy & self-hosted PaaS", "45-dokploy-and-self-hosted-paas.md"),
    ("k8s", "Kubernetes", "46-problems-kubernetes.md"),
    ("cicd", "CI/CD", "47-cicd-gitlab-jenkins-actions-argocd.md"),
    ("security", "Wazuh & security", "48-wazuh-and-security-tools.md"),
    ("observability", "Observability", "49-observability-stack-problems.md"),
    ("cloudiac", "Cloud, IaC & Proxmox", "50-problems-cloud-iac-proxmox.md"),
    ("data", "Databases, storage & backup", "51-problems-databases-storage-backup.md"),
    ("daily", "DevOps day to day", "52-devops-day-to-day.md"),
)
BY_MODULE = {module: domain for domain, _, module in CATALOGS}
SOURCE_HEADINGS = {domain: f"Sources: {title}" for domain, title, _ in CATALOGS}


def source_anchor(domain):
    return "m56-" + slugify(SOURCE_HEADINGS[domain], "-")


LABELS = {
    "thread": "Community thread page read · not a verified fix",
    "excerpt": "Indexed community excerpt read · incomplete",
    "report": "First-party report read · historical account",
    "reviewed": "Checked 2026-10-04 · limited scope",
    "recorded": "Reported checked in original research",
    "unverified": "Not verified in saved research",
    "discovery": "Discovery link · not evidence for a fix",
}

RESOLUTIONS = {
    "author-confirmed": "Author reports recovery",
    "reply-reported": "Reply reports a similar-case fix",
    "upstream-fix": "Upstream fix evidenced",
    "workaround": "Workaround only",
    "partial-improvement": "Partial improvement",
    "documented-remediation": "Vendor-documented remediation",
    "service-restored": "Service restored in report",
    "service-restored-data-loss": "Restored with reported data loss",
}


def safe_url(value):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ("https", "http") and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def source_status(source, checks):
    """A search/listing is discovery even if an earlier researcher visited it."""
    url = source.get("url", "")
    kind = str(source.get("type", "")).lower()
    path = urlsplit(url).path.lower() if safe_url(url) else ""
    if any(word in kind for word in ("search", "listing", "collection", "forum-top", "issues-list", "postmortems")) or "/search" in path or path.rstrip("/").endswith("/issues"):
        return "discovery"
    if source.get("access") in ("thread", "excerpt", "report"):
        return source["access"]
    if url in checks:
        return "reviewed"
    return "recorded" if source.get("verified") is True else "unverified"


def community_threads(root):
    records = json.loads((Path(root) / "research/community-threads.json").read_text(encoding="utf-8"))
    records += json.loads((Path(root) / "research/community-incidents.json").read_text(encoding="utf-8"))
    seen_urls, seen_anchors = set(), set()
    for record in records:
        if record["domain"] not in SOURCE_HEADINGS or record["access"] not in ("thread", "excerpt", "report"):
            raise ValueError("Invalid community domain or access status")
        if record["url"] in seen_urls or case_anchor(record) in seen_anchors:
            raise ValueError("Duplicate community URL or case anchor")
        seen_urls.add(record["url"])
        seen_anchors.add(case_anchor(record))
        if "kind" in record:
            if record["kind"] not in ("thread", "postmortem", "advisory") or record.get("resolution") not in RESOLUTIONS:
                raise ValueError("Invalid incident kind or outcome")
            for field in ("question", "evidence", "fix", "verification", "prevention", "level"):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    raise ValueError(f"Incident is missing {field}")
        for field in ("url", "official_url", "extra_url"):
            if field in record and not safe_url(record[field]):
                raise ValueError(f"Unsafe community URL: {field}")
    return records


def case_anchor(record):
    module = next(m for d, _, m in CATALOGS if d == record["domain"])
    return "m" + module.split("-", 1)[0] + "-" + slugify(record["title"], "-")


def community_directory(root):
    records = community_threads(root)
    expanded = [r for r in records if "kind" in r]
    sites = {urlsplit(r["url"]).hostname for r in records}
    postmortems = sum(r.get("kind") == "postmortem" for r in records)
    excerpts = sum(r["access"] == "excerpt" for r in records)
    parts = ["\n## Incident questions and documented resolutions\n",
             f"**{len(records)} case readings across {len(sites)} source websites**, including "
             f"{postmortems} first-party production postmortems. The latest {len(expanded)} additions "
             "include a question, deciding evidence, reported recovery, and proposed verification/prevention. "
             f"The {excerpts} excerpt-only readings retain their limitations.\n",
             "These are real reported incidents and historical discussions, **not a live outage feed**. "
             "Outcome labels describe the source's evidence, not a fix tested on your systems. "
             "A workaround, partial improvement or reply about a different environment is not a confirmed permanent solution.\n",
             "| Question or case | Stage | Source | Outcome scope |\n|---|---|---|---|"]
    for domain, _, _ in CATALOGS:
        for r in records:
            if r["domain"] == domain:
                parts.append(f"| [{r['title']}](#{case_anchor(r)}) | {r.get('level', 'See topic path')} | "
                             f"{r['platform']} | {RESOLUTIONS.get(r.get('resolution'), 'Read case limitations')} |")
    parts.extend(["\n### Practise the decision before reading the resolution\n",
                  "Choose a case at your level. Write your first hypothesis and the evidence that would disprove it. "
                  "Open the case's expandable answer, compare the reported action with your prediction, then design the "
                  "smallest disposable lab or tabletop check. Junior practice focuses on identifying the failing boundary; "
                  "senior practice adds data integrity, rollback safety, incident coordination and prevention. "
                  "No lab has been run or completion tick added by this integration.\n"])
    return '\n'.join(parts)


def load_catalog(root, domain):
    """Add explicitly related readings without rewriting the historical catalogs."""
    data = json.loads((Path(root) / "research" / f"{domain}.json").read_text(encoding="utf-8"))
    for record in community_threads(root):
        if record["domain"] != domain:
            continue
        matches = [p for p in data["problems"] if p["title"] == record["problem"]]
        if len(matches) != 1:
            raise ValueError(f"Community reading has no unique related problem: {record['problem']}")
        sources = matches[0].setdefault("sources", [])
        sources[:] = [s for s in sources if s.get("url") != record["url"]]
        sources.append({"title": f"{record['platform']}: {record['title']}",
                        "url": record["url"], "type": "related-community-reading",
                        "access": record["access"], "read_on": record["read_on"],
                        "case_anchor": case_anchor(record),
                        "community_domain": domain})
    return data


def community_markdown(root, module):
    """Render learning prompts, never progress records or executed incident reports."""
    domain = BY_MODULE.get(module)
    records = [r for r in community_threads(root) if r["domain"] == domain]
    if not records:
        return ""
    parts = ["\n## Community case reading\n",
             "Real community discussions and first-party incident reports for your personal learning path. "
             "These are other people's reports, not incidents you have completed. "
             "Exercises below are proposed lab work; no progress is marked. "
             "This initial selection illustrates reasoning, not how frequently a problem occurs.\n"]
    for r in records:
        parts.extend([f"### {r['title']}\n",
                      f"[Original {r['platform']} source]({r['url']}) · {LABELS[r['access']]} · retrieved {r['read_on']}.\n",
                      f"**Context and limits:** {r['environment']}.\n"])
        if "question" in r:
            parts.extend([f"**Incident question · {r['level']}:** {r['question']}\n",
                          f"**Outcome scope:** {RESOLUTIONS[r['resolution']]}.\n",
                          '<details class="incident-solution" markdown="1"><summary>Read the evidence, reported solution and next checks</summary>\n'])
        parts.extend([
                      f"**Reported symptom:** {r['report']}\n",
                      *( [f"**Deciding evidence:** {r['evidence']}\n", f"**How it was fixed or mitigated in the source:** {r['fix']}\n"] if "question" in r else [] ),
                      f"**What was established—and what was not:** {r['outcome']}\n",
                      f"**Reasoning to learn (handbook synthesis):** {r['lesson']}\n",
                      f"Compare with [{r['official_title']}]({r['official_url']}). " +
                      (f"Also see [{r['extra_title']}]({r['extra_url']})." if r.get('extra_url') else '') + "\n",
                      *( [f"**Verification you can practise (not claimed source actions):** {r['verification']}\n", f"**Prevention and safety (handbook synthesis):** {r['prevention']}\n"] if "question" in r else [] ),
                      f"**Your next lab, not completed work:** {r['next']}\n",
                      f"Related problem in this library: {r['problem']}. "
                      f"[Browse this domain's sources](#{source_anchor(domain)}).\n"])
        if "question" in r:
            parts.append('</details>\n')
    return '\n'.join(parts)


def catalog_markdown(root):
    root = Path(root)
    checks = json.loads((root / "research/source-checks.json").read_text(encoding="utf-8"))
    parts, counts = [], {key: 0 for key in LABELS}
    total_problems = 0
    urls = set()
    for domain, title, module in CATALOGS:
        data = load_catalog(root, domain)
        problems = data["problems"]
        total_problems += len(problems)
        parts.extend([f"\n## {SOURCE_HEADINGS[domain]}\n", f"**{title}** · [Open the problem library]({module}) · {len(problems)} research entries.\n"])
        date = data.get("checked_on")
        if date:
            parts.append(f"Catalog's recorded check date: {html.escape(str(date))}. This is historical metadata, not a new verification.\n")
        parts.append(f'<div class="source-group" data-source-domain="{domain}">')
        for problem in problems:
            name = str(problem.get("title", "Untitled research entry"))
            key = hashlib.sha256((domain + ":" + name).encode()).hexdigest()[:16]
            parts.append(f'<details class="source-entry" id="source-{key}"><summary>{html.escape(name)}</summary>')
            parts.append(f'<p>{html.escape(str(problem.get("tool", "")))} · {html.escape(str(problem.get("level", "")))}</p><ul>')
            seen = set()
            for source in problem.get("sources", []):
                url = source.get("url", "")
                if not safe_url(url):
                    raise ValueError(f"{domain}: unsafe or malformed source URL for {name}")
                if url in seen:
                    continue
                seen.add(url)
                urls.add(url)
                status = source_status(source, checks)
                counts[status] += 1
                label = html.escape(str(source.get("title") or url))
                kind = html.escape(str(source.get("type", "reference")))
                parts.append(f'<li data-source-status="{status}"><a href="{html.escape(url, quote=True)}">{label}</a> '
                             f'<span class="source-badge">{LABELS[status]}</span> <small>{kind}</small>')
                if status == "reviewed":
                    parts.append(f'<p class="source-scope">Checked claim: {html.escape(checks[url]["claim"])}</p>')
                if status in ("thread", "excerpt", "report"):
                    parts.append(f'<p class="source-scope">Retrieved {html.escape(source["read_on"])}. Related reading added during integration, not a claim that this source originally informed the entire problem entry. <a href="#{html.escape(source["case_anchor"], quote=True)}">Read the case, evidence limits and proposed lab</a>.</p>')
                parts.append('</li>')
            if not seen:
                parts.append('<li data-source-status="unverified">No source was recorded for this entry.</li>')
            parts.append('</ul></details>')
        parts.append('</div>\n')
    options = ''.join(f'<option value="{d}">{html.escape(t)}</option>' for d, t, _ in CATALOGS)
    status_options = ''.join(f'<option value="{k}">{v}</option>' for k, v in LABELS.items())
    intro = f'''
## Browse the saved sources

{total_problems} research entries across {len(CATALOGS)} domains; {sum(counts.values())} source associations
({len(urls)} distinct URLs). Counts include links reused by several problems, and research entries
are not a one-to-one inventory of the handbook's edited problem entries.

| Source status | Associations |
|---|---:|
''' + '\n'.join(f'| {LABELS[k]} | {v} |' for k, v in counts.items()) + f'''

<div class="source-controls no-index">
<label>Find a problem or source <input id="source-query" type="search" placeholder="Wazuh, TLS, GitLab…"></label>
<label>Domain <select id="source-domain"><option value="">All domains</option>{options}</select></label>
<label>Source status <select id="source-status"><option value="">All source statuses</option>{status_options}</select></label>
<button type="button" id="source-reset">Reset filters</button>
<p id="source-count" role="status" aria-live="polite">{total_problems} research entries. Open a problem to see its sources.</p>
</div>
'''
    return intro + '\n'.join(parts)


SOURCE_CSS = """
.source-controls { display:flex; flex-wrap:wrap; gap:12px; padding:14px; background:var(--bg2); border:1px solid var(--border); border-radius:10px; }
.source-controls label { display:flex; flex-direction:column; gap:4px; flex:1 1 180px; }
.source-controls input,.source-controls select,.source-controls button { font:inherit; color:var(--fg); background:var(--bg); border:1px solid var(--border); border-radius:6px; padding:8px; max-width:100%; }
.source-controls p { flex-basis:100%; margin:0; }
.source-entry,.incident-solution { border:1px solid var(--border); border-radius:8px; margin:8px 0; padding:10px 14px; }
.source-entry summary,.incident-solution summary { cursor:pointer; font-weight:600; }
.source-entry li { margin-bottom:10px; overflow-wrap:anywhere; }
.source-badge { display:inline-block; color:var(--fg-dim); font-size:12px; border:1px solid var(--border); border-radius:4px; padding:2px 5px; }
.source-scope { font-size:13px; }
.source-notice { border-left:3px solid var(--accent); padding:8px 12px; background:var(--bg2); }
"""

SOURCE_SCRIPT = """
<script>
(() => {
  const q=document.getElementById('source-query'), domain=document.getElementById('source-domain'), status=document.getElementById('source-status');
  if(!q) return;
  const groups=[...document.querySelectorAll('.source-group')];
  const entries=groups.flatMap(group=>[...group.querySelectorAll('.source-entry')].map(el=>({el,group,text:[...el.children].filter(child=>child.tagName!=='UL').map(child=>child.textContent).join(' ').toLowerCase(),refs:[...el.querySelectorAll('[data-source-status]')]})));
  function filter() {
    const term=q.value.trim().toLowerCase(); let shown=0;
    entries.forEach(({el,group,text,refs})=>{
      const domainOK=!domain.value || domain.value===group.dataset.sourceDomain;
      refs.forEach(ref=>{ref.hidden=!!status.value && status.value!==ref.dataset.sourceStatus;});
      const matchingRefs=refs.filter(ref=>!ref.hidden);
      const textOK=text.includes(term) || matchingRefs.some(ref=>ref.textContent.toLowerCase().includes(term));
      el.hidden= !domainOK || !textOK || !matchingRefs.length;
      if(!el.hidden) shown++;
    });
    groups.forEach(group=>{group.hidden=![...group.children].some(el=>!el.hidden);
      // Hide the catalog intro and heading together, including any historical date.
      let prev=group.previousElementSibling;
      while(prev && !/^H[12]$/.test(prev.tagName)){prev.hidden=group.hidden;prev=prev.previousElementSibling;}
      if(prev && prev.tagName==='H2') prev.hidden=group.hidden;
    });
    document.getElementById('source-count').textContent=`${shown} of ${entries.length} research entries${shown ? '. Open a problem to see matching sources.' : '. No matches—try another term or reset filters.'}`;
    document.dispatchEvent(new Event('handbook-layout'));
  }
  function reset(){q.value='';domain.value='';status.value='';filter();}
  q.addEventListener('input',filter); domain.addEventListener('change',filter);status.addEventListener('change',filter);
  document.getElementById('source-reset').addEventListener('click',reset);
  window.__sourcesReveal=el=>{if(el && el.closest('#m56')) reset();};
  document.addEventListener('click',e=>{if(e.target.closest('a[href^="#m56"]')) reset();});
  function revealHash(){ let id; try{id=decodeURIComponent(location.hash.slice(1));}catch(_){return;} const el=document.getElementById(id); if(el && el.closest('#m56')){reset();if(el.tagName==='DETAILS') el.open=true; el.scrollIntoView({block:'start'});} }
  addEventListener('hashchange',revealHash); revealHash();
})();
</script>
"""
