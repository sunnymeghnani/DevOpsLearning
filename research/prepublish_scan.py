#!/usr/bin/env python3
"""Pre-publish scan of artifact.html: personal data, secret-looking strings,
non-documentation IP addresses, and external resource loads.

    python3 research/prepublish_scan.py artifact.html
"""
import ipaddress
import re
import sys
from collections import Counter

path = sys.argv[1] if len(sys.argv) > 1 else "artifact.html"
h = open(path, encoding="utf-8").read()
issues = []

# 1. personal data of the handbook's owner
for pat in [r"sunnymeghnani", r"/home/sunny\b", r"\bsunny\b", r"@gmail\.com"]:
    for m in re.finditer(pat, h, flags=re.I):
        issues.append(("personal", pat, h[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")))

# 2. secret-looking strings in real formats (AWS's documented example key is allowed)
secret_pats = {
    "aws_access_key": r"\b(AKIA|ASIA)(?!IOSFODNN7EXAMPLE)[0-9A-Z]{16}\b",
    "private_key": r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----",
    "github_token": r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
    "gitlab_token": r"\bglpat-[A-Za-z0-9_\-]{20,}\b",
    "slack_token": r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    "jwt": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
    # a printed Docker Swarm join token; the handbook's stand-ins (SWMTKN-1-TOKEN, SWMTKN-1-…) are upper case
    "swarm_join_token": r"SWMTKN-1-[0-9a-z]{8,}",
}
for name, pat in secret_pats.items():
    for m in re.finditer(pat, h):
        issues.append(("secret?", name, h[max(0, m.start() - 80):m.end() + 40].replace("\n", " ")))

# 3. IPv4 outside documentation / private / well-known public ranges
allowed_nets = [ipaddress.ip_network(n) for n in [
    "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24",
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "127.0.0.0/8", "169.254.0.0/16", "0.0.0.0/8", "100.64.0.0/10",
    "224.0.0.0/4", "240.0.0.0/4", "198.18.0.0/15",
]]
allowed_hosts = {"8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9", "149.112.112.112",
                 "208.67.222.222", "208.67.220.220", "4.2.2.2"}
odd = Counter()
for m in re.finditer(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])", h):
    s = m.group(1)
    try:
        ip = ipaddress.ip_address(s)
    except ValueError:
        continue
    if s in allowed_hosts or any(ip in n for n in allowed_nets):
        continue
    odd[s] += 1

# 4. external resource loads
ext = []
for pat in [r"<script[^>]*\bsrc\s*=\s*[\"']?https?:", r"<link[^>]*rel=[\"']?stylesheet[^>]*href=[\"']?https?:",
            r"@import\s+url\(\s*[\"']?https?:", r"<img[^>]*\bsrc\s*=\s*[\"']?https?:", r"<iframe",
            r"url\(\s*[\"']?https?:"]:
    ext += [h[m.start():m.start() + 120] for m in re.finditer(pat, h, flags=re.I)]

print(f"file: {path}  size: {len(h.encode('utf-8')) / 1024 / 1024:.2f} MB")
print(f"personal/secret findings: {len(issues)}")
for kind, name, ctx in issues[:40]:
    print(f"  [{kind}] {name}: …{ctx}…")
print(f"external resource loads: {len(ext)}")
for e in ext[:10]:
    print("  ", e)
print(f"IPv4 outside doc/private/well-known ranges: {len(odd)} distinct")
for s, c in odd.most_common(40):
    print(f"   {s} x{c}")
