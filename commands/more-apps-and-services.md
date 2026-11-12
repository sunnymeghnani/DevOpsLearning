# More services, runtimes & monitoring

The tools here appear once or twice in the handbook, each inside one story: a mail relay for alerts, a Proxmox node, a CI build, a JVM or Node.js heap, a queue that keeps growing, a monitoring agent that will not answer. Most of them answer one question: which version and limits a runtime really got, whether a service answers its client the way the client asks, or whether a config parses before you reload. Run the read-only form first; each card marks the forms that change state.

| If you would reach for | Prefer | Because |
|---|---|---|
| restarting Postfix after editing `sasl_passwd` | `postmap /etc/postfix/sasl_passwd`, then the restart | Postfix reads the compiled `.db` file, not your text file |
| `cp grafana.db` on a running server | `sqlite3 grafana.db ".backup '/backup/grafana.db'"` | a consistent copy even while Grafana writes |
| `docker stats` to judge a JVM's memory | `jcmd 1 GC.heap_info`, `java -XX:+PrintFlagsFinal -version` | heap used, committed and its limit, which RSS mixes together |
| `psql` on every node to find the primary | `patronictl -c /etc/patroni/config.yml list` | leader, replicas, timeline and lag in one table |
| `rabbitmqctl list_queues` with its default columns | `list_queues name messages messages_unacknowledged consumers` | backlog, unacked and consumers together name the stuck side |
| `telnet AGENT 10050` | `zabbix_get -s AGENT -k agent.ping` from the Zabbix server | it also passes the agent's `Server=` allow-list, or names it as the problem |
| restarting Alloy to see whether the config parses | `alloy fmt FILE` in CI, `alloy convert --report=…` when migrating | a syntax error fails the pipeline, not the agent |

### postconf / postmap — relay this server's mail through an authenticated smarthost
Match: postconf, postmap
Instead of: editing main.cf by hand
Safety: changes state: `postconf -e` rewrites `/etc/postfix/main.cf`; `postmap` rebuilds a lookup table Postfix reads · needs root · `sasl_passwd` holds a password: mode 600

**In one line:** `postconf` reads or sets Postfix parameters in `main.cf`; `postmap` compiles a text lookup table, here the relay credentials, into the indexed file Postfix actually reads.

**Read the command:** `sudo postconf -e 'relayhost = [smtp.example.com]:587' 'smtp_sasl_auth_enable = yes' 'smtp_tls_security_level = encrypt'`

| Part | Meaning |
|---|---|
| `-e 'name = value' …` | edit `main.cf`: each argument sets one parameter, the rest of the file stays |
| `[smtp.example.com]:587` | brackets: use this host as named, no MX lookup; 587 is the submission port |
| `smtp_tls_security_level = encrypt` | never send to the relay without TLS |
| `postconf -n` · `postconf relayhost` | every non-default setting · one value |
| `postmap /etc/postfix/sasl_passwd` | build `sasl_passwd.db` for the `hash:` table named in `smtp_sasl_password_maps` |

**What the output tells you:** both are silent on success. The verdict is in the mail log (`/var/log/mail.log` on Ubuntu): `status=sent (250 …)`, or `SASL authentication failed` and `status=deferred` with the reason.

**Why it is effective:** Postfix then handles TLS, authentication, queueing and retries, so tools that can only send to `localhost:25` (Wazuh's maild, cron) reach an external provider.

**Compared with editing `main.cf` by hand:** the same result, but a second line for the same parameter further down the file silently wins over the one you edited; `postconf -e` changes the parameter itself.

**Trap:** after every edit of `sasl_passwd`, run `postmap` again. Its key must match `relayhost` exactly, brackets and port included, or no password is sent.

**Next step:** mail stuck → `mailq`, then `postqueue -f` to retry now. Authentication refused → the provider's rules (app password, allowed sender address).

### multipath — has multipathd wrapped a disk that something else needs?
Match: multipath
Instead of: lsblk alone
Safety: read-only for `-ll` (needs root) · changes state: `-F` flushes unused multipath maps; a `blacklist` in `/etc/multipath.conf` plus a multipathd restart changes which disks it claims

**In one line:** `multipath -ll` prints the device-mapper multipath maps: each `mpathX` device with the WWID, vendor and product it was built from, and the paths (sdX) under it.

**Read the command:** `sudo multipath -ll | head -2`

| Part | Meaning |
|---|---|
| `-ll` | show the current multipath topology, with everything sysfs and device mapper know |
| `| head -2` | the first map's name and size lines: enough to see that a map exists |

**What the output tells you:**

```
mpatha (360000000000000000e00000000010001) dm-2 IET,VIRTUAL-DISK
size=10G features='0' hwhandler='0' wp=rw
```

A map built on Longhorn's iSCSI disk (vendor `IET`): multipathd claimed it, so mkfs and mount find it busy (`apparently in use by the system`). No output: no maps.

**Why it is effective:** a disk "in use" with no mount and no process holding it usually has a device-mapper layer on top; this names it.

**Compared with `lsblk`:** lsblk shows the same clue, a child of type `mpath` under the sdX disk, but not the paths or the vendor that a blacklist needs.

**Trap:** Ubuntu Server runs multipathd by default. On a host with real SAN multipath, blacklisting `devnode "^sd[a-z0-9]+"` hides the SAN disks too: blacklist Longhorn by vendor and product instead.

**Next step:** Longhorn or another iSCSI CSI → blacklist, `systemctl restart multipathd`, recreate the pod. Real SAN → every path should read `active ready running`.

### pveversion / pvesubscription — which Proxmox VE release is this, and does it hold a subscription?
Match: pveversion, pvesubscription
Instead of: reading the version in the web UI
Safety: read-only for `pveversion` and `pvesubscription get` · changes state: `pvesubscription set KEY` registers a key

**In one line:** `pveversion` prints the pve-manager version and the running kernel; `pvesubscription get` shows whether this node has a valid subscription, which decides whether the enterprise repository lets apt in.

**Read the command:** `pveversion`

| Part | Meaning |
|---|---|
| `pveversion` | `pve-manager/VERSION/BUILD (running kernel: …)` |
| `pveversion -v` | the version of every Proxmox package (kernels, qemu-server, Ceph…): paste it into bug reports |
| `pvesubscription get | grep '^status'` | `status: active`, or `notfound` when no key is set |

**What the output tells you:**

```
pve-manager/9.0.11/3bf5476b8a4699e2 (running kernel: 6.14.11-4-pve)
status: notfound
```

PVE 9 (Debian 13) without a subscription: the enterprise repositories answer apt with 401, so configure the no-subscription repository instead. A running kernel older than the newest one in `pveversion -v` means no reboot since the upgrade.

**Why it is effective:** release notes, forum threads and provider bugs (the Terraform providers, cloud-init) are all by version; this gives the exact one in a line you can paste.

**Compared with the web UI:** the header shows the version too, but not the package list, and not when pveproxy is down.

**Trap:** each node reports only itself: run it on every node, as a cluster should not stay on mixed versions after an upgrade. The "No valid subscription" pop-up is only a notice; the 401 from apt is a real failure.

**Next step:** 401 from apt → disable the enterprise sources, add `pve-no-subscription`. Provider crashes after an upgrade → compare the version with the provider's release notes.

### buildah / nixpacks — build images without a Docker daemon, or without a Dockerfile
Match: buildah, nixpacks
Instead of: docker build with the host's Docker socket mounted into CI jobs
Safety: read-only for `buildah info` and `nixpacks plan` · changes state: `buildah build` and `push` create and publish images; `nixpacks build` builds an image with the local Docker

**In one line:** Buildah builds OCI images from a Dockerfile without a daemon, so CI jobs need no Docker socket; Nixpacks (Dokploy's default builder) reads the source code and writes the build plan itself.

**Read the command:** `buildah info | grep -E '"GraphDriverName"|"rootless"'`

| Part | Meaning |
|---|---|
| `info` | JSON about the host and the storage: driver, rootless or not, paths |
| `STORAGE_DRIVER=vfs` · `BUILDAH_ISOLATION=chroot` | in an unprivileged CI container: copy layers instead of nesting overlay · run `RUN` steps in a plain chroot, not a full container |
| `buildah build -t IMAGE .` · `buildah push IMAGE` | build from the Dockerfile here · upload it |
| `nixpacks plan .` | print the JSON plan: providers, install and build phases, start command |

**What the output tells you:**

```
        "rootless": false,
        "GraphDriverName": "overlay",
```

Overlay storage inside a container that already runs on overlay: the first layer write fails (`'overlay' is not supported over overlayfs`). From Nixpacks, `"providers": []` means it recognised no language in that directory: a wrong build path in a monorepo, or no `package.json`.

**Why it is effective:** both show the decision the tool made (storage driver, detected language) before you debug the build itself.

**Compared with `docker build` in CI:** the same Dockerfile works, but a mounted Docker socket gives every job root on the runner host.

**Trap:** `vfs` is slow and uses more disk. Nixpacks guesses, its guess can change between versions, and it is in maintenance mode (Railpack succeeds it): pin the plan in `nixpacks.toml`, or build production images from a Dockerfile.

**Next step:** Buildah and a private registry CA → `/etc/containers/certs.d/HOST/ca.crt`. Wrong Nixpacks plan → fix the build path, then reproduce with `nixpacks build . --name app`.

### pytest — which test failed, and why, in a report CI can show?
Match: pytest
Instead of: scrolling the whole CI log for the failure
Safety: runs the project's tests, which may write files or call any service they can reach · writes the report file

**In one line:** `pytest` collects the `test_*.py` files, runs every `test_` function, and prints each failure with the assertion that broke; its exit code fails the CI job.

**Read the command:** `pytest -q --junitxml=report.xml`

| Part | Meaning |
|---|---|
| `-q` | quiet: progress dots, then only the failures and the summary |
| `--junitxml=report.xml` | also write JUnit XML; GitLab's `artifacts:reports:junit` shows it in the merge request |
| `-x` · `-k version` | stop at the first failure · run only tests whose names match `version` |
| `--lf` · `-s` | rerun only the tests that failed last time · show `print` output instead of capturing it |

**What the output tells you:**

```
FAILED tests/test_health.py::test_version_endpoint - AssertionError: assert 'unknown' == '9d8c7b6a'
1 failed, 23 passed in 1.84s
```

File, test and the comparison that failed: the app reported `unknown` where the test expected the commit SHA, so a CI variable did not reach it. Exit code 0: all passed; 1: tests failed; 5: no tests collected, which also fails the job.

**Why it is effective:** the failing assertion with both values is often the whole diagnosis, and the XML report puts it in the merge request.

**Compared with the full CI log:** the same lines are there, between pages of dependency installs.

**Trap:** passing locally and failing in CI is usually the environment: Python version, a missing variable, test order. Reproduce in the job's image (`docker run … python:3.12-slim`), not in your virtualenv.

**Next step:** fails only in CI → paste the job's script lines into that image. Flaky → `--lf` several times, then remove the shared state between tests.

### opentelemetry-bootstrap / opentelemetry-instrument — traces from a Python app without changing its code
Match: opentelemetry-bootstrap, opentelemetry-instrument
Instead of: adding tracing calls by hand
Safety: changes state: `bootstrap -a install` pip-installs packages into the active environment · `instrument` starts the app and sends spans to the configured endpoint

**In one line:** `opentelemetry-bootstrap` finds the libraries installed in the environment (Flask, requests…) and installs the matching instrumentation packages; `opentelemetry-instrument` starts the app with them active, configured only by `OTEL_*` variables.

**Read the command:** `OTEL_SERVICE_NAME=shop OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318 opentelemetry-instrument flask --app app run --port 8002`

| Part | Meaning |
|---|---|
| `opentelemetry-bootstrap -a install` | install the instrumentations; `-a requirements` only prints them |
| `OTEL_SERVICE_NAME=shop` | the service name you pick in Jaeger or Tempo |
| `…PROTOCOL=http/protobuf` with `…ENDPOINT=…:4318` | OTLP over HTTP on 4318; gRPC uses 4317: protocol and port must match |
| `OTEL_TRACES_EXPORTER=console` | print spans on stdout instead: proves instrumentation without any collector |
| `flask --app app run …` | the usual start command, unchanged |

**What the output tells you:** the app answers as before, and traces appear under `shop`, with a span per incoming request and outgoing call. Export errors (wrong port or protocol) show on the app's stderr while every request still succeeds.

**Why it is effective:** the slow dependency becomes a span with its own duration, without touching the application's code.

**Compared with manual tracing:** hand-written spans add business detail, but need code changes; start automatic, add spans where needed.

**Trap:** a library installed later is not traced until you run bootstrap again. `OTEL_TRACES_SAMPLER=traceidratio` with `OTEL_TRACES_SAMPLER_ARG=0` keeps nothing while everything looks healthy. Flask's debug reloader can start the app without instrumentation.

**Next step:** no traces → `OTEL_TRACES_EXPORTER=console` splits "not instrumented" from "export fails"; then check the collector's port and protocol.

### java / jcmd / keytool — which heap did the JVM pick, what is it doing, and which CAs does it trust?
Match: java, jcmd, keytool
Instead of: docker stats for a JVM's memory
Safety: read-only for `java -version`, `-XX:+PrintFlagsFinal` and `jcmd … GC.heap_info` · `Thread.print` pauses the JVM briefly · changes state: `jcmd … GC.heap_dump` writes a heap-sized file full of data; `keytool -importcert` changes a trust store

**In one line:** `java -XX:+PrintFlagsFinal -version` prints the settings the JVM really chose; `jcmd PID COMMAND` asks a running JVM for its heap, threads or flags; `keytool` edits Java keystores, including the `cacerts` trust store.

**Read the command:** `docker exec CONTAINER jcmd 1 GC.heap_info`

| Part | Meaning |
|---|---|
| `jcmd 1 GC.heap_info` | heap per generation or region, used versus committed, of PID 1 in the container |
| `jcmd 1 Thread.print` · `jcmd 1 help` | a thread dump, as `jstack` prints · the commands this JVM offers |
| `java -XX:+PrintFlagsFinal -version | grep -E 'MaxHeapSize|MaxRAMPercentage'` | the heap limit in bytes, and the share of memory it came from (default 25) |
| `java -version 2>&1` | the version goes to stderr |
| `keytool -importcert -cacerts -storepass changeit -alias example-root-ca -file example-root-ca.crt -noprompt` | add a CA to the JDK's trust store, without the "Trust this certificate?" question |

**What the output tells you:** the old generation still nearly full right after a full GC means live data or a leak. A `MaxHeapSize` about a quarter of the container limit is the default: raise it with `-XX:MaxRAMPercentage`.

**Why it is effective:** RSS mixes heap, metaspace, thread stacks and native memory; these show what the JVM itself decided and holds.

**Trap:** `jcmd` ships with the JDK, not in JRE-only images, and must run as the JVM's user (`sudo -u APPUSER`, or inside the container). Each JDK has its own `cacerts`, and `changeit` is the well-known default password; on Ubuntu, `ca-certificates-java` syncs the OS store into it. Restart the JVM after an import.

**Next step:** heap full after GC → `jcmd 1 GC.heap_dump /tmp/app.hprof` where disk allows (the file contains secrets). Stuck threads → three `Thread.print` dumps a few seconds apart (see `jstack / jstat`).

### node / php — which runtime version and memory limit does the app really get?
Match: node, php
Instead of: trusting the version written in the Dockerfile or the docs
Safety: read-only for `-v`, `-m`, `--ini` · `node -e` runs the code you give it

**In one line:** asked inside the container or on the host that runs the app, the runtimes report their own version, extensions, configuration files and limits: what decides whether an app fits an image or runs out of memory.

**Read the command:** `docker exec CONTAINER node -e 'console.log(v8.getHeapStatistics().heap_size_limit/1048576 + " MB")'`

| Part | Meaning |
|---|---|
| `-e '…'` | evaluate this JavaScript; built-in modules such as `v8` need no `require` here |
| `heap_size_limit/1048576` | V8's heap limit in MB: where `JavaScript heap out of memory` happens |
| `--max-old-space-size=384`, or `NODE_OPTIONS=--max-old-space-size=384` | set the old-generation heap limit in MB |
| `php -v` · `php -m` · `php --ini` | version (`PHP 8.3.6 (cli) …`) · loaded extensions · which `php.ini` files the CLI reads |

**What the output tells you:** a limit above the container's memory means the kernel kills the container (exit 137) before V8 can throw; far below it means `FATAL ERROR: … JavaScript heap out of memory` with RAM to spare.

**Why it is effective:** the runtime answers for the environment that matters, not for the one you assume.

**Trap:** the PHP CLI and PHP-FPM read separate `php.ini` files (`/etc/php/8.3/cli/` and `/etc/php/8.3/fpm/` on Ubuntu) and can even be different versions: check FPM with `php-fpm8.3 -v` or a `phpinfo()` page. Node's default heap depends on its version and on the memory it detects: set it explicitly in containers.

**Next step:** heap limit wrong → `--max-old-space-size` at about three quarters of the container limit. Missing PHP extension → add it to the image.

### grafana cli / sqlite3 — reset Grafana's admin password, list plugins, back up grafana.db safely
Match: grafana, sqlite3
Instead of: deleting grafana.db to reset the password; cp of a live database file
Safety: read-only for `plugins ls`; `.backup` writes only the copy · changes state: `admin reset-admin-password` rewrites the admin's password; `plugins install` and `update` change plugins

**In one line:** `grafana cli` is Grafana's server-side command line (formerly `grafana-cli`); `sqlite3` opens a SQLite file such as Grafana's default `grafana.db`, and its `.backup` makes a consistent copy while Grafana keeps writing.

**Read the command:** `sudo sqlite3 /path/to/grafana.db ".backup '/backup/grafana-before-change.db'"`

| Part | Meaning |
|---|---|
| `".backup 'FILE'"` | copy the database through SQLite's backup API, a consistent snapshot |
| `"PRAGMA integrity_check;"` | check a database, or the copy: `ok` |
| `docker exec grafana grafana cli admin reset-admin-password "$PW"` | new password for the admin user, in the database the container uses |
| `grafana cli plugins ls` | installed plugins with versions, before an upgrade drops Angular ones |
| `--homepath /usr/share/grafana --config /etc/grafana/grafana.ini` | package install: point the CLI at the real config and data |

**What the output tells you:** `.backup` is silent on success, and the copy should pass `integrity_check`. `plugins ls` prints one `ID @ VERSION` line per plugin.

**Why it is effective:** a `cp` during a write can copy a half-updated file; `.backup` cannot. The CLI writes the password hash straight into the database the login checks.

**Trap:** on a host, the CLI without `--homepath` and `--config` can update a different `grafana.db` than the server reads, and still report success. A password typed as an argument lands in history: read it with `read -rsp` as the handbook does. `database is locked` under load points at SQLite on NFS or two replicas sharing one file.

**Next step:** locks, or more than one replica → PostgreSQL as Grafana's database. Reset "worked" but login fails → the wrong database, or SSO or an auth proxy owns the login.

### mongosh — log in as the app does, and see which users live in which database
Match: mongosh
Instead of: recreating the data volume to reset users
Safety: read-only for `getUsers()` and `ping` · changes state: `createUser`, `dropUser` and any write you pass to `--eval`

**In one line:** `mongosh` is MongoDB's shell (MongoDB 6.0 and later no longer ship the legacy `mongo` shell); with `--eval` it runs one JavaScript expression and exits.

**Read the command:** `docker exec -it MONGO mongosh -u root -p --authenticationDatabase admin --quiet --eval 'db.getSiblingDB("admin").getUsers().users.map(u => u.user + "@" + u.db)'`

| Part | Meaning |
|---|---|
| `-u root -p` | the user; `-p` without a value prompts for the password |
| `--authenticationDatabase admin` | the database that holds this user (`authSource` in a connection string) |
| `--quiet` · `--eval '…'` | no banner · run this and exit |
| `getSiblingDB("admin").getUsers()` | the users defined in `admin`; `.users.map(…)` prints them as `user@db` |
| `db.adminCommand({ ping: 1 })` | `{ ok: 1 }`: reachable and logged in |

**What the output tells you:** `[ 'root@admin' ]`: the only user lives in `admin`. An app that logs in as root against `shop`, without `authSource=admin`, gets `Authentication failed` although the password is right.

**Why it is effective:** a MongoDB user belongs to one database; this shows which, and repeats the login the app's URI makes.

**Trap:** `MONGO_INITDB_ROOT_*` variables apply only to an empty data directory: changing them later changes nothing. `-p PASSWORD` on the command line lands in history and `ps`.

**Next step:** user in `admin` → `?authSource=admin` in the URI, or better, one user per app database. `ECONNREFUSED` → `net.bindIp`, and the service name instead of `localhost`.

### patronictl — which node is the PostgreSQL leader, and how far behind are the replicas?
Match: patronictl
Instead of: psql on each node to find the primary
Safety: read-only for `list` and `history` · changes state: `switchover`, `failover`, `restart`, `reinit`, `edit-config`, `pause`

**In one line:** Patroni runs PostgreSQL under a leader key kept in a distributed store (etcd, Consul…); `patronictl` reads that store and the members to show who leads and who follows.

**Read the command:** `patronictl -c /etc/patroni/config.yml list`

| Part | Meaning |
|---|---|
| `-c /etc/patroni/config.yml` | Patroni's config: the cluster's name and how to reach the store |
| `list` | one row per member: role, state, timeline (`TL`), lag |
| `switchover` | **changes state**: a planned move of the leader to a healthy replica |
| `pause` · `resume` | maintenance mode on and off: no automatic failover meanwhile |

**What the output tells you:**

```
| Member | Host       | Role    | State     | TL | Lag in MB |
| db1    | 192.0.2.21 | Leader  | running   |  3 |           |
| db2    | 192.0.2.22 | Replica | streaming |  3 |         0 |
```

One `Leader`, replicas `streaming` on the same timeline with lag near 0: healthy. A replica on an older timeline, or with growing lag, is no safe failover target.

**Why it is effective:** one table instead of a `psql` session per node, and it is Patroni's view, the one that routes clients: its REST API answers `/primary` with 200 only on the leader.

**Trap:** when the store loses its majority, the leader stops accepting writes on purpose: fencing against split brain, not a bug. Never promote a node with `pg_ctl` behind Patroni's back.

**Next step:** no leader → the store's health (`etcdctl endpoint health`). Lag growing → the replica's disk and network, `pg_stat_replication` on the leader. Planned work → `pause`, the work, `resume`.

### rabbitmqctl — is the queue growing because nobody consumes, or because consumers are stuck?
Match: rabbitmqctl
Instead of: the management UI's overview graph
Safety: read-only for `list_*` · changes state: `purge_queue` deletes messages; `delete_queue`, user and permission commands

**In one line:** `rabbitmqctl` talks to the running RabbitMQ node; `list_queues` with chosen columns shows, per queue, the backlog, the messages delivered but not yet acknowledged, and the consumers.

**Read the command:** `docker exec rabbitmq rabbitmqctl list_queues name messages messages_unacknowledged consumers`

| Part | Meaning |
|---|---|
| `messages` | ready plus unacknowledged: the queue depth |
| `messages_unacknowledged` | delivered to a consumer, not acked yet |
| `consumers` | consumers attached to the queue |
| `-p VHOST` | another virtual host than `/` |
| `list_consumers` · `rabbitmq-diagnostics status` | who consumes, with prefetch · node health, memory and disk alarms |

**What the output tells you:**

```
name	messages	messages_unacknowledged	consumers
emails	1240	12	2
emails.dlq	3	0	0
```

A deep queue with few unacked and 2 consumers: they are alive but too slow. `consumers 0`: nobody reads. Unacked close to the depth: consumers take messages and never ack. A growing `.dlq`: messages that keep failing.

**Why it is effective:** the three numbers side by side say whether to look at the consumers, the producer or the messages themselves.

**Trap:** the default columns are only name and messages, which hides the difference. The tool authenticates with the node's Erlang cookie: run it as root or inside the container. A memory or disk alarm blocks publishers, which then hang instead of failing.

**Next step:** no consumers → the consumer service and its logs. Too slow → more consumers, check prefetch. Dead letters → inspect one message before any replay.

### zabbix_get — does the agent answer the Zabbix server, from the server's address?
Match: zabbix_get
Instead of: telnet AGENT 10050
Safety: read-only · asks the agent for one item value

**In one line:** `zabbix_get` requests one item from a Zabbix agent the way the server's passive poller does, so it tests the path, the port and the agent's `Server=` allow-list at once.

**Read the command:** `zabbix_get -s 192.0.2.30 -k agent.ping`

| Part | Meaning |
|---|---|
| `-s 192.0.2.30` | the agent's address |
| `-k agent.ping` | the item key; the answer `1` means the agent replied |
| `-p 10050` | the agent's port (10050 is the default) |
| `-k agent.version` | another key, to compare with what the frontend shows |

**What the output tells you:** `1`: path and permission work. `Check access restrictions in Zabbix agent configuration`: connected, but the agent dropped the caller because `Server=` lacks its real source address (after NAT, or a Docker bridge address when the server runs in a container). `Connection refused` or `No route to host`: agent down, listening on localhost only, or a firewall on 10050.

**Why it is effective:** run on the Zabbix server, or in its container, it connects from the poller's own address, and the agent's log then names the address it rejected.

**Compared with `telnet AGENT 10050`:** it proves the port only; the allow-list is where most "unreachable" agents fail.

**Trap:** it tests passive checks only. Active checks run the other way (agent to server on 10051, `ServerActive=`), and need `Hostname=` to equal the host name in the frontend. It comes in its own package, `zabbix-get`.

**Next step:** access restriction → add the address to `Server=`, restart `zabbix-agent2`. `host [Web01] not found` → `Hostname=` against the frontend.

### alloy — check, convert and debug the Grafana Alloy collector config
Match: alloy
Instead of: restarting Alloy to see whether the config works
Safety: read-only for `fmt` (without `-w`) and for `convert`, which writes only its output and report · `alloy run` starts the collector

**In one line:** `alloy` is Grafana's collector (successor to Grafana Agent and Promtail); `fmt` checks a config's syntax, and `convert` translates a Promtail, Prometheus or Grafana Agent static config into Alloy syntax.

**Read the command:** `alloy convert --source-format=promtail --report=report.txt --output=config.alloy promtail.yaml`

| Part | Meaning |
|---|---|
| `--source-format=promtail` | the input format (also `prometheus` and `static`) |
| `--report=report.txt` | what could not be converted, and why: read it |
| `--output=config.alloy` | the new file (otherwise stdout) |
| `alloy fmt FILE > /dev/null` | parse and format; a syntax error gives a non-zero exit, which fails CI |
| `alloy run --config.format=promtail promtail.yaml` | run the old file unchanged during the migration |

**What the output tells you:** the report lists what you must carry over by hand, such as Promtail's command-line flags and environment variables. At run time each component reports separately: `level=error msg="failed to start component" component_id=…` in the log, and per component in the UI (port 12345).

**Why it is effective:** a converted, syntax-checked file removes most migration mistakes before agents roll out host by host.

**Trap:** `fmt` checks syntax only, not that a mounted path, socket or endpoint exists: a component can still fail at start (`/var/log/journal: no such file`, docker.sock `permission denied`). Without a persistent `--storage.path`, read positions are lost and logs are missed or sent twice.

**Next step:** component errors → the container's mounts and groups. Logs missing in Loki → that component in the UI, then `logcli`.

### sqlcmd — run one T-SQL batch against SQL Server from the shell
Match: sqlcmd
Instead of: opening SQL Server Management Studio for one setting
Safety: read-only for `SELECT` · changes state: `sp_configure … RECONFIGURE` changes the server's configuration at once

**In one line:** `sqlcmd` is SQL Server's command-line client; `-Q` runs a batch and exits, so one setting can be read or changed from PowerShell or a script.

**Read the command:** `sqlcmd -S localhost -E -Q "EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'max server memory (MB)', 4096; RECONFIGURE;"`

| Part | Meaning |
|---|---|
| `-S localhost` | the server (`HOST\INSTANCE` for a named instance) |
| `-E` | Windows authentication as the current user |
| `-Q "…"` | run this and exit (`-q` stays at the prompt) |
| `'show advanced options', 1` | unhide advanced settings such as max server memory |
| `RECONFIGURE` | apply now; this setting needs no restart |

**What the output tells you:** `Configuration option 'max server memory (MB)' changed from 2147483647 to 4096. Run the RECONFIGURE statement to install.` The old value is the default, meaning no cap: SQL Server keeps growing its cache into almost all RAM.

**Why it is effective:** on a shared VM, the cap gives Windows, IIS and the agents their memory back, without a restart.

**Compared with Management Studio:** the same setting, but sqlcmd works over a remote shell, in a script, and leaves the exact statement in the change record.

**Trap:** `-U sa -P PASSWORD` puts a password in history and process lists; prefer `-E`. Agree the value with the DBA: too low a cap sends queries to disk.

**Next step:** verify → `sqlcmd -S localhost -E -Q "SELECT name, value_in_use FROM sys.configurations WHERE name = 'max server memory (MB)'"`, then watch `Memory\Available MBytes` with `Get-Counter`.

### vim — edit a YAML manifest without wrecking its indentation
Match: vim
Instead of: pasting YAML into vim with the default settings
Safety: changes state: rewrites the file when you save (`:w`)

**In one line:** `vim FILE` opens a modal editor: you start in normal mode, `i` starts inserting text, Esc stops, and `:wq` saves and quits.

**Read the command:** `vim sleeper.yaml`

| Part | Meaning |
|---|---|
| `i` · Esc | insert text · back to normal mode |
| `:wq` · `:q!` | save and quit · quit and discard the changes |
| `:set paste` | before pasting: no auto-indent, so pasted YAML keeps its own indentation (`:set nopaste` after) |
| `set expandtab tabstop=2 shiftwidth=2` in `~/.vimrc` | Tab inserts two spaces: YAML forbids tabs for indentation |
| `:set list` | show tabs as `^I` and line ends as `$` |

**What the output tells you:** nothing until you apply the file: `mapping values are not allowed in this context` or `found character that cannot start any token` (a tab) names the line that was pasted badly.

**Why it is effective:** with these settings every indent is spaces at a fixed width, which is all that YAML's structure depends on.

**Trap:** a recent vim in a terminal with bracketed paste may already paste cleanly, so the problem shows only on some machines; `:set paste` is harmless either way. `sudo vim` runs the editor and its plugins as root; `sudoedit FILE` edits a copy as you.

**Next step:** apply fails → `kubectl apply --dry-run=server -f FILE` to see the error before anything changes. Live objects → `KUBE_EDITOR=vim kubectl edit`.

### pwgen — generate a long random secret for a config file
Match: pwgen
Instead of: making up a secret by hand
Safety: read-only · its output is a secret: keep it out of tickets, chats and shell history

**In one line:** `pwgen` prints random passwords; `-s` makes them fully random instead of pronounceable, which is what a service secret needs.

**Read the command:** `GRAYLOG_PASSWORD_SECRET=$(pwgen -N 1 -s 96)`

| Part | Meaning |
|---|---|
| `-N 1` | one password (otherwise a screenful) |
| `-s` | secure: completely random characters |
| `96` | the length |
| `-c` · `-n` · `-y` | at least one capital · digit · symbol |
| `$(…)` | the value goes into the variable, not onto the screen |

**What the output tells you:** inside `$( )`, nothing: the secret goes straight into the variable or the `.env` file.

**Why it is effective:** a long random value, generated where it is used, with nothing typed, copied or remembered.

**Trap:** pwgen's manual makes capitals and digits the default only when the output is a terminal: inside `$( )` add `-c -n` if a policy demands them. Symbols (`-y`) can break `.env` files and YAML quoting. It is often not installed; `openssl rand -base64 48` serves the same purpose.

**Next step:** keep the value in the secret store, and the `.env` file at mode 600, out of Git.
