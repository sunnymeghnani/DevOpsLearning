# Free interactive learning tools: networking, DNS, TLS, HTTP, proxies, VPNs

Scope: free, browser-based tools in the same family as Protocol Explorer (visualisers, simulators, explainers, calculators, config generators/validators). Reader: an on-prem Ubuntu/Docker/Traefik/Kubernetes engineer moving to cloud. All domains in `known_domains.txt` were skipped (for example nginxconfig.io was dropped because it 301-redirects to digitalocean.com, which is a known domain).

How each tool was checked (9 Nov 2026): every page was fetched as text with WebFetch. No form was submitted, nothing was uploaded, no login was used and nothing was downloaded or run. So "verified" below means the page is live and states the features listed. Interactive behaviour was **not** exercised. Where a fetch failed (403/bot wall/TLS error), the tool is listed under Q4 with what is known from search snippets only.

Level key: L0 = no background, L1 = beginner, L2 = practitioner, L3 = advanced or debugging, L4 = expert or protocol internals.

## Q1. Which tools are verified, and how do they rank?

### Takeaway
26 tools were verified live, plus 5 lower-confidence extras. The strongest picks are:
- **TLSRef Configurator**, which has replaced the Mozilla SSL Config Generator and covers nginx, Apache, HAProxy, Traefik, Caddy and AWS ALB/ELB.
- **Visual Subnet Calculator**, which has AWS, Azure and OCI modes.
- **Kurose & Ross interactive problems**, for TCP, DNS and subnetting.
- **DNSViz**, **Let's Debug** plus **unboundtest**, **REDbot**, **quic.xargs.org**, **Globalping** and the **Toolsbase Traefik v3 validator**.

There are gaps. The fetcher found no maintained, hosted HAProxy-specific generator and no verified TCP congestion visualiser of good quality.

### Cited Findings

**Ranked list (1 = link first)**

| # | Tool | Category | Level | Roadmap ids | Data leaves browser? |
|---|---|---|---|---|---|
| 1 | TLSRef Configurator | TLS config generator | L2 | tls-certs, reverse-proxy, traefik, apache-vhosts, letsencrypt-acme | No secrets entered (you pick server and version) |
| 2 | Visual Subnet Calculator | Subnet/CIDR | L1–L2 | net-basics, routing-nat, vpn-mesh, deployment-patterns | The share URL encodes your plan |
| 3 | Kurose & Ross interactive problems | TCP/DNS/IP exercises | L1–L2 | net-basics, sockets-ports, dns-deep, routing-nat, network-speed, http-curl | No |
| 4 | DNSViz | DNSSEC/delegation visualiser | L2–L3 | dns-deep, network-problems | Domain name only (public data) |
| 5 | Let's Debug | ACME/LE diagnostics | L2 | letsencrypt-acme, dns-deep, tls-certs | Domain name only |
| 6 | REDbot | HTTP header/caching linter | L2–L3 | http-curl, reverse-proxy, proxy-problems, site-down-walk | URL fetched remotely |
| 7 | quic.xargs.org (+ tls12/dtls) | Byte-by-byte QUIC/TLS | L3–L4 | tls-certs, http-curl | No |
| 8 | Globalping | Multi-location ping/mtr/dig/curl | L1–L2 | network-speed, dns-deep, site-down-walk | Target only |
| 9 | Toolsbase Traefik Config Validator | Traefik v3 linter | L2 | traefik, traefik-legacy-routes, traefik-deep-dive | Claims no (client-side) |
| 10 | unboundtest.com | DNS resolver log (LE-like) | L3 | letsencrypt-acme, dns-deep | Domain name only |
| 11 | Explained from First Principles: The Internet | Long-form interactive explainer | L1–L3 | net-basics, sockets-ports, dns-deep, tls-certs, http-curl | DNS tool queries Google's API |
| 12 | Will It CORS? (HTTP Toolkit) | CORS wizard | L1–L2 | http-curl, reverse-proxy, proxy-problems | Not stated |
| 13 | curlconverter | curl → code | L1 | http-curl | No (stated) |
| 14 | Traceroute Visualizer (kriztalz.sh) | Traceroute map | L1 | network-speed, routing-nat, site-down-walk | Hop IPs go to IPinfo/PeeringDB |
| 15 | Encapsulation calculator (baturin.org) | Tunnel MTU/overhead | L2–L3 | vpn-mesh, network-speed | Not stated (nothing secret entered) |
| 16 | Is BGP safe yet? (Cloudflare) | BGP/RPKI explainer + ISP test | L0–L1 | routing-nat | Test loads a probe site |
| 17 | BGPlay (Massimo Candela instance) | BGP route-change animation | L3 | routing-nat | Prefix/ASN only |
| 18 | bgp.tools | AS/prefix explorer + looking glass | L2–L3 | routing-nat | Query only |
| 19 | Hurricane Electric Looking Glass | Looking glass | L3 | routing-nat, network-speed | Query only |
| 20 | Verisign Labs DNSSEC Debugger | DNSSEC chain check | L3 | dns-deep | Domain name only |
| 21 | crt.sh | Certificate Transparency search | L2 | tls-certs, letsencrypt-acme | Query only |
| 22 | CloudPing.info | Browser→cloud-region latency | L1 | network-speed, deployment-patterns | Your browser pings providers |
| 23 | HTTP/3 Check (LiteSpeed) | QUIC/HTTP/3 probe | L2 | http-curl, reverse-proxy, traefik-deep-dive | Domain name only |
| 24 | DevToolLab WireGuard Config Generator | WG config generator | L1–L2 | vpn-mesh | Claims keys stay in browser |
| 25 | Pro Custodibus AllowedIPs Calculator | WireGuard AllowedIPs subtraction | L2 | vpn-mesh, routing-nat | Not stated (CIDRs only) |
| 26 | PCAP Triage Lite | In-browser pcap triage | L2 | packet-capture | Claims no (Web Worker) |
| 27 | A-Packets | Online pcap analyser | L2 | packet-capture | **Yes: uploads, public reports** |
| 28 | Google Admin Toolbox Dig | Web dig | L1 | dns-deep, network-problems | Domain name only |
| 29 | HTTP/3 explained (haxx.se) | Free book/explainer | L2 | http-curl, reverse-proxy | No |
| 30 | cidr.xyz | Visual CIDR bit map | L1 | net-basics | No input beyond CIDR |
| 31 | jodies.de ipcalc | Binary subnet calculator | L1 | net-basics | Yes, server-side CGI (harmless input) |

Lower confidence (live, but quality or completeness not established): Toolkit TCP congestion/handshake sims (toolkit-1m9.pages.dev), Dan McCreary's networking MicroSims, SSLShopper Certificate Decoder, curlbuilder.com and Wireview. Details for each are below.

**Per-tool details**

1. **TLSRef Configurator: https://configurator.tlsref.org/**
   - What it is: the old Mozilla SSL Config Generator page now says it "has moved to TLSRef Configurator" — [ssl-config.mozilla.org](https://ssl-config.mozilla.org/).
   - What it does: generates TLS configs for Apache, AWS ALB, AWS ELB, Caddy, Coturn, Dovecot, Exim, Go, HAProxy, Jetty, lighttpd, LiteSpeed, MySQL, nginx, OpenLiteSpeed, Oracle HTTP, Postfix, PostgreSQL, ProFTPD, Redis, Squid, stunnel, Tomcat and Traefik.
   - Profiles: Modern, Intermediate ("recommended for almost all systems") and Old ("last resort").
   - Maintenance: build 6bcb595, generated 2026-10-13. It links to guidelines at docs.tlsref.org. The page does not name the operator or claim Mozilla affiliation. — [TLSRef Configurator](https://configurator.tlsref.org/)
   - Access and data: free, no sign-up, needs JavaScript. You choose a server and version, not paste a config, so it is safe for real setups.

2. **Visual Subnet Calculator: https://visualsubnetcalc.com**
   - What it does: you split and join subnets visually. Each subnet shows address, range, usable IPs and host count. Subnets can carry notes and colours.
   - Cloud modes: Standard, AWS, Azure and OCI. The AWS and Azure modes account for the addresses each cloud reserves, which matters for the move to cloud.
   - Sharing: "Copy Shareable URL", plus text import and export.
   - Data: the page says it stores nothing.
   - Maintenance: by Caesar Kabalan, inspired by davidc's original tool. v1.4.0, released 2025-05-19. — [Visual Subnet Calculator](https://visualsubnetcalc.com)
   - Caution: a share link encodes your whole internal IP plan. Don't post links for real networks.

3. **Kurose & Ross interactive problems: https://gaia.cs.umass.edu/kurose_ross/interactive/**
   - What it does: generates fresh problems with solutions on request. Topics include:
     - TCP: sequence/ACK numbers with segment loss, RTT and timeout, congestion-window evolution, retransmissions with ACK loss, and TCP mux/demux.
     - DNS: basics, iterative vs recursive queries, and DNS+HTTP delay.
     - IP and routing: subnet addressing, longest-prefix match, NAT, IPv6 tunnelling, and Dijkstra and Bellman-Ford routing.
   - Coverage gaps: there are no TCP-handshake, Go-Back-N/Selective Repeat or BGP exercises.
   - Maintenance and access: 8th edition, © 2010–2025, no login. — [Kurose & Ross interactive](https://gaia.cs.umass.edu/kurose_ross/interactive/)
   - Use: congestion-window and RTT/timeout drills for network-speed; DNS query types for dns-deep.

4. **DNSViz: https://dnsviz.net/**
   - What it does: shows the status of a zone, including the DNSSEC authentication chain and the resolution path, and lists the configuration errors it finds. It describes itself as "a resource for understanding and troubleshooting deployment of" DNSSEC.
   - Maintenance: sponsored by Sandia, Verisign and DNS-OARC, © Casey Deccio 2016–2023. The page shows no newer dates, so check recent activity on its GitHub before relying on it. — [DNSViz](https://dnsviz.net/)
   - Data: the DNSViz servers query public DNS. Only a domain name is entered.

5. **Let's Debug: https://letsdebug.net/**
   - What it does: diagnoses why a Let's Encrypt certificate fails to issue. Tests cover DNS, nameservers, rate limits, networking, CA policy and common web misconfigurations.
   - Validation methods: you pick HTTP-01, DNS-01 or TLS-ALPN-01.
   - Status: open-source API and CLI. Not affiliated with ISRG. — [Let's Debug](https://letsdebug.net/)
   - Data: the server probes your public domain from outside.

6. **REDbot: https://redbot.org/**
   - What it does: "lint for HTTP resources". It tests protocol correctness, cacheability, content negotiation and more.
   - Maintenance: v2.8.1 with httplint 2026.10.4, so it is actively maintained. — [REDbot](https://redbot.org/)
   - Use it to see what Traefik, nginx or Apache actually emit: Cache-Control, Vary, ETag and so on. You type in a URL. Because a browser page cannot fetch arbitrary URLs and read their raw headers, the check must be made from REDbot's side (an inference).

7. **quic.xargs.org: https://quic.xargs.org/**
   - What it does: walks through a QUIC connection byte by byte. That covers the X25519 key exchange, HKDF key derivation, TLS 1.3 handshake messages inside QUIC packets, and ping/pong and close. Each step is reproduced with command-line tools.
   - Sibling pages it links: tls12.xargs.org, dtls.xargs.org and tls13.xargs.org. — [The Illustrated QUIC Connection](https://quic.xargs.org/)
   - Note for the coordinator: tls13.xargs.org is in known_domains, but quic.xargs.org and tls12.xargs.org are different hosts. Merge them into the existing entry if xargs.org should count as one source.
   - Level: L3–L4. This is the HTTP/3 byte-level explainer in the requested scope.

8. **Globalping: https://globalping.io/**
   - What it does: runs ping, traceroute, DNS, MTR and HTTP from probes worldwide. You can pick probes by country, city, ASN, ISP, eyeball or datacenter tags, or cloud region name.
   - Access: "generous free limits", with higher limits for GitHub Sponsors. Anonymous limits are not stated.
   - Maintenance: built by the jsDelivr team, © 2022–2026. — [Globalping](https://globalping.io/)
   - Use: a free stand-in for "is it DNS propagation or my resolver?" (dig from many places) and for cloud-region latency comparisons.

9. **Toolsbase Traefik Config Validator: https://toolsbase.dev/en/developer/traefik-config-validator**
   - What it checks (24 rules for Traefik v3 file-provider YAML and Docker Compose labels):
     - missing services or middlewares that a router references;
     - label typos, such as singular vs plural keys and camel-case mistakes;
     - unbalanced parentheses and quotes in rules;
     - v2 to v3 breaking changes (removed matchers, path placeholders, multi-value matchers).
   - Data: "Everything runs in your browser. Your config is never sent to a server."
   - Maintenance: last updated 29 July 2026. Sibling tools include a Caddyfile validator, a Compose validator and a subnet calculator. — [Toolsbase Traefik validator](https://toolsbase.dev/en/developer/traefik-config-validator)
   - Fit: the best verified match for traefik-legacy-routes (v2 to v3 migration).

10. **unboundtest.com: https://unboundtest.com/**
    - What it does: runs a CAA, A, AAAA or TXT query against a fresh Unbound instance and returns its logs, so caching never gets in the way. The instance is "configured very similarly to Let's Encrypt's production servers".
    - Sharing: share URLs are held in memory only. The operator is not named; the source is linked. — [unboundtest](https://unboundtest.com/)
    - Use: when Let's Encrypt reports a DNS error, this shows the resolver's step-by-step reasoning (L3).

11. **Explained from First Principles: The Internet: https://explained-from-first-principles.com/internet/**
    - What it is: a long-form explainer by Kaspar Etter, first published 5 Aug 2020 and last modified 10 Feb 2026, under a CC BY 4.0 licence.
    - Embedded tools: a DNS lookup tool and a DNSSEC zone walker (both use "an API by Google"), an HTTP(S) request generator, and an IP geolocation tool (uses the IPinfo.io API). — [EF1P Internet](https://explained-from-first-principles.com/internet/); [EF1P home](https://explained-from-first-principles.com/)
    - Gap: the page is about 268k characters, and the full tools list was not read.

12. **Will It CORS? (HTTP Toolkit): https://httptoolkit.com/will-it-cors/**
    - What it does: you describe the cross-origin request you plan to make, and it tells you what the server must send. © 2026 Toolshed Labs.
    - Data: the page does not say whether anything is sent to a server. — [Will It CORS](https://httptoolkit.com/will-it-cors/)

13. **curlconverter: https://curlconverter.com/**
    - What it does: turns a curl command into code. Targets include Python requests, Go, Node, Ansible, HAR, HTTPie, Wget, PowerShell, Rust and more.
    - Data: "We do **not** transmit or record the curl commands you enter"; it is a static, client-side site. — [curlconverter](https://curlconverter.com/)
    - Still strip tokens and cookies copied from DevTools before pasting. It does not explain curl flags; it translates them.

14. **Traceroute Visualizer: https://kriztalz.sh/traceroute-visualizer/**
    - What it does: accepts traceroute, tracert, MTR or flyingroutes output. It produces a hop map, a hop table (location, ISP, loss, RTT), a latency heatmap, IXP flags and a share link.
    - Data: "processed in your browser and not stored on our servers", but hop IPs are looked up through IPinfo and PeeringDB. — [Traceroute Visualizer](https://kriztalz.sh/traceroute-visualizer/)
    - Accuracy (Show HN, about 98 points): commenters said geolocation is often wrong and that MPLS and silent hops mislead. The author agreed it is "not perfectly reliable". — [HN thread](https://hn.svelte.dev/item/45411514)
    - Use: teach it as "geolocation lies", which is itself a lesson.

15. **Encapsulation overhead calculator: https://baturin.org/tools/encapcalc/**
    - What it does: build a protocol stack (WireGuard, VXLAN, GRE, IPv4/IPv6, UDP/TCP, L2TPv3, MPLS, Ethernet with VLAN/QinQ, LISP, STT). It then either subtracts the overhead from the parent MTU or adds it to a payload.
    - Uses: tunnel MTU and fragmentation questions, which are key for WireGuard and overlay networks.
    - Coverage: whether IPsec and PPPoE are included was not confirmed. — [encapcalc](https://baturin.org/tools/encapcalc/)

16. **Is BGP safe yet? (Cloudflare): https://isbgpsafeyet.com/**
    - What it does: explains BGP hijacks and RPKI with clickable animations ("Hijack the request"). A live test announces a deliberately invalid route to check whether your ISP filters it.
    - Operator table: about 30 major operators rated safe, partially safe or unsafe.
    - Maintenance: last updated 3 Feb 2026. — [Is BGP safe yet?](https://isbgpsafeyet.com/)

17. **BGPlay: https://bgplay.massimocandela.com/**
    - What it does: "graphical representation of the inter-domain routing and its evolution over time", based on RIPE RIS data. Hosted by its maintainer, Massimo Candela. — [BGPlay](https://bgplay.massimocandela.com/)
    - Fetch note: the RIPEstat-embedded BGPlay at stat.ripe.net/bgplay returned only a heading to the fetcher. — [RIPEstat BGPlay](https://stat.ripe.net/bgplay)

18. **bgp.tools: https://bgp.tools/**
    - What it does: search by ASN, prefix, DNS name or MAC. Also includes a "super-lg" looking glass.
    - Access: free near-real-time BGP data; monitoring is paid. A Login link exists, but browsing works without it.
    - Maintenance: changelog runs to June 2026. — [bgp.tools](https://bgp.tools/)

19. **Hurricane Electric Looking Glass: https://lg.he.net/**
    - What it does: BGP route, BGP summary (v4/v6), ping and traceroute from HE routers.
    - Access: "best effort", with no login fields on the page. — [HE LG](https://lg.he.net/)

20. **Verisign Labs DNSSEC Debugger: https://dnssec-analyzer.verisignlabs.com/**
    - What it does: steps through a domain's DNSSEC chain. Options let you supply a trust anchor (DS or DNSKEY) and alternative starting nameservers.
    - Maintenance: the page showed a 2026-11-08 timestamp and © 2011–2026. — [Verisign DNSSEC Debugger](https://dnssec-analyzer.verisignlabs.com/)

21. **crt.sh: https://crt.sh/**
    - What it does: Certificate Transparency search by identity, fingerprint or ID. © Sectigo 2015–2026. — [crt.sh](https://crt.sh/)
    - Use: "which certificates exist for my domain?" for letsencrypt-acme renewals and rate limits. Note that public CT logs reveal internal hostnames you put in certificates.

22. **CloudPing.info: https://www.cloudping.info/**
    - What it does: an "HTTP Ping" from your browser to about 170 regions across AWS, GCP, DigitalOcean, Hetzner, Linode, OVH, Vultr, IBM, Scaleway and CoreWeave.
    - Caveat: Azure was listed as unavailable. — [CloudPing.info](https://www.cloudping.info/)

23. **HTTP/3 Check: https://http3check.net/**
    - What it does: first does a TCP GET and reads Alt-Svc. Then it tries HTTP/3 or gQUIC with version negotiation and tests 0-RTT on a second connection. It shows the QUIC versions, connection ID and handshake timings, and can export a qlog.
    - Operator: powered by LiteSpeed.
    - Maintenance: the About text dates from around 2019–2020, but the tool is live. — [HTTP/3 Check about](https://http3check.net/about)

24. **DevToolLab WireGuard Config Generator: https://devtoollab.com/tools/wireguard-config-generator**
    - What it generates: a server wg0.conf and per-peer configs with fresh keypairs, optional PSKs, a QR per peer, a ZIP, and optional iptables NAT PostUp/PostDown rules.
    - Data: "no private key is uploaded or stored", no signup. Undated, © 2026. — [DevToolLab](https://devtoollab.com/tools/wireguard-config-generator)
    - Caution: treat it as a learning aid. For real tunnels, generate keys with `wg genkey` on the host. A search also surfaced generators such as cryptostorm that ask you to type in a private key; avoid those. — [search summary of generators](https://jmrp.io/tools/wireguard-config-generator/)

25. **Pro Custodibus AllowedIPs Calculator: https://www.procustodibus.com/blog/2021/03/wireguard-allowedips-calculator/**
    - What it does: subtracts "Disallowed IPs" from "Allowed IPs" and outputs the CIDR list. For example, 10.0.0.0/8 minus 10.0.1.0/24 gives 16 blocks.
    - Maintenance: article by Justin Ludwig, 21 Mar 2021. Whether it runs client-side is not stated. — [AllowedIPs Calculator](https://www.procustodibus.com/blog/2021/03/wireguard-allowedips-calculator/)
    - Use: a classic split-tunnel pain point for vpn-mesh.

26. **PCAP Triage Lite: https://dfir-toolkit.andreafortuna.org/tools/pcap-triage-lite/**
    - What it does: extracts HTTP requests, DNS queries and TLS SNI from .pcap (pcapng handled heuristically) and exports CSV.
    - Data: "All analysis happens locally in your browser… No data is uploaded" (Web Worker).
    - Maintenance: v1.2.5, updated 19 Mar 2026, by Andrea Fortuna. — [PCAP Triage Lite](https://dfir-toolkit.andreafortuna.org/tools/pcap-triage-lite/)

27. **A-Packets: https://apackets.com/**
    - What it does: turns a pcap/pcapng into an interactive report (hosts, DNS, HTTP, TLS sessions, carved files, visible logins).
    - Free tier: 25 MB, public analysis only, with reports listed in a public feed; it advises "sanitized captures". Private use is paid, from $6.99. — [A-Packets](https://apackets.com/)
    - **Warning:** use only the public sample captures (for example from the Wireshark wiki). Never upload a capture from your own network.

28. **Google Admin Toolbox Dig: https://toolbox.googleapps.com/apps/dig/**
    - What it does: web dig with a raw view. Supported record types were not listed in the fetched text. — [Google Toolbox Dig](https://toolbox.googleapps.com/apps/dig/)

29. **HTTP/3 explained: https://http3-explained.haxx.se/**
    - What it is: "a collaborative effort to document the HTTP/3 and the QUIC protocols", in web and PDF, auto-updated on every commit. — [HTTP/3 explained](https://http3-explained.haxx.se/)
    - Author: generally known to be Daniel Stenberg, but the fetched page does not name him.

30. **cidr.xyz: https://cidr.xyz**
    - What it does: interactive visual CIDR calculator with a bit map, netmask, base and broadcast addresses, usable range, a share link, an FAQ and an embeddable widget.
    - Maintenance: by Yuval Adam, © 2026 Magic Monad. — [cidr.xyz](https://cidr.xyz)

31. **jodies.de ipcalc: https://jodies.de/ipcalc**
    - What it does: shows address, mask, wildcard, network and broadcast in binary, with a gap between network and host bits. Supports supernetting.
    - Data: a server-side CGI (v0.35.2, dated 2005, © 2022). — [ipcalc](https://jodies.de/ipcalc)
    - Use: old but a classic for "see the bits".

**Lower-confidence extras**

- **Toolkit simulators: https://toolkit-1m9.pages.dev/tools/simulators/tcp-congestion**
  - What it claims: in-browser AIMD, Reno and CUBIC with controls for initial and max window, ssthresh, loss rate and speed. Sibling sims: TCP Handshake, HTTP Flow and Load Balancer. © 2026 "Toolkit". The fetch was static, so it was not confirmed working. — [Toolkit TCP congestion](https://toolkit-1m9.pages.dev/tools/simulators/tcp-congestion)
  - Related Show HN (8 Mar 2026): "30+ protocol simulators", 100% client-side. Its listed domain, toolkit.whysonil.dev, did **not resolve** (ENOTFOUND), so the project's home is unstable. — [HN Showcase entry](https://www.hnshowcase.com/post/47301023/toolkit-visual-simulators-for-how-internet-protocols-and-sys)
- **Dan McCreary networking MicroSims: https://dmccreary.github.io/networking/sims/**
  - What it lists: 36 p5.js/vis-network sims, including the TCP handshake, congestion control, CIDR, a DNS walkthrough, a TLS 1.3 walkthrough, NAT traversal and BGP relationships. © 2026. — [MicroSims index](https://dmccreary.github.io/networking/sims/)
  - Status: the TCP congestion comparison page is marked "Status: Specified", with no rendered simulation. Some sims are probably unfinished, so check each before linking. — [congestion sim page](https://dmccreary.github.io/networking/sims/tcp-congestion-control-comparison/)
- **SSLShopper Certificate Decoder: https://www.sslshopper.com/certificate-decoder.html**
  - What it does: decodes a pasted PEM certificate. It does not say whether the paste goes to a server; it also gives the local openssl command. © 2026. — [SSLShopper decoder](https://www.sslshopper.com/certificate-decoder.html)
  - Caution: certificates are public, so this is acceptable, but never paste a private key.
- **curlbuilder.com: https://curlbuilder.com/**
  - What it does: a form that builds a curl command. Options: method, URL, `-d` body, headers, a JSON toggle, `--insecure` and `-v`.
  - Status: undated; client-side rendering is inferred from template markup. — [curlbuilder](https://curlbuilder.com/)
  - Level: L0–L1, and very basic.
- **Wireview: https://wireview.github.io/** (redirect from radiantly.github.io/Wireview)
  - What it claims: a FOSS Hack 2025 project, a "completely client-side online packet viewer" with Wireshark compiled to WASM. — [FOSS United project page](https://fossunited.org/hack/fosshack25/p/6sft94890b)
  - Status: the live page returned only its title to the fetcher (a JS app), so it was not verified working.

### Inferences
- **TLSRef replaces the Mozilla SSL Config Generator.** The handbook should link configurator.tlsref.org instead of ssl-config.mozilla.org. It also covers Traefik and AWS ALB/ELB, which suits the cloud move.
- **No verified generator exists for HAProxy or Traefik alone.** TLSRef covers TLS for both, and Toolsbase validates Traefik v3. Searches found only self-hosted dashboards (haproxy-dashboard), a Docker image (Traefik Labelizer) and a Python CLI (laebelmaker). — [HAProxy search results](https://github.com/alonz22/haproxy-dashboard); [Traefik search results](https://pypi.org/project/laebelmaker/)
- **For TCP congestion, Kurose & Ross is the best verified option.** It has congestion-window evolution and RTT/timeout exercises. The browser visualisers found (Toolkit, the McCreary MicroSims, a Go/WASM ccsim simulator mentioned in a July 2026 blog) are new or unfinished.
- **Many cloud-related labs fit here.** Visual Subnet Calculator (AWS/Azure/OCI), CloudPing.info, Globalping with cloud-region probe selection and TLSRef (ALB/ELB) suit the "moving to cloud" reader.

### Gaps
- No interactive behaviour was exercised, under the no-form-submission rule. "Verified" means live and described as stated.
- Whether several tools run client-side is not stated: Will It CORS, the AllowedIPs calculator, encapcalc, TLSRef and the SSLShopper decoder.
- No dedicated cookie or SameSite playground was found or verified.

## Q2. Where does pasted data go? (safety warnings)

### Takeaway
Most of these tools take only a public domain name, URL or CIDR, which is harmless. The real risks are:
- A-Packets: free uploads are public.
- Share links that encode internal IP plans: Visual Subnet Calculator, Traceroute Visualizer.
- Traceroute hop IPs are sent to IPinfo.
- WireGuard generators: never paste real private keys.
- crt.sh/CT logs: they expose any hostname you put in a certificate.

### Cited Findings
- **A-Packets:** the free tier is public analysis only, and reports appear in a public feed. It says to upload "sanitized captures". — [A-Packets](https://apackets.com/)
- **PCAP Triage Lite:** processes locally in a Web Worker and uploads nothing. This is the safe choice for a real capture. — [PCAP Triage Lite](https://dfir-toolkit.andreafortuna.org/tools/pcap-triage-lite/)
- **Toolsbase Traefik validator:** "Your config is never sent to a server." — [Toolsbase](https://toolsbase.dev/en/developer/traefik-config-validator)
- **curlconverter:** does not transmit or record commands. — [curlconverter](https://curlconverter.com/)
- **Traceroute Visualizer:** processes in the browser, but uses IPinfo and PeeringDB for hop data. — [kriztalz.sh](https://kriztalz.sh/traceroute-visualizer/)
- **EF1P:** the DNS tool and zone walker use Google's API, and IP geolocation uses IPinfo.io. — [EF1P Internet](https://explained-from-first-principles.com/internet/)
- **DevToolLab:** keys are generated in the browser, and "no private key is uploaded or stored". — [DevToolLab](https://devtoollab.com/tools/wireguard-config-generator)
- **WireGuard generators in general:** some require a member login (VPNUK), and cryptostorm asks for your private key in a form. — [search summary of WG generators](https://cryptostorm.is/wgconfzip)
- **jodies ipcalc:** server-side CGI. — [ipcalc](https://jodies.de/ipcalc)

### Inferences
- The handbook should add a one-line warning on each link: "public data only" (DNSViz, REDbot, Let's Debug, HTTP/3 Check, Globalping) or "never real secrets" (WireGuard generators, cert/pcap tools).
- **SSLShopper:** whether the pasted cert goes to a server is not stated. Certificates are public anyway, but the private key must never be pasted.

### Gaps
- No tool's privacy claim was independently audited, for example by watching its network requests.

## Q3. Mapping to roadmap.json topic ids (network and web tracks)

### Takeaway
Every network and web roadmap id gets at least one verified tool except apache-81-444 (a port-shift task, where no specific tool fits beyond TLSRef/REDbot) and ubuntu-netconfig (no netplan/systemd-resolved interactive tool was found).

### Cited Findings
Ids come from roadmap.json. Each tool's source is in Q1.
- **net-basics:** Visual Subnet Calculator, cidr.xyz, jodies ipcalc, Kurose & Ross (subnet addressing, longest-prefix match), EF1P Internet.
- **sockets-ports:** Kurose & Ross (TCP mux/demux, sequence/ACK), EF1P, Toolkit TCP sims (low confidence).
- **routing-nat:** Kurose & Ross (NAT, Dijkstra, Bellman-Ford), Is BGP safe yet?, BGPlay, bgp.tools, HE Looking Glass, AllowedIPs calculator.
- **packet-capture:** PCAP Triage Lite, A-Packets (samples only), Wireview (unverified).
- **dns-deep:** DNSViz, Verisign DNSSEC Debugger, unboundtest, Google Toolbox Dig, Globalping (multi-location dig), EF1P DNS tool and zone walker, Kurose & Ross DNS exercises.
- **network-speed:** Kurose & Ross (congestion window, RTT/timeout), Globalping (mtr), Traceroute Visualizer, CloudPing.info, encapcalc (MTU), HE LG traceroute.
- **network-problems:** DNSViz, Google Dig, Let's Debug, Globalping.
- **vpn-mesh:** DevToolLab WireGuard generator, AllowedIPs calculator, encapcalc, Visual Subnet Calculator (for planning overlay ranges).
- **http-curl:** curlconverter, curlbuilder, REDbot, Will It CORS, HTTP/3 Check, HTTP/3 explained, quic.xargs.org.
- **tls-certs:** TLSRef, quic.xargs.org and tls12.xargs.org, crt.sh, SSLShopper decoder, Let's Debug.
- **letsencrypt-acme:** Let's Debug, unboundtest, crt.sh, TLSRef.
- **reverse-proxy:** TLSRef (nginx/Apache/HAProxy/Traefik), REDbot, Will It CORS, HTTP/3 Check.
- **proxy-problems:** REDbot, Will It CORS.
- **site-down-walk:** Globalping, REDbot, Traceroute Visualizer, Let's Debug.
- **apache-vhosts:** TLSRef (Apache).
- **traefik, traefik-legacy-routes, traefik-deep-dive:** Toolsbase Traefik v3 validator, TLSRef (Traefik), HTTP/3 Check.
- **deployment-patterns:** Visual Subnet Calculator (cloud modes), CloudPing.info.

### Inferences
- **Suggested L0–L1 path:** Is BGP safe yet?, cidr.xyz, Visual Subnet Calculator, Kurose DNS and subnet exercises.
- **L2–L3 path:** DNSViz, Let's Debug and unboundtest, REDbot, TLSRef, Toolsbase validator, Globalping.
- **L4:** quic.xargs.org and tls12.xargs.org.

### Gaps
- ubuntu-netconfig (netplan, systemd-resolved): no interactive browser tool was found in this pass.

## Q4. Candidates that could not be verified or were excluded

### Takeaway
Several well-known tools block automated fetches, so they could not be opened. List them only as "seen via snippet/known, not verified": the Cloudflare Learning Center, whatsmydns.net, dnschecker.org, securityheaders.com, tcpdump101.com, lapo.it/asn1js, NetSim, Zonemaster and the DNSimple comics.

### Cited Findings
- **Cloudflare Learning Center:** https://www.cloudflare.com/learning/ and /learning/dns/what-is-dns/ returned HTTP 403 to the fetcher.
  - A search snippet confirms the page "What happens in a TLS handshake?" exists. It describes the cert/cipher/random exchange after the TCP handshake and the shorter TLS 1.3 handshake without RSA. — [Cloudflare Learning (snippet only)](https://www.cloudflare.com/learning/ssl/ssl-vs-tls/)
  - Its interactive parts were not verified. Cloudflare's verified interactive page in this pass is isbgpsafeyet.com (Q1 #16).
- **DNS propagation checkers:** https://www.whatsmydns.net/ and https://dnschecker.org/ both returned 403. They were not verified; use Globalping's DNS test as a verified alternative.
- **securityheaders.com:** returned 403. Not verified.
- **tcpdump101.com** (a tcpdump/tshark filter builder): the TLS handshake failed (SSLV3_ALERT_HANDSHAKE_FAILURE), so the site may be broken. Not verified.
- **lapo.it/asn1js** (client-side ASN.1/certificate decoder): blocked by the Anubis bot wall ("Access Denied"). Not verified.
- **NetSim, the packet-spoofing game:** https://netsim.erinn.io/ gave connection refused. It may be offline.
- **Zonemaster:** https://zonemaster.net/en/run-test returned 404. That path was a guess; the root was not tried.
- **howdns.works:** 301-redirects to dnsimple.com/comics/how-dns-works/ (not fetched).
- **nginxconfig.io:** 301-redirects to digitalocean.com/community/tools/nginx. Skipped as a known domain.
- **ssl-config.mozilla.org:** now only a "moved to TLSRef Configurator" notice. — [Mozilla page](https://ssl-config.mozilla.org/)
- **Tools found in search but not opened** (GitHub-hosted, a known domain, or install-only): wgcompose, the Traefik Labelizer Docker image, the haproxy-dashboard self-hosted UI, Sping (a CLI latency tool from Show HN), webShark (needs a sharkd server) and ccsim (a Go/WASM TCP simulator from a 26 July 2026 blog). — [Sping HN](https://hn.svelte.dev/item/45008819); [pcap search results](https://awesome.ecosyste.ms/projects/github.com%2Fqxip%2Fwebshark)

### Inferences
- Rerun the 403 tools from a normal browser before adding them to the handbook. whatsmydns, dnschecker, securityheaders and the Cloudflare Learning Center are widely used and probably fine; they block bot user-agents.

### Gaps
- Julia Evans' own tools are on known domains (messwithdns, dns-lookup.jvns.ca, nginx-playground), so they were excluded and none of her other link pages were mined.
- Server Fault, Stack Overflow and Reddit were not used, as instructed.
- An HTTP/2 visual demo (for example Akamai's tile demo) was not checked.
