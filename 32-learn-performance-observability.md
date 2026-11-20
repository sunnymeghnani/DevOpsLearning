# 32 — Learn: Performance & Observability

"The server is slow" and "the site was down last night and nobody noticed" are the two
complaints this module prepares you for. The first needs **performance analysis**: a
vocabulary, a method and a tool for every subsystem, so you can name the saturated
resource with evidence instead of guessing. The second needs **observability**: metrics,
logs, traces and alerts that tell you about a problem before the client does, and keep
the history you need afterwards. Both sit at L2–L4 of your Ops Ladder, and both pay off
directly in the Apache → Dokploy migration: you will want a baseline of the old box
before the move and dashboards plus alerts on the new one after it.

All commands are documented with illustrative sample output from Ubuntu 22.04/24.04
(RHEL/Rocky differences noted). Run them on your own test VM, never blindly on a client's
production server. Placeholders are UPPERCASE: HOST, PORT, PID, UNIT, CONTAINER, POD,
IFACE, DEVICE.

**Who it is for (career stages).** This module serves three stages of the Fresher → Senior
path:

| Stage | Ops Ladder level | Areas | What you can do afterwards |
|-------|------------------|-------|----------------------------|
| Mid-level | [L2 · Mid] | §1–§7 | Turn "the server is slow" into a named, saturated resource with evidence, in minutes |
| Senior | [L3 · Senior] | §4–§9, §16 | Explain cgroup throttling and OOM kills, prove a pool or GC or query problem, benchmark safely, size a server |
| Senior/Lead | [L4 · Lead/SRE] | §10–§18 | Build the monitoring, alerting, SLOs and capacity plans a team relies on, and run incident drills |

As a Fresher [L0 · Fresher] or Junior [L1 · Junior], read §1 and the 60-second checklist in
§2 now, then return after the [Linux](27-learn-linux.md) and [Docker](30-learn-docker.md)
modules. Every topic below carries a **Level** line with the same tags, so you can skip
what is above your stage for now. The [career ladder](40-career-ladder.md) shows where
this module fits in the whole journey.

---

## 0. How to use this module

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Observability Fundamentals → Prometheus Fundamentals → PromQL → Alerting ([link](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) KodeKloud: *Fundamentals of SRE* — Service Level Objectives and Measurements → Observability and Monitoring ([link](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Read: [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) and [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) (KodeKloud teaches the tools, not the method) · 4) Practice: the §17 lab and the §18 exercise in your homelab or a [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu).

This is a **learn** module: each topic explains the idea, shows it on a real system, has
you build and break it in a lab, and then points to the playbook you would use during a
real incident. The command references that go with it are
[CPU & performance](03-cpu-performance.md), [Memory](04-memory.md),
[Storage & disk](01-storage-disk.md) and [Network](02-network.md). The incident playbooks
are [Why is the system slow?](23-playbook-slow-system.md) and
[Network slow / speed](24-playbook-network-speed.md).

### Learning path

Work through the areas in this order. The level tags match the Ops Ladder (L0
Foundations, L1 Operator, L2 Troubleshooter, L3 Platform, L4 SRE) and the career stages
(Fresher, Junior, Mid, Senior, Lead/SRE).

| # | Area | Level · stage | Why at this point |
|---|------|---------------|-------------------|
| 1 | Performance vocabulary (§1) | [L2 · Mid] | Without exact words (latency vs throughput, utilization vs saturation) you cannot state a problem precisely |
| 2 | Methodologies (§2) | [L2 · Mid] | USE, RED and the 60-second checklist replace "poke around in top" |
| 3 | Linux observability tools map (§3) | [L2 · Mid] | Know which tool looks at which layer before you need it |
| 4 | CPU deep dive (§4) | [L2 · Mid] → [L3 · Senior] | Load average, iowait, steal and cgroup throttling are the most misread numbers |
| 5 | Memory deep dive (§5) | [L2 · Mid] → [L3 · Senior] | Page cache, swap, OOM and PSI explain "memory full" panics and silent kills |
| 6 | Disk deep dive (§6) | [L2 · Mid] → [L3 · Senior] | IOPS vs throughput vs latency, and how to benchmark without destroying data |
| 7 | Network deep dive (§7) | [L2 · Mid] → [L3 · Senior] | BDP, retransmits and iperf3 baselines answer "the network is slow" |
| 8 | Application performance (§8) | [L3 · Senior] | Most "slow server" tickets end in a pool, a GC or a slow query |
| 9 | Benchmarking and load testing (§9) | [L3 · Senior] | Measure capacity safely before a migration, never against production by accident |
| 10 | Observability pillars and cardinality (§10) | [L4 · Lead/SRE] | Choose metrics vs logs vs traces on purpose |
| 11 | Prometheus (§11) | [L3 · Senior] → [L4 · Lead/SRE] | The de-facto metrics system for Docker, Traefik and Kubernetes |
| 12 | Alertmanager and alert rules (§12) | [L4 · Lead/SRE] | Turn metrics into pages that are actionable |
| 13 | Grafana (§13) | [L3 · Senior] → [L4 · Lead/SRE] | Dashboards your team and client can read |
| 14 | Logs and tracing (§14) | [L2 · Mid] → [L4 · Lead/SRE] | journald, Loki/Alloy, ELK, structured logs, OpenTelemetry |
| 15 | SLIs, SLOs and error budgets (§15) | [L4 · Lead/SRE] | Decide what "good enough" means and alert on it |
| 16 | Capacity planning (§16) | [L3 · Senior] → [L4 · Lead/SRE] | Answer "do we need a bigger server, and when?" with data |
| 17 | Homelab lab: full monitoring stack (§17) | [L4 · Lead/SRE] drill | The Ops Ladder L4 drill: node_exporter, Prometheus, Grafana, Alertmanager |
| 18 | stress-ng exercise (§18) | [L4 · Lead/SRE] drill | Name the saturated resource before you look at the flags |
| 19 | Self-check / exit test (§19) | [L2 · Mid] → [L4 · Lead/SRE] | Prove it under a timer, per stage |
| 20 | Where to go next (§20) | all stages | Which module or course comes after this one |

If you are short on time: do §1, §2 (especially the 60-second checklist), §4–§6, then the
§17 lab and the §18 exercise. Everything else can follow.

### Study method

For every ### topic, follow the same five steps. The order matters: the note gives you the
mental model, the course gives you a second explanation, the lab makes it stick, and the
playbook shows you where it is used under pressure.

1. Read this note for the topic, including the sample outputs and the "→" explanations.
2. Do the KodeKloud course or lesson listed in the 📚 study path line at the top of the area.
3. Optional: watch one short video on the same topic if something still feels fuzzy.
4. Do the hands-on lab on a test VM: build it, break it on purpose, fix it, and write one line about what you saw.
5. Open the related playbook ([23](23-playbook-slow-system.md), [24](24-playbook-network-speed.md) or [26](26-playbook-containers-k8s.md)) and find where the topic shows up in a real incident.

### The lab VM you need

One disposable Ubuntu 22.04 or 24.04 VM (Proxmox, VirtualBox, Multipass or a small cloud
instance): 2–4 vCPU, 4 GB RAM, 2 GB swap, 30 GB disk. A second small VM helps for iperf3
and HTTP load tests. Install the tools once:

```bash
# Ubuntu 22.04/24.04 test VM — observability + benchmarking toolbox
sudo apt update
sudo apt install -y sysstat iotop-c fio stress-ng iperf3 sysbench wrk jq \
  linux-tools-common "linux-tools-$(uname -r)" bpfcc-tools bpftrace

# Keep sar history (Ubuntu ships the collector disabled on many releases)
grep ENABLED /etc/default/sysstat           # ENABLED="false" means no history
sudo sed -i 's/^ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
sudo systemctl enable --now sysstat         # history lands in /var/log/sysstat/saDD

# RHEL/Rocky equivalents
# sudo dnf install -y sysstat perf bcc-tools bpftrace fio stress-ng iperf3
# sudo systemctl enable --now sysstat       # history in /var/log/sa/saDD
# bcc tools live in /usr/share/bcc/tools/ (no -bpfcc suffix)
# tools your enabled repos lack (sysbench, wrk on most releases): EPEL, or build from source
```

On Ubuntu the bcc tools carry a `-bpfcc` suffix (`runqlat-bpfcc`, `biolatency-bpfcc`,
`tcpretrans-bpfcc`, `execsnoop-bpfcc`). Docker is needed for the §17 lab; see the
[Docker learn module](30-learn-docker.md) if it is not installed yet.

> ⚠️ Every "Hands-on lab" and "break it" step in this module is for a **test VM only**.
> stress-ng, fio, iperf3 and HTTP load tools can take a production server or a shared
> network down. Never run them against anything you do not own without written approval.

---

## 1. Performance vocabulary

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Observability and Monitoring → *Performance Monitoring Deep Dive* ([lesson notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page)) · 2) Note: this area, then the [CPU & performance reference](03-cpu-performance.md) · 3) Video: *Linux Performance Tools, Brendan Gregg, part 1 of 2* ([YouTube](https://www.youtube.com/watch?v=FJW8nGV4jxY), 54 min) · 4) Practice: the §1 labs on a test VM, then check Little's law against one real server's `server-status`.

Every performance conversation goes wrong when people use "slow", "busy" and "full" loosely.
This area gives you the five words that make a problem statement precise, shows why the
average is the wrong number to watch, and introduces the two pieces of queueing theory a
senior engineer actually uses: Little's law and the utilization knee.

### Latency, throughput, utilization, saturation

**Level:** [L2 · Mid] · the words every later topic uses

**Concept.** Think of a supermarket checkout. *Latency* is how long you personally spend
from joining the queue to walking out. *Throughput* is how many customers per minute leave
the shop. *Utilization* is the share of time the cashier is busy. *Saturation* is the queue:
work that is waiting because the cashier is busy. *Errors* are customers who leave without
paying because the card reader failed. A resource can be 100% utilized with no queue (fine,
just full), or 70% utilized with a growing queue (bursty arrivals), and those need different
fixes.

```
 arrivals (λ per s)        QUEUE = saturation          SERVER = utilization        throughput (X per s)
 ──────────────────▶   [ ■ ■ ■ ■ ]   ──────────▶   [ busy 80% of the time ]   ──────────────────▶
                        wait time Wq                 service time S
                   └──────────────── latency (response time) R = Wq + S ────────────────┘
```

Precisely: latency is time per operation (ms, µs), throughput is operations per unit of
time (req/s, IOPS, MB/s), utilization is busy time divided by elapsed time (or used
capacity divided by total capacity for things like memory and disk space), saturation is
the degree to which extra work queues (run-queue length, disk queue depth, swap activity,
TCP retransmits, PSI stall time), and errors are failed operations (5xx, I/O errors,
dropped packets).

**Key terms**

| Term | Meaning | Linux example |
|------|---------|---------------|
| Latency / response time | Wait time + service time for one operation | `curl -w '%{time_total}'`, iostat `r_await` |
| Service time | Time the resource actually works on the request | Time a disk spends serving one I/O |
| Throughput | Completed operations per second | req/s, `rkB/s`, `rxkB/s` |
| Bandwidth | Maximum possible throughput (capacity) | NIC speed 1000 Mb/s |
| Utilization | Busy time ÷ elapsed time | mpstat `%usr+%sys`, iostat `%util` |
| Saturation | Queued work that cannot be served yet | vmstat `r` > CPUs, iostat `aqu-sz`, PSI |
| Errors | Failed operations | `ip -s link` errors, `dmesg` I/O errors, HTTP 5xx |
| Concurrency | Operations in flight at the same moment | Busy Apache workers, open DB connections |
| Tail latency | The slowest requests (p99, p99.9) | One slow disk read behind a page load |
| Headroom | Capacity left before saturation | 30% CPU free at peak |

**See it on a real system**

```bash
# LATENCY of one HTTP request, split into phases (read-only, safe)
curl -s -o /dev/null -w 'dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://app.example.com/

# THROUGHPUT of a NIC and of a disk
sar -n DEV 1 3          # rxkB/s txkB/s per interface
iostat -xz 1 3          # rkB/s wkB/s r/s w/s per device

# UTILIZATION of CPUs
mpstat 1 3              # %usr %sys ... %idle

# SATURATION of CPU, memory and I/O
vmstat 1 5              # r column vs nproc; si/so for swapping
cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io

# ERRORS
ip -s link show         # RX/TX errors and dropped
journalctl -k -p err -b --no-pager | tail -20
```

```
dns=0.004 connect=0.021 tls=0.067 ttfb=0.212 total=0.214
```

→ DNS took 4 ms, the TCP handshake finished at 21 ms, TLS at 67 ms, and the first byte
arrived at 212 ms. Server "think time" is ttfb − tls ≈ 145 ms. If total is slow but think
time is small, the problem is the network or TLS, not the app.

```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 9  0      0 812344  90120 5312000    0    0     3    88 4800 9200 92  7  1  0  0
```

→ On a 4-vCPU VM, `r` = 9 means nine runnable tasks for four CPUs: utilization is ~99%
(`us`+`sy`) **and** the CPU is saturated (five tasks waiting at any moment).

**Hands-on lab (test VM only)**

**Step 1 — Start a tiny web server and measure baseline latency.** In terminal 1 start a
static server bound to loopback, in terminal 2 measure 50 requests and print percentiles.

```bash
# terminal 1
python3 -m http.server 8000 --bind 127.0.0.1 --directory /usr/share/doc

# terminal 2: 50 requests → p50 / p95 / max in seconds
for i in $(seq 1 50); do
  curl -s -o /dev/null -w '%{time_total}\n' http://127.0.0.1:8000/
done | sort -n | awk '{a[NR]=$1} END {print "p50="a[int(NR*0.50)], "p95="a[int(NR*0.95)], "max="a[NR]}'
```

```
p50=0.001412 p95=0.002034 max=0.003310
```

**Step 2 — Break it: saturate the CPU.** In terminal 3 start twice as many CPU hogs as
cores, then repeat the measurement and watch `vmstat 1` at the same time.

```bash
stress-ng --cpu $(( $(nproc) * 2 )) --timeout 120s &
vmstat 1 5
```

→ `r` jumps to about 2 × cores, `id` drops to 0, and p95/max latency of the trivial web
server grows several-fold even though each request still needs the same tiny amount of
CPU. The extra time is pure waiting in the run queue (saturation).

**Step 3 — Fix it and confirm.** Stop the load (`kill %1` or wait for the timeout) and
measure again: latency returns to baseline. Write down: "utilization 100% + run queue 2×
cores → p95 ×N".

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| "Everything is slow" but CPU shows 30% | `vmstat 1` (look at `b`, `wa`, `si/so`) | [Slow system playbook](23-playbook-slow-system.md) |
| Throughput flat while latency climbs | `iostat -xz 1` (`aqu-sz`, `await`) | [Storage reference](01-storage-disk.md) |
| Big file copy slow, ping fine | `iperf3 -c HOST` | [Network speed playbook](24-playbook-network-speed.md) |
| Only some requests slow | Percentiles from the access log (next topic) | [Slow system playbook](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** "The server is slow" is not a problem statement.
"p95 latency of /api/orders went from 120 ms to 2.4 s at 14:05 while request rate stayed
at 80 req/s, CPU utilization 35%, disk aqu-sz 18" is, and it already points at the disk.
Every later tool in this module produces one of these five numbers.

**Next step.** Learn why the *average* latency is the least useful of those numbers, and
what percentiles show instead.

### Percentiles and why averages lie

**Level:** [L2 · Mid] · read latency the way users feel it

**Concept.** Sort all request durations from fastest to slowest. The p50 (median) is the
value in the middle: half the requests were faster. The p95 is the value 95% of requests
beat, the p99 the value 99% beat. Averages hide the slow minority that users actually
complain about, because a few very fast requests cancel out a few very slow ones.

Worked example: 100 requests, 98 take 50 ms and 2 take 5 s.

| Statistic | Value | What it suggests |
|-----------|-------|------------------|
| Mean (average) | (98 × 50 + 2 × 5000) / 100 = **149 ms** | "Fine, under 200 ms" |
| p50 | **50 ms** | Typical user is happy |
| p98 | **50 ms** | Still looks fine |
| p99 | **5000 ms** | 1 in 100 requests takes five seconds |
| max | **5000 ms** | Something stalls hard |

The mean describes no real request at all. Three more rules a senior engineer keeps in
mind:

- **You cannot average percentiles.** The p95 of two servers is not the mean of their p95s. Aggregate the raw data (histogram buckets) and compute the percentile once; Prometheus does this with `histogram_quantile` over summed buckets (§11).
- **Tail latency multiplies with fan-out.** If one page load calls 100 backends and each has a 1% chance of a slow (p99) response, the chance that the page hits at least one slow call is 1 − 0.99¹⁰⁰ ≈ 63%. Your p99 becomes the user's median.
- **Coordinated omission.** A load tester that waits for a slow response before sending the next request silently stops measuring during the stall, so its p99 looks better than reality (more in §9).

**Key terms**

| Term | Meaning |
|------|---------|
| pNN / NNth percentile | Value below which NN% of observations fall |
| Median | p50 |
| Tail | p99, p99.9, max: the slowest requests |
| Histogram | Counts of observations per latency bucket (e.g. ≤100 ms, ≤250 ms, ≤500 ms) |
| Outlier | A rare extreme value; often the most interesting one |
| Bimodal distribution | Two humps, e.g. cache hits at 2 ms and misses at 200 ms; the mean falls between them where no request lives |

**See it on a real system**

Apache's default `combined` log has no duration. Add `%D` (microseconds) at the **end** of
a custom format so `$NF` picks it up:

```apache
# /etc/apache2/conf-available/timed-log.conf  (enable with a2enconf timed-log; then use it in a vhost)
LogFormat "%h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\" %D" combined_timed
# in the vhost:  CustomLog ${APACHE_LOG_DIR}/app-access.log combined_timed
```

```bash
# percentiles in ms from the last 10,000 requests
tail -n 10000 /var/log/apache2/app-access.log \
  | awk '{print $NF/1000}' | sort -n \
  | awk '{a[NR]=$1; s+=$1} END {printf "n=%d mean=%.1f p50=%.1f p95=%.1f p99=%.1f max=%.1f ms\n", NR, s/NR, a[int(NR*.5)], a[int(NR*.95)], a[int(NR*.99)], a[NR]}'

# Traefik JSON access log (Dokploy): Duration is in nanoseconds
jq -r 'select(.RequestHost=="app.example.com") | .Duration/1e6' access.log \
  | sort -n | awk '{a[NR]=$1} END {print "p50="a[int(NR*.5)]" p99="a[int(NR*.99)]" ms"}'

# Nginx: add $request_time (seconds) and $upstream_response_time to log_format
```

```
n=10000 mean=182.4 p50=41.0 p95=310.7 p99=2954.2 max=30012.6 ms
```

→ The mean (182 ms) looks acceptable, but 1% of requests take ~3 s and the max hits 30 s,
which smells like a timeout somewhere (Gunicorn's default worker timeout is 30 s). Next
move: group the slow ones by URL path.

```bash
# which paths produce the slow tail? (requests slower than 1 s, by path)
awk '$NF > 1000000 {print $7}' /var/log/apache2/app-access.log | sort | uniq -c | sort -rn | head
```

**Hands-on lab (test VM only)**

**Step 1 — Generate a bimodal workload.** Create two files: a small one (fast) and a
large one (slow because of transfer), served by the loopback Python server from the
previous lab.

```bash
mkdir -p /var/tmp/www && cd /var/tmp/www
head -c 1K  /dev/urandom > small.bin
head -c 50M /dev/urandom > big.bin
python3 -m http.server 8000 --bind 127.0.0.1 --directory /var/tmp/www
```

**Step 2 — Measure 98 fast + 2 slow requests and compare mean vs percentiles.**

```bash
( for i in $(seq 1 98); do curl -s -o /dev/null -w '%{time_total}\n' http://127.0.0.1:8000/small.bin; done
  for i in 1 2;           do curl -s -o /dev/null -w '%{time_total}\n' http://127.0.0.1:8000/big.bin;   done ) \
  | sort -n | awk '{a[NR]=$1; s+=$1} END {print "mean="s/NR, "p50="a[50], "p98="a[98], "p99="a[99]}'
```

**Step 3 — Break your intuition.** Before reading the output, guess the mean. Then compare
it with p50 and p99. **Fix:** decide which number you would put on a dashboard (p50 and
p99, never the mean alone). Clean up with `rm -rf /var/tmp/www` (it only contains the two
test files you just created).

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| Users complain, dashboard average is green | Percentiles from access log (above) | [Slow system playbook](23-playbook-slow-system.md) |
| p99 = exactly 30 s or 60 s | `grep -i 'timeout' ` in app and proxy logs | [Site down playbook](25-playbook-site-down.md) |
| Latency "averaged across servers" hides one bad node | Per-instance p99, not global mean | §11 PromQL |

**Why it matters for troubleshooting.** Timeouts, retries, lock waits and GC pauses live in
the tail. If you only watch averages you will be told about these problems by the client.

**Next step.** Learn the law that links latency, throughput and concurrency, and the curve
that explains why latency explodes long before 100% utilization.

### Little's law and the queueing knee

**Level:** [L2 · Mid] → [L3 · Senior] · sanity-check numbers and size pools

**Concept.** Little's law says that, in any stable system, the average number of things
inside it equals the arrival rate times the average time each one spends inside:

```
   L  =  λ  ×  W
   in-flight work = arrivals per second × seconds each one stays
```

It needs no assumptions about distributions, which is why it works everywhere: web
servers, disk queues, connection pools, Kubernetes pods.

| System | L (in flight) | λ (rate) | W (time inside) |
|--------|---------------|----------|-----------------|
| Apache / Gunicorn workers | Busy workers | Requests/s | Response time |
| Disk | iostat `aqu-sz` | IOPS (`r/s + w/s`) | `await` in seconds |
| DB connection pool | Connections in use | Queries/s | Query time |
| Checkout line | People in the shop | People arriving/s | Minutes per person |

Worked examples you will meet:

- Apache with `MaxRequestWorkers 150` and an average response time of 0.5 s can sustain at most 150 / 0.5 = **300 req/s**. If a backend slows to 3 s, the same 150 workers handle only 50 req/s; at 80 req/s of traffic the extra requests queue, workers run out, and the error log says `AH00484: server reached MaxRequestWorkers setting`.
- A disk doing 2000 IOPS with 4 ms average await has 2000 × 0.004 = **8** I/Os in the queue. iostat's `aqu-sz` should show ≈ 8; it is Little's law in a column.
- A pool of 20 DB connections and 50 ms queries tops out at 20 / 0.05 = **400 queries/s**.

The **knee.** For a single server with random arrivals (the textbook M/M/1 queue),
response time grows with utilization U as R = S / (1 − U):

| Utilization | Response time (× service time) |
|-------------|--------------------------------|
| 10% | 1.1 × |
| 50% | 2 × |
| 70% | 3.3 × |
| 80% | 5 × |
| 90% | 10 × |
| 95% | 20 × |
| 99% | 100 × |

```
 R/S
 20 |                                                    *  (95%)
    |
 10 |                                               *  (90%)
    |
  5 |                                          *  (80%)
  3 |                                     *  (70%)
  2 |                          *  (50%)
  1 | *    *    *    *    *
    +----+----+----+----+----+----+----+----+----+----+--
      0   10   20   30   40   50   60   70   80   90  100   utilization %
                                           └─ knee: ~70–80% ─┘
```

Below ~60% utilization extra load costs almost nothing; past ~70–80% each extra percent
costs a lot of latency. Real systems with many parallel servers (many CPU cores, NVMe
queues) have a later but sharper knee; bursty traffic makes it earlier. That is why
latency-sensitive resources are planned for 60–70% peak utilization, not 95%.

**Key terms**

| Term | Meaning |
|------|---------|
| λ (lambda) | Arrival rate, e.g. 80 req/s |
| W / R | Average time in system (latency) |
| L | Average number in the system (concurrency, queue length) |
| Stable system | Arrival rate ≤ capacity over the long run; otherwise queues grow forever |
| Knee | Utilization where latency starts rising steeply |
| M/M/1 | Textbook model: random arrivals, random service times, one server |

**See it on a real system**

```bash
# Disk: check Little's law on live data (aqu-sz ≈ (r/s + w/s) × await/1000)
iostat -xz 1 3

# Web server: concurrency right now (busy workers) and request rate
curl -s 'http://127.0.0.1/server-status?auto' | grep -E 'ReqPerSec|BusyWorkers|IdleWorkers|DurationPerReq'
```

```
ReqPerSec: 21.2479
DurationPerReq: 182.45
BusyWorkers: 148
IdleWorkers: 2
```

→ Little's law predicts 21.2 req/s × 0.182 s ≈ 4 busy workers, but 148 are busy. Either
requests are piling up right now (current latency is far higher than the lifetime average
in `DurationPerReq`) or workers are stuck in keep-alive. Look at the scoreboard
(`?auto` shows `Scoreboard:`; many `W` = sending reply, many `K` = keep-alive) and at the
backend latency. Ubuntu enables `mod_status` restricted to local requests by default
(`Require local`).

**Hands-on lab (test VM only)**

**Step 1 — Measure capacity.** Against the loopback Python server, run `wrk` with 1, then
10 connections, and note requests/s and latency.

```bash
wrk -t1 -c1  -d15s --latency http://127.0.0.1:8000/small.bin
wrk -t2 -c10 -d15s --latency http://127.0.0.1:8000/small.bin
```

**Step 2 — Check Little's law.** For each run compute connections ÷ Requests/sec and
compare it with the reported average latency. They should match within a few percent
(wrk keeps exactly `-c` requests in flight).

**Step 3 — Break it: walk up the knee.** Stop the server (Ctrl-C in its terminal), restart
it pinned to one CPU, put a CPU hog on the same core, then repeat Step 1. Throughput drops and latency rises far more than the
lost CPU share would suggest.

```bash
# restart the server pinned to CPU 0, and a 50%-load hog on CPU 0
taskset -c 0 python3 -m http.server 8000 --bind 127.0.0.1 --directory /var/tmp/www &
taskset -c 0 stress-ng --cpu 1 --cpu-load 50 --timeout 120s &
```

**Step 4 — Fix it.** Stop the hog (`kill %2`) and confirm latency recovers. Write down
the measured utilization → latency pairs; you have drawn your own knee.

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| `AH00484: server reached MaxRequestWorkers setting` | `curl -s 'http://127.0.0.1/server-status?auto'` | §8 pools, [Slow system playbook](23-playbook-slow-system.md) |
| `server reached pm.max_children setting (5)` (PHP-FPM) | `grep max_children /var/log/php*-fpm.log` | §8 pools |
| Latency doubles when a node is drained | Per-node utilization at peak | §16 capacity |
| `aqu-sz` high while `%util` < 100% | `iostat -xz 1` | §6 disk |

**Why it matters for troubleshooting.** Little's law lets you sanity-check every number
you read ("do these three values agree?"), size pools without guessing, and explain to a
client why "only 80% CPU" is already too much for a latency-sensitive service.

**Next step.** With the vocabulary in place, learn the methods that tell you *which*
resource to look at first: USE, RED and the 60-second checklist.

---

## 2. Methodologies

> 📚 **Study path:** 1) Read: [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) (KodeKloud has no lesson on USE or RED) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment → *Diagnose and Manage Processes* ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) and *Verify Integrity and Availability of Resources and Processes* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Video: *Linux Performance Tools, Brendan Gregg, LinuxCon Europe 2014* ([YouTube](https://www.youtube.com/watch?v=SN7Z0eCn0VY), 49 min) · 4) Practice: the [slow system playbook](23-playbook-slow-system.md) plus one [SadServers scenario](https://sadservers.com/scenarios) a week.

A method is a checklist that makes you look in the right order and stops you from
stopping at the first interesting number. Brendan Gregg's USE method covers resources,
RED and the four golden signals cover services, and the 60-second checklist is the
concrete first minute on a Linux box.

### The USE method

**Level:** [L2 · Mid] · a complete resource sweep

**Concept.** For **every resource**, check **U**tilization, **S**aturation and **E**rrors.
A resource is anything with a capacity: CPUs, memory, disks, network interfaces, but also
software resources such as file descriptors, the conntrack table, worker pools and
connection pools. Iterating over resources (instead of over the tools you happen to know)
is what makes USE complete: you cannot forget the disk because you were busy in `top`.

```
for each resource in [CPU, memory, disk, network, fds, conntrack, pools...]:
    utilization high?  → it is busy (maybe fine)
    saturation > 0?    → work is waiting (users feel this)
    errors > 0?        → something is failing (check first: cheapest to confirm)
```

**Key terms**

| Term | Meaning in USE |
|------|----------------|
| Resource | Any component with finite capacity |
| Utilization | Busy time or used capacity, as a percentage |
| Saturation | Extra work the resource cannot serve yet (queue length, wait time) |
| Errors | Count of error events for that resource |

**See it on a real system**

The USE checklist for a Linux server (all read-only):

| Resource | Utilization | Saturation | Errors |
|----------|-------------|------------|--------|
| CPU | `mpstat -P ALL 1` (%usr+%sys per CPU) | `vmstat 1` r > nproc; `cat /proc/pressure/cpu` | `dmesg` (MCE, thermal throttling) |
| Memory | `free -m` (available vs total) | `vmstat 1` si/so; `sar -B 1` pgscand/s; PSI memory; OOM kills | `dmesg` (EDAC/ECC errors) |
| Disk I/O | `iostat -xz 1` %util | `iostat -xz 1` aqu-sz, r_await/w_await; PSI io | `dmesg` I/O errors; `smartctl -H` |
| Disk capacity | `df -h`, `df -i` | (n/a: it is full or not) | `dmesg` filesystem errors, read-only remount |
| Network | `sar -n DEV 1` vs link speed | `nstat` retransmits; `ss -lnt` Recv-Q on listeners; `ip -s link` drops | `ip -s link` errors; `ethtool -S IFACE` |
| File descriptors | `cat /proc/sys/fs/file-nr` | Processes near `ulimit -n` | `Too many open files` in logs |
| Conntrack | `conntrack -C` vs `nf_conntrack_max` | Table full | `nf_conntrack: table full, dropping packet` in dmesg |
| Worker pools | Busy workers (`server-status`) | Requests queued | AH00484, pm.max_children, 503s |

**Hands-on lab (test VM only)**

**Step 1 — Write it down.** Copy the table above into your notes as a checklist with one
command per cell.

**Step 2 — Break one resource.** Ask a friend (or use the §18 script) to load one
resource on your VM with stress-ng without telling you which.

**Step 3 — Walk the table row by row** and tick U, S and E for each resource. Stop only
when every row is ticked, even after you found "the" problem; second problems are common.

**Step 4 — Fix and verify.** Stop the load and run the table again; all saturation cells
should return to zero.

**How it breaks**

| Symptom | Usual missed resource | First command |
|---------|-----------------------|---------------|
| Random connection failures under load | Conntrack table or listen backlog | `dmesg -T`, `nstat -az TcpExtListenOverflows` |
| App hangs, CPU idle | Worker or DB pool exhausted | `server-status`, DB connection count |
| "Too many open files" | File descriptors | `cat /proc/PID/limits`, `ls /proc/PID/fd` count |

Full walk-throughs live in the [slow system playbook](23-playbook-slow-system.md).

**Why it matters for troubleshooting.** USE turns "I looked at top and it looked fine"
into a complete sweep that finishes in a few minutes, and it catches the software limits
(pools, fds, conntrack) that `top` never shows.

**Next step.** USE answers "which resource?". For "is the service healthy for users?" you
need RED and the four golden signals.

### RED and the four golden signals

**Level:** [L2 · Mid] → [L4 · Lead/SRE] · service health as users see it

**Concept.** USE is resource-centric; users do not care about your disk queue, they care
about their request. For **services**, measure:

- **RED** (Tom Wilkie): **R**ate (requests per second), **E**rrors (failed requests per second or ratio), **D**uration (latency distribution, as percentiles).
- **The four golden signals** (Google SRE book, "Monitoring Distributed Systems"): **latency**, **traffic**, **errors** and **saturation**. RED plus "how full is the service".

```
 users ──▶ Traefik ──▶ app container ──▶ PostgreSQL
           RED/golden   RED/golden          RED/golden        ← request-centric: "is it OK for users?"
 ────────────────────────────────────────────────────────────
 host:     USE on CPU, memory, disk, network, fds, conntrack  ← resource-centric: "why is it not OK?"
```

Use RED/golden signals to **detect** and **alert** (they describe user pain), and USE to
**diagnose** (it finds the cause).

**Key terms**

| Signal | Typical source | Example PromQL (Traefik metrics, §11) |
|--------|----------------|---------------------------------------|
| Rate / traffic | Proxy or app metrics, access log | `sum(rate(traefik_service_requests_total[5m]))` |
| Errors | 5xx count, failed probes | `sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))` |
| Duration / latency | Histogram buckets | `histogram_quantile(0.95, sum by (le) (rate(traefik_service_request_duration_seconds_bucket[5m])))` |
| Saturation | Pool usage, queue length, CPU throttling | Busy workers ÷ max workers |

**See it on a real system**

Without any metrics system, the access log already contains RED:

```bash
# Rate: requests per minute over the last 5,000 lines (Apache combined log; field 4 = [dd/Mon/yyyy:HH:MM:SS)
tail -n 5000 /var/log/apache2/access.log | awk '{print substr($4, 2, 17)}' | uniq -c | tail -5

# Errors: status code distribution (field 9)
tail -n 5000 /var/log/apache2/access.log | awk '{print $9}' | sort | uniq -c | sort -rn

# Duration: see the percentile recipe in the previous area (needs %D in the LogFormat)
```

```
    212 03/Oct/2026:10:41
    198 03/Oct/2026:10:42
    207 03/Oct/2026:10:43
   4689 200
    188 304
     97 502
     26 404
```

→ About 200 requests per minute, and 97 of the last 5,000 are 502s (~2%): the proxy could
not get an answer from a backend. That is an error-rate symptom; USE on the backend host
tells you why.

**Hands-on lab (test VM only)**

**Step 1 — Create RED data.** Run the §17 monitoring stack, or for now just the loopback
Python server, and send a mix of good and bad requests:

```bash
for i in $(seq 1 200); do curl -s -o /dev/null http://127.0.0.1:8000/small.bin; done
for i in $(seq 1 20);  do curl -s -o /dev/null http://127.0.0.1:8000/missing.bin; done
```

**Step 2 — Compute R, E and D** by hand from the server's output (the Python server logs
each request with its status to the terminal).

**Step 3 — Break it** by stopping the server mid-loop; your "errors" become connection
failures (curl exit code 7), which never appear in the server's own log. **Fix:** note that
a server cannot log requests it never received; that is why black-box probes (§11) and
proxy-side metrics matter.

**How it breaks**

| Symptom | First check | Go to |
|---------|-------------|-------|
| 502/504 rate rises | Proxy logs, backend health | [Site down playbook](25-playbook-site-down.md) |
| Rate drops to zero, no errors logged | Black-box probe, DNS, firewall | [Site down playbook](25-playbook-site-down.md) |
| Duration up, rate and errors flat | USE on backend host | [Slow system playbook](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** A drop in *rate* with no errors is often the
scariest signal (traffic is not reaching you at all), and only RED makes you look at it.

**Next step.** Make USE concrete for the first minute on a Linux box: the 60-second
checklist.

### The 60-second checklist

**Level:** [L2 · Mid] · the first minute on any slow Linux box

**Concept.** Netflix's "Linux Performance Analysis in 60,000 Milliseconds" (linked from
the Ops Ladder) is ten commands that give you a USE overview in about a minute. They need
only `procps` and `sysstat`, which you should have on every server. Run them in this
order; each one narrows the next.

| # | Command | What it tells you |
|---|---------|-------------------|
| 1 | `uptime` | Load averages: is load rising or falling? |
| 2 | `dmesg -T | tail` (with `sudo` on Ubuntu) | OOM kills, I/O errors, dropped packets, hung tasks |
| 3 | `vmstat 1` | Run queue, blocked tasks, swapping, CPU split |
| 4 | `mpstat -P ALL 1` | Per-CPU balance: one hot core = single-threaded bottleneck |
| 5 | `pidstat 1` | Which processes use CPU, rolling (not a snapshot like top) |
| 6 | `iostat -xz 1` | Disk throughput, latency, queue, utilization |
| 7 | `free -m` | Memory available, page cache size |
| 8 | `sar -n DEV 1` | Network throughput per interface vs link speed |
| 9 | `sar -n TCP,ETCP 1` | TCP connection rates and retransmits |
| 10 | `top` | Final cross-check of everything above |

**Key terms**

| Term | Meaning |
|------|---------|
| Rolling output | Commands with an interval (`1`) print one line per second: watch several lines, ignore the first (since boot) |
| Since-boot line | The first line of vmstat/iostat/mpstat summaries averages since boot; usually misleading |
| Snapshot | One sample (`ps`, `top -b -n1`); can catch an untypical moment |

**See it on a real system**

The outputs below come from one 4-vCPU VM during a slow database import, so you can see
how the clues add up.

```bash
uptime
```

```
 10:41:00 up 12 days,  4:02,  1 user,  load average: 7.31, 5.92, 3.10
```

→ Load 7.3 on 4 CPUs and rising (1-min ≫ 15-min). Load counts runnable *and*
uninterruptible tasks, so this is not yet proof of a CPU problem.

```bash
sudo dmesg -T | tail        # Ubuntu sets kernel.dmesg_restrict=1, so plain dmesg fails for normal users
```

```
[Sat Oct  3 10:38:12 2026] INFO: task mysqld:2214 blocked for more than 120 seconds.
[Sat Oct  3 10:38:12 2026] "echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
```

→ A task stuck for over two minutes in uninterruptible sleep: almost always storage.

```bash
vmstat 1
```

```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  6      0 431208  80244 5368320    0    0   612 31544 2310 4120  7  4 37 52  0
 1  6      0 319812  80244 5468320    0    0    40 52800 3110 5402  6  4 28 62  0
 1  7      0 301144  80244 5481200    0    0    16 50112 2988 5230  5  3 30 62  0
```

→ `r` = 1–2 (CPU not saturated), `b` = 6–7 blocked tasks (that is the load average),
`wa` = 62%, `bo` ≈ 50 MB/s written, no swapping. Strong hint: disk writes. (Newer procps
releases add a final `gu` guest column; ignore it.)

```bash
mpstat -P ALL 1
```

```
10:41:03     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:41:04     all    6.03    0.00    3.27   61.81    0.00    0.25    0.00    0.00    0.00   28.64
10:41:04       0    5.05    0.00    3.03   88.89    0.00    1.01    0.00    0.00    0.00    2.02
10:41:04       1    7.07    0.00    4.04   62.63    0.00    0.00    0.00    0.00    0.00   26.26
10:41:04       2    6.00    0.00    3.00   49.00    0.00    0.00    0.00    0.00    0.00   42.00
10:41:04       3    6.00    0.00    3.00   47.00    0.00    0.00    0.00    0.00    0.00   44.00
```

→ No core is busy computing (`%usr` ≈ 6%); time is iowait. No steal, so the hypervisor is
not starving you.

```bash
pidstat 1
```

```
10:41:05      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
10:41:06      113      2214    4.00    3.00    0.00    0.00    7.00     2  mysqld
10:41:06        0       412    0.00    1.00    0.00    0.00    1.00     0  jbd2/sda2-8
```

→ The only active process is mysqld (and the ext4 journal thread working for it).

```bash
iostat -xz 1
```

```
avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           6.03    0.00    3.52   61.81    0.00   28.64

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dkB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
sda              2.00     32.00     0.00   0.00    4.50    16.00  412.00  52736.00    18.00   4.19   38.62   128.00    0.00      0.00     0.00   0.00    0.00     0.00   38.00   12.40   16.39  99.60
```

→ 412 writes/s of 128 KB, each waiting ~39 ms, queue of ~16, device 99.6% busy. Little's
law check: (2 × 4.5 + 412 × 38.62 + 38 × 12.4) / 1000 ≈ 16.4 = `aqu-sz`. The disk is
saturated. On a single HDD or a slow virtual disk, 50 MB/s of synchronous-ish writes is
plausible as the ceiling.

```bash
free -m
```

```
               total        used        free      shared  buff/cache   available
Mem:            7941        2210         312          41        5418        5402
Swap:           2047           0        2047
```

→ Plenty available (5.4 GB), no swap used. Memory is not the problem.

```bash
sar -n DEV 1
sar -n TCP,ETCP 1
```

```
10:41:20        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
10:41:21           lo      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
10:41:21        ens18    812.00    790.00    102.31     98.77      0.00      0.00      0.00      0.08

10:41:25     active/s passive/s    iseg/s    oseg/s
10:41:26         2.00     41.00    830.00    805.00

10:41:25     atmptf/s  estres/s retrans/s isegerr/s   orsts/s
10:41:26         0.00      0.00      0.00      0.00      1.00
```

→ Network nearly idle, no retransmits. Not the network.

```bash
top        # press 1 for per-CPU lines, then q
```

→ Confirms the picture: high `wa`, mysqld at the top with state `D` most of the time.

**Verdict in one sentence:** the disk (`sda`) is saturated by mysqld writes; CPU, memory
and network have headroom. Next: why so many writes (import with per-row commits?) and
whether the storage is right for the workload (§6).

**Hands-on lab (test VM only)**

**Step 1 — Save the checklist as a script** that prints a header before each command and
limits each rolling command to five samples, so you can run it in one go:

```bash
sudo tee /usr/local/bin/sixty-seconds >/dev/null <<'EOF'
#!/usr/bin/env bash
# 60-second performance checklist (read-only). Usage: sudo sixty-seconds [samples]
# (sudo because Ubuntu restricts dmesg to root: kernel.dmesg_restrict=1)
N=${1:-5}
run() { printf '\n===== %s =====\n' "$*"; "$@"; }
run uptime
printf '\n===== dmesg -T | tail =====\n'; dmesg -T | tail -n 15
run vmstat 1 "$N"
run mpstat -P ALL 1 "$N"
run pidstat 1 "$N"
run iostat -xz 1 "$N"
run free -m
run sar -n DEV 1 "$N"
run sar -n TCP,ETCP 1 "$N"
printf '\n===== top -b -n 1 | head -20 =====\n'; top -b -n 1 | head -20
EOF
sudo chmod 755 /usr/local/bin/sixty-seconds
```

**Step 2 — Baseline an idle VM.** Run `sudo sixty-seconds > /var/tmp/baseline-idle.txt` and
read it. Knowing what "normal" looks like on your hardware is half the skill.

**Step 3 — Break it.** Start `stress-ng --hdd 2 --hdd-opts dsync --temp-path /var/tmp --timeout 180s`
and run the script again. Compare with the baseline and write the one-sentence verdict.

**Step 4 — Fix.** Let the timeout expire (or Ctrl-C stress-ng); stress-ng removes its
temporary files. Re-run the script and confirm it matches the baseline.

**How it breaks**

| Checklist clue | Meaning | Go to |
|----------------|---------|-------|
| dmesg: `Out of memory: Killed process` | OOM kill | §5, [Memory reference](04-memory.md) |
| vmstat `r` ≫ nproc | CPU saturated | §4 |
| vmstat `b` high, `wa` high | Storage or NFS waits | §6, [Storage reference](01-storage-disk.md) |
| vmstat `si`/`so` non-zero sustained | Swapping (memory saturation) | §5 |
| mpstat one CPU at 100% | Single-threaded bottleneck or IRQs on one core | §4 |
| mpstat `%steal` > 5–10% | Noisy neighbour / CPU credits | §4, [AWS reference](16-aws-cloud.md) |
| sar `retrans/s` non-zero | Packet loss or congestion | §7, [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting.** It gives you a defensible verdict in a minute and
the evidence to paste into the ticket. The [slow system playbook](23-playbook-slow-system.md)
starts with exactly this sweep.

**Next step.** Learn how to keep digging after the first minute, and the anti-methods that
waste hours.

### Drill-down analysis and anti-methods

**Level:** [L2 · Mid] → [L3 · Senior] · from resource to root cause

**Concept.** After the first minute you usually know the *resource*. Drill-down analysis
narrows from there, one level at a time, and at every level you ask "which part of this
is responsible?":

```
 user symptom (p99 of /checkout = 4 s)
   └─ which service?          (Traefik metrics / access logs per router)
       └─ which host/container? (per-instance RED)
           └─ which resource?   (USE: disk sda saturated)
               └─ which process? (pidstat -d, iotop-c)
                   └─ which code path / query / file? (strace, perf, slow query log)
```

Before you start, answer Brendan Gregg's **problem statement** questions; they often
solve the problem on their own:

1. What makes you think there is a performance problem?
2. Has this system ever performed well? What were the numbers?
3. What changed recently (deploy, config, traffic, kernel, data size)?
4. Can the problem be expressed in latency or run time?
5. Does it affect other people or applications, or only this one?
6. What is the environment (hardware, VM, versions, where does storage live)?

**Anti-methods** to recognise in yourself and others:

| Anti-method | What it looks like | Why it fails |
|-------------|--------------------|--------------|
| Streetlight | Using the tools you know (top, ping) because they are familiar, not because they observe the right layer | You only find problems that happen to be under the lamp |
| Random change | Tweaking sysctls, restarting services, adding RAM until it "feels better" | Unmeasured, slow, and may hide the real cause |
| Blame someone else | "It's the network / the database / DNS" without evidence | Bounces the ticket, wastes another team's time |
| Ad hoc checklist only | Running last incident's checklist | Misses the new failure |
| Stopping at the first finding | "Found high CPU, done" | Often a symptom; the cause is one level deeper |

**Key terms**

| Term | Meaning |
|------|---------|
| Drill-down | Narrowing from a broad view to a specific component, one level at a time |
| Workload characterization | Who causes the load, why, what kind (read/write, size), how it changes |
| Scientific method | Question → hypothesis → prediction → test → analysis |
| 5 whys | Asking "why" repeatedly to move from symptom to root cause |

**See it on a real system**

Drill-down from "disk saturated" (previous topic) to the file:

```bash
# which process issues the I/O?
pidstat -d 1 5
sudo iotop-c -oPa            # accumulated I/O per process (q to quit)

# which write/sync syscalls dominate, and how long do they block? (trace briefly: strace slows the target)
# -w reports wall-clock time per call; without it, -c sums only system CPU time and hides waits
sudo strace -f -e trace=write,fsync,fdatasync -p 2214 -c -w   # Ctrl-C after ~10 s

# which files are open for writing?
sudo ls -l /proc/2214/fd | grep -v -E 'socket|pipe|anon_inode'
```

```
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 91.37    9.812341        2402      4085           fsync
  8.21    0.881201          13     65411           write
```

→ 4,085 fsync calls in ten seconds, each ~2.4 ms: the import commits every row. The fix
is in the workload (batch commits), not in the kernel.

**Hands-on lab (test VM only)**

**Step 1 — Write the problem statement** for the §2 checklist lab before touching any
tool: answer the six questions in your notes.

**Step 2 — Break it:** run `stress-ng --hdd 1 --hdd-opts fsync --temp-path /var/tmp --timeout 120s`.

**Step 3 — Drill down** with `pidstat -d 1`, then `sudo strace -c -w -f -p PID` on the
stress-ng worker for 10 seconds. Name the syscall that dominates (by calls and by wall-clock
time).

**Step 4 — Fix** by stopping the load, and write a five-line incident note (symptom, first
wrong guess, evidence, fix, what to check first next time), exactly as the Ops Ladder's
weekly rhythm asks.

**How it breaks**

| Trap | Better move |
|------|-------------|
| "Restart fixed it" (cause unknown) | Capture evidence first: 60-second checklist output, logs, `ps` |
| Tuning sysctls from a blog | Measure, change one thing, measure again |
| Ping is fine, so "network is fine" | Test the actual path and port, measure throughput (§7) |

**Why it matters for troubleshooting.** The Google SRE book's "Effective Troubleshooting"
chapter (linked from the Ops Ladder) describes the same loop. Your notes already follow it
by instinct; naming the anti-methods helps you notice when you, a colleague or a vendor
slips into one.

**Next step.** Drill-down needs a tool for every layer. Next is the map of Linux
observability tools.

---

## 3. The Linux observability tools map

> 📚 **Study path:** 1) Note: the [CPU](03-cpu-performance.md), [Memory](04-memory.md) and [Storage](01-storage-disk.md) references (quick refresher of the commands) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage → *Monitor Storage Performance* (iostat, pidstat) ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)) · 3) Read: [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) (the tools diagram) and the free [Linux debugging tools zine](https://wizardzines.com/zines/debugging/) · 4) Practice: the §3 lab, one broken layer per day.

You cannot drill down into a layer you have no tool for. This area is the map: which tool
observes which subsystem, which tools are cheap enough for production, and what the
equivalents are on Windows, macOS and AWS. Brendan Gregg's Linux performance page (linked
from the Ops Ladder) has the famous diagram this map is based on.

### Which tool for which subsystem

**Level:** [L2 · Mid] · the map you reach for under pressure

**Concept.** A Linux server is a stack: applications on top, then the system-call
interface, then kernel subsystems (scheduler, virtual memory, file systems, block layer,
network stack), then device drivers and hardware. Each tool looks at one or a few of those
layers. Pick the tool by the layer your hypothesis lives in, not by habit.

```
 ┌─────────────────────────────── APPLICATIONS ───────────────────────────────┐
 │ app logs, access logs (%D), language profilers (py-spy, async-profiler)     │  perf top -p, strace, ltrace
 ├──────────────────────────── SYSTEM CALL INTERFACE ─────────────────────────┤
 │ strace -c, perf trace, syscount-bpfcc                                       │
 ├───────────────┬─────────────────┬──────────────────┬───────────────────────┤
 │ SCHEDULER     │ VIRTUAL MEMORY  │ VFS / FILESYSTEMS│ NETWORK STACK          │
 │ vmstat r      │ free, vmstat    │ opensnoop-bpfcc  │ ss -tin, nstat, sar -n │
 │ mpstat,pidstat│ /proc/meminfo   │ ext4slower-bpfcc │ tcpretrans-bpfcc       │
 │ runqlat-bpfcc │ slabtop, PSI    │ fincore, lsof    │ tcpdump, ip -s link    │
 │ perf sched    │ sar -B, smem    │ df -h, df -i     │ conntrack -S           │
 ├───────────────┴─────────────────┼──────────────────┴───────────────────────┤
 │                                 │ BLOCK LAYER: iostat -xz, biolatency-bpfcc  │
 │                                 │ biosnoop-bpfcc, pidstat -d, iotop-c        │
 ├─────────────────────────────────┴──────────────────────────────────────────┤
 │ DEVICE DRIVERS & HARDWARE: dmesg, smartctl, nvme smart-log, ethtool -S,     │
 │ perf stat (CPU counters), turbostat, sensors, edac-util                     │
 └─────────────────────────────────────────────────────────────────────────────┘
   whole-system history: sar (sysstat), node_exporter + Prometheus (§11)
```

**Key terms**

| Term | Meaning |
|------|---------|
| procps | Package with `ps`, `top`, `vmstat`, `free`, `uptime`, `pidof` |
| sysstat | Package with `sar`, `iostat`, `mpstat`, `pidstat`, plus the history collector |
| bcc / `bpfcc-tools` | Ready-made eBPF tools (`runqlat`, `biolatency`, `execsnoop`, `tcpretrans`...) |
| bpftrace | One-liner language for eBPF tracing |
| perf | Kernel profiler and tracer (`linux-tools-$(uname -r)` on Ubuntu) |

**See it on a real system**

| Question | Quick look | Deeper | History / metric |
|----------|------------|--------|------------------|
| Is the CPU busy or saturated? | `mpstat -P ALL 1`, `vmstat 1` | `pidstat 1`, `perf top`, `runqlat-bpfcc` | `sar -u`, `sar -q`, `node_cpu_seconds_total` |
| Who uses memory, is it under pressure? | `free -m`, `vmstat 1` | `smem -tk`, `/proc/PID/smaps_rollup`, `sar -B` | `sar -r`, `node_memory_*`, PSI |
| Is the disk slow or saturated? | `iostat -xz 1` | `pidstat -d 1`, `iotop-c`, `biolatency-bpfcc` | `sar -d`, `node_disk_*` |
| Is a filesystem full? | `df -h`, `df -i` | `du -xh --max-depth=1`, `lsof +L1` | `node_filesystem_*` |
| Is the network the bottleneck? | `sar -n DEV 1`, `ip -s link` | `ss -tin`, `nstat`, `tcpretrans-bpfcc`, `tcpdump` | `sar -n DEV`, `node_network_*` |
| What is a process doing? | `top -H -p PID`, `ps -o wchan` | `strace -c -p PID`, `perf top -p PID` | Application metrics |
| What new processes start? | `ps -ef --forest` | `execsnoop-bpfcc` | (audit logs) |
| What happened at 03:00? | `sar -A -s 02:50:00 -e 03:10:00` | `journalctl --since/--until` | Prometheus, Loki |

Windows, macOS and AWS equivalents, for the occasional box that is not Ubuntu:

| Need | Windows | macOS | AWS |
|------|---------|-------|-----|
| Live overview | Task Manager, Resource Monitor | Activity Monitor, `top -o cpu` | CloudWatch metrics (CPU, network, EBS) |
| Counters over time | Performance Monitor (perfmon), `Get-Counter` | `vm_stat 1`, `iostat 1` | CloudWatch; memory and disk space need the CloudWatch agent |
| Per-process I/O | Resource Monitor, Disk tab | `sudo fs_usage` | (inside the instance: iostat) |
| Network throughput | Resource Monitor, Network tab | `nettop` | VPC flow logs, `NetworkIn/Out` |

See [Windows](17-windows.md), [macOS](20-macos.md) and [AWS](16-aws-cloud.md) for the
command details.

**Hands-on lab (test VM only)**

**Step 1 — Build your own map.** For each row of the first table, run the "quick look"
command on your idle VM and save the output in `/var/tmp/toolmap-idle/`.

**Step 2 — Break one layer at a time** (one per day is fine): CPU with
`stress-ng --cpu $(nproc)`, memory with `stress-ng --vm 1 --vm-bytes 70%`, disk with
`stress-ng --hdd 2 --temp-path /var/tmp`, network with iperf3 between two VMs (§7). Each
time, find the tool in the table that shows it most clearly.

**Step 3 — Fix** by stopping the load each time, then note which tools did *not* show the
problem (that is the lesson about streetlights).

**How it breaks**

| Situation | What goes wrong | Better tool |
|-----------|-----------------|-------------|
| "sar: command not found" or empty history | sysstat missing or collector disabled | Install and enable (§0) |
| bcc tool fails: `modprobe: FATAL: Module kheaders not found` | Kernel headers or BTF missing | `sudo apt install linux-headers-$(uname -r)` |
| `perf: command not found` after kernel update | `linux-tools` not installed for the new kernel | `sudo apt install linux-tools-$(uname -r)` |
| No tools inside a container image | Minimal image | Run tools from the host, or `nicolaka/netshoot` sharing the container's namespace ([Containers playbook](26-playbook-containers-k8s.md)) |

**Why it matters for troubleshooting.** The worst time to learn that `sar` had no history
or `perf` was not installed is during the incident. Install the toolbox on every server
you own as part of the base image or Ansible role.

**Next step.** Understand the cost and nature of each tool type: counters, tracing and
profiling.

### Counters, tracing and profiling

**Level:** [L3 · Senior] · which tools are safe on production

**Concept.** Observability tools come in three kinds, and the kind decides how safe a tool
is on a busy production box:

- **Counters** (fixed statistics the kernel keeps anyway): `vmstat`, `iostat`, `mpstat`, `sar`, `/proc`, node_exporter. Near-zero overhead; always safe.
- **Tracing** (record every event of some type): `strace`, `tcpdump`, bcc tools, `perf trace`. Overhead scales with the event rate. `strace` uses ptrace and can slow a syscall-heavy process 10–100×; eBPF tools are far cheaper but not free.
- **Profiling / sampling** (take a sample N times per second): `perf record -F 99`, `perf top`, py-spy. Low, bounded overhead; shows where time goes statistically.

**Key terms**

| Term | Meaning |
|------|---------|
| Overhead | Extra CPU or latency the tool causes in the target |
| Sampling frequency | Samples per second; 99 Hz avoids lock-step with 100 Hz timers |
| eBPF | Safe, verified programs running inside the kernel; base of bcc and bpftrace |
| Static vs dynamic tracing | Tracepoints defined by developers vs probes attached to any kernel or user function |
| Observer effect | The act of measuring changes the system |

**See it on a real system**

```bash
# counters: safe anywhere
cat /proc/loadavg
grep -E 'ctxt|procs_running|procs_blocked' /proc/stat

# tracing with eBPF: new processes system-wide (cheap, great for "who keeps spawning?")
sudo execsnoop-bpfcc

# sampling: 99 Hz CPU profile of the whole box for 10 s
sudo perf record -F 99 -a -g -- sleep 10 && sudo perf report --stdio --no-children | head -40
```

```
PCOMM            PID     PPID    RET ARGS
sh               48211   1022      0 /bin/sh -c /usr/local/bin/backup.sh
backup.sh        48211   1022      0 /usr/local/bin/backup.sh
tar              48213   48211     0 /usr/bin/tar czf /backup/www.tgz /var/www
gzip             48214   48213     0 /usr/bin/gzip
```

→ A cron-started backup compresses `/var/www`: a classic "box slow every night at 02:00"
cause that never stays long enough to be caught in `top`.

**Hands-on lab (test VM only)**

**Step 1 — Measure the observer effect.** Time a syscall-heavy command with and without
strace:

```bash
time dd if=/dev/zero of=/dev/null bs=1 count=500000
time strace -c -o /dev/null dd if=/dev/zero of=/dev/null bs=1 count=500000
```

**Step 2 — Compare with perf stat**, which only reads counters instead of tracing every
call:

```bash
time sudo perf stat -e task-clock dd if=/dev/zero of=/dev/null bs=1 count=500000
```

**Step 3 — Break and fix:** the strace run is many times slower. Write down the ratio; it
is the reason you never leave `strace -f` attached to a busy production process.

**How it breaks**

| Mistake | Consequence | Safer alternative |
|---------|-------------|-------------------|
| `strace -f -p` on a busy DB for minutes | Latency spike for every client | `strace -c` for 5–10 s, or `perf trace`, or bcc tools |
| `tcpdump` without filter on a 10 Gb link | Dropped packets, full disk | Filter host/port, `-c 1000`, `-w` to a file with `-C`/`-W` rotation |
| `perf record -F 10000 -a` | Heavy overhead, huge files | `-F 99` for 10–30 s |

**Why it matters for troubleshooting.** Being able to say "this tool is safe to run on a
loaded production box" is what lets you collect evidence during an incident instead of
after it.

**Next step.** Start the subsystem deep dives with the CPU.

---

## 4. CPU deep dive

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — *Diagnose and Manage Processes* (ps, top, nice, signals) ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)), then *Docker Certified Associate* — Docker Engine – Security → resource limits and cgroups ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: [CPU & performance reference](03-cpu-performance.md) · 3) Video: *Linux Performance Tools, Brendan Gregg, part 1 of 2* ([YouTube](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 4) Practice: the §4 labs, then the CPU branch of the [slow system playbook](23-playbook-slow-system.md).

The CPU is where most people start and where numbers are most often misread: load average
is not CPU usage, iowait is not CPU work, and a container can be starved while the host is
idle. Command reference: [CPU & performance](03-cpu-performance.md).

### Scheduler and run queue

**Level:** [L2 · Mid] · CPU saturation, not just utilization

**Concept.** A CPU core runs one thread at a time. Every other runnable thread waits in
that core's **run queue**. The kernel **scheduler** decides who runs next and for how long:
CFS (Completely Fair Scheduler) on Ubuntu 22.04's 5.15 kernel, EEVDF (its successor,
merged in Linux 6.6) on Ubuntu 24.04's 6.8 kernel. Both aim to share CPU time fairly,
weighted by nice value (−20 highest priority, 19 lowest) or cgroup weight. When more
threads are runnable than there are cores, they take turns, and each one's latency grows
with the queue: that is CPU saturation.

```
            CPU0                         CPU1
   run queue: [T5][T6][T7]       run queue: [T8]
   running:    T1                running:    T2
                                                         sleeping (not in any queue):
   R = running or runnable (T1,T2,T5..T8)                T3 waiting on network (S)
   S = interruptible sleep, D = uninterruptible sleep    T4 waiting on disk (D)
```

**Key terms**

| Term | Meaning |
|------|---------|
| Run queue | Threads ready to run, waiting for a core |
| Runnable (R) | Running or waiting in the run queue |
| Run-queue latency | Time a thread waits before it gets a core |
| Nice | User-space priority hint, −20..19 |
| Time slice | How long a thread runs before the scheduler may switch |
| CPU affinity | Restricting a thread to certain cores (`taskset`, cpusets) |
| NUMA | Multi-socket memory layout; remote memory is slower |

**See it on a real system**

```bash
nproc                                   # cores available to this process (respects cpusets)
lscpu | grep -E '^CPU\(s\)|Thread|Core|Socket|NUMA node\(s\)|Model name'
vmstat 1 5                              # r = runnable tasks (running + waiting)
cat /proc/PID/schedstat                 # ns on CPU, ns waiting in run queue, number of time slices
sudo runqlat-bpfcc 10 1                 # histogram of run-queue latency over 10 s
ps -eLo pid,tid,psr,ni,stat,comm --sort=psr | head   # which core (psr) each thread last ran on
```

```
$ cat /proc/2214/schedstat
918273645512 41203391842 5521873
```

→ This process has used 918 s of CPU and waited 41 s in run queues over its life. The
ratio waiting ÷ running (~4.5%) is a quick saturation indicator for one process; compare
two readings a minute apart to see the current rate.

```
Tracing run queue latency... Hit Ctrl-C to end.

     usecs               : count     distribution
         0 -> 1          : 2342     |*****                                   |
         2 -> 3          : 15671    |****************************************|
         4 -> 7          : 6120     |***************                         |
         8 -> 15         : 1803     |****                                    |
        16 -> 31         : 412      |*                                       |
        32 -> 63         : 96       |                                        |
        64 -> 127        : 31       |                                        |
       128 -> 255        : 12       |                                        |
```

→ Healthy: almost all wake-ups get a CPU within a few microseconds. On a saturated box
the mass shifts to milliseconds.

**Hands-on lab (test VM only)**

**Step 1 — Baseline:** `sudo runqlat-bpfcc 10 1` on the idle VM.

**Step 2 — Break it:** start `stress-ng --cpu $(( $(nproc) * 4 )) --timeout 120s` and run
`runqlat-bpfcc 10 1` and `vmstat 1 5` again. Note the `r` column and the shift of the
histogram into the 1–30 ms buckets.

**Step 3 — Prioritise:** while the hogs run, start a second measurement with high
priority and compare its latency:

```bash
sudo nice -n -10 sysbench cpu --threads=1 --time=10 run | grep -A4 'Latency'
nice -n 19      sysbench cpu --threads=1 --time=10 run | grep -A4 'Latency'
```

**Step 4 — Fix:** stop the load; the histogram and `r` return to baseline.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| Load ≫ cores, CPUs at 100% | `vmstat 1`, `pidstat 1` | [Slow system playbook](23-playbook-slow-system.md) |
| Latency spikes, average CPU only 50% | `runqlat-bpfcc`, `mpstat -P ALL 1` (one hot core?) | §4 throttling |
| App slow on a big multi-socket server | `lscpu`, `numastat -p PID` | [Memory reference](04-memory.md) |

**Why it matters for troubleshooting.** Run-queue length and run-queue latency measure
CPU *saturation*, which is what users feel; `%CPU` alone only measures utilization.

**Next step.** The number everyone looks at first and most often misreads: load average.

### Load average and D-state

**Level:** [L2 · Mid] · the first fork of the slow-system tree

**Concept.** The load average is an exponentially damped moving average of the number of
tasks that are **runnable (R) or in uninterruptible sleep (D)**, over 1, 5 and 15 minutes.
The D part is Linux-specific: tasks waiting for disk I/O, NFS or some kernel locks count
as load even though they use no CPU. So "load 20 on a 4-core box" can mean a CPU
shortage, or 16 processes stuck on a dead NFS server with the CPUs idle.

**Key terms**

| Term | Meaning |
|------|---------|
| Load average | Damped average of R + D tasks over 1, 5, 15 minutes |
| D state | Uninterruptible sleep, usually I/O; cannot be killed until the I/O returns |
| wchan | Kernel function a sleeping task waits in |
| Hung task | A task in D state for more than `kernel.hung_task_timeout_secs` (120 s) |

**See it on a real system**

```bash
uptime
cat /proc/loadavg                       # 1m 5m 15m running/total last-PID
ps -eo state,pid,wchan:32,comm | awk '$1=="D"'   # who is in D state, and where in the kernel
sudo cat /proc/PID/stack                # full kernel stack of a stuck task
vmstat 1 5                              # r vs b tells you which half of the load it is
```

```
$ cat /proc/loadavg
7.31 5.92 3.10 2/431 98765

$ ps -eo state,pid,wchan:32,comm | awk '$1=="D"'
D    2214 io_schedule                      mysqld
D    3051 rpc_wait_bit_killable            df
D    3077 rpc_wait_bit_killable            ls
```

→ `2/431`: only 2 tasks runnable right now out of 431, yet load is 7.3: the rest is D
state. `io_schedule` is waiting for block I/O; `rpc_wait_bit_killable` is waiting for an
NFS server. A hanging `df` or `ls` is the textbook sign of a hard NFS mount whose server
went away. The exact `wchan` names depend on the kernel version (newer kernels often show
the caller instead, such as `folio_wait_bit_common` or a `jbd2_*` function for ext4); read
them as "which subsystem", and use `/proc/PID/stack` when you need the full path.

Two traps: inside a container, `/proc/loadavg` and `uptime` show the **host's** load, not
the container's; and load is not normalized, so always compare it with `nproc`.

**Hands-on lab (test VM only)**

**Step 1 — CPU load:** `stress-ng --cpu $(nproc) --timeout 300s` and watch `uptime` every
30 s. Load climbs toward `nproc`; `vmstat` shows it all in `r`.

**Step 2 — Break it differently: I/O load with idle CPUs.** Throttle a cgroup's disk
writes and run synchronous writers inside it. Their tasks sit in D state.

```bash
# throttle writes of this scope to 1 MB/s on the device backing /var/tmp
sudo systemd-run --scope -p "IOWriteBandwidthMax=/var/tmp 1M" \
  stress-ng --hdd 4 --hdd-opts dsync --temp-path /var/tmp --timeout 180s
# second terminal
vmstat 1 5; ps -eo state,pid,wchan:32,comm | awk '$1=="D"'; uptime
```

→ CPUs mostly idle, `b` = 4, load rising toward 4+. (If the throttle has no effect on an
LVM root, pass the physical disk instead, e.g. `/dev/sda`.)

**Step 3 — Fix:** let the timeout expire. Note how slowly the 15-minute average decays:
the load average is a trailing indicator, so after a fix trust `vmstat`, not `uptime`.

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| High load, CPU idle | `vmstat 1` (`b`), `ps ... awk '$1=="D"'` | [Slow system playbook](23-playbook-slow-system.md) |
| `INFO: task X blocked for more than 120 seconds` | `dmesg -T`, `iostat -xz 1` | §6 disk |
| `df` hangs forever | `mount -t nfs,nfs4`, `ps` D state | [Storage reference](01-storage-disk.md) (NFS) |
| Load alert inside a container | Check host load and the container's cgroup instead | §4 throttling |

**Why it matters for troubleshooting.** The Ops Ladder case "High load average while the
CPU is mostly idle" is exactly this. Splitting load into R and D is the first fork in the
slow-system decision tree.

**Next step.** Break CPU time itself into categories: user, system, iowait, steal, softirq.

### CPU time: user, system, iowait, steal, softirq

**Level:** [L2 · Mid] · which half of the toolbox to open

**Concept.** The kernel accounts every tick of every CPU to one category. Reading the split
tells you *what kind* of work the CPU is doing, and therefore where to look next.

| Field (top / mpstat) | Meaning | High value usually means | Next tool |
|----------------------|---------|--------------------------|-----------|
| `us` / `%usr` | Application code | App computing (busy loops, regex, JSON, crypto, GC) | `pidstat 1`, `perf top -p PID` |
| `ni` / `%nice` | User code at positive nice | Background jobs (backups, builds) | `ps -eo ni,pid,comm --sort=-ni` |
| `sy` / `%sys` | Kernel on behalf of processes | Syscall storm, context switches, page faults, network stack | `strace -c`, `pidstat -w`, `perf top` |
| `wa` / `%iowait` | **Idle** CPU while some I/O is outstanding | Storage or NFS latency; not CPU work | `iostat -xz 1` |
| `hi` / `%irq` | Hardware interrupts | NIC/disk interrupt load | `/proc/interrupts` |
| `si` / `%soft` | Softirqs (deferred interrupt work, mainly network RX/TX) | Packet storm, high PPS, conntrack | `/proc/softirqs`, `sar -n DEV` |
| `st` / `%steal` | Time the hypervisor gave your vCPU to someone else | Overcommitted host, AWS T-instance out of CPU credits | Hypervisor / CloudWatch `CPUCreditBalance` |
| `id` / `%idle` | Nothing to do | — | — |

Two subtleties: iowait is a kind of idle time, so it can *fall* when CPU load rises even
though the disk is just as slow; and steal is invisible from inside the guest except as
this number, so a VM with 20% steal is effectively a smaller VM.

**Key terms**

| Term | Meaning |
|------|---------|
| Tick accounting | The kernel attributes CPU time to categories, visible in `/proc/stat` |
| Softirq | Deferred kernel work (NET_RX, NET_TX, TIMER, BLOCK...) run after interrupts or by `ksoftirqd/N` |
| Steal | Involuntary wait of a virtual CPU for the physical CPU |
| Guest | Time spent running a VM (on a hypervisor host) |

**See it on a real system**

```bash
mpstat -P ALL 1 5                       # per-CPU split
top                                     # press 1 for per-CPU lines
cat /proc/softirqs | grep -E 'CPU|NET_RX|NET_TX'
ps -eo pid,comm,%cpu --sort=-%cpu | grep ksoftirqd   # softirq threads busy = packet load
sar -u -f /var/log/sysstat/sa$(date +%d -d yesterday)  # yesterday's split (Ubuntu path)
```

```
10:52:01     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:52:02     all   41.22    0.00    6.11    0.25    0.00    0.51   38.40    0.00    0.00   13.51
```

→ 38% steal: the VM wants CPU but the hypervisor is not giving it. On-prem, check the
Proxmox/VMware host for overcommit; on AWS, a `t3` instance that used up its CPU credits
looks exactly like this. No amount of tuning inside the guest fixes it.

**Hands-on lab (test VM only)**

**Step 1 — Generate each category on purpose and watch `mpstat 1`:**

```bash
stress-ng --cpu 2 --timeout 30s                       # %usr
stress-ng --switch 4 --timeout 30s                    # %sys (context switches)
stress-ng --hdd 2 --hdd-opts dsync --temp-path /var/tmp --timeout 30s   # %iowait
nice -n 19 stress-ng --cpu 1 --timeout 30s            # %nice
stress-ng --sock 4 --timeout 30s                      # %sys + %soft (loopback TCP)
```

**Step 2 — Break it: steal.** If your hypervisor lets you, run a CPU hog on the *host* (or
in another VM pinned to the same physical cores) while the guest runs
`stress-ng --cpu $(nproc)`; `%steal` appears in the guest.

**Step 3 — Fix:** stop the loads and confirm `%idle` returns. For each category write one
sentence: "if I see high X in production, my next command is Y".

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| High `sy` with many small requests | `pidstat -w 1`, `strace -c -p PID` | §4 context switches |
| `ksoftirqd/0` at 100%, network slow | `cat /proc/interrupts`, `ethtool -l IFACE` (queues) | [Network speed playbook](24-playbook-network-speed.md) |
| AWS instance slow every afternoon | CloudWatch `CPUCreditBalance` | [AWS reference](16-aws-cloud.md) |
| High `wa` | `iostat -xz 1` | §6 disk |

**Why it matters for troubleshooting.** The split decides which half of the toolbox you
open. High `%usr` → profile the app. High `%sys` → look at syscalls and the kernel. High
`wa` → leave the CPU alone and go to storage. High `st` → talk to whoever owns the
hypervisor.

**Next step.** Look closer at one source of `%sys`: context switches and interrupts.

### Context switches and interrupts

**Level:** [L3 · Senior] · waiting vs fighting for CPU

**Concept.** A context switch happens when a core stops running one thread and starts
another. A **voluntary** switch means the thread blocked (waiting for I/O, a lock, a
network reply). An **involuntary** switch means the scheduler preempted it because its
time slice ended and others were waiting: a sign of CPU contention. Each switch costs a few
microseconds plus cold caches, so hundreds of thousands per second burn real CPU in
`%sys`. Interrupts are hardware telling a CPU "packet arrived" or "I/O done"; if they all
land on one core, that core becomes the bottleneck.

**Key terms**

| Term | Meaning |
|------|---------|
| `cs` (vmstat) | Context switches per second, system-wide |
| `cswch/s` (pidstat -w) | Voluntary switches per second per process |
| `nvcswch/s` (pidstat -w) | Involuntary switches per second per process |
| `in` (vmstat) | Interrupts per second |
| irqbalance | Daemon that spreads interrupts across cores |
| RSS / multiqueue NIC | Receive-side scaling: NIC spreads flows across queues and cores |

**See it on a real system**

```bash
vmstat 1 5                              # in, cs columns
pidstat -w 1 5                          # per process: voluntary vs involuntary
grep ctxt /proc/PID/status              # lifetime counters for one process
cat /proc/interrupts | head -5; grep -E 'ens|eth|nvme' /proc/interrupts
systemctl status irqbalance --no-pager
```

```
10:58:11      UID       PID   cswch/s nvcswch/s  Command
10:58:12       33      1830    812.00      3.00  apache2
10:58:12     1000      4412     12.00   2210.00  node
```

→ apache2 blocks often (waiting for clients and backends: normal). `node` is being
preempted 2,210 times per second: it wants more CPU than it gets. Combine with
`pidstat 1` (is it near 100% of one core, since Node.js is single-threaded?) and with
cgroup throttling (next topic).

**Hands-on lab (test VM only)**

**Step 1 — Baseline:** `vmstat 1 5` on the idle VM; note `cs`.

**Step 2 — Break it:** `stress-ng --switch $(nproc) --timeout 60s` and watch `cs` reach
hundreds of thousands and `%sys` rise in `mpstat`. Then `stress-ng --cpu $(( $(nproc) * 3 )) --timeout 60s`
and watch `nvcswch/s` in `pidstat -w 1` for the stress-ng workers.

**Step 3 — Fix:** stop the load. Explain in one line why the first test raises voluntary
and the second involuntary switches.

**How it breaks**

| Symptom | Likely cause | First command |
|---------|--------------|---------------|
| `cs` in the hundreds of thousands, high `%sys` | Too many threads, lock contention, tiny I/O | `pidstat -w 1`, `perf top` |
| One core at 100% `%soft`/`%irq`, others idle | Interrupts pinned to one core, single-queue NIC | `/proc/interrupts`, `ethtool -l IFACE` |
| High `nvcswch/s` | CPU contention or cgroup throttling | `vmstat 1` (`r`), `cpu.stat` |

**Why it matters for troubleshooting.** Voluntary vs involuntary switching is a cheap way
to tell "waiting for something else" from "fighting for CPU" for a single process,
without any tracing.

**Next step.** The case where the host is idle but the container is starved: cgroup CPU
limits and throttling.

### cgroup CPU limits and throttling

**Level:** [L3 · Senior] · "host idle, container slow" in Docker, Dokploy and Kubernetes

**Concept.** Docker, systemd and Kubernetes put processes into **cgroups** (control
groups), which can cap CPU. In cgroup v2 (Ubuntu 22.04+, RHEL 9) the hard cap is
`cpu.max = QUOTA PERIOD`: the group may use QUOTA microseconds of CPU time every PERIOD
microseconds (default period 100 ms). `--cpus=1.5` in Docker becomes `150000 100000`;
`limits.cpu: 500m` in Kubernetes becomes `50000 100000`. When a group uses its quota
before the period ends, **all its threads stop until the next period**: that is
throttling. A multi-threaded app can burn a 100 ms quota in 20 ms with 5 busy threads and
then sit frozen for 80 ms, so it shows latency spikes while its *average* CPU usage is
well under the limit. The soft alternative is `cpu.weight` (shares), which only matters
when there is contention and never throttles.

```
 cpu.max = 50000 100000  (0.5 CPU)          4 threads busy at once
 period:  |←─────────── 100 ms ───────────→|←─────────── 100 ms ───────────→|
 usage:   |████ 12.5 ms × 4 = 50 ms│  frozen (throttled) 87.5 ms  |████│ frozen ...
                                   └ nr_throttled += 1
```

**Key terms**

| Term | Meaning |
|------|---------|
| cgroup v2 | Unified control-group hierarchy under `/sys/fs/cgroup` |
| `cpu.max` | Hard CPU cap: quota and period in µs (`max` = no cap) |
| `cpu.weight` | Relative share under contention (1–10000, default 100) |
| `cpu.stat` | Usage and throttling counters: `nr_periods`, `nr_throttled`, `throttled_usec` |
| CPUQuota= | systemd unit setting that writes `cpu.max` |
| requests / limits | Kubernetes: request → weight and scheduling; limit → `cpu.max` |

**See it on a real system**

```bash
stat -fc %T /sys/fs/cgroup              # cgroup2fs = cgroup v2
systemd-cgtop -d 2                      # live CPU/memory per cgroup (q to quit)

# a systemd service
systemctl show UNIT -p CPUQuotaPerSecUSec -p CPUWeight
cat /sys/fs/cgroup/system.slice/UNIT.service/cpu.max
cat /sys/fs/cgroup/system.slice/UNIT.service/cpu.stat

# a Docker container (systemd cgroup driver, the Ubuntu default)
CID=$(docker inspect -f '{{.Id}}' CONTAINER)
cat /sys/fs/cgroup/system.slice/docker-$CID.scope/cpu.max
cat /sys/fs/cgroup/system.slice/docker-$CID.scope/cpu.stat
docker stats --no-stream CONTAINER
```

```
$ cat /sys/fs/cgroup/system.slice/docker-3f2a...e4b.scope/cpu.max
50000 100000

$ cat /sys/fs/cgroup/system.slice/docker-3f2a...e4b.scope/cpu.stat
usage_usec 81234567
user_usec 80011223
system_usec 1223344
nr_periods 5321
nr_throttled 4870
throttled_usec 312456789
nr_bursts 0
burst_usec 0
```

→ Limited to 0.5 CPU, and throttled in 4870 of 5321 periods (92%), frozen for 312 s in
total. Inside the container the app just looks slow; on the host `top` shows plenty of
idle CPU. Compare two readings a minute apart to get the current throttling rate. In
Prometheus: `rate(container_cpu_cfs_throttled_periods_total[5m]) / rate(container_cpu_cfs_periods_total[5m])` (§11).

**Hands-on lab (test VM only)**

**Step 1 — Build:** run a CPU-bound benchmark without a limit and note events per second.

```bash
sysbench cpu --threads=4 --time=20 run | grep -E 'events per second|95th'
```

**Step 2 — Break it:** run the same benchmark in a scope limited to half a CPU and read
the throttling counters while it runs.

```bash
sudo systemd-run --scope --unit=throttle-lab -p CPUQuota=50% \
  sysbench cpu --threads=4 --time=20 run | grep -E 'events per second|95th'
# second terminal, while it runs:
cat /sys/fs/cgroup/system.slice/throttle-lab.scope/cpu.stat
```

→ Events per second drop to 0.5 CPU's worth: about one eighth on a 4-vCPU VM, one
quarter on 2 vCPUs (the unlimited run could use at most `nproc` CPUs). The 95th
percentile latency jumps (threads freeze at the end of each period), and `nr_throttled`
climbs every period.

**Step 3 — Same with Docker:**

```bash
docker run --rm --cpus=0.5 --name thr alpine sh -c 'while :; do :; done' &
sleep 10; docker stats --no-stream thr
cat /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' thr).scope/cpu.stat
docker stop thr
```

**Step 4 — Fix:** raise or remove the limit (`--cpus=2`, `CPUQuota=200%`, or in
Kubernetes raise `limits.cpu` or remove it and keep a sensible `requests.cpu`), and
match the app's thread count to its limit (JVM `-XX:ActiveProcessorCount`, `GOMAXPROCS`
on older Go versions, Gunicorn `--workers`).

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| Container slow, host idle | `cpu.stat` `nr_throttled`, `docker stats` | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| p99 latency spikes every few seconds on K8s | Throttling ratio in Prometheus | [Kubernetes learn module](31-learn-kubernetes.md) |
| Liveness probe timeouts under load | Throttled pod cannot answer in time | `kubectl describe pod POD` events |
| `docker stats` shows 50% and never more | `--cpus=0.5` set in compose/Dokploy | `docker inspect -f '{{.HostConfig.NanoCpus}}' CONTAINER` |

**Why it matters for troubleshooting.** In Dokploy, Swarm and Kubernetes, CPU limits are
set in YAML and forgotten. "Host idle, app slow" is very often throttling, and only the
cgroup counters prove it.

**Next step.** When the CPU really is busy, find out *where*: perf and flame graphs.

### perf and flame graphs

**Level:** [L3 · Senior] · where CPU time actually goes

**Concept.** `perf` samples the stack of whatever is running on each CPU many times per
second. Counting which functions appear most often tells you where CPU time goes, without
modifying the application. A **flame graph** draws those stacks: each box is a function,
its **width** is the share of samples it was on-CPU (including its children), the y-axis
is stack depth (callers below, callees above), and the x-axis is sorted alphabetically,
**not time**. Look for wide plateaus near the top: that function itself burns CPU.

```
          ┌────────┐
          │ sha512 │ ← wide top box = hot code (fix or cache this)
 ┌────────┴────────┴───┐┌──────────┐
 │ password_verify     ││ json_enc │
 ├─────────────────────┴┴──────────┴──────┐
 │ handle_request                          │
 ├─────────────────────────────────────────┤
 │ main                                    │   width = % of CPU samples
 └─────────────────────────────────────────┘
```

**Key terms**

| Term | Meaning |
|------|---------|
| Sample | One snapshot of the current stack on a CPU |
| `-F 99` | Sampling frequency (99 Hz) |
| `-g` | Record call graphs (stacks) |
| Symbols | Function names; missing symbols show as hex addresses or `[unknown]` |
| Frame pointers | Register convention that makes stack walking cheap; Ubuntu 24.04 builds its packages with them, which makes profiles much better |
| On-CPU vs off-CPU | Time running vs time blocked; perf sampling shows on-CPU only |

**See it on a real system**

```bash
sudo perf top                           # live hottest functions, whole system
sudo perf top -p PID                    # one process
sudo perf record -F 99 -g -p PID -- sleep 30   # 30 s profile of one process
sudo perf report --stdio --no-children | head -60
sudo perf stat -p PID -- sleep 10       # counters: task-clock, context switches, IPC (bare metal)
```

```
Samples: 48K of event 'cpu-clock:ppp', 4000 Hz, Event count (approx.): 9874123456 lost: 0/0
Overhead  Shared Object            Symbol
  31.42%  libcrypto.so.3           [.] sha512_block_data_order_avx2
  12.08%  php-fpm8.3               [.] execute_ex
   6.77%  [kernel]                 [k] rep_movs_alternative
   4.12%  libc.so.6                [.] __memmove_avx_unaligned_erms
```

→ 31% of all CPU time is SHA-512 in OpenSSL, called from PHP: password hashing on every
request (for example a login check that runs on each API call). The fix is in the
application, not more cores. `cpu-clock` instead of `cycles` means this VM exposes no
hardware performance counters; `perf stat` will show `not supported` for cycles and
instructions there, which is normal in many VMs.

Making a flame graph (Brendan Gregg's FlameGraph scripts, two Perl files you copy onto the
box):

```bash
sudo perf record -F 99 -a -g -- sleep 30
sudo perf script > /var/tmp/out.perf
./stackcollapse-perf.pl /var/tmp/out.perf | ./flamegraph.pl > /var/tmp/cpu-flame.svg
# open the SVG in a browser; click to zoom, search with Ctrl-F
```

JIT-compiled runtimes (Java, Node.js) show `[unknown]` frames unless they publish a symbol
map (Node: `--perf-basic-prof`; Java: async-profiler is the easier route). For Python use
py-spy (§8).

**Hands-on lab (test VM only)**

**Step 1 — Build a CPU hog you can recognise:**

```bash
python3 - <<'EOF' &
import hashlib, time
end = time.time() + 120
while time.time() < end:
    hashlib.sha512(b"x" * 4096).hexdigest()
EOF
HOG=$!          # PID of the background python process
```

**Step 2 — Profile it:** `sudo perf top -p $HOG`. You should see OpenSSL's SHA-512
routine and the Python interpreter's eval loop at the top.

**Step 3 — Break the profile:** run `perf top` without `sudo` on Ubuntu (restrictive
`kernel.perf_event_paranoid`), or on a kernel without a matching `linux-tools` package,
and read the error. **Fix:** use sudo and install `linux-tools-$(uname -r)`.

**Step 4 — Make a flame graph** of the same process with the FlameGraph scripts and find
the widest top box.

**How it breaks**

| Error text | Cause | Fix |
|------------|-------|-----|
| `WARNING: perf not found for kernel 6.8.0-45` | linux-tools for running kernel missing | `sudo apt install linux-tools-$(uname -r)` |
| `Access to performance monitoring and observability operations is limited` | `perf_event_paranoid` restriction | Run with `sudo` |
| Stacks full of `[unknown]` | No symbols / no frame pointers / JIT | Install `-dbgsym` packages, use runtime profilers |
| Profile shows only `cpu_idle` / `default_idle` | The process is not on-CPU: it is waiting | Off-CPU analysis: `offcputime-bpfcc`, strace, §8 |

**Why it matters for troubleshooting.** "CPU is at 100%" ends the argument about *whether*
there is a problem; a profile ends the argument about *what* to fix, and gives the
developers evidence instead of a vague ticket.

**Next step.** Move to the second resource: memory.

---

## 5. Memory deep dive

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage (swap) and Operations Deployment → *Change Kernel Runtime Parameters* (sysctl) ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine – Security → resource limits for memory ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) Note: [Memory reference](04-memory.md) · 4) Practice: the §5 labs, then the OOM and exit-137 cases in the [containers playbook](26-playbook-containers-k8s.md).

Memory problems produce the most confusing symptoms: "free" memory near zero on a healthy
box, processes vanishing without a log line, servers that freeze instead of failing. This
area explains how Linux actually uses RAM. Command reference: [Memory](04-memory.md).

### Virtual vs resident memory

**Level:** [L2 · Mid] · picking the right memory column

**Concept.** Every process gets its own **virtual address space**, a huge range of
addresses it may use. Only pages it actually touches are backed by physical RAM; that is
its **resident set** (RSS). So VSZ/VIRT (virtual size) is mostly a promise and often
enormous and harmless (a JVM or a Go program reserving gigabytes), while RSS is real RAM.
RSS double-counts shared pages (libraries, forked workers sharing memory), which is why
PSS (proportional set size: shared pages divided among their users) is the honest number
for many forked workers such as Apache prefork or PHP-FPM.

```
 virtual address space of one process (VSZ = all of it)
 ┌──────────┬───────────┬───────────────┬───────────────┬──────────┐
 │ code     │ libraries │ heap          │ mmap'd files  │ stack    │
 │ (shared) │ (shared)  │ (anon, private│ (page cache)  │          │
 └────┬─────┴─────┬─────┴──────┬────────┴───────┬───────┴──────────┘
      ▼           ▼            ▼                ▼
   only touched pages are in RAM = RSS (RssAnon + RssFile + RssShmem)
```

**Key terms**

| Term | Meaning |
|------|---------|
| VSZ / VIRT / VmSize | Virtual address space size; not RAM |
| RSS / RES / VmRSS | Resident pages in RAM, shared ones included |
| PSS | RSS with shared pages divided among sharers |
| Anonymous memory | Heap, stack: no file behind it; can only go to swap |
| File-backed memory | Pages of files (code, mmap, page cache); can be dropped and re-read |
| Overcommit | Linux lets processes reserve more virtual memory than RAM + swap |

**See it on a real system**

```bash
ps -eo pid,user,vsz,rss,comm --sort=-rss | head -8          # KB
grep -E 'VmSize|VmRSS|RssAnon|RssFile|RssShmem|VmSwap' /proc/PID/status
sudo cat /proc/PID/smaps_rollup                               # Rss vs Pss, private vs shared
sudo smem -tk -P apache2                                      # PSS per process + total (apt install smem)
```

```
    PID USER        VSZ    RSS COMMAND
   2214 mysql   2741332 812440 mysqld
   1830 www-data 891204  61220 apache2
   1831 www-data 891204  60984 apache2
```

```
$ sudo smem -tk -P apache2
  PID User     Command                         Swap      USS      PSS      RSS
 1831 www-data /usr/sbin/apache2 -k start         0    18.1M    24.6M    59.6M
 1830 www-data /usr/sbin/apache2 -k start         0    18.3M    24.9M    59.8M
...
-------------------------------------------------------------------------------
   12 4                                           0   214.0M   301.2M   712.8M
```

→ Summing RSS says Apache uses 713 MB; PSS says 301 MB, because most of each worker's RSS
is shared code. USS (unique set size) is what you would free by killing one worker.

**Hands-on lab (test VM only)**

**Step 1 — Allocate virtual but not resident memory:**

```bash
python3 -c 'import mmap,time; m=mmap.mmap(-1, 4*1024**3); time.sleep(60)' &
ps -o pid,vsz,rss,comm -p $!
```

→ VSZ ≈ 4 GB, RSS a few MB: nothing was touched.

**Step 2 — Touch it:** the same, but write one byte per page of the first 1 GB, and watch
RSS grow:

```bash
python3 -c 'import mmap,time; m=mmap.mmap(-1, 4*1024**3); [m.__setitem__(i,1) for i in range(0, 1024**3, 4096)]; time.sleep(60)' &
sleep 15; ps -o pid,vsz,rss,comm -p $!
```

**Step 3 — Break your intuition:** run `free -m` before and after; "used" grows by about
1 GB only in step 2. **Fix:** kill both test processes (`kill %1 %2`).

**How it breaks**

| Symptom | Real meaning | First command |
|---------|--------------|---------------|
| "Java uses 20 GB!" (VIRT) | Reserved address space | RSS in `ps`, `smaps_rollup` |
| Sum of RSS > total RAM | Shared pages counted many times | `smem -tk` (PSS) |
| `fork: Cannot allocate memory` with RAM free | Overcommit limit or pid/thread limit | `cat /proc/sys/vm/overcommit_memory`, `ulimit -u`, `pids.max` |

**Why it matters for troubleshooting.** Picking the wrong column produces wrong
conclusions ("Java leaks 20 GB", "Apache needs 4 GB"). Size worker counts with PSS, and
watch RSS of the anonymous kind for leaks.

**Next step.** Where the rest of the RAM goes: the page cache.

### Page cache, dirty pages and reclaim

**Level:** [L2 · Mid] · why "free memory is low" is usually fine

**Concept.** Linux uses otherwise-free RAM to cache file contents (the **page cache**), so
a second read of a file comes from RAM. That is why `free` shows little "free" memory on a
healthy server; the number to watch is **available**, which estimates how much can be
reclaimed without swapping. Writes also go to the page cache first as **dirty** pages and
are flushed to disk later by writeback threads. When memory runs short, the kernel
**reclaims**: first clean cache pages (cheap: just drop them), then dirty pages (must be
written first), then anonymous pages (must go to swap). Background reclaim by `kswapd` is
harmless; **direct reclaim**, where the allocating process has to free memory itself
before it can continue, adds latency to that process.

```
 RAM ┌──────────────┬───────────────────────────┬──────────┐
     │ anon (apps)  │ page cache (file pages)   │ free     │
     │ heap, stacks │ clean ......... dirty     │          │
     └──────────────┴───────────────────────────┴──────────┘
       → swap only    → drop (clean)              "available" ≈ free + reclaimable cache
                        → write back, then drop (dirty)
```

**Key terms**

| Term | Meaning |
|------|---------|
| Page cache / buff/cache | File data cached in RAM |
| Available | Estimate of memory usable without swapping |
| Dirty | Modified cache pages not yet written to disk |
| Writeback | Flushing dirty pages to disk |
| `vm.dirty_background_ratio` / `vm.dirty_ratio` | % of memory dirty before background flushing starts (10) / before writers are blocked (20) |
| kswapd | Background reclaim thread |
| Direct reclaim | Reclaim done synchronously by an allocating process (latency!) |
| Slab | Kernel object caches (dentries, inodes) |

**See it on a real system**

```bash
free -m
grep -E '^(MemTotal|MemFree|MemAvailable|Cached|Dirty|Writeback|Active\(file\)|Inactive\(file\)|Slab|SReclaimable)' /proc/meminfo
sysctl vm.dirty_background_ratio vm.dirty_ratio vm.dirty_expire_centisecs
sar -B 1 5                              # pgscank/s (kswapd) vs pgscand/s (direct reclaim)
grep -E 'allocstall|pgscan_direct|pgsteal' /proc/vmstat
sudo fincore /var/lib/mysql/ibdata1     # how much of a file is in the page cache (util-linux; sudo: the datadir is mysql-only)
```

```
10:12:01     pgpgin/s pgpgout/s   fault/s  majflt/s  pgfree/s pgscank/s pgscand/s pgsteal/s    %vmeff
10:12:02      8120.00  41210.00  23011.00     98.00  31877.00  18892.00   6410.00  24021.00     94.95
```

→ `pgscand/s` = 6,410: processes are doing direct reclaim themselves, and `majflt/s` = 98
means pages are being re-read from disk. Memory is under pressure even if nothing is
swapping yet. PSI memory (later topic) will confirm it as stall time.

```
$ sudo fincore /var/lib/mysql/ibdata1
   RES  PAGES   SIZE FILE
  1.2G 314572   1.5G /var/lib/mysql/ibdata1
```

→ 1.2 GB of this 1.5 GB file is cached: reads of it are RAM-speed.

**Hands-on lab (test VM only)**

**Step 1 — Watch the cache fill:** read a large file twice and time both reads.

```bash
head -c 1G /dev/urandom > /var/tmp/cache-test.bin
sync; echo 1 | sudo tee /proc/sys/vm/drop_caches >/dev/null   # test VM only: empties clean cache
time cat /var/tmp/cache-test.bin > /dev/null                   # from disk
time cat /var/tmp/cache-test.bin > /dev/null                   # from page cache
fincore /var/tmp/cache-test.bin; free -m
```

**Step 2 — Watch dirty pages:** write a file and watch `Dirty` and `Writeback` grow and
drain.

```bash
dd if=/dev/zero of=/var/tmp/dirty-test.bin bs=1M count=1500 &
watch -n1 "grep -E '^(Dirty|Writeback):' /proc/meminfo"
```

**Step 3 — Break it:** squeeze memory with `stress-ng --vm 1 --vm-bytes 85% --vm-keep --timeout 90s`
and watch `sar -B 1` (scans) and the second `cat` timing get slower (cache evicted).

**Step 4 — Fix:** stop the load and remove the test files: `rm /var/tmp/cache-test.bin /var/tmp/dirty-test.bin`.

> ⚠️ `drop_caches` is a diagnostic for test VMs. On a production database server it
> causes a burst of disk reads and a latency spike while the cache refills. It never
> "frees memory" in any useful sense.

**How it breaks**

| Symptom | Real meaning | First command |
|---------|--------------|---------------|
| "Free memory is 200 MB, add RAM!" | Cache is doing its job | `free -m` (available) |
| Writes stall for seconds periodically | Dirty limit reached, writers throttled | `grep -E 'Dirty|Writeback' /proc/meminfo`, `iostat -xz 1` |
| Latency up, no swap, `pgscand` high | Direct reclaim | `sar -B 1`, PSI memory |
| "Memory missing", ps does not add up | Slab, tmpfs or shared memory | `slabtop -o`, `df -h -t tmpfs` ([Memory reference](04-memory.md)) |

**Why it matters for troubleshooting.** Most "memory full" alarms are cache; most real
memory trouble shows up first as reclaim activity and stall time, not as zero free
memory. Knowing the difference saves you from unnecessary RAM upgrades and from missing
real pressure.

**Next step.** When reclaim is not enough, anonymous pages go to swap.

### Swap and swappiness

**Level:** [L2 · Mid] · usage vs activity, and thrashing

**Concept.** Swap is disk space where the kernel can park anonymous pages that have not
been used for a while, freeing RAM for active work and for the page cache. Swap **usage**
alone is harmless (old idle pages parked there); swap **activity** (pages going in and out
every second, `si`/`so` in vmstat) means the working set does not fit in RAM and every
access may wait for the disk: thrashing. `vm.swappiness` (0–200, default 60) tunes how
willing the kernel is to swap anonymous memory versus dropping page cache; lower values
prefer dropping cache.

**Key terms**

| Term | Meaning |
|------|---------|
| Swap-out (`so`) | Pages written from RAM to swap |
| Swap-in (`si`) | Pages read back from swap; the process waited for it |
| Working set | Memory a workload actively uses |
| Thrashing | Constant swapping because the working set does not fit |
| `vm.swappiness` | Preference for swapping anon pages vs dropping cache |

**See it on a real system**

```bash
swapon --show                           # swap devices/files and usage
free -m
vmstat 1 5                              # si / so columns (KB/s)
sar -W 1 5                              # pswpin/s pswpout/s
sysctl vm.swappiness
for f in /proc/[0-9]*/status; do awk '/^Name/{n=$2} /^VmSwap/{if($2>0) print $2" kB", n}' "$f"; done 2>/dev/null | sort -rn | head
```

```
$ swapon --show
NAME      TYPE SIZE  USED PRIO
/swap.img file   2G  1.6G   -2

 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3  4 1677312  61200   1204  98112 4120 6024  9812  6890 3120 4410 12  9 31 48  0
```

→ 1.6 GB of swap used **and** 4–6 MB/s moving in and out every second, cache squeezed to
98 MB, high `wa`. This box is thrashing; it will feel frozen. Compare: 1.6 GB swap used
with `si`/`so` at 0 would be fine.

Kubernetes note: kubelet refuses to start with swap enabled unless it is explicitly
configured to allow it (`failSwapOn: false` plus a swap behaviour), which is why CKA
setups run `swapoff -a` and remove the swap line from `/etc/fstab`.

**Hands-on lab (test VM only)**

**Step 1 — Baseline:** `swapon --show; vmstat 1 5` on the idle VM (2 GB swap configured).

**Step 2 — Break it:** allocate more anonymous memory than is available and keep touching
it:

```bash
AVAIL_MB=$(free -m | awk '/^Mem:/{print $7}')
stress-ng --vm 1 --vm-bytes $(( AVAIL_MB * 120 / 100 ))M --vm-keep --timeout 120s &
vmstat 1 20
```

→ `so` rises first, then `si` too, `wa` climbs, and the VM's shell becomes sluggish.

**Step 3 — Experiment with swappiness** (test VM only) and repeat: `sudo sysctl vm.swappiness=10`.
Note the difference, then restore: `sudo sysctl vm.swappiness=60`.

**Step 4 — Fix:** stop stress-ng. Swap usage stays high afterwards (pages are only read
back when needed), but `si`/`so` return to zero: the box is healthy again.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| Server "frozen", SSH takes a minute | `vmstat 1` (si/so), `ps aux --sort=-rss` | [Slow system playbook](23-playbook-slow-system.md) |
| Swap 90% used, no activity | Nothing urgent; check which process owns it | Loop above |
| kubelet: `running with swap on is not supported` | Swap enabled on a K8s node | `swapon --show`, [Kubernetes learn module](31-learn-kubernetes.md) |

**Why it matters for troubleshooting.** A thrashing box looks like a CPU or disk problem
(high load, high iowait) until you read `si`/`so`. Without swap, the same situation ends
in the OOM killer instead, which is the next topic.

**Next step.** What happens when RAM and swap are both exhausted: the OOM killer.

### The OOM killer and oom_score_adj

**Level:** [L2 · Mid] · processes that vanish without a log line

**Concept.** Linux overcommits memory: it lets processes reserve more than exists, betting
they will not all use it. When the bet fails and reclaim cannot free enough, the
**out-of-memory (OOM) killer** picks a victim and sends it SIGKILL. The victim is the
process with the highest `oom_score`, mostly driven by its memory size and adjusted by
`oom_score_adj` (−1000 = never kill, +1000 = kill first). The process gets no chance to log
anything; the evidence is in the **kernel** log. A cgroup limit (container `--memory`,
Kubernetes `limits.memory`, systemd `MemoryMax=`) triggers a **cgroup** OOM kill even when
the host has plenty of free RAM. Exit code 137 = 128 + 9 (SIGKILL).

**Key terms**

| Term | Meaning |
|------|---------|
| OOM killer | Kernel mechanism that kills a process to free memory |
| `oom_score` | Current badness score of a process (higher = more likely victim) |
| `oom_score_adj` | Admin bias, −1000..1000 |
| `vm.overcommit_memory` | 0 heuristic (default), 1 always allow, 2 strict limit |
| `OOMScoreAdjust=` / `OOMPolicy=` | systemd unit settings |
| QoS class (K8s) | Guaranteed (adj −997), Burstable (in between), BestEffort (adj 1000) |
| systemd-oomd | Userspace killer that acts earlier, using PSI (enabled on Ubuntu desktop installs) |

**See it on a real system**

```bash
journalctl -k -b --no-pager | grep -iE 'out of memory|oom-kill|killed process'
sudo dmesg -T | grep -iE 'out of memory|killed process'
cat /proc/PID/oom_score /proc/PID/oom_score_adj
systemctl status UNIT --no-pager | grep -iE 'oom|result'     # "Failed with result 'oom-kill'"
docker inspect -f '{{.State.OOMKilled}} {{.State.ExitCode}}' CONTAINER
kubectl describe pod POD | grep -A3 'Last State'               # Reason: OOMKilled, Exit Code: 137
journalctl -u systemd-oomd --no-pager | tail                   # if systemd-oomd is active
```

```
[Sat Oct  3 03:12:44 2026] oom-kill:constraint=CONSTRAINT_NONE,nodemask=(null),cpuset=/,mems_allowed=0,global_oom,task_memcg=/system.slice/app.service,task=java,pid=2134,uid=1001
[Sat Oct  3 03:12:44 2026] Out of memory: Killed process 2134 (java) total-vm:8321412kB, anon-rss:6873220kB, file-rss:2304kB, shmem-rss:0kB, UID:1001 pgtables:14112kB oom_score_adj:0

[Sat Oct  3 11:20:07 2026] oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=docker-3f2a...e4b.scope,mems_allowed=0,oom_memcg=/system.slice/docker-3f2a...e4b.scope,task_memcg=/system.slice/docker-3f2a...e4b.scope,task=node,pid=4412,uid=1000
[Sat Oct  3 11:20:07 2026] Memory cgroup out of memory: Killed process 4412 (node) total-vm:1823344kB, anon-rss:521004kB, file-rss:31220kB, shmem-rss:0kB, UID:1000 pgtables:2412kB oom_score_adj:0
```

→ First block: a **global** OOM (`CONSTRAINT_NONE`, `global_oom`): the whole host ran out;
java with 6.8 GB anonymous memory was chosen. Second block: a **cgroup** OOM
(`CONSTRAINT_MEMCG`): a container hit its own memory limit; the host may have had plenty
free. Different fixes: the first needs less total demand or more RAM, the second a higher
limit or a fix for the app's usage.

**Hands-on lab (test VM only)**

**Step 1 — Build a protected and an unprotected process:**

```bash
sleep 3600 & echo -1000 | sudo tee /proc/$!/oom_score_adj   # protected (never chosen)
cat /proc/$!/oom_score
```

**Step 2 — Break it: trigger a cgroup OOM safely** (only the scope is affected, not the
host):

```bash
sudo systemd-run --scope -p MemoryMax=200M -p MemorySwapMax=0 \
  stress-ng --vm 1 --vm-bytes 400M --vm-keep --oomable --timeout 30s
journalctl -k --since '2 min ago' --no-pager | grep -iE 'memory cgroup out of memory|killed process'
```

**Step 3 — Same with Docker:**

```bash
docker run --rm --memory=128m --memory-swap=128m --name oomtest alpine \
  sh -c 'head -c 300m /dev/zero | tail' ; echo "exit code: $?"
```

→ Exit code 137, `Memory cgroup out of memory` in the kernel log, and `docker inspect`
would show `OOMKilled=true` (the container is gone here because of `--rm`).

**Step 4 — Fix:** kill the protected sleep (`kill %1`). Decide for a real app: raise the
limit **only** after checking whether usage is legitimate or a leak (later topic).

> ⚠️ Setting `oom_score_adj = -1000` on many processes is dangerous: when the host runs out
> of memory the kernel has nothing left to kill and may panic or freeze. Protect only the
> one critical process (for example sshd or the DB), and give it a memory budget.

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| Process vanished, its own log says nothing | `journalctl -k -b` and grep for `killed process` | [Memory reference](04-memory.md) |
| Container exit 137, `OOMKilled: true` | `docker inspect`, `memory.events` | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| Pod `OOMKilled`, node has free RAM | `kubectl describe pod`, `limits.memory` | [Kubernetes learn module](31-learn-kubernetes.md) |
| `Failed with result 'oom-kill'` on a unit | `systemctl show UNIT -p MemoryMax` | [Services reference](07-services-systemd.md) |

**Why it matters for troubleshooting.** OOM kills are the Ops Ladder case "A process was
killed and its own log says nothing". The kernel log line is the only evidence, and it
tells you global vs cgroup, which decides the fix.

**Next step.** Measure memory pressure *before* it becomes an OOM: PSI.

### Pressure stall information (PSI)

**Level:** [L3 · Senior] · a direct saturation number per resource

**Concept.** Utilization and free-memory numbers do not tell you whether work is actually
**waiting**. PSI does: the kernel measures the share of wall-clock time in which tasks were
stalled because of a shortage of CPU, memory or I/O. `some` is the share of time at least
one task was stalled; `full` is the share of time all non-idle tasks were stalled at once
(nothing productive happened). It exists system-wide in `/proc/pressure/` and per cgroup
(`cpu.pressure`, `memory.pressure`, `io.pressure`) since kernel 4.20; Ubuntu kernels have
it on. It is the closest thing Linux has to a direct "saturation" number.

**Key terms**

| Term | Meaning |
|------|---------|
| `some avg10` | % of the last 10 s in which at least one task stalled |
| `full avg10` | % of the last 10 s in which all non-idle tasks stalled |
| `total` | Cumulative stall time in µs (use for rates) |
| avg60 / avg300 | Same over 1 and 5 minutes |

**See it on a real system**

```bash
grep -H . /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
cat /sys/fs/cgroup/system.slice/UNIT.service/memory.pressure
watch -n2 'grep -H . /proc/pressure/*'
```

```
/proc/pressure/cpu:some avg10=0.12 avg60=0.40 avg300=0.35 total=88123411
/proc/pressure/cpu:full avg10=0.00 avg60=0.00 avg300=0.00 total=0
/proc/pressure/memory:some avg10=12.47 avg60=8.03 avg300=2.11 total=48215533
/proc/pressure/memory:full avg10=4.90 avg60=3.12 avg300=0.80 total=19022871
/proc/pressure/io:some avg10=31.20 avg60=22.45 avg300=9.71 total=912334012
/proc/pressure/io:full avg10=18.33 avg60=12.04 avg300=5.10 total=512230111
```

→ CPU is fine. For 12% of the last 10 seconds some task waited for memory (reclaim or
swap-in), and for 18% of the time *everything* was stuck on I/O. This box is memory- and
I/O-starved; the two often go together (reclaim causes I/O). The system-wide CPU `full`
line is always zero; it is meaningful only per cgroup. Prometheus exposes these as
`node_pressure_*_seconds_total` (§11).

**Hands-on lab (test VM only)**

**Step 1 — Baseline:** `grep -H . /proc/pressure/*` on the idle VM (all near 0).

**Step 2 — Break each resource and watch which line moves:**

```bash
stress-ng --cpu $(( $(nproc) * 2 )) --timeout 60s                    # cpu some
AVAIL_MB=$(free -m | awk '/^Mem:/{print $7}')
stress-ng --vm 1 --vm-bytes $(( AVAIL_MB * 110 / 100 ))M --vm-keep --timeout 60s   # memory some/full
stress-ng --hdd 4 --hdd-opts dsync --temp-path /var/tmp --timeout 60s  # io some/full
```

**Step 3 — Fix and observe decay:** stop each load; `avg10` drops within seconds, `avg300`
over minutes.

**How it breaks**

| PSI signal | Meaning | Next command |
|------------|---------|--------------|
| memory `some` > 10% sustained | Reclaim/swap stalls are hurting latency | `sar -B 1`, `vmstat 1` |
| memory `full` > 5% | Host close to thrashing or OOM | `ps aux --sort=-rss`, OOM log |
| io `full` high | Storage is the bottleneck | `iostat -xz 1` |
| cgroup `cpu.pressure` high, host CPU idle | Throttling or weight starvation | `cpu.stat` |

**Why it matters for troubleshooting.** PSI answers "is anyone actually waiting?" in one
file per resource. It is also the best input for alerts on resource saturation, because
it measures pain rather than busy-ness.

**Next step.** Memory limits per service and per container: cgroup memory.

### cgroup memory limits

**Level:** [L3 · Senior] · container and pod memory incidents

**Concept.** cgroup v2 gives each group of processes its own memory accounting and limits:
`memory.max` is the hard limit (exceed it after reclaim → cgroup OOM kill),
`memory.high` is a soft limit (the group is throttled and reclaimed aggressively but not
killed), `memory.low`/`memory.min` protect memory from being reclaimed by others. Page
cache that the group's processes create **counts** toward its usage, but clean cache is
reclaimed before an OOM kill. That is why the useful number is the **working set**:
usage minus inactive file cache. Kubernetes uses working set for eviction decisions, and
`docker stats` subtracts inactive cache from its MEM USAGE.

**Key terms**

| File / setting | Meaning |
|----------------|---------|
| `memory.current` | Current usage of the group (includes page cache) |
| `memory.max` | Hard limit (`--memory`, `limits.memory`, `MemoryMax=`) |
| `memory.high` | Throttling threshold (`MemoryHigh=`) |
| `memory.swap.max` | Swap limit for the group |
| `memory.events` | Counters: `high`, `max`, `oom`, `oom_kill` |
| `memory.stat` | Breakdown: `anon`, `file`, `inactive_file`, `slab`... |
| `memory.peak` | Highest usage seen (kernel 5.19+, so Ubuntu 24.04 yes, 22.04 GA kernel no) |
| Working set | `memory.current` − `inactive_file` |

**See it on a real system**

```bash
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' CONTAINER).scope
cat $CG/memory.max $CG/memory.current
cat $CG/memory.events
grep -E '^(anon|file|inactive_file|active_file|slab) ' $CG/memory.stat
docker stats --no-stream CONTAINER
systemctl show UNIT -p MemoryCurrent -p MemoryMax -p MemoryHigh
```

```
536870912
529211392
low 0
high 0
max 1841
oom 3
oom_kill 3
anon 401113088
file 121634816
inactive_file 98123776
active_file 23511040
slab 5212160

CONTAINER ID   NAME        CPU %     MEM USAGE / LIMIT   MEM %     NET I/O         BLOCK I/O        PIDS
3f2a9c1d7e4b   app-web-1   12.40%    411.6MiB / 512MiB   80.39%    1.2GB / 3.4GB   12.1MB / 0B      23
```

→ Limit 512 MiB, current 505 MiB, of which ~94 MiB is reclaimable inactive cache. The group
hit `max` 1,841 times (reclaim was forced) and was OOM-killed 3 times. Anonymous memory
(383 MiB) is the part that will not shrink: if it keeps growing between restarts you are
looking at a leak.

**Hands-on lab (test VM only)**

**Step 1 — Build:** run a container with a 256 MB limit and print its counters:

```bash
docker run -d --name memlab --memory=256m --memory-swap=256m alpine sleep 3600
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' memlab).scope
cat $CG/memory.max $CG/memory.events
```

**Step 2 — Fill it with page cache (not a problem):**

```bash
docker exec memlab sh -c 'head -c 200m /dev/urandom > /tmp/f; cat /tmp/f > /dev/null'
cat $CG/memory.current; grep -E '^(anon|file) ' $CG/memory.stat
```

→ Usage climbs near the limit, mostly `file`, and nothing is killed (alpine's `/tmp` is the
container's writable layer, so this is page cache, not tmpfs).

**Step 3 — Break it with anonymous memory:**

```bash
docker exec memlab sh -c 'head -c 400m /dev/zero | tail'; echo "exit: $?"
cat $CG/memory.events
```

→ `oom_kill` increments; the `tail` process was killed (the container's main `sleep`
survives because the victim was the biggest process).

**Step 4 — Fix:** `docker rm -f memlab`. For a real service, measure the anonymous working
set at peak, then set the limit about 25–50% above it.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| `MEM %` near 100% in docker stats, no kills | Probably cache; check `memory.stat` anon vs file | — |
| `memory.events` `oom_kill` > 0 | Limit too low or leak | Next topic, [Containers playbook](26-playbook-containers-k8s.md) |
| Pod evicted: `The node was low on resource: memory` | Node pressure, not the pod limit | `kubectl describe node NODE` |
| App slow, `memory.events high` rising | `memory.high` throttling | `systemctl show UNIT -p MemoryHigh` |

**Why it matters for troubleshooting.** In Dokploy, Swarm and Kubernetes most memory
incidents are cgroup incidents. Reading `memory.events` and `memory.stat` turns "the
container keeps dying" into "anon memory grows 40 MB/hour until the 512 MiB limit".

**Next step.** Tell a leak from normal growth.

### Memory leaks

**Level:** [L3 · Senior] · proving a leak with a time series

**Concept.** A leak is memory a program allocates and never releases, so its anonymous
RSS grows with time or with the number of requests handled, until a limit or the OOM
killer stops it. Not every growth is a leak: caches that warm up and then plateau, heap
sizing in garbage-collected runtimes (a JVM may grow to its max heap and stay there), and
allocator fragmentation all look similar at first. The test is the **shape** over hours or
days: steady, unbounded growth that correlates with work done, and drops only at restart.

```
 RSS                                                     leak: grows with requests, never plateaus
  │                                          ╱╲ restart     ╱
  │                                       ╱╱   ╲         ╱╱
  │                                    ╱╱       ╲     ╱╱
  │         cache/heap warm-up      ╱╱           ╲ ╱╱
  │    ╭───────────────────────── plateau (fine)
  │  ╱
  └──────────────────────────────────────────────────────────▶ time
```

**Key terms**

| Term | Meaning |
|------|---------|
| Leak | Allocated memory that is never freed |
| Plateau | Growth that stops at a stable level (cache, heap max) |
| Heap dump | Snapshot of a managed runtime's objects (Java, Node, Python tools) |
| Fragmentation | Free memory inside the process that the allocator cannot return to the OS |

**See it on a real system**

```bash
# RSS of one process every minute (kB) — leave it running for an hour
while true; do echo "$(date +%T) $(ps -o rss= -p PID)"; sleep 60; done
pidstat -r -p PID 60                    # RSS plus minor/major faults per interval

# a container's anonymous memory over time
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' CONTAINER).scope
while true; do echo "$(date +%T) $(awk '/^anon /{print int($2/1048576)" MiB"}' $CG/memory.stat)"; sleep 60; done
```

In Prometheus (§11), the growth rate over hours is the giveaway:
`deriv(container_memory_working_set_bytes{name="app-web-1"}[1h])` stays positive, and
`predict_linear(container_memory_working_set_bytes{name="app-web-1"}[6h], 24*3600)` gives
the value expected 24 hours from now: compare it with the limit to see whether the next
OOM kill falls within a day.

```
10:00:00 401220
11:00:00 452104
12:00:00 503338
13:00:00 549870
```

→ About 50 MB per hour, steadily, with flat traffic: a leak. With a 1 GB limit you have
roughly ten hours between OOM kills, which matches "it crashes every night".

**Hands-on lab (test VM only)**

**Step 1 — Build a leaking process:**

```bash
tee /var/tmp/leak.py >/dev/null <<'EOF'
import time
leak = []
while True:
    leak.append(b"x" * 1024 * 1024)   # 1 MiB per second, never freed
    time.sleep(1)
EOF
python3 /var/tmp/leak.py &
LEAK=$!
```

**Step 2 — Observe:** `pidstat -r -p $LEAK 10` for a few minutes; RSS grows ~1 MiB/s in a
straight line. Stop it with `kill $LEAK`.

**Step 3 — Break it under a limit:** run the same script in a scope with a hard limit and
watch it get OOM-killed after about five minutes; then find the kernel log line.

```bash
sudo systemd-run --scope -p MemoryMax=300M -p MemorySwapMax=0 python3 /var/tmp/leak.py
journalctl -k --since '10 min ago' --no-pager | grep -i 'killed process'
```

**Step 4 — Fix:** remove `/var/tmp/leak.py`. For real applications the mitigation is a
scheduled restart or a memory limit with automatic restart (`Restart=on-failure`,
`restart: unless-stopped`), and the real fix is a heap profile handed to the developers.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| App OOM-killed at regular intervals | Kernel log + RSS trend | [Slow system playbook](23-playbook-slow-system.md) |
| JVM: `java.lang.OutOfMemoryError: Java heap space` | GC logs, heap dump | §8 GC |
| Node.js: `JavaScript heap out of memory` | `--max-old-space-size`, heap snapshot | §8 GC |
| Memory grows only after a deploy | Compare versions; roll back first | [CI/CD & SRE learn module](33-learn-cicd-iac-sre.md) |

**Why it matters for troubleshooting.** Raising a memory limit for a leaking app only
moves the crash to later. Proving a leak with a time series is what gets it fixed.

**Next step.** The third resource: storage.

---

## 6. Disk deep dive

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage → *Monitor Storage Performance* ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)) · 2) Note: [Storage & disk reference](01-storage-disk.md) · 3) Video: *Linux Performance Tools, Brendan Gregg, LinuxCon Europe 2014* ([YouTube](https://www.youtube.com/watch?v=SN7Z0eCn0VY)) · 4) Practice: a fio baseline of every lab disk and the etcd fsync check on your CKA homelab nodes.

Storage is the slowest component in most servers and the one whose numbers are easiest to
misread: a "fast" disk at 200 MB/s can be hopeless for a database doing 4 KB random reads,
and `%util` 100% on an NVMe drive may mean nothing. Command reference:
[Storage & disk](01-storage-disk.md).

### IOPS, throughput and latency

**Level:** [L2 · Mid] · the three storage numbers

**Concept.** Three different numbers describe storage performance, and a workload cares
about one of them most:

- **IOPS**: I/O operations per second. Matters for small random I/O (databases, mail spools, package installs, Docker layer extraction).
- **Throughput**: bytes per second. Matters for large sequential I/O (backups, video, log shipping, image pulls). Throughput = IOPS × I/O size.
- **Latency**: time per I/O, including time in queues. Matters for anything synchronous: every `fsync` of a database commit or of etcd waits for it.

The same disk gives very different numbers per workload: a SATA SSD might do 90,000 IOPS
of 4 KB random reads (≈ 350 MB/s) and 530 MB/s sequential, while a 7,200 rpm HDD does
~150 random IOPS (0.6 MB/s!) but ~200 MB/s sequential.

**Key terms**

| Term | Meaning |
|------|---------|
| IOPS | Completed I/O operations per second (`r/s + w/s`) |
| Throughput | `rkB/s + wkB/s` |
| I/O size | Bytes per request (`rareq-sz`, `wareq-sz` in KB) |
| Latency / await | Average ms per request including queueing (`r_await`, `w_await`) |
| Service time | Time the device itself spends; no longer reported by iostat (svctm was removed) |
| Random vs sequential | Scattered offsets vs consecutive offsets |
| Sync write | Write that must be on stable storage before returning (`fsync`, `O_DSYNC`) |

**See it on a real system**

```bash
iostat -xz 1 5                          # per device, extended, skip idle
iostat -xz -p sda 1 5                   # include partitions of sda
cat /proc/diskstats | grep -w sda       # raw counters the tools read
sar -d -p 1 5                           # same view, plus history (sar -d -f FILE)
```

Read each device line as: *how many* (r/s, w/s), *how big* (rareq-sz, wareq-sz), *how
much* (rkB/s, wkB/s), *how long* (r_await, w_await), *how queued* (aqu-sz), *how busy*
(%util).

```
Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dkB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
nvme0n1       8211.00  32844.00     0.00   0.00    0.21     4.00  1520.00  12160.00    12.00   0.78    0.05     8.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    1.80  46.10
sdb            142.00    568.00     0.00   0.00   26.80     4.00    11.00    176.00     2.00  15.38   41.22    16.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    4.26  99.20
```

→ The NVMe serves 9,700 small IOPS at 0.2 ms with a queue under 2: relaxed. The HDD
`sdb` does only 153 IOPS of 4 KB (0.7 MB/s!) at 27–41 ms and is 99% busy: that is
the physical limit of a spinning disk for random I/O. Moving that workload to SSD is the
fix; no tuning will make an HDD do 1,000 random IOPS.

**Hands-on lab (test VM only)**

**Step 1 — Same disk, two workloads.** With fio (last topic of this area explains the
flags) run a sequential and a random test on a test file and compare MB/s and IOPS:

```bash
cd /var/tmp
fio --name=seq  --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=read     --bs=1M --ioengine=libaio --iodepth=8  --runtime=30 --time_based --group_reporting
fio --name=rand --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randread --bs=4k --ioengine=libaio --iodepth=32 --runtime=30 --time_based --group_reporting
```

**Step 2 — Watch iostat during each run** in a second terminal: `iostat -xz 1`. Match
`rareq-sz` (1024 vs 4), `r/s`, `rkB/s` and `r_await` to fio's report.

**Step 3 — Break it:** run both at the same time and watch the random test's latency rise
(the sequential reader fills the queue).

**Step 4 — Fix:** clean up: `rm /var/tmp/fio.test`.

**How it breaks**

| Symptom | Likely cause | First command |
|---------|--------------|---------------|
| "Disk does 200 MB/s but DB is slow" | DB needs IOPS and latency, not MB/s | `iostat -xz 1` (r/s, r_await) |
| `w_await` high, `wareq-sz` tiny, many `f/s` | Sync writes/fsync storm | `strace -c -f -p PID` |
| Throughput hits a flat ceiling | Device, controller, network storage or cloud volume limit | §6 storage types |

**Why it matters for troubleshooting.** "The disk is fast, I tested it with dd" is the
storage equivalent of "ping works". Always test with the workload's I/O size, pattern and
sync behaviour.

**Next step.** Learn the column that most directly measures disk saturation: queue depth.

### Queue depth and reading iostat

**Level:** [L2 · Mid] · disk saturation without the %util trap

**Concept.** Requests wait in queues on their way to the device: in the block layer
(scheduler), in the driver, in the device itself. **Queue depth** is how many requests are
outstanding at once. iostat's `aqu-sz` is the average number in flight, which by Little's
law equals IOPS × average latency. A deeper queue lets fast parallel devices (SSD, NVMe,
RAID, SAN) reach their peak IOPS; on an HDD it mostly adds waiting time. `%util` is "the
share of time at least one request was in flight": for a single HDD 100% means saturated,
for an NVMe or a RAID array that serves many requests in parallel, 100% only means "never
idle" and the device may still have plenty of capacity.

**Key terms**

| Column | Meaning | Worry when |
|--------|---------|------------|
| `aqu-sz` | Average requests in flight | Sustained > 1 on HDD; much higher than usual on SSD |
| `r_await` / `w_await` | Average ms per request, queue included | HDD > 20 ms, SATA SSD > 2–5 ms, NVMe > 1 ms, sustained |
| `%util` | Time with ≥ 1 request in flight | ~100% on HDD; on NVMe/RAID check await and aqu-sz instead |
| `rrqm/s` / `wrqm/s` | Requests merged before dispatch | Informational (sequential I/O merges well) |
| `f/s`, `f_await` | Flush (cache flush) requests and their latency | Many flushes = fsync-heavy workload |
| `nr_requests` | Block-layer queue size per device | — |

**See it on a real system**

```bash
iostat -xz 1 5
lsblk -d -o NAME,ROTA,SCHED,RQ-SIZE,MODEL           # rotational? scheduler? queue size?
cat /sys/block/sda/queue/nr_requests
sudo biolatency-bpfcc -D 10 1                        # latency histogram per disk, 10 s
```

```
     disk = 'sda'
     usecs               : count     distribution
       128 -> 255        : 210      |**                                      |
       256 -> 511        : 1802     |********************                    |
       512 -> 1023       : 3550     |****************************************|
      1024 -> 2047       : 912      |**********                              |
      2048 -> 4095       : 103      |*                                       |
      4096 -> 8191       : 41       |                                        |
      8192 -> 16383      : 188      |**                                      |
     16384 -> 32767      : 77       |                                        |
```

→ Bimodal: most I/O completes in 0.25–2 ms (SSD-class), but a second hump at 8–32 ms
suggests a subset of requests waits on something slower (a write cache flush, a busy
neighbour on shared storage, a RAID rebuild). The average `await` would hide this; the
histogram shows it.

**Hands-on lab (test VM only)**

**Step 1 — Queue depth vs latency:** run the same random-read fio test at iodepth 1, 4, 16
and 64 and record IOPS and average latency for each:

```bash
for qd in 1 4 16 64; do
  fio --name=qd$qd --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randread --bs=4k \
      --ioengine=libaio --iodepth=$qd --runtime=20 --time_based --group_reporting \
      | grep -E '^ *read:|^ *lat \([num]sec\): min' | sed "s/^/qd=$qd /"   # fio picks nsec/usec/msec by size
done
```

**Step 2 — Check Little's law** for each row: iodepth ≈ IOPS × latency (s).

**Step 3 — Break it:** past some depth, IOPS stops rising and only latency grows: you have
found the device's saturation point (its knee). **Fix:** note the depth where it happens;
that is the useful concurrency for this disk. Clean up the test file.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| `%util` 100% on NVMe, app fine | Ignore `%util`, check await/aqu-sz | — |
| `aqu-sz` and await grow, IOPS flat | Device saturated | [Slow system playbook](23-playbook-slow-system.md) |
| Periodic latency spikes every few seconds | Writeback bursts, RAID/BBU learn cycle, neighbours on SAN | `biolatency-bpfcc`, `grep Dirty /proc/meminfo`, controller logs |

**Why it matters for troubleshooting.** Saturation of a disk is visible as queue and
latency, not as `%util`. Reading those correctly prevents both false alarms (NVMe at 100%)
and missed problems (HDD at 70% with 40 ms latency).

**Next step.** What kind of I/O the workload sends, and how the kernel orders it.

### Access patterns and I/O schedulers

**Level:** [L3 · Senior] · workload characterization for storage

**Concept.** Workloads differ in **read/write mix**, **I/O size**, **randomness** and
**sync behaviour**: a PostgreSQL OLTP database does small random reads plus small
synchronous WAL writes; a backup does large sequential reads; Docker image extraction does
many small file creates; etcd does tiny `fdatasync` writes and cares only about their
latency. The **I/O scheduler** reorders and merges requests before they reach the device.
Modern Linux uses multi-queue schedulers: `none` (no reordering; default for NVMe), 
`mq-deadline` (default for SATA/SAS; bounds latency), `bfq` (fairness, mostly desktops) and
`kyber`. On fast SSD/NVMe, `none` or `mq-deadline` is right; on HDDs `mq-deadline`.

**Key terms**

| Term | Meaning |
|------|---------|
| Read/write mix | e.g. 70% read / 30% write |
| Random / sequential | Scattered vs consecutive offsets |
| Direct I/O | Bypasses the page cache (`O_DIRECT`) |
| Buffered I/O | Goes through the page cache (most apps) |
| `fsync` / `fdatasync` | Force data to stable storage; latency of these = commit latency |
| Scheduler | Block-layer request ordering policy (`none`, `mq-deadline`, `bfq`, `kyber`) |

**See it on a real system**

```bash
cat /sys/block/sda/queue/scheduler          # brackets mark the active scheduler
cat /sys/block/nvme0n1/queue/scheduler
lsblk -d -o NAME,ROTA,SCHED,MODEL
pidstat -d 1 5                              # who reads/writes how much
sudo biosnoop-bpfcc | head -30              # each I/O: process, R/W, sector, size, latency
```

```
$ cat /sys/block/sda/queue/scheduler
[mq-deadline] none
$ cat /sys/block/nvme0n1/queue/scheduler
[none] mq-deadline

NAME    ROTA SCHED       MODEL
sda        1 mq-deadline ST4000NM0035-1V4107
nvme0n1    0 none        Samsung SSD 980 PRO 1TB
vda        1 none
```

→ Defaults are sensible. Note `vda`: virtio disks in VMs often report `ROTA=1` even when
the host stores them on SSD; do not draw conclusions from that flag inside a VM.

**Hands-on lab (test VM only)**

**Step 1 — Characterise a workload:** while `stress-ng --hdd 2 --temp-path /var/tmp --timeout 60s`
runs, use `pidstat -d 1` and `iostat -xz 1` to write down: read/write mix, average size,
and whether it is sync (`f/s`).

**Step 2 — Compare schedulers on a test disk** (an extra virtual disk, not the root disk):
switch the scheduler and repeat a fio random-read test.

```bash
cat /sys/block/vdb/queue/scheduler
echo none        | sudo tee /sys/block/vdb/queue/scheduler
echo mq-deadline | sudo tee /sys/block/vdb/queue/scheduler
```

**Step 3 — Break it:** run a sequential writer and a latency-sensitive random reader
together under each scheduler and compare the reader's p99 latency in fio's
`clat percentiles` section. **Fix:** set the scheduler back to its original value (the
change does not survive a reboot unless a udev rule sets it).

**How it breaks**

| Symptom | Likely cause | First command |
|---------|--------------|---------------|
| etcd: `apply request took too long`, `slow fdatasync` | Disk fsync latency too high for etcd | fio fsync test (end of this area) |
| DB slow during backups | Sequential backup starves random reads | `pidstat -d 1`, schedule backups, `ionice -c3` |
| Docker pulls/extraction slow | Many small files on slow disk/overlay | `iostat -xz 1` during pull |

**Why it matters for troubleshooting.** "What kind of I/O is this?" decides whether you
need more IOPS, more throughput, lower fsync latency or just a different schedule. It is
the workload characterization step of drill-down analysis.

**Next step.** Know what each storage type can deliver, so you recognise a hardware
ceiling when you hit one.

### HDD, SSD, NVMe and network storage

**Level:** [L2 · Mid] → [L3 · Senior] · recognising a hardware ceiling

**Concept.** Each storage technology has an order-of-magnitude performance envelope.
Knowing these numbers lets you tell "broken" from "working as designed". Treat the table
as rough guidance; measure your own hardware with fio.

| Type | 4 KB random read IOPS | Typical latency | Sequential | Notes |
|------|----------------------|-----------------|------------|-------|
| 7,200 rpm HDD | ~75–200 | 5–15 ms | 150–250 MB/s | Seek-bound; RAID multiplies IOPS by data disks |
| SATA SSD | ~50k–100k | ~0.1–0.5 ms | ~500–550 MB/s | Interface-bound at ~600 MB/s |
| NVMe SSD | ~200k–1M+ | ~0.02–0.1 ms | 2–7 GB/s | Many parallel queues; `%util` meaningless |
| NFS / SMB | Depends on server | + network RTT (0.2–2 ms LAN) | ≤ NIC (1 GbE ≈ 110 MB/s) | Hard mounts hang processes in D state when the server dies |
| iSCSI / SAN / Ceph RBD | Depends on array/cluster | + network and replication | ≤ NIC/fabric | Shared: neighbours affect you |
| AWS EBS gp3 | 3,000 baseline (provisionable) | sub-ms to ~1 ms | 125 MiB/s baseline (provisionable) | Also capped by the instance's EBS bandwidth |
| AWS EBS gp2 / st1 | Burst credits | — | — | Performance drops sharply when credits run out |

**Key terms**

| Term | Meaning |
|------|---------|
| Seek time | HDD head movement; dominates random I/O latency |
| Write cache / BBU | Controller cache that acknowledges writes early; needs battery or flash backup to be safe |
| Write amplification | SSD writes more internally than you asked (garbage collection) |
| TRIM / discard | Tells the SSD which blocks are free (`fstrim.timer` on Ubuntu) |
| Burst credits | Cloud volumes that run faster until a credit balance is exhausted |

**See it on a real system**

```bash
lsblk -d -o NAME,SIZE,ROTA,TRAN,MODEL           # TRAN: sata, nvme, iscsi, usb
sudo smartctl -i /dev/sda | grep -E 'Model|Rotation Rate|SATA Version'
sudo nvme list
findmnt -t nfs,nfs4,cifs                         # network filesystems in use
nfsstat -c                                       # NFS client stats (retrans = network trouble)
systemctl list-timers fstrim.timer --no-pager
```

```
NAME      SIZE ROTA TRAN   MODEL
sda       3.6T    1 sata   ST4000NM0035-1V4107
nvme0n1 931.5G    0 nvme   Samsung SSD 980 PRO 1TB
sdc       500G    1 iscsi  LIO-ORG lun0
```

→ `sdc` is an iSCSI LUN: its latency includes the network and the remote array. Monitor
it like a network dependency, not a local disk.

**Hands-on lab (test VM only)**

**Step 1 — Measure your lab disks** with the fio latency test from the last topic of this
area (iodepth 1) and fill your own row in the table.

**Step 2 — Break it: simulate a slow network disk.** On a test VM with an NFS export from
a second VM, add 50 ms of delay on the client's interface toward the NFS server (see §7
for safe `tc netem` usage with an automatic revert) and repeat the test.

**Step 3 — Fix:** remove the delay and compare: latency per I/O tracks the network RTT
almost one to one.

**How it breaks**

| Symptom | Likely cause | First command |
|---------|--------------|---------------|
| Processes stuck in D, `df` hangs | Dead NFS server, hard mount | `findmnt -t nfs,nfs4`, `ps` D state |
| EBS volume fast, then slow after an hour | gp2/st1 burst credits exhausted, or instance EBS limit | CloudWatch `BurstBalance`, [AWS reference](16-aws-cloud.md) |
| SSD writes slow down over time | No TRIM, drive nearly full, worn out | `fstrim -av` (test VM), `smartctl -a` |
| RAID array slow for hours | Rebuild or patrol read | `cat /proc/mdstat`, controller tool |

**Why it matters for troubleshooting.** Half of storage tickets are not faults: they are a
workload asking a technology for more than it can do. Recognising the envelope makes the
conversation with the client ("this needs SSD", "this volume needs provisioned IOPS")
short and factual.

**Next step.** Benchmark storage properly and safely with fio.

### Benchmarking safely with fio

**Level:** [L3 · Senior] · baselines without destroying data

**Concept.** fio is the standard storage benchmark: you describe a workload (pattern,
size, depth, sync behaviour, duration) and it reports IOPS, bandwidth and a full latency
distribution. Used carelessly it destroys data: pointing a **write** test at a block
device (`/dev/sdb`) overwrites whatever is on it, including partition tables. The safe
habit is to always benchmark a **test file** inside a mounted filesystem, on a test
machine, with a size and a time limit.

> ⚠️ Never run fio with `--filename=/dev/sdX` (or any block device) and a write pattern
> unless the device is empty and you intend to wipe it. Never benchmark a disk shared with
> a production database during business hours. Safer: a test file such as
> `/var/tmp/fio.test`, `--size` a few GB, `--runtime` 30–60 s, then delete the file.

**Key terms**

| Flag | Meaning |
|------|---------|
| `--filename=/var/tmp/fio.test` | Test file (created and laid out by fio) |
| `--size=1G` | Size of the test file / region |
| `--rw=` | `read`, `write`, `randread`, `randwrite`, `randrw` (with `--rwmixread=70`) |
| `--bs=4k` | I/O size |
| `--direct=1` | Bypass the page cache (otherwise you benchmark RAM) |
| `--ioengine=libaio` | Asynchronous engine on Linux (or `io_uring` on newer kernels) |
| `--iodepth=32` | Requests in flight per job |
| `--numjobs=4` + `--group_reporting` | Parallel jobs, reported as one |
| `--runtime=60 --time_based` | Run for 60 s regardless of size |
| `--fdatasync=1` | Call fdatasync after every write (commit latency test) |

**See it on a real system**

```bash
cd /var/tmp
# 1. random read IOPS (database-like reads)
fio --name=randread --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randread --bs=4k \
    --ioengine=libaio --iodepth=32 --runtime=60 --time_based --group_reporting
# 2. random write IOPS
fio --name=randwrite --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randwrite --bs=4k \
    --ioengine=libaio --iodepth=32 --runtime=60 --time_based --group_reporting
# 3. mixed 70/30 OLTP-like
fio --name=mixed --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randrw --rwmixread=70 --bs=8k \
    --ioengine=libaio --iodepth=16 --numjobs=4 --runtime=60 --time_based --group_reporting
# 4. sequential throughput (backups, image pulls)
fio --name=seqread --filename=/var/tmp/fio.test --size=2G --direct=1 --rw=read --bs=1M \
    --ioengine=libaio --iodepth=8 --runtime=60 --time_based --group_reporting
# 5. pure device latency (one request at a time)
fio --name=lat --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randread --bs=4k \
    --ioengine=libaio --iodepth=1 --runtime=30 --time_based
# 6. etcd / Kubernetes control-plane disk check: fdatasync latency of small writes
mkdir -p /var/tmp/etcd-fio && fio --rw=write --ioengine=sync --fdatasync=1 \
    --directory=/var/tmp/etcd-fio --size=22m --bs=2300 --name=etcd-check
# clean up
rm -rf /var/tmp/fio.test /var/tmp/etcd-fio
```

```
randread: (g=0): rw=randread, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=libaio, iodepth=32
fio-3.36
Starting 1 process
randread: Laying out IO file (1 file / 1024MiB)
Jobs: 1 (f=1): [r(1)][100.0%][r=176MiB/s][r=45.1k IOPS][eta 00m:00s]
randread: (groupid=0, jobs=1): err= 0: pid=4242: Sat Oct  3 10:12:41 2026
  read: IOPS=45.2k, BW=177MiB/s (185MB/s)(10.3GiB/60001msec)
    slat (usec): min=2, max=312, avg= 4.11, stdev= 1.90
    clat (usec): min=88, max=9120, avg=702.35, stdev=210.44
     lat (usec): min=92, max=9125, avg=706.61, stdev=210.51
    clat percentiles (usec):
     |  1.00th=[  396],  5.00th=[  469], 10.00th=[  506], 20.00th=[  562],
     | 30.00th=[  603], 40.00th=[  644], 50.00th=[  685], 60.00th=[  725],
     | 70.00th=[  775], 80.00th=[  832], 90.00th=[  930], 95.00th=[ 1020],
     | 99.00th=[ 1336], 99.50th=[ 1532], 99.90th=[ 2474], 99.95th=[ 3195],
     | 99.99th=[ 5866]
   iops        : min=42830, max=46128, avg=45228.10, stdev=552.54, samples=119
  cpu          : usr=9.81%, sys=31.22%, ctx=1102934, majf=0, minf=42
  IO depths    : 1=0.1%, 2=0.1%, 4=0.1%, 8=0.1%, 16=0.1%, 32=100.0%, >=64=0.0%

Run status group 0 (all jobs):
   READ: bw=177MiB/s (185MB/s), 177MiB/s-177MiB/s (185MB/s-185MB/s), io=10.3GiB (11.1GB), run=60001-60001msec

Disk stats (read/write):
  vda: ios=2710234/48, sectors=21681872/760, merge=0/31, ticks=1893340/41, in_queue=1893402, util=99.92%
```

→ 45.2k IOPS × 4 KiB = 177 MiB/s (consistent). Little's law: 32 in flight ÷ 45,200/s ≈
0.71 ms = the average completion latency (`clat avg` 702 µs). Median 685 µs, p99 1.3 ms,
p99.99 5.9 ms: a tight distribution, typical for SSD-backed virtual disks. `util=99.92%`
here just means the queue was never empty.

For the etcd check, read the `fsync/fdatasync/sync_file_range` → `sync percentiles`
section: the etcd project recommends the 99th percentile of fdatasync below about 10 ms.
Above that, a Kubernetes control plane on this disk will log slow-apply warnings and leader
elections become unstable.

**Hands-on lab (test VM only)**

**Step 1 — Build a baseline file** for your lab VM: run tests 1, 2, 4, 5 and 6 and record
IOPS, MB/s, p50 and p99 into `/var/tmp/storage-baseline.txt` with the date.

**Step 2 — Break it: forget `--direct=1`.** Run test 1 again without it and with
`--size=512M` on a VM with 4 GB RAM; the "disk" suddenly does hundreds of thousands of
IOPS because you benchmarked the page cache.

**Step 3 — Break it differently: throttle the disk** with a cgroup limit and re-run test 1
inside it:

```bash
sudo systemd-run --scope -p "IOReadIOPSMax=/var/tmp 500" \
  fio --name=thr --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randread --bs=4k \
      --ioengine=libaio --iodepth=32 --runtime=20 --time_based
```

→ IOPS pinned at ~500 and latency ≈ 32 / 500 = 64 ms: Little's law again, and the same
signature as a cloud volume capped at its provisioned IOPS.

**Step 4 — Fix:** remove all test files. Keep the baseline file: next time someone says
"the disk is slow", you have numbers to compare against.

**How it breaks**

| Mistake / symptom | Consequence | Fix |
|-------------------|-------------|-----|
| `--filename=/dev/sdb` with a write test | Data on sdb destroyed | Always a test file; `lsblk` before anything |
| No `--direct=1` | You measured RAM | Add `--direct=1`, size ≫ RAM for buffered tests |
| Test on a nearly full filesystem | `No space left on device` mid-test, apps fail | `df -h` first; small `--size` |
| Results vary wildly between runs | Shared storage, burst credits, thermal throttling | Repeat 3×, longer runtime, check neighbours |

**Why it matters for troubleshooting.** A baseline turns "slow" into "40% below the
baseline we measured in March". The etcd check is also a CKA homelab essential: many
"flaky control plane" problems are disk latency.

**Next step.** The fourth resource: the network.

---

## 7. Network deep dive

> 📚 **Study path:** 1) Note: [Network reference](02-network.md) and the TCP parts of the [networking learn module](28-learn-networking.md) (refresher) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → Troubleshooting ([lesson notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)), and *Networks and Communications* — Network Troubleshooting if TCP/IP still feels shaky ([course](https://kodekloud.com/courses/networks-and-communications)) · 3) Read: the network section of [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) (no KodeKloud course covers BDP, retransmits or iperf3) · 4) Practice: the §7 labs with two VMs, then the [network speed playbook](24-playbook-network-speed.md).

"The network is slow" usually means one of three things: the link is genuinely full,
packets are being lost and retransmitted, or one TCP connection cannot fill a long fat
pipe because its window is too small. This area teaches you to tell them apart. Command
reference: [Network](02-network.md); incident playbook: [Network speed](24-playbook-network-speed.md).

### Bandwidth-delay product and TCP buffers

**Level:** [L3 · Senior] · slow single streams on long paths

**Concept.** TCP may only have a limited amount of unacknowledged data "in the air" per
connection: the **window**, bounded by the receiver's buffer (receive window) and the
sender's congestion window. One connection can therefore never go faster than
`window ÷ RTT`. To fill a link, the window must be at least the **bandwidth-delay product**
(BDP): bandwidth × round-trip time.

```
 BDP = bandwidth × RTT

 1 Gbit/s LAN,  RTT 0.5 ms :  125 MB/s × 0.0005 s =  62.5 KB   (any default works)
 1 Gbit/s WAN,  RTT 40 ms  :  125 MB/s × 0.040  s =  5 MB
 10 Gbit/s WAN, RTT 40 ms  : 1250 MB/s × 0.040  s = 50 MB      (needs tuning)

 max single-stream throughput ≈ window / RTT
 e.g. window 6 MB, RTT 80 ms  →  6 MB / 0.08 s = 75 MB/s ≈ 600 Mbit/s, even on a 10 Gbit/s link
```

Linux auto-tunes TCP buffers per connection between the min/default/max values in
`net.ipv4.tcp_rmem` and `tcp_wmem`. Ubuntu's defaults (max 6 MB receive, 4 MB send) are
plenty for a LAN and for 1 Gbit/s over moderate RTT, but not for 10 Gbit/s across
continents. `net.core.rmem_max`/`wmem_max` only cap buffers that applications request
explicitly with `setsockopt`; they do not limit auto-tuning.

**Key terms**

| Term | Meaning |
|------|---------|
| RTT | Round-trip time (ping, `ss -ti` `rtt:`) |
| BDP | Bandwidth × RTT: data needed in flight to fill the pipe |
| Receive window (rwnd) | How much the receiver can accept, from its buffer |
| Congestion window (cwnd) | How much the sender dares to send, from the congestion algorithm |
| Window scaling | TCP option allowing windows > 64 KB (on by default) |
| MSS | Maximum segment size (MTU minus headers, typically 1448 bytes of data) |

**See it on a real system**

```bash
ping -c 5 HOST                                   # RTT
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.core.rmem_max net.core.wmem_max net.ipv4.tcp_window_scaling
ss -tin dst 192.0.2.20                           # per-connection: rtt, cwnd, send rate, limits
```

```
net.ipv4.tcp_rmem = 4096	131072	6291456
net.ipv4.tcp_wmem = 4096	16384	4194304
net.core.rmem_max = 212992
net.core.wmem_max = 212992
net.ipv4.tcp_window_scaling = 1

State  Recv-Q  Send-Q    Local Address:Port     Peer Address:Port
ESTAB  0       2457600   192.0.2.10:50412       192.0.2.20:5201
	 cubic wscale:7,7 rto:248 rtt:47.9/0.8 ato:40 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:742 ssthresh:520 bytes_sent:1180291744 bytes_retrans:2896 bytes_acked:1177834001 send 179Mbps pacing_rate 215Mbps delivery_rate 172Mbps busy:9180ms rwnd_limited:4120ms(44.9%) retrans:0/2 notsent:1009024 minrtt:47.1
```

→ RTT 48 ms, `send 179Mbps` (= cwnd 742 × 1448 bytes × 8 ÷ 0.0479 s). The key field is
`rwnd_limited:4120ms(44.9%)`: for 45% of its busy time the sender was waiting for the
**receiver's** window. The receiver's buffer, not the network, is the bottleneck; raising
the receiver's `tcp_rmem` max (or using parallel streams) helps. `sndbuf_limited` would
point at the sender's buffer, and neither field plus retransmits points at the network.

**Hands-on lab (test VM only)**

**Step 1 — Baseline between two lab VMs** on the same LAN: `iperf3 -s` on VM B,
`iperf3 -c VM_B -t 20` on VM A. Expect ~940 Mbit/s on 1 GbE.

**Step 2 — Break it: add WAN latency** on VM A's interface with `tc netem`, with an
automatic revert so you cannot lock yourself out:

```bash
IFACE=ens18
sudo systemd-run --on-active=10min /usr/sbin/tc qdisc del dev $IFACE root   # dead-man switch
sudo tc qdisc add dev $IFACE root netem delay 80ms
ping -c 3 VM_B                                   # RTT now ~80 ms
iperf3 -c VM_B -t 30                             # single stream
ss -tin dst VM_B                                 # look at rtt, cwnd, rwnd_limited
# "Error: Specified qdisc kind is unknown." → netem module missing; on Ubuntu cloud/minimal
# kernels it may live in linux-modules-extra-$(uname -r) (check: modinfo sch_netem)
```

**Step 3 — Shrink the receive buffer on VM B** (test VM only) and repeat: throughput
drops to roughly `window ÷ RTT`.

```bash
sudo sysctl -w net.ipv4.tcp_rmem='4096 131072 1048576'   # on VM B: 1 MB max
```

**Step 4 — Fix:** restore VM B's value (`sudo sysctl -w net.ipv4.tcp_rmem='4096 131072 6291456'`)
and remove the delay on VM A (`sudo tc qdisc del dev $IFACE root`). Calculate the BDP for
80 ms at 1 Gbit/s and compare with what you measured.

**How it breaks**

| Symptom | Likely cause | First command |
|---------|--------------|---------------|
| Single transfer to remote site stuck at ~100–200 Mbit/s, link idle | Window/BDP limit | `ss -tin` (`rwnd_limited`), BDP calculation |
| `iperf3 -P 8` much faster than `-P 1` | Per-connection limit, not link capacity | Tune buffers or parallelise |
| Fast inside the LAN, slow over VPN | Higher RTT + lower MTU through the tunnel | `ping`, `tracepath -n HOST` |

**Why it matters for troubleshooting.** Backups, registry pulls from Harbor across sites
and database replication are long-lived single streams. When they are slow while the link
graph is flat, BDP is the first suspect.

**Next step.** The other big cause of slow TCP: loss, retransmits and congestion control.

### Retransmits, drops and congestion control

**Level:** [L2 · Mid] → [L3 · Senior] · loss, cables and congestion

**Concept.** TCP treats packet loss as a congestion signal: when segments are lost it
retransmits them and shrinks its congestion window, so even 1% loss can cut throughput
of a long-RTT connection by an order of magnitude. Loss happens at many places: a full
switch buffer, a duplex mismatch or bad cable (CRC errors), a NIC ring buffer overflow
on a busy host, a full conntrack table, a policer at the provider. **Congestion control**
is the algorithm that decides how fast to send: Linux defaults to **CUBIC**; **BBR** models
bandwidth and RTT instead of reacting to loss and often does much better on lossy,
long-RTT paths.

**Key terms**

| Term | Meaning |
|------|---------|
| Retransmit | A segment sent again because it was (or seemed) lost |
| RTO | Retransmission timeout (`rto:` in `ss -ti`), minimum 200 ms on Linux |
| Duplex mismatch | One side full, other half duplex: late collisions, CRC errors, terrible throughput |
| Ring buffer | NIC receive queue; overflows show as `rx_missed`/`rx_no_buffer` in `ethtool -S` |
| qdisc | Queueing discipline on egress (`fq_codel` default on Ubuntu, `fq` for BBR) |
| CUBIC / BBR | Loss-based vs model-based congestion control |

**See it on a real system**

```bash
nstat -az TcpRetransSegs TcpOutSegs TcpExtTCPLostRetransmit TcpExtListenOverflows TcpExtListenDrops
nstat -n; sleep 10; nstat TcpRetransSegs TcpOutSegs   # deltas over the last 10 s
sar -n ETCP 1 5                                       # retrans/s
ip -s link show IFACE                                 # RX/TX errors, dropped, overrun
ethtool IFACE | grep -E 'Speed|Duplex|Auto-negotiation'
sudo ethtool -S IFACE | grep -iE 'drop|err|miss|crc|no_buf' | grep -v ': 0$'
cat /proc/net/softnet_stat                            # col 2 = dropped, col 3 = time_squeeze (hex, per CPU)
tc -s qdisc show dev IFACE
sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_available_congestion_control net.core.default_qdisc
sudo tcpretrans-bpfcc                                 # live: each retransmit with addresses and state
```

```
#kernel
TcpOutSegs                      48211933           0.0
TcpRetransSegs                  12933              0.0

$ ethtool eno1 | grep -E 'Speed|Duplex|Auto-negotiation'
	Speed: 100Mb/s
	Duplex: Half
	Auto-negotiation: on

$ ip -s link show eno1
2: eno1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    RX:    bytes   packets errors dropped  missed   mcast
    9182231442 12001233   4821       0       0    1201
    TX:    bytes   packets errors dropped carrier collsns
    7712093321 10233122      0       0     310    8812
```

→ Retransmit ratio 12,933 / 48.2M ≈ 0.03%: healthy (worry above ~0.5–1%). But this
server's NIC negotiated **100 Mb/s half duplex** with thousands of RX errors, carrier
errors and collisions: a bad cable, a bad switch port or forced speed on one side. This is
one of the most common on-prem "network is slow" root causes and no amount of TCP tuning
helps. Fix the physical layer, then re-run iperf3.

**Hands-on lab (test VM only)**

**Step 1 — Baseline** `iperf3 -c VM_B -t 20` and `nstat -az TcpRetransSegs`.

**Step 2 — Break it: add 1% loss and 40 ms delay** on VM A, with the dead-man switch from
the previous topic, and repeat with CUBIC:

```bash
sudo systemd-run --on-active=10min /usr/sbin/tc qdisc del dev $IFACE root
sudo tc qdisc add dev $IFACE root netem delay 40ms loss 1%
iperf3 -c VM_B -t 30                              # note the Retr column and bitrate
```

**Step 3 — Compare with BBR** (test VM only; both sides can stay CUBIC for receiving):

```bash
sudo modprobe tcp_bbr
iperf3 -c VM_B -t 30 -C bbr                       # -C picks the algorithm for this test only
```

→ With 1% loss and 40 ms RTT, CUBIC typically collapses to a fraction of the link, while
BBR keeps much more of it. Note the numbers.

**Step 4 — Fix:** `sudo tc qdisc del dev $IFACE root`. Only make BBR permanent
(`/etc/sysctl.d/` with `net.core.default_qdisc=fq` and `net.ipv4.tcp_congestion_control=bbr`)
after testing it on real paths.

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| `retrans/s` > 0 sustained, slow transfers | `ss -ti`, `tcpretrans-bpfcc`, `mtr -rwn -c 100 HOST` | [Network speed playbook](24-playbook-network-speed.md) |
| `Speed: 100Mb/s` on a gigabit port, CRC errors | Cable, port, autonegotiation | `ethtool IFACE`, switch port counters |
| `nf_conntrack: table full, dropping packet` | Conntrack exhausted (busy proxy/NAT host) | `conntrack -C`, `sysctl net.netfilter.nf_conntrack_max` |
| `TcpExtListenOverflows` rising | App accept queue full (app too slow to accept) | `ss -lnt` (Recv-Q vs Send-Q on listeners) |
| softnet_stat column 2 rising | Kernel dropping packets before the stack (CPU too slow per packet) | `mpstat -P ALL 1` (`%soft`), RSS/queues |

**Why it matters for troubleshooting.** Retransmits are the network's saturation and error
signal in USE terms. Reading them at the host tells you whether to look at cables and
switches, the remote side, or your own kernel.

**Next step.** Measure what the path can actually deliver, and keep the number: iperf3
baselines.

### iperf3 baselines

**Level:** [L2 · Mid] · make "the network is slow" testable

**Concept.** iperf3 measures achievable throughput between two hosts with synthetic
traffic, removing disks and applications from the equation. A **baseline** is a recorded
result for each important path (server ↔ server, site ↔ site, host ↔ NAS, node ↔ Harbor)
taken when everything is healthy. During an incident you rerun the same command and
compare; without a baseline "is 600 Mbit/s slow?" has no answer. iperf3 uses TCP port 5201
by default; on a UFW-protected server allow it temporarily from the client only.

> ⚠️ iperf3 can fill a link for everyone. On shared or production networks, agree a time
> window, use `-t 10`, and limit rate with `-b` if needed. Remove the temporary firewall
> rule afterwards.

**Key terms**

| Flag | Meaning |
|------|---------|
| `-s` | Server mode (listens on 5201) |
| `-c HOST` | Client: send to HOST |
| `-R` | Reverse: server sends to client (test the other direction) |
| `-P 4` | 4 parallel streams |
| `-u -b 500M` | UDP at 500 Mbit/s: shows loss and jitter |
| `-t 30 -i 5` | 30 s test, report every 5 s |
| `--json`, `--logfile FILE` | Machine-readable / saved output for baselines |
| `Retr` | TCP retransmits during the interval |

**See it on a real system**

```bash
# on the server (VM B)
sudo ufw allow from 192.0.2.10 to any port 5201 proto tcp comment 'iperf3 test - remove after'
iperf3 -s --one-off                     # exits after one test

# on the client (VM A)
iperf3 -c 192.0.2.20 -t 30 -i 5 --logfile /var/tmp/iperf-$(date +%F)-A-to-B.txt
iperf3 -c 192.0.2.20 -t 30 -R           # B → A
iperf3 -c 192.0.2.20 -t 30 -P 4         # parallel streams
iperf3 -c 192.0.2.20 -u -b 900M -t 10   # UDP: loss % and jitter

# afterwards on the server
sudo ufw status numbered                # then: sudo ufw delete NUMBER
```

```
Connecting to host 192.0.2.20, port 5201
[  5] local 192.0.2.10 port 50412 connected to 192.0.2.20 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-5.00   sec   561 MBytes   941 Mbits/sec    0    417 KBytes
[  5]   5.00-10.00  sec   561 MBytes   941 Mbits/sec    0    417 KBytes
...
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-30.00  sec  3.29 GBytes   941 Mbits/sec    0             sender
[  5]   0.00-30.00  sec  3.28 GBytes   939 Mbits/sec                  receiver
```

→ 941 Mbit/s with zero retransmits is the practical maximum of 1 GbE for TCP (headers
take the rest). If the application path is much slower than this, the network is not the
bottleneck: look at disks, the app or the proxy. If iperf3 itself is slow, continue with
the [network speed playbook](24-playbook-network-speed.md).

**Hands-on lab (test VM only)**

**Step 1 — Record baselines** for A→B, B→A, `-P 4` and UDP at 900M into
`/var/tmp/baselines/` with dates.

**Step 2 — Break it in three different ways**, one at a time, and identify each from the
iperf3 output alone: (a) `tc netem delay 50ms`, (b) `tc netem loss 2%`, (c) limit the
interface with `sudo ethtool -s IFACE speed 100 duplex full autoneg off` (only on a lab VM
with a console, since it can drop your SSH session; virtio NICs may ignore it).

**Step 3 — Fix** each one (`tc qdisc del dev IFACE root`, `sudo ethtool -s IFACE autoneg on`)
and confirm you are back at baseline.

**How it breaks**

| iperf3 output | Meaning | Next step |
|---------------|---------|-----------|
| `unable to connect to server` … `Connection refused` (newer iperf3, e.g. 3.16 on Ubuntu 24.04, adds a hint about port and firewall between the two) | No server running, or wrong port | `ss -ltnp 'sport = :5201'` on the server |
| `Connection timed out` | Firewall drops 5201 | UFW/nftables rule, security group |
| ~94 Mbit/s exactly | 100 Mb/s link somewhere on the path | `ethtool`, switch ports |
| Low bitrate, high `Retr` | Loss on the path | `mtr`, NIC errors, [24](24-playbook-network-speed.md) |
| `-R` much slower than forward | Asymmetric problem (one direction's buffer, policer, duplex) | Test each direction, check both NICs |
| `-P 4` ≫ `-P 1` | Per-stream (BDP/window) limit | Previous topic |

**Why it matters for troubleshooting.** A baseline makes "the network is slow" testable in
one minute, and it is what you show the network team or the provider as evidence.

**Next step.** With all four resources covered, move up the stack to the application.

---

## 8. Application performance

> 📚 **Study path:** 1) KodeKloud: *Nginx For Beginners* — Performance → *Monitoring & Troubleshooting* ([lesson notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Performance/Monitoring-Troubleshooting/page)) · 2) Note: this area, the pool and timeout parts of [webservers & proxies](29-learn-webservers-proxies.md), and [databases ops](38-learn-databases-ops.md) for slow queries · 3) Read: [Deploying Gunicorn](https://gunicorn.org/deploy/) (workers and timeouts) · 4) Practice: the §8 PHP-FPM pool lab, then the 502/504 cases in the [site down playbook](25-playbook-site-down.md).

Once the host's resources look healthy and the service is still slow, the cause is
usually inside the application or its dependencies: hot code, an exhausted pool, garbage
collection pauses, or a slow query. You will not fix the code yourself, but you must be
able to prove which of these it is.

### Profiling basics

**Level:** [L3 · Senior] · on-CPU vs off-CPU time

**Concept.** A profiler tells you where a program spends its time. **On-CPU** profiling
(sampling stacks while the program runs, like perf) finds hot code. **Off-CPU** analysis
finds where it *waits*: locks, disk, network, sleeping in a pool queue. Most web
applications spend most of their latency off-CPU, waiting on the database or another
service, so a CPU profile of a slow-but-idle app shows nothing useful. Start with timing
breakdowns from logs (proxy time vs app time vs DB time), then profile the part that is
slow.

```
 request latency 900 ms
 ├── Traefik overhead           2 ms   (Traefik access log: Overhead)
 ├── app on-CPU                40 ms   (perf / py-spy / async-profiler)
 └── app waiting (off-CPU)    858 ms
     ├── DB query             810 ms   (slow query log, pg_stat_statements)
     └── HTTP call to API      48 ms   (app logs, tracing §14)
```

**Key terms**

| Term | Meaning |
|------|---------|
| On-CPU profile | Where CPU time goes (perf, py-spy, pprof, async-profiler) |
| Off-CPU profile | Where blocked time goes (`offcputime-bpfcc`, tracing, thread dumps) |
| Thread dump | Snapshot of all threads' stacks (`jstack`, `py-spy dump`) |
| Wall-clock time | Real elapsed time, on- plus off-CPU |
| Upstream time | Time the backend took, as seen by the proxy |

**See it on a real system**

```bash
# timing breakdown from the proxy's point of view
#   Nginx:   log_format with $request_time $upstream_connect_time $upstream_response_time
#   Traefik: JSON access log fields Duration, OriginDuration, Overhead (nanoseconds)
# requests whose backend took over 1 s, counted per path and status
jq -r 'select(.OriginDuration > 1e9) | [.RequestPath, .OriginStatus] | @tsv' access.log | sort | uniq -c | sort -rn | head

# Python app: live top-like view and a flame graph (pip install py-spy; needs sudo for other users' PIDs)
sudo py-spy top --pid PID
sudo py-spy dump --pid PID              # where is each thread right now?
sudo py-spy record -o /var/tmp/profile.svg --pid PID --duration 30

# JVM: thread dump and quick GC view
sudo -u APPUSER jstack PID > /var/tmp/threads.txt
# any process: where does it block? (eBPF, 10 s)
sudo offcputime-bpfcc -p PID -f 10 > /var/tmp/offcpu.folded
```

```
$ sudo py-spy dump --pid 8812
Thread 8812 (idle): "MainThread"
    wait (threading.py:331)
    get (queue.py:180)
    _get_conn (urllib3/connectionpool.py:289)
    urlopen (urllib3/connectionpool.py:715)
    send (requests/adapters.py:486)
```

→ The main thread is waiting to *get a connection* from urllib3's pool: all pooled
connections to a dependency are busy. (urllib3 only waits here when the pool was created
with blocking enabled, e.g. `HTTPAdapter(pool_block=True)`; with the default it opens
extra connections instead and the wait moves to the dependency.) The fix is in the pool
size or the dependency's latency, not in CPU.

**Hands-on lab (test VM only)**

**Step 1 — Build a slow app** with one CPU-bound and one waiting endpoint:

```bash
tee /var/tmp/slowapp.py >/dev/null <<'EOF'
import hashlib, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/cpu":
            for _ in range(20000): hashlib.sha256(b"x" * 1024).digest()
        elif self.path == "/wait":
            time.sleep(0.5)                       # pretend: slow database
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n")
ThreadingHTTPServer(("127.0.0.1", 8001), H).serve_forever()
EOF
python3 /var/tmp/slowapp.py &
APP=$!
```

**Step 2 — Load each endpoint and profile:**

```bash
wrk -t2 -c8 -d20s http://127.0.0.1:8001/cpu &  sudo py-spy top --pid $APP
wrk -t2 -c8 -d20s http://127.0.0.1:8001/wait & sudo py-spy dump --pid $APP
```

→ `/cpu` shows hashlib at the top of py-spy; `/wait` shows threads sitting in `sleep`, with
almost no CPU in `pidstat`. Same latency complaint, opposite causes.

**Step 3 — Fix:** `kill $APP; rm /var/tmp/slowapp.py`. Write which tool proved each case.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| Slow, CPU high in app process | `perf top -p PID`, language profiler | §4 perf |
| Slow, CPU idle | Thread dump, upstream timings, DB slow log | Next topics |
| Proxy shows high Overhead, app fast | Proxy saturated or TLS cost | [Webservers & proxies learn module](29-learn-webservers-proxies.md) |

**Why it matters for troubleshooting.** It stops the "add more CPU" reflex for a problem
that is waiting, not computing, and gives developers a stack trace instead of an opinion.

**Next step.** The most common "waiting" cause: exhausted pools.

### Worker, thread and connection pools

**Level:** [L2 · Mid] → [L3 · Senior] · the most common "waiting" cause

**Concept.** Servers handle concurrency with fixed-size pools: Apache workers
(`MaxRequestWorkers`), PHP-FPM children (`pm.max_children`), Gunicorn workers, Java/Node
thread pools, database connection pools, and the database's own `max_connections`. A pool
of N slots with an average hold time W can serve at most N / W requests per second
(Little's law). When a dependency slows down, W grows, the pool fills, new requests queue
in front of it, and latency explodes even though no resource looks busy. Pools that are
too large just move the queue to the next layer (a database with 500 connections
thrashing).

```
 requests ──▶ [ queue ] ──▶ Apache workers (150) ──▶ PHP-FPM children (5!) ──▶ DB pool (20) ──▶ PostgreSQL (max 100)
                                                         ▲
                     the smallest pool relative to its hold time is the bottleneck
```

**Key terms**

| Pool | Setting | Ubuntu default | Full-pool message |
|------|---------|----------------|-------------------|
| Apache event/prefork MPM | `MaxRequestWorkers` | 150 | `AH00484: server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting` |
| PHP-FPM | `pm.max_children` | 5 (`pm = dynamic`) | `WARNING: [pool www] server reached pm.max_children setting (5), consider raising it` |
| Gunicorn | `--workers`, `--threads` | 1 worker | `[CRITICAL] WORKER TIMEOUT` when one is stuck > `--timeout` (30 s) |
| PostgreSQL | `max_connections` | 100 | `FATAL:  sorry, too many clients already` |
| MySQL/MariaDB | `max_connections` | 151 | `ERROR 1040 (HY000): Too many connections` |
| App DB pool | e.g. HikariCP, SQLAlchemy | varies | `Connection is not available, request timed out`, `QueuePool limit ... reached` |

**See it on a real system**

```bash
# Apache: busy vs idle workers and the scoreboard
curl -s 'http://127.0.0.1/server-status?auto' | grep -E 'BusyWorkers|IdleWorkers|Scoreboard'
grep -rE 'MaxRequestWorkers|ThreadsPerChild|ServerLimit' /etc/apache2/mods-enabled/mpm_*.conf
grep AH00484 /var/log/apache2/error.log | tail -3

# PHP-FPM
grep -E '^pm(\.|\s)' /etc/php/*/fpm/pool.d/www.conf
grep max_children /var/log/php*-fpm.log | tail -3

# PostgreSQL: connections by state
sudo -u postgres psql -c "select state, count(*) from pg_stat_activity group by state order by 2 desc;"
# MySQL
sudo mysql -e "show status like 'Threads_connected'; show variables like 'max_connections';"
```

```
BusyWorkers: 150
IdleWorkers: 0
Scoreboard: WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW...

[03-Oct-2026 10:41:12] WARNING: [pool www] server reached pm.max_children setting (5), consider raising it
```

→ All 150 Apache workers are busy sending replies (`W`) but they are all waiting on only
5 PHP-FPM children. PHP-FPM's tiny default pool is the bottleneck, and raising Apache's
limit would make it worse. Size `pm.max_children` from memory: (RAM you can give PHP) ÷
(average PSS of one child), then check the DB can take that many connections.

**Hands-on lab (test VM only)**

**Step 1 — Build:** install Apache with PHP-FPM on the test VM and a PHP page that sleeps
for 1 second (simulating a slow query):

```bash
sudo apt install -y apache2 php-fpm
sudo a2enmod proxy_fcgi setenvif && sudo a2enconf "$(basename /etc/apache2/conf-available/php*-fpm.conf .conf)"
echo '<?php usleep(1000000); echo "ok\n";' | sudo tee /var/www/html/slow.php
sudo systemctl reload apache2
```

**Step 2 — Break it:** send 20 concurrent requests with the default `pm.max_children = 5`:

```bash
wrk -t2 -c20 -d20s --latency http://127.0.0.1/slow.php
```

→ Throughput ≈ 5 req/s (5 children ÷ 1 s), latency ≈ 4 s (20 in flight ÷ 5 req/s), and the
`max_children` warning in the FPM log. Little's law predicted both numbers.

**Step 3 — Fix:** set `pm.max_children = 20` in the pool file, reload with
`sudo systemctl reload 'php*-fpm.service'` (quoted, so systemctl expands the pattern),
repeat the test: ≈ 20 req/s at ≈ 1 s latency. Then clean up the test page.

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| AH00484 / `max_children` warnings, CPU low | Pool status pages, dependency latency | [Slow system playbook](23-playbook-slow-system.md) |
| 502 after exactly 30 s (Gunicorn) | `docker logs CONTAINER` and grep for `WORKER TIMEOUT` | [Site down playbook](25-playbook-site-down.md) |
| `too many clients already` | `pg_stat_activity` by state and app | Next topics |
| Pool raised, DB now melts | You moved the queue | Fix the slow dependency; add a pooler (PgBouncer) |

**Why it matters for troubleshooting.** When you move the client's Apache vhosts into
containers behind Traefik, every hop gets its own pool and timeouts. Knowing where the
pools are and how to read their status is how you find the 502s and 504s that only appear
under load.

**Next step.** Pauses that come from the runtime itself: garbage collection.

### Garbage collection and runtimes

**Level:** [L3 · Senior] · runtimes inside container limits

**Concept.** Java, Go, Node.js, .NET and Python free memory automatically. The garbage
collector (GC) costs CPU and, depending on the algorithm, can pause the application. When
a heap is too small for the live data, the GC runs constantly, spends most of the CPU
reclaiming almost nothing, and latency explodes long before an out-of-memory error
appears. Runtimes must also know their **container limits**: modern JVMs (10+, 8u191+)
size the heap from the cgroup memory limit (`-XX:MaxRAMPercentage`, default 25%), Node.js
sizes its old space from available memory unless `--max-old-space-size` is set, and Go
uses `GOMEMLIMIT` for memory and, on older releases, ignores CPU limits for `GOMAXPROCS`.

**Key terms**

| Term | Meaning |
|------|---------|
| Heap | Memory managed by the GC |
| Young / old generation | Short-lived vs long-lived objects (JVM) |
| Stop-the-world pause | All application threads paused for GC |
| GC thrashing | Continuous GC with little memory reclaimed |
| `MaxRAMPercentage` | JVM heap as % of container limit |
| `--max-old-space-size` | Node.js old-generation heap size in MB |
| `GOMEMLIMIT` / `GOGC` | Go soft memory limit / GC aggressiveness |

**See it on a real system**

```bash
# JVM: GC utilisation every second (S0 S1 Eden Old Metaspace ... YGC FGC GCT)
sudo -u APPUSER jstat -gcutil PID 1000 5
# JVM: enable GC logging (startup flag)            -Xlog:gc*:file=/var/log/app/gc.log:time,uptime
# JVM: what heap did it pick inside the container?
docker exec CONTAINER java -XX:+PrintFlagsFinal -version | grep -E 'MaxHeapSize|MaxRAMPercentage'
# Node.js: heap limit in effect
docker exec CONTAINER node -e 'console.log(v8.getHeapStatistics().heap_size_limit/1048576 + " MB")'
```

```
  S0     S1     E      O      M     CCS    YGC     YGCT     FGC    FGCT     CGC    CGCT       GCT
  0.00 100.00  63.21  97.85  95.12  90.33   1520   21.334    37   88.120     12    0.410  109.864
  0.00 100.00  81.02  98.90  95.12  90.33   1521   21.351    38   88.920     12    0.410  110.681
```

→ Old generation (`O`) is 98% full and the full-GC count went from 37 to 38 in one second,
adding 0.8 s of full-GC time (plus 17 ms of young GC) within that one-second sample: the
JVM spends most of its time collecting. Either the heap
is too small for the live data or the app leaks. A heap dump decides which.

**Hands-on lab (test VM only)**

**Step 1 — Build:** run a Node.js container with a tiny heap and a leaking script:

```bash
docker run --rm --name gclab --memory=256m node:22-alpine \
  node --max-old-space-size=64 -e 'const a=[]; setInterval(()=>{a.push("x".repeat(1e6)+a.length); console.log(a.length+" MB")},100)'
```

**Step 2 — Break it:** watch the output slow down as the heap fills (GC runs more and
more), then end with a `FATAL ERROR: ... JavaScript heap out of memory` line and exit.

**Step 3 — Fix:** run it again with `--max-old-space-size=200`: it lasts longer but still
dies, because a leak is a leak. Write down the difference between "heap too small" (raise
it) and "leak" (no size is enough).

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| `java.lang.OutOfMemoryError: Java heap space` | `jstat -gcutil`, GC log, heap dump | §5 leaks |
| `java.lang.OutOfMemoryError: GC overhead limit exceeded` | Same: GC thrashing | — |
| `FATAL ERROR: Reached heap limit ... JavaScript heap out of memory` | `--max-old-space-size` vs container limit | [Containers playbook](26-playbook-containers-k8s.md) |
| Container OOM-killed although heap max < limit | Off-heap memory (threads, metaspace, buffers) | `memory.stat` anon, native memory tracking |
| Periodic latency spikes every N seconds | GC pauses | GC log, pause times |

**Why it matters for troubleshooting.** A container limit and a runtime's heap setting
must agree. Many "random" OOM kills after a containerisation (exactly your Apache →
Dokploy move) come from a runtime that assumed it owned the whole host.

**Next step.** The last and most common application cause: slow queries.

### Slow queries

**Level:** [L2 · Mid] → [L3 · Senior] · where web latency usually lives

**Concept.** In most web applications, the database is where latency lives: a missing
index turns a 2 ms lookup into a 2 s table scan; lock contention makes queries wait for
each other; an N+1 pattern issues 500 small queries per page. Databases can log every
query slower than a threshold and keep aggregated statistics, which turns "the DB is slow"
into "this one query, called 40,000 times per hour, takes 180 ms because of a sequential
scan".

**Key terms**

| Term | Meaning |
|------|---------|
| Slow query log | Log of queries above a duration threshold |
| `log_min_duration_statement` | PostgreSQL threshold in ms (`-1` = off) |
| `slow_query_log`, `long_query_time` | MySQL/MariaDB switch and threshold in seconds |
| `pg_stat_statements` | PostgreSQL extension with per-query totals, calls, mean time |
| `EXPLAIN ANALYZE` | Run a query and show the real execution plan and timings |
| Sequential scan / full table scan | Reading the whole table: fine for small tables, fatal for big ones |
| Lock wait | Query blocked by another transaction |
| N+1 | One query for a list plus one per item |

**See it on a real system**

```bash
# PostgreSQL: currently running queries, longest first, with what they wait for
sudo -u postgres psql -x -c "select pid, now()-query_start as runtime, state, wait_event_type, wait_event, left(query,80) as query from pg_stat_activity where state <> 'idle' order by runtime desc limit 5;"
# top statements by total time (needs pg_stat_statements; column names for PostgreSQL 13+)
sudo -u postgres psql -c "select calls, round(mean_exec_time::numeric,1) as mean_ms, round(total_exec_time::numeric) as total_ms, left(query,70) from pg_stat_statements order by total_exec_time desc limit 5;"
# log queries slower than 500 ms (postgresql.conf, then reload)
#   log_min_duration_statement = 500

# MySQL / MariaDB
sudo mysql -e "SET GLOBAL slow_query_log = ON; SET GLOBAL long_query_time = 0.5; SHOW VARIABLES LIKE 'slow_query_log_file';"
sudo mysqldumpslow -s t -t 5 /var/lib/mysql/HOST-slow.log    # top 5 by total time
sudo mysql -e "SHOW FULL PROCESSLIST;"
```

```
 calls  | mean_ms | total_ms | left
--------+---------+----------+------------------------------------------------------------------------
  41823 |   182.4 |  7628517 | SELECT * FROM orders WHERE customer_email = $1 ORDER BY created_at DES
   9120 |    12.1 |   110352 | UPDATE sessions SET last_seen = $1 WHERE id = $2
```

→ One query accounts for 7,600 s of DB time: 41,823 calls at 182 ms each. An
`EXPLAIN ANALYZE` will almost certainly show a sequential scan on `orders` because
`customer_email` has no index. That is a finding to hand to the developers or DBA with
evidence attached.

**Hands-on lab (test VM only)**

**Step 1 — Build:** run PostgreSQL in Docker and create a table with a million rows:

```bash
docker run -d --name pglab -e POSTGRES_PASSWORD=labonly -p 127.0.0.1:5432:5432 postgres:16
sleep 5
docker exec -i pglab psql -U postgres <<'EOF'
CREATE TABLE orders (id serial primary key, customer_email text, created_at timestamptz default now());
INSERT INTO orders (customer_email) SELECT 'user' || (random()*100000)::int || '@example.com' FROM generate_series(1,1000000);
ANALYZE orders;
EOF
```

**Step 2 — Break it:** time a lookup without an index and read the plan:

```bash
docker exec -i pglab psql -U postgres -c "EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_email = 'user42@example.com';"
```

→ `Seq Scan on orders` (or `Parallel Seq Scan`) and an execution time in the tens of
milliseconds or more.

**Step 3 — Fix:** add the index and repeat:

```bash
docker exec -i pglab psql -U postgres -c "CREATE INDEX ON orders (customer_email);"
docker exec -i pglab psql -U postgres -c "EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_email = 'user42@example.com';"
docker rm -f pglab
```

→ `Index Scan` (or `Bitmap Index Scan`) and well under a millisecond.

**How it breaks**

| Symptom | First command | Go to |
|---------|---------------|-------|
| DB CPU high, app slow | `pg_stat_statements` / `mysqldumpslow` | This topic |
| DB CPU low, queries slow | Lock waits: `wait_event_type = Lock` in `pg_stat_activity` | DBA |
| Disk saturated on DB host | `iostat -xz 1` + slow log | §6 disk |
| Slow only after a deploy | New query or missing migration index | [CI/CD & SRE learn module](33-learn-cicd-iac-sre.md) |

**Why it matters for troubleshooting.** "The server is slow" tickets for web apps end here
more often than anywhere else. Being able to show the exact query and its plan earns you
credibility with developers fast.

**Next step.** Before changing anything for performance, learn to measure capacity safely
with benchmarks and load tests.

---

## 9. Benchmarking and load testing safely

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil (capacity planning) and Release Engineering (production readiness) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Note: this area and the baseline steps of the [slow system playbook](23-playbook-slow-system.md) · 3) Read: [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) (active benchmarking) · 4) Practice: write a one-page test plan, then run wrk and k6 against your own lab Dokploy app only.

Benchmarks answer "how much can this handle?" and "did my change help?". Done badly they
measure the wrong thing, or take down something shared. Done well they give you the
numbers for capacity planning (§16) and for the before/after of a migration.

### Rules of safe benchmarking

**Level:** [L3 · Senior] · measure without causing an incident

**Concept.** A benchmark is an experiment, and experiments need a hypothesis, a controlled
environment and repeatable measurements. Brendan Gregg's **active benchmarking** rule:
while the benchmark runs, observe the system with the tools from §2–§7 to confirm the
bottleneck is what you think. A disk benchmark that is actually limited by the CPU of the
load generator tells you nothing about the disk.

The rules:

1. **Get written approval** before generating load against anything shared: production, staging used by others, the company network, a provider's API, a client's server. Rate limits, intrusion detection, autoscaling bills and angry colleagues are all real outcomes.
2. **Use a test environment** that resembles production (same instance type, same storage class, same proxy chain).
3. **Know what you are measuring**: write the hypothesis ("Traefik + app sustain 300 req/s at p95 under 300 ms").
4. **Observe while testing** (active benchmarking): 60-second checklist on the target *and* on the load generator.
5. **Warm up**, then **repeat at least three times**; report the median and the spread.
6. **Change one variable at a time.**
7. **Record the environment**: versions, kernel, instance type, config, date.
8. **Make sure the load generator is not the bottleneck** (separate machine, enough cores, check its CPU).
9. **Beware caches**: page cache (`--direct=1`), CDN or reverse-proxy caches, DB buffer cache warm vs cold.
10. **Clean up**: test files, temporary firewall rules, test users, containers.

**Key terms**

| Term | Meaning |
|------|---------|
| Micro-benchmark | Tests one component (disk, CPU) in isolation |
| Macro / load test | Tests the whole service through its real entry point |
| Closed model | Fixed number of users/connections; each waits for its response before the next request (wrk, hey) |
| Open model | Requests arrive at a fixed rate regardless of responses (k6 arrival-rate executors), like real traffic |
| Coordinated omission | Closed-model testers stop sending while the server stalls, hiding the stall from percentiles |
| Soak test | Long test at moderate load to find leaks and slow degradation |
| Stress test | Load beyond expected peak to find the breaking point |

**See it on a real system**

```bash
# before any test: snapshot the target and record the environment
uname -r; lsb_release -ds; nproc; free -m; lsblk -d -o NAME,ROTA,SIZE,MODEL
docker version --format '{{.Server.Version}}' 2>/dev/null
# during the test: watch both machines
sudo sixty-seconds 5                    # the §2 script, on target and on load generator
```

**Hands-on lab (test VM only)**

**Step 1 — Write a test plan** (one page): hypothesis, target, tool, load profile,
duration, success criteria, who approved, how to stop, clean-up steps. Reuse it for every
test in this area.

**Step 2 — Break it: make the load generator the bottleneck.** Run `wrk -t1 -c200` from a
1-vCPU VM against a fast target and watch the generator's CPU hit 100% while the target is
half idle. The "result" is the generator's limit.

**Step 3 — Fix:** more threads (`-t` = cores of the generator), a bigger generator, or
several generators. Confirm the target is now the one saturating.

**How it breaks**

| Mistake | Consequence |
|---------|-------------|
| Load test against production without approval | Outage, security incident, lost trust |
| Testing through a CDN or cache | You measured the cache |
| One run only | Noise reported as a result |
| No observation during the test | Wrong bottleneck blamed |

**Why it matters for troubleshooting.** Before the Apache → Dokploy migration, a load test
of the old and the new stack with the same plan gives you the before/after numbers that
prove the migration did not make things worse.

**Next step.** The tools for system micro-benchmarks: stress-ng and sysbench.

### stress-ng and sysbench

**Level:** [L2 · Mid] → [L3 · Senior] · load generators and comparable numbers

**Concept.** **stress-ng** puts a configurable load on a subsystem (CPU, memory, I/O,
scheduler, network stack and hundreds more "stressors"). It is a *load generator*, ideal
for practising diagnosis and for testing alerts, cgroup limits and stability.
**sysbench** is a *benchmark* that reports comparable numbers (events per second,
latency percentiles) for CPU, memory, file I/O and MySQL/PostgreSQL OLTP workloads.

**Key terms**

| Command | What it loads / measures |
|---------|--------------------------|
| `stress-ng --cpu N --cpu-load P` | N CPU workers at P% each |
| `stress-ng --vm N --vm-bytes B --vm-keep` | N workers allocating and touching B of memory |
| `stress-ng --hdd N --hdd-opts dsync --temp-path DIR` | N workers writing files in DIR (synchronously with dsync) |
| `stress-ng --iomix N` | Mixed I/O patterns |
| `stress-ng --switch N` | Context-switch storm |
| `stress-ng --sock N` | Loopback TCP socket traffic |
| `--timeout 60s`, `--metrics-brief` | Always set a timeout; print bogo-ops summary |
| `sysbench cpu run` | Prime-number CPU benchmark |
| `sysbench memory run` | Memory bandwidth |
| `sysbench fileio prepare/run/cleanup` | File I/O benchmark with its own test files |

**See it on a real system**

```bash
stress-ng --cpu 4 --timeout 60s --metrics-brief
sysbench cpu --threads=4 --time=30 run
sysbench memory --threads=2 --memory-total-size=10G run
cd /var/tmp && sysbench fileio --file-total-size=2G prepare \
  && sysbench fileio --file-total-size=2G --file-test-mode=rndrw --time=60 run \
  ; sysbench fileio --file-total-size=2G cleanup
```

```
CPU speed:
    events per second:  4321.07

General statistics:
    total time:                          30.0004s
    total number of events:              129638

Latency (ms):
         min:                                    0.90
         avg:                                    0.93
         max:                                   14.21
         95th percentile:                        0.97
         sum:                               119884.12

Threads fairness:
    events (avg/stddev):           32409.5000/41.22
    execution time (avg/stddev):   29.9710/0.01
```

→ 4,321 events/s on 4 threads; the max of 14 ms against a p95 of 0.97 ms means one thread
was briefly descheduled (another process, or steal). Compare `events per second` between
VMs or instance types to see whether "the new server is slower".

**Hands-on lab (test VM only)**

**Step 1 — Compare two VMs** (or the same VM before and after changing vCPU count) with
`sysbench cpu --threads=$(nproc) --time=30 run`, three runs each.

**Step 2 — Break it:** run the sysbench CPU test while `stress-ng --cpu $(nproc)` is
running; events per second roughly halve and max latency jumps.

**Step 3 — Fix:** stop stress-ng. Keep the numbers as your VM's CPU baseline.

**How it breaks**

| Mistake | Consequence | Safer alternative |
|---------|-------------|-------------------|
| `stress-ng --vm` without `--timeout` on a box without swap | OOM kills of real services | Always `--timeout`, test VM, leave headroom |
| `sysbench fileio prepare` and forgetting `cleanup` | GBs of `test_file.*` left in the directory | Run in `/var/tmp`, always `cleanup` |
| Comparing bogo-ops across stress-ng versions | Meaningless numbers | Use sysbench or fio for comparisons |

**Why it matters for troubleshooting.** stress-ng is how you rehearse incidents (§18) and
test that alerts fire; sysbench is how you answer "is this VM as fast as the old one?".

**Next step.** Load test whole HTTP services: wrk, hey and k6.

### HTTP load testing with wrk, hey and k6

**Level:** [L3 · Senior] · capacity numbers for whole services

**Concept.** HTTP load tools send many requests to a URL and report throughput and the
latency distribution. **wrk** is a fast C tool with a closed model (fixed connections);
**hey** is a simple Go binary, also closed-model, with a latency histogram; **k6** is
scriptable in JavaScript, supports an **open model** (fixed arrival rate), thresholds
(pass/fail in CI) and staged ramps. Use wrk/hey for quick capacity checks and k6 for
repeatable tests in CI and for realistic SLO validation.

**Key terms**

| Term | Meaning |
|------|---------|
| `-c` / connections | Concurrent connections (closed model) |
| `-t` (wrk) | Load-generator threads (≈ cores of the generator) |
| `-d` / `-z` | Duration |
| VU (k6) | Virtual user |
| Arrival rate (k6) | Requests started per time unit, independent of responses |
| Threshold (k6) | Pass/fail rule, e.g. p95 under 300 ms |

**See it on a real system**

```bash
# wrk: 4 threads, 100 connections, 30 s, print latency percentiles
wrk -t4 -c100 -d30s --latency https://staging.example.com/health
# hey: 50 concurrent workers for 30 s
hey -z 30s -c 50 https://staging.example.com/health
# k6: scripted, open-model, with thresholds (script below)
k6 run /var/tmp/k6-health.js
```

```
Running 30s test @ https://staging.example.com/health
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    24.31ms   12.07ms 312.55ms   88.41%
    Req/Sec     1.04k   118.20     1.40k    71.25%
  Latency Distribution
     50%   21.87ms
     75%   27.03ms
     90%   36.41ms
     99%   71.92ms
  124112 requests in 30.03s, 98.41MB read
Requests/sec:   4133.04
Transfer/sec:      3.28MB
```

→ 4,133 req/s at p99 72 ms with 100 connections. Little's law check: 100 ÷ 4,133 ≈
24 ms = the average latency. If you see `Non-2xx or 3xx responses: N` or `Socket errors`
lines, part of your "throughput" was errors: always read them.

A k6 script with an open model and SLO-style thresholds:

```javascript
// /var/tmp/k6-health.js — run only against a test/staging target you are allowed to load
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: 50,              // 50 requests started per second, whatever the latency
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 20,
      maxVUs: 200,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],                   // under 1% errors
    http_req_duration: ['p(95)<300', 'p(99)<800'],    // ms
  },
};

export default function () {
  const res = http.get('https://staging.example.com/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
}
```

k6 exits non-zero when a threshold fails, so the same script can gate a GitLab CI job
(see [CI/CD & SRE learn module](33-learn-cicd-iac-sre.md)).

**Hands-on lab (test VM only)**

**Step 1 — Build:** deploy any small app behind Traefik on your lab Dokploy (or the §8
slowapp on loopback). Run wrk with `-c 10`, `-c 50`, `-c 200` and plot req/s and p99 for
each: you will see throughput flatten and p99 shoot up past the knee.

**Step 2 — Break it:** limit the app container to `--cpus=0.25` (or set a CPU limit in
Dokploy's advanced settings) and rerun: the knee arrives at a fraction of the load, and
cgroup `nr_throttled` climbs (§4).

**Step 3 — Compare models:** run the k6 script at a rate just above the knee. Unlike wrk,
k6 keeps sending at the fixed rate, so the queue and p99 grow without bound and
`http_req_failed` rises: this is what real users experience.

**Step 4 — Fix:** remove the limit, rerun, and write the capacity number ("this app on
this VM: ~X req/s at p95 under 300 ms").

**How it breaks**

| Output / symptom | Meaning | Next step |
|------------------|---------|-----------|
| `Socket errors: connect N, read N, timeout N` | Server refusing/timeouts, or generator out of ports/fds | Server logs; `ulimit -n` on generator |
| `Non-2xx or 3xx responses` | Errors counted as throughput | Read the error codes |
| 429 responses | Rate limiting (Traefik middleware, Cloudflare, WAF) | Agree limits or test behind them |
| Great results, tiny latency | You hit a cache or a 404 page | Check status codes and response size |

**Why it matters for troubleshooting.** A measured capacity number turns "will the new
server cope?" into a fact, and gives you the threshold for alerts and the input for
capacity planning.

**Next step.** From one-off measurements to continuous observability: the pillars.

---

## 10. Observability pillars and cardinality

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Observability Fundamentals ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) KodeKloud: *Fundamentals of SRE* — Observability and Monitoring ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Note: [Logs & journal reference](06-logs-journal.md) · 4) Practice: the §10 lab (one stopped unit, three pillars) on the §17 stack.

Everything so far was interactive: you log in and look. Observability is what lets you
answer questions about a system **without** logging in, including questions about the
past ("what happened at 03:00?") and about things you did not anticipate. This area
explains the kinds of telemetry and the single most common way to break a metrics system.

### Metrics, logs, traces and events

**Level:** [L4 · Lead/SRE] · the right pillar for each question

**Concept.** Four kinds of telemetry, each good at different questions:

| Pillar | What it is | Good for | Cost / limits | Tools |
|--------|------------|----------|---------------|-------|
| **Metrics** | Numbers sampled over time, with labels | Trends, alerts, dashboards, capacity; "how much / how often / how fast" | Cheap per data point; no per-request detail | Prometheus, node_exporter, CloudWatch |
| **Logs** | Timestamped text or structured records of discrete events | "What exactly happened to this request / this unit?" | Expensive at volume; need parsing | journald, Loki, ELK, CloudWatch Logs |
| **Traces** | The path of one request across services, as timed spans | "Which hop of this request was slow?" in distributed systems | Needs instrumentation; usually sampled | OpenTelemetry, Jaeger, Tempo |
| **Events** | Records of changes: deploys, config changes, restarts, scaling, Kubernetes events | Correlating "it broke" with "what changed" | Often forgotten | Grafana annotations, `kubectl get events`, CI logs |

Continuous **profiling** (always-on low-rate CPU/memory profiles, e.g. Grafana Pyroscope)
is sometimes counted as a fifth pillar. In practice: **metrics tell you that** something is
wrong, **traces tell you where**, **logs tell you why**, and **events tell you what
changed**.

```
 alert fires (metric: p99 > 1 s) ──▶ dashboard: which service/instance? (metrics)
        └──▶ trace of a slow request: DB span 900 ms (trace)
               └──▶ DB slow log / app log for that trace ID: lock wait on orders (logs)
                      └──▶ annotation: migration deployed 14:02 (event)
```

**Key terms**

| Term | Meaning |
|------|---------|
| Telemetry | Data a system emits about itself |
| Time series | One metric name + one set of label values, sampled over time |
| Label | Key/value dimension on a metric (`instance`, `job`, `code`) |
| Structured log | Log record with fields (JSON, logfmt) instead of free text |
| Span | One timed operation in a trace, with a parent |
| Exemplar | A sample trace ID attached to a metric data point |
| Monitoring vs observability | Watching known failure modes vs being able to ask new questions |

**See it on a real system**

```bash
# metrics: what a node_exporter exposes (one HTTP GET)
curl -s http://127.0.0.1:9100/metrics | grep -E '^node_load|^node_memory_MemAvailable'
# logs: structured fields journald already stores
journalctl -u ssh -n 1 -o json-pretty --no-pager | grep -E '"(MESSAGE|_PID|_SYSTEMD_UNIT|PRIORITY)"'
# events: what changed recently (systemd, packages, Kubernetes)
journalctl --since '2 hours ago' -u 'apt-daily*' --no-pager | tail -5
grep -E ' (install|upgrade) ' /var/log/dpkg.log | tail -5
kubectl get events -A --sort-by=.lastTimestamp | tail -10
```

```
node_load1 0.42
node_load15 0.31
node_load5 0.38
node_memory_MemAvailable_bytes 5.664620544e+09
```

→ Plain text, one series per line; Prometheus scrapes this every `scrape_interval` (15 s in
this module's configs; Prometheus's built-in default is 1 m) and stores it.

**Hands-on lab (test VM only)**

**Step 1 — Build:** run the §17 stack (or just node_exporter) so metrics exist.

**Step 2 — Break something and answer three questions with three pillars:** stop a
service (`sudo systemctl stop cron`). Metrics: when did `node_systemd_unit_state` change?
Logs: `journalctl -u cron` shows who stopped it. Events: was there a package upgrade or
deploy just before?

**Step 3 — Fix:** `sudo systemctl start cron`. Write which pillar answered which question.

**How it breaks**

| Gap | Symptom |
|-----|---------|
| Metrics only | You know p99 is bad but cannot find which requests |
| Logs only | No alert until a human reads logs; no trends |
| No events | Hours spent before someone remembers the deploy |
| Logs not persistent | After a reboot `journalctl -b -1` shows nothing from before it; current systemd says `Specifying boot ID or boot offset has no effect, no persistent journal was found.` ([Logs reference](06-logs-journal.md)) |

**Why it matters for troubleshooting.** Picking the right pillar for the question saves
hours: never grep a week of logs for something a metric answers in one query, and never
try to find one bad request in a metric.

**Next step.** Learn the property that decides whether a metrics system survives:
cardinality.

### Cardinality

**Level:** [L4 · Lead/SRE] · keeping the metrics system alive

**Concept.** In Prometheus, every unique combination of metric name and label values is
a separate **time series**, and each active series costs memory (a few KB) and disk. The
number of series for a metric is the product of the number of distinct values of each
label. Labels with unbounded values (user IDs, email addresses, full URLs with IDs,
request IDs, IP addresses of clients, timestamps) create millions of series: Prometheus
slows down, runs out of memory or gets OOM-killed. Loki has the same problem with stream
labels.

```
 http_requests_total{method, code, path}
   method: 5 values × code: 10 values × path: 20 routes        =      1,000 series   ✓
   method: 5 values × code: 10 values × path: /user/123456 ... = millions of series  ✗
```

**Key terms**

| Term | Meaning |
|------|---------|
| Cardinality | Number of unique series (per metric or total) |
| Active series / head series | Series with recent samples, held in memory |
| Bounded label | Small, known set of values (`method`, `code`, `route`) |
| Unbounded label | Grows with users/requests (`user_id`, `path` with IDs, `trace_id`) |
| `metric_relabel_configs` | Scrape-time rules to drop or rewrite labels and metrics |

**See it on a real system**

```bash
# total active series
curl -s 'http://127.0.0.1:9090/api/v1/query?query=prometheus_tsdb_head_series' | jq -r '.data.result[0].value[1]'
# top 10 metric names by series count (fine on a homelab; heavy on big servers)
curl -s 'http://127.0.0.1:9090/api/v1/query' --data-urlencode 'query=topk(10, count by (__name__) ({__name__=~".+"}))' \
  | jq -r '.data.result[] | "\(.value[1])\t\(.metric.__name__)"'
# the Prometheus UI shows the same under Status → TSDB Status
```

```
2814  node_systemd_unit_state
1311  node_cpu_seconds_total
 640  container_memory_working_set_bytes
 402  node_filesystem_avail_bytes
```

→ Healthy small numbers. The systemd collector is the largest here (one series per unit
and state; five states per unit); restricting it with `--collector.systemd.unit-include`
keeps it small on busy hosts.

**Hands-on lab (test VM only)**

**Step 1 — Baseline** `prometheus_tsdb_head_series` on the §17 stack.

**Step 2 — Break it:** add a textfile-collector metric with a unique label value on
every line (simulating a request ID used as a label), and watch the series count grow:

```bash
sudo mkdir -p /var/lib/node_exporter/textfile
for i in $(seq 1 30); do
  echo "lab_bad_metric{request_id=\"$(cat /proc/sys/kernel/random/uuid)\"} 1" | sudo tee -a /var/lib/node_exporter/textfile/bad.prom >/dev/null
done
```

(node_exporter must run with `--collector.textfile.directory` pointing at that directory,
mounted into the container in §17.)

**Step 3 — Fix:** delete `bad.prom`, and add a `metric_relabel_configs` rule that drops the
label or the metric at scrape time:

```yaml
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: lab_bad_metric
        action: drop
```

**How it breaks**

| Symptom | First check |
|---------|-------------|
| Prometheus OOM-killed, restarts loop | Head series count; recent new label |
| Queries time out, dashboards slow | `topk(count by (__name__))`, TSDB status page |
| Loki: `maximum active stream limit exceeded` | High-cardinality stream labels (use log fields, not labels) |

**Why it matters for troubleshooting.** Your monitoring is also a production system; a
single badly labelled metric from a developer can take it down at the moment you need it
most.

**Next step.** Run the system that stores all those series: Prometheus.

---

## 11. Prometheus

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals (*Prometheus Basics* [notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Prometheus-Basics), *Node Exporter* [notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page), *Monitoring Containers* [notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Monitoring-Containers/page)) → PromQL → Service Discovery and relabeling ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) Note: this area and the [Prometheus docs](https://prometheus.io/docs/) · 3) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* ([YouTube](https://www.youtube.com/watch?v=6xmWr7p5TE0), 68 min) · 4) Practice: the §17 lab, then Traefik metrics on your lab Dokploy.

Prometheus is the standard metrics system for Linux hosts, Docker, Traefik and Kubernetes.
Official documentation: [prometheus.io/docs](https://prometheus.io/docs/). The §17 lab
builds everything in this area.

### Pull model and architecture

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · how Prometheus sees targets

**Concept.** Prometheus **pulls**: every `scrape_interval` (typically 15 s) it sends an
HTTP GET to each target's `/metrics` endpoint, parses the plain-text answer and stores the
samples in its local time-series database (TSDB, 15 days retention by default). Targets
come from static lists or service discovery (files, Docker/Swarm, Kubernetes, EC2). For
every scrape Prometheus also records a synthetic `up` series: 1 if the scrape worked, 0 if
not, which makes "target down" detection free. **Rules** evaluated every
`evaluation_interval` create new series (recording rules) or alerts (alerting rules);
firing alerts are sent to **Alertmanager**, which groups, routes and delivers them.
**Grafana** queries Prometheus with PromQL for dashboards.

```
                 ┌──────────── scrape: HTTP GET /metrics every 15 s ─────────────┐
                 ▼                                                               │
   ┌──────────────────────────┐   alerting rules   ┌──────────────────┐        targets
   │ Prometheus :9090         │ ─────────────────▶ │ Alertmanager     │──▶ email / chat / webhook
   │ TSDB (local, 15 d)       │                    │ :9093            │
   │ recording rules          │                    └──────────────────┘   node_exporter   :9100
   └────────────┬─────────────┘                                           blackbox        :9115
                │ PromQL                                                  cAdvisor        :8080
           ┌────┴─────┐                                                   Traefik metrics :8082
           │ Grafana  │                                                   app /metrics
           └──────────┘        short-lived batch jobs ─▶ Pushgateway ─▶ (scraped like a target)
```

Pull has practical advantages: Prometheus knows when a target is down, you can curl any
target yourself to see exactly what Prometheus sees, and targets need no knowledge of the
monitoring server. It requires network reachability **from** Prometheus **to** each
target port, which on UFW-protected hosts means a firewall rule.

**Key terms**

| Term | Meaning |
|------|---------|
| Target | One endpoint Prometheus scrapes (`host:port`) |
| Job | Group of targets with the same purpose (`job="node"`) |
| `instance` label | The target address (or a name you set) |
| Exporter | Program that translates a system's stats into `/metrics` |
| Counter | Only goes up (resets to 0 on restart): requests, bytes, seconds |
| Gauge | Goes up and down: temperature, memory available, queue length |
| Histogram | Buckets (`_bucket{le=...}`), `_sum`, `_count`: aggregatable latency distributions |
| Summary | Client-computed quantiles; cannot be aggregated across instances |
| Pushgateway | Holds metrics pushed by batch jobs for Prometheus to scrape |

**See it on a real system**

```bash
curl -s http://127.0.0.1:9090/-/ready                                  # Prometheus is up
curl -s http://127.0.0.1:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job, .labels.instance, .health, .lastError] | @tsv'
curl -s http://127.0.0.1:9100/metrics | grep -A3 '^# HELP node_cpu_seconds_total'
```

```
prometheus	localhost:9090	up
node	lab-vm1	up
blackbox-https	https://app.example.com	up
cadvisor	cadvisor:8080	down	Get "http://cadvisor:8080/metrics": dial tcp: lookup cadvisor on 127.0.0.11:53: server misbehaving

# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{cpu="0",mode="idle"} 362812.97
node_cpu_seconds_total{cpu="0",mode="iowait"} 1210.44
```

→ The cadvisor target is down because its name does not resolve on Docker's embedded DNS
(127.0.0.11): the container is not running or not on the same network. The `lastError`
column is the first thing to read for any down target.

**Hands-on lab (test VM only)**

**Step 1 — Build:** bring up the §17 stack and open the targets page
(`http://127.0.0.1:9090/targets` through an SSH tunnel).

**Step 2 — Break it:** `docker stop node-exporter`. Within one scrape interval the target
turns red with `connection refused`, and the query `up{job="node"}` returns 0.

**Step 3 — Fix:** `docker start node-exporter`; `up` returns to 1. Note that the gap in
the graphs is real missing data, not zero.

**How it breaks**

| `lastError` text | Cause | First command |
|------------------|-------|---------------|
| `connection refused` | Exporter not running or bound elsewhere | `ss -ltnp 'sport = :9100'` on the target |
| `context deadline exceeded` | Firewall drop, routing, or exporter too slow (> `scrape_timeout`) | `curl -m 5 http://TARGET:9100/metrics` from the Prometheus host/container |
| `server misbehaving` / `no such host` | DNS name does not resolve inside the Prometheus container | Container networks, `docker network inspect` |
| `server returned HTTP status 404 Not Found` | Wrong `metrics_path` | `curl -s TARGET/metrics` |
| `x509: certificate signed by unknown authority` | HTTPS target with private CA (Harbor-style) | `tls_config: ca_file:` in the scrape config |

**Why it matters for troubleshooting.** When your monitoring says nothing, first check
whether it is *able* to see: a down target means "no data", not "no problem".

**Next step.** The exporters you need for hosts, endpoints and containers.

### Exporters: node, blackbox and cAdvisor

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · host, endpoint and container metrics

**Concept.** Three exporters cover most of what an on-prem Docker host needs:

- **node_exporter** (port 9100): host metrics from `/proc` and `/sys`: CPU, memory, disks, filesystems, network, PSI, load, time sync, plus optional collectors. The **systemd collector** is off by default; enable it with `--collector.systemd` to get `node_systemd_unit_state` (the Ops Ladder drill alerts on failed units with it). The **textfile collector** reads `*.prom` files from a directory, so cron jobs and scripts can publish metrics such as "last successful backup".
- **blackbox_exporter** (port 9115): probes from the outside, like a user: HTTP(S) status and timings, TLS certificate expiry, TCP connect, ICMP, DNS. Prometheus passes the target as a URL parameter: `/probe?target=https://app.example.com&module=http_2xx`.
- **cAdvisor** (port 8080): per-container CPU, memory, I/O, network and throttling from cgroups (`container_*` metrics). In Kubernetes, the kubelet embeds it.

Others you will meet: `mysqld_exporter`, `postgres_exporter`, an Apache exporter that
reads `mod_status`, Traefik's built-in metrics, Docker engine metrics (`"metrics-addr"` in
`daemon.json`), and in Kubernetes `kube-state-metrics` and metrics-server.

**Key terms**

| Term | Meaning |
|------|---------|
| Collector | A module of node_exporter (cpu, meminfo, systemd, textfile...) |
| `--path.rootfs=/host` | Tell a containerised node_exporter where the host's root filesystem is mounted |
| Module (blackbox) | A named probe definition (`http_2xx`, `tcp_connect`, `icmp`) |
| `probe_success` | 1 if the blackbox probe passed |
| `probe_ssl_earliest_cert_expiry` | Unix time when the first certificate in the chain expires |

**See it on a real system**

```bash
# node_exporter: is the systemd collector on? any failed units?
curl -s http://127.0.0.1:9100/metrics | grep 'node_systemd_unit_state{.*state="failed"} 1'
# blackbox: run one probe by hand, exactly as Prometheus would (debug=true explains each step)
curl -s 'http://127.0.0.1:9115/probe?target=https://app.example.com&module=http_2xx&debug=true' | head -40
curl -s 'http://127.0.0.1:9115/probe?target=https://app.example.com&module=http_2xx' | grep -E '^probe_(success|http_status_code|ssl_earliest_cert_expiry|duration_seconds)'
# cAdvisor: memory working set per container
curl -s http://127.0.0.1:8080/metrics | grep '^container_memory_working_set_bytes{.*name="' | head -3
```

```
probe_duration_seconds 0.214389
probe_http_status_code 200
probe_ssl_earliest_cert_expiry 1.7961696e+09
probe_success 1
```

→ The probe succeeded, HTTP 200, total 214 ms, and the earliest certificate in the chain
expires at Unix time 1796169600: `date -u -d @1796169600` gives 2 December 2026, about 60
days away. The alert rules in §12 compute `probe_ssl_earliest_cert_expiry - time()`, the
seconds remaining.

A textfile-collector metric from a backup script (written atomically: temp file + `mv`,
so node_exporter never reads half a file):

```bash
# at the end of /usr/local/bin/backup.sh, only on success:
cat > /var/lib/node_exporter/textfile/backup.prom.$$ <<EOF
# HELP backup_last_success_timestamp_seconds Unix time of the last successful backup.
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds{job_name="www"} $(date +%s)
EOF
mv /var/lib/node_exporter/textfile/backup.prom.$$ /var/lib/node_exporter/textfile/backup.prom
```

Alert when `time() - backup_last_success_timestamp_seconds > 26 * 3600`: a backup that
silently stopped is caught within a day.

**Hands-on lab (test VM only)**

**Step 1 — Build:** the §17 stack runs all three exporters. Curl each `/metrics` and
count series: `curl -s http://127.0.0.1:9100/metrics | grep -vc '^#'`.

**Step 2 — Break it:** create a failing unit and watch the systemd collector report it:

```bash
printf '[Unit]\nDescription=lab unit that fails\n[Service]\nExecStart=/bin/false\n' | sudo tee /etc/systemd/system/lab-fail.service
sudo systemctl daemon-reload && sudo systemctl start lab-fail.service
curl -s http://127.0.0.1:9100/metrics | grep 'lab-fail.service'
```

**Step 3 — Break blackbox:** probe a name that does not resolve and one with a
self-signed certificate; read `probe_success` and the `debug=true` output for each.

**Step 4 — Fix:** `sudo systemctl reset-failed lab-fail.service && sudo rm /etc/systemd/system/lab-fail.service && sudo systemctl daemon-reload`.

**How it breaks**

| Symptom | Cause | Fix |
|---------|-------|-----|
| No `node_systemd_*` metrics | Collector not enabled, or no D-Bus access in a container | `--collector.systemd`, mount the system bus socket (§17) |
| Filesystem metrics show the container's disks | `--path.rootfs` missing or host `/` not mounted | `-v /:/host:ro,rslave` + `--path.rootfs=/host` |
| Network metrics show only `eth0` of a container | node_exporter not on the host network | `network_mode: host` |
| blackbox `probe_success 0` with `x509` in debug | Private CA (e.g. your Harbor CA) | `tls_config.ca_file` in the module |
| cAdvisor metrics without `name` labels | Wrong mounts / cgroup driver, or a cAdvisor too old for Docker Engine 29's containerd image store (`failed to identify the read-write layer ID` in its log) | Check its volumes; `docker logs cadvisor`; upgrade cAdvisor (v0.54+) |

**Why it matters for troubleshooting.** These three give you USE for the host, RED-style
black-box availability for every site, and per-container resource usage: the minimum
monitoring for a Dokploy server.

**Next step.** Tell Prometheus what to scrape: scrape configs and service discovery.

### Scrape configs and service discovery

**Level:** [L4 · Lead/SRE] · monitoring that follows Dokploy services

**Concept.** `prometheus.yml` lists **scrape jobs**. Each job has targets (static or
discovered), an interval, a path, a scheme and **relabeling** rules. `relabel_configs`
run before the scrape and act on targets and their labels (keep, drop, rename, build the
address); `metric_relabel_configs` run after the scrape and act on samples (drop noisy
metrics or labels). Service discovery replaces hand-maintained target lists: `file_sd`
reads target files you generate (from Ansible, for example), `docker_sd`/`dockerswarm_sd`
read the Docker API (Dokploy runs Swarm mode), `kubernetes_sd` reads the Kubernetes API.

**Key terms**

| Term | Meaning |
|------|---------|
| `static_configs` | Hard-coded targets |
| `file_sd_configs` | Targets from YAML/JSON files, reloaded automatically |
| `dockerswarm_sd_configs` | Targets from Swarm services/tasks/nodes |
| `__address__` | Internal label holding host:port to scrape |
| `__meta_*` | Discovery metadata labels, available only during relabeling |
| `__param_NAME` | URL parameter for the scrape (used by blackbox) |
| `scrape_timeout` | Must be ≤ `scrape_interval` (default 10 s) |

**See it on a real system**

A complete, commented example for a small on-prem estate (the §17 lab uses a subset):

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    site: onprem-dc1

rule_files:
  - /etc/prometheus/rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']

  # host metrics: target lists generated by Ansible into files
  - job_name: node
    file_sd_configs:
      - files: ['/etc/prometheus/targets/node-*.yml']

  # black-box HTTPS probes of public sites
  - job_name: blackbox-https
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://app.example.com
          - https://harbor.example.com
    relabel_configs:
      - source_labels: [__address__]      # the URL becomes ?target=...
        target_label: __param_target
      - source_labels: [__param_target]   # and the instance label
        target_label: instance
      - target_label: __address__         # but we actually scrape the exporter
        replacement: blackbox:9115

  # containers that opt in with a label, discovered from Docker Swarm (Dokploy)
  - job_name: swarm-apps
    dockerswarm_sd_configs:
      - host: unix:///var/run/docker.sock
        role: tasks
    relabel_configs:
      - source_labels: [__meta_dockerswarm_task_desired_state]
        regex: running
        action: keep
      - source_labels: [__meta_dockerswarm_service_label_prometheus_scrape]
        regex: "true"
        action: keep
      - source_labels: [__meta_dockerswarm_service_name]
        target_label: service
```

```yaml
# /etc/prometheus/targets/node-web.yml  (file_sd: picked up without a reload)
- targets: ['192.0.2.11:9100', '192.0.2.12:9100']
  labels:
    env: prod
    role: web
```

Validate and reload:

```bash
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml
curl -s -X POST http://127.0.0.1:9090/-/reload        # needs --web.enable-lifecycle
# or: docker kill -s HUP prometheus
```

> ⚠️ Mounting `/var/run/docker.sock` into Prometheus (needed for Docker/Swarm discovery)
> gives that container root-equivalent control of the host. Mount it read-only, keep
> Prometheus off public networks, or use file-based discovery instead.

**Hands-on lab (test VM only)**

**Step 1 — Build:** convert the §17 `node` job from `static_configs` to `file_sd_configs`
with a targets file in `./prometheus/targets/`.

**Step 2 — Break it:** add a target with a wrong port to the file. Without any reload,
it appears on the targets page within a minute as down with `connection refused`.

**Step 3 — Break the config:** introduce a YAML indentation error in `prometheus.yml` and
run `promtool check config`. Read the error. Then reload anyway and see that Prometheus
keeps the *old* config and logs `Error reloading config`.

**Step 4 — Fix** both, check with promtool, reload.

**How it breaks**

| Error text | Meaning |
|------------|---------|
| `FAILED: parsing YAML file ...: yaml: line 23: did not find expected key` | Indentation/syntax |
| `scrape timeout greater than scrape interval` | Fix `scrape_timeout` |
| `Error reloading config` in Prometheus logs | Old config still active; check with promtool |
| Target appears twice with different labels | Two jobs discover the same endpoint |
| `permission denied` on `/var/run/docker.sock` | Prometheus runs as nobody; socket is root:docker |

**Why it matters for troubleshooting.** Discovery is what keeps monitoring correct as
Dokploy services come and go; a static list silently goes stale.

**Next step.** Query the data: PromQL essentials.

### PromQL essentials

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · graphs you can trust

**Concept.** PromQL selects series by name and labels and computes over them. An
**instant vector** is the latest value of each matching series; a **range vector**
(`[5m]`) is all samples in a window, which functions such as `rate()` turn back into an
instant vector. Aggregations (`sum`, `avg`, `max`, `count`, `topk`) collapse series
`by` or `without` labels. Arithmetic between vectors matches series with identical label
sets unless you say otherwise with `on()`/`ignoring()`.

The functions you will use daily:

| Function | Use on | What it does | Example |
|----------|--------|--------------|---------|
| `rate(c[5m])` | Counters | Per-second average increase over the window, handles counter resets | Requests/s, bytes/s, CPU seconds/s |
| `irate(c[5m])` | Counters | Per-second rate from the **last two** samples only; spiky | Fast-moving graphs, never alerts |
| `increase(c[1h])` | Counters | Total increase over the window (= rate × seconds; extrapolated, may be fractional) | "OOM kills in the last hour" |
| `delta(g[1h])` / `deriv(g[1h])` | Gauges | Change / per-second slope of a gauge | Memory growth |
| `predict_linear(g[6h], 4*3600)` | Gauges | Linear-regression value N seconds ahead | "Disk full in 4 hours" |
| `histogram_quantile(0.95, ...)` | Histogram buckets | Percentile from summed bucket rates; keep `le` | p95 latency |
| `avg_over_time` / `max_over_time` / `quantile_over_time` | Gauges | Statistics over a window | Peak memory last 7 days |
| `absent(expr)` | Any | 1 when nothing matches | "Metric disappeared" alerts |
| `sum by (instance) (...)` | Any | Aggregate keeping only `instance` | Per-host totals |
| `topk(5, ...)` | Any | Five largest series | Top containers by memory |

Rules that prevent wrong graphs:

- **Never `rate()` a gauge**, and never use a raw counter's value on a graph (it only grows).
- **`rate` first, then `sum`**: `sum(rate(x[5m]))`, never `rate(sum(x)[5m:])` (a subquery; plain `rate(sum(x)[5m])` is not even valid PromQL), because summing first hides counter resets: when one series resets, the sum only drops a little and `rate` misreads that as a reset of the whole sum, producing a huge false spike.
- The range must contain at least 2 samples; use **≥ 4 × scrape interval** (`[1m]` at 15 s, `[5m]` is a safe default). In Grafana use `$__rate_interval`.
- `histogram_quantile` needs `le` kept in the aggregation: `sum by (le) (rate(..._bucket[5m]))`, or `sum by (le, service)` for per-service percentiles.
- Do not average percentiles; aggregate buckets.

**Key terms**

| Term | Meaning |
|------|---------|
| Matcher | `=`, `!=`, `=~` (regex), `!~` on a label |
| `by` / `without` | Keep only / drop these labels when aggregating |
| `on()` / `ignoring()` | Labels used to match two vectors |
| `group_left(LABEL)` | Many-to-one match that copies LABEL from the right side |
| `offset 1d` | Same query, shifted back in time (compare with yesterday) |
| Subquery `expr[30d:5m]` | Evaluate `expr` every 5 m over 30 days, then apply a range function |

**See it on a real system**

```bash
# run any PromQL from the shell (the UI and Grafana Explore do the same)
q() { curl -s http://127.0.0.1:9090/api/v1/query --data-urlencode "query=$1" | jq -r '.data.result[] | "\(.metric | del(.__name__) | tostring)\t\(.value[1])"'; }
q 'rate(node_network_receive_bytes_total{device="ens18"}[5m]) * 8'
q 'irate(node_network_receive_bytes_total{device="ens18"}[5m]) * 8'
q 'increase(node_vmstat_oom_kill[1h])'
q 'node_load1 * on (instance) group_left (nodename) node_uname_info'
```

```
{"device":"ens18","instance":"lab-vm1","job":"node"}	8123456.78
{"device":"ens18","instance":"lab-vm1","job":"node"}	21877400.12
{"instance":"lab-vm1","job":"node"}	0
{"instance":"lab-vm1","job":"node","nodename":"lab-vm1"}	0.42
```

→ Averaged over 5 minutes the interface receives ~8 Mbit/s, but the last two samples show
~22 Mbit/s: a burst that `rate` smooths out and `irate` shows. Alert on `rate`, explore
with `irate`. The `group_left` join copied the hostname from `node_uname_info` (whose
value is always 1) onto the load series.

**Hands-on lab (test VM only)**

**Step 1 — Build:** in the Prometheus UI (Graph tab) plot `node_cpu_seconds_total` raw:
lines that only go up. Then plot `rate(node_cpu_seconds_total{mode!="idle"}[1m])`.

**Step 2 — Break it on purpose:** plot `rate(node_memory_MemAvailable_bytes[5m])` (rate
of a gauge: nonsense values) and `rate(node_cpu_seconds_total[15s])` (range too short:
gaps and empty results). Graph `rate(sum(process_cpu_seconds_total)[5m:])` next to
`sum(rate(process_cpu_seconds_total[5m]))`, restart node_exporter (its own process counter
resets; kernel counters such as `node_cpu_seconds_total` do not, because they come from
`/proc` and run since boot) and see the huge false spike that `sum(rate(...))` does not
have.

**Step 3 — Fix** each query using the rules above and save the correct versions in your
notes.

**How it breaks**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `empty query result` for a rate | Range shorter than 2 scrapes | `[5m]` or `$__rate_interval` |
| Huge false spike (`rate(sum())`) or negative dip (`delta`/`deriv` on a counter) after an exporter or app restart | Counter reset handled on the wrong side of the aggregation, or a gauge function on a counter | `sum(rate())` |
| `histogram_quantile` returns NaN | No requests in window, or `le` dropped | Keep `le`; check `_count` rate > 0 |
| `many-to-many matching not allowed` | Join without unique match labels | `on(...)` with the right labels, `group_left` |
| `vector cannot contain metrics with the same labelset` | Labels dropped so series collide | Keep a distinguishing label |

**Why it matters for troubleshooting.** Wrong PromQL is the most common reason dashboards
"lie". You need to trust the graph during an incident.

**Next step.** Ready-made queries for the four resources.

### PromQL recipes for CPU, memory, disk and network

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · USE as queries

**Concept.** The same USE questions from §2, expressed as PromQL over node_exporter and
cAdvisor metrics. Copy them into Grafana panels and alert rules. All assume a `[5m]`
window; in Grafana replace it with `[$__rate_interval]`.

**Key terms**

| Metric family | Source |
|---------------|--------|
| `node_cpu_seconds_total{mode}` | Per-CPU time counters (like `/proc/stat`) |
| `node_memory_*_bytes` | `/proc/meminfo` |
| `node_disk_*` | `/proc/diskstats` (like iostat) |
| `node_filesystem_*` | `statfs` per mount (like df) |
| `node_network_*` | `/proc/net/dev` (like `ip -s link`) |
| `node_netstat_*` | `/proc/net/snmp`, `netstat` (TCP counters) |
| `node_pressure_*` | PSI |
| `container_*` | cAdvisor (per container cgroup) |

**See it on a real system**

```
# ---------- CPU ----------
# CPU busy % per host
100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))
# iowait % and steal % per host
100 * avg by (instance) (rate(node_cpu_seconds_total{mode="iowait"}[5m]))
100 * avg by (instance) (rate(node_cpu_seconds_total{mode="steal"}[5m]))
# load per core (saturation)
node_load5 / count without (cpu, mode) (node_cpu_seconds_total{mode="idle"})
# CPU pressure: share of time some task waited for CPU
rate(node_pressure_cpu_waiting_seconds_total[5m])

# ---------- Memory ----------
# memory used % (based on available, not free)
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
# swap activity (pages/s): the thrashing signal
rate(node_vmstat_pswpin[5m]) + rate(node_vmstat_pswpout[5m])
# OOM kills in the last hour
increase(node_vmstat_oom_kill[1h])
# memory pressure (some / full)
rate(node_pressure_memory_waiting_seconds_total[5m])
rate(node_pressure_memory_stalled_seconds_total[5m])

# ---------- Disk ----------
# filesystem used % (real filesystems only)
100 * (1 - node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"})
# hours until full, from the last 6 h trend (negative or huge = not filling)
(node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / -deriv(node_filesystem_avail_bytes{fstype=~"ext4|xfs"}[6h])) / 3600
# IOPS, throughput
rate(node_disk_reads_completed_total[5m]) + rate(node_disk_writes_completed_total[5m])
rate(node_disk_read_bytes_total[5m]) + rate(node_disk_written_bytes_total[5m])
# average read / write latency in seconds (iostat r_await / w_await)
rate(node_disk_read_time_seconds_total[5m])  / rate(node_disk_reads_completed_total[5m])
rate(node_disk_write_time_seconds_total[5m]) / rate(node_disk_writes_completed_total[5m])
# utilisation (0-1, iostat %util) and average queue (iostat aqu-sz)
rate(node_disk_io_time_seconds_total[5m])
rate(node_disk_io_time_weighted_seconds_total[5m])
# I/O pressure
rate(node_pressure_io_stalled_seconds_total[5m])

# ---------- Network ----------
# bits per second in/out, physical interfaces only
rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br-.*"}[5m]) * 8
rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|br-.*"}[5m]) * 8
# errors and drops
rate(node_network_receive_errs_total[5m]) + rate(node_network_receive_drop_total[5m])
# TCP retransmit ratio
rate(node_netstat_Tcp_RetransSegs[5m]) / rate(node_netstat_Tcp_OutSegs[5m])
# listen queue overflows (app not accepting fast enough)
rate(node_netstat_TcpExt_ListenOverflows[5m])
# conntrack table usage
node_nf_conntrack_entries / node_nf_conntrack_entries_limit

# ---------- System ----------
node_systemd_unit_state{state="failed"} == 1                  # failed units
node_timex_sync_status == 0                                   # clock not synchronised
time() - node_boot_time_seconds < 600                         # rebooted in last 10 min
node_filefd_allocated / node_filefd_maximum                   # file handle usage

# ---------- Containers (cAdvisor) ----------
# CPU cores used per container
sum by (name) (rate(container_cpu_usage_seconds_total{name!=""}[5m]))
# CPU throttling ratio per container (§4)
rate(container_cpu_cfs_throttled_periods_total{name!=""}[5m]) / rate(container_cpu_cfs_periods_total{name!=""}[5m])
# memory working set vs limit (limit 0 = unlimited)
container_memory_working_set_bytes{name!=""} / (container_spec_memory_limit_bytes{name!=""} > 0)
# top 5 containers by memory
topk(5, container_memory_working_set_bytes{name!=""})
```

→ Each recipe maps to a §2 USE cell: CPU busy = utilization, load per core and PSI =
saturation, retransmits and errors = errors. Build one Grafana row per resource with
these and you have your own "60-second checklist" dashboard.

**Hands-on lab (test VM only)**

**Step 1 — Build** a Grafana dashboard (§13) with one panel per recipe group.

**Step 2 — Break each resource** with the stress-ng commands from §4–§7 and confirm the
matching panel moves (and that the others do not).

**Step 3 — Fix** by stopping the load; save the dashboard JSON into `./grafana/dashboards/`
so it is provisioned as code.

**How it breaks**

| Symptom | Cause |
|---------|-------|
| Filesystem panel shows `tmpfs`, `overlay`, `squashfs` | Missing `fstype` filter |
| Network graph doubled | Counting both physical NIC and bridges/veths |
| Disk latency NaN when idle | Division by zero when no I/O: expected |
| Container panels empty | cAdvisor not scraped, or `name` label missing |

**Why it matters for troubleshooting.** Prepared queries mean that during an incident you
read graphs instead of debugging PromQL.

**Next step.** Metrics from the proxy and the orchestrator: Traefik, Dokploy and
Kubernetes.

### Traefik, Dokploy and Kubernetes metrics

**Level:** [L4 · Lead/SRE] · RED for every routed service

**Concept.** Host and container metrics tell you about resources; RED metrics for your
services come from the layer that sees every request. In the Dokploy stack that is
**Traefik**, which can expose Prometheus metrics for entrypoints, routers and services
(request counts by status code, duration histograms, open connections). Dokploy keeps
Traefik's static configuration under `/etc/dokploy/traefik/`; enable metrics there (or
through Dokploy's Traefik settings) on a dedicated internal entrypoint, and attach
Prometheus to `dokploy-network` so it can reach Traefik without publishing the port. In
Kubernetes the usual stack is the **kube-prometheus-stack** Helm chart (Prometheus
Operator, Alertmanager, Grafana, node_exporter, kube-state-metrics); `kubectl top` needs
**metrics-server**, which is separate and only keeps the latest values.

**Key terms**

| Term | Meaning |
|------|---------|
| `traefik_service_requests_total{code,method,service}` | Requests per backend service |
| `traefik_service_request_duration_seconds_bucket` | Latency histogram per service |
| `traefik_entrypoint_requests_total` | Requests per entrypoint (web, websecure) |
| kube-state-metrics | Kubernetes object state (deployments, pods, restarts) as metrics |
| metrics-server | Live CPU/memory for `kubectl top` and HPA; no history |
| ServiceMonitor | Prometheus Operator object that declares a scrape target |

**See it on a real system**

```yaml
# Traefik static config (traefik.yml) — add metrics on an internal-only entrypoint
entryPoints:
  metrics:
    address: ":8082"
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true
    buckets: [0.1, 0.3, 0.5, 1.0, 2.5, 5.0]
```

```yaml
# prometheus.yml job (Prometheus container attached to dokploy-network)
  - job_name: traefik
    static_configs:
      - targets: ['dokploy-traefik:8082']
```

```
# RED per Traefik service
sum by (service) (rate(traefik_service_requests_total[5m]))                                   # Rate
sum by (service) (rate(traefik_service_requests_total{code=~"5.."}[5m]))
  / sum by (service) (rate(traefik_service_requests_total[5m]))                               # Error ratio
histogram_quantile(0.95, sum by (le, service) (rate(traefik_service_request_duration_seconds_bucket[5m])))  # p95
```

```bash
# Kubernetes (CKA): live usage needs metrics-server
kubectl top nodes
kubectl top pods -A --sort-by=memory | head
kubectl get pods -A -o wide | grep -v Running          # then describe the odd ones
```

```
NAME     CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
cp1      312m         15%    2210Mi          58%
worker1  1840m        92%    5120Mi          66%
```

→ worker1 is at 92% CPU: check which pods (`kubectl top pods -A --sort-by=cpu`) and
whether their CPU limits throttle them (§4). `error: Metrics API not available` means
metrics-server is not installed or not ready.

The container name of Traefik in your Dokploy install and the exact location of its
config can differ between Dokploy versions; check with `docker ps --format '{{.Names}}' | grep -i traefik`
and the [Dokploy docs](https://docs.dokploy.com/). Traefik's metrics options are in the
[Traefik docs](https://doc.traefik.io/traefik/).

**Hands-on lab (test VM only)**

**Step 1 — Build:** on your lab Dokploy, enable Traefik metrics on `:8082`, restart
Traefik from Dokploy, attach the §17 Prometheus to `dokploy-network`
(`networks: dokploy-network: external: true` in compose) and add the job.

**Step 2 — Break it:** deploy a test app, then change its domain's port to a wrong one so
Traefik returns 502 (the Ops Ladder L3 drill). Watch the 5xx ratio for that service jump
in PromQL before you look at any log.

**Step 3 — Fix** the port and watch the ratio fall back to 0.

**How it breaks**

| Symptom | Cause |
|---------|-------|
| Traefik target `context deadline exceeded` | Prometheus not on `dokploy-network`, or port not listening |
| No `traefik_service_*` series, only entrypoint ones | `addServicesLabels` false |
| `kubectl top`: `Metrics API not available` | metrics-server missing / TLS to kubelet failing |
| Huge Traefik series count | Router labels with many routers; disable `addRoutersLabels` |

**Why it matters for troubleshooting.** After the migration the client's three Apache
vhosts become three Traefik services; per-service RED from Traefik tells you which one is
failing and since when, without opening a single log.

**Next step.** Turn queries into alerts: Alertmanager and alert rules.

---

## 12. Alertmanager and alert rules

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting (Alertmanager, receivers, silences) ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) KodeKloud: *Fundamentals of SRE* — Incident Management → Designing Effective Alerts ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Note: the rule set in this area and §15 on symptom-based alerting · 4) Practice: fire, group, silence and resolve every lab alert in §17 Step 6.

Prometheus decides **whether** an alert is firing; Alertmanager decides **who hears about
it, how, and how often**. Good alerting is mostly about saying less: grouped, deduplicated
pages that need a human, with a link to what to do.

### Routing, grouping, inhibition and silences

**Level:** [L4 · Lead/SRE] · pages that stay rare and meaningful

**Concept.** Prometheus evaluates alerting rules and sends every firing alert (with its
labels) to Alertmanager repeatedly while it fires. Alertmanager then:

- **Groups** alerts with the same values of `group_by` labels into one notification (one message for "5 disks filling on host X", not five).
- **Routes** them through a tree of matchers to a **receiver** (email, Slack/Discord/Telegram/Teams, webhook, PagerDuty).
- **Throttles**: waits `group_wait` before the first notification of a new group (to collect related alerts), `group_interval` before sending updates for that group, and `repeat_interval` before re-sending an unchanged firing alert.
- **Inhibits**: suppresses alerts when another alert is firing (no "high latency" pages when "host down" already fired for that host).
- **Silences**: mutes matching alerts for a time window, for planned maintenance.

```
 Prometheus ──alerts──▶ Alertmanager
                         ├─ inhibition (critical mutes warning for same instance)
                         ├─ silences   (maintenance on web01 until 22:00)
                         └─ route tree
                              ├─ severity="critical" ──▶ receiver: oncall (chat + email), repeat 1h
                              └─ default             ──▶ receiver: team-email, repeat 4h
                         grouped by [alertname, instance]: group_wait 30s, group_interval 5m
```

**Key terms**

| Term | Meaning |
|------|---------|
| Receiver | Named destination with one or more integrations |
| Route / matchers | Tree of rules matching alert labels (`severity="critical"`) |
| `group_by` | Labels that define one notification group |
| `group_wait` / `group_interval` / `repeat_interval` | First wait / update wait / re-notify wait |
| Inhibition | Rule muting target alerts while source alerts fire |
| Silence | Time-limited mute by matchers, with author and comment |
| `send_resolved` | Also notify when the alert stops firing |

**See it on a real system**

```yaml
# alertmanager.yml (lab version in §17)
global:                                   # email receivers fail validation without these
  smtp_smarthost: 'mail.example.com:587'
  smtp_from: 'alertmanager@example.com'
  # smtp_auth_username / smtp_auth_password if your relay requires login
route:
  receiver: team-email
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - matchers: ['severity="critical"']
      receiver: oncall
      repeat_interval: 1h

inhibit_rules:
  - source_matchers: ['severity="critical"']
    target_matchers: ['severity="warning"']
    equal: ['instance']

receivers:
  - name: team-email
    email_configs:
      - to: 'ops@example.com'
        send_resolved: true
  - name: oncall
    webhook_configs:
      - url: 'http://alert-relay.example.com/hook'    # e.g. a chat bridge you run
        send_resolved: true
```

```bash
# amtool ships in the Alertmanager image
amtool() { docker exec alertmanager amtool --alertmanager.url=http://localhost:9093 "$@"; }
amtool check-config /etc/alertmanager/alertmanager.yml
amtool alert query                                   # what is firing now
amtool silence add instance=lab-vm1 --duration=2h --author="$USER" --comment="resize LV, CHG-0042"
amtool silence query
amtool silence expire SILENCE_ID
# which receiver would an alert with these labels go to?
amtool config routes test --config.file=/etc/alertmanager/alertmanager.yml severity=critical alertname=TargetDown
```

```
Alertname                Starts At                Summary                                   State
DiskSpaceAbove85Percent  2026-10-03 10:12:44 UTC  Filesystem / on lab-vm1 is 91% full       active
SystemdUnitFailed        2026-10-03 10:20:01 UTC  lab-fail.service failed on lab-vm1        active
```

**Hands-on lab (test VM only)**

**Step 1 — Build:** the §17 stack with the lab `alertmanager.yml`.

**Step 2 — Break it:** fire two alerts for the same instance (fill the disk and fail a
unit, §17). Watch the Alertmanager UI group them per `alertname, instance`.

**Step 3 — Silence it:** add a silence for the instance with a comment, confirm the alerts
show as suppressed, then expire the silence.

**Step 4 — Fix** the underlying problems and confirm resolved notifications arrive (if
your receiver supports them).

**How it breaks**

| Symptom | Cause |
|---------|-------|
| Alerts firing in Prometheus, nothing in Alertmanager | `alerting:` block missing or wrong address; `docker logs prometheus` shows `Error sending alert` |
| Alert storm: 50 messages for one outage | `group_by` too fine (e.g. includes `device`), no inhibition |
| Pages never stop during maintenance | No silence; or silence matchers do not match labels exactly |
| Notifications fail | Receiver error in `docker logs alertmanager` (SMTP auth, webhook URL) |

**Why it matters for troubleshooting.** An alerting system that spams gets muted, and a
muted alerting system is the same as none. Grouping, inhibition and silences keep pages
rare and meaningful.

**Next step.** Write the rules that produce alerts worth sending.

### Alert rules that earn their page

**Level:** [L4 · Lead/SRE] · actionable alerts with a first command

**Concept.** An alerting rule is a PromQL expression plus a `for:` duration: the alert
goes **pending** when the expression returns results and **firing** only after it has
stayed true for the whole `for:` period (which filters spikes). Labels (`severity`) drive
routing; annotations (`summary`, `description`, `runbook_url`) are what the human reads.
Every rule should answer: is it urgent, is it actionable, and what is the first command
to run?

```
 expression true? ──no──▶ inactive
       │yes
       ▼
    pending ──(still true after `for:`)──▶ firing ──▶ Alertmanager
       │ false before `for:` ends                   │ expression false
       ▼                                            ▼
    inactive                                     resolved
```

**Key terms**

| Term | Meaning |
|------|---------|
| `expr` | PromQL; every returned series becomes one alert instance |
| `for` | How long it must stay true before firing |
| `keep_firing_for` | Keep firing for a while after it clears (avoids flapping; Prometheus 2.42+) |
| `labels.severity` | Routing hint: `warning` (ticket/chat) vs `critical` (page) |
| `annotations` | Human text; can use `{{ $labels.instance }}` and `{{ $value }}` |
| Recording rule | Precomputes an expression into a new series (faster dashboards and SLO alerts) |

**See it on a real system**

The rule set used in the §17 lab: every alert the spec and the Ops Ladder drill ask for.

```yaml
# prometheus/rules/node.yml
groups:
  - name: availability
    rules:
      - alert: TargetDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.job }} target {{ $labels.instance }} is down"
          description: "Prometheus cannot scrape it. First: curl the /metrics URL from the Prometheus container."

      - alert: EndpointProbeFailed
        expr: probe_success == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.instance }} fails its blackbox probe"
          description: "Check DNS, TLS and proxy: curl -v {{ $labels.instance }}"

      - alert: TLSCertExpiresIn14Days
        expr: probe_ssl_earliest_cert_expiry - time() < 14 * 86400
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificate for {{ $labels.instance }} expires in {{ $value | humanizeDuration }}"

      - alert: TLSCertExpiresIn3Days
        expr: probe_ssl_earliest_cert_expiry - time() < 3 * 86400
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "Certificate for {{ $labels.instance }} expires in {{ $value | humanizeDuration }}"

  - name: node
    rules:
      - alert: DiskSpaceAbove85Percent
        expr: |
          100 * (1 - node_filesystem_avail_bytes{fstype=~"ext4|xfs"}
                     / node_filesystem_size_bytes{fstype=~"ext4|xfs"}) > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Filesystem {{ $labels.mountpoint }} on {{ $labels.instance }} is {{ $value | printf \"%.0f\" }}% full"
          description: "First: du -xh --max-depth=1 {{ $labels.mountpoint }} | sort -h | tail"

      - alert: DiskWillFillIn4Hours
        expr: |
          predict_linear(node_filesystem_avail_bytes{fstype=~"ext4|xfs"}[6h], 4 * 3600) < 0
          and
          node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"} < 0.40
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.mountpoint }} on {{ $labels.instance }} will be full within 4 hours at the current rate"

      - alert: SystemdUnitFailed
        expr: node_systemd_unit_state{state="failed"} == 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.name }} failed on {{ $labels.instance }}"
          description: "First: systemctl status {{ $labels.name }}; journalctl -u {{ $labels.name }} -b -n 50"

      - alert: HighLoadPerCore
        expr: node_load15 / count without (cpu, mode) (node_cpu_seconds_total{mode="idle"}) > 2
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Load per core on {{ $labels.instance }} is {{ $value | printf \"%.1f\" }}"
          description: "Run the 60-second checklist: R (CPU) or D (I/O) tasks?"

      - alert: MemoryPressure
        expr: rate(node_pressure_memory_stalled_seconds_total[5m]) > 0.10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "All tasks on {{ $labels.instance }} stalled on memory {{ $value | humanizePercentage }} of the time"

      - alert: OOMKillDetected
        expr: increase(node_vmstat_oom_kill[10m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "OOM kill on {{ $labels.instance }}"
          description: "First: journalctl -k --since '15 min ago' | grep -i 'killed process'"

      - alert: ClockNotSynchronised
        expr: node_timex_sync_status == 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Clock on {{ $labels.instance }} not NTP-synchronised (TLS and auth will break)"
```

Why these thresholds:

- **Disk > 85% for 10 m** is the Ops Ladder drill's alert; the `for` stops a log burst from paging you.
- **predict_linear over 6 h, 4 h ahead**: fires for disks that are *filling*, regardless of size, and the `< 40% free` guard stops a large, slowly-shrinking disk from firing on noise. This is a **symptom-predicting** alert: a full disk is coming, act now.
- **Failed units for 5 m**: needs `--collector.systemd` on node_exporter.
- **Load per core > 2 for 15 m** is deliberately loose: load is a cause-signal, so it is a warning for a ticket, not a page (see §15).
- **Cert expiry** at 14 days (warning) and 3 days (critical) via blackbox: catches renewals that silently stopped (Let's Encrypt in Traefik, or your private CA for Harbor).

Validate before loading:

```bash
docker exec prometheus promtool check rules /etc/prometheus/rules/node.yml
# unit-test a rule with promtool test rules (optional, great in CI)
```

```
Checking /etc/prometheus/rules/node.yml
  SUCCESS: 11 rules found
```

**Hands-on lab (test VM only)**

**Step 1 — Build:** load the rules (§17) and open `http://127.0.0.1:9090/alerts`.

**Step 2 — Break it:** trigger each alert you can safely trigger on a test VM: stop
node_exporter (TargetDown), fill the disk with `fallocate` (§17 step list), fail a unit,
probe a non-existent host (EndpointProbeFailed). Watch each go inactive → pending → firing.

**Step 3 — Fix** each cause and watch the alerts resolve. Time how long detection took and
compare with the `for:` durations.

**How it breaks**

| Symptom | Cause |
|---------|-------|
| `promtool`: `could not parse expression` | PromQL syntax; test it in the UI first |
| Annotation shows `<no value>` | Label name wrong in `{{ $labels.X }}` |
| Alert flaps firing/resolved every few minutes | Threshold at the noise level; use `for`, `keep_firing_for`, or hysteresis |
| DiskWillFillIn4Hours fires after log rotation | Short window; 6 h window plus the free-space guard reduces this |
| Alert never fires though condition is visible | Labels differ between the two sides of `and`; test the expr alone |

**Why it matters for troubleshooting.** Every rule carries its first command in the
description, so the alert itself starts the troubleshooting. That is the difference
between "alert received" and "incident handled".

**Next step.** Make it all visible: Grafana.

---

## 13. Grafana

> 📚 **Study path:** 1) Tutorial: [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) (free sandbox; the PCA course's dashboarding module uses the Prometheus UI, not Grafana) · 2) KodeKloud: *Fundamentals of SRE* — Service Level Objectives and Measurements → Lab: Building a Monitoring Dashboard ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Read: [Grafana learning hub](https://grafana.com/docs/learning-hub/) · 4) Practice: import Node Exporter Full (1860) and build your own "60-second" dashboard as code.

Grafana turns PromQL (and Loki, CloudWatch, Elasticsearch queries) into dashboards. The
Grafana learning hub and the Grafana fundamentals tutorial linked from the Ops Ladder are
good companions to this area.

### Dashboards, panels and variables

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · dashboards as code

**Concept.** A **data source** tells Grafana where to query (Prometheus at
`http://prometheus:9090` from inside the Docker network). A **dashboard** is a set of
**panels**; each panel runs one or more queries and draws them (time series, stat, gauge,
bar gauge, table, heatmap for histograms, logs). **Variables** make one dashboard work for
every host or service: a drop-down filled by a query such as
`label_values(node_uname_info, instance)`, used in panel queries as `$instance`.
**Annotations** mark events (deploys, incidents) on every graph. Dashboards can be
imported by ID from the Grafana community catalog: **Node Exporter Full** (ID **1860**) is
the standard host dashboard and the quickest way to a complete USE view. Dashboards and
data sources can also be **provisioned** from files, so the whole setup lives in Git.

**Key terms**

| Term | Meaning |
|------|---------|
| Data source | Connection to a backend (Prometheus, Loki...) |
| Panel | One visualisation with its queries |
| Variable | Templated value (`$instance`, `$job`) from a query, list or text box |
| `$__rate_interval` | Grafana-computed safe range for `rate()` (≥ 4 scrape intervals) |
| `$__interval` | Grafana-computed step for the current zoom |
| Annotation | Event marker on graphs |
| Provisioning | Data sources/dashboards loaded from YAML/JSON files at startup |
| Explore | Ad-hoc query view, best place to debug PromQL and LogQL |

**See it on a real system**

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: 15s          # = scrape_interval, so $__rate_interval is computed correctly
```

A panel query using a variable and `$__rate_interval`:

```
100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle", instance=~"$instance"}[$__rate_interval])))
```

Importing Node Exporter Full: Dashboards → New → Import → enter `1860` → Load → pick the
Prometheus data source → Import. Its variables (`job`, `node`) must match your labels; if
panels are empty, check the `job` variable first.

```bash
# Grafana health and data source check from the host
curl -s http://127.0.0.1:3001/api/health
docker logs grafana 2>&1 | grep -iE 'error|provision' | tail
```

```
{
  "database": "ok",
  "version": "12.0.2"
}
```

**Hands-on lab (test VM only)**

**Step 1 — Build:** with the §17 stack running, import dashboard 1860, then build your own
"60-second" dashboard with four rows (CPU, memory, disk, network) from the §11 recipes and
an `$instance` variable.

**Step 2 — Break it: the classic data source mistake.** Change the data source URL to
`http://localhost:9090` and click "Save & test". Grafana runs in its own container, so
localhost is Grafana itself:

```
Post "http://localhost:9090/api/v1/query": dial tcp [::1]:9090: connect: connection refused
```

**Step 3 — Fix:** use the service name on the shared Docker network
(`http://prometheus:9090`). Then export your dashboard JSON (Share → Export) into
`./grafana/dashboards/` so it is provisioned on the next start.

**Step 4 — Annotate:** add an annotation for "stress test started" while running a §18
scenario, so the cause is visible on every panel.

**How it breaks**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` on Save & test | `localhost` inside the container | Service name on the Docker network |
| Panels show `No data` after import | Variable `job` does not match your job name | Edit the variable or your scrape job name |
| Graphs jagged or empty when zoomed out | Fixed `[1m]` range with large step | `$__rate_interval` |
| Grafana UI unreachable on :3000 | Port 3000 already used by Dokploy | Publish on another port (`127.0.0.1:3001:3000`) |
| Provisioned dashboard edits lost on restart | Provisioned dashboards are read from files | Edit the JSON file in Git, or set `allowUiUpdates` |

**Why it matters for troubleshooting.** A good dashboard answers the first three questions
of an incident (what, since when, which host) before you open a shell. Provisioning makes
it reproducible on every new server.

**Next step.** The other half of observability: logs and traces.

---

## 14. Logs and tracing

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — *Locate and Analyze System Log Files* ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)), then *Docker Certified Associate* — *Logging Driver* ([lesson notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · 2) KodeKloud: *Grafana Loki* — Grafana Loki Essentials (Alloy agent) → LogQL labs ([course](https://kodekloud.com/courses/grafana-loki)); heavier alternative *EFK Stack: Enterprise-Grade Logging and Monitoring* ([course](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring)) · 3) Note: [Logs & journal reference](06-logs-journal.md) · 4) Practice: the §14 labs on the §17 stack; for tracing, the OpenTelemetry (OTCA) course in KodeKloud's SRE learning path (check the current catalog).

Metrics tell you *that* something is wrong and *when*. Logs tell you *why*, and traces
tell you *where* in a chain of services the time went. This area starts with the log store
every Ubuntu server already has (journald), adds central log search with Loki, makes logs
machine-readable, and ends with distributed tracing. Command reference:
[Logs & journal](06-logs-journal.md).

### journald and persistent logs

**Level:** [L2 · Mid] · where every log on an Ubuntu server starts

**Concept.** systemd-journald collects everything a systemd unit writes to stdout and
stderr, syslog messages and the kernel log, and stores it in indexed binary files with
structured fields (`_SYSTEMD_UNIT`, `_PID`, `PRIORITY`, `_BOOT_ID`...). On Ubuntu the
directory `/var/log/journal` exists, so with the default `Storage=auto` the journal is
**persistent** across reboots; if that directory is missing, logs live only in
`/run/log/journal` (RAM) and vanish at reboot. Ubuntu also keeps classic text files written
by rsyslog (`/var/log/syslog`, `/var/log/auth.log`), and applications such as Apache write
their own files (`/var/log/apache2/`). Docker containers log through a **logging driver**:
the default `json-file` writes `/var/lib/docker/containers/ID/ID-json.log` and never
rotates it unless you set `log-opts` in `daemon.json`.

```
 kernel ─────────────┐
 systemd units ──────┤ stdout/stderr ──▶ journald ──▶ /var/log/journal/MACHINE-ID/*.journal (persistent)
 syslog() callers ───┘                        └──────▶ rsyslog ──▶ /var/log/syslog, auth.log (Ubuntu)
 Apache ────────────────────────────────────────────▶ /var/log/apache2/*.log  (logrotate)
 containers ──▶ dockerd logging driver ─────────────▶ /var/lib/docker/containers/ID/ID-json.log
                                     (or the journald driver ──▶ journal, field CONTAINER_NAME)
```

**Key terms**

| Term | Meaning |
|------|---------|
| `Storage=` | `auto` (persistent if `/var/log/journal` exists), `persistent`, `volatile`, `none` |
| `SystemMaxUse=` | Disk cap for the persistent journal (default 10% of the filesystem, at most 4 GB) |
| Rate limiting | `RateLimitIntervalSec=30s` and `RateLimitBurst=10000` per unit; the excess is dropped with a "Suppressed" message |
| Priority | 0 emerg, 3 err, 4 warning, 6 info, 7 debug (`-p err` shows err and worse) |
| Boot offset | `-b` is this boot, `-b -1` the previous one |
| Logging driver | How Docker stores container stdout: `json-file`, `local`, `journald`, `syslog`... |

**See it on a real system**

```bash
journalctl --disk-usage                                   # how much space the journal uses
ls -d /var/log/journal && journalctl --list-boots | tail -3   # persistent? how many boots kept?
journalctl -u apache2 --since '1 hour ago' -p warning --no-pager   # one unit, warnings and worse
journalctl -k -b -1 -p err --no-pager | tail              # kernel errors from the previous boot
journalctl -u ssh -o json --output-fields=MESSAGE,_PID -n 2 --no-pager   # the structured fields
journalctl --since today --no-pager | grep 'Suppressed' | tail -2       # rate limiting hit today?
docker info --format '{{.LoggingDriver}}'; cat /etc/docker/daemon.json
sudo du -sh /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -h | tail -3
```

```
Archived and active journals take 1.2G in the file system.
/var/log/journal
 -2 5f0c1e2a9b8d4c7e9a1b2c3d4e5f6a7b Mon 2026-09-28 06:01:12 UTC—Wed 2026-09-30 22:14:03 UTC
 -1 9a77d2c41e0f4b2d8c3e5f6a7b8c9d0e Wed 2026-09-30 22:15:40 UTC—Fri 2026-10-02 04:00:11 UTC
  0 c41b88a0d2e3f4a5b6c7d8e9f0a1b2c3 Fri 2026-10-02 04:01:02 UTC—Sat 2026-10-03 10:44:19 UTC
Oct 03 10:12:41 web01 systemd-journald[312]: Suppressed 48211 messages from app.service
json-file
{ "dns": ["192.0.2.53"] }
7.9G	/var/lib/docker/containers/3f2a9c1d7e4b.../3f2a9c1d7e4b...-json.log
```

→ The journal is persistent (the directory exists, three boots are kept) and uses 1.2 GB.
journald dropped 48,211 messages from `app.service` in one 30-second window: a log storm,
and the lines from that window are gone for good. Docker uses `json-file` without
`log-opts`, and one container's log has grown to 7.9 GB: a classic "disk full" root
cause. The fix is `"log-opts": {"max-size": "50m", "max-file": "5"}` in `daemon.json`,
which only applies to containers created after the change (recreate them).

**Hands-on lab (test VM only)**

**Step 1 — Build a noisy unit** that prints about 2,000 lines per second for two minutes:

```bash
sudo systemd-run --unit=lab-noisy --property=RuntimeMaxSec=120 \
  bash -c 'while :; do for i in $(seq 1 200); do echo "lab line $i"; done; sleep 0.1; done'
journalctl -u lab-noisy -f          # Ctrl-C after a few seconds
```

**Step 2 — Break it: hit the rate limit.** Within 30 seconds journald logs
`Suppressed N messages from lab-noisy.service`. Compare `journalctl -u lab-noisy --no-pager | wc -l`
with what the loop printed (about 2,000 per second): most lines were never stored.

**Step 3 — Break persistence (test VM only).** Switch the journal to RAM, note the time,
reboot, and look at the end of the previous boot:

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=volatile\n' | sudo tee /etc/systemd/journald.conf.d/lab.conf
sudo systemctl restart systemd-journald; date      # note this time
logger -t labtest "written while the journal was volatile"
sudo reboot                                        # test VM only
# after the reboot:
journalctl -b -1 --no-pager | tail -3              # ends at about the time you noted
journalctl -b -1 -t labtest --no-pager             # the labtest line is gone
```

**Step 4 — Fix:** `sudo rm /etc/systemd/journald.conf.d/lab.conf && sudo systemctl restart systemd-journald`.
After the next reboot, `journalctl --list-boots` keeps the current boot again. For a real
noisy service, lower its log level first; raise the limit only for a unit that
legitimately logs a lot (`LogRateLimitBurst=` in that unit).

**How it breaks**

| Symptom / error text | First command | Go to |
|----------------------|---------------|-------|
| `Suppressed N messages from UNIT` | `journalctl -u UNIT --since TIME` around the storm; fix the log level | [Logs reference](06-logs-journal.md) |
| Logs from before the reboot are missing | `ls -d /var/log/journal`, `grep -r Storage /etc/systemd/journald.conf*` | [Logs reference](06-logs-journal.md) |
| Disk full, `/var/lib/docker/containers` huge | `sudo du -sh /var/lib/docker/containers/*/*-json.log` | [Docker learn module](30-learn-docker.md) (`max-size`, `max-file`) |
| Disk full but `du` finds nothing | A deleted log file still held open: `sudo lsof +L1` | [Storage reference](01-storage-disk.md) |
| `docker logs` prints nothing useful | The app writes to a file inside the container instead of stdout | `docker exec CONTAINER ls -l /var/log` |

**Why it matters for troubleshooting.** "Where are this app's logs?" was one of the
questions in your Apache → Dokploy incident. The answer depends on the layer (journal,
Apache files, container driver, Traefik access log), and the journal only helps if it
survived the reboot and was not rate-limited during the incident.

**Next step.** Searching logs host by host does not scale: collect them centrally with
Loki.

### Loki, Alloy and LogQL

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · one place to search every host's logs

**Concept.** Grafana **Loki** stores logs from many hosts and lets you query them in
Grafana next to your metrics. Unlike Elasticsearch, Loki does **not** index the log text:
it indexes only a small set of **labels** (`job`, `host`, `unit`, `container`) and stores
the lines compressed in chunks. A query first selects streams by label, then filters the
text, much like `grep` across a fleet. That makes it cheap enough for a homelab or a small
on-prem estate, as long as labels stay low-cardinality (§10). An **agent** on each host
ships the logs: **Grafana Alloy** is the current one; **Promtail** is deprecated in favour
of Alloy (end of life in 2026), but you will still meet it on existing servers. The
**ELK/EFK** alternative (Elasticsearch, Logstash or Fluent Bit, Kibana) indexes every
word, which gives powerful full-text search and analytics at a much higher RAM and disk
cost.

```
 host: journald, /var/log/apache2, docker.sock
        │  Alloy (or Promtail) adds labels {host, job, unit, container}
        ▼
 Loki :3100   index = labels only, chunks = compressed lines
        ▲
        │  LogQL
 Grafana Explore, dashboards, alert rules
```

| Aspect | Loki + Alloy | ELK / EFK |
|--------|--------------|-----------|
| Index | Labels only | Every field and word |
| Resource cost | Low (a homelab VM is enough) | High (Elasticsearch wants several GB of RAM) |
| Query | LogQL: label selector, then line filters and parsers | Lucene / KQL full-text search |
| Best for | Ops logs next to Prometheus metrics in Grafana | Search-heavy analytics, security logs, large teams |
| KodeKloud | *Grafana Loki* | *EFK Stack: Enterprise-Grade Logging and Monitoring* |

**Key terms**

| Term | Meaning |
|------|---------|
| Stream | All lines that share the same label set |
| Label | Indexed key/value (`job`, `host`, `unit`, `container`); keep the set small |
| Line filter | Text match after the selector: contains, does not contain, regex (examples below) |
| Parser | `json`, `logfmt`, `pattern` and `regexp` stages extract fields at query time |
| Metric query | `count_over_time`, `rate` and `sum by` turn log lines into numbers |
| Alloy | Grafana's collector for logs, metrics and traces, with its own config language |

**See it on a real system**

LogQL, typed into Grafana Explore with the Loki data source:

```
# Apache error-log lines with AH00484 (MaxRequestWorkers reached) on web01
{job="apache", host="web01", filename=~".*error.log"} |= "AH00484"

# failed or OOM-killed units on any host
{job="systemd-journal"} |~ "Failed with result|oom-kill"

# Traefik JSON access log on a Dokploy host (when Traefik logs to stdout): 5xx for one site
{container=~".*traefik.*"} | json | DownstreamStatus >= 500 and RequestHost="app.example.com"

# a metric from logs: 5xx lines per minute, by status code
sum by (DownstreamStatus) (count_over_time({container=~".*traefik.*"} | json | DownstreamStatus >= 500 [1m]))

# rate of OOM messages per host, usable in a Loki alert rule
sum by (host) (rate({job="systemd-journal"} |= "Out of memory" [5m]))
```

```
2026-10-03 10:41:12  {filename="/var/log/apache2/error.log", host="web01", job="apache"}
[Sat Oct 03 10:41:12.004211 2026] [mpm_event:error] [pid 1022:tid 140211] AH00484: server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting
2026-10-03 09:58:40  {filename="/var/log/apache2/error.log", host="web01", job="apache"}
[Sat Oct 03 09:58:40.517330 2026] [mpm_event:error] [pid 1022:tid 140211] AH00484: server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting
```

→ Apache ran out of workers twice this morning on web01. The timestamps line up with the
latency panel in Grafana, so the next move is §8 (pools): which backend made the workers
wait?

The Alloy configuration that ships journald, Apache files and Docker container output:

```hcl
// alloy/config.alloy — ship journald, Apache log files and Docker container logs to Loki
loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}

// journald: keep the unit name as a label
loki.relabel "journal" {
  forward_to = []
  rule {
    source_labels = ["__journal__systemd_unit"]
    target_label  = "unit"
  }
}
loki.source.journal "system" {
  forward_to    = [loki.write.default.receiver]
  relabel_rules = loki.relabel.journal.rules
  labels        = {job = "systemd-journal", host = "lab-vm1"}
}

// Apache log files (adds a filename label automatically)
local.file_match "apache" {
  path_targets = [{"__path__" = "/var/log/apache2/*.log", job = "apache", host = "lab-vm1"}]
}
loki.source.file "apache" {
  targets    = local.file_match.apache.targets
  forward_to = [loki.write.default.receiver]
}

// Docker containers: stdout/stderr, labelled with the container name
discovery.docker "local" {
  host = "unix:///var/run/docker.sock"
}
discovery.relabel "containers" {
  targets = discovery.docker.local.targets
  rule {
    source_labels = ["__meta_docker_container_name"]
    regex         = "/(.*)"
    target_label  = "container"
  }
}
loki.source.docker "containers" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.relabel.containers.output
  labels     = {job = "docker", host = "lab-vm1"}
  forward_to = [loki.write.default.receiver]
}
```

**Hands-on lab (test VM only)**

**Step 1 — Build:** add Loki and Alloy to the §17 stack. Save the Alloy configuration above
as `~/monitoring/alloy/config.alloy`, add these two services under `services:` in
`docker-compose.yml`, and a Loki data source next to the Prometheus one:

```yaml
# docker-compose.yml, under services: (lab only; pin versions you have tested)
  loki:
    image: grafana/loki:3.5.1
    container_name: loki
    command: -config.file=/etc/loki/local-config.yaml   # the image's built-in single-node config
    networks: [monitoring]
    restart: unless-stopped

  alloy:
    image: grafana/alloy:v1.9.1
    container_name: alloy
    command: run --server.http.listen-addr=0.0.0.0:12345 --storage.path=/var/lib/alloy/data /etc/alloy/config.alloy
    volumes:
      - ./alloy/config.alloy:/etc/alloy/config.alloy:ro
      - /var/log/journal:/var/log/journal:ro
      - /run/log/journal:/run/log/journal:ro
      - /etc/machine-id:/etc/machine-id:ro
      - /var/log/apache2:/var/log/apache2:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    ports:
      - "127.0.0.1:12345:12345"       # Alloy UI: health of every component
    networks: [monitoring]
    restart: unless-stopped
```

```yaml
# grafana/provisioning/datasources/loki.yml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    uid: loki
    access: proxy
    url: http://loki:3100
```

Then `docker compose up -d loki alloy && docker compose restart grafana`. The built-in Loki
config keeps data inside the container, which is fine for a lab and lost when the
container is removed; write your own config with a volume for anything longer-lived.

**Step 2 — Generate and find logs:**

```bash
logger -t labtest "hello from the lab"
docker run -d --name loglab alpine sh -c 'while :; do echo "container says hi"; sleep 5; done'
```

In Explore: `{job="systemd-journal"} |= "hello from the lab"` and
`{container="loglab"} |= "container says hi"` (Docker discovery refreshes about once a
minute, so give it a moment).

**Step 3 — Break it:** remove the `/var/log/journal` mount from the alloy service and
recreate it (`docker compose up -d alloy`). Depending on the Alloy version, the journal
component shows an error in the Alloy UI (`http://127.0.0.1:12345` through the SSH tunnel)
and `docker logs alloy`, or it stays green but reads only the empty `/run/log/journal`;
either way new `logger` lines never reach Loki. That silent case is the lesson: check that
data arrives, not only that the agent is healthy.

**Step 4 — Fix:** restore the mount, recreate Alloy, confirm a fresh `logger` line
appears, then `docker rm -f loglab`.

**How it breaks**

| Symptom / error text | Cause | First check / fix |
|----------------------|-------|-------------------|
| Explore shows nothing | Wrong label or time range, or the agent is not shipping | Label browser in Explore; `docker logs alloy` |
| `entry too far behind` / out-of-order errors | Old lines replayed after the agent lost its position, or clock skew | NTP ([Time reference](12-time-ntp.md)); keep Alloy's `--storage.path` on a volume |
| `maximum active stream limit exceeded` | High-cardinality labels (request IDs, client IPs, URL paths) | Keep those as fields and parse them with the json parser at query time |
| `429` with `ingestion rate limit exceeded` | Log storm, or Loki limits too low | Fix the noisy source first, then raise `limits_config` on purpose |
| `permission denied` on the journal or `docker.sock` | The agent's user cannot read them | Run the agent with access to the `systemd-journal` group or as root (lab) |
| `client version 1.4x is too old. Minimum supported API version is 1.44` | Docker Engine 29+ refuses old API clients; the agent image is too old | Upgrade the agent image; `"min-api-version"` in `daemon.json` only as a temporary workaround |

**Why it matters for troubleshooting.** During the migration you will have Apache logs on
the old host, Traefik and container logs on the Dokploy host, and journal entries on both.
One LogQL query across all of them, next to the metric that alerted, replaces five SSH
sessions and a lot of `grep`.

**Next step.** Logs are only as searchable as their format: structured logging.

### Structured logging

**Level:** [L3 · Senior] · logs that machines can query

**Concept.** A free-text line such as `user 42 checkout failed after 3.2s` needs a regex
per format. A **structured** line carries named fields, as JSON
(`{"level":"error","user":42,"duration_ms":3200}`) or logfmt
(`level=error user=42 duration_ms=3200`). Tools then filter and aggregate without guessing:
`jq`, Loki's `json` and `logfmt` parsers, Elasticsearch fields. Good structured logs carry
a timestamp with a time zone (ISO 8601, ideally UTC), a level, the service name, a
**request ID or trace ID** so one request can be followed across proxy, app and database,
and numbers as numbers (`duration_ms`, `status`). They never contain passwords, tokens or
card numbers, and they keep personal data to what you are allowed to store.

**Key terms**

| Term | Meaning |
|------|---------|
| JSON lines | One JSON object per line |
| logfmt | `key=value` pairs separated by spaces |
| Request ID / correlation ID | One ID per request, passed between services in a header and logged by each |
| Log level | debug, info, warning, error; production usually logs info and above |
| Sampling | Logging only a share of high-volume, low-value lines |

**See it on a real system**

```bash
# Apache: a JSON access log format (put it in a conf file, then use it in CustomLog)
#   LogFormat "{\"time\":\"%{%Y-%m-%dT%H:%M:%S%z}t\",\"host\":\"%V\",\"client\":\"%a\",\"method\":\"%m\",\"path\":\"%U\",\"status\":%>s,\"bytes\":%B,\"duration_us\":%D,\"request_id\":\"%{UNIQUE_ID}e\"}" json_access
#   (UNIQUE_ID needs mod_unique_id: sudo a2enmod unique_id)

# Traefik JSON access log (Dokploy): slowest requests with status, duration in ms
jq -r '[.StartUTC, .RequestHost, .RequestPath, .DownstreamStatus, (.Duration/1e6|floor)] | @tsv' access.log \
  | sort -t$'\t' -k5 -n | tail -3

# a JSON-logging app in Docker: errors only, skipping any non-JSON lines
docker logs --since 10m CONTAINER 2>&1 | jq -Rrc 'fromjson? | select(.level=="error") | {time, request_id, msg}'
```

```
2026-10-03T10:41:07.512Z	app.example.com	/api/orders	200	2954
2026-10-03T10:41:09.118Z	app.example.com	/api/orders	200	3012
2026-10-03T10:41:12.004Z	app.example.com	/api/export	504	30001
{"time":"2026-10-03T10:41:12Z","request_id":"8f3c2a91","msg":"upstream timeout calling inventory"}
```

→ `/api/orders` takes about 3 s, and `/api/export` ends in a 504 after exactly 30 s: a
proxy or worker timeout. The app's error line carries request ID `8f3c2a91`; search that ID
in the proxy and database logs and you see the same request from every hop. Apache escapes
unusual bytes as `\xhh`, which strict JSON parsers reject, so test your format with `jq`
before you depend on it.

**Hands-on lab (test VM only)**

**Step 1 — Build:** generate a JSON log like a small web app would:

```bash
tee /var/tmp/jsonlog.py >/dev/null <<'EOF'
import json, random, time, uuid
from datetime import datetime, timezone
for _ in range(200):
    status = random.choice([200] * 18 + [500, 504])
    rec = {"time": datetime.now(timezone.utc).isoformat(), "service": "shop",
           "level": "error" if status >= 500 else "info", "request_id": uuid.uuid4().hex[:8],
           "status": status, "duration_ms": random.randint(5, 900)}
    print(json.dumps(rec), flush=True)
    time.sleep(0.01)
EOF
python3 /var/tmp/jsonlog.py > /var/tmp/shop.log
```

**Step 2 — Query it** like a metrics system would: error count and p95 duration.

```bash
jq -s '[.[] | select(.status >= 500)] | length' /var/tmp/shop.log
jq -r '.duration_ms' /var/tmp/shop.log | sort -n | awk '{a[NR]=$1} END {print "p95="a[int(NR*0.95)]" ms"}'
```

**Step 3 — Break it:** append a multi-line Python traceback and rerun the first query.

```bash
python3 -c 'raise ValueError("boom")' 2>> /var/tmp/shop.log
jq -s '[.[] | select(.status >= 500)] | length' /var/tmp/shop.log   # parse error: the file is no longer pure JSON lines
```

A log shipper would also split that traceback into several unrelated entries.

**Step 4 — Fix:** make queries tolerant (`jq -R 'fromjson?' /var/tmp/shop.log | jq -s '[.[] | select(.status >= 500)] | length'`),
and make real apps log exceptions as one JSON field instead of raw stderr. Clean up with
`rm /var/tmp/jsonlog.py /var/tmp/shop.log`.

**How it breaks**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `jq: error ... parse error` | JSON and plain-text lines mixed | Make queries tolerant (`fromjson?`); log only JSON to stdout |
| Stack traces split into many entries | Multi-line output | Log exceptions as one field; use a multiline stage in the agent |
| Times off by hours between hosts | Local time without an offset | ISO 8601 with offset, or UTC everywhere ([Time reference](12-time-ntp.md)) |
| Passwords or tokens in logs | Full requests or query strings logged | Redact at the source and rotate the leaked secret ([Security learn module](37-learn-security-devsecops.md)) |
| One request cannot be followed across hops | No request ID propagated | Create it at the edge (Traefik or Apache), pass it as a header, log it everywhere |

**Why it matters for troubleshooting.** With a request ID in every hop's log, "this user
got a 504 at 10:41" becomes one search instead of an afternoon of matching timestamps
across Traefik, the app and PostgreSQL.

**Next step.** Request IDs in logs are the manual version of distributed tracing. Next:
OpenTelemetry.

### Tracing with OpenTelemetry

**Level:** [L4 · Lead/SRE] · where the time went across services

**Concept.** A **trace** follows one request through every service it touches. Each unit
of work (an HTTP handler, a database query, an outgoing call) is a **span** with a start
time, a duration, attributes and a parent. All spans of one request share a **trace ID**,
which travels between services in the W3C `traceparent` HTTP header. **OpenTelemetry
(OTel)** is the vendor-neutral standard: SDKs and auto-instrumentation for each language,
the **OTLP** protocol (port 4317 for gRPC, 4318 for HTTP), and the **Collector**, which
receives, samples, batches and forwards telemetry to a backend such as **Jaeger** or
**Grafana Tempo**. Traefik v3 can create spans and pass `traceparent` on by itself.
Tracing every request is expensive, so production systems **sample**: for example 10% of
traces, or all slow and failed ones with tail sampling in the Collector.

```
 trace 4bf92f3577b34da6a3ce929d0e0e4736                     0 ms        250        500
 ├─ traefik    GET /checkout                                 ████████████████████████  480 ms
 │  └─ shop    GET /checkout (Flask)                          ███████████████████████  470 ms
 │     ├─ shop GET (requests → inventory)                      ████████████████████    410 ms
 │     │  └─ inventory GET /inventory                           ███████████████████    402 ms  ← slow
 │     └─ shop SELECT orders (psycopg)                                             ██   12 ms
```

**Key terms**

| Term | Meaning |
|------|---------|
| Trace / trace ID | One request end to end / its 128-bit ID |
| Span | One timed operation with a parent span |
| `traceparent` | W3C header carrying the trace ID, the parent span ID and the sampled flag |
| Instrumentation | Code (manual or automatic) that creates spans |
| OTLP | OpenTelemetry's wire protocol: 4317 gRPC, 4318 HTTP |
| Collector | Receives, processes (sampling, batching) and exports telemetry |
| Head / tail sampling | Decide at the start of a trace / after seeing the whole trace |

**See it on a real system**

```bash
# a single-container Jaeger v2 backend for the lab: UI on 16686, OTLP on 4317/4318 (loopback only;
# the tag was current when written, pin the version you have tested)
docker run -d --name jaeger -p 127.0.0.1:16686:16686 -p 127.0.0.1:4317:4317 -p 127.0.0.1:4318:4318 \
  jaegertracing/jaeger:2.5.0

# the slowest spans of the latest trace of service "shop" (Jaeger reports microseconds)
curl -s 'http://127.0.0.1:16686/api/traces?service=shop&limit=1' \
  | jq -r '.data[0].spans[] | [(.duration/1000|floor), .operationName] | @tsv' | sort -rn

# Traefik v3 static configuration: export spans over OTLP/HTTP
#   tracing:
#     otlp:
#       http:
#         endpoint: http://jaeger:4318/v1/traces
```

```
452	GET /checkout
409	GET
401	GET /inventory
```

→ The checkout took 452 ms; 409 ms of it was one outgoing HTTP call (`GET`, the client
span), and 401 ms of that was the `/inventory` handler itself. The slow part is the
inventory service, not the network and not the checkout code.

**Hands-on lab (test VM only)**

**Step 1 — Build an instrumented app** with two endpoints in a virtualenv, with Jaeger from
the commands above already running:

```bash
sudo apt install -y python3-venv
python3 -m venv /var/tmp/otel-lab && . /var/tmp/otel-lab/bin/activate
pip install flask requests opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install            # adds instrumentation for flask and requests
tee /var/tmp/otel-lab/app.py >/dev/null <<'EOF'
import time, requests
from flask import Flask
app = Flask(__name__)

@app.route("/checkout")
def checkout():
    requests.get("http://127.0.0.1:8002/inventory", timeout=5)
    return "ok\n"

@app.route("/inventory")
def inventory():
    time.sleep(0.4)          # the slow dependency
    return "in stock\n"
EOF
cd /var/tmp/otel-lab
OTEL_SERVICE_NAME=shop OTEL_TRACES_EXPORTER=otlp OTEL_METRICS_EXPORTER=none OTEL_LOGS_EXPORTER=none \
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318 \
  opentelemetry-instrument flask --app app run --port 8002 &
sleep 3; for i in 1 2 3 4 5; do curl -s http://127.0.0.1:8002/checkout; done
```

**Step 2 — Find the slow span:** open Jaeger (`http://127.0.0.1:16686` through an SSH
tunnel), pick service `shop`, open one trace, or use the `curl | jq` query above.

**Step 3 — Break it twice.** Restart the app with `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317`
(the gRPC port) while keeping `http/protobuf`: requests still work, the app's stderr shows
export errors, and no new traces appear. Then restore the endpoint but add
`OTEL_TRACES_SAMPLER=traceidratio OTEL_TRACES_SAMPLER_ARG=0`: everything looks healthy and
nothing is exported at all.

**Step 4 — Fix:** restore the 4318 endpoint and the default sampler, confirm new traces
appear, then clean up: `kill %1; deactivate; rm -rf /var/tmp/otel-lab; docker rm -f jaeger`
(the directory holds only the lab virtualenv and app you just created).

**How it breaks**

| Symptom | Cause | First check |
|---------|-------|-------------|
| No traces at all | Port/protocol mismatch (4317 gRPC vs 4318 HTTP), firewall, sampler at 0 | App stderr for exporter errors; the `OTEL_*` variables |
| Traces stop at the proxy | Proxy not instrumented or not forwarding `traceparent` | Traefik `tracing:` config; Apache passes request headers through by default |
| One service missing from the chain | Library not instrumented, or async work loses the context | `opentelemetry-bootstrap -a requirements` lists missing packages |
| Child spans start before their parent | Clock skew between hosts | NTP on every host ([Time reference](12-time-ntp.md)) |
| Backend storage fills up or costs too much | Every request traced | Head sampling ratio, tail sampling in the Collector |

**Why it matters for troubleshooting.** Once the client's apps are split into containers
behind Traefik, "which hop is slow?" can no longer be answered with one host's tools. A
trace answers it per request, and its trace ID leads straight to the right log lines.

**Next step.** You can now see almost everything. Decide which of it matters to users, and
alert only on that: SLIs, SLOs and error budgets.

---

## 15. SLIs, SLOs and error budgets

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Service Level Objectives and Measurements (SLIs, SLOs, error budgets; Lab: Building a Monitoring Dashboard) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Observability Fundamentals (SLO/SLA/SLI) ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 3) Read: the Google SRE book chapters on service level objectives and on monitoring distributed systems, from its [table of contents](https://sre.google/sre-book/table-of-contents/) · 4) Practice: an SLO with burn-rate alerts for one lab app (§15 labs), then a draft SLO for one of the client's apps.

Monitoring everything is easy; deciding what "working" means is the senior part. An SLO
is a number the team and the client agree on, its error budget says how much risk you may
take, and burn-rate alerts page only when users are really hurt.

### SLIs and SLOs

**Level:** [L4 · Lead/SRE] · agree on what "working" means, in numbers

**Concept.** A **service level indicator (SLI)** measures user experience as a ratio of
good events to valid events: "share of HTTP requests that did not return 5xx"
(availability), "share of requests answered within 300 ms" (latency), "share of probes
that succeeded". A **service level objective (SLO)** is a target for an SLI over a window:
"99.9% of requests succeed, rolling 30 days". A **service level agreement (SLA)** is a
contract with penalties, usually looser than the SLO. Measure SLIs as close to the user as
you can (Traefik, blackbox probes), never from the host's CPU, and never aim for 100%:
every extra nine is expensive, and users cannot tell 99.99% from 100% through their own
Wi-Fi.

| SLO (30 days) | Full outage allowed | Failed requests allowed per million |
|---------------|---------------------|-------------------------------------|
| 99% | 7 h 12 min | 10,000 |
| 99.5% | 3 h 36 min | 5,000 |
| 99.9% | 43 min 12 s | 1,000 |
| 99.95% | 21 min 36 s | 500 |
| 99.99% | 4 min 19 s | 100 |

**Key terms**

| Term | Meaning |
|------|---------|
| SLI | Good events ÷ valid events, measured where the users are |
| SLO | Target for an SLI over a window (rolling 30 days is common) |
| SLA | Contract with consequences; keep it looser than the SLO |
| Error budget | 1 − SLO: the share of events allowed to fail (next topic) |
| Valid events | What counts: usually excludes health checks and 4xx caused by clients |
| Recording rule | A precomputed series that keeps SLO queries cheap |

**See it on a real system**

First find the exact Traefik service label of the app (the suffix depends on how Dokploy
deployed it):

```
count by (service) (traefik_service_requests_total)
```

Then the SLIs as recording rules, which also feed the burn-rate alerts in the next topic:

```yaml
# prometheus/rules/slo-shop.yml — SLIs for the "shop" app behind Traefik
groups:
  - name: slo-shop-sli
    rules:
      # availability SLI: share of non-5xx requests
      - record: sli:shop_availability:ratio_rate5m
        expr: |
          1 - (
            sum(rate(traefik_service_requests_total{service=~"shop.*", code=~"5.."}[5m]))
            /
            sum(rate(traefik_service_requests_total{service=~"shop.*"}[5m]))
          )
      # latency SLI: share of requests faster than 300 ms (needs a 0.3 bucket, see §11)
      - record: sli:shop_latency_300ms:ratio_rate5m
        expr: |
          sum(rate(traefik_service_request_duration_seconds_bucket{service=~"shop.*", le="0.3"}[5m]))
          /
          sum(rate(traefik_service_request_duration_seconds_count{service=~"shop.*"}[5m]))
```

The 30-day view for a Grafana stat panel:

```
# availability over the last 30 days
1 - (sum(increase(traefik_service_requests_total{service=~"shop.*", code=~"5.."}[30d]))
     / sum(increase(traefik_service_requests_total{service=~"shop.*"}[30d])))

# latency SLI over the last 30 days
sum(increase(traefik_service_request_duration_seconds_bucket{service=~"shop.*", le="0.3"}[30d]))
  / sum(increase(traefik_service_request_duration_seconds_count{service=~"shop.*"}[30d]))

# probe-based SLI for sites without Traefik metrics (the old Apache host, for example)
avg_over_time(probe_success{instance="https://app.example.com"}[30d])
```

```
availability 30d     0.99942
latency_300ms 30d    0.9871
probe 30d            0.99965
```

→ 99.942% of requests succeeded, so a 99.9% availability SLO is met. Only 98.7% were faster
than 300 ms, so a 99% latency SLO is missed, and that is what to work on. The probe says
99.965% because it hits one URL once per scrape and misses errors that only some paths
produce. Use both: probes catch "completely down", Traefik ratios catch partial failure.

**Hands-on lab (test VM only)**

**Step 1 — Build:** with Traefik metrics enabled on your lab Dokploy (§11) and Prometheus
scraping them, deploy a small app named `shop` (any image with an HTTP endpoint), add the
SLI rules, reload Prometheus, and generate steady traffic:
`while :; do curl -s -o /dev/null https://SHOP_DOMAIN/; sleep 0.2; done`.

**Step 2 — Write the SLO down:** "shop: 99.5% of requests non-5xx and 95% under 300 ms,
rolling 30 days". Lab targets are looser than production ones on purpose, so you can see
the budget move.

**Step 3 — Break it:** point the app's domain at a wrong port for three minutes (the
Traefik 502 drill) and watch `sli:shop_availability:ratio_rate5m` drop in the Prometheus
UI.

**Step 4 — Fix** the port and watch the SLI recover. Keep the traffic loop running for
the next topic.

**How it breaks**

| Mistake | Consequence | Better |
|---------|-------------|--------|
| SLO on CPU or load | Pages for busy-but-fine servers, silence for broken-but-idle ones | SLIs from requests or probes |
| 100% target | No room for any change; every deploy is a breach | The lowest target users accept |
| Only a probe-based SLI | Partial failures (one path, some users) stay invisible | Add request-based SLIs from Traefik |
| Only a request-based SLI | A total outage (DNS, firewall) sends no requests: the ratio has no data and nothing fires | Add a probe-based SLI and alert |
| Ratios on tiny traffic | 1 error in 3 requests reads as 67% bad | Longer windows; a minimum-traffic condition |

**Why it matters for troubleshooting.** An SLO turns "the site feels slow lately" into
"latency SLI 98.7% against a 99% objective since the 14 September deploy": something you
can prioritise, report to the client and verify after the fix.

**Next step.** Turn the SLO into a budget and into alerts that page only when the budget
is really at risk.

### Error budgets and burn rates

**Level:** [L4 · Lead/SRE] · pages only when users are really hurt

**Concept.** The **error budget** is what the SLO allows to fail: with 99.9% over 30 days,
0.1% of requests, or 43 minutes of full outage. The **burn rate** is how fast you are
spending it: the current error ratio divided by the budget ratio. Burn rate 1 spends the
budget exactly by the end of the window; burn rate 14.4 spends 2% of a 30-day budget in
one hour. Alerting on burn rate over **two windows** (a long one for significance, a short
one so the alert clears soon after recovery) gives pages that are both fast and quiet;
this is the multi-window, multi-burn-rate approach from Google's SRE practice.

| Severity | Burn rate | Long window | Short window | Budget spent when it fires |
|----------|-----------|-------------|--------------|----------------------------|
| Page | 14.4 | 1 h | 5 min | 2% |
| Page | 6 | 6 h | 30 min | 5% |
| Ticket | 1 | 3 days | 6 h | 10% |

The budget is also a **policy**: while budget remains, ship features and take planned
risks; when it is spent, freeze risky changes and spend the time on reliability. That
turns arguments about "too many deploys" into a number both sides agreed on (change
management is in the [CI/CD & SRE learn module](33-learn-cicd-iac-sre.md)).

**Key terms**

| Term | Meaning |
|------|---------|
| Error budget | 1 − SLO over the window |
| Burn rate | Observed error ratio ÷ (1 − SLO) |
| Multi-window alert | Both the long and the short window must exceed the burn rate |
| Budget policy | Agreed actions when the budget is low or spent |

**See it on a real system**

```yaml
# prometheus/rules/slo-shop.yml (continued) — SLO 99.9%, so the budget ratio is 0.001
  - name: slo-shop-burn
    rules:
      - record: slo:shop_errors:ratio_rate5m
        expr: 1 - sli:shop_availability:ratio_rate5m
      - record: slo:shop_errors:ratio_rate30m
        expr: |
          sum(rate(traefik_service_requests_total{service=~"shop.*", code=~"5.."}[30m]))
          / sum(rate(traefik_service_requests_total{service=~"shop.*"}[30m]))
      - record: slo:shop_errors:ratio_rate1h
        expr: |
          sum(rate(traefik_service_requests_total{service=~"shop.*", code=~"5.."}[1h]))
          / sum(rate(traefik_service_requests_total{service=~"shop.*"}[1h]))
      - record: slo:shop_errors:ratio_rate6h
        expr: |
          sum(rate(traefik_service_requests_total{service=~"shop.*", code=~"5.."}[6h]))
          / sum(rate(traefik_service_requests_total{service=~"shop.*"}[6h]))

      - alert: ShopErrorBudgetFastBurn
        expr: |
          slo:shop_errors:ratio_rate1h > (14.4 * 0.001)
          and
          slo:shop_errors:ratio_rate5m > (14.4 * 0.001)
        labels:
          severity: critical
        annotations:
          summary: "shop is spending its 30-day error budget 14x too fast (2% per hour)"
          description: "First: 5xx per Traefik service and router, then the site down playbook."
      - alert: ShopErrorBudgetSlowBurn
        expr: |
          slo:shop_errors:ratio_rate6h > (6 * 0.001)
          and
          slo:shop_errors:ratio_rate30m > (6 * 0.001)
        labels:
          severity: critical
        annotations:
          summary: "shop is spending its error budget 6x too fast (5% per 6 hours)"
```

How much budget is left this month:

```
# 1 = untouched, 0 = spent, negative = overspent
1 - (
  (sum(increase(traefik_service_requests_total{service=~"shop.*", code=~"5.."}[30d]))
   / sum(increase(traefik_service_requests_total{service=~"shop.*"}[30d])))
  / 0.001
)
```

```
0.42
```

→ 58% of this month's budget is gone. If that happened in the first week, the policy says
slow down risky changes; on the last day of the window it is fine. For a feel of the
numbers: at steady traffic, a 3-minute total outage spends 3 ÷ 43.2 ≈ 7% of a 99.9%
budget.

**Hands-on lab (test VM only)**

**Step 1 — Build:** add the burn-rate group to `slo-shop.yml` (keep `0.001`, or use
`0.005` to match a 99.5% lab SLO), check it with `promtool check rules`, and reload.

**Step 2 — Break it:** set the wrong port again for five minutes. Watch
`ShopErrorBudgetFastBurn` go from inactive straight to firing on the alerts page within a
few minutes (the burn rules have no `for:`, so there is no pending phase): with 100%
errors, the 1-hour window crosses 1.44% after less than a minute.

**Step 3 — Fix** the port. The 5-minute window recovers within minutes and the alert
resolves, although the 1-hour ratio is still high: that is the short window's job.

**Step 4 — Compute** the budget used with the query above and write it into a one-line
incident note.

**How it breaks**

| Symptom | Cause | Fix |
|---------|-------|-----|
| Burn alert never fires on a quiet app | Too few requests for a meaningful ratio | Synthetic traffic (blackbox) or longer windows |
| Fires on 2 errors out of 3 requests at night | Tiny denominators | Add a minimum-traffic condition, e.g. `and sum(rate(traefik_service_requests_total{service=~"shop.*"}[1h])) > 0.1` |
| Alert still firing an hour after the fix | Only the long window is used | Add the short window |
| Planned maintenance spends the whole budget | Maintenance counted as errors | Agree in the policy whether planned windows count |

**Why it matters for troubleshooting.** Burn-rate alerts page you for the outage that
matters and stay quiet for a 30-second blip. That keeps on-call sustainable and keeps
people trusting the pager.

**Next step.** Apply the same thinking to the rest of your rules: alert on symptoms, not
causes.

### Alerting on symptoms, not causes

**Level:** [L4 · Lead/SRE] · fewer pages, faster fixes

**Concept.** A **symptom** is what users experience: errors, slow responses, an
unreachable site, a certificate about to expire, a disk about to fill. A **cause** is one
of many possible reasons: high CPU, high load, little free memory, a busy disk. Causes
often happen without hurting anyone (a 02:00 backup pushes CPU to 100% and nobody
notices), and symptoms can happen with no cause alert at all (a wrong Traefik port: CPU
idle, every request a 502). So **page** on symptoms and on imminent, certain failures, and
send cause signals to **tickets and dashboards**, where they speed up the diagnosis once a
symptom alert has fired. Every page should be urgent, actionable and new, and carry the
first command or a runbook link.

How the §12 and §15 rules classify:

| Rule | Type | Route |
|------|------|-------|
| ShopErrorBudgetFastBurn, ShopErrorBudgetSlowBurn | Symptom: users are failing | Page |
| EndpointProbeFailed | Symptom: site unreachable | Page |
| DiskWillFillIn4Hours, TLSCertExpiresIn3Days | Imminent, certain failure | Page |
| TLSCertExpiresIn14Days, DiskSpaceAbove85Percent | Early warning | Ticket or chat |
| TargetDown | Monitoring blind spot | Ticket; page if it is the probe or Prometheus itself |
| SystemdUnitFailed, OOMKillDetected | Cause, sometimes a symptom | Ticket; page only for critical units |
| HighLoadPerCore, MemoryPressure | Cause | Ticket or dashboard |

**Key terms**

| Term | Meaning |
|------|---------|
| Symptom-based alert | Fires on user-visible impact (SLO burn, failed probe) |
| Cause-based alert | Fires on an internal condition that may or may not hurt users |
| Alert fatigue | So many low-value pages that real ones get ignored |
| Runbook | Short, tested steps for one alert, linked from its annotation |

**See it on a real system**

```bash
# how noisy was alerting last week? notifications sent per integration (q() from §11)
q 'sum by (integration) (increase(alertmanager_notifications_total[7d]))'
# minutes each alert spent firing in 7 days (ALERTS is written every 15 s evaluation)
q 'topk(5, sum by (alertname) (count_over_time(ALERTS{alertstate="firing"}[7d])) * 15 / 60)'
```

```
{"integration":"email"}	212
{"integration":"webhook"}	37
{"alertname":"HighLoadPerCore"}	1840
{"alertname":"DiskSpaceAbove85Percent"}	610
{"alertname":"EndpointProbeFailed"}	22
```

→ 212 emails in one week, and the alert that fired longest was HighLoadPerCore (1,840
minutes), a cause alert nobody acted on. EndpointProbeFailed fired for 22 minutes: that was
the one that mattered, and it was buried in the noise. Demote or retune the cause alerts.

**Hands-on lab (test VM only)**

**Step 1 — Build:** classify every rule you loaded in §12 and §15 with the table above, and
set `severity` labels to match.

**Step 2 — Break it:** add a cause alert, `CPUAbove80` with
`100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m]))) > 80`,
`for: 1m` and `severity: critical`, then run the §18 CPU round. You are paged although the
lab app's SLI stays at 100%.

**Step 3 — Fix:** delete the rule, rely on the burn-rate alert for users and keep CPU on the
dashboard. Write a one-line runbook for every remaining page.

**How it breaks**

| Symptom | Cause | Fix |
|---------|-------|-----|
| On-call ignores pages | Alert fatigue from cause alerts | Demote causes to tickets; review noisy alerts weekly |
| Outage and no page | Only cause alerts; nothing measures users | Add SLO burn and probe alerts |
| Paged with no idea what to do | No runbook, vague summary | First command in `description`, a `runbook_url` annotation |
| Same incident pages 30 times | Grouping too fine, no inhibition | §12 routing and inhibition |

**Why it matters for troubleshooting.** Your first ten minutes in an incident depend on the
alert that woke you: a symptom alert with a first command starts the right drill-down, a
"CPU high" page starts a guessing game.

**Next step.** Look further ahead than the next page: capacity planning.

---

## 16. Capacity planning

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil (capacity planning) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Note: Little's law (§1), your load-test numbers (§9) and the [senior architecture module](39-learn-senior-architecture.md) for sizing designs · 3) Read: the methodology pages of [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) · 4) Practice: a capacity sheet for your lab, then one for the client's Apache server before the Dokploy move.

Capacity planning answers two questions before they turn into incidents: "will this
server cope with next quarter's load?" and "what do we need to buy or migrate, and by
when?". It combines the baselines from §2–§7, long-term metrics from §11, load-test
results from §9 and the queueing theory from §1.

### Baselines, trends and headroom

**Level:** [L3 · Senior] · know how full every resource really is at peak

**Concept.** For each resource you need four numbers: the **peak** (not the average: use
the daily peak, or its p95 over a month), the **trend** (growth per week or month), the
**limit** at which service degrades (not 100%: the knee from §1 for latency-sensitive
resources, the hard limit for space), and from those the **headroom** and the **time to
exhaustion**. Plan for failure too: with **N+1** redundancy the remaining nodes must carry
a failed node's load, so three nodes at 60% become two nodes at 90%, past the knee.

| Resource | What to measure for planning | Practical planning limit |
|----------|------------------------------|--------------------------|
| CPU | p95 of 5-minute busy % at the daily peak; run queue per core | 60–70% for latency-sensitive services |
| Memory | Peak of total minus available; PSI memory | 80% used, PSI `some` near zero |
| Disk space | Used %, growth per day | Alert at 85%, plan never to pass 80% |
| Inodes | `df -i` used % | 80% |
| Disk I/O | Peak IOPS and await against the fio baseline (§6) | 60–70% of baseline IOPS, await near baseline |
| Network | Peak bit/s against link speed; retransmits | 60–70% of the link at peak |
| Pools | Busy workers ÷ maximum at peak | 70% |

**Key terms**

| Term | Meaning |
|------|---------|
| Baseline | Usage and performance when things are known to be healthy |
| Peak | The busiest period that matters: daily, month-end, a campaign |
| Headroom | Capacity left before the planning limit |
| Time to exhaustion | Headroom ÷ growth rate |
| N+1 | Enough capacity to lose one node and still meet the SLO |

**See it on a real system**

```bash
# daily peak CPU busy % from sysstat history
# (Ubuntu keeps 7 days by default; raise HISTORY in /etc/sysstat/sysstat for planning)
for f in /var/log/sysstat/sa[0-9][0-9]; do
  LC_ALL=C sar -u -f "$f" | awk -v f="${f##*/}" '$1 ~ /^[0-9]/ && $NF ~ /^[0-9.]+$/ {b=100-$NF; if (b>m) m=b} END {printf "%s peak CPU busy %.0f%%\n", f, m}'
done
```

The same questions in PromQL, over a month of §17 data:

```
# p95 of CPU busy % over 30 days, per host (the subquery samples every 5 minutes)
quantile_over_time(0.95, (100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))))[30d:5m])

# peak memory used % over 30 days
max_over_time((100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))[30d:5m])

# days until the root filesystem is full, from the 30-day trend (negative or NaN = not filling)
node_filesystem_avail_bytes{mountpoint="/"} / -deriv(node_filesystem_avail_bytes{mountpoint="/"}[30d]) / 86400

# request-rate growth: this week compared with four weeks earlier
sum(rate(traefik_service_requests_total[7d])) / sum(rate(traefik_service_requests_total[7d] offset 28d))
```

```
sa28 peak CPU busy 71%
sa29 peak CPU busy 74%
sa30 peak CPU busy 69%

{instance="web01"}  p95 CPU busy            58.2
{instance="web01"}  peak memory used         83.9
{instance="web01"}  days until / is full     46
                    request rate vs 4 weeks  1.18
```

→ CPU p95 is 58%, but the daily peaks already reach 69–74%: the busiest hour sits at the
knee. Traffic grew 18% in four weeks, so in a month the peak hour lands around 85% and
latency will suffer long before CPU reaches 100%. Memory peaks at 84%, above the 80%
planning limit. The root filesystem fills in 46 days: a ticket now, not a page later.
Verdict: plan the resize or the migration within weeks, not quarters.

**Hands-on lab (test VM only)**

**Step 1 — Build a capacity sheet** for your lab VM, one row per resource: peak, planning
limit, headroom, growth, time to exhaustion. A few days of §17 data are enough to
practise.

**Step 2 — Break it: simulate growth.** Write 200 MB every ten minutes with a transient
timer and watch the "days until full" query count down:

```bash
sudo systemd-run --unit=lab-growth --on-calendar='*:0/10' \
  /bin/sh -c 'fallocate -l 200M /var/tmp/growth-$(date +%s).bin'
```

**Step 3 — Fix:** `sudo systemctl stop lab-growth.timer && sudo rm -f /var/tmp/growth-*.bin`
(only the files this timer created). Compare the forecast you wrote with what really
happened.

**How it breaks**

| Mistake | Consequence |
|---------|-------------|
| Planning from 24-hour averages | The peak hour is past the knee while the average says 35% |
| Ignoring per-core saturation | A single-threaded process maxes one core while total CPU shows 25% |
| Watching bytes, not inodes | `No space left on device` with `df -h` at 60% ([Storage reference](01-storage-disk.md)) |
| Sizing for "all nodes healthy" | One node failure pushes the rest past the knee |
| Burstable cloud instances | Fine until the CPU credits run out ([AWS learn module](36-learn-cloud-aws.md)) |

**Why it matters for troubleshooting.** Many "sudden" incidents (disk full, slow every
Monday, OOM at month-end) are capacity problems the data predicted weeks earlier. A
capacity sheet turns them into planned work.

**Next step.** Turn the sheet into a forecast and a sizing for a new or migrated server.

### Forecasting and sizing

**Level:** [L4 · Lead/SRE] · decide what to buy or migrate, and when

**Concept.** Sizing combines three tools you already have. **Little's law** (§1) turns the
peak request rate and latency into required concurrency: workers, threads, database
connections. **Load tests** (§9) give the measured capacity of one instance at the SLO
latency, for example "140 req/s at p95 under 300 ms for one 2-vCPU container". **Trends**
(previous topic) give the forecast peak. Instances needed = forecast peak ÷ (capacity per
instance × planning utilization), plus one for failures and rolling deploys. Memory is
sized from the working sets you measured (PSS for forked workers, the container working
set for containers), plus page cache for the data you want to keep hot.

Worked example: sizing the Dokploy host before moving the client's Apache vhosts.

| Input | Value | Source |
|-------|-------|--------|
| Peak traffic today, all vhosts | 120 req/s | Apache access logs, busiest hour (command below) |
| Growth | 20% per quarter | The last two quarters of logs |
| Forecast peak in 12 months | 120 × 1.2⁴ ≈ 250 req/s | |
| Capacity of one app container (2 vCPU) at p95 under 300 ms | 140 req/s | k6 test on the new stack (§9) |
| Planning utilization | 65% | Below the knee (§1) |
| Containers needed | 250 ÷ (140 × 0.65) ≈ 2.7 → 3, plus 1 for failures and deploys = 4 | |
| Workers per container | 250 req/s × 0.15 s average latency ≈ 38 in flight → 10 per container | Little's law |
| Memory | 4 × 450 MB working set + Traefik 150 MB + DB 2 GB + page cache 2 GB + OS 1 GB ≈ 7 GB | cAdvisor, `smem` |
| CPU | 4 × 2 vCPU for the app + 2 for the DB + 2 for Traefik and the OS = 12 vCPU | |
| Decision | One 12 vCPU / 16 GB host, or two 8 vCPU / 16 GB hosts for real N+1 at host level | |

**Key terms**

| Term | Meaning |
|------|---------|
| Forecast | Expected peak at a future date (trend plus seasonality) |
| Capacity per instance | Measured maximum throughput that still meets the SLO |
| Planning utilization | The share of capacity you allow at the forecast peak, below the knee |
| Seasonality | Repeating peaks: Monday mornings, month-end, campaigns |
| Lead time | How long buying or migrating takes; the forecast must reach further than that |

**See it on a real system**

```bash
# busiest hours (average requests per second) across all vhost access logs, rotated .gz included
zcat -f /var/log/apache2/*access.log* \
  | awk '{split($4, t, ":"); print substr(t[1], 2) " " t[2] ":00"}' \
  | sort | uniq -c | sort -rn | head -5 \
  | awk '{printf "%6.1f req/s  %s %s\n", $1/3600, $2, $3}'
```

```
 118.6 req/s  28/Sep/2026 09:00
 112.3 req/s  21/Sep/2026 09:00
  97.4 req/s  29/Sep/2026 09:00
  95.0 req/s  14/Sep/2026 09:00
  61.2 req/s  30/Sep/2026 14:00
```

→ Monday 09:00 is the peak every week (seasonality); plan from about 120 req/s today. An
hourly average still hides the busiest minutes; for latency-sensitive sizing, count per
minute (keep `t[3]` in the first `awk`) and expect the peak minute to be noticeably higher.

A rough forecast in PromQL once the new stack has a month of data:

```
# daily request rate projected 90 days ahead from a 30-day linear trend
predict_linear((sum(rate(traefik_service_requests_total[1d])))[30d:1h], 90 * 86400)
```

**Hands-on lab (test VM only)**

**Step 1 — Build:** take the wrk or k6 capacity number of the §9 lab app at your SLO
latency.

**Step 2 — Forecast:** assume 25% growth per quarter and compute the instances you need in
6 and 12 months with the formula above.

**Step 3 — Break it:** limit the app container to half its CPU (`--cpus`, or Dokploy's
resource limits) and rerun the load test. Does capacity halve, or drop further because
you are now past the knee? Update the sheet.

**Step 4 — Fix:** restore the limit, and write the sizing as a short recommendation:
inputs, formula, result, risks.

**How it breaks**

| Mistake | Consequence |
|---------|-------------|
| Linear extrapolation past the knee | Latency explodes earlier than the CPU forecast suggests |
| Sizing on CPU only | The database connection limit or a pool is the real ceiling (§8) |
| Forgetting deploy overlap | Rolling deploys briefly run old and new containers side by side |
| No lead time | The forecast says "full in 30 days" and procurement takes 60 |

**Why it matters for troubleshooting.** A sizing with its inputs written down can be
reviewed: when the new host struggles, you can see which assumption was wrong instead of
arguing about whether the server is "too small".

**Next step.** Build the monitoring stack that produces all these numbers: the §17 homelab
lab.

---

## 17. Homelab lab: full monitoring stack

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals → *Node Exporter* ([lesson notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page)) → Alerting ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) Note: Compose and networking in the [Docker learn module](30-learn-docker.md) · 3) Read: the [Prometheus docs](https://prometheus.io/docs/) and the [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) tutorial · 4) Practice: this lab end to end, then rebuild it from your Git repo on a second VM without looking at the notes.

**Level:** [L4 · Lead/SRE] · the Ops Ladder L4 drill, written as a runbook

This is the Ops Ladder L4 drill: node_exporter, Prometheus, Grafana and Alertmanager in the
homelab, with alerts for a disk above 85% and for failed systemd units (which needs
node_exporter's systemd collector). It also adds cAdvisor (containers), blackbox_exporter
(probes) and a tiny "alert sink" that prints every notification, so you can see the whole
chain without an email server. Everything runs with Docker Compose on one Ubuntu
22.04/24.04 test VM. Published ports bind to `127.0.0.1` only, because Docker-published
ports bypass UFW; you reach the web UIs through an SSH tunnel.

```
 lab VM (Ubuntu + Docker)                                           your laptop
 ┌─────────────────────────────────────────────────────────────┐    ssh -L 3001 -L 9090 -L 9093
 │ host network: node-exporter :9100 (systemd + textfile)      │◀──────────────────────────────
 │ ┌── docker network "monitoring" 172.30.0.0/24 ────────────┐ │
 │ │ prometheus :9090 ──scrape──▶ host.docker.internal:9100   │ │
 │ │      │          ──scrape──▶ cadvisor :8080, blackbox :9115, alertmanager :9093
 │ │      └──alerts──▶ alertmanager ──webhook──▶ alert-sink :5001 (prints notifications)
 │ │ grafana :3000 (published as 127.0.0.1:3001) ──PromQL──▶ prometheus
 │ └──────────────────────────────────────────────────────────┘ │
 └─────────────────────────────────────────────────────────────┘
```

The directory layout you will build:

```
~/monitoring/
├── docker-compose.yml
├── .env                          # Grafana admin password (lab only, never commit)
├── prometheus/
│   ├── prometheus.yml
│   ├── rules/node.yml            # the §12 rule set
│   └── targets/                  # for file_sd later (§11 lab)
├── alertmanager/alertmanager.yml
├── blackbox/blackbox.yml
├── alert-sink/sink.py
└── grafana/
    ├── provisioning/datasources/prometheus.yml
    ├── provisioning/dashboards/files.yml
    └── dashboards/               # dashboard JSON files, provisioned at start
```

### Step 1 — Prepare the lab VM

**Goal:** confirm Docker and Compose work, the lab ports are free, and the folders and
secret file exist.

```bash
docker version --format '{{.Server.Version}}'; docker compose version
# lab ports must be free (3000 may already belong to Dokploy, so Grafana is published on 3001)
sudo ss -ltnp | grep -E ':(3001|5001|8080|9090|9093|9100|9115)\b' || echo "all lab ports free"
mkdir -p ~/monitoring/{prometheus/rules,prometheus/targets,alertmanager,blackbox,alert-sink}
mkdir -p ~/monitoring/grafana/{provisioning/datasources,provisioning/dashboards,dashboards}
sudo mkdir -p /var/lib/node_exporter/textfile
cd ~/monitoring && printf 'GF_ADMIN_PASSWORD=%s\n' "$(openssl rand -base64 18)" > .env && chmod 600 .env
```

```
28.4.0
Docker Compose version v2.39.1
all lab ports free
```

**What it means:** Docker Engine and the Compose v2 plugin are installed, none of the lab
ports is taken, and `.env` holds a random Grafana admin password that only you can read.
If `ss` prints a line instead, that port already has an owner (on a Dokploy host, 8080 or
3000 are common).

**Why this step (now):** every later failure is easier to read when you know the base is
sound. A port clash is the most common reason a Compose service restarts in a loop with
`address already in use`: the same class of problem as your Apache/Dokploy port incident,
and cheaper to find now than after six containers are running.

**Next step:** if all ports are free → Step 2. If a port is taken → find its owner with
`sudo ss -ltnp 'sport = :PORT'` ([ports playbook](22-playbook-ports-inventory.md)) and
change the left side of that service's `ports:` mapping in Step 2. If `docker compose` is
missing → install the Compose plugin first ([Docker learn module](30-learn-docker.md)).

### Step 2 — Write the compose file

**Goal:** one file that defines all seven services, their volumes, ports and the network.

```yaml
# ~/monitoring/docker-compose.yml — homelab monitoring stack (test VM / homelab only)
# Image tags were current when this was written: pin the versions you have tested.
name: monitoring

services:
  prometheus:
    image: prom/prometheus:v3.5.0
    container_name: prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
      - --web.enable-lifecycle                 # allows POST /-/reload
    volumes:
      - ./prometheus:/etc/prometheus:ro
      - prometheus-data:/prometheus
    ports:
      - "127.0.0.1:9090:9090"
    extra_hosts:
      - "host.docker.internal:host-gateway"    # reach node-exporter on the host network
    networks: [monitoring]
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.28.1
    container_name: alertmanager
    command:
      - --config.file=/etc/alertmanager/alertmanager.yml
      - --storage.path=/alertmanager
    volumes:
      - ./alertmanager:/etc/alertmanager:ro
      - alertmanager-data:/alertmanager
    ports:
      - "127.0.0.1:9093:9093"
    networks: [monitoring]
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:v1.9.1
    container_name: node-exporter
    command:
      - --path.rootfs=/host
      - --collector.systemd                        # node_systemd_unit_state: failed units
      - --collector.textfile.directory=/textfile   # *.prom files written by scripts (backups...)
    network_mode: host                             # real host interfaces; listens on :9100
    pid: host
    volumes:
      - /:/host:ro,rslave
      - /run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket:ro   # the systemd collector uses D-Bus
      - /var/lib/node_exporter/textfile:/textfile:ro
    restart: unless-stopped

  cadvisor:
    image: ghcr.io/google/cadvisor:v0.60.5   # new registry; tags before ~v0.54 (e.g. gcr.io/cadvisor/cadvisor:v0.49.1) see no containers on Docker Engine 29
    container_name: cadvisor
    privileged: true
    devices:
      - /dev/kmsg
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "127.0.0.1:8080:8080"
    networks: [monitoring]
    restart: unless-stopped

  blackbox:
    image: prom/blackbox-exporter:v0.27.0
    container_name: blackbox
    command:
      - --config.file=/etc/blackbox/blackbox.yml
    volumes:
      - ./blackbox:/etc/blackbox:ro
    ports:
      - "127.0.0.1:9115:9115"
    networks: [monitoring]
    restart: unless-stopped

  grafana:
    image: grafana/grafana:12.0.2
    container_name: grafana
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GF_ADMIN_PASSWORD:?set it in .env}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana-data:/var/lib/grafana
    ports:
      - "127.0.0.1:3001:3000"
    networks: [monitoring]
    restart: unless-stopped

  alert-sink:
    image: python:3.12-alpine
    container_name: alert-sink
    command: ["python3", "-u", "/sink/sink.py"]
    volumes:
      - ./alert-sink:/sink:ro
    networks: [monitoring]
    restart: unless-stopped

networks:
  monitoring:
    name: monitoring
    ipam:
      config:
        - subnet: 172.30.0.0/24       # pick a range that does not clash with your LAN or VPN

volumes:
  prometheus-data:
  alertmanager-data:
  grafana-data:
```

```bash
cd ~/monitoring
docker compose config --quiet && echo "compose file OK"
docker compose config --services
```

```
compose file OK
alert-sink
alertmanager
blackbox
cadvisor
grafana
node-exporter
prometheus
```

**What it means:** Compose parsed the file, resolved `${GF_ADMIN_PASSWORD}` from `.env`, and
found seven services. Note the design choices: node-exporter uses the host network (so it
sees the real interfaces) and is reached by Prometheus through `host.docker.internal`;
everything else talks over the `monitoring` network by container name; only loopback ports
are published.

**Why this step (now):** writing all services first lets Compose validate the whole file
(indentation, variables, the `.env` value) before anything starts. The `127.0.0.1` bindings
decide the security posture: Docker-published ports skip UFW, so binding to loopback is
what keeps Prometheus, Alertmanager and Grafana off your LAN.

**Next step:** if the file is OK and lists seven services → Step 3. If Compose reports
`required variable GF_ADMIN_PASSWORD is missing a value` → recreate `.env` (Step 1). If it
reports `yaml: line N` → fix the indentation at that line (spaces only, no tabs).

### Step 3 — Write the configuration files

**Goal:** Prometheus jobs and rules, Alertmanager routing, blackbox modules, the alert sink
and Grafana provisioning, each validated before the first start.

```yaml
# ~/monitoring/prometheus/prometheus.yml — lab subset of the §11 example
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']

  - job_name: node
    static_configs:
      - targets: ['host.docker.internal:9100']
        labels:
          instance: lab-vm1                 # a readable name instead of host.docker.internal:9100

  - job_name: cadvisor
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: alertmanager
    static_configs:
      - targets: ['alertmanager:9093']

  - job_name: blackbox-http
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://grafana:3000/api/health  # always reachable inside the lab
          # - https://app.example.com       # add sites you own
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox:9115
```

Copy the complete rule set from §12 ("Alert rules that earn their page") into
`~/monitoring/prometheus/rules/node.yml`. Then the Alertmanager, blackbox and sink files:

```yaml
# ~/monitoring/alertmanager/alertmanager.yml — lab version of the §12 routing
route:
  receiver: lab-sink
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - matchers: ['severity="critical"']
      receiver: lab-sink
      repeat_interval: 1h

inhibit_rules:
  - source_matchers: ['severity="critical"']
    target_matchers: ['severity="warning"']
    equal: ['instance']

receivers:
  - name: lab-sink
    webhook_configs:
      - url: http://alert-sink:5001/
        send_resolved: true
```

```yaml
# ~/monitoring/blackbox/blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      preferred_ip_protocol: ip4
      # for sites signed by a private CA (Harbor-style), mount the CA file and add:
      # tls_config:
      #   ca_file: /etc/blackbox/private-ca.crt
  tcp_connect:
    prober: tcp
    timeout: 5s
```

```python
# ~/monitoring/alert-sink/sink.py — prints every Alertmanager notification (lab only)
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class Sink(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        for a in body.get("alerts", []):
            print(a["status"].upper(), a["labels"].get("alertname"), a["labels"].get("instance", ""),
                  "-", a["annotations"].get("summary", ""), flush=True)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):    # silence the default access log
        pass

HTTPServer(("0.0.0.0", 5001), Sink).serve_forever()
```

For Grafana, save the data source file from §13 as
`grafana/provisioning/datasources/prometheus.yml`, and add a dashboard provider:

```yaml
# ~/monitoring/grafana/provisioning/dashboards/files.yml
apiVersion: 1
providers:
  - name: lab-files
    folder: Lab
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

Validate with the same image versions you will run:

```bash
cd ~/monitoring
docker run --rm -v "$PWD/prometheus:/etc/prometheus:ro" --entrypoint promtool \
  prom/prometheus:v3.5.0 check config /etc/prometheus/prometheus.yml
docker run --rm -v "$PWD/alertmanager:/etc/alertmanager:ro" --entrypoint amtool \
  prom/alertmanager:v0.28.1 check-config /etc/alertmanager/alertmanager.yml
```

```
Checking /etc/prometheus/prometheus.yml
  SUCCESS: 1 rule files found
 SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax

Checking /etc/prometheus/rules/node.yml
  SUCCESS: 11 rules found

Checking '/etc/alertmanager/alertmanager.yml'  SUCCESS
Found:
 - global config
 - route
 - 1 inhibit rules
 - 1 receivers
 - 0 templates
```

**What it means:** the Prometheus config, its rule file (all 11 rules from §12) and the
Alertmanager config are syntactically valid for exactly the versions in the compose file.

**Why this step (now):** a broken config makes Prometheus or Alertmanager exit at start, or,
on a later reload, silently keep the old config (§11). Validating before the first start
separates "my YAML is wrong" from "the network is wrong", which otherwise look the same: a
restarting container.

**Next step:** if both checks say SUCCESS → Step 4. If promtool reports
`could not parse expression` → fix that rule (§12 "How it breaks"). If amtool fails →
check the indentation of `routes:` and `receivers:`, and that every receiver named in a
route exists.

### Step 4 — Start the stack and check every target

**Goal:** all containers running and every scrape target `up`.

```bash
cd ~/monitoring
# only if UFW is active (sudo ufw status): let the monitoring network, and nothing else, reach node_exporter
sudo ufw allow from 172.30.0.0/24 to any port 9100 proto tcp comment 'prometheus -> node_exporter (lab)'
docker compose up -d
docker compose ps --format 'table {{.Name}}\t{{.Status}}'
curl -s http://127.0.0.1:9090/api/v1/targets \
  | jq -r '.data.activeTargets[] | [.labels.job, .labels.instance, .health, .lastError] | @tsv'
```

```
NAME            STATUS
alert-sink      Up 40 seconds
alertmanager    Up 40 seconds
blackbox        Up 40 seconds
cadvisor        Up 40 seconds (healthy)
grafana         Up 40 seconds
node-exporter   Up 40 seconds
prometheus      Up 40 seconds

prometheus	localhost:9090	up
node	lab-vm1	up
cadvisor	cadvisor:8080	up
alertmanager	alertmanager:9093	up
blackbox-http	http://grafana:3000/api/health	up
```

**What it means:** every container is up and every target is `up` with an empty
`lastError`. A container that keeps failing shows `Restarting (1)`; a failing target shows
its error text in the fourth column (decode it with the §11 table). Without UFW, port 9100
is reachable from your LAN: acceptable on an isolated homelab, otherwise add the rule or a
firewall in front.

**Why this step (now):** the targets list is the single place that proves the whole data
path (Docker DNS, firewall, exporter, Prometheus). Checking it before building dashboards
saves you from debugging an empty panel that is really a down target.

**Next step:** if everything is up → Step 5. If `node` is down with
`context deadline exceeded` → the UFW rule is missing or the subnet differs
(`docker network inspect monitoring`). If a container restarts →
`docker compose logs --tail 30 SERVICE`; on Docker Engine 29+ a log line such as
`client version 1.41 is too old` means that image's Docker client is too old for the
daemon: upgrade the image. If `cadvisor` is up but later panels lack `name`
labels → check its mounts and its version against your Docker Engine (§11).

### Step 5 — Open Grafana and import Node Exporter Full

**Goal:** see the data in Grafana and get a complete host dashboard in five minutes.

```bash
# on your laptop: tunnel the three UIs (they listen on the VM's loopback only)
ssh -N -L 3001:127.0.0.1:3001 -L 9090:127.0.0.1:9090 -L 9093:127.0.0.1:9093 USER@LAB_VM
# browse http://127.0.0.1:3001 and log in as admin with the password from ~/monitoring/.env

# on the VM: Grafana healthy, provisioning applied?
curl -s http://127.0.0.1:3001/api/health
docker logs grafana 2>&1 | grep -iE 'provision|error' | tail -5
```

```
{
  "database": "ok",
  "version": "12.0.2"
}
logger=provisioning.datasources level=info msg="inserting datasource from configuration" name=Prometheus uid=prometheus
logger=provisioning.dashboard level=info msg="starting to provision dashboards"
```

Then in Grafana: Dashboards → New → Import → `1860` → Load → choose the Prometheus data
source → Import. Pick job `node` and host `lab-vm1` in its variables.

**What it means:** Grafana's database is fine and the provisioned Prometheus data source was
created from your file, so the setup is reproducible. The dashboard import needs the VM to
reach grafana.com.

**Why this step (now):** seeing the data before building alerts confirms that the queries
your alerts depend on return what you expect. Node Exporter Full gives a complete USE view
of the host that you can compare with the 60-second checklist output (§2).

**Next step:** if the panels show data → Step 6. If they show `No data` → make the
dashboard's job and instance variables match `node` and `lab-vm1` (§13 table). If "Save &
test" fails with `connection refused` → the data source points at `localhost` (§13). If the
import cannot reach grafana.com → download the dashboard JSON on a machine with internet
access and use "Upload dashboard JSON file", or save it into `grafana/dashboards/`.

### Step 6 — Fire the drill alerts

**Goal:** prove the two Ops Ladder alerts (disk above 85%, failed systemd unit) fire, reach
Alertmanager, notify, and later resolve.

> ⚠️ The fill step is for a test VM only. A full root filesystem stops logging, package
> installs and databases. The commands below stop at about 88% used; never go further, and
> remove the file in Step 7.

```bash
# terminal 1: watch notifications arrive
docker logs -f alert-sink

# terminal 2, (a) a failed systemd unit
printf '[Unit]\nDescription=lab unit that fails\n[Service]\nExecStart=/bin/false\n' \
  | sudo tee /etc/systemd/system/lab-fail.service >/dev/null
sudo systemctl daemon-reload && sudo systemctl start lab-fail.service

# (b) fill / to about 88% used (test VM only)
read -r size used <<<"$(df --output=size,used -B1 / | tail -1)"
fill=$(( size * 88 / 100 - used )); echo "will allocate $(( fill / 1024 / 1024 )) MiB"
[ "$fill" -gt 0 ] && sudo fallocate -l "$fill" /var/tmp/lab-fill.bin
df -h /

# watch the alert states: inactive → pending → firing
curl -s http://127.0.0.1:9090/api/v1/alerts \
  | jq -r '.data.alerts[] | [.labels.alertname, .state, .labels.instance] | @tsv'
```

The rules wait `for: 5m` (failed unit) and `for: 10m` (disk). For a faster lab cycle,
lower both to `1m` in `rules/node.yml` and reload with
`curl -X POST http://127.0.0.1:9090/-/reload`; restore them afterwards.

```
SystemdUnitFailed	pending	lab-vm1
DiskSpaceAbove85Percent	pending	lab-vm1
...
SystemdUnitFailed	firing	lab-vm1
DiskSpaceAbove85Percent	firing	lab-vm1

FIRING SystemdUnitFailed lab-vm1 - lab-fail.service failed on lab-vm1
FIRING DiskSpaceAbove85Percent lab-vm1 - Filesystem / on lab-vm1 is 93% full
```

**What it means:** both alerts went pending, stayed true for their `for:` period, fired,
were routed by Alertmanager and reached the sink. The disk shows about 93% although you
filled to 88% of its size: the rule uses `avail` bytes, which exclude the root-reserved
blocks (5% by default on ext4: 12% free minus 5% reserved leaves 7% available), so it sees
the disk the way an unprivileged application does; `df -h` reports the same 93%. With a
different reserve (`tune2fs -l` shows `Reserved block count`) or on XFS the number differs. About 30 minutes later
`DiskWillFillIn4Hours` may fire too: a sudden step down looks like a steep trend to
`predict_linear`, a known false positive worth discussing in your notes.

**Why this step (now):** an alert you have never seen fire is an assumption. Firing it on
purpose tests the whole chain (collector → rule → Alertmanager route → receiver) and shows
the real detection time: `for:` plus the scrape and evaluation intervals plus
`group_wait`.

**Next step:** if both alerts reach the sink as FIRING → Step 7. If they fire in Prometheus
but the sink prints nothing → `docker logs alertmanager` for notify errors and check the
receiver URL. If SystemdUnitFailed never goes pending → `curl -s http://127.0.0.1:9100/metrics | grep lab-fail`:
no output means the systemd collector cannot reach D-Bus (check the socket mount). If the
disk alert stays inactive → `df -T /`: the rule only matches `ext4` and `xfs`.

### Step 7 — Resolve, clean up and keep the lab as code

**Goal:** see the RESOLVED notifications, remove the drill leftovers, and keep the
configuration in Git.

```bash
sudo rm /var/tmp/lab-fill.bin && df -h /
sudo systemctl reset-failed lab-fail.service
sudo rm /etc/systemd/system/lab-fail.service && sudo systemctl daemon-reload
# a few minutes later the sink prints RESOLVED lines (send_resolved: true)
docker logs --since 10m alert-sink | grep RESOLVED
# keep the lab as code; .env stays out of Git
cd ~/monitoring && git init -q && printf '.env\n' > .gitignore \
  && git add -A && git commit -qm 'homelab monitoring stack' && git log --oneline | head -1
```

```
RESOLVED SystemdUnitFailed lab-vm1 - lab-fail.service failed on lab-vm1
RESOLVED DiskSpaceAbove85Percent lab-vm1 - Filesystem / on lab-vm1 is 93% full
3c1d2e7 homelab monitoring stack
```

**What it means:** both alerts resolved by themselves once their causes were gone (the
summary still shows the last value seen). The stack is now a Git repository that you can
deploy on any VM.

**Why this step (now):** cleaning up at once is part of the drill: a forgotten fill file is
how a lab exercise becomes a real incident. Committing the configuration turns the lab into
portfolio material and the starting point for an Ansible role
([CI/CD, IaC & SRE module](33-learn-cicd-iac-sre.md)).

**Next step:** if the RESOLVED lines arrived → do the §18 exercise with these dashboards
open. If an alert stays firing → check that its condition really cleared (`df -h /`,
`systemctl --failed`). If `git commit` complains about your identity → set `user.name` and
`user.email` once with `git config --global`. To remove the whole lab → see Rollback below.

**Decision tree (lab troubleshooting)**

```
 Panel empty or alert silent?
 ├─ Target down on the targets page?
 │   ├─ yes → read lastError
 │   │   ├─ connection refused ......... exporter not running / wrong port     → docker compose ps; ss -ltnp
 │   │   ├─ context deadline exceeded .. firewall (UFW rule for 9100) / route  → ufw status; docker network inspect monitoring
 │   │   └─ no such host ............... container not on the monitoring network → networks: in compose
 │   └─ no → does the query return data in the Prometheus UI?
 │       ├─ no  → metric missing: collector disabled (--collector.systemd), wrong mounts
 │       └─ yes → Grafana side: data source URL, dashboard variables, time range
 └─ Alert firing in Prometheus but no notification?
     ├─ not visible in Alertmanager → alerting: block or address in prometheus.yml
     └─ visible → silenced or inhibited? (amtool alert query; silences) → else receiver error in docker logs alertmanager
```

**Fix & verify**

- After any config change, validate first (Step 3), then reload: `curl -X POST http://127.0.0.1:9090/-/reload` for Prometheus, `docker compose restart alertmanager` for Alertmanager.
- Verify with the targets query (Step 4) and one deliberate alert (Step 6). A config you have not seen fire is not verified.

**Rollback**

Stop the lab but keep its history (safe default):

```bash
cd ~/monitoring
docker compose down                 # removes containers and the network, keeps the data volumes
sudo ufw status numbered            # then remove the 9100 rule: sudo ufw delete NUMBER
```

> ⚠️ `docker compose down -v` also deletes the Prometheus, Alertmanager and Grafana data
> volumes: all metric history and any dashboard you did not export. Use it only for a
> deliberate clean slate, after exporting dashboards into `grafana/dashboards/`.

**Prevent it next time**

- Keep the stack in Git and deploy it with Ansible or as a Dokploy Compose app, so every new server has monitoring on day one.
- Pin image versions and upgrade on purpose, after reading release notes (Prometheus 2 → 3 changed several defaults).
- Monitor the monitoring: a dead Prometheus cannot alert about itself, so probe Prometheus and Alertmanager from a second machine.
- Provision every dashboard from files instead of relying on the `grafana-data` volume.

---

## 18. stress-ng exercise: name the saturated resource

> 📚 **Study path:** 1) Note: the 60-second checklist (§2) and the [slow system playbook](23-playbook-slow-system.md) · 2) Read: [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) · 3) KodeKloud: *Linux Challenges* (free, timed scenario challenges) ([course](https://kodekloud.com/courses/linux-challenges)) · 4) Practice: three rounds of this exercise a week until each verdict takes under five minutes, plus [SadServers scenarios](https://sadservers.com/scenarios).

**Level:** [L2 · Mid] for the checklist itself · [L4 · Lead/SRE] as a timed drill with dashboards

The Ops Ladder drill: load a VM with stress-ng, run the 60-second checklist, and name the
saturated resource *before* you look at the flags you used. Here a script picks the load at
random and hides the answer, so you practise reading numbers instead of remembering what
you typed. Use a test VM with 2–4 vCPU and swap configured, ideally with the §17 stack
running so you can compare the shell with the dashboards.

> ⚠️ Test VM only. The memory round deliberately pushes the VM into swap; on a VM without
> swap it can trigger the OOM killer instead. Never run this on a shared or production
> host.

### Step 1 — Start a hidden load

**Goal:** a random, unknown load runs for five minutes and the answer is stored where you
will not look yet.

```bash
sudo tee /usr/local/bin/mystery-load >/dev/null <<'EOF'
#!/usr/bin/env bash
# Starts one random load for 5 minutes and records the answer in a root-only file.
set -euo pipefail
N=$(nproc)
AVAIL_MB=$(free -m | awk '/^Mem:/{print $7}')
case $(( RANDOM % 6 )) in
  0) ANSWER="CPU saturation"
     CMD=(stress-ng --cpu $(( N * 2 )) --timeout 300s) ;;
  1) ANSWER="memory (swapping)"
     CMD=(stress-ng --vm 1 --vm-bytes $(( AVAIL_MB * 110 / 100 ))M --vm-keep --timeout 300s) ;;
  2) ANSWER="disk (synchronous writes)"
     CMD=(stress-ng --hdd 2 --hdd-opts dsync --temp-path /var/tmp --timeout 300s) ;;
  3) ANSWER="kernel %sys (context switches)"
     CMD=(stress-ng --switch "$N" --timeout 300s) ;;
  4) ANSWER="network stack (%soft and %sys, loopback TCP)"
     CMD=(stress-ng --sock "$N" --timeout 300s) ;;
  5) ANSWER="cgroup CPU throttling (host looks idle)"
     CMD=(systemd-run --scope --unit=mystery-throttle -p CPUQuota=20% stress-ng --cpu "$N" --timeout 300s) ;;
esac
echo "$(date -Is) ${ANSWER} :: ${CMD[*]}" >> /root/mystery-answers.log
chmod 600 /root/mystery-answers.log
nohup "${CMD[@]}" >/dev/null 2>&1 &
echo "A load is running for 5 minutes. Start the clock and begin Step 2."
EOF
sudo chmod 755 /usr/local/bin/mystery-load
sudo mystery-load
```

```
A load is running for 5 minutes. Start the clock and begin Step 2.
```

**What it means:** something is running and you do not know what. The answer and the exact
command are in `/root/mystery-answers.log`, readable only by root, for Step 7.

**Why this step (now):** naming a resource you already know is memory, not diagnosis. A
hidden load forces you to reach the verdict from the numbers, which is exactly what the
60-second checklist is for.

**Next step:** start a five-minute timer → Step 2. Do not run `ps`, `top` or a plain
`pidstat` yet: stress-ng names its workers after the stressor (for example
`stress-ng-cpu`), which gives the answer away. Step 4 shows how to hide the name column.

### Step 2 — Read uptime, dmesg and PSI

**Goal:** know whether load is rising, whether the kernel already complained, and which
resource has tasks waiting.

```bash
uptime
sudo dmesg -T | tail -n 15
grep -H . /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
```

```
 11:02:41 up 3 days,  1:12,  2 users,  load average: 4.12, 1.33, 0.52
/proc/pressure/cpu:some avg10=0.31 avg60=0.12 avg300=0.03 total=812345
/proc/pressure/cpu:full avg10=0.00 avg60=0.00 avg300=0.00 total=0
/proc/pressure/memory:some avg10=41.87 avg60=18.20 avg300=4.11 total=21873311
/proc/pressure/memory:full avg10=30.02 avg60=12.71 avg300=2.80 total=15982344
/proc/pressure/io:some avg10=38.40 avg60=17.02 avg300=3.95 total=20117765
/proc/pressure/io:full avg10=29.11 avg60=12.30 avg300=2.64 total=15002210
```

**What it means:** on this 2-vCPU VM the load jumped from 0.5 to 4.1 within a minute
(1-minute value far above the 15-minute one: it just started). `dmesg` printed nothing new,
so no OOM kill, hung task or I/O error yet. PSI already points somewhere: memory `full`
30% and io `full` 29% while CPU pressure is near zero. Memory and I/O pressure rising
together usually means swapping or heavy reclaim. Other rounds move other lines; compare
with the answer key at the end of this area.

**Why this step (now):** `uptime` and `dmesg` cost nothing and catch the loud failures (OOM
kills, hung tasks, disk errors) before you read any rates; PSI adds a one-line "who is
waiting" summary per resource.

**Next step:** whatever PSI suggests, one signal is a hypothesis, not a verdict → Step 3.
If `dmesg` shows `Out of memory: Killed process` → note it as evidence for memory and still
continue to Step 3 to confirm.

### Step 3 — Split the load with vmstat

**Goal:** see whether the load is runnable tasks (CPU), blocked tasks (I/O) or swapping.

```bash
vmstat 1 6
```

```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0 1302336  98012   1204  61244    0    0   140   210  512  880  3  2 94  1  0
 2  3 1325416  71240    980  48812 18240 41320 19112 41500 3120 4410  6 18 21 55  0
 1  4 1350718  69880    912  41120 22410 47712 22650 47790 3398 4821  5 21 17 57  0
 2  3 1375830  70112    880  38770 20118 45230 20304 45310 3301 4710  6 19 19 56  0
 1  4 1400064  68990    860  36410 19876 44110 19950 44201 3288 4699  5 20 18 57  0
 2  3 1425063  69320    845  35102 21003 46002 21110 46118 3310 4733  6 19 20 55  0
```

**What it means:** ignore the rates in the first line (averages since boot; the memory
columns are current values). `si` and `so` move 20–47 MB every second, `swpd` grows by
the difference (about 25 MB/s: it can never grow faster than `so`), `cache` shrinks, `b` shows 3–4 blocked tasks, `wa` is about 55%
and `r` stays small. That is memory saturation: the working set does not fit in RAM, and
the swap traffic causes the iowait. Other rounds look different: CPU → `r` far above
nproc and `us` near 100; disk → `b`, `wa` and `bo` high with `si`/`so` at zero; the %sys
round → `sy` high and `cs` in the hundreds of thousands; the network-stack round → `sy`,
`in` and `cs` up (the softirq share shows in mpstat); the throttling round → almost
everything idle.

**Why this step (now):** vmstat separates the three classic causes of high load (CPU queue,
I/O blocking, swapping) on one screen. It is the first fork of the slow-system decision
tree.

**Next step:** if `si`/`so` are non-zero → memory: confirm with `free -m` in Step 5. If `r`
is far above nproc → CPU: Step 4. If `b` and `wa` are high without swapping → disk: Step 5
(iostat). If `sy` is high or nothing stands out → Step 4 for the per-CPU and per-process
split.

### Step 4 — Per-CPU and per-process view

**Goal:** see how CPU time splits per core and per process, without revealing process
names.

```bash
LC_ALL=C mpstat -P ALL 1 3 | grep -E '^Average'
# pidstat with the last column (Command) blanked, busiest first
LC_ALL=C pidstat 1 3 | awk '/^Average/ {$NF=""; print}' | sort -k8 -rn | head -5 | column -t
```

```
Average:     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
Average:     all    5.53    0.00   19.85   55.78    0.00    0.25    0.00    0.00    0.00   18.59
Average:       0    6.06    0.00   21.21   52.53    0.00    0.00    0.00    0.00    0.00   20.20
Average:       1    5.00    0.00   18.00   59.00    0.00    1.00    0.00    0.00    0.00   17.00
Average:  0  4182  3.00  21.00  0.00  9.00  24.00  -
Average:  0  64    0.00  4.00   0.00  0.00  4.00   -
```

**What it means:** no core is computing much (`%usr` about 6%); the time goes to `%sys`
(page-fault and reclaim work) and iowait. One process uses about 24% CPU, almost all of it
system time, and a kernel thread (PID 64, name hidden; it is `kswapd`) works for it.
Consistent with memory pressure. For comparison: the CPU round shows every core near 100%
`%usr`; the %sys round shows high `%sys` without iowait; the network-stack round shows
`%soft` and `%sys`; the throttling round shows a few processes that together never exceed
about 20% of one CPU.

**Why this step (now):** the per-core split tells you whether the work is computation,
kernel work or waiting, and the per-process view confirms that one workload, not the whole
box, is responsible, still without the name giving the answer away.

**Next step:** if `%usr` is near 100% on all cores → CPU saturation, confirm in Step 6. If
total CPU is low but a group of processes looks capped at a fixed share → check cgroups
with `systemd-cgtop -d 2` and the `cpu.stat` of the busiest cgroup (§4 throttling), then
Step 6. Otherwise → Step 5 for disk, memory and network.

### Step 5 — Disk, memory and network

**Goal:** finish the USE sweep so that a second problem cannot hide behind the first.

```bash
iostat -xz 1 3
free -m
sar -n DEV 1 3 | grep Average
sar -n ETCP 1 3 | grep Average
```

```
Device      r/s      w/s     rkB/s     wkB/s  r_await  w_await  aqu-sz  %util      (columns trimmed)
vda     4980.00 11402.00  19920.00  45608.00     2.10     2.40   38.10  99.80

               total        used        free      shared  buff/cache   available
Mem:            3911        3702          68           2         141          64
Swap:           2047        1460         587

Average:        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
Average:           lo      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
Average:        ens18      4.33      3.67      0.31      0.42      0.00      0.00      0.00      0.00
Average:     atmptf/s  estres/s retrans/s isegerr/s   orsts/s
Average:         0.00      0.00      0.00      0.00      0.00
```

**What it means:** the disk is 99.8% busy with about 5,000 reads and 11,400 writes per
second, but together with `si`/`so` from vmstat this is swap traffic, not application I/O.
`available` is 64 MB and 1.4 GB of swap is in use and growing. The network is idle with no
retransmits. The verdict is forming: memory saturation, with the disk saturated as a
consequence.

**Why this step (now):** USE means every resource, every time. Here the disk also looks
saturated; only the combination with `si`/`so` and `available` shows it is a consequence,
not the cause, and that changes the fix (less memory demand or more RAM, not faster
storage).

**Next step:** write your one-sentence verdict now → Step 6 to confirm it on the dashboard.
If the disk is saturated with no swapping → the verdict is disk. If `retrans/s` or `%soft`
stand out → the network stack.

### Step 6 — Confirm on the dashboard

**Goal:** confirm the verdict with the §17 stack and write it down before the reveal.

```bash
# the same signals as PromQL (q() is the helper from §11)
q 'rate(node_vmstat_pswpin[1m]) + rate(node_vmstat_pswpout[1m])'
q 'rate(node_pressure_memory_stalled_seconds_total[1m])'
q '100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])))'
q 'rate(node_disk_io_time_seconds_total{device="vda"}[1m])'
```

```
{"instance":"lab-vm1","job":"node"}	16712.4
{"instance":"lab-vm1","job":"node"}	0.297
{"instance":"lab-vm1"}	81.2
{"device":"vda","instance":"lab-vm1","job":"node"}	0.998
```

Then write the verdict in this form:

```
Verdict:    MEMORY saturated (swap in+out ≈ 65 MB/s, PSI memory full ≈ 30%, available 64 MB)
Consequence: disk vda 99.8% busy with swap I/O; CPU time mostly iowait and %sys
Evidence:   vmstat si/so, free -m, iostat, PSI, Grafana memory and swap panels
Confidence: high          Time to verdict: 4 min 10 s
```

**What it means:** the dashboard and the shell agree: about 16,700 pages per second of swap
(≈ 65 MB/s), memory stalled 30% of the time, the disk busy all the time. "CPU busy 81%"
is mostly iowait and system time: a CPU-busy number on its own would have sent you the
wrong way.

**Why this step (now):** writing the verdict before the reveal is the whole point. It is the
habit you need in a real incident, where nobody reveals the answer. Checking the dashboard
also proves the §17 stack would have shown this to someone who never logged in.

**Next step:** verdict written → Step 7. If the shell and the dashboard disagree → check
the time range and the `rate` window (`[1m]` against `[5m]`) before trusting either, then
go back to Step 3.

### Step 7 — Reveal, score and repeat

**Goal:** compare your verdict with the answer, then run more rounds.

```bash
sudo tail -n 1 /root/mystery-answers.log
ps -eo pid,stat,comm | grep stress-ng | head -3      # now you may look at the names
```

```
2026-10-03T11:02:12+00:00 memory (swapping) :: stress-ng --vm 1 --vm-bytes 2112M --vm-keep --timeout 300s
   4181 S    stress-ng
   4182 R    stress-ng-vm
```

**What it means:** the answer matches the verdict. Score the round: right resource (yes or
no), time to verdict, and your first wrong guess if you had one.

**Why this step (now):** immediate feedback is what makes the drill work, and the
five-line note (symptom, first wrong guess, deciding evidence, fix, what to check first
next time) turns each round into an entry in your incident notebook, as the Ops Ladder's
weekly rhythm asks.

**Next step:** if the verdict was right in under five minutes → run another round
(`sudo mystery-load` after the current one ends) until you have seen all six answers. If it
was wrong → find the step where the evidence pointed elsewhere and re-read that topic (§4
CPU and throttling, §5 memory, §6 disk, §7 network). After six correct rounds → the timed
version in §19.

**Answer key: what each round looks like**

| Round | vmstat | mpstat / pidstat | iostat / free / sar | PSI | Verdict |
|-------|--------|------------------|---------------------|-----|---------|
| CPU | `r` about 2× nproc, `us` near 100, `id` 0 | Every core near 100% `%usr` | Disk and network idle | cpu `some` high | CPU saturated |
| Memory | `si`/`so` non-zero, `swpd` grows, `wa` high | `%sys` and `%iowait`, little `%usr` | `available` tiny, swap grows, disk busy with swap | memory and io `full` high | Memory saturated; the disk is a consequence |
| Disk | `b`, `wa` and `bo` high, `si`/`so` zero | `%iowait` high, low `%usr` | `aqu-sz` and `w_await` high, many flushes (`f/s`) | io high, memory low | Disk saturated by synchronous writes |
| %sys | `cs` in the hundreds of thousands, `sy` high | `%sys` high on all cores | Disk and network idle | cpu `some` moderate | Kernel overhead from context switches |
| Network stack | `in`, `cs` and `sy` up | `%soft` and `%sys` up | `lo` busy in `sar -n DEV`, NIC idle | cpu `some` moderate | Loopback TCP load: the network stack, not the NIC |
| Throttling | Mostly idle | A few processes capped at about 20% of one CPU in total | Everything idle | Host PSI low | A cgroup CPU limit, visible only in `cpu.stat` |

**Decision tree**

```
 Load high or "server slow"?
 ├─ vmstat si/so non-zero, sustained ................ MEMORY (swapping) → free -m, ps --sort=-rss (§5)
 ├─ vmstat r far above nproc, us+sy near 100 ........ CPU saturated → pidstat, perf top (§4)
 ├─ vmstat b and wa high, no swapping ............... DISK → iostat -xz (aqu-sz, await), pidstat -d (§6)
 ├─ sy high and cs very high ........................ kernel overhead → pidstat -w, strace -c (§4)
 ├─ %soft high or retrans/s above 0 ................. NETWORK stack → sar -n DEV/ETCP, ss -tin (§7)
 └─ host mostly idle but the app is slow ............ cgroup limits → systemd-cgtop, cpu.stat, memory.events (§4, §5)
                                                      or waiting on something else → pools, DB, upstream (§8)
```

**Fix & verify**

- In the drill the load stops by itself after 300 s (`--timeout`). Verify with `vmstat 1 5` that `r`, `b` and `si`/`so` are back at your idle baseline and that PSI `avg10` falls to near zero.
- In a real incident the fix follows the verdict: stop or reschedule the job, reduce memory demand or add RAM, move I/O to faster storage, raise or remove a wrong cgroup limit. Verify with the same commands that produced the evidence.

**Rollback**

To end a round early on the test VM, stop it gracefully and check that nothing is left:

```bash
sudo systemctl stop mystery-throttle.scope 2>/dev/null   # only exists in the throttling round
sudo pkill -TERM -x stress-ng                             # the parent stops its workers and removes its temp files
pgrep -a stress-ng || echo "no stress-ng left"
ls -d /var/tmp/tmp-stress-ng-* 2>/dev/null || echo "no temp files left"
swapon --show
```

Swap may stay partly used after the memory round. That is harmless (§5): pages come back
only when needed, and `si`/`so` at zero is what matters.

**Prevent it next time**

- Keep sysstat history and the §17 stack on every server, so the first minute of evidence also exists after the fact.
- Alert on saturation that hurts (PSI memory, swap activity, disk-full prediction) and on SLO burn, not on raw CPU (§15).
- Set memory and CPU limits on purpose for every container and service, and watch `oom_kill` counts and throttling ratios.
- Repeat the drill monthly; it keeps the 60-second checklist automatic.

---

## 19. Self-check and exit test

Prove the module at your stage. Answer the questions without notes first, then check
against the section in brackets. Do the practical tasks on a test VM with a timer, and
repeat any you fail on another day.

### Questions for Mid-level

**Level:** [L2 · Mid]

1. What is the difference between utilization and saturation? Give one Linux command for each, for the CPU and for a disk. (§1, §2)
2. Why is mean latency misleading, and what does a p99 of exactly 30 s usually point to? (§1)
3. Name the ten commands of the 60-second checklist, in order, and what each one is for. (§2)
4. A 4-vCPU server shows a load average of 12 with 85% idle CPU. What do you check next, and why? (§4)
5. `free -m` shows 150 MB free and 5 GB available. Is the server short of memory? (§5)
6. How do you tell a global OOM kill from a cgroup OOM kill in the kernel log? (§5)
7. iostat shows `%util` 100% on an NVMe drive with `r_await` 0.2 ms. Is the disk saturated? (§6)
8. iperf3 reports 94 Mbit/s between two servers with gigabit NICs. What is your first suspect? (§7)
9. Where does Docker keep a container's logs with the default driver, and how do you stop them filling the disk? (§14)

### Questions for Senior

**Level:** [L3 · Senior]

1. A container is slow while its host is idle. Which file proves CPU throttling, and which fields do you read? (§4)
2. Use Little's law to explain why `MaxRequestWorkers 150` in front of `pm.max_children 5` with 1-second requests caps throughput at 5 req/s. (§8)
3. A JVM in a 1 GiB container is OOM-killed although its maximum heap is 512 MB. Give two possible reasons. (§8)
4. Why must a fio write test never target a block device such as `/dev/sdb`, and what makes a fio read test measure RAM instead of the disk? (§6)
5. A single backup stream to a site 60 ms away is stuck at 150 Mbit/s on an idle 1 Gbit/s link. Compute the BDP and name the likely limit and the field in `ss -tin` that proves it. (§7)
6. What is the difference between a closed-model and an open-model load test, and why does it matter for p99? (§9)
7. A server's peak hour runs at 72% CPU and traffic grows 15% per quarter. In which quarter does the peak pass 85%, and what do you recommend now? (§16)
8. Why should a structured log line carry a request ID, and where should that ID be created? (§14)

### Questions for Lead/SRE

**Level:** [L4 · Lead/SRE]

1. Why do alert rules use `rate()` rather than `irate()`, and why must you `rate` before you `sum`? (§11)
2. A developer adds `user_id` as a label on a request counter. What happens to Prometheus, and how do you stop it at scrape time? (§10)
3. Write the PromQL for "the root filesystem will be full within 4 hours". Which false positive does it have, and how do you guard against it? (§12, §17)
4. Define an availability SLI and a latency SLI for an app behind Traefik. (§15)
5. With a 99.9% SLO over 30 days, how much of the error budget does a 15-minute total outage consume? (§15)
6. Which of these should page: high load, disk 90% full, a fast SLO burn, a certificate expiring in two days, an OOM kill of a nightly batch job? Justify each. (§15)
7. Loki or Elasticsearch for a small on-prem estate with Prometheus already running: which, and why? (§14)
8. What does a trace show that logs with request IDs do not? (§14)

### Timed practical tasks

| # | Task (test VM or homelab only) | Stage | Time limit | Pass when |
|---|--------------------------------|-------|------------|-----------|
| 1 | Run the 60-second checklist on an idle VM and save a baseline note | [L2 · Mid] | 5 min | All ten commands run, baseline saved with the date |
| 2 | Three `mystery-load` rounds (§18) | [L2 · Mid] | 5 min per round | Right resource in all three, evidence written down |
| 3 | Three containers run with different `--cpus` limits; find the throttled one | [L3 · Senior] | 10 min | The throttling ratio from `cpu.stat` quoted for the right container |
| 4 | fio baseline: random read, random write, sequential, latency and the etcd fsync check, then clean up | [L3 · Senior] | 15 min | Five numbers recorded, all test files removed |
| 5 | A partner adds a `tc netem` delay or loss; name it from iperf3 and `ss -tin` only | [L3 · Senior] | 15 min | Correct impairment named, netem removed |
| 6 | Load-test a lab app with k6 thresholds and state its capacity at p95 under 300 ms | [L3 · Senior] | 30 min | A capacity number plus the one-page test plan |
| 7 | Rebuild the §17 stack from your Git repo on a fresh VM; the disk and failed-unit alerts reach the sink | [L4 · Lead/SRE] | 45 min | Both alerts FIRING, then RESOLVED |
| 8 | Add an SLO with a fast-burn alert for a lab app and trigger it with the wrong-port drill | [L4 · Lead/SRE] | 30 min | Alert fires and resolves; budget used computed |
| 9 | Given a request ID, find its log lines on every host with one LogQL query | [L4 · Lead/SRE] | 10 min | All matching lines and hosts found |
| 10 | Game day: a partner or script breaks one thing at random; you learn of it from an alert, fix it and publish a one-page postmortem | [L4 · Lead/SRE] | one weekend | Alert-driven detection, fix, postmortem with timeline, root cause and follow-ups ([CI/CD & SRE module](33-learn-cicd-iac-sre.md)) |

**Exit criteria.** You have finished this module at your stage when you answer that stage's
questions without notes and pass its timed tasks within the limits, twice, on different
days. Write the dates down: they are evidence for the next step on the
[career ladder](40-career-ladder.md).

---

## 20. Where to go next

| If you want to... | Go to | Why |
|-------------------|-------|-----|
| Use all of this under incident pressure | [Why is the system slow?](23-playbook-slow-system.md) | The step-by-step playbook built on §2 and §4–§6 |
| Fix slow transfers and packet loss | [Network slow / speed](24-playbook-network-speed.md) | iperf3, BDP and retransmits in incident form |
| Debug 502/504 errors and outages | [Site down](25-playbook-site-down.md) | The layered walk that RED metrics and probes point you into |
| Watch Docker, Dokploy and Kubernetes workloads | [Containers & K8s playbook](26-playbook-containers-k8s.md), [Kubernetes learn module](31-learn-kubernetes.md) | cgroups, OOM kills, throttling and `kubectl top` in context |
| Turn alerts into incident response and postmortems | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) | Incident roles, change management, the L4 game day |
| Baseline the old Apache box and watch the new Dokploy host | [Apache 443 / Dokploy case](21-case-apache-443-dokploy.md), [Deployment patterns](35-deployment-patterns.md) | A baseline before the cut-over, dashboards and SLOs after it |
| Tune the databases you found in §8 | [Databases ops](38-learn-databases-ops.md) | Slow query logs, connection pools, backups |
| Design for capacity and failure | [Senior architecture](39-learn-senior-architecture.md) | N+1, scaling and observability as design inputs |
| Plan your next career stage | [Career ladder](40-career-ladder.md) | Where observability sits on the Mid → Senior → Lead path |

Recommended order after this module:

1. Finish the PCA course sections you skipped (Monitoring Kubernetes, Service Discovery and relabeling) and keep the PCA exam for after CKA: until you pass CKA, the CKA course comes first.
2. Do *Fundamentals of SRE* — Incident Management together with the [CI/CD & SRE module](33-learn-cicd-iac-sre.md), to turn alerts into incident handling.
3. Do the *Grafana Loki* course labs and keep Loki in your §17 stack permanently.
4. Keep [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) as the reference for everything past L4.
