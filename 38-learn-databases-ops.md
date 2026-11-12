# 38 — Learn: Databases for DevOps (Operate, Back Up, Troubleshoot)

This module teaches you to **operate** databases, not to design schemas. A DBA tunes queries and
models data; a DevOps engineer keeps the database reachable, sized, backed up, replicated,
monitored and safely changed by pipelines. Most database tickets that land on a DevOps desk are the
same seven: "the app can't connect", "too many connections", "the disk is full", "everything got
slow after the deploy", "queries are hanging", "the replica is behind" and "we deleted something,
get it back". This module gives you the mental model behind each one, shows it on a real Ubuntu
server, has you break it on a test VM, and ends with step-by-step incident playbooks.

It fits the rest of your stack: apps that used to sit behind Apache (now on ports 81/444) and are
moving to Dokploy (Traefik v3, Docker Swarm, `dokploy-network`), GitLab CI pipelines that run
schema migrations, images in Harbor behind a private CA, a kubeadm/containerd homelab on the CKA
track, and AWS where the same databases may run as RDS. Disk problems link to
[Storage & disk](01-storage-disk.md), network problems to [Network](02-network.md) and
[DNS](08-dns.md), slow systems to the [slow system playbook](23-playbook-slow-system.md) and
metrics to [Performance & observability](32-learn-performance-observability.md).

> All sample outputs are illustrative: Ubuntu 22.04/24.04, PostgreSQL 16 (the Ubuntu 24.04 default;
> 22.04 ships 14), MySQL 8.0 with notes for the 8.4 LTS series, MariaDB 10.11, Redis 7. Database
> servers use 192.0.2.21–23, app servers 192.0.2.50–52, lab VMs 192.168.56.0/24, names end in
> example.com or example.internal, and the AWS account is 123456789012. UPPERCASE words in commands
> are placeholders: HOST, PORT, DBNAME, TABLE, USER, PASSWORD, PID, CONTAINER, POD, NAMESPACE.

> Every "break it" step is for a **test VM or sandbox account only**. Several of them kill
> sessions, fill disks, drop tables or stop replication on purpose.

---

## 0. How to use this module

> 📚 **Study path:** 1) Note: this section first (who the module is for, the learning path, the lab) · 2) Note: the [career ladder](40-career-ladder.md) to place yourself before you pick sections · 3) KodeKloud: *Learning Linux Basics Course & Labs* — Package Management and Service Management with SYSTEMD, only if installing packages and managing services still feels new ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 4) Practice: build the lab below on Ubuntu 24.04 VMs, or on the [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) when no VM is at hand.

### Who this module is for

Databases appear at every career stage, but what you are trusted with changes. Find your stage,
do its sections first, and use its exit test in section 12 to decide when to move up. The stage
names match the [career ladder](40-career-ladder.md) used across the handbook.

| Stage | Tag | What you are expected to do with databases | Focus sections |
|---|---|---|---|
| Fresher (0–1 yr) | L0 · Fresher | Connect with `psql` and `mysql`, run basic SQL, know that a database is a service with a port, a data directory, a config file and a log | 1, 2 (psql), 3 (client) |
| Junior (1–2 yrs) | L1 · Junior | Install and configure a server, fix "can't connect", create users and grants, take a logical backup **and restore it** | 2, 3, 4 (logical), 6 (basics) |
| Mid-level (2–4 yrs) | L2 · Mid | Run the incident playbooks alone: connections, locks, slow queries, disk full from WAL, Redis memory; read EXPLAIN; run databases in Docker safely | 1 (locks, WAL), 2–3 (ops), 6, 7 (Docker), 8, 10 |
| Senior (4–7 yrs) | L3 · Senior | Point-in-time recovery, replication, pooling, monitoring and alerts, migrations in CI/CD, major upgrades, databases on Kubernetes | 4 (PITR), 5, 7, 9, 11 |
| Senior/Lead/SRE (5+ yrs) | L4 · Lead/SRE | Set RPO/RTO with the business, design HA (Patroni or managed), run restore drills and game days, own capacity and change management | 4, 5, 7, 9, 12 |

A senior engineer is not the one who knows the most SQL. It is the one who has **restored a backup
under pressure**, knows which lock a migration will take before running it, and refuses to raise
`max_connections` as a fix.

### Learning path

The areas below are grouped by subject so the module also works as a reference. To learn from zero,
follow this order instead.

| # | Topic | Tag | Section | Why it is in this position |
|---|---|---|---|---|
| 1 | Connections, sessions, ports, sockets | [L0 · Fresher] | 1 | Every database ticket starts with "who is connected, from where" |
| 2 | psql and the mysql client | [L0 · Fresher] | 2, 3 | You cannot inspect anything without a client |
| 3 | Install, layout, config files, logs | [L1 · Junior] | 2, 3 | Know where things live before you change them |
| 4 | The "can't connect" checklist | [L1 · Junior] | 2, 3 | The single most common ticket |
| 5 | Transactions and MVCC | [L1 · Junior] | 1 | Explains idle-in-transaction, bloat and lock waits later |
| 6 | Logical backups and a real restore | [L1 · Junior] | 4 | A backup you never restored is a hope, not a backup |
| 7 | Redis in one page | [L1 · Junior] | 6 | Nearly every app stack you deploy has one |
| 8 | Locks and blocking | [L2 · Mid] | 1, 2, 3 | "Everything hangs" during migrations |
| 9 | pg_stat_activity and SHOW PROCESSLIST | [L2 · Mid] | 2, 3 | The `ps` and `ss` of a database |
| 10 | Slow query logs, pg_stat_statements, EXPLAIN | [L2 · Mid] | 2, 3 | "Slow after deploy" |
| 11 | Indexes in one page | [L2 · Mid] | 1 | Why one missing index takes a site down |
| 12 | WAL and binlog | [L2 · Mid] | 1 | Disk full, replication and PITR all hang on this |
| 13 | VACUUM, bloat, InnoDB status | [L2 · Mid] | 2, 3 | Slow degradation over weeks |
| 14 | Connection limits and PgBouncer | [L2 · Mid] → [L3 · Senior] | 2, 3 | "Too many connections" after scaling out |
| 15 | Redis persistence, eviction, incidents | [L2 · Mid] | 6 | MISCONF and OOM errors at 3 a.m. |
| 16 | Databases in Docker and Dokploy | [L2 · Mid] | 7 | Your migration target |
| 17 | Security and access | [L2 · Mid] | 8 | Exposed 5432/6379 ports are a classic breach |
| 18 | The seven incident playbooks | [L2 · Mid] | 10 | Where everything above pays off |
| 19 | Physical backups, PITR, restore tests | [L3 · Senior] | 4 | Recover to 10:14, not to last night |
| 20 | Replication and lag | [L3 · Senior] | 5 | Read scaling and the basis of HA |
| 21 | Exporters, metrics and alerts | [L3 · Senior] | 9 | Learn about problems from an alert, not a user |
| 22 | Migrations in CI/CD | [L3 · Senior] | 11 | Deploys that do not lock tables |
| 23 | Major version upgrades | [L3 · Senior] | 2, 3 | PostgreSQL 14 and MySQL 8.0 are leaving support |
| 24 | StatefulSets and CloudNativePG | [L3 · Senior] | 7 | Databases on your CKA homelab |
| 25 | Failover, Patroni, VM vs Kubernetes vs managed | [L4 · Lead/SRE] | 5, 7 | Architecture decisions you will be asked to defend |
| 26 | RPO/RTO, restore drills, game days | [L4 · Lead/SRE] | 4, 12 | Proving recovery, not assuming it |

> Fast track for a Mid-level engineer: skim 1–7, do the section 12 Junior exit test, then spend
> your real hours on 8–18. The incident playbooks in section 10 are the core of this module.

### Study method

For every ### topic, use the same five steps, in this order:

1. **Read this note.** Concept, key terms, then run the "See it on a real system" commands on your
   lab VM. They are read-only.
2. **Do the matching KodeKloud lesson.** Each area starts with a 📚 Study path line. KodeKloud labs
   come pre-built, so you practise the skill without fighting installation.
3. **Optional video**, only if the concept still feels fuzzy. One good explanation, then stop.
4. **Hands-on lab on your own VM.** Build it, break it on purpose, then diagnose from evidence
   **before** you fix it. Write down the exact error text; that is what you will search for in a
   real incident.
5. **Read the matching playbook** in section 10, so the incident version feels familiar.

Database-specific habits to build from day one:

- **Every backup lab ends with a restore.** No exceptions, not even in the lab.
- **Write the timestamp down** before you break something. Point-in-time recovery needs it, and so
  does every postmortem.
- **Read the database log first.** PostgreSQL and MySQL both say exactly what is wrong far more
  often than people expect.
- **Prefer the gentle action.** Cancel a query before you terminate a session; terminate one
  session before you restart a server; restart before you restore.

After each lab, write the five-line note from your weekly rhythm: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time.

> Timebox: one topic per 30–45 minute morning slot. Until your CKA exam, CKA sessions come first;
> section 7 (StatefulSets, PVCs) counts as CKA practice too.

### Build your database lab

Use two Ubuntu 24.04 VMs with 2 vCPU, 4 GB RAM and a 30 GB disk each: **db1** at 192.168.56.21
(PostgreSQL primary, MySQL source, Redis) and **db2** at 192.168.56.22 (replicas). A third VM
**app1** at 192.168.56.11 with Docker installed plays the application server. **Snapshot every VM
after installation** so each "break it" lab can be undone in seconds.

```bash
# db1 and db2: PostgreSQL 16 (Ubuntu 24.04 default), MySQL 8.0, Redis, tools
sudo apt update
sudo apt install -y postgresql postgresql-contrib mysql-server redis-server \
  pgbouncer percona-toolkit jq netcat-openbsd dnsutils
psql --version
mysql --version
redis-server --version
```

```
psql (PostgreSQL) 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
mysql  Ver 8.0.43-0ubuntu0.24.04.1 for Linux on x86_64 ((Ubuntu))
Redis server v=7.0.15 sha=00000000:0 malloc=jemalloc-5.3.0 bits=64 build=d81b8ff71cfb150e
```

→ Three servers, three systemd units: `postgresql@16-main`, `mysql` and `redis-server`.

On **Ubuntu 22.04** the default PostgreSQL is 14, which reaches upstream end of life in
November 2026. To get 16 (or newer) use the PostgreSQL project's own apt repository (PGDG):

```bash
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh    # adds the PGDG repo and key
sudo apt install -y postgresql-16 postgresql-contrib-16
```

**RHEL/Rocky difference:** packages come from the distribution AppStream module or the PGDG yum
repo. There is no Debian "cluster" wrapper: you run `sudo /usr/pgsql-16/bin/postgresql-16-setup
initdb`, then `sudo systemctl enable --now postgresql-16`, and config lives in the data directory
`/var/lib/pgsql/16/data/`. MySQL's unit is `mysqld` (not `mysql`) and its config is `/etc/my.cnf`
plus `/etc/my.cnf.d/`. SELinux is enforcing, so a non-default port or data directory needs
`semanage` labels.

Load test data once (as the `postgres` OS user, which is the database superuser through peer
authentication):

```bash
sudo -u postgres psql -c "CREATE ROLE app LOGIN PASSWORD 'LabPass-123';"
sudo -u postgres createdb -O app appdb
pgbench -i -s 20 -h 127.0.0.1 -U app appdb     # 2,000,000 rows in pgbench_accounts
```

```
dropping old tables...
creating tables...
generating data (client-side)...
2000000 of 2000000 tuples (100%) done (elapsed 3.41 s, remaining 0.00 s)
vacuuming...
creating primary keys...
done in 5.12 s (drop tables 0.00 s, create tables 0.01 s, client-side generate 3.52 s, vacuum 0.71 s, primary keys 0.88 s).
```

And an `orders` table that the EXPLAIN, lock and restore labs reuse:

```bash
psql -h 127.0.0.1 -U app appdb <<'SQL'
CREATE TABLE orders (
  id          bigserial PRIMARY KEY,
  customer_id int           NOT NULL,
  status      text          NOT NULL,
  total       numeric(10,2) NOT NULL,
  created_at  timestamptz   NOT NULL DEFAULT now()
);
INSERT INTO orders (customer_id, status, total, created_at)
SELECT (random()*50000)::int,
       (ARRAY['new','paid','shipped'])[(1 + floor(random()*3))::int],
       round((random()*500)::numeric, 2),
       now() - random() * interval '365 days'
FROM generate_series(1, 1000000);
ANALYZE orders;
SQL
```

> Never run the labs in this module against a work database, and never point a lab tool at a
> production connection string "just to look". `pgbench -i` starts by dropping its tables.

---

## 1. Relational basics for ops

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — 2 Tier Applications, where you deploy an application with its database first on one host and then on two, which is the connection model of this section ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) · 2) Note: this section, then [Processes](05-processes.md), because every PostgreSQL connection is an operating-system process · 3) Read: the tutorial part of the [PostgreSQL documentation](https://www.postgresql.org/docs/) if SQL itself is new; KodeKloud has no SQL or database-operations course in the verified map (check the current catalog) · 4) Practice: the labs below on your db1 VM or on the [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu).

You do not need relational theory to operate a database, but you do need five ideas. Each one
explains a class of incident: connections explain "too many clients", transactions explain
"idle in transaction", locks explain "everything hangs", indexes explain "slow after deploy", and
the write-ahead log explains "the disk filled up" and "the replica is behind".

### Connections and sessions

**Level:** [L0 · Fresher] → [L1 · Junior] · about 40 minutes

**Concept.** A database server is a long-running service that listens on a TCP port (PostgreSQL
5432, MySQL/MariaDB 3306, Redis 6379) and on a local Unix socket. A client opens a **connection**,
authenticates, and gets a **session**: a server-side context with its own settings, its own
transaction and its own locks. PostgreSQL forks one **operating system process per connection**;
MySQL runs one **thread per connection**. Either way, every connection costs memory and CPU even
when idle, which is why the server caps them (`max_connections`) and why applications keep a
**connection pool** instead of connecting per request.

```
  app1 (Gunicorn, 4 workers x pool of 5)          db1 192.0.2.21
 ┌──────────────────────────────────┐          ┌──────────────────────────────────────────┐
 │ worker 1  [c][c][c][c][c] ───────┼── TCP ──▶│ postgres (postmaster, PID 1012) :5432     │
 │ worker 2  [c][c][c][c][c] ───────┼── TCP ──▶│  ├─ backend PID 4821  app appdb idle      │
 │ worker 3  [c][c][c][c][c] ───────┼── TCP ──▶│  ├─ backend PID 4830  app appdb SELECT    │
 │ worker 4  [c][c][c][c][c] ───────┼── TCP ──▶│  ├─ ... one process per connection        │
 └──────────────────────────────────┘          │  └─ max_connections = 100 (hard cap)      │
   = 20 server connections from ONE host        └──────────────────────────────────────────┘
   x 3 app replicas = 60 connections before anyone runs a cron job or a migration
```

Opening a connection is expensive: TCP handshake, often TLS, authentication (SCRAM is deliberately
slow), and for PostgreSQL a `fork()`. A pool pays that once and reuses the connection.

**Key terms**

| Term | Meaning |
|---|---|
| Connection string | Where and how to connect, e.g. `postgresql://app:PASSWORD@db1.example.internal:5432/appdb?sslmode=verify-full` |
| Unix socket | Local-only connection through a file such as `/var/run/postgresql/.s.PGSQL.5432` or `/var/run/mysqld/mysqld.sock`; no TCP, no network firewall |
| Backend | PostgreSQL's per-connection server process |
| max_connections | Hard limit on concurrent sessions (PostgreSQL default 100, MySQL default 151) |
| Connection pool | Client-side (in the app) or server-side (PgBouncer, ProxySQL, RDS Proxy) set of reusable connections |
| Session state | Settings, temp tables, prepared statements and locks that belong to one connection |

**See it on a real system**

```bash
ps -o pid,ppid,cmd --forest -u postgres         # one process per connection
sudo ss -tnp state established '( sport = :5432 )' | head
sudo -u postgres psql -c "SELECT state, count(*) FROM pg_stat_activity WHERE backend_type = 'client backend' GROUP BY state;"
sudo mysql -e "SHOW GLOBAL STATUS LIKE 'Threads_connected'; SHOW VARIABLES LIKE 'max_connections';"
```

```
    PID    PPID CMD
   1012       1 /usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/16/main -c config_file=/etc/postgresql/16/main/postgresql.conf
   1013    1012  \_ postgres: 16/main: checkpointer
   1014    1012  \_ postgres: 16/main: background writer
   1016    1012  \_ postgres: 16/main: walwriter
   1017    1012  \_ postgres: 16/main: autovacuum launcher
   1018    1012  \_ postgres: 16/main: logical replication launcher
   4821    1012  \_ postgres: 16/main: app appdb 192.168.56.11(50412) idle
   4830    1012  \_ postgres: 16/main: app appdb 192.168.56.11(50418) SELECT

Recv-Q Send-Q   Local Address:Port    Peer Address:Port  Process
0      0       192.168.56.21:5432   192.168.56.11:50412  users:(("postgres",pid=4821,fd=9))
0      0       192.168.56.21:5432   192.168.56.11:50418  users:(("postgres",pid=4830,fd=9))

 state  | count
--------+-------
 active |     1
 idle   |     1

+-------------------+-------+
| Variable_name     | Value |
+-------------------+-------+
| Threads_connected | 3     |
+-------------------+-------+
+-----------------+-------+
| Variable_name   | Value |
+-----------------+-------+
| max_connections | 151   |
+-----------------+-------+
```

→ The process title tells you user, database, client address and what the session is doing, so
plain `ps` is already a monitoring tool. The `ss` peer port (50412) matches the process title,
which is how you tie a TCP connection on the network to a session in the database.

**Hands-on lab (test VM only)**

**Step 1 — Build: watch sessions appear.** Open two more terminals and run
`psql -h 127.0.0.1 -U app appdb` in each, then re-run the `ps` command above. Two new backends
appear; quit one psql and its process disappears.

**Step 2 — Break it: run out of connection slots.** pgbench with more clients than the server
allows:

```bash
pgbench -h 127.0.0.1 -U app -c 120 -j 4 -T 20 appdb
```

```
pgbench: error: connection to server at "127.0.0.1", port 5432 failed: FATAL:  remaining connection slots are reserved for roles with the SUPERUSER attribute
pgbench: error: could not create connection for client 97
```

→ 100 slots minus 3 kept for superusers (`superuser_reserved_connections`) leaves 97 for `app`.
Once even the reserved slots are used, the message becomes `FATAL:  sorry, too many clients
already`. Note that `sudo -u postgres psql` still works while `app` is locked out: that reserved
headroom is exactly what lets you investigate during a real incident.

**Step 3 — Fix it.** Run with `-c 50`. The real-world fix (pool sizing and PgBouncer) is in
section 2; the incident version is the "Too many connections" playbook in section 10.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| `sorry, too many clients already` | `SELECT state, count(*) FROM pg_stat_activity GROUP BY 1;` | Section 10, too many connections |
| `ERROR 1040 (HY000): Too many connections` | `SHOW PROCESSLIST;` (uses the extra admin slot) | Section 10, too many connections |
| `Connection refused` from the app host only | `sudo ss -ltnp` on the DB host | Section 10, app can't connect |
| App latency spikes, DB looks idle | app pool metrics (wait time for a free connection) | [Slow system](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** A database is just a process with sockets. Everything you
learned with `ps`, `ss` and `journalctl` works here too, and the session view inside the database
(`pg_stat_activity`, `SHOW PROCESSLIST`) is the same idea one layer higher.

**Next step:** a session can hold a transaction open; learn what that costs.

### Transactions and MVCC

**Level:** [L1 · Junior] · about 40 minutes

**Concept.** A **transaction** groups statements so they succeed or fail together (`BEGIN` …
`COMMIT` or `ROLLBACK`). Without an explicit `BEGIN`, each statement is its own transaction
(autocommit). Both PostgreSQL and InnoDB use **MVCC** (multi-version concurrency control): an
`UPDATE` does not overwrite a row in place, it creates a new **row version**, and each transaction
sees a consistent snapshot. That is why readers do not block writers. The price is cleanup: old
versions must be removed once no transaction can still see them. PostgreSQL does that with
**VACUUM**; InnoDB does it with **purge** of its undo log. **A single long-running or forgotten
transaction blocks that cleanup for the whole database.**

```
 time ───────────────────────────────────────────────────────────────────────▶
 session A  BEGIN; UPDATE pgbench_accounts SET abalance = abalance - 100 WHERE aid = 1;  ...  COMMIT;
 session B         SELECT abalance FROM pgbench_accounts WHERE aid = 1;  → old value, no waiting
 session C         UPDATE pgbench_accounts SET abalance = 0 WHERE aid = 1;  → WAITS for A's row lock
```

**Key terms**

| Term | Meaning |
|---|---|
| ACID | Atomic, Consistent, Isolated, Durable: the transaction guarantees |
| Autocommit | Each statement commits by itself unless you open a transaction |
| Isolation level | How much of other sessions' work you see. PostgreSQL default READ COMMITTED, InnoDB default REPEATABLE READ |
| MVCC | Multiple row versions so readers and writers do not block each other |
| Dead tuple | PostgreSQL row version no longer visible to anyone, waiting for VACUUM |
| idle in transaction | Session that opened a transaction and is not running anything: holds locks and blocks cleanup |
| History list length | InnoDB's count of undo records not yet purged; grows behind long transactions |

**See it on a real system**

```bash
sudo -u postgres psql -d appdb -c "
SELECT pid, usename, state, now() - xact_start AS xact_age, left(query, 60) AS query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;"
```

```
 pid  | usename |        state        |    xact_age     |                 query
------+---------+---------------------+-----------------+----------------------------------------
 5120 | app     | idle in transaction | 00:47:12.40319  | SELECT * FROM orders WHERE id = 991 FOR UPDATE
 5302 | app     | active              | 00:00:00.01211  | UPDATE pgbench_accounts SET abalance = ...
 5340 | postgres| active              | 00:00:00        | SELECT pid, usename, state, now() - xact...
```

→ PID 5120 opened a transaction 47 minutes ago, locked a row with `FOR UPDATE` and went quiet.
The `query` column shows the **last** statement it ran, not something it is running now. Any
session that needs order 991 will wait on it, and VACUUM cannot clean anything newer than its
snapshot.

**Hands-on lab (test VM only)**

**Step 1 — Build: see MVCC.** In terminal A run `BEGIN;` then
`UPDATE pgbench_accounts SET abalance = 500 WHERE aid = 1;` and leave it open. In terminal B run
`SELECT abalance FROM pgbench_accounts WHERE aid = 1;`. B returns the old value immediately.

**Step 2 — Break it: a writer waits.** In terminal B run
`UPDATE pgbench_accounts SET abalance = 0 WHERE aid = 1;`. It hangs. In terminal C, run the
`pg_stat_activity` query above: A is `idle in transaction`, B is `active` with
`wait_event_type = Lock`.

**Step 3 — Fix it, then prevent it.** `COMMIT;` in A releases B instantly. Now make the server
protect you from forgotten transactions for the `app` role:

```bash
sudo -u postgres psql -c "ALTER ROLE app SET idle_in_transaction_session_timeout = '30s';"
```

Reconnect as `app`, run `BEGIN; SELECT 1;`, wait 31 seconds, then run `SELECT 1;` again:

```
FATAL:  terminating connection due to idle-in-transaction timeout
server closed the connection unexpectedly
```

→ The server ended the session and rolled the transaction back. In production pick a value longer
than any legitimate pause in your app (often 1–10 minutes), and log it so developers can fix the
code path that leaves transactions open.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| Many sessions `idle in transaction` | `pg_stat_activity` ordered by `xact_start` | Section 10, locks |
| Tables grow every week though data does not | `n_dead_tup` in `pg_stat_user_tables` | Section 2, VACUUM |
| InnoDB `History list length` in the millions | `SELECT * FROM information_schema.innodb_trx ORDER BY trx_started;` | Section 3, InnoDB status |
| `could not serialize access due to concurrent update` | app retry logic, isolation level | ask the app team; it is expected under REPEATABLE READ |

**Why it matters for troubleshooting.** "The database is slow" is often "one transaction has been
open since yesterday". Checking the oldest transaction takes ten seconds and rules out a whole
class of problems.

**Next step:** transactions hold locks; learn which ones and why they queue.

### Locks and blocking

**Level:** [L2 · Mid] · about 60 minutes

**Concept.** Databases lock at two granularities. **Row locks** are taken by `UPDATE`, `DELETE`
and `SELECT … FOR UPDATE`; they only block other writers of the same row. **Table-level locks**
come in modes. In PostgreSQL every `SELECT` takes the weakest mode (ACCESS SHARE) and most
`ALTER TABLE`, `DROP`, `TRUNCATE` and `VACUUM FULL` take the strongest (ACCESS EXCLUSIVE), which
conflicts with everything, including plain reads. Locks are granted in **queue order**: once a
strong lock request is waiting, every newer request queues behind it, even ones compatible with
the current holder. That is how a two-second migration takes a site down.

```
 10:00:00  S1  long report: SELECT ... FROM orders (runs 5 min)    holds ACCESS SHARE ──────────────▶
 10:00:30  S2  migration: ALTER TABLE orders ADD COLUMN note text  wants ACCESS EXCLUSIVE → waits for S1
 10:00:31  S3  app: SELECT * FROM orders WHERE id = 7              wants ACCESS SHARE → waits for S2 (!)
 10:00:31+ every request touching orders queues, app pool fills, Traefik returns 504, site "down"
```

MySQL has the same shape with different names: InnoDB row locks (plus gap locks under REPEATABLE
READ) and **metadata locks** (MDL) for DDL. A waiting `ALTER TABLE` shows `Waiting for table
metadata lock` in `SHOW PROCESSLIST`, and new queries pile up behind it.

A **deadlock** is two transactions each waiting for the other. Both engines detect it and abort
one (PostgreSQL after `deadlock_timeout`, 1 s by default): `ERROR: deadlock detected` or MySQL
`ERROR 1213 (40001)`. Deadlocks are an application bug to fix (consistent update order), not a
server problem, unless they suddenly appear after a deploy.

**Key terms**

| Term | Meaning |
|---|---|
| ACCESS SHARE / ACCESS EXCLUSIVE | Weakest / strongest PostgreSQL table lock modes |
| Lock queue | Waiting requests are granted in order; a waiting strong lock blocks newer weak ones |
| `pg_locks` | View of every lock held or awaited |
| `pg_blocking_pids(pid)` | Function returning the PIDs that block a given session |
| `lock_timeout` | Give up waiting for a lock after N ms; the key safety net for migrations |
| Metadata lock (MDL) | MySQL lock protecting table definitions during DDL |
| `innodb_lock_wait_timeout` | MySQL row-lock wait limit, default 50 s (`ERROR 1205`) |

**See it on a real system**

```bash
sudo -u postgres psql -d appdb -c "
SELECT a.pid, pg_blocking_pids(a.pid) AS blocked_by, a.state, a.wait_event_type,
       now() - a.query_start AS waiting, left(a.query, 50) AS query
FROM pg_stat_activity a
WHERE a.backend_type = 'client backend' AND a.datname = 'appdb'
ORDER BY a.query_start;"
```

```
 pid  | blocked_by |        state        | wait_event_type |     waiting     |                       query
------+------------+---------------------+-----------------+-----------------+----------------------------------------------------
 6001 | {}         | idle in transaction | Client          | 00:02:14.33     | SELECT count(*) FROM orders
 6002 | {6001}     | active              | Lock            | 00:01:40.10     | ALTER TABLE orders ADD COLUMN note text
 6003 | {6002}     | active              | Lock            | 00:01:39.87     | SELECT * FROM orders WHERE id = 7
 6004 | {6002}     | active              | Lock            | 00:01:39.52     | SELECT * FROM orders WHERE id = 12
```

→ Read the `blocked_by` column as a tree: 6003 and 6004 wait for 6002, and 6002 waits for 6001.
The **root blocker** is 6001, an idle-in-transaction session. Killing the ALTER (6002) unblocks
the app; ending 6001 lets the ALTER through.

**Hands-on lab (test VM only)**

**Step 1 — Build the queue.** Terminal S1: `BEGIN; SELECT count(*) FROM orders;` (leave the
transaction open, it now holds ACCESS SHARE). Terminal S2:
`ALTER TABLE orders ADD COLUMN note text;` (hangs). Terminal S3:
`SELECT * FROM orders WHERE id = 7;` (hangs, although S1 is "only reading").

**Step 2 — Diagnose.** Run the query above in a fourth terminal and draw the tree on paper.

**Step 3 — Fix with the gentlest action.** In S2 press Ctrl+C: S3 returns immediately. Then
`COMMIT;` in S1.

**Step 4 — Prevent it.** Re-run the scenario, but in S2 first run `SET lock_timeout = '3s';`
before the `ALTER TABLE`:

```
ERROR:  canceling statement due to lock timeout
```

→ The migration fails fast instead of freezing the table. A failed migration is retried in a
quiet minute; a frozen table is an outage. Section 11 makes `lock_timeout` part of every migration.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| Site hangs right after a migration starts | blocking-tree query above | Section 10, locks |
| `Waiting for table metadata lock` (MySQL) | `SELECT * FROM sys.schema_table_lock_waits\G` | Section 10, locks |
| `ERROR 1205 (HY000): Lock wait timeout exceeded` | `SELECT * FROM sys.innodb_lock_waits\G` | Section 3, PROCESSLIST |
| `ERROR:  deadlock detected` after a deploy | the DB log shows both statements | send both statements to the app team |

**Why it matters for troubleshooting.** Lock waits look like a slow or dead database, but CPU, disk
and memory are idle. If the server is quiet and queries hang, check locks before anything else.

**Next step:** the other reason queries are slow is that they read too much; that is what indexes
fix.

### Indexes in one page

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** Without an index, finding rows means reading the whole table (a **sequential scan**).
An index is a separate sorted structure, almost always a **B-tree**, that maps values to row
locations, like the index at the back of a book. Looking up `customer_id = 4242` in a B-tree of a
million rows touches about four pages instead of eight thousand.

```
                       B-tree on orders(customer_id)
                          ┌──────────────┐
                          │ 25000        │                 root
                          └──┬────────┬──┘
                ┌────────────┘        └────────────┐
         ┌──────┴──────┐                     ┌──────┴──────┐
         │ 4000  12000 │                     │ 31000 44000 │  branch
         └──┬───┬───┬──┘                     └─────────────┘
            ▼   ▼   ▼
   leaf: 4240 → (page 812, row 3)  4242 → (page 77, row 9), (page 5120, row 1)  ...
```

What an ops engineer must know:

- **Indexes are not free.** Every `INSERT`/`UPDATE` maintains every index, and indexes use disk
  and cache. Unused indexes are pure cost.
- **A matching predicate is required.** An index on `customer_id` is not used for
  `WHERE customer_id::text = '4242'` or `WHERE lower(email) = …` unless you build an expression
  index on exactly that expression.
- **Column order matters** in multi-column indexes: `(customer_id, created_at)` serves
  `WHERE customer_id = ?` and `WHERE customer_id = ? AND created_at > ?`, not
  `WHERE created_at > ?` alone.
- **Building an index locks writes** in PostgreSQL unless you use `CREATE INDEX CONCURRENTLY`.
  In MySQL 8, `ALTER TABLE … ADD INDEX` is online (`ALGORITHM=INPLACE, LOCK=NONE`) for InnoDB.
- **Statistics drive the planner.** After bulk loads the planner may not know the data changed
  until `ANALYZE` runs (autovacuum does it eventually).

**Key terms:** sequential scan, index scan, index-only scan, bitmap scan, selectivity, composite
index, expression index, `CREATE INDEX CONCURRENTLY`, planner statistics.

**See it on a real system**

```bash
sudo -u postgres psql -d appdb -c "\di+ orders*"
sudo -u postgres psql -d appdb -c "
SELECT relname, indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes ORDER BY idx_scan ASC LIMIT 5;"
```

```
                                       List of relations
 Schema |    Name     | Type  | Owner | Table  | Persistence | Access method | Size  | Description
--------+-------------+-------+-------+--------+-------------+---------------+-------+-------------
 public | orders_pkey | index | app   | orders | permanent   | btree         | 21 MB |

    relname       |       indexrelname        | idx_scan |  size
------------------+---------------------------+----------+---------
 orders           | orders_status_idx         |        0 | 6840 kB
 pgbench_branches | pgbench_branches_pkey     |       12 | 16 kB
 orders           | orders_pkey               |     1408 | 21 MB
```

→ `orders_status_idx` (if someone created it) has never been used since statistics were reset:
it slows every write for nothing. Check replicas too before dropping an index, because
`idx_scan` counts only the server you asked.

**Hands-on lab (test VM only)**

**Step 1 — Build: measure without and with an index.**

```bash
psql -h 127.0.0.1 -U app appdb <<'SQL'
\timing on
SELECT count(*) FROM orders WHERE customer_id = 4242;
CREATE INDEX CONCURRENTLY orders_customer_id_idx ON orders (customer_id);
SELECT count(*) FROM orders WHERE customer_id = 4242;
SQL
```

```
 count
-------
    21
Time: 74.218 ms
CREATE INDEX
Time: 612.904 ms
 count
-------
    21
Time: 0.412 ms
```

→ 180 times faster. Under load the difference is not just speed: 74 ms of CPU and I/O per call
times hundreds of calls per second is what saturates a database server.

**Step 2 — Break it: the index exists but is not used.**

```bash
psql -h 127.0.0.1 -U app appdb -c "\timing on" -c "SELECT count(*) FROM orders WHERE customer_id::text = '4242';"
```

→ Back to roughly 100 ms: the cast turned the indexed column into an expression the index does
not cover. ORMs generate this kind of mismatch (wrong parameter type, a function wrapped around
the column) more often than you would think.

**Step 3 — Fix it.** Compare with the right type (`WHERE customer_id = 4242`), or, if the query
really needs the expression, build an expression index on it. Section 2's EXPLAIN topic shows how
to prove which plan was chosen.

**How it breaks**

| Symptom | First command | Where to go |
|---|---|---|
| One endpoint slow after a deploy, DB CPU up | `pg_stat_statements` top by total time | Section 10, slow queries after deploy |
| Writes slower every month | count indexes per table, `idx_scan = 0` | Section 2, slow query log |
| `CREATE INDEX` froze writes in production | it lacked `CONCURRENTLY` | Section 11, migrations |

**Why it matters for troubleshooting.** "Slow after deploy" is very often "a new query without an
index". You will not write the index yourself in most teams, but you will be the one who proves it
with evidence and gets it built safely.

**Next step:** every change, indexed or not, goes through the write-ahead log first.

### WAL and binlog

**Level:** [L2 · Mid] · about 60 minutes

**Concept.** Writing a changed 8 KB page to its data file on every commit would be slow and unsafe
(a crash mid-write corrupts it). Instead PostgreSQL appends a compact description of the change to
the **write-ahead log** (WAL) and flushes only that to disk at `COMMIT`. Changed pages stay in
memory and are written to data files later, in bulk, at a **checkpoint**. After a crash, the
server replays WAL from the last checkpoint. The same WAL stream feeds **replication** (standbys
replay it) and **point-in-time recovery** (archived WAL replayed on top of a base backup).

```
  COMMIT
    │
    ▼
 ┌────────────────────┐ 1. append + fsync  ┌──────────────────────────┐
 │ shared buffers     │ ─────────────────▶ │ WAL: pg_wal/ 16 MB files │
 │ (dirty pages, RAM) │                    └────────────┬─────────────┘
 └─────────┬──────────┘                                 │ 3. the same stream goes to
           │ 2. checkpoint, later                       ├──▶ standby (streaming replication)
           ▼                                            ├──▶ archive (PITR, archive_command)
 ┌────────────────────┐                                 └──▶ crash recovery (replay)
 │ data files base/   │
 └────────────────────┘
```

WAL files are removed only when **nothing needs them any more**. Four things keep them: the next
checkpoint not having happened yet, `wal_keep_size`, an archiver that is failing, and a
**replication slot** whose consumer is gone. The last two are the classic "disk full from WAL"
incidents.

MySQL has two logs. InnoDB's **redo log** plays the crash-recovery role. The **binary log
(binlog)** records committed changes for replication and point-in-time recovery; it is on by
default in MySQL 8.0, rotated into numbered files (`binlog.000042`) and expired after
`binlog_expire_logs_seconds` (default 2592000, 30 days). On a busy server 30 days of binlogs can
be bigger than the database itself.

**Key terms**

| Term | Meaning |
|---|---|
| WAL segment | One 16 MB file in `pg_wal/`, named like `000000010000000A0000003F` |
| LSN | Log sequence number, a position in the WAL stream, e.g. `A/3F2B1C80` |
| Checkpoint | Flush of dirty pages that lets older WAL be recycled; driven by `max_wal_size` and `checkpoint_timeout` |
| Replication slot | Server-side bookmark that keeps WAL until a consumer has received it |
| Archiving | Copying each finished WAL segment elsewhere (`archive_command`) for PITR |
| Binlog | MySQL's logical change log for replication and PITR |
| Redo log | InnoDB's crash-recovery log |

**See it on a real system**

```bash
sudo -u postgres psql -c "SELECT pg_current_wal_lsn(), pg_walfile_name(pg_current_wal_lsn());"
sudo -u postgres psql -c "SHOW max_wal_size;" -c "SHOW wal_keep_size;" -c "SELECT slot_name, active, wal_status FROM pg_replication_slots;"
sudo du -sh /var/lib/postgresql/16/main/pg_wal
sudo mysql -e "SHOW BINARY LOGS; SHOW VARIABLES LIKE 'binlog_expire_logs_seconds';"
```

```
 pg_current_wal_lsn |     pg_walfile_name
--------------------+--------------------------
 0/5A3F2B18         | 00000001000000000000005A

 max_wal_size
--------------
 1GB

 wal_keep_size
---------------
 0

 slot_name | active | wal_status
-----------+--------+------------
(0 rows)

336M    /var/lib/postgresql/16/main/pg_wal

+---------------+-----------+-----------+
| Log_name      | File_size | Encrypted |
+---------------+-----------+-----------+
| binlog.000001 |       180 | No        |
| binlog.000002 | 104857912 | No        |
| binlog.000003 |  48211907 | No        |
+---------------+-----------+-----------+
+----------------------------+---------+
| Variable_name              | Value   |
+----------------------------+---------+
| binlog_expire_logs_seconds | 2592000 |
+----------------------------+---------+
```

→ `pg_wal` normally hovers below `max_wal_size` plus a little. If it keeps growing past that, one
of the four retention reasons is holding files: that is a question you can answer in a minute
(section 10, disk full).

**Hands-on lab (test VM only)**

**Step 1 — Build: measure your WAL rate.** Note the LSN, generate load, note it again:

```bash
sudo -u postgres psql -Atc "SELECT pg_current_wal_lsn();"        # e.g. 0/5A3F2B18
pgbench -h 127.0.0.1 -U app -c 8 -T 60 appdb > /dev/null
sudo -u postgres psql -Atc "SELECT pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), '0/5A3F2B18'));"
```

```
412 MB
```

→ About 400 MB of WAL per busy minute on this lab. Multiply by your retention to size the WAL
archive and decide how long a dead replica can stay down before the disk fills.

**Step 2 — Break it: a forgotten replication slot.** Create a slot that nobody consumes, then
generate load:

```bash
sudo -u postgres psql -c "SELECT pg_create_physical_replication_slot('ghost', true);"
pgbench -h 127.0.0.1 -U app -c 8 -T 120 appdb > /dev/null
sudo -u postgres psql -c "CHECKPOINT;"
sudo du -sh /var/lib/postgresql/16/main/pg_wal
sudo -u postgres psql -c "SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained FROM pg_replication_slots;"
```

```
1.3G    /var/lib/postgresql/16/main/pg_wal

 slot_name | active | retained
-----------+--------+----------
 ghost     | f      | 1279 MB
```

→ Even after a checkpoint the WAL does not shrink: the inactive slot pins it. In production this is
the replica that was decommissioned without dropping its slot, and the disk fills over days.

**Step 3 — Fix it.** Drop the slot, checkpoint, and watch the directory shrink:

```bash
sudo -u postgres psql -c "SELECT pg_drop_replication_slot('ghost');" -c "CHECKPOINT;"
sudo du -sh /var/lib/postgresql/16/main/pg_wal
```

> **Never delete files from `pg_wal/` or MySQL binlogs with `rm`.** PostgreSQL may need them for
> crash recovery and will refuse to start without them; MySQL's binlog index and replicas break.
> Remove the *reason* WAL is retained, or use `PURGE BINARY LOGS` in MySQL (section 10).

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| `PANIC:  could not write to file "pg_wal/xlogtemp.1234": No space left on device` | `df -h`, then `pg_replication_slots` | Section 10, disk full |
| `archive command failed with exit code 1` repeating in the log | `SELECT * FROM pg_stat_archiver;` | Section 4, PITR |
| `/var/lib/mysql` full of `binlog.0*` | `SHOW BINARY LOGS;` | Section 10, disk full |
| Replica far behind after a bulk job | `pg_stat_replication` | Section 10, replication lag |

**Why it matters for troubleshooting.** WAL and binlogs connect disk usage, replication and backups.
If you understand what keeps WAL around, three different incidents become one question.

**Next step:** with these five ideas, PostgreSQL's operational tools in section 2 will make sense.

---

## 2. PostgreSQL operations

> 📚 **Study path:** 1) Note: section 1 of this module first (connections, MVCC, locks, WAL) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment: Manage Startup Process and Services, then Locate and Analyze System Log Files, the systemd and log skills every topic below relies on ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Read: the Server Administration part of the [PostgreSQL documentation](https://www.postgresql.org/docs/) (server configuration, client authentication, routine vacuuming); a KodeKloud PostgreSQL course is not in the verified map (check the current catalog) · 4) Practice: *Linux Challenges* (free), whose timed scenarios include a broken database service ([course](https://kodekloud.com/courses/linux-challenges)), then the labs below.

PostgreSQL is the database you will meet most in new projects, in Dokploy templates, in
CloudNativePG on Kubernetes and as RDS/Aurora on AWS. This area covers what you run on the server
itself. Everything here applies to PostgreSQL 14–18; differences are noted where they matter.

### Install, layout and configuration

**Level:** [L1 · Junior] · about 45 minutes

**Concept.** Ubuntu and Debian wrap PostgreSQL in a **cluster** layer: one machine can run several
clusters (a version plus a name, such as `16/main`), each with its own port, data directory,
config directory and log. Tools from `postgresql-common` (`pg_lsclusters`, `pg_ctlcluster`,
`pg_upgradecluster`) and the systemd template unit `postgresql@16-main.service` manage them. The
plain `postgresql.service` is only an umbrella that shows `active (exited)`; the real server is the
templated unit.

| What | Ubuntu / Debian | RHEL / Rocky (PGDG) |
|---|---|---|
| Config | `/etc/postgresql/16/main/postgresql.conf`, `pg_hba.conf`, `conf.d/` | `/var/lib/pgsql/16/data/postgresql.conf`, `pg_hba.conf` |
| Data | `/var/lib/postgresql/16/main` | `/var/lib/pgsql/16/data` |
| Server log | `/var/log/postgresql/postgresql-16-main.log` | `/var/lib/pgsql/16/data/log/` |
| Unit | `postgresql@16-main` | `postgresql-16` |
| Socket | `/var/run/postgresql/.s.PGSQL.5432` | `/run/postgresql/` and `/tmp` |
| Binaries | `/usr/lib/postgresql/16/bin/` (wrappers in `/usr/bin`) | `/usr/pgsql-16/bin/` |

Settings come from several places, and the **last one wins**: `postgresql.conf`, then files in
`conf.d/` (Debian includes that directory at the end of `postgresql.conf`), then
`postgresql.auto.conf` in the data directory, which `ALTER SYSTEM` writes. "I changed
`postgresql.conf` and nothing happened" is usually an `ALTER SYSTEM` value overriding it, or a
setting that needs a restart rather than a reload.

Every setting has a **context**: `postmaster` settings (such as `listen_addresses`,
`max_connections`, `shared_buffers`, `shared_preload_libraries`) need a **restart**; `sighup`
settings (such as `archive_command`, `log_checkpoints`), `superuser` settings changed in the file
(such as `log_min_duration_statement`, `log_lock_waits`) and `pg_hba.conf` changes need only a
**reload**, which never drops connections.

| Memory setting | Default | Sensible start on a dedicated server | Why care |
|---|---|---|---|
| `shared_buffers` | 128MB | about 25% of RAM | PostgreSQL's own page cache |
| `effective_cache_size` | 4GB | 50–75% of RAM | Planner hint only, allocates nothing |
| `work_mem` | 4MB | 8–64MB | Per sort or hash **per query node**: 200 connections x 3 nodes x 64MB can exhaust RAM |
| `maintenance_work_mem` | 64MB | 256MB–1GB | VACUUM and CREATE INDEX speed |

**Key terms:** cluster, data directory, `postgresql.auto.conf`, `ALTER SYSTEM`, context
(postmaster/sighup/superuser/user), reload, restart, `pg_settings`, `pg_file_settings`.

**See it on a real system**

```bash
pg_lsclusters
systemctl status postgresql@16-main --no-pager | head -5
sudo -u postgres psql -c "SHOW config_file;" -c "SHOW data_directory;"
sudo -u postgres psql -c "
SELECT name, setting, unit, context, source, sourcefile
FROM pg_settings
WHERE name IN ('max_connections','shared_buffers','work_mem','listen_addresses','log_min_duration_statement');"
```

```
Ver Cluster Port Status Owner    Data directory              Log file
16  main    5432 online postgres /var/lib/postgresql/16/main /var/log/postgresql/postgresql-16-main.log

● postgresql@16-main.service - PostgreSQL Cluster 16-main
     Loaded: loaded (/usr/lib/systemd/system/postgresql@.service; enabled-runtime; preset: enabled)
     Active: active (running) since Sat 2026-10-03 09:01:12 UTC; 1h 2min ago
   Main PID: 1012 (postgres)

               config_file
-----------------------------------------
 /etc/postgresql/16/main/postgresql.conf

        data_directory
-----------------------------
 /var/lib/postgresql/16/main

            name            |  setting  | unit |  context   |       source       |                sourcefile
----------------------------+-----------+------+------------+--------------------+------------------------------------------
 listen_addresses           | localhost |      | postmaster | default            |
 log_min_duration_statement | -1        | ms   | superuser  | default            |
 max_connections            | 100       |      | postmaster | configuration file | /etc/postgresql/16/main/postgresql.conf
 shared_buffers             | 16384     | 8kB  | postmaster | configuration file | /etc/postgresql/16/main/postgresql.conf
 work_mem                   | 4096      | kB   | user       | default            |
```

→ `shared_buffers` 16384 x 8 kB = 128 MB, the default. `listen_addresses` shows `default` because
Ubuntu's `postgresql.conf` leaves that line commented out. `sourcefile` tells you which file set each
value, which ends the "which file wins" guessing. Note that the server log on Ubuntu goes to
`/var/log/postgresql/`, not to the journal; `journalctl -u postgresql@16-main` only shows starts
and stops.

**Hands-on lab (test VM only)**

**Step 1 — Build: change a setting the safe way.** Put your changes in `conf.d/` so package
upgrades never conflict with them:

```bash
echo "log_min_duration_statement = '500ms'" | sudo tee /etc/postgresql/16/main/conf.d/50-logging.conf
sudo -u postgres psql -c "SELECT pg_reload_conf();" -c "SHOW log_min_duration_statement;"
```

**Step 2 — Break it: a typo.** Add a broken line and reload:

```bash
echo "work_mem = 64MB oops" | sudo tee /etc/postgresql/16/main/conf.d/90-typo.conf
sudo -u postgres psql -c "SELECT pg_reload_conf();"
sudo -u postgres psql -c "SELECT sourcefile, sourceline, error FROM pg_file_settings WHERE error IS NOT NULL;"
sudo tail -n 3 /var/log/postgresql/postgresql-16-main.log
```

```
                 sourcefile                  | sourceline |    error
---------------------------------------------+------------+--------------
 /etc/postgresql/16/main/conf.d/90-typo.conf |          1 | syntax error

2026-10-03 10:12:41.207 UTC [1012] LOG:  received SIGHUP, reloading configuration files
2026-10-03 10:12:41.208 UTC [1012] LOG:  syntax error in file "/etc/postgresql/16/main/conf.d/90-typo.conf" line 1, near token "oops"
2026-10-03 10:12:41.208 UTC [1012] LOG:  configuration file "/etc/postgresql/16/main/postgresql.conf" contains errors; no changes were applied
```

→ A **reload** with a broken file is harmless: the server keeps running on the old config and tells
you why. A **restart** with the same file would fail and leave the database down. So: edit, reload,
check `pg_file_settings`, and only then restart if the setting needs it.

**Step 3 — Fix it.** `sudo rm /etc/postgresql/16/main/conf.d/90-typo.conf`, reload, and confirm
`pg_file_settings` shows no errors. For settings with context `postmaster`, check
`SELECT name FROM pg_settings WHERE pending_restart;` to see what is waiting for a restart.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| Service fails to start after a config change | `sudo tail -n 30 /var/log/postgresql/postgresql-16-main.log` | [Services & systemd](07-services-systemd.md) |
| Setting "ignored" | `SELECT name, setting, sourcefile FROM pg_settings WHERE name = 'X';` | this topic |
| `FATAL:  could not map anonymous shared memory` | `free -m`, lower `shared_buffers` | [Memory](04-memory.md) |
| Server killed, log shows `terminated by signal 9: Killed` | `journalctl -k -b` for the OOM killer | [Memory](04-memory.md) |
| Package update restarted the database | `/var/log/apt/history.log` | plan minor updates as changes (section 11) |

**Why it matters for troubleshooting.** You cannot reason about behaviour until you know which
values are live. `pg_settings` is the single source of truth, and "reload, check, then restart" is
the habit that stops a config change from becoming an outage.

**Next step:** get fluent in `psql`, the tool you will use for everything else.

### psql essentials

**Level:** [L0 · Fresher] · about 30 minutes

**Concept.** `psql` is PostgreSQL's command-line client. It runs SQL and also **meta-commands**
that start with a backslash and are answered by psql itself (they turn into catalog queries). On
the server, `sudo -u postgres psql` logs you in as the superuser through the Unix socket using
**peer** authentication: the OS user name must match the database role, no password needed.

| Meta-command | What it does |
|---|---|
| `\l` | List databases with owner, encoding, size (`\l+`) |
| `\c DBNAME` | Connect to another database |
| `\dt`, `\dt+` | List tables (with sizes) |
| `\d TABLE` | Columns, indexes, constraints, triggers of a table |
| `\di+`, `\dn`, `\df` | Indexes, schemas, functions |
| `\du` | Roles and their attributes |
| `\x auto` | Expanded output when rows are too wide |
| `\timing on` | Print how long each statement took |
| `\conninfo` | Who, where, which database, SSL or not |
| `\watch 2` | Re-run the last query every 2 seconds (a poor man's dashboard) |
| `\copy` | Client-side COPY, reads/writes files on **your** machine |
| `\i FILE`, `\e` | Run a file, edit the last query in `$EDITOR` |
| `\q` | Quit |

For scripts: `psql -X -At -v ON_ERROR_STOP=1 -c "…"` (no `.psqlrc`, unaligned tuples only, stop
on the first error). For passwords use `~/.pgpass` (mode 600, lines of
`hostname:port:database:username:password`), never a password on the command line, where `ps`
shows it to every user.

**See it on a real system**

```bash
sudo -u postgres psql -c "\l+ appdb"
psql -h 127.0.0.1 -U app appdb -c "\conninfo" -c "\dt+"
```

```
                                                                List of databases
 Name  | Owner | Encoding | Locale Provider |   Collate   |    Ctype    | ICU Locale | ICU Rules | Access privileges |  Size  | Tablespace | Description
-------+-------+----------+-----------------+-------------+-------------+------------+-----------+-------------------+--------+------------+-------------
 appdb | app   | UTF8     | libc            | C.UTF-8     | C.UTF-8     |            |           |                   | 401 MB | pg_default |

You are connected to database "appdb" as user "app" on host "127.0.0.1" at port "5432".
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, compression: off)

                                        List of relations
 Schema |       Name       | Type  | Owner | Persistence | Access method |  Size   | Description
--------+------------------+-------+-------+-------------+---------------+---------+-------------
 public | orders           | table | app   | permanent   | heap          | 65 MB   |
 public | pgbench_accounts | table | app   | permanent   | heap          | 256 MB  |
 public | pgbench_branches | table | app   | permanent   | heap          | 40 kB   |
 public | pgbench_history  | table | app   | permanent   | heap          | 0 bytes |
 public | pgbench_tellers  | table | app   | permanent   | heap          | 120 kB  |
```

→ Ubuntu's package enables SSL with a self-signed "snakeoil" certificate, so even local TCP
connections are encrypted. That certificate proves nothing about identity; section 8 covers real
TLS with your private CA.

**Hands-on lab (test VM only)**

**Step 1 — Build a password file.** As your normal user:

```bash
echo '127.0.0.1:5432:appdb:app:LabPass-123' > ~/.pgpass
chmod 600 ~/.pgpass
psql -h 127.0.0.1 -U app appdb -c "SELECT current_user, inet_server_addr();"
```

**Step 2 — Break it.** `chmod 644 ~/.pgpass` and connect again:

```
WARNING: password file "/home/ops/.pgpass" has group or world access; permissions should be u=rw (0600) or less
Password for user app:
```

→ psql refuses to use a password file others can read, and falls back to prompting. In a cron job
or CI job there is no one to type, so the job "hangs" or fails with `fe_sendauth: no password
supplied`.

**Step 3 — Fix it.** `chmod 600 ~/.pgpass`. Then try `\watch`: run
`SELECT state, count(*) FROM pg_stat_activity GROUP BY 1` followed by `\watch 2` while pgbench runs
in another terminal.

**How it breaks**

| Error text | Meaning | Fix |
|---|---|---|
| `FATAL:  Peer authentication failed for user "app"` | Local socket login, OS user is not `app` | Use `-h 127.0.0.1` (TCP, password) or `sudo -u postgres` |
| `FATAL:  role "ops" does not exist` | psql defaults the role to your OS user name | Pass `-U USER` |
| `FATAL:  database "ops" does not exist` | psql defaults the database to the role name | Pass a database name |
| `fe_sendauth: no password supplied` | Non-interactive run without `.pgpass` | Fix `.pgpass` or use a secret-backed env var |

**Why it matters for troubleshooting.** During an incident you will type `psql` before anything
else. The defaults (role and database named after your OS user, socket connection, peer auth)
explain most "I can't even get in" moments.

**Next step:** the same errors from a remote app server: the "can't connect" checklist.

### listen_addresses and pg_hba.conf

**Level:** [L1 · Junior] · about 60 minutes

**Concept.** A connection from an app server has to pass seven gates, in order. Each failing gate
produces a different error, so **the exact error text tells you which gate to look at**.

```
 app1 192.0.2.50                                                 db1 192.0.2.21
   │ 1. DNS: db1.example.internal → 192.0.2.21 ?              (getent ahosts)
   │ 2. Route + firewalls (UFW/nftables on db1, AWS SG) ?     (nc -vz, tcpdump)
   │ 3. Is PostgreSQL listening on 192.0.2.21:5432 ?          (listen_addresses, ss -ltnp)
   │ 4. pg_hba.conf: is there a rule for this host/user/db ?  (first match wins)
   │ 5. Authentication: right password, right method ?        (scram-sha-256)
   │ 6. Database exists, role may CONNECT ?
   │ 7. A free connection slot ?                              (max_connections)
   ▼   then TLS requirements (sslmode) on top
```

| Error text (from psql or the app log) | Gate | What to check |
|---|---|---|
| `could not translate host name "db1.example.internal" to address: Name or service not known` | 1 DNS | `getent ahosts` from the app host or container ([DNS](08-dns.md)) |
| `Connection timed out` | 2 Network | Firewall drop, security group, wrong route ([Network](02-network.md)) |
| `No route to host` | 2 Network | Host down, ARP failure, or a REJECT rule with icmp-host-prohibited |
| `Connection refused` | 3 Listen | Nothing listens on that IP:port; `listen_addresses = 'localhost'` is the default |
| `no pg_hba.conf entry for host "192.0.2.50", user "app", database "appdb", no encryption` | 4 pg_hba | Add a matching `host` or `hostssl` line, then reload |
| `password authentication failed for user "app"` | 5 Auth | Wrong password, or role has no password, or hash is md5 and rule says scram |
| `database "appdb" does not exist` / `permission denied for database` | 6 | Name typo (case!), or missing `GRANT CONNECT` |
| `sorry, too many clients already` | 7 Slots | Section 10, too many connections |

`pg_hba.conf` is read **top to bottom, first match wins**. Each line is
`TYPE DATABASE USER ADDRESS METHOD`. `local` is the Unix socket, `host` is TCP with or without
SSL, `hostssl` is TCP with SSL only. Use `scram-sha-256` for passwords (the default hashing since
PostgreSQL 14), `peer` for local OS users, and never `trust` on anything reachable from a network.

```
# TYPE   DATABASE   USER        ADDRESS            METHOD
local    all        postgres                       peer
local    all        all                            peer
host     all        all         127.0.0.1/32       scram-sha-256
host     all        all         ::1/128            scram-sha-256
hostssl  appdb      app         192.0.2.50/32      scram-sha-256    # app1
hostssl  appdb      app         192.0.2.51/32      scram-sha-256    # app2
hostssl  replication replicator 192.0.2.22/32      scram-sha-256    # standby db2
```

**Key terms:** `listen_addresses` (which local IPs the server binds, restart required),
`pg_hba.conf` (who may connect from where, reload is enough), `pg_hba_file_rules` (parsed view of
the file, with an `error` column), `scram-sha-256`, `peer`, `hostssl`.

**See it on a real system**

```bash
sudo ss -ltnp 'sport = :5432'
sudo -u postgres psql -c "SHOW listen_addresses;"
sudo -u postgres psql -c "SELECT line_number, type, database, user_name, address, auth_method, error FROM pg_hba_file_rules;"
sudo ufw status numbered
```

```
State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port Process
LISTEN 0      200         127.0.0.1:5432       0.0.0.0:*     users:(("postgres",pid=1012,fd=7))
LISTEN 0      200             [::1]:5432          [::]:*     users:(("postgres",pid=1012,fd=6))

 listen_addresses
------------------
 localhost

 line_number | type  |   database    | user_name |  address  | auth_method | error
-------------+-------+---------------+-----------+-----------+-------------+-------
         118 | local | {all}         | {postgres}|           | peer        |
         123 | local | {all}         | {all}     |           | peer        |
         125 | host  | {all}         | {all}     | 127.0.0.1 | scram-sha-256 |
         127 | host  | {all}         | {all}     | ::1       | scram-sha-256 |
         130 | local | {replication} | {all}     |           | peer        |
         131 | host  | {replication} | {all}     | 127.0.0.1 | scram-sha-256 |
         132 | host  | {replication} | {all}     | ::1       | scram-sha-256 |

Status: active
     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    Anywhere
```

→ Listening on loopback only, no rule for remote hosts, and UFW does not open 5432. Three gates are
closed, which is the correct default. Opening them is a deliberate, three-part change.

**Hands-on lab (test VM only)**

**Step 1 — Break it from the outside.** From app1 (192.168.56.11):

```bash
psql "host=192.168.56.21 dbname=appdb user=app connect_timeout=5" -c "SELECT 1;"
```

```
psql: error: connection to server at "192.168.56.21", port 5432 failed: Connection refused
	Is the server running on that host and accepting TCP/IP connections?
```

→ Refused means a host answered with a TCP reset: db1 is up, but nothing listens on that address.

**Step 2 — Open gate 3 (listen).** On db1:

```bash
echo "listen_addresses = 'localhost,192.168.56.21'" | sudo tee /etc/postgresql/16/main/conf.d/10-listen.conf
sudo systemctl restart postgresql@16-main
sudo ss -ltnp 'sport = :5432'
```

Retry from app1. If UFW is active on db1 you now get `Connection timed out` (gate 2), because UFW
drops the SYN silently. Open it for the app host only:

```bash
sudo ufw allow from 192.168.56.11 to any port 5432 proto tcp comment 'postgres from app1'
```

Retry from app1:

```
psql: error: connection to server at "192.168.56.21", port 5432 failed: FATAL:  no pg_hba.conf entry for host "192.168.56.11", user "app", database "appdb", SSL encryption
connection to server at "192.168.56.21", port 5432 failed: FATAL:  no pg_hba.conf entry for host "192.168.56.11", user "app", database "appdb", no encryption
```

→ Now PostgreSQL itself answers, which proves gates 1–3 are fine. The message names the exact
host, user and database it was looking for; the two lines are psql's default `sslmode=prefer`
trying TLS first and then retrying without it.

**Step 3 — Open gate 4 (pg_hba) and reload.**

```bash
echo "hostssl appdb app 192.168.56.11/32 scram-sha-256" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

Retry: you get a password prompt, and with the right password, a result.

**Step 4 — Break it again: rule order.** Insert a line `host all all 192.168.56.0/24 reject`
**above** your new line, reload, and retry. You get `pg_hba.conf rejects connection for host
"192.168.56.11", user "app", database "appdb", SSL encryption`. First match wins. Remove the
reject line and reload.

**How it breaks**

| Symptom | First command | Where to go |
|---|---|---|
| Works on the DB host, not from the app host | `sudo ss -ltnp 'sport = :5432'` on the DB host | Section 10, app can't connect |
| Works from the host, not from a container | `docker exec CONTAINER getent ahosts DBHOST` | [Docker reference](14-docker-containers.md) |
| Worked yesterday, fails after the DB host got a new IP | `listen_addresses` lists the old IP; the log shows `could not bind IPv4 address` and the server listens only on the remaining addresses | section 10 |
| RDS: timeout | the DB security group inbound rules | [AWS](16-aws-cloud.md) |

**Why it matters for troubleshooting.** "Can't connect to the database" sounds like one problem
but is seven. Reading the error text tells you which of the seven it is, and the fix for one gate
never fixes another, which is why random changes do not help.

**Next step:** once you can connect, look at what everyone else connected is doing.

### Sessions with pg_stat_activity

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** `pg_stat_activity` has one row per server process: client sessions plus background
workers. It is the database's `ps`. The columns that matter in incidents:

| Column | Meaning |
|---|---|
| `pid` | Server process ID; the same PID you see in `ps` and `top` on the host |
| `usename`, `datname`, `application_name` | Who, which database, which app (if the app sets it) |
| `client_addr`, `client_port` | Where from; matches `ss` output |
| `backend_start`, `xact_start`, `query_start`, `state_change` | When the session, transaction, statement and state began |
| `state` | `active`, `idle`, `idle in transaction`, `idle in transaction (aborted)` |
| `wait_event_type`, `wait_event` | What an active session is waiting for: `Lock`, `LWLock`, `IO`, `Client`, `IPC`, `Timeout` |
| `backend_type` | `client backend` for app sessions; `autovacuum worker`, `walsender` and others |
| `query` | Current statement if active, otherwise the **last** one it ran |

Two ways to stop a session, gentlest first:

- `pg_cancel_backend(PID)` cancels the **running statement**. The session survives; the app gets
  `ERROR: canceling statement due to user request`. It does nothing to an idle-in-transaction
  session, because there is no running statement to cancel.
- `pg_terminate_backend(PID)` ends the **whole session**; its open transaction rolls back and the
  app sees a dropped connection. Use it for idle-in-transaction blockers and leaked connections.

> Never terminate sessions in bulk without a `WHERE` that you have run as a `SELECT` first. Never
> terminate `walsender` (replication) or `autovacuum` processes to "free slots": the first breaks
> replication, the second only postpones the cleanup that is already overdue.

Ask developers to set `application_name` in their connection string
(`?application_name=billing-worker`). It costs nothing and turns "someone has 80 connections" into
"the billing worker on app2 has 80 connections".

**See it on a real system**

```bash
sudo -u postgres psql -c "
SELECT datname, usename, application_name, client_addr, state, count(*)
FROM pg_stat_activity WHERE backend_type = 'client backend'
GROUP BY 1,2,3,4,5 ORDER BY count(*) DESC;"

sudo -u postgres psql -c "
SELECT pid, now() - query_start AS runtime, wait_event_type, wait_event, left(query, 70) AS query
FROM pg_stat_activity
WHERE state = 'active' AND backend_type = 'client backend' AND pid <> pg_backend_pid()
ORDER BY runtime DESC LIMIT 5;"
```

```
 datname | usename | application_name | client_addr |        state        | count
---------+---------+------------------+-------------+---------------------+-------
 appdb   | app     | web              | 192.0.2.50  | idle                |    38
 appdb   | app     | web              | 192.0.2.51  | idle                |    36
 appdb   | app     | billing-worker   | 192.0.2.52  | idle in transaction |    11
 appdb   | app     | web              | 192.0.2.50  | active              |     3
 appdb   | grafana | grafana          | 192.0.2.60  | idle                |     2

 pid  |     runtime     | wait_event_type |  wait_event   |                                 query
------+-----------------+-----------------+---------------+-----------------------------------------------------------------------
 7312 | 00:04:51.20833  | IO              | DataFileRead  | SELECT customer_id, sum(total) FROM orders GROUP BY customer_id ORDER
 7340 | 00:00:02.11720  | Lock            | transactionid | UPDATE orders SET status = 'paid' WHERE id = 991
 7351 | 00:00:00.00410  |                 |               | SELECT * FROM orders WHERE id = 120034
```

→ Eleven `idle in transaction` sessions from the billing worker is a smell (a code path that
forgets to commit). PID 7312 has been reading data files for five minutes: a report on the primary.
PID 7340 waits on a row lock; the lock topic below finds who holds it.

**Hands-on lab (test VM only)**

**Step 1 — Build: a runaway query.** In one terminal run
`psql -h 127.0.0.1 -U app appdb -c "SELECT pg_sleep(600);"`. In another, find it with the
second query above.

**Step 2 — Cancel it.** `SELECT pg_cancel_backend(PID);` The first terminal prints
`ERROR:  canceling statement due to user request` and stays connected.

**Step 3 — Break it: cancel is not enough.** In the first terminal run `BEGIN;` then
`UPDATE orders SET status = 'paid' WHERE id = 1;` and leave it. `pg_cancel_backend` on that PID
returns `t` but the session stays `idle in transaction` and keeps its lock. Use
`SELECT pg_terminate_backend(PID);` and the next command in the first terminal reports
`FATAL:  terminating connection due to administrator command`.

**How it breaks**

| Symptom | First query | Where to go |
|---|---|---|
| Connection count near the limit | grouped query above | Section 10, too many connections |
| Many `active` with `wait_event_type = Lock` | blocking tree (next topic) | Section 10, locks |
| Many `active` with `IO` waits | `iostat -xz 1` on the host | [Slow system](23-playbook-slow-system.md) |
| High CPU on the DB host | match top's PIDs to `pg_stat_activity.pid` | [CPU](03-cpu-performance.md) |

**Why it matters for troubleshooting.** The host PID in `top` is the `pid` here. That one join
turns "postgres is using 100% CPU" into "this exact query from this exact app is using 100% CPU",
which is a ticket a developer can act on.

**Next step:** sessions that wait on `Lock` need the lock view.

### Locks with pg_locks

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** `pg_locks` lists every lock held (`granted = true`) or awaited (`granted = false`).
For incidents you rarely read it raw: `pg_blocking_pids()` (section 1) gives the tree, and
`pg_locks` adds **which mode on which table**, which tells you *why* something waits. This table is
worth memorising, because it predicts what a migration will do to live traffic:

| Statement | Table lock mode | Blocks reads? | Blocks writes? |
|---|---|---|---|
| `SELECT` | ACCESS SHARE | no | no |
| `INSERT`, `UPDATE`, `DELETE` | ROW EXCLUSIVE | no | no (rows lock individually) |
| `VACUUM` (plain), `ANALYZE`, `CREATE INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | no | no |
| `ALTER TABLE … VALIDATE CONSTRAINT` | SHARE UPDATE EXCLUSIVE | no | no |
| `CREATE INDEX` (without CONCURRENTLY) | SHARE | no | **yes** |
| `REINDEX` (without CONCURRENTLY) | SHARE on the table, ACCESS EXCLUSIVE on the index | in practice yes: planning a query locks every index of the table | **yes** |
| `ALTER TABLE … ADD FOREIGN KEY` | SHARE ROW EXCLUSIVE (both tables) | no | **yes** |
| Most `ALTER TABLE`, `DROP`, `TRUNCATE`, `VACUUM FULL`, `CLUSTER` | ACCESS EXCLUSIVE | **yes** | **yes** |

Even a fast ACCESS EXCLUSIVE operation (adding a nullable column takes milliseconds) is dangerous
if it has to **wait** for the lock, because of the queue effect in section 1.

Turn on `log_lock_waits = on` in production. Any lock wait longer than `deadlock_timeout` (1 s) is
then logged with the PIDs involved, so you can investigate lock storms after the fact.

**See it on a real system**

```bash
sudo -u postgres psql -d appdb -c "
SELECT l.pid, l.locktype, l.relation::regclass AS relation, l.mode, l.granted,
       a.state, left(a.query, 45) AS query
FROM pg_locks l JOIN pg_stat_activity a USING (pid)
WHERE a.datname = 'appdb' AND l.locktype IN ('relation','transactionid')
  AND a.pid <> pg_backend_pid()
ORDER BY l.granted, l.pid;"
```

```
 pid  |   locktype    | relation |        mode         | granted |        state        |                   query
------+---------------+----------+---------------------+---------+---------------------+-------------------------------------------
 6002 | relation      | orders   | AccessExclusiveLock | f       | active              | ALTER TABLE orders ADD COLUMN note text
 6003 | relation      | orders   | AccessShareLock     | f       | active              | SELECT * FROM orders WHERE id = 7
 6001 | relation      | orders   | AccessShareLock     | t       | idle in transaction | SELECT count(*) FROM orders
 6001 | transactionid |          | ExclusiveLock       | t       | idle in transaction | SELECT count(*) FROM orders
```

→ Rows with `granted = f` are waiting. The ALTER wants AccessExclusiveLock on `orders` and the
only granted lock on `orders` belongs to 6001: that is the root blocker.

**Hands-on lab (test VM only)**

**Step 1 — Build: log lock waits.**

```bash
echo "log_lock_waits = on" | sudo tee /etc/postgresql/16/main/conf.d/50-locks.conf
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

**Step 2 — Break it: a row-lock wait.** Terminal A: `BEGIN; UPDATE orders SET status = 'paid'
WHERE id = 991;` Terminal B: `UPDATE orders SET status = 'shipped' WHERE id = 991;` (hangs).
Wait 15 seconds, `COMMIT;` in A, then read the log:

```bash
sudo grep -A3 'still waiting' /var/log/postgresql/postgresql-16-main.log | tail -n 6
```

```
2026-10-03 10:31:05.412 UTC [7340] app@appdb LOG:  process 7340 still waiting for ShareLock on transaction 81234 after 1000.118 ms
2026-10-03 10:31:05.412 UTC [7340] app@appdb DETAIL:  Process holding the lock: 7338. Wait queue: 7340.
2026-10-03 10:31:05.412 UTC [7340] app@appdb CONTEXT:  while updating tuple (8123,41) in relation "orders"
2026-10-03 10:31:19.877 UTC [7340] app@appdb LOG:  process 7340 acquired ShareLock on transaction 81234 after 15465.302 ms
```

→ Row locks show up as a wait on the other **transaction** (`ShareLock on transaction 81234`),
and the log names the holder. This is the evidence you attach to a ticket for the app team.

**Step 3 — Fix it.** Nothing to fix here except the habit: keep `log_lock_waits` on and look at
these lines first when someone says "it was slow at 10:31".

**How it breaks:** see the locks playbook in section 10 and the migration rules in section 11.

**Why it matters for troubleshooting.** The lock-mode table lets you predict impact before a change
and explain it after one. "The ALTER needed ACCESS EXCLUSIVE and waited behind a report" is a root
cause; "the database was slow" is not.

**Next step:** queries that do not wait but are simply slow need the slow query log.

### Slow query log and pg_stat_statements

**Level:** [L2 · Mid] · about 60 minutes

**Concept.** Two complementary tools:

- **`log_min_duration_statement`** logs every statement slower than a threshold, with its duration
  and text. It answers "what was slow at 10:31?" with exact examples.
- **`pg_stat_statements`** (an extension shipped with PostgreSQL) aggregates **all** statements by
  normalized shape (`WHERE id = $1`), with call counts and total, mean and max time. It answers
  "what costs the most overall?", which is usually a fast query called a million times, not the
  slowest single query.

Related logging worth enabling: `log_temp_files = 0` (queries spilling sorts to disk because
`work_mem` is too small), `log_autovacuum_min_duration = '10s'`, `log_checkpoints = on` (default
since 15) and `auto_explain` (logs the plan of slow queries automatically).

**Key terms:** threshold, normalized query, `queryid`, `total_exec_time`, `mean_exec_time`,
`calls`, `shared_preload_libraries`, `auto_explain`.

**See it on a real system**

```bash
sudo grep 'duration:' /var/log/postgresql/postgresql-16-main.log | tail -n 2
sudo -u postgres psql -d appdb -c "
SELECT calls, round(total_exec_time) AS total_ms, round(mean_exec_time::numeric, 1) AS mean_ms,
       rows, left(query, 60) AS query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 5;"
```

```
2026-10-03 10:40:12.118 UTC [7312] app@appdb LOG:  duration: 2871.442 ms  statement: SELECT customer_id, sum(total) FROM orders GROUP BY customer_id ORDER BY 2 DESC LIMIT 20
2026-10-03 10:40:15.902 UTC [7366] app@appdb LOG:  duration: 612.007 ms  statement: SELECT * FROM orders WHERE status = 'new' ORDER BY created_at LIMIT 50

  calls  | total_ms | mean_ms |  rows   |                            query
---------+----------+---------+---------+--------------------------------------------------------------
  418220 |  1840112 |     4.4 |  418220 | SELECT * FROM orders WHERE customer_id = $1 AND status = $2
     612 |   374591 |   612.1 |   30600 | SELECT * FROM orders WHERE status = $1 ORDER BY created_at L
      44 |   126344 |  2871.5 |     880 | SELECT customer_id, sum(total) FROM orders GROUP BY customer
  910432 |    91022 |     0.1 |  910432 | UPDATE pgbench_accounts SET abalance = abalance + $1 WHERE a
    3108 |    20480 |     6.6 |    3108 | SELECT count(*) FROM orders WHERE customer_id = $1
```

→ The log points at the 2.9-second report, but `pg_stat_statements` shows the real cost: a 4 ms
query called 418,220 times is 1,840 seconds of database time, five times the report. Fix the top
of *this* list first.

**Hands-on lab (test VM only)**

**Step 1 — Build: enable pg_stat_statements.** It must be preloaded, so this is a restart:

```bash
echo "shared_preload_libraries = 'pg_stat_statements'" | sudo tee /etc/postgresql/16/main/conf.d/40-pgss.conf
sudo systemctl restart postgresql@16-main
sudo -u postgres psql -d appdb -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
pgbench -h 127.0.0.1 -U app -c 4 -T 30 appdb > /dev/null
```

Run the query above and find pgbench's statements.

**Step 2 — Break it: log everything.** Set `log_min_duration_statement = 0` in
`conf.d/50-logging.conf`, reload, run pgbench for 30 seconds, then `ls -lh /var/log/postgresql/`.
The log grows by tens of megabytes in seconds and pgbench's TPS drops noticeably. On a busy
production server this fills `/var/log` within hours.

**Step 3 — Fix it.** Restore `'500ms'` (or `'250ms'` for latency-sensitive apps) and reload. If you
need every statement for a short investigation, set it for one role or database only
(`ALTER ROLE app SET log_min_duration_statement = 0;`) and time-box it.

**How it breaks**

| Symptom | First command | Where to go |
|---|---|---|
| Endpoint slow since a deploy | top-5 by `total_exec_time`, compare with yesterday's snapshot | Section 10, slow after deploy |
| `temporary file: path "base/pgsql_tmp/…", size 1073741824` in the log | find the query, raise `work_mem` for it only | this topic |
| `/var/log/postgresql` filling the disk | log thresholds, logrotate | [Logs & journal](06-logs-journal.md) |

**Why it matters for troubleshooting.** Without these two tools "the database is slow" stays an
opinion. With them it becomes a ranked list of statements with numbers, which is what you bring to
the app team.

**Next step:** once you know *which* query, `EXPLAIN` tells you *why* it is slow.

### EXPLAIN ANALYZE basics

**Level:** [L2 · Mid] · about 60 minutes

**Concept.** `EXPLAIN` shows the **plan** the optimizer picked: a tree of nodes (scan a table,
join, sort, aggregate), each with an estimated cost and row count. `EXPLAIN ANALYZE` **runs the
query** and adds the actual time and rows per node; `BUFFERS` adds how many 8 KB pages came from
cache (`hit`) or disk (`read`). Read a plan from the most-indented node outward. Three things to
look for:

1. **Seq Scan on a big table with a selective filter** (`Rows Removed by Filter` in the millions):
   a missing or unusable index.
2. **Estimated rows far from actual rows** (`rows=20` vs `rows=500000`): stale statistics or
   correlated columns; the planner chose a plan for the wrong data size. Running `ANALYZE` on the
   table (`ANALYZE orders;`; `ANALYZE TABLE` is MySQL's spelling) often fixes it.
3. **Sort or hash spilling to disk** (`Sort Method: external merge  Disk: 51200kB`): `work_mem`
   too small for that query.

> `EXPLAIN ANALYZE` **executes** the statement. For `UPDATE`, `DELETE` or `INSERT` always wrap it:
> `BEGIN; EXPLAIN ANALYZE UPDATE …; ROLLBACK;`. On a production primary prefer plain `EXPLAIN`
> (no ANALYZE) first, or run ANALYZE on a replica or a restored copy.

**See it on a real system** (index from section 1 dropped first, so you see both plans)

```bash
psql -h 127.0.0.1 -U app appdb <<'SQL'
DROP INDEX CONCURRENTLY IF EXISTS orders_customer_id_idx;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE customer_id = 4242;
CREATE INDEX CONCURRENTLY orders_customer_id_idx ON orders (customer_id);
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE customer_id = 4242;
SQL
```

```
                                                       QUERY PLAN
------------------------------------------------------------------------------------------------------------------------
 Gather  (cost=1000.00..15554.43 rows=20 width=34) (actual time=0.512..41.873 rows=21 loops=1)
   Workers Planned: 2
   Workers Launched: 2
   Buffers: shared hit=2208 read=6126
   ->  Parallel Seq Scan on orders  (cost=0.00..14552.43 rows=8 width=34) (actual time=6.104..36.012 rows=7 loops=3)
         Filter: (customer_id = 4242)
         Rows Removed by Filter: 333326
         Buffers: shared hit=2208 read=6126
 Planning Time: 0.098 ms
 Execution Time: 41.902 ms

                                                         QUERY PLAN
----------------------------------------------------------------------------------------------------------------------------
 Index Scan using orders_customer_id_idx on orders  (cost=0.42..84.62 rows=20 width=34) (actual time=0.031..0.074 rows=21 loops=1)
   Index Cond: (customer_id = 4242)
   Buffers: shared hit=24
 Planning Time: 0.143 ms
 Execution Time: 0.093 ms
```

→ Before: three processes read all 8,334 pages and threw away a million rows to return 21. After:
24 pages, all from cache, 450 times faster. `loops=3` means the node ran three times (leader plus
two workers), so its actual rows are per loop.

**Hands-on lab (test VM only)**

**Step 1 — Break it: stale statistics.** Stop autovacuum on the table, bulk-insert skewed data,
and look at the estimate:

```bash
psql -h 127.0.0.1 -U app appdb <<'SQL'
ALTER TABLE orders SET (autovacuum_enabled = off);
INSERT INTO orders (customer_id, status, total)
SELECT 7, 'new', 9.99 FROM generate_series(1, 300000);
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 7;
SQL
```

```
 Index Scan using orders_customer_id_idx on orders  (cost=0.42..84.62 rows=20 width=34) (actual time=0.040..96.311 rows=300019 loops=1)
```

→ Estimated 20 rows, actual 300,019. The planner believes customer 7 is like everyone else. In a
join, a 15,000-fold misestimate produces catastrophic plans (nested loops over 300k rows).

**Step 2 — Fix it.** `ANALYZE orders;` and re-run the EXPLAIN: the estimate becomes about 300,000
and the plan changes to a sequential or bitmap scan, which is cheaper for that many rows. Then put
things back: `ALTER TABLE orders RESET (autovacuum_enabled);` and
`DELETE FROM orders WHERE customer_id = 7 AND total = 9.99;`.

**How it breaks:** see the "slow queries after deploy" playbook in section 10.

**Why it matters for troubleshooting.** EXPLAIN turns "add more CPU" into "add this index" or "run
ANALYZE after the import job". MySQL's `EXPLAIN ANALYZE` (8.0.18 and later) reads the same way.

**Next step:** dead rows from all those updates need cleaning; that is VACUUM.

### VACUUM, autovacuum and bloat

**Level:** [L2 · Mid] → [L3 · Senior] · about 60 minutes

**Concept.** Because of MVCC, every `UPDATE` and `DELETE` leaves a **dead tuple**. **VACUUM** marks
the space of dead tuples reusable (it does not return it to the OS) and updates the visibility map
that makes index-only scans possible. **Autovacuum** runs it automatically when a table's dead
tuples exceed `autovacuum_vacuum_threshold + autovacuum_vacuum_scale_factor x rows` (50 + 20%;
PostgreSQL 18 also caps the trigger at `autovacuum_vacuum_max_threshold`, 100 million dead tuples by
default), and also runs ANALYZE. Things go wrong in three ways:

- **Vacuum cannot remove dead tuples** because something still needs them: a long-running or
  idle-in-transaction session, an abandoned replication slot, `hot_standby_feedback` from a replica
  running long queries, or a forgotten prepared transaction (`pg_prepared_xacts`). The table grows
  and queries slow down (**bloat**).
- **Vacuum is too slow** for the write rate on big tables (20% of a billion rows is a lot of dead
  tuples before it even starts). Tune per table, e.g. `ALTER TABLE orders SET
  (autovacuum_vacuum_scale_factor = 0.02);`.
- **Transaction ID wraparound.** Transaction IDs are 32-bit; old rows must be **frozen** before the
  counter wraps. If freezing falls far behind, PostgreSQL logs
  `WARNING:  database "appdb" must be vacuumed within N transactions`, and close to the limit it
  stops accepting commands that assign new transaction IDs to protect data. That is a full outage
  that only a long VACUUM fixes. Monitor `age(datfrozenxid)`.

> `VACUUM FULL` rewrites the table to give space back to the OS, but it holds an **ACCESS
> EXCLUSIVE** lock for the whole run (no reads, no writes) and needs free disk equal to the table's
> live size. On a production table that is an outage. Safer, in order: fix what blocks vacuum and
> let plain VACUUM reuse the space; tune autovacuum; use the `pg_repack` extension, which rebuilds
> online with only brief locks (it still needs the extra disk).

**Key terms:** dead tuple, bloat, autovacuum, freeze, `datfrozenxid`, wraparound, visibility map,
`pg_stat_progress_vacuum`, `pgstattuple`.

**See it on a real system**

```bash
sudo -u postgres psql -d appdb -c "
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       last_autovacuum, last_autoanalyze, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 5;"
sudo -u postgres psql -c "SELECT datname, age(datfrozenxid) AS xid_age FROM pg_database ORDER BY 2 DESC;"
```

```
     relname      | n_live_tup | n_dead_tup | dead_pct |        last_autovacuum        |       last_autoanalyze        |  size
------------------+------------+------------+----------+-------------------------------+-------------------------------+--------
 orders           |    1000000 |    1874200 |     65.2 | 2026-09-28 02:11:40.118+00    | 2026-09-28 02:11:41.007+00    | 198 MB
 pgbench_accounts |    2000000 |      41022 |      2.0 | 2026-10-03 10:20:12.551+00    | 2026-10-03 10:20:14.330+00    | 301 MB
 pgbench_tellers  |        200 |        118 |     37.1 | 2026-10-03 10:42:01.002+00    | 2026-10-03 10:42:01.005+00    | 120 kB

  datname  |  xid_age
-----------+-----------
 appdb     | 184023117
 postgres  |  12004118
 template1 |  12004118
 template0 |  12004118
```

→ `orders` has not been autovacuumed for five days and is 65% dead: something is blocking or
autovacuum is disabled for it. `appdb`'s xid age of 184 million is close to
`autovacuum_freeze_max_age` (200 million), so an aggressive anti-wraparound vacuum is about to
start on its own; fine if it can finish, an emergency if something blocks it.

**Hands-on lab (test VM only)**

**Step 1 — Build bloat.** Disable autovacuum on the table and update every row twice:

```bash
psql -h 127.0.0.1 -U app appdb -c "ALTER TABLE orders SET (autovacuum_enabled = off);" \
  -c "UPDATE orders SET total = total + 1;" -c "UPDATE orders SET total = total - 1;" \
  -c "SELECT pg_size_pretty(pg_total_relation_size('orders'));"
```

The table roughly triples in size.

**Step 2 — Break it: block the cleanup.** In terminal A open a transaction and take a snapshot:
`BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT 1;` (leave it open). Then update again and vacuum in
terminal B:

```bash
psql -h 127.0.0.1 -U app appdb -c "UPDATE orders SET total = total + 1;" -c "VACUUM (VERBOSE) orders;" 2>&1 | grep -E 'finished|tuples|removable'
```

```
INFO:  finished vacuuming "appdb.public.orders": index scans: 1
tuples: 2000000 removed, 2000000 remain, 1000000 are dead but not yet removable
removable cutoff: 81904, which was 3 XIDs old when operation ended
```

→ "dead but not yet removable" is the signature of a blocker. The 2 million versions from step 1
are older than terminal A's snapshot and go; the million from the new `UPDATE` stay. The
`removable cutoff` stays at the oldest snapshot still open, here terminal A.

**Step 3 — Fix it.** `COMMIT;` in terminal A, run `VACUUM (VERBOSE) orders;` again and see the dead
tuples removed. The file size does not shrink (space is reused, not returned), which is normal.
Re-enable autovacuum: `ALTER TABLE orders RESET (autovacuum_enabled);`.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| Table and disk grow while row count is flat | `n_dead_tup`, oldest `xact_start`, `pg_replication_slots` | this topic |
| `must be vacuumed within N transactions` | `SELECT datname, age(datfrozenxid) FROM pg_database;` | escalate now; remove blockers, run `VACUUM (VERBOSE)` |
| Queries slower every week, plans unchanged | dead_pct on hot tables | tune per-table autovacuum |
| Autovacuum "always running" on one big table | `SELECT * FROM pg_stat_progress_vacuum;` | raise `maintenance_work_mem`, cost limits |

**Why it matters for troubleshooting.** Bloat and wraparound are slow-burning incidents that a
dashboard catches weeks early and an outage reveals too late. Section 9 turns these queries into
alerts.

**Next step:** the last PostgreSQL limit you will hit is the number of connections.

### max_connections and PgBouncer

**Level:** [L2 · Mid] → [L3 · Senior] · about 75 minutes

**Concept.** Raising `max_connections` is the tempting fix for "too many clients" and usually the
wrong one. Each PostgreSQL connection is a process with its own memory (several MB, plus `work_mem`
per sort), the setting needs a restart, and hundreds of mostly-idle connections still cost CPU in
snapshot and lock bookkeeping. The real fix is to **pool**: many client connections share a few
server connections.

**Do the arithmetic first.** Everything that connects must fit:

```
 app replicas x workers per replica x pool size per worker
 + background workers + cron jobs + migrations + monitoring + admins
 ≤ max_connections − superuser_reserved_connections (3) − reserved_connections (PG 16+)

 Example:  3 replicas x 4 Gunicorn workers x pool 5 = 60
           + 10 (workers) + 5 (cron) + 2 (migration) + 3 (exporters, Grafana) = 80  ≤ 97  OK
           Scale web to 6 replicas: 120 + 20 = 140  > 97  → "too many clients" at the next deploy
```

**PgBouncer** is a lightweight pooler that speaks the PostgreSQL protocol, usually on port 6432,
either on the DB host or next to the apps. Its **pool mode** decides when a server connection
returns to the pool:

| Pool mode | Server connection released when | Safe for | Breaks |
|---|---|---|---|
| `session` | client disconnects | everything | little pooling benefit for long-lived app pools |
| `transaction` | transaction ends | most web apps | session state: `SET` without `LOCAL`, advisory locks, `LISTEN`, temp tables across transactions, prepared statements unless `max_prepared_statements` is set (PgBouncer 1.21+) |
| `statement` | each statement | rare, autocommit-only | multi-statement transactions |

```
  300 client connections                PgBouncer :6432                 PostgreSQL :5432
 ┌────────────────────────┐         ┌─────────────────────────┐       ┌────────────────────┐
 │ web x 6 replicas       │ ──────▶ │ pool appdb/app          │ ────▶ │ 20 server          │
 │ workers, cron          │ ──────▶ │ default_pool_size = 20  │       │ connections        │
 └────────────────────────┘         │ max_client_conn = 1000  │       │ max_connections 100│
                                    │ cl_waiting queue        │       └────────────────────┘
                                    └─────────────────────────┘
```

**Key terms:** pool mode, `default_pool_size`, `max_client_conn`, `reserve_pool_size`,
`cl_active`, `cl_waiting`, `sv_active`, `sv_idle`, `maxwait`, `auth_file`, admin console.

**See it on a real system**

```bash
sudo cat /etc/pgbouncer/pgbouncer.ini | grep -Ev '^\s*(;|$)'
psql -h 127.0.0.1 -p 6432 -U pgbouncer_admin pgbouncer -c "SHOW POOLS;"
```

```
[databases]
appdb = host=127.0.0.1 port=5432 dbname=appdb
[pgbouncer]
listen_addr = 127.0.0.1,192.168.56.21
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
admin_users = pgbouncer_admin
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
reserve_pool_size = 5
max_prepared_statements = 100
server_idle_timeout = 600

 database  |      user       | cl_active | cl_waiting | sv_active | sv_idle | sv_used | maxwait | pool_mode
-----------+-----------------+-----------+------------+-----------+---------+---------+---------+-------------
 appdb     | app             |        38 |        262 |        20 |       0 |       0 |       2 | transaction
 pgbouncer | pgbouncer       |         1 |          0 |         0 |       0 |       0 |       0 | statement
```

→ All 20 server connections are busy and 262 clients wait, the oldest for 2 seconds (`maxwait`).
The database is protected, but the **pool is now the bottleneck**: either queries are too slow
(fix them; check `pg_stat_statements`) or the pool is too small for the load. Columns are trimmed
here; newer PgBouncer versions show more.

**Hands-on lab (test VM only)**

**Step 1 — Build.** PgBouncer was installed with the lab. Copy the `app` role's SCRAM hash into the
auth file and write the config above:

```bash
sudo -u postgres psql -Atc "SELECT format('\"%s\" \"%s\"', rolname, rolpassword) FROM pg_authid WHERE rolname = 'app';" \
  | sudo tee /etc/pgbouncer/userlist.txt
echo '"pgbouncer_admin" "AdminLabPass-1"' | sudo tee -a /etc/pgbouncer/userlist.txt
sudo chown postgres:postgres /etc/pgbouncer/userlist.txt && sudo chmod 640 /etc/pgbouncer/userlist.txt
sudo systemctl restart pgbouncer
```

**Step 2 — Prove the benefit.** 300 clients through PgBouncer, against a server that allows 97:

```bash
pgbench -h 192.168.56.21 -p 6432 -U app -c 300 -j 4 -T 30 appdb | tail -n 3
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE usename = 'app';"
```

→ The benchmark completes, and the database never sees more than about 20 `app` sessions. The same
command against port 5432 fails as in section 1.

**Step 3 — Break it: lost session state.** Connect twice through 6432 while pgbench keeps running
and run `SELECT pg_backend_pid();` several times in one psql session. In transaction mode the PID
changes between transactions: anything stored in the session (a `SET search_path`, an advisory
lock, a temp table) belongs to a server connection you no longer have. Migration tools that take an
advisory lock to prevent concurrent runs are the classic victim.

**Step 4 — Fix it.** Point migrations and admin tools at the database directly (5432) or at a
separate PgBouncer database entry with `pool_mode=session`; keep the app on the transaction pool.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| `no more connections allowed (max_client_conn)` | `SHOW POOLS;`, `SHOW CLIENTS;` | raise `max_client_conn`, check for client leaks |
| App timeouts, `cl_waiting` high, DB calm | `SHOW POOLS;` then `pg_stat_statements` | slow queries hold the pool |
| `prepared statement "S_1" does not exist` | PgBouncer version, `max_prepared_statements` | this topic |
| `server login has been failing, try again later (server_login_retry)` | PgBouncer log, pg_hba for PgBouncer's address | section 2, pg_hba |

**Why it matters for troubleshooting.** Connection problems after scaling out are arithmetic. A
senior engineer does the sum before the scale-out, and puts a pooler in front before the sum stops
working.

**Next step:** the last senior PostgreSQL skill is moving between major versions.

### Major version upgrades

**Level:** [L3 · Senior] · about 90 minutes

**Concept.** **Minor** upgrades (16.9 → 16.10) only replace binaries: install the package, restart,
done; read the release notes for the occasional "reindex these indexes" note. **Major** upgrades
(16 → 17) change the on-disk format, so the data must be converted. Three methods:

| Method | Downtime | Disk | When |
|---|---|---|---|
| `pg_dump` + `pg_restore` | Long (proportional to size) | 2x | Small databases, or to clean up bloat at the same time |
| `pg_upgrade` (`--link` mode) | Minutes, regardless of size | Almost none with `--link` | The default choice on VMs |
| Logical replication to a new cluster | Seconds (switch over) | 2x, second server | Large databases with tight downtime budgets |

Version lifecycle matters for planning: each major version gets five years of fixes. PostgreSQL 13
reached end of life in November 2025 and **14 (Ubuntu 22.04's default) does so in November 2026**.
Ubuntu keeps patching its own package for the LTS lifetime, but extensions, drivers and managed
services (RDS charges extended support) move on.

Debian/Ubuntu wrap `pg_upgrade` in `pg_upgradecluster`. Rules that prevent bad days: take and
**test** a backup first; install every extension for the new version; run the upgrade on a restored
copy first; after the upgrade run `vacuumdb --all --analyze-in-stages` because `pg_upgrade` before
version 18 does not carry planner statistics, so the first hour after an upgrade without it is
"everything is slow". From 18 on, `pg_upgrade` keeps most statistics (not extended statistics), and
`vacuumdb --all --analyze-in-stages --missing-stats-only` fills in only what is missing.

**See it on a real system**

```bash
pg_lsclusters
apt-cache policy postgresql-17 | head -3          # is a newer major available (PGDG)?
```

```
Ver Cluster Port Status Owner    Data directory              Log file
16  main    5432 online postgres /var/lib/postgresql/16/main /var/log/postgresql/postgresql-16-main.log

postgresql-17:
  Installed: (none)
  Candidate: 17.6-1.pgdg24.04+1
```

**Hands-on lab (test VM only, with the PGDG repo added)**

**Step 1 — Install the new major.** `sudo apt install -y postgresql-17`. The package creates an
empty `17/main` cluster on port 5433.

**Step 2 — Break it.** Run `sudo pg_upgradecluster -v 17 -m upgrade --link 16 main`:

```
Error: target cluster 17/main already exists
```

→ The auto-created empty cluster is in the way. This error is harmless; the dangerous variant is
connecting apps to the empty 5433 cluster by mistake.

**Step 3 — Fix it and upgrade.**

```bash
sudo pg_dropcluster 17 main --stop            # the EMPTY new cluster, check the version twice
sudo pg_upgradecluster -v 17 -m upgrade --link 16 main
pg_lsclusters
sudo -u postgres vacuumdb --all --analyze-in-stages
```

```
Ver Cluster Port Status Owner    Data directory              Log file
16  main    5433 down   postgres /var/lib/postgresql/16/main /var/log/postgresql/postgresql-16-main.log
17  main    5432 online postgres /var/lib/postgresql/17/main /var/log/postgresql/postgresql-17-main.log
```

→ The new cluster took over port 5432; the old one is stopped on 5433. With `--link` the old
cluster **must not be started again** once the new one has run, because they share data files.
Verify the application, then remove the old cluster with `sudo pg_dropcluster 16 main`.

**How it breaks**

| Symptom | First command | Where to go |
|---|---|---|
| Upgrade aborts: extension missing | `pg_upgrade` check output names it | install `postgresql-17-EXTENSION` |
| Everything slow right after the upgrade | `SELECT relname, last_analyze, last_autoanalyze FROM pg_stat_user_tables;` | run `vacuumdb --analyze-in-stages` |
| Docker container fails after a tag bump | `docker logs` shows `database files are incompatible with server` | section 7 |

**Why it matters for troubleshooting.** Upgrades are planned changes with known failure modes. A
written runbook with a tested rollback (keep the old cluster until verified, or restore from the
backup you tested) is what makes them boring.

**Next step:** the same operational skills, in MySQL and MariaDB.

---

## 3. MySQL and MariaDB operations

> 📚 **Study path:** 1) Note: the matching topic in section 2 first; the concepts carry over, and this section concentrates on what is different in MySQL and MariaDB · 2) KodeKloud: *DevOps Pre-Requisite Course* — 2 Tier Applications, an application and its database across two hosts, if you have not done it yet ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) · 3) Read: the reference manual chapters on server administration and the InnoDB storage engine in the [MySQL documentation](https://dev.mysql.com/doc/); a KodeKloud MySQL course is not in the verified map (check the current catalog) · 4) Practice: the labs below on db1, then *Linux Challenges* ([course](https://kodekloud.com/courses/linux-challenges)).

MySQL and MariaDB share a history, a protocol (port 3306) and most commands, but they have
diverged: different GTID formats, different authentication defaults, different backup tools. The
ideas from sections 1 and 2 carry over; this area maps them to MySQL's names and tools.

### Install, layout and the mysql client

**Level:** [L0 · Fresher] → [L1 · Junior] · about 40 minutes

**Concept.** One server process, `mysqld`, one thread per connection, storage engine **InnoDB**
for everything that matters (avoid MyISAM: no transactions, no crash safety). On Ubuntu the
`root` database account authenticates with **auth_socket**: only the OS root user can log in as
it, through the socket, with `sudo mysql`. Settings come from option files, and
`SET PERSIST` writes `mysqld-auto.cnf` in the data directory, which overrides them (the MySQL twin
of `ALTER SYSTEM`).

| What | Ubuntu MySQL | Ubuntu MariaDB | RHEL / Rocky |
|---|---|---|---|
| Config | `/etc/mysql/mysql.conf.d/mysqld.cnf` | `/etc/mysql/mariadb.conf.d/50-server.cnf` | `/etc/my.cnf`, `/etc/my.cnf.d/` |
| Data | `/var/lib/mysql` | `/var/lib/mysql` | `/var/lib/mysql` |
| Error log | `/var/log/mysql/error.log` | journal (`journalctl -u mariadb`) | `/var/log/mysqld.log` (MySQL's own repo), `/var/log/mysql/mysqld.log` (AppStream), `/var/log/mariadb/mariadb.log` (MariaDB); confirm with `SELECT @@log_error;` |
| Unit | `mysql` | `mariadb` | `mysqld` or `mariadb` |
| Client, dump | `mysql`, `mysqldump` | `mariadb`, `mariadb-dump` (old names still work) | same as upstream |

**Versions.** Upstream MySQL 8.0 reached end of life in April 2026; the long-term series is
**8.4 LTS**. An in-place upgrade from 8.0 to 8.4 is supported; check first with MySQL Shell's
upgrade checker (`util.checkForServerUpgrade()`). Two 8.4 changes bite operators:
`mysql_native_password` is disabled by default (old clients and some replication setups break),
and the old `MASTER`/`SLAVE` statements are gone (use `SHOW REPLICA STATUS`,
`CHANGE REPLICATION SOURCE TO`). Check which series your distribution's package tracks.

| Client command | What it does |
|---|---|
| `sudo mysql` | Log in as root through the socket (Ubuntu) |
| `mysql -h HOST -u USER -p DBNAME` | TCP login with a password prompt |
| `STATUS` or `\s` | Server version, connection, uptime, threads |
| `SHOW DATABASES;`, `USE DBNAME;`, `SHOW TABLES;` | Navigate |
| `SHOW CREATE TABLE TABLE\G` | Full definition with indexes; `\G` prints vertically |
| `SHOW VARIABLES LIKE 'max_conn%';` | Configuration values |
| `SHOW GLOBAL STATUS LIKE 'Threads%';` | Counters and gauges |

Keep credentials for scripts in `~/.my.cnf` (mode 600) under a `[client]` section, never as
`-pPASSWORD` on the command line.

**See it on a real system**

```bash
systemctl status mysql --no-pager | head -4
sudo mysql -e "SELECT @@version, @@datadir, @@log_error, @@bind_address, @@max_connections, @@innodb_buffer_pool_size/1024/1024 AS bp_mb;"
```

```
● mysql.service - MySQL Community Server
     Loaded: loaded (/usr/lib/systemd/system/mysql.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-10-03 09:01:20 UTC; 1h 15min ago
   Main PID: 1190 (mysqld)

+-------------------------+-----------------+--------------------------+----------------+-------------------+----------+
| @@version               | @@datadir       | @@log_error              | @@bind_address | @@max_connections | bp_mb    |
+-------------------------+-----------------+--------------------------+----------------+-------------------+----------+
| 8.0.43-0ubuntu0.24.04.1 | /var/lib/mysql/ | /var/log/mysql/error.log | 127.0.0.1      |               151 | 128.0000 |
+-------------------------+-----------------+--------------------------+----------------+-------------------+----------+
```

→ Loopback only, 151 connections, and a 128 MB buffer pool, which is far too small for a dedicated
database server (50–70% of RAM is the usual starting point).

**Hands-on lab (test VM only)**

**Step 1 — Build.** Set the buffer pool in a drop-in file (MySQL reads every `.cnf` in
`/etc/mysql/mysql.conf.d/`): create `/etc/mysql/mysql.conf.d/zz-lab.cnf` with `[mysqld]` and
`innodb_buffer_pool_size = 1G`, then `sudo systemctl restart mysql`. The `zz-` prefix is deliberate:
MySQL does not document the order in which it reads a directory's files (current versions go
alphabetically), and Ubuntu's own `mysqld.cnf` sets `bind-address = 127.0.0.1`, so a value you
place in a file that sorts before it, such as `60-lab.cnf`, can be silently overridden. After any
restart, confirm the live value (`SELECT @@bind_address;`).

**Step 2 — Break it.** Add a misspelled line `max_connection = 500` to the same file and restart:

```bash
sudo systemctl restart mysql
sudo tail -n 3 /var/log/mysql/error.log
```

```
Job for mysql.service failed because the control process exited with error code.
2026-10-03T10:52:11.402190Z 0 [ERROR] [MY-000067] [Server] unknown variable 'max_connection=500'.
2026-10-03T10:52:11.402415Z 0 [ERROR] [MY-010119] [Server] Aborting
```

→ Unlike PostgreSQL's reload, a MySQL restart with a bad file means the database is **down**.

**Step 3 — Fix it, then validate before every restart.** Correct the name to `max_connections`,
then run `sudo mysqld --validate-config` (MySQL 8.0.16+). No output means the files parse; then
restart. For dynamic variables, skip the restart entirely: `SET PERSIST max_connections = 300;`.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| Service will not start | `sudo tail -n 30 /var/log/mysql/error.log` | [Services & systemd](07-services-systemd.md) |
| `Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)` | `systemctl status mysql` (server down or different socket path) | this topic |
| `ERROR 1698 (28000): Access denied for user 'root'@'localhost'` | use `sudo mysql`; root uses auth_socket | this topic |
| `[Warning] ... InnoDB: page_cleaner ... intended loop takes ...` | I/O too slow for the write rate | [Slow system](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** Knowing where the error log is and how root logs in saves
the first ten minutes of every MySQL incident.

**Next step:** let remote apps in, safely.

### bind-address, users and grants

**Level:** [L1 · Junior] · about 60 minutes

**Concept.** MySQL's "can't connect" gates mirror PostgreSQL's, with two differences. First, the
listen address is `bind-address` (default `127.0.0.1` on Ubuntu) and it is a restart. Second, an
account is a **user at a host**: `'app'@'localhost'`, `'app'@'192.0.2.50'` and `'app'@'192.0.2.%'`
are three different accounts with possibly different passwords and grants. When several match, the
most specific host wins. There is no separate `pg_hba.conf`: the host part of the account plays
that role.

| Error text | Gate | What to check |
|---|---|---|
| `ERROR 2005 (HY000): Unknown MySQL server host 'db1.example.internal' (-2)` | DNS | `getent ahosts` from the client |
| `ERROR 2003 (HY000): Can't connect to MySQL server on '192.0.2.21:3306' (110)` | Network | 110 = timed out: firewall, security group, route |
| `ERROR 2003 (HY000): Can't connect to MySQL server on '192.0.2.21:3306' (111)` | Listen | 111 = refused: `bind-address` is 127.0.0.1 or mysqld is down |
| `ERROR 1130 (HY000): Host '192.0.2.50' is not allowed to connect to this MySQL server` | Account host | No account matches this client host |
| `ERROR 1045 (28000): Access denied for user 'app'@'192.0.2.50' (using password: YES)` | Auth | Wrong password for the account that matched |
| `ERROR 1044 (42000): Access denied for user 'app'@'192.0.2.%' to database 'appdb'` | Grants | Account exists, lacks privileges on that database |
| `ERROR 2061 (HY000): Authentication plugin 'caching_sha2_password' reported error: Authentication requires secure connection.` | Auth plugin | Use TLS, or let the client fetch the server key |

Set `skip_name_resolve = ON`. Without it, MySQL does a reverse DNS lookup for every new
connection, so a slow or broken DNS server makes every connect slow; with it, account hosts must
be IPs or IP patterns.

**See it on a real system**

```bash
sudo ss -ltnp 'sport = :3306'
sudo mysql -e "SELECT user, host, plugin, account_locked FROM mysql.user ORDER BY user, host;"
sudo mysql -e "SHOW GRANTS FOR 'app'@'192.0.2.%';"
```

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      151        127.0.0.1:3306       0.0.0.0:*     users:(("mysqld",pid=1190,fd=23))

+------------------+-----------+-----------------------+----------------+
| user             | host      | plugin                | account_locked |
+------------------+-----------+-----------------------+----------------+
| app              | 192.0.2.% | caching_sha2_password | N              |
| app              | localhost | caching_sha2_password | N              |
| debian-sys-maint | localhost | caching_sha2_password | N              |
| exporter         | 192.0.2.% | caching_sha2_password | N              |
| mysql.infoschema | localhost | caching_sha2_password | Y              |
| mysql.session    | localhost | caching_sha2_password | Y              |
| mysql.sys        | localhost | caching_sha2_password | Y              |
| root             | localhost | auth_socket           | N              |
+------------------+-----------+-----------------------+----------------+

+----------------------------------------------------------------------------+
| Grants for app@192.0.2.%                                                   |
+----------------------------------------------------------------------------+
| GRANT USAGE ON *.* TO `app`@`192.0.2.%`                                    |
| GRANT SELECT, INSERT, UPDATE, DELETE ON `appdb`.* TO `app`@`192.0.2.%`     |
+----------------------------------------------------------------------------+
```

→ The locked `mysql.*` accounts are MySQL's internal system accounts; leave them alone. `app`
exists twice; the remote account has only data privileges on `appdb`, which is right for
an application. Migrations need DDL (`CREATE`, `ALTER`, `INDEX`, `DROP`): give those to a separate
migration account, not to the app's runtime account.

**Hands-on lab (test VM only)**

**Step 1 — Break it from app1.** `mysql -h 192.168.56.21 -u app -p appdb` gives
`ERROR 2003 … (111)`. On db1, set `bind-address = 127.0.0.1,192.168.56.21` in `zz-lab.cnf`
(several addresses need MySQL 8.0.13+; keeping loopback lets local tools and the exporter in
section 9 connect over TCP; also set `mysqlx-bind-address` if you use the X protocol on 33060),
restart, check `SELECT @@bind_address;`, and allow the port in UFW for app1 only, as in section 2.

**Step 2 — The next gate.** Retry: `ERROR 1130 … Host '192.168.56.11' is not allowed`. Create the
account and grant:

```bash
sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS appdb;
CREATE USER 'app'@'192.168.56.%' IDENTIFIED BY 'LabPass-123';
GRANT SELECT, INSERT, UPDATE, DELETE ON appdb.* TO 'app'@'192.168.56.%';
SQL
```

**Step 3 — Break it: the wrong account matches.** Create `'app'@'192.168.56.11'` with a
**different** password. Log in from app1 with the first password: `ERROR 1045`. The more specific
account won. `SELECT USER(), CURRENT_USER();` after a successful login shows which account matched
(`CURRENT_USER`). Drop the extra account: `DROP USER 'app'@'192.168.56.11';`.

**How it breaks:** the full layered walk is the "app can't connect" playbook in section 10.

**Why it matters for troubleshooting.** `ERROR 1130` and `ERROR 1045` look similar to users and mean
completely different things. Reading the number tells you whether to look at hosts or passwords.

**Next step:** see who is connected and what they are doing.

### SHOW PROCESSLIST and lock waits

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** `SHOW FULL PROCESSLIST` is MySQL's `pg_stat_activity`: one row per connection with
`Id` (use it with `KILL`), `User`, `Host`, `db`, `Command` (`Sleep`, `Query`, `Binlog Dump`),
`Time` (seconds in the current state) and `State`. The `sys` schema adds ready-made views:
`sys.innodb_lock_waits` (who blocks whom on rows), `sys.schema_table_lock_waits` (metadata locks),
and `information_schema.innodb_trx` lists open transactions with their age.

- `KILL QUERY ID` stops the running statement, keeps the connection (like `pg_cancel_backend`).
- `KILL ID` closes the connection and rolls back its transaction (like `pg_terminate_backend`).
  Rolling back a huge transaction can take as long as it ran; killing it again does not help.

**See it on a real system**

```bash
sudo mysql -e "SHOW FULL PROCESSLIST;"
sudo mysql -e "SELECT waiting_pid, waiting_query, blocking_pid, blocking_query, wait_age, sql_kill_blocking_connection FROM sys.innodb_lock_waits\G"
```

```
+-----+-----------------+------------------+-------+---------+------+---------------------------------+-------------------------------------------------+
| Id  | User            | Host             | db    | Command | Time | State                           | Info                                            |
+-----+-----------------+------------------+-------+---------+------+---------------------------------+-------------------------------------------------+
|   5 | event_scheduler | localhost        | NULL  | Daemon  | 4510 | Waiting on empty queue          | NULL                                            |
| 912 | app             | 192.0.2.50:51544 | appdb | Sleep   |  301 |                                 | NULL                                            |
| 915 | app             | 192.0.2.50:51560 | appdb | Query   |   38 | updating                        | UPDATE orders SET status='paid' WHERE id=991    |
| 918 | deploy          | 192.0.2.70:40112 | appdb | Query   |   35 | Waiting for table metadata lock | ALTER TABLE orders ADD COLUMN note TEXT         |
| 920 | app             | 192.0.2.51:39880 | appdb | Query   |   34 | Waiting for table metadata lock | SELECT * FROM orders WHERE id=7                 |
| 931 | root            | localhost        | NULL  | Query   |    0 | init                            | SHOW FULL PROCESSLIST                           |
+-----+-----------------+------------------+-------+---------+------+---------------------------------+-------------------------------------------------+

*************************** 1. row ***************************
                 waiting_pid: 915
               waiting_query: UPDATE orders SET status='paid' WHERE id=991
                blocking_pid: 912
              blocking_query: NULL
                    wait_age: 00:00:38
sql_kill_blocking_connection: KILL 912
```

→ Connection 912 is `Sleep` with an open transaction (it holds the row lock but runs nothing, so
`blocking_query` is NULL): MySQL's idle-in-transaction. The ALTER (918) waits for a metadata lock
and the SELECT (920) queues behind it: the same lock-queue outage as in section 1.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Create a small table: `CREATE TABLE appdb.orders (id INT PRIMARY KEY, status
VARCHAR(20)); INSERT INTO appdb.orders VALUES (991,'new'),(7,'new');`

**Step 2 — Break it.** Session A: `START TRANSACTION; UPDATE appdb.orders SET status='paid' WHERE
id=991;` Session B: same row, different value (waits). After 50 seconds B gets
`ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`
(`innodb_lock_wait_timeout`). Repeat, and this time find the blocker with `sys.innodb_lock_waits`
before the timeout.

**Step 3 — Fix it.** `KILL 912;` (the blocker's Id from the view), and B proceeds. Note that the
fix for the *code* is to commit promptly; the fix for the *server* is a sensible `wait_timeout` so
abandoned sessions do not live for the default eight hours.

**How it breaks:** see the locks playbook in section 10.

**Why it matters for troubleshooting.** `Sleep` connections with open transactions are invisible in
a naive processlist scan. `sys.innodb_lock_waits` and `information_schema.innodb_trx` are where they
show up.

**Next step:** queries that do not wait but are slow: the slow query log.

### Slow query log and EXPLAIN

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** MySQL writes statements slower than `long_query_time` (seconds, may be fractional) to
the slow log when `slow_query_log = ON`. Each entry has `Query_time`, `Lock_time`, `Rows_sent` and
**`Rows_examined`**: a big gap between examined and sent rows is the signature of a missing index.
`mysqldumpslow` (ships with the server) and `pt-query-digest` (Percona Toolkit) aggregate the log
by query shape, like `pg_stat_statements`. `EXPLAIN FORMAT=TREE` and `EXPLAIN ANALYZE` read like
PostgreSQL's plans.

**See it on a real system**

```bash
# Ubuntu ships slow_query_log_file commented out; the default is HOSTNAME-slow.log in the data directory
sudo mysql -e "SET PERSIST slow_query_log_file = '/var/log/mysql/mysql-slow.log'; SET PERSIST slow_query_log = ON; SET PERSIST long_query_time = 0.5;"
sudo tail -n 6 /var/log/mysql/mysql-slow.log
sudo pt-query-digest --limit 3 /var/log/mysql/mysql-slow.log | sed -n '/Profile/,/^$/p'
```

```
# Time: 2026-10-03T10:21:44.512331Z
# User@Host: app[app] @  [192.0.2.50]  Id:   912
# Query_time: 3.481220  Lock_time: 0.000004 Rows_sent: 12  Rows_examined: 1048576
use appdb;
SET timestamp=1791022904;
SELECT * FROM orders WHERE customer_id = 4242 AND status = 'paid';

# Profile
# Rank Query ID                            Response time  Calls R/Call V/M   Item
# ==== =================================== ============== ===== ====== ===== ===========
#    1 0x5A3F2B18C0FFEE0123456789ABCDEF01  1840.1120 71.3%  6120 0.3007  0.02 SELECT orders
#    2 0x77D1E2A3B4C5D6E7F8091A2B3C4D5E6F   374.5911 14.5%   612 0.6121  0.01 SELECT orders
#    3 0x0C9B8A7F6E5D4C3B2A19080706050403   126.3440  4.9%    44 2.8715  0.05 SELECT orders
```

→ 1,048,576 rows examined to send 12: a full table scan. The digest ranks by total response time,
so rank 1 is where an index pays off most.

**Hands-on lab (test VM only):** load 1 million rows into `appdb.orders` (a `customer_id` column
without an index), run the query above a few times, find it in the slow log, run
`EXPLAIN ANALYZE SELECT …` (look for `Table scan on orders`), add the index online with
`ALTER TABLE orders ADD INDEX idx_customer (customer_id), ALGORITHM=INPLACE, LOCK=NONE;` and confirm
the plan changes to `Index lookup on orders using idx_customer`. Then **break it** by setting
`log_queries_not_using_indexes = ON` on a busy lab and watch the log flood; turn it off again.

**How it breaks:** see "slow queries after deploy" in section 10.

**Why it matters for troubleshooting.** `Rows_examined` is the single most useful number in MySQL
performance work, and it is in every slow log entry.

**Next step:** InnoDB's own status report, for when the slow log is not enough.

### InnoDB status and buffer pool

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** `SHOW ENGINE INNODB STATUS\G` prints a snapshot report of the storage engine. You do
not need all of it; four parts answer most questions:

| Section | Look for | Meaning |
|---|---|---|
| `LATEST DETECTED DEADLOCK` | the two transactions and statements | Send to developers; set `innodb_print_all_deadlocks = ON` to log every one |
| `TRANSACTIONS` | `History list length` | Undo not yet purged; grows behind long transactions (MySQL's bloat) |
| `BUFFER POOL AND MEMORY` | `Buffer pool hit rate`, `Free buffers` | Below about 990/1000 under steady load means reads go to disk |
| `FILE I/O` | `Pending normal aio reads/writes` | Non-zero for long periods means the disk cannot keep up |

The **buffer pool** is InnoDB's cache for data and indexes. Size it at 50–70% of RAM on a dedicated
server; it is resizable online in 8.0 (`SET PERSIST innodb_buffer_pool_size = …`).

**See it on a real system**

```bash
sudo mysql -e "SHOW ENGINE INNODB STATUS\G" | grep -E 'History list length|Buffer pool hit rate|Pending normal aio|^LATEST DETECTED DEADLOCK' | head -n 12
sudo mysql -e "SHOW GLOBAL STATUS WHERE Variable_name IN ('Innodb_buffer_pool_read_requests','Innodb_buffer_pool_reads','Innodb_row_lock_waits');"
sudo mysql -e "SELECT name, count FROM information_schema.INNODB_METRICS WHERE name = 'lock_deadlocks';"
```

```
History list length 1843077
Buffer pool hit rate 951 / 1000, young-making rate 12 / 1000 not 0 / 1000
Pending normal aio reads: [0, 0, 0, 0] , aio writes: [0, 0, 0, 0] ,

+----------------------------------+-------------+
| Variable_name                    | Value       |
+----------------------------------+-------------+
| Innodb_buffer_pool_read_requests | 88412901772 |
| Innodb_buffer_pool_reads         |   912044511 |
| Innodb_row_lock_waits            |       20419 |
+----------------------------------+-------------+
+----------------+-------+
| name           | count |
+----------------+-------+
| lock_deadlocks |    37 |
+----------------+-------+
```

MySQL has no `Innodb_deadlocks` status variable (MariaDB and Percona Server do); the deadlock
counter lives in `INNODB_METRICS` as `lock_deadlocks`.

→ A history list of 1.8 million means a long-running transaction is preventing purge; find it with
`SELECT trx_mysql_thread_id, trx_started FROM information_schema.innodb_trx ORDER BY trx_started
LIMIT 3;`. A 95% hit rate (about 1% of logical reads going to disk overall) suggests the buffer pool
is too small for the working set.

**Hands-on lab (test VM only):** create a deadlock on purpose with two sessions updating rows 991
and 7 in opposite order (A updates 991, B updates 7, A updates 7, B updates 991). One gets
`ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`. Read the
`LATEST DETECTED DEADLOCK` section and identify both statements. **Fix:** the application must
update rows in a consistent order and retry on 1213. Then enable `innodb_print_all_deadlocks` so the
next one lands in the error log.

**Why it matters for troubleshooting.** InnoDB status distinguishes "the disk is slow", "the cache
is too small", "something holds old snapshots" and "the app deadlocks", four problems that all
look like "MySQL is slow".

**Next step:** the connection ceiling.

### max_connections and timeouts

**Level:** [L2 · Mid] · about 30 minutes

**Concept.** `max_connections` defaults to 151, and MySQL keeps **one extra** connection for an
account with `CONNECTION_ADMIN` (or legacy `SUPER`) so an administrator can get in when the server
is full. MySQL 8.0.14+ can also listen on a dedicated **admin interface** (`admin_address`,
`admin_port` 33062) that is never counted against `max_connections`; configure it before you need
it. Unlike PostgreSQL, `max_connections` is dynamic (`SET PERSIST max_connections = 300;` takes
effect immediately), but each thread can allocate per-session buffers, so check memory first.

Idle connections linger for `wait_timeout` seconds (default 28800, eight hours). Apps with pools
that never close connections, plus a large `wait_timeout`, plus a scale-out, is how MySQL fills up.

| Status variable | Meaning |
|---|---|
| `Threads_connected` | Connections now |
| `Max_used_connections`, `Max_used_connections_time` | Peak since start, and when |
| `Connection_errors_max_connections` | Connections refused because the server was full |
| `Aborted_clients` | Connections dropped without a proper close (timeouts, killed apps) |
| `Aborted_connects` | Failed logins (wrong password, wrong host) |

**See it on a real system**

```bash
sudo mysql -e "SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Max_used_connections','Max_used_connections_time','Connection_errors_max_connections','Aborted_connects');"
sudo mysql -e "SELECT user, substring_index(host, ':', 1) AS client, command, count(*) FROM information_schema.processlist GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 5;"
```

```
+-----------------------------------+---------------------+
| Variable_name                     | Value               |
+-----------------------------------+---------------------+
| Aborted_connects                  | 14                  |
| Connection_errors_max_connections | 2207                |
| Max_used_connections              | 152                 |
| Max_used_connections_time         | 2026-10-03 09:58:02 |
| Threads_connected                 | 149                 |
+-----------------------------------+---------------------+

+------+------------+---------+----------+
| user | client     | command | count(*) |
+------+------------+---------+----------+
| app  | 192.0.2.52 | Sleep   |      118 |
| app  | 192.0.2.50 | Sleep   |       19 |
| app  | 192.0.2.50 | Query   |        8 |
+------+------------+---------+----------+
```

→ The server hit 152 (151 plus the admin slot) at 09:58 and has refused 2,207 connections since.
118 sleeping connections from one host (192.0.2.52) is a leaking client, not a capacity problem.

**Hands-on lab (test VM only):** `SET GLOBAL max_connections = 5;`, open five `mysql -u app`
sessions from app1; the sixth fails with `ERROR 1040 (HY000): Too many connections`. `sudo mysql`
on db1 still works through the extra admin slot. Find the sessions, `KILL` two of them, and restore
the setting with `SET GLOBAL max_connections = 151;`.

**How it breaks:** see "Too many connections" in section 10. Poolers for MySQL are ProxySQL (on VMs)
and RDS Proxy (on AWS).

**Why it matters for troubleshooting.** `Max_used_connections_time` tells you *when* the ceiling was
hit, which you then match to a deploy, a cron job or a scale-out.

**Next step:** with operations covered, the most important skill of all: backups that restore.

---

## 4. Backups that actually restore

> 📚 **Study path:** 1) Note: this section first; KodeKloud has no database backup course in the verified map, so the handbook leads here (if you want video, look for a PostgreSQL or MySQL administration course by name and check the current catalog) · 2) Read: [GitLab's 2017 database outage postmortem](https://about.gitlab.com/2017/02/10/postmortem-of-database-outage-of-january-31/), then chapter 26 (Data Integrity) from the [SRE book table of contents](https://sre.google/sre-book/table-of-contents/) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance: Backup and Restore Methods, the same snapshot-then-restore discipline applied to etcd, and it counts as CKA study ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Cluster-Maintenance/Backup-and-Restore-Methods)) · 4) Practice: every lab below ends with a restore on db1/db2, then the timed backup task in section 12.

A backup is only half of a restore, and nobody has ever been praised for the half. In January 2017
GitLab.com lost about six hours of production data: during a replication problem an engineer
removed the data directory on the wrong server, and the team then found that the nightly
`pg_dump` had been failing silently for a long time (a client/server version mismatch, with the
error emails rejected by the mail system). Recovery came from a snapshot that someone had taken six
hours earlier for a different purpose. Read their postmortem from the study path: every control in
this section exists because of a story like that one.

The rules this section teaches:

- **Two numbers drive every design: RPO and RTO.** The business sets them; you prove them.
- **Logical and physical backups solve different problems.** Most teams need both.
- **Replication is not a backup.** A `DROP TABLE` reaches the replica in milliseconds.
- **A backup that has never been restored does not exist.** Restore tests are automated and alert.

### RPO, RTO and the 3-2-1 rule

**Level:** [L1 · Junior] → [L4 · Lead/SRE] · about 45 minutes

**Concept.** Two numbers decide everything else:

- **RPO (recovery point objective):** how much data loss, measured in time, is acceptable. "RPO
  15 minutes" means that after a disaster you may lose at most the last 15 minutes of writes.
- **RTO (recovery time objective):** how long the service may stay down while you recover.

```
  last restorable point                    incident                     service back
          │◄──────────── RPO: data you lose ──────────►│◄──── RTO: time to recover ────►│
  ────────●────────────────────────────────────────────●────────────────────────────────●───▶ time
        02:00 (nightly dump)                        10:14                             11:40
```

With only a nightly dump, the RPO is up to 24 hours and the RTO is however long a full restore
takes, which you only know if you have measured it. Each backup type moves those numbers:

| Type | Example tools | Restore granularity | Typical RPO | Typical RTO |
|---|---|---|---|---|
| Logical | `pg_dump`, `mysqldump`, `mariadb-dump` | one table, schema or database | time since the last dump, often 24 h | slow: rows are re-inserted and indexes rebuilt |
| Physical | `pg_basebackup`, pgBackRest, XtraBackup, Mariabackup | whole server (cluster) | time since the last backup | faster: copy files, then crash recovery |
| Physical + log archive (PITR) | base backup + archived WAL or binlogs | whole server, to any second | seconds to a minute | copy files plus replay time |
| Volume snapshot | LVM, VM, EBS snapshots | whole volume | snapshot interval | fast, but only crash-consistent |
| Replica | streaming or binlog replication | none | seconds, for hardware failure only | minutes (failover) |

The last row is the trap: a replica protects you against a dead server, never against a mistake,
because the mistake is replicated as faithfully as everything else.

**The 3-2-1 rule** (with its modern additions, sometimes written 3-2-1-1-0):

- **3** copies of the data: production plus two backups.
- **2** different storage systems, so one failure mode cannot take both.
- **1** copy offsite: another building, another cloud account, another region.
- **1** copy immutable or offline: S3 Object Lock, tape, or a backup server that *pulls* and that
  the database host has no credentials to delete. Ransomware and attackers delete backups first.
- **0** errors after a verified restore.

**Key terms**

| Term | Meaning |
|---|---|
| Retention | How long backups are kept; must be longer than the time it takes to *notice* a problem |
| Full / incremental / differential | Everything / changes since the last backup of any kind / changes since the last full |
| Crash-consistent | Like pulling the power cord: the database recovers, but only if data and WAL were captured at the same instant |
| Application-consistent | The database itself produced a consistent copy (`pg_dump`, `pg_basebackup`, XtraBackup) |
| PITR | Point-in-time recovery: base backup plus replayed logs, stopped at a chosen moment |
| Restore test | An automated job that restores the newest backup somewhere else and checks it |

**See it on a real system: audit what exists today**

```bash
systemctl list-timers --all | grep -iE 'backup|dump|pgbackrest|xtrabackup'
sudo crontab -l -u postgres 2>/dev/null | grep -v '^#'
sudo ls -lht /var/backups/db/ | head -n 5     # the directory is 0750 postgres
sudo -u postgres psql -Atc "SELECT archived_count, last_archived_wal, last_archived_time, failed_count FROM pg_stat_archiver;"
df -h /var/backups/db /var/lib/postgresql
```

```
Sun 2026-10-04 02:00:00 UTC 13h left  Sat 2026-10-03 02:00:03 UTC 10h ago  db-backup.timer  db-backup.service

total 6.2G
-rw------- 1 postgres postgres 1.6G Oct  3 02:07 appdb-2026-10-03_0200.dump
-rw------- 1 postgres postgres 1.6G Oct  2 02:07 appdb-2026-10-02_0200.dump
-rw------- 1 postgres postgres 1.5G Oct  1 02:06 appdb-2026-10-01_0200.dump
-rw------- 1 postgres postgres 1.5G Sep 30 02:06 appdb-2026-09-30_0200.dump

0|||0

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   71G   23G  76% /
/dev/sda2        98G   71G   23G  76% /
```

→ Read it like an auditor. There is a nightly logical dump (good) kept for four days. WAL archiving
has never run (`archived_count` is 0), so the RPO is up to 24 hours. Both paths are on the same
filesystem, `/dev/sda2`: one dead disk, one `rm -rf` or one ransomware run takes the database and
its backups together. There is no offsite copy and no evidence that anyone has ever restored one
of these files. This is a very typical first audit, and the rest of this section fixes each
finding.

**Getting copies off the host.** Two patterns, best used together:

```bash
# On the backup server (pull model): the database host has no way to delete these copies
rsync -a backup@db1.example.internal:/var/backups/db/ /srv/backups/db1/

# Offsite: a versioned bucket with Object Lock in another region (GOVERNANCE mode for the lab;
# COMPLIANCE mode cannot be shortened by anyone, including the account root user)
aws s3api create-bucket --bucket example-db-backups-123456789012 --region eu-central-1 \
  --create-bucket-configuration LocationConstraint=eu-central-1 --object-lock-enabled-for-bucket
aws s3api put-object-lock-configuration --bucket example-db-backups-123456789012 \
  --object-lock-configuration '{"ObjectLockEnabled":"Enabled","Rule":{"DefaultRetention":{"Mode":"GOVERNANCE","Days":30}}}'
aws s3 sync /srv/backups/db1/ s3://example-db-backups-123456789012/db1/
```

Note the deliberate absence of `--delete` on the `rsync`: a deletion (or encryption) on the
database host must never propagate to the backup server. Retention on the backup server is a
separate job that only the backup server runs. Encrypt dumps before they leave your network (for
example with `gpg` or `age` and a public key), keep the private key somewhere that survives the
loss of the whole site, and make decryption part of the restore test.

**Hands-on lab (test VM only)**

**Step 1 — Build: write the policy.** One page for the lab app: RPO, RTO, retention (for example 7
daily, 4 weekly, 3 monthly), where each copy lives, who is alerted when a backup or restore test
fails, and how often restores are tested.

**Step 2 — Break it (tabletop).** For each scenario, write which copy you would restore from, how
much data you would lose and how long it would take: the database disk dies; someone runs
`DROP TABLE orders` at 10:14; ransomware encrypts db1 including `/var/backups`; a bug has been
corrupting 2% of rows for three weeks and you notice today; the whole server room is lost.
Every "we can't" is a gap.

**Step 3 — Fix it.** Map each gap to a topic: offsite and immutable copies (this topic), PITR
(next topics), longer retention, restore tests (last topic). Then run the audit commands above on
db1 and fill in the real numbers.

**How it breaks**

| Failure | Symptom | First check | Where to go |
|---|---|---|---|
| Backup job fails silently | newest file is days old; cron mail goes nowhere | `sudo ls -lht /var/backups/db`, `systemctl status db-backup.service` | restore tests and alerts, section 9 |
| Backups on the same disk or host | database and backups lost together | `df -h` on both paths | 3-2-1 above |
| Retention shorter than detection | corruption found after three weeks, oldest backup is seven days old | the written policy | this topic |
| Encryption key only on the server | backups unreadable after the host is lost | where the private key lives | keep a key copy offline, test decryption |
| Replica treated as the backup | `DROP TABLE` gone on the replica too | — | PITR topic below |

**Why it matters for troubleshooting.** In a data-loss incident the first question is "what is our
newest restorable copy and how long does it take to restore?" If you can answer in one sentence
with measured numbers, the incident is an inconvenience. If you cannot, it becomes the incident
everyone remembers.

**Next step:** the backup every Junior must master: logical dumps, restored for real.

### Logical backups: pg_dump and mysqldump

**Level:** [L1 · Junior] · about 60 minutes

**Concept.** A logical backup is the database exported as SQL or as an archive of objects and rows.
It is portable (another version, another server, your laptop) and allows restoring a single table,
but restoring re-inserts every row and rebuilds every index, so it is slow for large databases.

PostgreSQL:

- `pg_dump` backs up **one database** at one consistent instant. It reads everything in a single
  repeatable-read snapshot, so the application keeps working during the dump.
- It does **not** include roles, passwords or tablespaces. Those are cluster-wide "globals"; dump
  them with `pg_dumpall --globals-only`, or a restore on a new server fails on missing roles.
- Formats: plain SQL (`-Fp`, restored with `psql`), **custom (`-Fc`, compressed, selective restore
  with `pg_restore`; the usual choice)**, directory (`-Fd`, allows a parallel dump with `-j`).
- `pg_dump` holds an ACCESS SHARE lock on every table it dumps until it finishes. That conflicts
  only with ACCESS EXCLUSIVE (most `ALTER TABLE`, `DROP`, `TRUNCATE`, `VACUUM FULL`), so a
  migration that starts during the nightly dump waits for the whole dump, and everything queues
  behind the migration: the lock-queue outage from section 1. Keep dumps and migrations apart.
- Use a `pg_dump` at least as new as the server, and restore with a `pg_restore` at least as new
  as the `pg_dump` that wrote the file: an older client may reject a newer archive format.

MySQL and MariaDB:

- `mysqldump --single-transaction` dumps InnoDB tables from one consistent snapshot without
  blocking writes (MyISAM tables get no such guarantee). Add `--routines --events` (triggers are
  included by default).
- `--source-data=2` (MySQL 8.0.26+; older versions call it `--master-data`) records the binlog
  position as a comment in the dump: the starting point for binlog PITR and for seeding a replica.
- DDL on a table during a `--single-transaction` dump can abort it with
  `Table definition has changed, please retry transaction`.
- Users and grants live in the `mysql` system schema. Export them separately with `pt-show-grants`
  (Percona Toolkit) or `SHOW CREATE USER` plus `SHOW GRANTS`, not by dumping `mysql.*`.
- For large databases, MySQL Shell's parallel dump utilities are much faster; `mysqlpump` was
  deprecated in 8.0.34 and removed in 8.4. MariaDB ships the same tool as `mariadb-dump`.

**See it on a real system**

```bash
sudo install -d -o postgres -g postgres -m 0750 /var/backups/db
sudo -u postgres pg_dumpall --globals-only -f /var/backups/db/globals-$(date +%F).sql
sudo -u postgres pg_dump -Fc -f /var/backups/db/appdb-$(date +%F_%H%M).dump appdb
sudo -u postgres pg_restore -l /var/backups/db/appdb-2026-10-03_1205.dump | head -n 20
```

```
;
; Archive created at 2026-10-03 12:05:09 UTC
;     dbname: appdb
;     TOC Entries: 37
;     Compression: gzip
;     Dump Version: 1.15-0
;     Format: CUSTOM
;     Integer: 4 bytes
;     Offset: 8 bytes
;     Dumped from database version: 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
;     Dumped by pg_dump version: 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
;
;
; Selected TOC Entries:
;
216; 1259 16412 TABLE public orders app
215; 1259 16411 SEQUENCE public orders_id_seq app
3402; 0 16412 TABLE DATA public orders app
3260; 2606 16418 CONSTRAINT public orders orders_pkey app
```

→ The TOC (table of contents) lists every object in restore order. The `orders` table, its
sequence, its rows and its primary key are separate entries, which is what makes single-table
restores possible (playbook in section 10). The header tells you which versions made the file.

Now the part that matters, the restore. Always restore into a **new** database:

```bash
sudo -u postgres createdb -O app appdb_restore
time sudo -u postgres pg_restore -d appdb_restore -j 4 --no-owner --role=app /var/backups/db/appdb-2026-10-03_1205.dump
sudo -u postgres psql -d appdb_restore -Atc "SELECT count(*), max(created_at) FROM orders;"
```

```
real    0m41.322s
user    0m3.120s
sys     0m0.611s
1000000|2026-10-03 12:04:58.113+00
```

→ 41 seconds for this lab database: that is your **measured** RTO for a logical restore, and it
grows roughly with data size plus index count. `max(created_at)` shows how fresh the copy is, so
it is your measured RPO. Write both into the policy from the previous topic.

MySQL, the same pair of habits:

```bash
sudo install -d -m 0750 /var/backups/mysql
sudo bash -c 'set -o pipefail; mysqldump --single-transaction --routines --events --source-data=2 appdb | gzip > /var/backups/mysql/appdb-$(date +%F_%H%M).sql.gz'
sudo bash -c 'pt-show-grants > /var/backups/mysql/grants-$(date +%F).sql'
sudo zcat /var/backups/mysql/appdb-2026-10-03_1210.sql.gz | grep -m1 'CHANGE REPLICATION SOURCE'
```

```
-- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='binlog.000003', SOURCE_LOG_POS=48211907;
```

→ The binlog coordinates of the snapshot are inside the dump. Two details in those commands are
deliberate. The redirections run inside `sudo bash -c`, because with a plain `sudo mysqldump ... >
FILE` the redirection is done by your own unprivileged shell and fails on a root-owned directory.
And `set -o pipefail` matters: without it, the exit status of `mysqldump ... | gzip` is gzip's, so
a failed dump still "succeeds" and leaves a tiny, useless file. Restore into a new database the
same way: `sudo mysql -e "CREATE DATABASE appdb_restore"` then
`sudo zcat /var/backups/mysql/appdb-2026-10-03_1210.sql.gz | sudo mysql appdb_restore`.

A nightly job that does this properly, with retention and a metric for monitoring:

```bash
#!/usr/bin/env bash
# /usr/local/sbin/db-backup.sh: nightly logical backup of appdb, started by db-backup.timer
set -euo pipefail
umask 077
DIR=/var/backups/db
STAMP=$(date +%F_%H%M)
METRICS=/var/lib/prometheus/node-exporter/db_backup.prom   # node_exporter textfile directory (Ubuntu package)

runuser -u postgres -- pg_dumpall --globals-only > "$DIR/globals-$STAMP.sql"
runuser -u postgres -- pg_dump -Fc -f "$DIR/appdb-$STAMP.dump" appdb
runuser -u postgres -- pg_restore -l "$DIR/appdb-$STAMP.dump" > /dev/null   # the archive is readable
find "$DIR" -name 'appdb-*.dump' -mtime +14 -delete
find "$DIR" -name 'globals-*.sql' -mtime +14 -delete

SIZE=$(stat -c %s "$DIR/appdb-$STAMP.dump")
cat > "$METRICS.tmp" <<EOF
db_backup_last_success_timestamp_seconds{db="appdb"} $(date +%s)
db_backup_size_bytes{db="appdb"} $SIZE
EOF
chmod 0644 "$METRICS.tmp"   # umask 077 would hide it from node_exporter, which runs as "prometheus"
mv "$METRICS.tmp" "$METRICS"
```

```ini
# /etc/systemd/system/db-backup.service
[Unit]
Description=Nightly logical backup of appdb

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/db-backup.sh
```

```ini
# /etc/systemd/system/db-backup.timer
[Unit]
Description=Run db-backup nightly

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

→ The script writes its success metric **last**, so any failure leaves the old timestamp in place
and the "backup too old" alert in section 9 fires. That is far more reliable than an email on
failure, because a job that never starts sends no email at all.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Install the script and timer above on db1 (`sudo systemctl daemon-reload`,
`sudo systemctl enable --now db-backup.timer`), run it once with
`sudo systemctl start db-backup.service`, and copy the newest dump and globals file to db2.

**Step 2 — Break it: restore on a fresh server.** On db2 (which has no `app` role yet), restore
without `--no-owner` and without the globals:

```bash
sudo -u postgres createdb appdb
sudo -u postgres pg_restore -d appdb /tmp/appdb-2026-10-03_0200.dump
```

```
pg_restore: error: could not execute query: ERROR:  role "app" does not exist
Command was: ALTER TABLE public.orders OWNER TO app;
pg_restore: warning: errors ignored on restore: 9
```

→ The data arrived, but every ownership statement failed. In a real restore, the app would then
fail with `permission denied` because its role does not exist either.

**Step 3 — Fix it.** Restore the globals first, then restore into a **new** database, check it,
and only then retire the broken copy:

```bash
sudo -u postgres psql -f /tmp/globals-2026-10-03_0200.sql
sudo -u postgres createdb -O app appdb_ok
sudo -u postgres pg_restore -d appdb_ok -j 4 /tmp/appdb-2026-10-03_0200.dump
sudo -u postgres psql -d appdb_ok -Atc "SELECT count(*) FROM orders;"
# Lab only, after the count matches db1: replace the broken copy (dropdb cannot be undone)
sudo -u postgres dropdb appdb
sudo -u postgres psql -c "ALTER DATABASE appdb_ok RENAME TO appdb;"
```

The order is the lesson: build and verify the good copy before you destroy anything. The globals
file contains `CREATE ROLE` statements with password hashes, so it is as sensitive as the data.

**Step 4 — MySQL.** Restore the dump into `appdb_restore` on db1, load the grants file on db2,
then deliberately run the dump command **without** `set -o pipefail` and with a wrong database
name, and look at the size of the "successful" file.

**How it breaks**

| Symptom / error text | First command | Fix |
|---|---|---|
| `pg_dump: error: aborting because of server version mismatch` | `pg_dump --version` and `SELECT version();` | install the newer client (PGDG packages); this is the GitLab 2017 failure |
| `pg_restore: error: unsupported version (1.15) in file header` | `pg_restore --version` | restore with a client at least as new as the `pg_dump` that wrote the file |
| `ERROR:  role "app" does not exist` during restore | `grep -c 'CREATE ROLE' globals-*.sql` | restore the globals first, or `--no-owner --role=app` |
| `mysqldump: Error 1412: Table definition has changed, please retry transaction` | was a migration running? | schedule dumps and migrations apart |
| Dump file of a few KB and the job "succeeded" | look at the last lines of the file: a complete mysqldump ends with `-- Dump completed` | `set -o pipefail` and a size check |
| Migrations hang every night at 02:00 | `pg_stat_activity` shows `pg_dump` holding locks | move the dump or the migration window |

**Why it matters for troubleshooting.** Logical dumps are the tool for "restore one table" and "move
to another version", and they catch logical problems because every row is read. They are the
wrong tool for "restore 500 GB by lunchtime" or "get back to 10:14". Knowing which question each
backup type answers is the whole skill.

**Next step:** physical backups and WAL archiving, which shrink the RPO from a day to a minute.

### PostgreSQL PITR with WAL archiving

**Level:** [L3 · Senior] · about 2 hours

**Concept.** A **base backup** is a copy of the whole data directory taken while the server runs.
On its own it is crash-consistent and only useful together with the WAL written while it was being
taken. Add **continuous WAL archiving** (every finished 16 MB segment copied somewhere safe) and you
can rebuild the database as it was at **any moment** after the base backup: restore the base
backup, then let PostgreSQL replay archived WAL up to a target time and stop.

```
 Sunday 01:00
 base backup ──▶ WAL WAL WAL WAL WAL WAL WAL WAL WAL WAL ──▶ DELETE by mistake at 12:41:07
     │                                                   ▲
     └─ 1. copy base backup ─ 2. replay archived WAL ────┘  3. stop just before 12:41:07, then promote
```

Three settings turn archiving on (`archive_mode` needs a restart, the others a reload):

| Setting | Lab value | Why |
|---|---|---|
| `archive_mode` | `on` | Start archiving finished WAL segments |
| `archive_command` | `'test ! -f /srv/walarchive/%f && cp %p /srv/walarchive/%f'` | `%p` is the segment's path, `%f` its file name; `test ! -f` refuses to overwrite an existing file |
| `archive_timeout` | `60` | Force a segment switch at least every 60 s, so a quiet database still archives; this caps your RPO |

The `cp` command is the documentation's teaching example. In production use a tool built for the
job, because it handles compression, encryption, parallelism, retention, remote repositories (an
SSH backup server or S3) and verification: **pgBackRest** and **Barman** are the common choices on
VMs, WAL-G is popular in containers. Whatever you choose, the archive must live on **another
machine**. PostgreSQL 17 adds native incremental backups (`pg_basebackup --incremental` plus
`pg_combinebackup`, with `summarize_wal = on`).

**Key terms**

| Term | Meaning |
|---|---|
| Base backup | Online copy of the data directory, with a `backup_manifest` (PostgreSQL 13+) |
| `restore_command` | How recovery fetches archived segments, the reverse of `archive_command` |
| `recovery.signal` | Empty file in the data directory: "start in targeted recovery mode" (PostgreSQL 12+) |
| `recovery_target_time` | Stop replay at this moment; always write it with a time zone offset |
| `recovery_target_action` | `pause` (inspect first, the default), `promote` or `shutdown` |
| Timeline | After a PITR promotion the server starts timeline 2, so its WAL never collides with the old history |

**See it on a real system**

```bash
sudo -u postgres psql -x -c "SELECT * FROM pg_stat_archiver;"
sudo ls /srv/walarchive | tail -n 3
```

```
-[ RECORD 1 ]------+------------------------------
archived_count     | 1843
last_archived_wal  | 000000010000000000000061
last_archived_time | 2026-10-03 12:31:02.118+00
failed_count       | 0
last_failed_wal    |
last_failed_time   |
stats_reset        | 2026-09-01 08:00:11.502+00

00000001000000000000005F
000000010000000000000060
000000010000000000000061
```

→ `failed_count` 0 and a `last_archived_time` within the last minute or two: archiving works. When
`failed_count` grows, every unarchived segment stays in `pg_wal` (PostgreSQL never recycles a
segment it has not archived), which is one road to the "disk full from WAL" playbook in section 10.

**Hands-on lab (test VM only, snapshot db1 first)**

**Step 1 — Build: archiving plus a base backup.**

```bash
sudo install -d -o postgres -g postgres -m 0700 /srv/walarchive /srv/basebackup
sudo tee /etc/postgresql/16/main/conf.d/50-archive.conf >/dev/null <<'EOF'
archive_mode = on
archive_command = 'test ! -f /srv/walarchive/%f && cp %p /srv/walarchive/%f'
archive_timeout = 60
EOF
sudo systemctl restart postgresql@16-main
sudo -u postgres pg_basebackup -D /srv/basebackup/base1 -Fp -Xs -P -c fast -v
sudo -u postgres /usr/lib/postgresql/16/bin/pg_verifybackup /srv/basebackup/base1
```

```
pg_basebackup: initiating base backup, waiting for checkpoint to complete
pg_basebackup: checkpoint completed
pg_basebackup: write-ahead log start point: 0/5C000028 on timeline 1
pg_basebackup: starting background WAL receiver
pg_basebackup: created temporary replication slot "pg_basebackup_41234"
1931211/1931211 kB (100%), 1/1 tablespace
pg_basebackup: write-ahead log end point: 0/5C000138
pg_basebackup: waiting for background process to finish streaming ...
pg_basebackup: syncing data to disk ...
pg_basebackup: renaming backup_manifest.tmp to backup_manifest
pg_basebackup: base backup completed
backup successfully verified
```

→ The base backup connected through Ubuntu's default `local replication all peer` rule in
`pg_hba.conf`. `pg_verifybackup` (not on the PATH on Ubuntu, hence the full path) checks every
file against the manifest, so you know the copy is complete before you ever need it.

**Step 2 — Break it.** Generate some traffic, write down the time, then make the mistake:

```bash
pgbench -h 127.0.0.1 -U app -c 4 -T 60 appdb > /dev/null
sudo -u postgres psql -d appdb -Atc "SELECT now();"
sudo -u postgres psql -d appdb -c "DELETE FROM orders WHERE status = 'paid';"
sudo -u postgres psql -Atc "SELECT pg_walfile_name(pg_switch_wal());"   # lab only: archive the current segment now
```

```
2026-10-03 12:41:07.522+00
DELETE 333412
000000010000000000000063
```

→ The timestamp you wrote down **before** the mistake is the most valuable fact in the incident.
In a real incident you get it from the application log, the PostgreSQL log
(`log_min_duration_statement` or `log_statement = 'ddl'` catch many mistakes) or the person who
ran it.

**Step 3 — Fix it: recover a copy next to production.** Never practise PITR on top of the only
copy. Ubuntu's cluster tools let you build a second cluster on port 5433 and restore into it:

```bash
sudo pg_createcluster 16 pitr --port 5433
sudo mv /var/lib/postgresql/16/pitr /var/lib/postgresql/16/pitr.empty   # the new, EMPTY cluster's data
sudo -u postgres cp -a /srv/basebackup/base1 /var/lib/postgresql/16/pitr
sudo tee /etc/postgresql/16/pitr/conf.d/90-pitr.conf >/dev/null <<'EOF'
restore_command = 'cp /srv/walarchive/%f %p'
recovery_target_time = '2026-10-03 12:41:07+00'
recovery_target_action = 'pause'
archive_mode = off      # the restored copy must never write into the production archive
EOF
sudo -u postgres touch /var/lib/postgresql/16/pitr/recovery.signal
sudo pg_ctlcluster 16 pitr start
sudo tail -n 9 /var/log/postgresql/postgresql-16-pitr.log
```

```
2026-10-03 12:52:10.114 UTC [8812] LOG:  starting point-in-time recovery to 2026-10-03 12:41:07+00
2026-10-03 12:52:10.161 UTC [8812] LOG:  restored log file "00000001000000000000005C" from archive
2026-10-03 12:52:10.402 UTC [8812] LOG:  redo starts at 0/5C000028
2026-10-03 12:52:10.611 UTC [8812] LOG:  consistent recovery state reached at 0/5C000138
2026-10-03 12:52:10.612 UTC [8810] LOG:  database system is ready to accept read-only connections
2026-10-03 12:52:13.877 UTC [8812] LOG:  restored log file "000000010000000000000063" from archive
2026-10-03 12:52:14.208 UTC [8812] LOG:  recovery stopping before commit of transaction 91877, time 2026-10-03 12:41:12.304113+00
2026-10-03 12:52:14.208 UTC [8812] LOG:  pausing at the end of recovery
2026-10-03 12:52:14.208 UTC [8812] HINT:  Execute pg_wal_replay_resume() to promote.
```

→ Recovery replayed everything up to the first commit after 12:41:07, which was the `DELETE`
(transaction 91877, committed at 12:41:12), and stopped **before** it. Because the target action is
`pause`, the copy is read-only and you can check it before deciding anything:

```bash
sudo -u postgres psql -p 5433 -d appdb -Atc "SELECT count(*) FROM orders WHERE status = 'paid';"
sudo -u postgres psql -p 5433 -c "SELECT pg_wal_replay_resume();"     # ends recovery, promotes to timeline 2
```

```
333412
```

→ The rows are back in the side copy. Now choose: copy the missing rows into production (the
least disruptive option, done step by step in the single-table playbook in section 10), or, if the
whole database is damaged, point the application at the recovered cluster after a full check.
Afterwards remove `90-pitr.conf`, and drop the side cluster with `sudo pg_dropcluster 16 pitr --stop`
once you no longer need it.

With pgBackRest the same recovery is one command plus the target, for example
`pgbackrest --stanza=main --type=time "--target=2026-10-03 12:41:07+00" --target-action=promote restore`,
run against a stopped, empty data directory or with `--delta`.

**How it breaks**

| Symptom / error text | First command | Where to go |
|---|---|---|
| `archive command failed with exit code 1` and `archiving write-ahead log file "…" failed too many times` | `SELECT * FROM pg_stat_archiver;`, then the archive mount and permissions | fix the target; queued WAL drains by itself |
| `FATAL:  recovery ended before configured recovery target was reached` | `ls /srv/walarchive` around the target | a segment is missing from the archive: pick an earlier target or find the file |
| Recovered to the wrong moment | the time zone in `recovery_target_time` | always write the offset (`+00`), and use `pause` to inspect before promoting |
| A restored copy writes into the production archive | `SHOW archive_mode;` on the copy | `archive_mode = off` on every restore cluster |
| `pg_verifybackup: error: checksum mismatch for file` | storage health | take a new base backup, check the disk |
| `pg_wal` fills while archiving looks fine | `pg_replication_slots` | a slot, not the archiver (section 10, disk full) |

**Why it matters for troubleshooting.** PITR turns "we lost everything since 02:00" into "we lost
nothing". It also explains a whole class of disk incidents: once archiving is on, a broken archive
target fills `pg_wal`, so the archive itself must be monitored.

**Next step:** the MySQL equivalent: physical backups with XtraBackup and binlog replay.

### MySQL physical backups and binlog PITR

**Level:** [L3 · Senior] · about 90 minutes

**Concept.** For MySQL the physical tool is **Percona XtraBackup** (free; use the 8.0 series for
MySQL 8.0 and the 8.4 series for MySQL 8.4). For MariaDB it is **Mariabackup**
(`mariadb-backup`). Both copy InnoDB files while the server runs and record the redo log written
during the copy. A backup has three phases:

1. `--backup` copies the files and writes the binlog coordinates to `xtrabackup_binlog_info`.
2. `--prepare` applies the redo log so the files become consistent. **A backup that was never
   prepared cannot be started.** Prepare right after the backup, or at least in the restore test.
3. `--copy-back` puts the files into an empty data directory; then fix ownership and start MySQL.

Point-in-time recovery then replays the **binlogs** written after the backup with `mysqlbinlog`,
stopping just before the bad transaction. Binlogs are the only source of those changes, so copy
them off the server continuously (for example with `mysqlbinlog --read-from-remote-server
--raw --stop-never` on the backup server) and make `binlog_expire_logs_seconds` longer than the
interval between full backups.

Install XtraBackup from Percona's apt repository (their `percona-release` tool sets it up; package
`percona-xtrabackup-80` for MySQL 8.0), and upgrade it **with** the server: an older XtraBackup can
refuse to back up a newer server minor version because the redo log format changed.

**See it on a real system**

```bash
sudo xtrabackup --backup --user=root --target-dir=/srv/xtrabackup/full-2026-10-03 2>&1 | tail -n 2
sudo xtrabackup --prepare --target-dir=/srv/xtrabackup/full-2026-10-03 2>&1 | tail -n 1
sudo cat /srv/xtrabackup/full-2026-10-03/xtrabackup_binlog_info
```

```
2026-10-03T13:02:09.881204-00:00 0 [Note] [MY-011825] [Xtrabackup] Transaction log of lsn (19422038) to (19422058) was copied.
2026-10-03T13:02:10.112933-00:00 0 [Note] [MY-011825] [Xtrabackup] completed OK!
2026-10-03T13:03:41.520771-00:00 0 [Note] [MY-011825] [Xtrabackup] completed OK!
binlog.000003	48211907
```

→ Two `completed OK!` lines: one for the backup, one for the prepare. The binlog file and position
are where binlog replay must start. With GTIDs enabled the file also holds the GTID set.

**Hands-on lab (test VM only, snapshot db1 first)**

**Step 1 — Build.** Take and prepare the backup above, then note the time and run some writes with
`INSERT`s into `appdb.orders`.

**Step 2 — Break it.** Run `DELETE FROM appdb.orders WHERE status = 'paid';`, then find the bad
transaction in the binlog:

```bash
sudo mysqlbinlog --base64-output=DECODE-ROWS -v --start-datetime="2026-10-03 13:10:00" \
  --stop-datetime="2026-10-03 13:15:00" /var/lib/mysql/binlog.000003 | grep -n -B18 -m1 'DELETE FROM `appdb`.`orders`'
```

```
1411-# at 51200433
1412-#261003 13:12:40 server id 1  end_log_pos 51200512 CRC32 0x4f1d2a7c 	Anonymous_GTID	last_committed=8121	sequence_number=8122	rbr_only=yes	original_committed_timestamp=1791033160304118	immediate_commit_timestamp=1791033160304118	transaction_length=9813421
1413-/*!50718 SET TRANSACTION ISOLATION LEVEL READ COMMITTED*//*!*/;
1414-# original_commit_timestamp=1791033160304118 (2026-10-03 13:12:40.304118 UTC)
1415-# immediate_commit_timestamp=1791033160304118 (2026-10-03 13:12:40.304118 UTC)
1416-/*!80001 SET @@session.original_commit_timestamp=1791033160304118*//*!*/;
1417-/*!80014 SET @@session.original_server_version=80043*//*!*/;
1418-/*!80014 SET @@session.immediate_server_version=80043*//*!*/;
1419-SET @@SESSION.GTID_NEXT= 'ANONYMOUS'/*!*/;
1420-# at 51200512
1421-#261003 13:12:40 server id 1  end_log_pos 51200589 CRC32 0x1a2b3c4d 	Query	thread_id=1442	exec_time=0	error_code=0
1422-SET TIMESTAMP=1791033160/*!*/;
1423-BEGIN
1424-/*!*/;
1425-# at 51200589
1426-#261003 13:12:40 server id 1  end_log_pos 51200664 CRC32 0x6e7f8091 	Table_map: `appdb`.`orders` mapped to number 92
1427-# at 51200664
1428-#261003 13:12:40 server id 1  end_log_pos 51208851 CRC32 0x22c1f0aa 	Delete_rows: table id 92
1429:### DELETE FROM `appdb`.`orders`
```

→ The bad transaction starts at position **51200433** (its GTID event, just before `BEGIN`).
`mysqlbinlog` prints times in the time zone of the machine running it; on servers set to UTC that
is UTC.

**Step 3 — Fix it: restore and replay up to that position.**

```bash
sudo systemctl stop mysql
sudo mv /var/lib/mysql /var/lib/mysql.broken-2026-10-03     # keep it (and its binlogs) until verified
sudo xtrabackup --copy-back --target-dir=/srv/xtrabackup/full-2026-10-03 --datadir=/var/lib/mysql
sudo chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysql
sudo mysqlbinlog --start-position=48211907 --stop-position=51200433 \
  /var/lib/mysql.broken-2026-10-03/binlog.000003 | sudo mysql
sudo mysql -e "SELECT count(*) FROM appdb.orders WHERE status = 'paid';"
```

→ The backup brings the server to 13:02, the replay applies everything up to the start of the
`DELETE` and stops. If the changes span several binlog files, pass them all to **one**
`mysqlbinlog` command so that transactions crossing a file boundary replay correctly. In
production you would restore on a separate server and copy rows back, exactly as in the PostgreSQL
lab; the in-place version here shows every moving part.

**How it breaks**

| Symptom / error text | First command | Fix |
|---|---|---|
| MySQL will not start after `--copy-back` | `sudo tail -n 20 /var/log/mysql/error.log` | the backup was not prepared, or ownership is wrong (`chown -R mysql:mysql`) |
| XtraBackup fails right after a MySQL minor upgrade | `xtrabackup --version` | upgrade XtraBackup to a release that supports the server version |
| `Got fatal error 1236` style gaps, or binlogs for the needed period are gone | `SHOW BINARY LOGS;` | raise `binlog_expire_logs_seconds`, stream binlogs to the backup server |
| Replay stops with `ERROR 1062 (23000): Duplicate entry` | the start position | replay must start exactly at the coordinates in `xtrabackup_binlog_info` |
| Restored to the wrong moment | the time zone of `--start-datetime`/`--stop-datetime` | prefer positions (or GTIDs) over times |

**Why it matters for troubleshooting.** Binlogs are both the replication stream and the PITR source.
If you know where a transaction starts in the binlog, you can undo a mistake to the second and
explain to developers exactly which statement did the damage.

**Next step:** prove all of this keeps working without you: automated restore tests.

### Restore tests and backup alerts

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 90 minutes

**Concept.** "The backup job succeeded" only means a file was written. A **restore test** is a
scheduled job that restores the newest backup into a throwaway instance, checks it, measures how
long it took and publishes the result as a metric, so a failure becomes an alert rather than a
surprise during an incident. Good checks:

- the restore command exits 0 (and, for encrypted backups, decryption worked);
- key tables have plausible row counts (not 0, not half of yesterday's);
- the newest row is younger than your RPO (catches "the backup is from last month");
- the restore duration is within your RTO (catches slow growth into an RTO breach);
- optionally, the application's smoke test runs against the restored copy.

Run it on the backup server or a spare VM, not on the database host: it proves the backup is usable
off-host and does not compete with production for I/O. Quarterly, also run a **manual restore
drill**: a second person follows the written runbook with a timer, because the person who wrote the
runbook is not the one who will be awake when it is needed.

**See it on a real system: a restore test in about 30 lines**

```bash
#!/usr/bin/env bash
# /usr/local/sbin/restore-test.sh: restore the newest appdb dump into a throwaway container and check it
set -euo pipefail
BACKUP_DIR=/srv/backups/db1
METRICS=/var/lib/prometheus/node-exporter/restore_test.prom
NAME=restore-test-$$
DUMP=$(find "$BACKUP_DIR" -name 'appdb-*.dump' -printf '%T@ %p\n' | sort -n | tail -n 1 | cut -d' ' -f2-)
START=$(date +%s)
trap 'docker rm -f -v "$NAME" >/dev/null 2>&1 || true' EXIT   # -v: also remove the anonymous data volume

docker run -d --name "$NAME" -e POSTGRES_USER=app -e POSTGRES_DB=appdb \
  -e POSTGRES_PASSWORD=restore-test-only -v "$BACKUP_DIR":/backups:ro postgres:16 >/dev/null
# The image's init step runs a temporary server on the Unix socket only, so wait for TCP
until docker exec "$NAME" pg_isready -h 127.0.0.1 -U app -q; do sleep 2; done

docker exec "$NAME" pg_restore -U app -d appdb -j 4 --no-owner "/backups/$(basename "$DUMP")"
ROWS=$(docker exec "$NAME" psql -U app -d appdb -Atc "SELECT count(*) FROM orders;")
AGE=$(docker exec "$NAME" psql -U app -d appdb -Atc "SELECT extract(epoch FROM now() - max(created_at))::int FROM orders;")
DURATION=$(( $(date +%s) - START ))

[ "$ROWS" -gt 900000 ] || { echo "FAIL: only $ROWS orders in $DUMP"; exit 1; }
[ "$AGE" -lt 93600 ]   || { echo "FAIL: newest order is $AGE s old in $DUMP"; exit 1; }

cat > "$METRICS.tmp" <<EOF
db_restore_test_last_success_timestamp_seconds{db="appdb"} $(date +%s)
db_restore_test_duration_seconds{db="appdb"} $DURATION
db_restore_test_rows{db="appdb",table="orders"} $ROWS
EOF
mv "$METRICS.tmp" "$METRICS"
echo "OK: $(basename "$DUMP") restored in ${DURATION}s, $ROWS orders, newest ${AGE}s old"
```

```ini
# /etc/systemd/system/restore-test.service
[Unit]
Description=Restore the newest appdb dump and verify it
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/restore-test.sh
```

```ini
# /etc/systemd/system/restore-test.timer
[Unit]
Description=Weekly appdb restore test

[Timer]
OnCalendar=Sun *-*-* 05:00:00
RandomizedDelaySec=30m
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now restore-test.timer
sudo systemctl start restore-test.service
journalctl -u restore-test.service -n 3 --no-pager
```

```
Oct 03 13:20:41 app1 restore-test.sh[10422]: OK: appdb-2026-10-03_0200.dump restored in 58s, 1000000 orders, newest 4310s old
Oct 03 13:20:41 app1 systemd[1]: restore-test.service: Deactivated successfully.
Oct 03 13:20:41 app1 systemd[1]: Finished restore-test.service - Restore the newest appdb dump and verify it.
```

→ 58 seconds of measured RTO and a fresh data point every week. The thresholds (900,000 rows,
26 hours) are this lab's numbers; derive yours from production. Keep the image's major version
(`postgres:16`) equal to production's, or the test stops proving anything. Like the backup script,
the metric is written last, so any failed check leaves the old timestamp and section 9's
"restore test too old" alert fires.

**Hands-on lab (test VM only)**

**Step 1 — Build.** On app1 (it has Docker), sync the dumps from db1 with the pull-model `rsync`
from the first topic, install the script and timer, and run it once.

**Step 2 — Break it.** On db1, change the backup script to dump a database that is almost empty
(for example `postgres` instead of `appdb`), run it, sync, and run the restore test.

```
Oct 03 13:31:02 app1 restore-test.sh[10988]: ERROR:  relation "orders" does not exist
Oct 03 13:31:02 app1 restore-test.sh[10988]: LINE 1: SELECT count(*) FROM orders;
Oct 03 13:31:02 app1 systemd[1]: restore-test.service: Main process exited, code=exited, status=1/FAILURE
Oct 03 13:31:02 app1 systemd[1]: restore-test.service: Failed with result 'exit-code'.
```

→ `pg_restore` had nothing to complain about, because the dump was a perfectly valid backup of the
wrong database. The backup job reported success every night; only the restore test's checks
noticed that the backups are useless. This exact failure (a backup of the wrong thing) is more common than a crashed backup job.

**Step 3 — Fix it.** Restore the backup script, rerun both jobs, and confirm the metric file has a
new timestamp: `cat /var/lib/prometheus/node-exporter/restore_test.prom`.

**How it breaks**

| Failure | Symptom | First check |
|---|---|---|
| Restore test never runs | metric timestamp stops moving | `systemctl list-timers restore-test.timer` |
| Test passes on an old file | `AGE` check fails, or `ls -lt` shows no new dumps | the backup job and the sync |
| Test image newer than the dump | `pg_restore` works but production cannot restore with its own client | pin the image to production's major version |
| Disk fills on the test host | restore aborts with `No space left on device` | `docker volume ls -f dangling=true`: the postgres image declares a volume, so remove containers with `docker rm -v` |

**Why it matters for troubleshooting.** When someone asks "can we restore?" at 3 a.m., you answer with
last Sunday's measured result instead of a guess. That is the difference between operating a backup
and owning one.

**Next step:** backups protect you from mistakes. Replication protects you from dead servers.

---

## 5. Replication and high availability

> 📚 **Study path:** 1) Note: "WAL and binlog" in section 1 of this module, a quick refresher, so it comes first · 2) KodeKloud: *Docker Certified Associate* — Docker Swarm: High Availability/Quorum, the same majority-vote idea that Patroni's etcd and your Kubernetes control plane rely on ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts: etcd, the store Patroni most often uses for its leader lock, and CKA study at the same time ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 4) Read: the "High Availability, Load Balancing, and Replication" chapter of the [PostgreSQL documentation](https://www.postgresql.org/docs/) and the Replication chapter of the [MySQL documentation](https://dev.mysql.com/doc/); KodeKloud has no database replication course in the verified map (check the current catalog) · 5) Note: [Senior architecture](39-learn-senior-architecture.md) for failure domains and DR tiers · 6) Practice: build the db1 → db2 replica below, then run the failover drill with a timer.

Replication continuously copies every committed change from a **primary** to one or more
**standbys** (MySQL says source and replica). It gives you a warm spare for hardware failure, a
place for read-only traffic and reports, a source for backups that does not load the primary, and
the basis of near-zero-downtime upgrades. It does **not** give you a backup: mistakes, bad
migrations and application bugs replicate in milliseconds.

**High availability** is replication plus five things that must all work, automatically or by
runbook: detect the failure, choose the most up-to-date standby, promote it, stop the old primary
from accepting writes (fencing), and send the clients to the new primary. Most HA outages come from
the last two, not from replication itself.

### Streaming replication

**Level:** [L3 · Senior] · about 90 minutes

**Concept.** A PostgreSQL standby connects to the primary with the replication protocol. On the
primary a **walsender** process streams WAL as it is written; on the standby a **walreceiver**
writes it to the standby's `pg_wal` and the startup process **replays** it. With `hot_standby = on`
(the default) the standby answers read-only queries while it replays.

```
 db1 (primary, read-write)                            db2 (standby, read-only)
 ┌─────────────────────────┐   WAL stream, TCP 5432  ┌─────────────────────────┐
 │ backends write WAL      │ ──────────────────────▶ │ walreceiver → pg_wal    │
 │ walsender               │ ◀── feedback (LSNs) ─── │ startup process: replay │
 │ slot "db2" keeps WAL    │                         │ hot standby: SELECTs    │
 └─────────────────────────┘                         └─────────────────────────┘
```

Replication is **asynchronous** by default: a commit returns as soon as the primary has flushed
its own WAL, so a primary crash can lose the last fraction of a second of commits. Synchronous
replication closes that gap at a price:

| Mode | Setting | Commit waits for | Loss if the primary dies | Cost |
|---|---|---|---|---|
| Asynchronous (default) | `synchronous_standby_names = ''` | local WAL flush | the current lag, usually under a second | none |
| Synchronous | `synchronous_standby_names = 'ANY 1 (db2, db3)'` | one listed standby has flushed it | none | a network round trip per commit; with a single standby, its outage stops all writes |
| Synchronous with `remote_apply` | `synchronous_commit = remote_apply` | a standby has **applied** it | none, and reads there see the write | the highest commit latency |

**Key terms**

| Term | Meaning |
|---|---|
| Hot standby | A standby that serves read-only queries while replaying |
| Replication slot | Makes the primary keep WAL until this standby has it; without one, a standby that falls too far behind must be rebuilt |
| `max_slot_wal_keep_size` | Cap on WAL a slot may pin (PostgreSQL 13+); beyond it the slot is invalidated instead of filling the disk |
| `primary_conninfo` | How the standby connects to the primary; written by `pg_basebackup -R` into `postgresql.auto.conf` |
| `standby.signal` | Empty file in the data directory: "start as a standby" |
| Promote | Turn a standby into a primary (`pg_ctlcluster 16 main promote` or `SELECT pg_promote();`) |

**Setup on Ubuntu** (lab: db1 192.168.56.21 is the primary, db2 192.168.56.22 the standby). On db1:

```bash
sudo -u postgres psql -c "CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'LabRepl-123';"
echo "host  replication  replicator  192.168.56.22/32  scram-sha-256" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
sudo tee /etc/postgresql/16/main/conf.d/60-replication.conf >/dev/null <<'EOF'
listen_addresses = 'localhost,192.168.56.21'
max_slot_wal_keep_size = 10GB      # a dead standby may pin at most 10 GB of WAL
EOF
sudo systemctl restart postgresql@16-main
```

`wal_level = replica`, `max_wal_senders = 10` and `max_replication_slots = 10` are already the
defaults. Note that `all` in the database column of `pg_hba.conf` does **not** match replication
connections; they need the `replication` keyword. On db2:

```bash
echo "192.168.56.21:5432:replication:replicator:LabRepl-123" | sudo -u postgres tee /var/lib/postgresql/.pgpass >/dev/null
sudo -u postgres chmod 0600 /var/lib/postgresql/.pgpass
sudo systemctl stop postgresql@16-main
sudo mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main.orig    # keep until the standby works
sudo -u postgres pg_basebackup -h 192.168.56.21 -U replicator -D /var/lib/postgresql/16/main \
  -X stream -C -S db2 -R -P
sudo systemctl start postgresql@16-main
```

`-C -S db2` creates the slot `db2` on the primary, and `-R` writes `standby.signal` plus
`primary_conninfo` and `primary_slot_name`. On Ubuntu the configuration files live in
`/etc/postgresql/16/main/`, outside the data directory, so the base backup does **not** copy them:
keep db1 and db2 configured alike (memory settings, `max_connections`, extensions), or the standby
may refuse to start or behave differently after a failover.

**See it on a real system.** On the primary:

```bash
sudo -u postgres psql -x -c "SELECT application_name, client_addr, state, sent_lsn, replay_lsn, write_lag, flush_lag, replay_lag, sync_state FROM pg_stat_replication;"
```

```
-[ RECORD 1 ]----+----------------
application_name | 16/main
client_addr      | 192.168.56.22
state            | streaming
sent_lsn         | 0/7A0001F8
replay_lsn       | 0/7A0001F8
write_lag        | 00:00:00.000912
flush_lag        | 00:00:00.001873
replay_lag       | 00:00:00.002201
sync_state       | async
```

→ One standby, streaming, fully replayed. `application_name` shows Ubuntu's `cluster_name`
(`16/main`) because `primary_conninfo` does not set one; add `application_name=db2` to it so that
`pg_stat_replication` and `synchronous_standby_names` can tell standbys apart. On the standby:

```bash
sudo -u postgres psql -x -c "SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), now() - pg_last_xact_replay_timestamp() AS replay_age;"
sudo -u postgres psql -x -c "SELECT status, sender_host, slot_name FROM pg_stat_wal_receiver;"
```

```
-[ RECORD 1 ]-----------+----------------
pg_is_in_recovery       | t
pg_last_wal_receive_lsn | 0/7A0001F8
pg_last_wal_replay_lsn  | 0/7A0001F8
replay_age              | 00:00:03.418722

-[ RECORD 1 ]---------------
status      | streaming
sender_host | 192.168.56.21
slot_name   | db2
```

→ Receive and replay positions are equal, so nothing is waiting. `replay_age` is the time since
the last **replayed transaction**: on an idle primary it grows even though the standby is not
behind at all. Compare LSNs before you raise an alarm (next topic).

**Hands-on lab (test VMs only)**

**Step 1 — Build.** Set up db2 as above. On db1 run `CREATE TABLE repl_test (x int);` and check
that `\d repl_test` works on db2 a moment later. On db2 try `INSERT INTO repl_test VALUES (1);` and
read the error: `ERROR:  cannot execute INSERT in a read-only transaction`.

**Step 2 — Break it, twice.** First, stop the standby while the primary is busy and watch its slot:

```bash
# db2
sudo systemctl stop postgresql@16-main
# db1, after a few minutes of: pgbench -h 127.0.0.1 -U app -c 8 -T 300 appdb
sudo -u postgres psql -c "SELECT slot_name, active, wal_status, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained, pg_size_pretty(safe_wal_size) AS safe FROM pg_replication_slots;"
```

```
 slot_name | active | wal_status | retained |  safe
-----------+--------+------------+----------+---------
 db2       | f      | extended   | 2304 MB  | 7936 MB
(1 row)
```

→ The slot keeps 2.3 GB of WAL for the absent standby, and 7.9 GB more may accumulate before
`max_slot_wal_keep_size` invalidates the slot. Without that cap, a standby that stays down over a
weekend fills the primary's disk.

Second, start db2 again and create a **replication conflict**. On db2 open a long read:
`BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT count(*) FROM pgbench_accounts;`, keep pgbench
running on db1, wait a few minutes and repeat the `SELECT` in the same transaction:

```
ERROR:  canceling statement due to conflict with recovery
DETAIL:  User query might have needed to see row versions that must be removed.
```

→ Vacuum on the primary removed row versions that the standby query still needed. After
`max_standby_streaming_delay` (30 s by default) of replay waiting, PostgreSQL cancels the query to
let replication continue.

**Step 3 — Fix it.** The stopped standby: start it and watch `retained` shrink to almost nothing as
it catches up. The conflict has three possible fixes, each with a cost, and choosing one is the
senior part:

| Fix | Effect | Cost |
|---|---|---|
| `hot_standby_feedback = on` on the standby | primary keeps the rows the standby needs | bloat on the primary while long standby queries run |
| Raise `max_standby_streaming_delay` | replay waits longer for queries | replication lag grows during long queries (playbook in section 10) |
| A separate replica for reports | fresh replica for the app, a lagging one for reports | another server |

**How it breaks**

| Symptom / error text | First command | Fix |
|---|---|---|
| `no pg_hba.conf entry for replication connection from host "192.168.56.22", user "replicator"` | `grep replication /etc/postgresql/16/main/pg_hba.conf` | add a `replication` line, reload |
| `FATAL:  could not start WAL streaming: ERROR:  replication slot "db2" does not exist` | `SELECT slot_name FROM pg_replication_slots;` on the primary | `SELECT pg_create_physical_replication_slot('db2');` |
| `requested WAL segment 0000000100000000000000A1 has already been removed` | `wal_status` of the slot (`lost`?) | rebuild the standby with `pg_basebackup` |
| `canceling statement due to conflict with recovery` | which queries run on the standby | table above |
| Primary disk filling | `pg_replication_slots` | section 10, disk full |

**Why it matters for troubleshooting.** Every replication incident is one of three questions: is
the standby connected, is WAL arriving, is WAL being replayed? The two views above answer all three
in seconds, from either side.

**Next step:** measure lag precisely, because "the replica is behind" is the ticket you will get.

### Measuring replication lag

**Level:** [L3 · Senior] · about 30 minutes

**Concept.** "Lag" means three different things, and each points to a different bottleneck:

| Where the WAL is waiting | Primary-side measure | Usual cause |
|---|---|---|
| Not yet **sent** | `pg_current_wal_lsn() - sent_lsn` | standby disconnected, network saturated, primary overloaded |
| Sent, not yet **flushed** on the standby | `sent_lsn - flush_lsn` | network latency, slow standby disk |
| Flushed, not yet **replayed** | `flush_lsn - replay_lsn` | replay is slow (I/O, a huge transaction) or blocked (conflicts, `pg_wal_replay_pause()`) |

Bytes tell you *how much* is waiting; `write_lag`, `flush_lag` and `replay_lag` in
`pg_stat_replication` tell you *how long* recent WAL took to get there. On the standby,
`now() - pg_last_xact_replay_timestamp()` is easy to read but lies on an idle primary.

In MySQL, `Seconds_Behind_Source` in `SHOW REPLICA STATUS` compares the applier with the events it
has already received. It shows 0 while the receiver itself is behind (for example on a saturated
link) and NULL when a replication thread is stopped. For a truthful number, write a timestamp on
the source every second and read it on the replica (`pt-heartbeat` from Percona Toolkit does
exactly that), or use the `performance_schema.replication_applier_status_by_worker` timestamps.

Lag matters to users through **read-your-writes**: a user saves an order (primary), the next page
reads from the replica, and the order "disappeared". Route reads that must see the user's own
writes to the primary.

**See it on a real system**

```bash
sudo -u postgres psql -x -c "SELECT application_name, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn)) AS not_sent, pg_size_pretty(pg_wal_lsn_diff(sent_lsn, flush_lsn)) AS not_flushed, pg_size_pretty(pg_wal_lsn_diff(flush_lsn, replay_lsn)) AS not_replayed, replay_lag FROM pg_stat_replication;"
```

```
-[ RECORD 1 ]----+----------------
application_name | db2
not_sent         | 0 bytes
not_flushed      | 0 bytes
not_replayed     | 41 MB
replay_lag       | 00:00:09.812004
```

→ Everything arrived; 41 MB is waiting to be replayed, about 10 seconds' worth. A short spike like
this after a bulk job is normal; a number that keeps growing is an incident.

**Hands-on lab (test VMs only)**

**Step 1 — Build.** Keep pgbench running on db1 against the replica pair.

**Step 2 — Break it.** On db2 run `SELECT pg_wal_replay_pause();` and watch `not_replayed` and
`replay_lag` grow on db1 every 10 seconds, while `not_sent` stays at 0. On the MySQL pair, run
`STOP REPLICA SQL_THREAD;` on the replica and watch `Seconds_Behind_Source` turn NULL.

**Step 3 — Fix it.** `SELECT pg_wal_replay_resume();` on db2 and time how long it takes to catch
up: that is your replay speed, and it tells you how long a standby needs after a burst. On MySQL,
`START REPLICA SQL_THREAD;`.

**How it breaks:** the full walk is the "replication lag" playbook in section 10; the alert is in
section 9.

**Why it matters for troubleshooting.** The three-way split turns "the replica is slow" into
"network", "disk" or "replay", each with a different owner and fix.

**Next step:** when the primary dies, a standby must take over safely.

### Failover, fencing and Patroni

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 90 minutes

**Concept.** A **switchover** is planned: the old primary shuts down cleanly first, so nothing is
lost. A **failover** is unplanned: the primary is gone, and the most up-to-date standby is
promoted. The dangerous part of a failover is not the promotion, it is the old primary. If it comes
back and accepts writes while the new primary also accepts writes, you have **split brain**: two
diverging histories that no tool can merge automatically. **Fencing** prevents it: power the old
node off, block it at the network, or make sure it can only rejoin as a standby.

A manual failover on the lab pair has five steps:

1. Confirm the primary is really gone (from more than one place) and note the time.
2. Promote the best standby: `sudo pg_ctlcluster 16 main promote` (or `SELECT pg_promote();`).
3. Fence the old primary: keep it stopped (`systemctl mask` it, or power it off).
4. Repoint clients: DNS (mind the TTL), a virtual IP, a proxy, or a multi-host connection string.
5. Rebuild the old primary as a standby: `pg_rewind` if possible, otherwise `pg_basebackup`.

`pg_rewind` rewinds the old primary's data directory to the point where the histories diverged,
which is much faster than a full copy. It requires `wal_log_hints = on` or data checksums (which
PostgreSQL 16's `initdb` does not enable by default; from PostgreSQL 18 `initdb` enables them unless
told not to, but clusters upgraded from older versions keep their old setting, so check with
`SHOW data_checksums;`), so set `wal_log_hints = on` on every node **before** you need it.

**Patroni** automates all five steps. A Patroni agent runs next to PostgreSQL on every node and
competes for a **leader key** in a distributed configuration store (DCS): etcd, Consul, ZooKeeper,
or the Kubernetes API. The leader must renew the key before its TTL expires; if it cannot, it
demotes itself, and a healthy replica takes the key and promotes. Clients find the leader through a
proxy that asks each node's Patroni REST API.

```
  ┌───────────────── etcd: 3 nodes, majority quorum ─────────────────┐
  │          leader key for cluster pg-main = db1 (TTL 30 s)         │
  └──────────▲──────────────────────▲──────────────────────▲─────────┘
             │ renew / watch        │                      │
  ┌──────────┴─────────┐ ┌──────────┴─────────┐ ┌──────────┴─────────┐
  │ db1  Patroni :8008 │ │ db2  Patroni :8008 │ │ db3  Patroni :8008 │
  │ PostgreSQL leader  │ │ PostgreSQL replica │ │ PostgreSQL replica │
  └──────────▲─────────┘ └────────────────────┘ └────────────────────┘
             │  HAProxy :5000 sends traffic only where GET /primary on :8008 returns 200
           apps
```

The DCS needs three (or five) members for a majority, exactly like Swarm managers and the
Kubernetes etcd: with two nodes, losing one loses the quorum. If Patroni loses the DCS, the leader
stops accepting writes on purpose. That looks like an outage, but it is the fencing that prevents
split brain.

**See it on a real system** (a three-node Patroni lab, optional)

```bash
patronictl -c /etc/patroni/config.yml list
curl -s -o /dev/null -w 'db1 %{http_code}\n' http://192.0.2.21:8008/primary
curl -s -o /dev/null -w 'db2 %{http_code}\n' http://192.0.2.22:8008/primary
```

```
+ Cluster: pg-main (7421934417262931234) -----+----+-----------+
| Member | Host       | Role    | State     | TL | Lag in MB |
+--------+------------+---------+-----------+----+-----------+
| db1    | 192.0.2.21 | Leader  | running   |  3 |           |
| db2    | 192.0.2.22 | Replica | streaming |  3 |         0 |
| db3    | 192.0.2.23 | Replica | streaming |  3 |         0 |
+--------+------------+---------+-----------+----+-----------+
db1 200
db2 503
```

→ One leader on timeline 3 (two promotions so far in this cluster's life), two replicas with no lag. The
REST API answers 200 on `/primary` only on the leader; that is what the proxy uses. The exact
columns of `patronictl list` vary between Patroni versions.

```
# /etc/haproxy/haproxy.cfg (excerpt)
listen postgres_primary
    bind *:5000
    mode tcp
    option httpchk GET /primary
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server db1 192.0.2.21:5432 maxconn 200 check port 8008
    server db2 192.0.2.22:5432 maxconn 200 check port 8008
    server db3 192.0.2.23:5432 maxconn 200 check port 8008
```

Without a proxy, libpq-based drivers can find the writable node themselves:
`postgresql://app@db1.example.internal,db2.example.internal,db3.example.internal/appdb?target_session_attrs=read-write`.
On AWS, RDS Multi-AZ does all of this for you behind one DNS name (section 7, "RDS basics", in
[Cloud & AWS](36-learn-cloud-aws.md)).

Planned work uses `patronictl switchover`, and `patronictl pause` puts the cluster into
maintenance mode so Patroni does not "repair" a node you stopped on purpose.

**Hands-on lab (test VMs only): a timed manual failover on db1/db2**

**Step 1 — Build.** Set `wal_log_hints = on` on both nodes (restart), confirm streaming, start
pgbench against db1, start a stopwatch.

**Step 2 — Break it.** Power off db1 from the hypervisor (a crash, not a clean shutdown). On db2,
confirm it really is gone (`pg_stat_wal_receiver` shows no `streaming` row), then promote:

```bash
sudo pg_ctlcluster 16 main promote
sudo -u postgres psql -Atc "SELECT pg_is_in_recovery();"
```

```
f
```

→ db2 is now a primary. Point pgbench (your "application") at 192.168.56.22, and stop the
stopwatch when it runs again: that is your RTO for a manual failover.

**Step 3 — Break it worse: split brain.** Power db1 back on **without** fencing it. Its PostgreSQL
starts as a primary, because nothing told it otherwise. Run an `INSERT` on both nodes: both
succeed, with different data. This is the outcome fencing exists to prevent. (Ubuntu starts
PostgreSQL at boot, which is exactly why a crashed primary must be masked or kept powered off.)

**Step 4 — Fix it.** Stop db1, rewind it against the new primary, and start it as a standby:

```bash
# db1 (the writes made on db1 after the split are discarded by the rewind)
sudo systemctl stop postgresql@16-main
sudo -u postgres /usr/lib/postgresql/16/bin/pg_rewind --target-pgdata=/var/lib/postgresql/16/main \
  --source-server="host=192.168.56.22 user=postgres dbname=postgres" -R --progress
sudo systemctl start postgresql@16-main
```

```
pg_rewind: connected to server
pg_rewind: servers diverged at WAL location 0/9A000148 on timeline 1
pg_rewind: rewinding from last common checkpoint at 0/9A0000D8 on timeline 1
pg_rewind: reading source file list
pg_rewind: reading target file list
pg_rewind: reading WAL in target
pg_rewind: need to copy 211 MB (total source directory size is 2954 MB)
pg_rewind: creating backup label and updating control file
pg_rewind: syncing target data directory
pg_rewind: Done!
```

→ db1 is now a standby of db2 (`-R` wrote `standby.signal` and `primary_conninfo`). The source
connection needs a superuser or a role granted the functions `pg_rewind` uses, plus a
`pg_hba.conf` line on db2 for it. Write down the timeline you just lived through; it is the
skeleton of your failover runbook.

**How it breaks**

| Symptom | First check | Lesson |
|---|---|---|
| Two nodes both return `f` for `pg_is_in_recovery()` | `pg_is_in_recovery()` on every node | split brain: fence first, then rebuild one side |
| Failover lost the last minutes of orders | lag at the moment of failure | asynchronous replication: decide whether you need synchronous |
| Apps still write to the old address after failover | DNS TTL, connection pools, PgBouncer config | client redirection is part of HA |
| `pg_rewind: error: target server needs to use either data checksums or "wal_log_hints = on"` | `SHOW wal_log_hints;` | enable it before the incident; otherwise use `pg_basebackup` |
| Patroni cluster read-only, `patronictl list` shows no leader | etcd health, quorum | a lost DCS quorum stops writes by design |

**Why it matters for troubleshooting.** A failover is a planned sequence even when the failure is
not. Teams that rehearse it recover in minutes; teams that improvise create split brain.

**Next step:** the MySQL side of replication, where GTIDs make failover sane.

### MySQL replication with GTIDs

**Level:** [L3 · Senior] · about 75 minutes

**Concept.** The source writes changes to its binlog. On the replica a **receiver (I/O) thread**
copies them into a local relay log, and **applier (SQL) threads** execute them; MySQL 8.0.27+ uses
four parallel applier workers by default. With **GTIDs** (global transaction identifiers,
`server_uuid:number`) every transaction has a unique name, and a replica set to
`SOURCE_AUTO_POSITION = 1` tells the source which transactions it already has, so pointing a replica
at a new source after a failover needs no file names or positions.

- Replicas should run with `super_read_only = ON`, so nobody (not even an administrator by
  accident) writes to them and causes divergence.
- HA options: **InnoDB Cluster** (Group Replication managed with MySQL Shell, with MySQL Router in
  front), Orchestrator for classic asynchronous topologies, or a managed service.
- MariaDB uses its own, incompatible GTID format (`domain-server-sequence`), and many MariaDB
  shops use **Galera** for multi-primary clusters instead.

**Setup** (both nodes; `server_id` must differ):

```ini
# /etc/mysql/mysql.conf.d/zz-replication.cnf on db1, named to sort after Ubuntu's mysqld.cnf
# (on db2: server_id = 2, bind-address = 127.0.0.1,192.168.56.22, plus read_only = ON and
# super_read_only = ON)
[mysqld]
server_id                = 1
gtid_mode                = ON
enforce_gtid_consistency = ON
bind-address             = 127.0.0.1,192.168.56.21
```

On a server that already has data, `gtid_mode` must be switched online in steps (`OFF_PERMISSIVE`,
`ON_PERMISSIVE`, then `ON`); on fresh lab servers a restart with the file above is enough. Then:

```sql
-- db1 (source)
CREATE USER 'repl'@'192.168.56.22' IDENTIFIED BY 'LabRepl-123' REQUIRE SSL;
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'192.168.56.22';
-- db2 (replica), after seeding it with a copy of db1 (clone plugin, XtraBackup or a dump)
CHANGE REPLICATION SOURCE TO SOURCE_HOST = '192.168.56.21', SOURCE_USER = 'repl',
  SOURCE_PASSWORD = 'LabRepl-123', SOURCE_AUTO_POSITION = 1, SOURCE_SSL = 1;
START REPLICA;
```

The privilege still has its old name, `REPLICATION SLAVE`. The simplest way to seed the replica on
MySQL 8.0.17+ is the clone plugin: `INSTALL PLUGIN clone SONAME 'mysql_clone.so';` on both nodes, a
donor account with `BACKUP_ADMIN` on db1, then on db2
`SET GLOBAL clone_valid_donor_list = '192.168.56.21:3306';` and
`CLONE INSTANCE FROM 'clone'@'192.168.56.21':3306 IDENTIFIED BY 'LabClone-123';`. The replica
restarts with a full copy (if it does not come back by itself, `sudo systemctl start mysql`).

**See it on a real system**

```bash
sudo mysql -e "SHOW REPLICA STATUS\G" | grep -E 'Replica_IO_State|Source_Host|Replica_IO_Running|Replica_SQL_Running:|Seconds_Behind_Source|Last_IO_Errno|Last_SQL_Errno|Gtid_Set|Auto_Position'
```

```
             Replica_IO_State: Waiting for source to send event
                  Source_Host: 192.168.56.21
           Replica_IO_Running: Yes
          Replica_SQL_Running: Yes
        Seconds_Behind_Source: 0
                Last_IO_Errno: 0
               Last_SQL_Errno: 0
           Retrieved_Gtid_Set: 3e11fa47-71ca-11ee-9a3e-080027a1b2c3:1-5821
            Executed_Gtid_Set: 3e11fa47-71ca-11ee-9a3e-080027a1b2c3:1-5821
                Auto_Position: 1
```

→ Both threads `Yes`, every retrieved transaction executed, no errors. The two lines to check first
in any MySQL replication ticket are `Replica_IO_Running` and `Replica_SQL_Running`; the
corresponding `Last_*_Error` line explains a `No`.

**Hands-on lab (test VMs only)**

**Step 1 — Build.** Configure both nodes, seed db2 with the clone plugin, start replication, and
insert a row on db1 to see it on db2. Leave `super_read_only` **off** on db2 for the next step.

**Step 2 — Break it: write to the replica.** On db2 insert a row with id 5000 into `appdb.orders`,
then insert a different row with the same id on db1:

```
               Last_SQL_Errno: 1062
               Last_SQL_Error: Coordinator stopped because there were error(s) in the worker(s). The most recent failure being: Worker 1 failed executing transaction '3e11fa47-71ca-11ee-9a3e-080027a1b2c3:5822' at source log binlog.000004, end_log_pos 1234. See error log and/or performance_schema.replication_applier_status_by_worker table for more details about this failure or others, if any.
          Replica_SQL_Running: No
```

The detail is in the worker table:
`SELECT WORKER_ID, LAST_ERROR_NUMBER, LAST_ERROR_MESSAGE FROM performance_schema.replication_applier_status_by_worker WHERE LAST_ERROR_NUMBER <> 0\G`
shows `Could not execute Write_rows event on table appdb.orders; Duplicate entry '5000' for key
'orders.PRIMARY', Error_code: 1062`.

→ The replica has **diverged**: it contains a row the source never had. Replication stops rather
than guess which version is right.

**Step 3 — Fix it properly.** Do not skip the transaction to make the error go away: that hides the
divergence and the next failover promotes a wrong copy. Either correct the row on db2 to match db1
and `START REPLICA;` (only when you understand both sides, followed by a consistency check with
`pt-table-checksum`), or, the safe default, re-clone db2 from db1. Then set `super_read_only = ON`
on db2 so it cannot happen again.

**How it breaks**

| Symptom / error text | First check | Fix |
|---|---|---|
| `Authentication plugin 'caching_sha2_password' reported error: Authentication requires secure connection.` in `Last_IO_Error` | the `CHANGE REPLICATION SOURCE` options | `SOURCE_SSL = 1`, or `GET_SOURCE_PUBLIC_KEY = 1` |
| `Got fatal error 1236 from source when reading data from binary log: 'Cannot replicate because the source purged required binary logs…'` | `binlog_expire_logs_seconds`, how long the replica was down | rebuild the replica; keep binlogs longer than the longest outage you tolerate |
| `Last_SQL_Errno: 1062` or `1032` | was anyone writing to the replica? | re-clone; `super_read_only = ON` |
| `Seconds_Behind_Source: NULL` | `Replica_IO_Running`, `Replica_SQL_Running` | read the matching `Last_*_Error` |
| `source and replica have equal MySQL server UUIDs` | the VM was cloned with its data directory | remove `/var/lib/mysql/auto.cnf` on the replica, restart |

**Why it matters for troubleshooting.** MySQL replication errors are precise: the error number tells
you whether it is connectivity (I/O thread), missing history (1236) or divergence (1062/1032). Each
has one correct response, and "skip it" is never it.

**Next step:** the other database in nearly every stack you deploy: Redis.

---

## 6. Redis

> 📚 **Study path:** 1) Note: this section first; KodeKloud has no Redis course in the verified map (look for one by name and check the current catalog) · 2) Note: [Memory](04-memory.md) for overcommit and the OOM killer, which explain Redis's two classic failures · 3) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts), because most of your Redis instances run as containers ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 4) Practice: the MISCONF and eviction labs below on db1, or on the [Docker playground](https://kodekloud.com/playgrounds/playground-docker) with the `redis:7` image.

Nearly every application stack you deploy, whether on the Apache VM, in Dokploy or on Kubernetes,
has a Redis next to its database: for the cache, the sessions, the job queue, or all three in one
instance. Redis is simple to run until it is full, cannot write its snapshot, or is reachable from
the internet. This section covers exactly those three situations.

### Redis in one page

**Level:** [L1 · Junior] · about 45 minutes

**Concept.** Redis is an in-memory data-structure server: keys hold strings, hashes, lists, sets,
sorted sets or streams, and any key can have a TTL. One main thread executes commands one at a time,
which makes Redis fast and predictable, and also means **one slow command blocks every client**:
`KEYS *` on a million keys, deleting a huge key, or a long Lua script. Typical uses in your stack:
cache, web sessions, job queues (Sidekiq, Celery, BullMQ), rate limits, locks and pub/sub.

Data lives in RAM. Persistence to disk is optional and configurable (next topic), and the right
setting depends on the use: losing a cache is a slow minute, losing a job queue is lost work.

On Ubuntu 24.04 the package is Redis 7.0: config `/etc/redis/redis.conf`, data `/var/lib/redis`,
log `/var/log/redis/redis-server.log`, unit `redis-server.service`, port 6379. Licensing changed in
2024: Redis 7.4 and later are source-available (Redis 8 added AGPLv3 as an option), and the Linux
Foundation fork **Valkey** continues the BSD-licensed line. Everything in this section works the
same on all of them.

**Key terms**

| Term | Meaning |
|---|---|
| TTL | Time to live of a key; expired keys disappear by themselves |
| Eviction | Redis deleting keys to stay under `maxmemory` |
| RDB / AOF | Snapshot file / append-only log of writes (persistence) |
| Replica, Sentinel | A read-only copy; Sentinel watches a primary and fails over to a replica |
| ACL | Users with passwords and command permissions (Redis 6+) |
| Protected mode | Refuses non-loopback clients while the default user has no password |

**See it on a real system**

```bash
redis-cli PING
redis-cli INFO server | grep -E '^(redis_version|redis_mode|tcp_port|uptime_in_days|config_file):'
redis-cli INFO clients | grep -E '^(connected_clients|maxclients|blocked_clients):'
redis-cli INFO memory | grep -E '^(used_memory_human|used_memory_rss_human|maxmemory_human|maxmemory_policy|mem_fragmentation_ratio):'
redis-cli INFO keyspace
redis-cli SLOWLOG GET 1
```

```
PONG
redis_version:7.0.15
redis_mode:standalone
tcp_port:6379
uptime_in_days:41
config_file:/etc/redis/redis.conf
connected_clients:87
maxclients:10000
blocked_clients:12
used_memory_human:1.21G
used_memory_rss_human:1.43G
maxmemory_human:1.50G
maxmemory_policy:allkeys-lru
mem_fragmentation_ratio:1.18
# Keyspace
db0:keys=1820411,expires=1790022,avg_ttl=1630441
db1:keys=2210,expires=0,avg_ttl=0
1) 1) (integer) 4411
   2) (integer) 1791034212
   3) (integer) 1813220
   4) 1) "KEYS"
      2) "session:*"
   5) "192.0.2.51:51644"
   6) "shop-admin"
```

→ 87 clients, 12 of them blocked: workers waiting on an empty queue with `BLPOP`, which is normal.
`db0` holds 1.8 million keys that almost all have a TTL (a cache); `db1` holds 2,210 keys with
**no** TTL (a queue or sessions). With one `maxmemory-policy` of `allkeys-lru` for the whole
instance, Redis may evict queue entries when the cache fills up: a design problem worth a ticket
(separate instances for cache and queue). The slow log shows a `KEYS session:*` from an admin tool
that took 1.8 seconds, during which every other client waited.

**Hands-on lab (test VM only)**

**Step 1 — Build.** On db1: `redis-cli SET greeting hello EX 60`, `redis-cli TTL greeting`,
`redis-cli GET greeting`, and wait for it to expire.

**Step 2 — Break it.** Make Redis listen on the LAN without a password: set `bind 0.0.0.0` in
`/etc/redis/redis.conf`, `sudo systemctl restart redis-server`, then from app1:

```bash
redis-cli -h 192.168.56.21 PING
```

```
(error) DENIED Redis is running in protected mode because protected mode is enabled and no password is set for the default user. In this mode connections are only accepted from the loopback interface. …
```

→ Protected mode saved you here; with `protected-mode no` this Redis would be open to anyone who
can reach the port (section 8 explains what attackers do with that).

**Step 3 — Fix it.** Bind to the private address only, give the default user a password and the
application its own restricted user:

```
# /etc/redis/redis.conf (lab excerpt)
bind 127.0.0.1 -::1 192.168.56.21
protected-mode yes
user default on >LabRedisAdmin-123 ~* &* +@all
user app on >LabRedis-123 ~* &* +@all -@dangerous +info
```

```bash
sudo systemctl restart redis-server
redis-cli -h 192.168.56.21 --user app --askpass PING
redis-cli -h 192.168.56.21 --user app --askpass FLUSHALL
```

```
PONG
(error) NOPERM User app has no permissions to run the 'flushall' command
```

→ The application can work but cannot wipe the instance or reconfigure it (`@dangerous` covers
`FLUSHALL`, `KEYS`, `CONFIG`, `DEBUG` and more; `+info` is added back because many client
libraries call `INFO`). `--askpass` keeps the password out of your shell history; avoid `-a`.
Finish with a UFW rule that allows 6379 only from the app hosts.

**How it breaks**

| Error text | Gate | First check |
|---|---|---|
| `Could not connect to Redis at 192.168.56.21:6379: Connection refused` | listen | `bind` line, `sudo ss -ltnp 'sport = :6379'` |
| `DENIED Redis is running in protected mode…` | protected mode | set a password or ACL users |
| `NOAUTH Authentication required.` | auth | the client sends no credentials |
| `WRONGPASS invalid username-password pair or user is disabled.` | auth | the secret the app actually has |
| `ERR max number of clients reached` | clients | common incidents topic below |
| Every client slow for a second at a time | blocking command | `SLOWLOG GET 10` |

**Why it matters for troubleshooting.** Redis errors name their cause in the first word (`DENIED`,
`NOAUTH`, `OOM`, `MISCONF`, `READONLY`, `LOADING`). Learn the words and most Redis tickets are
solved by reading the application log carefully.

**Next step:** what Redis writes to disk, and the error that stops all writes when it cannot.

### Persistence with RDB and AOF

**Level:** [L2 · Mid] · about 60 minutes

**Concept.** Two independent mechanisms:

- **RDB snapshots.** Redis forks; the child writes the whole dataset to `dump.rdb` while the parent
  keeps serving (copy-on-write). Triggered by `save` rules (Redis 7 default: `3600 1 300 100 60
  10000`, meaning after 3600 s if at least 1 change, after 300 s if 100, after 60 s if 10,000) or
  by `BGSAVE`. You lose everything since the last snapshot.
- **AOF (append-only file).** Every write is appended to a log; with `appendfsync everysec` (the
  default when AOF is on) you lose at most about a second. Redis 7 keeps it as a directory
  `appendonlydir/` with a base file, incremental files and a manifest, and compacts it with a
  background rewrite.

| Setting | Loses on crash | Good for |
|---|---|---|
| No persistence (`save ""`, `appendonly no`) | everything | a pure cache that can be rebuilt |
| RDB only | minutes of writes | caches that are expensive to warm, sessions you can afford to lose |
| AOF (`everysec`), usually with RDB too | about one second | queues, sessions, anything that must survive a restart |

Two operational facts cause most persistence incidents:

- **Forking needs memory.** In the worst case a write-heavy instance needs up to twice its memory
  during a save. Redis asks for `vm.overcommit_memory = 1` and logs a warning at startup if it is
  not set; without it, `fork` can fail with `Cannot allocate memory`.
- **Failed snapshots stop writes.** With `stop-writes-on-bgsave-error yes` (the default), after a
  failed background save Redis refuses all writes with the `MISCONF` error until a save succeeds.
  That is deliberate: the alternative is silently running without persistence.

When `appendonly yes` is set, Redis loads the **AOF** at startup and ignores `dump.rdb`, which
matters when you restore from an RDB file.

**See it on a real system**

```bash
redis-cli INFO persistence | grep -E '^(rdb_changes_since_last_save|rdb_bgsave_in_progress|rdb_last_save_time|rdb_last_bgsave_status|aof_enabled|aof_last_write_status):'
redis-cli CONFIG GET save
redis-cli CONFIG GET appendonly
sudo ls -lh /var/lib/redis
sudo grep -E 'overcommit|Background saving|MISCONF' /var/log/redis/redis-server.log | tail -n 3
```

```
rdb_changes_since_last_save:48210
rdb_bgsave_in_progress:0
rdb_last_save_time:1791029400
rdb_last_bgsave_status:ok
aof_enabled:0
aof_last_write_status:ok
1) "save"
2) "3600 1 300 100 60 10000"
1) "appendonly"
2) "no"
total 1.1G
-rw-rw---- 1 redis redis 1.1G Oct  3 12:10 dump.rdb
1123:M 03 Oct 2026 09:02:11.400 # WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition. …
1123:M 03 Oct 2026 12:10:00.022 * Background saving started by pid 38804
1123:M 03 Oct 2026 12:10:02.517 * Background saving terminated with success
```

→ RDB only, last snapshot at 12:10 (the epoch `1791029400`), 48,210 changes not yet on disk, and
the overcommit warning at startup that someone should have acted on: add `vm.overcommit_memory = 1`
to a file in `/etc/sysctl.d/` and apply it with `sudo sysctl --system`.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Run `redis-cli BGSAVE` and confirm `rdb_last_bgsave_status:ok` and a new
`rdb_last_save_time`.

**Step 2 — Break it.** Take the data directory away from Redis, then ask for a snapshot and write:

```bash
sudo chown root:root /var/lib/redis          # lab only
redis-cli BGSAVE
sudo tail -n 3 /var/log/redis/redis-server.log
redis-cli SET order:1 paid
```

```
Background saving started
40211:C 03 Oct 2026 12:31:40.120 # Failed opening the temp RDB file temp-40211.rdb (in server root dir /var/lib/redis) for saving: Permission denied
1123:M 03 Oct 2026 12:31:40.219 # Background saving error
(error) MISCONF Redis is configured to save RDB snapshots, but it's currently unable to persist to disk. Commands that may modify the data set are disabled, because this instance is configured to report errors during writes if RDB snapshotting fails (stop-writes-on-bgsave-error option). Please check the Redis logs for details about the RDB error.
```

→ Reads still work; every write fails. In production the cause is usually a full disk
(`Write error saving DB on disk: No space left on device`), wrong ownership after a restore or a
package change, or a failed fork.

**Step 3 — Fix it properly.** Fix the cause, then prove a snapshot works:

```bash
sudo chown redis:redis /var/lib/redis
redis-cli BGSAVE
redis-cli INFO persistence | grep rdb_last_bgsave_status
redis-cli SET order:1 paid
```

```
Background saving started
rdb_last_bgsave_status:ok
OK
```

The popular "fix" found online, `CONFIG SET stop-writes-on-bgsave-error no`, makes the error
disappear and leaves you running without persistence until the next restart loses data. Do not.

**Step 4 — Restore drill, then switch to AOF safely.** Copy `dump.rdb` aside after a successful
`BGSAVE`, run `FLUSHALL` (lab only), stop Redis, put the copy back (owned by `redis:redis`), start
Redis and compare `DBSIZE`. Then enable AOF **at runtime**, which builds the AOF from the current
data, and only afterwards persist the setting:

```bash
redis-cli CONFIG SET appendonly yes
redis-cli INFO persistence | grep -E '^aof_(enabled|rewrite_in_progress):'
redis-cli CONFIG REWRITE
sudo ls /var/lib/redis/appendonlydir
```

```
aof_enabled:1
aof_rewrite_in_progress:0
OK
appendonly.aof.1.base.rdb  appendonly.aof.1.incr.aof  appendonly.aof.manifest
```

→ Editing `appendonly yes` into the file and restarting instead can start Redis from an empty AOF,
which looks exactly like data loss. The runtime switch avoids that trap.

**How it breaks**

| Symptom / error text | First command | Cause and fix |
|---|---|---|
| `MISCONF Redis is configured to save RDB snapshots…` | `tail /var/log/redis/redis-server.log` | disk full, ownership, or fork failure; fix it and `BGSAVE` |
| `Can't save in background: fork: Cannot allocate memory` | `sysctl vm.overcommit_memory`, `free -m` | set overcommit to 1, leave memory headroom |
| All data gone after a restart | `CONFIG GET save`, `CONFIG GET appendonly` | persistence was off: fine for a cache, fatal for a queue |
| A restored `dump.rdb` is ignored | `CONFIG GET appendonly` | Redis loads the AOF when it is enabled |
| Latency spikes every few minutes | `INFO stats` (`latest_fork_usec`) | forking a large dataset; persist on a replica instead |

**Why it matters for troubleshooting.** `MISCONF` looks like an application bug ("writes fail,
reads work") and is really a disk or memory problem on the Redis host. Reading the Redis log first
saves an hour of debugging the wrong layer.

**Next step:** the other way Redis refuses writes: running out of memory.

### maxmemory and eviction

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** `maxmemory` defaults to 0, meaning no limit, so Redis grows until the kernel's OOM
killer (or the container's memory limit, exit code 137) kills it. Always set it, with headroom:
`used_memory` does not include fragmentation, client buffers, the replication backlog or the extra
memory a fork needs. A common starting point is 60–75% of the RAM or container limit available to
Redis.

What happens at the limit is the **eviction policy**:

| Policy | What Redis removes | Use for |
|---|---|---|
| `noeviction` (default) | nothing; writes fail with an `OOM` error | queues, sessions, anything that must not silently disappear |
| `allkeys-lru`, `allkeys-lfu` | any key, least recently / least frequently used | pure caches |
| `volatile-lru`, `volatile-lfu`, `volatile-ttl`, `volatile-random` | only keys that have a TTL | mixed instances where the non-TTL keys must stay |
| `allkeys-random` | any key at random | rarely the right answer |

The two failure modes are opposites. With `noeviction` the application gets errors (loud, safe for
data). With an `allkeys-*` policy the application gets **missing data** (quiet): evicted sessions log
users out, evicted queue entries are jobs that never run.

**See it on a real system**

```bash
redis-cli CONFIG GET maxmemory*
redis-cli INFO stats | grep -E '^(rejected_connections|expired_keys|evicted_keys|keyspace_hits|keyspace_misses|latest_fork_usec):'
```

```
1) "maxmemory"
2) "1610612736"
3) "maxmemory-clients"
4) "0"
5) "maxmemory-eviction-tenacity"
6) "10"
7) "maxmemory-policy"
8) "allkeys-lru"
9) "maxmemory-samples"
10) "5"
rejected_connections:0
expired_keys:4410921
evicted_keys:0
keyspace_hits:91234117
keyspace_misses:2210443
latest_fork_usec:18211
```

→ A 1.5 GB limit with LRU eviction, and no evictions so far. The hit ratio is
91.2 M / (91.2 M + 2.2 M), about 97.6%: the cache is doing its job. A falling hit ratio together
with rising `evicted_keys` means the cache is too small for the working set.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Give the lab instance a tiny limit and the default policy:

```bash
redis-cli CONFIG SET maxmemory 50mb
redis-cli CONFIG SET maxmemory-policy noeviction
```

**Step 2 — Break it.** Fill it and try one more write:

```bash
redis-benchmark -t set -n 2000000 -r 1000000 -d 100 -q
redis-cli SET probe 1
```

```
(error) OOM command not allowed when used memory > 'maxmemory'.
```

→ This is the error a job queue produces when its consumers stop: producers keep pushing until the
limit, and then every write fails.

**Step 3 — Fix it, and see the trade-off.** Switch to `allkeys-lru`, repeat the benchmark and
watch `evicted_keys` climb while writes succeed. Then decide, for each Redis in your inventory,
which failure you prefer: errors or silently missing keys. Restore the lab settings with
`CONFIG SET maxmemory 0` (or your real value). For a container, set the limit inside Redis below
the container's limit:

```bash
docker run -d --name cache --memory 256m redis:7 redis-server --maxmemory 180mb --maxmemory-policy allkeys-lru
```

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| `OOM command not allowed when used memory > 'maxmemory'.` | `INFO memory`, `redis-cli --bigkeys` | a consumer stopped, or the limit is too low |
| Users logged out at random | `evicted_keys` rising | sessions in an instance with an `allkeys-*` policy: separate them |
| Redis restarted, data gone, kernel log shows the OOM killer | `journalctl -k -b` and search for `redis-server` | set `maxmemory` below the RAM or container limit |
| Container restarts with exit code 137 | `docker inspect -f '{{.State.OOMKilled}}' CONTAINER` | `maxmemory` below the container's `--memory` |

**Why it matters for troubleshooting.** Memory incidents are the most common Redis tickets, and the
policy decides whether you get an error or silently lost data. Know which one each of your Redis
instances is configured for before it fills up.

**Next step:** the full list of Redis incidents you will meet, and the first command for each.

### Common Redis incidents

**Level:** [L2 · Mid] · about 30 minutes

**Concept.** Redis incidents repeat. Keep this table next to the playbooks in section 10; the error
word in the application log usually tells you which row you are in.

| Symptom / error text | First command | Usual cause | Fix |
|---|---|---|---|
| `OOM command not allowed…` | `redis-cli INFO memory` | limit reached with `noeviction` | find what grew (`--bigkeys`), restart the stuck consumer, then size it |
| `MISCONF …unable to persist to disk` | Redis log | disk full, permissions, fork failure | persistence topic |
| Data gone after a restart | `journalctl -k -b`, `CONFIG GET save` | OOM kill, or persistence off | `maxmemory`, AOF for queues |
| Latency spikes for everyone | `redis-cli SLOWLOG GET 10` | `KEYS *`, deleting huge keys, big Lua scripts, forks | `SCAN` instead of `KEYS`, `UNLINK` instead of `DEL`, smaller keys |
| `ERR max number of clients reached` | `redis-cli INFO clients`, `redis-cli CLIENT LIST` | a client leaking connections | fix the pool; check the log for the file-descriptor warning about `maxclients` |
| `READONLY You can't write against a read only replica.` | `redis-cli INFO replication` | the app points at a replica, often after a Sentinel failover | Sentinel-aware client or a proxy |
| `MASTERDOWN Link with MASTER is down and replica-serve-stale-data is set to 'no'.` | `INFO replication` (`master_link_status`) | the replica lost its primary | fix the primary or the network |
| `LOADING Redis is loading the dataset in memory` | `INFO persistence` (`loading:1`) | restart of a large instance | wait; plan restarts; keep datasets smaller |
| High CPU, unknown keys, new cron jobs or SSH keys on the host | `redis-cli CONFIG GET dir`, `sudo crontab -l -u redis` | an exposed, unauthenticated Redis was taken over | isolate and rebuild the host, rotate secrets (section 8) |

**High availability in one paragraph.** A Redis replica follows a primary (`replicaof HOST PORT`)
and shows up in `INFO replication`; **Sentinel** (three instances for a quorum) watches the primary,
promotes a replica when it fails and tells clients the new address, so clients must be
Sentinel-aware. **Redis Cluster** shards keys across several primaries. Many teams instead treat
Redis as disposable (cache only) and avoid needing either.

```bash
redis-cli INFO replication | head -n 4
```

```
# Replication
role:master
connected_slaves:1
slave0:ip=192.168.56.22,port=6379,state=online,offset=88412211,lag=0
```

**Hands-on lab (test VM only).** Ask a colleague (or a script) to cause one row of the table on
db1 without telling you which. Find it from the application-side error text and the first command
only, fix it, and write the five-line note. Repeat until you can do any row in 15 minutes.

**Why it matters for troubleshooting.** Redis sits on the request path of almost every page. When it
misbehaves, the whole application looks broken; knowing the nine rows above turns that into a
five-minute fix.

**Next step:** where your databases run: containers, Dokploy and Kubernetes.

---

## 7. Databases in containers and Kubernetes

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts), then Docker Compose ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) Note: [Learn: Docker](30-learn-docker.md) for volumes, networks and the UFW bypass, then [Learn: Kubernetes](31-learn-kubernetes.md) for storage · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Storage (persistent volumes, claims, storage classes); it is CKA study at the same time ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 4) KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Pending Pods and Multi-Attach Volume Errors ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 5) KodeKloud: *Certified Kubernetes Application Developer (CKAD)* — State Persistence, only after CKA ([course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad)) · 6) Video: KodeKloud *What is Helm? | Helm Concepts Explained* (13 min), before you install an operator with Helm ([YouTube](https://www.youtube.com/watch?v=kJscDZfHXrQ)) · 7) Practice: the [Docker playground](https://kodekloud.com/playgrounds/playground-docker), then your kubeadm homelab or the [Kubernetes multi-cluster playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster).

Containers made databases easy to start and easy to lose. The database does not change when it
moves into a container; what changes is where its files live, who may restart it, and how it is
reached. Every topic below is one of those three questions, from a single Docker container to a
Kubernetes operator, and the last topic is the senior decision of where a database should run at
all.

### Databases in Docker

**Level:** [L2 · Mid] · about 60 minutes

**Concept.** Seven rules, each learned from an outage:

1. **The data lives in a volume, never in the container.** Use a named volume (or a bind mount on
   a known disk). The official images declare a `VOLUME`, so without `-v` the data silently goes
   to an anonymous volume that a new container will not reuse.
2. **Initialisation runs once.** `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and the
   scripts in `/docker-entrypoint-initdb.d/` are applied only when the data directory is empty.
   Changing `POSTGRES_PASSWORD` later changes nothing; use `ALTER ROLE`.
3. **Pin the version.** A major version changes the on-disk format. A tag bump from 16 to 17 on the
   same volume does not upgrade anything; it refuses to start. Pin at least the major
   (`postgres:16`), better the minor (`postgres:16.10`), and read the image's release notes before
   a major change (for example, the PostgreSQL 18 images moved the default data directory to a
   version-specific path under `/var/lib/postgresql`).
4. **Give it shared memory.** Docker's default `/dev/shm` is 64 MB; PostgreSQL's parallel queries
   need more and fail with `could not resize shared memory segment`. Set `shm_size`.
5. **Let it shut down.** `docker stop` waits 10 seconds and then kills. A busy database killed
   mid-shutdown runs crash recovery on the next start. Set `stop_grace_period`.
6. **Do not publish the port to the world.** Docker's published ports bypass UFW (see
   [Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
   in the Docker docs). Apps reach the database over the Docker network by service name; publish
   on `127.0.0.1` only if an admin tool on the host needs it.
7. **Back up with database tools.** `docker exec` + `pg_dump`/`mysqldump`, or physical tools; never
   `tar` a running data directory.

Set memory settings (`shared_buffers`, `innodb_buffer_pool_size`, `maxmemory`) explicitly when the
container has a memory limit: a database that sizes itself from the host's RAM inside a 1 GB
container gets OOM-killed.

```yaml
# compose.yaml (lab): PostgreSQL done carefully
services:
  db:
    image: postgres:16.10
    restart: unless-stopped
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: appdb
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"       # admin tools on this host only; apps use the network
    shm_size: 256mb
    stop_grace_period: 60s
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U app -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
  api:
    image: harbor.example.com/shop/api:4f1c2a9
    environment:
      DATABASE_HOST: db               # the service name, resolved by Docker's embedded DNS
      DATABASE_NAME: appdb
    depends_on:
      db:
        condition: service_healthy
volumes:
  pgdata:
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

**See it on a real system**

```bash
docker ps --filter name=db --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker inspect -f '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{println}}{{end}}' shop-db-1
docker exec shop-db-1 df -h /dev/shm
docker exec shop-db-1 pg_dump -U app -Fc appdb > /var/backups/db/shop-appdb-$(date +%F).dump
```

```
NAMES       IMAGE            STATUS                PORTS
shop-db-1   postgres:16.10   Up 3 days (healthy)   127.0.0.1:5432->5432/tcp
volume shop_pgdata -> /var/lib/postgresql/data
Filesystem      Size  Used Avail Use% Mounted on
shm             256M  1.1M  255M   1% /dev/shm
```

→ Pinned image, healthy, published on loopback only, data in the named volume `shop_pgdata`,
256 MB of shared memory. The dump runs inside the container and streams to the host; note there
is no `-t` on `docker exec`, because a TTY would corrupt the binary output. Run the redirection
as a user that can write to the target directory.

**Hands-on lab (Docker playground or app1)**

**Step 1 — Build.** Start the compose file above, connect with
`docker compose exec db psql -U app appdb`, and create and fill a small table.

**Step 2 — Break it, twice.** First remove the `volumes:` line from the `db` service, run
`docker compose up -d`, insert rows, then `docker compose down` and `docker compose up -d` again:
the table is gone. Second, restore the volume line, and change the image to `postgres:17`:

```bash
docker compose up -d && docker compose logs --tail 3 db
```

```
db-1  | PostgreSQL Database directory appears to contain a database; Skipping initialization
db-1  | 2026-10-03 13:40:02.118 UTC [1] FATAL:  database files are incompatible with server
db-1  | 2026-10-03 13:40:02.118 UTC [1] DETAIL:  The data directory was initialized by PostgreSQL version 16, which is not compatible with this version 17.6 (Debian 17.6-1.pgdg13+1).
```

**Step 3 — Fix it.** The "lost" table from the first break is in a dangling anonymous volume:
`docker volume ls -f dangling=true`, then look inside a candidate with
`docker run --rm -v VOLUME:/v alpine cat /v/PG_VERSION`. Copy it into the named volume with both
containers stopped, or dump it from a temporary container that mounts it. For the second break,
set the tag back to `postgres:16.10` and the server starts again. A real major upgrade is
deliberate: dump from the 16 container and restore into a new 17 container with a **new** volume,
or use `pg_upgrade` (section 2, major version upgrades), and keep the old volume until verified.

**How it breaks**

| Symptom / error text | First command | Fix |
|---|---|---|
| `FATAL:  database files are incompatible with server` | `docker inspect -f '{{.Config.Image}}' CONTAINER` | pin the tag; upgrade majors deliberately |
| `could not resize shared memory segment "/PostgreSQL.…" to … bytes: No space left on device` | `docker exec CONTAINER df -h /dev/shm` | `shm_size` |
| Data gone after `down` and `up` | `docker volume ls -f dangling=true` | named volume |
| `password authentication failed` after changing `POSTGRES_PASSWORD` | the logs show `Skipping initialization` | `ALTER ROLE app PASSWORD …` inside the database |
| `database system was interrupted; last known up at …` after every restart | `docker inspect -f '{{.State.ExitCode}}' CONTAINER` (137 = killed) | `stop_grace_period`, a memory limit that fits |
| Port 5432 reachable from outside despite UFW | `sudo ss -ltnp`, then a scan from another host | publish on `127.0.0.1` or not at all |

**Why it matters for troubleshooting.** Container database incidents are rarely database problems.
They are volume, tag, shared-memory, shutdown or exposure problems, and each one has a precise
first command.

**Next step:** the same database inside Dokploy, where Swarm adds its own rules.

### Databases on Dokploy and Swarm

**Level:** [L2 · Mid] · about 45 minutes

**Concept.** Dokploy can create PostgreSQL, MySQL, MariaDB, MongoDB and Redis for you. Each one is a
Docker **Swarm service** with a named volume for its data, attached to `dokploy-network`;
applications in Dokploy reach it by the internal host name and connection URL that Dokploy shows on
the database's page. Three Swarm facts matter for operations:

- **"External port" publishes through Swarm's routing mesh**, on every node's IP and through
  Docker's own iptables rules, so UFW does not stop it. Leave it off. For admin access use
  `docker exec` into the task's container, or a VPN.
- **Volumes are local to a node.** On a multi-node Dokploy setup, a database service without a
  placement constraint can be rescheduled to another node, where it finds an empty volume and
  starts as a fresh, empty database. Pin database services to their node, in Dokploy's own service
  settings so that the next deploy does not overwrite it.
- **Dokploy's own state is a database too.** `dokploy-postgres` and `dokploy-redis` hold Dokploy's
  configuration; include them in your backups.

Dokploy can schedule backups of its PostgreSQL, MySQL, MariaDB and MongoDB databases to an
S3-compatible destination ([Dokploy docs](https://docs.dokploy.com/docs/core)). Turn that on, and
then apply section 4 anyway: restore one into a scratch database on a schedule.

**See it on a real system** (on the Dokploy host)

```bash
docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}\t{{.Ports}}'
docker service ps shop-db-x7k2pq --format 'table {{.Node}}\t{{.CurrentState}}\t{{.Error}}'
docker service inspect shop-db-x7k2pq --format '{{json .Spec.TaskTemplate.Placement}}'
```

```
NAME                REPLICAS   IMAGE                                 PORTS
dokploy             1/1        dokploy/dokploy:latest                *:3000->3000/tcp
dokploy-postgres    1/1        postgres:16
dokploy-redis       1/1        redis:7
shop-api-4m9tqz     6/6        harbor.example.com/shop/api:4f1c2a9
shop-db-x7k2pq      1/1        postgres:16                           *:15432->5432/tcp
shop-redis-p2l8sd   1/1        redis:7
NODE      CURRENT STATE          ERROR
dok1      Running 3 days ago
{}
```

→ Two findings. `shop-db` has an external port (15432) published on every node through the
routing mesh: anyone who can reach the host can reach the database, whatever UFW says. And its
placement is empty (`{}`): harmless on one node, an empty-database incident waiting to happen on
two. For a quick shell inside it:
`docker exec -it $(docker ps -q -f name=shop-db-x7k2pq) psql -U postgres`.

**Hands-on lab (test Dokploy instance only)**

**Step 1 — Build.** Create a PostgreSQL database in Dokploy and an app that uses its internal
connection URL. Confirm from the app's container: `getent ahosts` on the internal host name.

**Step 2 — Break it.** Set an external port, then from another machine run
`nc -vz DOKPLOY_HOST 15432` while `sudo ufw status` on the host shows no rule allowing it. The
connection succeeds.

**Step 3 — Fix it.** Remove the external port and confirm the scan now fails. If remote access is
truly required, filter it in the `DOCKER-USER` chain (see "Docker bypasses UFW" in
[Security & DevSecOps](37-learn-security-devsecops.md) and "DOCKER-USER, UFW and the firewall" in
[Learn: Docker](30-learn-docker.md)), not in UFW.

**Step 4 — Back up and restore.** Configure a Dokploy backup to an S3-compatible destination (a
MinIO container works in the lab), run it once, download the file and restore it into a scratch
database with the commands from section 4.

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| App cannot resolve the database host | `docker network inspect dokploy-network` (is the app attached?) | attach the app to `dokploy-network`, use the internal host name |
| Database suddenly empty after a node change | `docker service ps SERVICE` (which node?) | placement constraint; the old node still has the volume |
| Service stuck with `no suitable node` | `docker node ls` | the pinned node is drained or down |
| Database reachable from the internet | `docker service ls` (PORTS column) | remove the external port |

**Why it matters for troubleshooting.** On Dokploy the database is "just another service" in the UI,
which makes its two special needs (one fixed node, no public port) easy to miss until the day they
matter.

**Next step:** databases on your CKA homelab: StatefulSets and persistent volumes.

### StatefulSets and volumes

**Level:** [L3 · Senior] · about 75 minutes

**Concept.** A Deployment's pods are interchangeable; a database's are not. A **StatefulSet** gives
each replica a stable name (`pg-0`), a stable DNS name through a **headless Service**
(`pg-0.pg.db.svc.cluster.local`) and its own **PersistentVolumeClaim** from `volumeClaimTemplates`
(`data-pg-0`), and starts and stops replicas in order. Key facts:

- **`replicas: 3` is not replication.** It creates three independent, empty databases. Replication,
  failover and backups need PostgreSQL's own mechanisms, which is what operators automate (next
  topic).
- **Claims outlive pods.** Deleting a pod or scaling down keeps the PVC (the
  `persistentVolumeClaimRetentionPolicy` defaults to Retain). Deleting the PVC deletes the data
  when the StorageClass `reclaimPolicy` is `Delete`, the default for dynamic provisioning.
- **Storage decides availability.** With node-local storage (local-path, local PVs) the pod is
  tied to one node: if the node dies, the pod cannot start elsewhere. Network storage (Longhorn,
  Ceph, cloud volumes) can move, at a performance cost. NFS is a poor fit for databases.
- **Probes must respect crash recovery.** A liveness probe that fails during a long recovery
  restarts the database in the middle of it, forever. Use a `startupProbe` with a generous budget.
- **Memory limits apply to the whole process tree.** `shared_buffers` plus connections must fit, or
  the pod is OOMKilled.

```yaml
# pg-statefulset.yaml (homelab, single instance: NOT high availability)
apiVersion: v1
kind: Service
metadata:
  name: pg
  namespace: db
spec:
  clusterIP: None                  # headless: gives pg-0.pg.db.svc.cluster.local
  selector:
    app: pg
  ports:
    - name: postgres
      port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: pg
  namespace: db
spec:
  serviceName: pg
  replicas: 1
  selector:
    matchLabels:
      app: pg
  template:
    metadata:
      labels:
        app: pg
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: postgres
          image: postgres:16.10
          env:
            - name: POSTGRES_DB
              value: appdb
            - name: POSTGRES_USER
              value: app
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pg-secret
                  key: password
            - name: PGDATA                       # a subdirectory: a fresh volume may contain lost+found
              value: /var/lib/postgresql/data/pgdata
          ports:
            - name: postgres
              containerPort: 5432
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              memory: 1Gi
          startupProbe:
            exec:
              command: ["pg_isready", "-h", "127.0.0.1", "-U", "app", "-d", "appdb"]
            periodSeconds: 10
            failureThreshold: 60                 # up to 10 minutes for crash recovery
          readinessProbe:
            exec:
              command: ["pg_isready", "-h", "127.0.0.1", "-U", "app", "-d", "appdb"]
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["pg_isready", "-h", "127.0.0.1", "-U", "app", "-d", "appdb"]
            periodSeconds: 20
            failureThreshold: 6
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
            - name: dshm
              mountPath: /dev/shm
      volumes:
        - name: dshm
          emptyDir:
            medium: Memory
            sizeLimit: 256Mi
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path
        resources:
          requests:
            storage: 10Gi
```

**See it on a real system**

```bash
kubectl create namespace db
kubectl -n db create secret generic pg-secret --from-literal=password='LabPass-123'
kubectl apply -f pg-statefulset.yaml
kubectl -n db get sts,pod,pvc -o wide
```

```
NAME                  READY   AGE   CONTAINERS   IMAGES
statefulset.apps/pg   1/1     6m    postgres     postgres:16.10

NAME       READY   STATUS    RESTARTS   AGE   IP            NODE     NOMINATED NODE   READINESS GATES
pod/pg-0   1/1     Running   0          6m    10.244.2.17   node02   <none>           <none>

NAME                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE   VOLUMEMODE
persistentvolumeclaim/data-pg-0   Bound    pvc-5b6f0c1e-2d4a-4e8b-9c11-7f3a2e9d1b44   10Gi       RWO            local-path     <unset>                 6m    Filesystem
```

→ One pod on `node02` with its claim bound. Because the StorageClass is `local-path`, the data
physically lives on `node02`'s disk, and this pod can only ever run there.

**Hands-on lab (kubeadm homelab or the Kubernetes playground)**

**Step 1 — Build.** Apply the manifest, create a table through `kubectl -n db exec -it pg-0 --
psql -U app appdb`, then delete the pod: `kubectl -n db delete pod pg-0`. It comes back with the
same name and the same claim, and the table is still there.

**Step 2 — Break it.** Drain the node that holds the data, as you would for a kernel upgrade:

```bash
kubectl drain node02 --ignore-daemonsets --delete-emptydir-data
kubectl -n db describe pod pg-0 | tail -n 3
```

```
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  41s   default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }, 1 node(s) had volume node affinity conflict, 1 node(s) were unschedulable. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.
```

→ The pod is `Pending`: its volume exists only on `node02`, which is now unschedulable. A routine
node drain has become a database outage. That is the core reason databases on Kubernetes need
either replication across nodes or storage that can move.

**Step 3 — Fix it.** `kubectl uncordon node02` and the pod starts again. The durable fix is
architectural: an operator running a replica on another node (next topic), a PodDisruptionBudget
so drains wait for a switchover, or network storage.

**How it breaks**

| Symptom | First command | Where to go |
|---|---|---|
| Pod `Pending`, `volume node affinity conflict` | `kubectl describe pod` | the node holding the volume is down or cordoned |
| `initdb: error: directory "/var/lib/postgresql/data" exists but is not empty` | the volume's contents (`lost+found`) | set `PGDATA` to a subdirectory |
| `CrashLoopBackOff` during crash recovery, `Liveness probe failed` | `kubectl describe pod` events | a `startupProbe` with a long budget |
| `OOMKilled` in `kubectl get pod -o wide` or `describe` | `kubectl top pod`, memory settings | fit `shared_buffers` and connections inside the limit |
| `Multi-Attach error for volume` after a node failure | `kubectl get volumeattachment` | RWO volume still attached to the dead node: [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** StatefulSet incidents are storage incidents. If you can say
where a pod's data physically lives, you can predict what every drain, node failure and upgrade will
do to it.

**Next step:** let an operator run PostgreSQL properly on Kubernetes.

### Operators and CloudNativePG

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 60 minutes

**Concept.** An **operator** is a controller that runs a database the way an experienced DBA would:
it creates the primary and replicas, wires up streaming replication, fails over, takes backups,
rotates certificates and performs rolling minor upgrades, all driven by one custom resource.
**CloudNativePG** (CNPG, a CNCF project) is the most widely used PostgreSQL operator; alternatives
include the Zalando operator (Patroni-based), Crunchy PGO and the Percona operators, and for MySQL
the MySQL Operator (InnoDB Cluster) or the MariaDB operator.

CNPG does not use Patroni or a StatefulSet: the operator manages the pods and PVCs itself and uses
the Kubernetes API as its source of truth. It creates three Services: `CLUSTER-rw` (always the
primary), `CLUSTER-ro` (replicas only) and `CLUSTER-r` (any instance), and a secret `CLUSTER-app`
with the application's credentials and connection URI. Install the operator with its Helm chart or
release manifest, following the CloudNativePG documentation for your version; backups to an object
store are configured per cluster (current releases do this through the Barman Cloud plugin).

```yaml
# pg-main.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: pg-main
  namespace: db
spec:
  instances: 3
  imageName: ghcr.io/cloudnative-pg/postgresql:16.10
  storage:
    storageClass: local-path
    size: 20Gi
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: 512MB
  bootstrap:
    initdb:
      database: appdb
      owner: app
  resources:
    requests:
      cpu: 500m
      memory: 2Gi
    limits:
      memory: 2Gi
  affinity:
    enablePodAntiAffinity: true
    topologyKey: kubernetes.io/hostname       # spread instances across nodes
    podAntiAffinityType: required             # the default, "preferred", may still co-locate them
```

**See it on a real system**

```bash
kubectl apply -f pg-main.yaml
kubectl -n db get cluster
kubectl -n db get pods -L cnpg.io/instanceRole
kubectl -n db get svc
```

```
NAME      AGE   INSTANCES   READY   STATUS                     PRIMARY
pg-main   14m   3           3       Cluster in healthy state   pg-main-1

NAME        READY   STATUS    RESTARTS   AGE   INSTANCEROLE
pg-main-1   1/1     Running   0          14m   primary
pg-main-2   1/1     Running   0          13m   replica
pg-main-3   1/1     Running   0          12m   replica

NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
pg-main-r    ClusterIP   10.96.142.17    <none>        5432/TCP   14m
pg-main-ro   ClusterIP   10.96.88.203    <none>        5432/TCP   14m
pg-main-rw   ClusterIP   10.96.201.44    <none>        5432/TCP   14m
```

→ Three instances on three nodes, one primary. Applications connect to
`pg-main-rw.db.svc.cluster.local:5432` and never need to know which pod is the primary. With the
`cnpg` kubectl plugin, `kubectl cnpg status pg-main -n db` shows replication lag, WAL archiving and
backups in one view.

**Hands-on lab (homelab with three worker nodes)**

**Step 1 — Build.** Install the operator, apply `pg-main.yaml`, and point a test app (or a
`kubectl run` psql pod) at the `-rw` Service using the `pg-main-app` secret.

**Step 2 — Break it.** Kill the primary while a client loop writes once a second:

```bash
kubectl -n db delete pod pg-main-1
kubectl -n db get cluster -w
```

```
NAME      AGE   INSTANCES   READY   STATUS                     PRIMARY
pg-main   31m   3           2       Failing over               pg-main-1
pg-main   31m   3           2       Failing over               pg-main-2
pg-main   32m   3           3       Cluster in healthy state   pg-main-2
```

→ The operator promoted `pg-main-2`, moved the `-rw` Service to it and recreated `pg-main-1` as a
replica. Count how many writes your client loop lost or retried: that is your observed RTO.

**Step 3 — Fix and verify.** Nothing to fix by hand, which is the point. Verify instead: run
`kubectl drain` on the node with the new primary and watch the operator switch over before the pod
is evicted, then restore a backup into a new cluster (the operator bootstraps a cluster from a
backup) and check the row counts. An operator automates backups; it does not exempt you from
testing restores.

**How it breaks**

| Symptom | First command | Usual cause |
|---|---|---|
| Cluster stuck in `Setting up primary` or `Creating a new replica` | `kubectl -n db describe cluster pg-main`, operator logs | PVCs pending (storage), image pull errors |
| Writes fail for 10–30 s during failover | client logs | expected; apps must retry and reconnect |
| WAL archiving failing in `kubectl cnpg status` | object store credentials, network | backups and PITR silently stop |
| All instances on one node | `kubectl -n db get pods -o wide` | anti-affinity left at `preferred` with too few nodes (with `required`, the extra instances stay `Pending` instead) |

**Why it matters for troubleshooting.** With an operator you troubleshoot two layers: the operator's
view (the `Cluster` status) and PostgreSQL's view (everything from sections 2 and 5, inside the
pods). Start with the first, confirm with the second.

**Next step:** step back and decide where each database should run.

### VM, container, Kubernetes or managed

**Level:** [L4 · Lead/SRE] · about 30 minutes

**Concept.** "Can we run the database on Kubernetes?" has the answer "yes"; the senior question is
"should this team run this database there?" The options:

| Option | Good when | Watch out for | Who carries the pager |
|---|---|---|---|
| VM or bare metal, distribution packages | a few important databases, steady load, a team fluent in Linux | you build HA, backups, patching and monitoring yourself | you |
| Docker or Dokploy | small apps, staging, single-node platforms like your Dokploy host | volumes, tag pinning, exposure, node-local data, backups | you |
| Kubernetes with an operator (CloudNativePG) | many databases, a platform team, GitOps, good storage | storage performance, operator and cluster upgrades become database events, two layers to debug | the platform team |
| Managed service (RDS, Aurora) | AWS workloads, a small team, Multi-AZ and PITR without building them | cost, no superuser, extension and version limits, maintenance windows | AWS for the platform, you for everything above it |

Many experienced teams keep their important databases on VMs or managed services, for reasons
that are operational rather than ideological: storage is the hardest part of an on-prem
Kubernetes cluster; cluster upgrades and node drains become database events; a 3 a.m. incident
needs someone fluent in both PostgreSQL and Kubernetes; and the blast radius of a cluster problem
now includes the data. Teams that run databases on Kubernetes successfully usually have a platform
team, an operator they know well, local NVMe with operator-managed replication or solid network
storage, and restore tests like any other team.

For your stack today, a reasonable position is: Dokploy-managed databases for small apps with
Dokploy backups plus restore tests; VMs (or RDS on AWS) for the databases whose loss would hurt;
CloudNativePG on the homelab to learn the operator model. Write the decision down as an ADR (see
[Senior architecture](39-learn-senior-architecture.md)) so the next engineer knows why.

**Hands-on lab.** For each database in your real inventory (Dokploy, VMs, anything on the old
Apache server), fill in one row: where it runs, RPO and RTO it needs, current backup and restore
test, who is paged. Mark every row where the "where" does not fit the "needs".

**Why it matters for troubleshooting.** Most painful database incidents are decided long before
they happen, by where the database was put and what that platform does to it during routine work.

**Next step:** who and what may reach those databases: security and access.

---

## 8. Security and access

> 📚 **Study path:** 1) Note: [Security & DevSecOps](37-learn-security-devsecops.md) — "Docker bypasses UFW", TLS and PKI, and secrets management (a refresher, so it comes first) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure Packet Filtering (Firewall) ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 3) KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)), then LFCS — Work With SSL Certificates ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 4) Read: the [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) for PostgreSQL and MySQL, and the SQL injection material on [OWASP](https://owasp.org/) · 5) Practice: scan your own lab database hosts from app1 with nmap, then the labs below.

Databases hold the data attackers want, and a few default-looking choices hand it over: a port
open to the world, an application connecting as superuser, a password in a Git repository, or a
"TLS" connection that never checks who is on the other end. This section closes those four doors.
The general skills (firewalls, PKI, secrets) live in [Security & DevSecOps](37-learn-security-devsecops.md);
here they are applied to PostgreSQL, MySQL and Redis.

### Network exposure

**Level:** [L2 · Mid] · about 30 minutes

**Concept.** A database port is never reachable from the internet, and inside the network only
from the hosts that need it. Real attacks on exposed databases are automated and fast:

- **Redis without a password:** attackers use `CONFIG SET dir` and `SAVE` to write their SSH key or
  a cron job onto the host, then install crypto-miners.
- **PostgreSQL with a guessable superuser password:** `COPY ... TO PROGRAM` runs shell commands as
  the `postgres` OS user; miners again.
- **MongoDB, Elasticsearch, MySQL:** data copied and deleted, with a ransom note left in a table.

Defence is layered, so that one mistake is not enough:

| Layer | PostgreSQL / MySQL / Redis setting | Check |
|---|---|---|
| Listen address | `listen_addresses`, `bind-address`, `bind`: loopback plus the private IP, never `0.0.0.0` "for now" | `sudo ss -ltnp` |
| Host firewall | UFW allowlist per app host; default deny incoming | `sudo ufw status numbered` |
| Network | databases in their own subnet or VLAN; on AWS, a security group that only admits the app's security group | a scan from another subnet |
| Docker | publish on `127.0.0.1` or not at all; published ports bypass UFW | see "Docker bypasses UFW" in module 37 |
| Exporters | 9187, 9104, 9121 open only to the Prometheus host; they reveal a lot | `sudo ss -ltnp` |
| Admin access | VPN, bastion or an SSH tunnel, not an open port | — |

An SSH tunnel gives an administrator a database connection without opening anything:
`ssh -L 15432:127.0.0.1:5432 admin@db1.example.internal`, then
`psql -h 127.0.0.1 -p 15432 -U app appdb` on the laptop.

**See it on a real system**

```bash
sudo ss -ltnp | grep -E ':(5432|3306|6379|9187|9104|9121)\b'
sudo ufw status numbered
# from app1, and again from a host in another network
nmap -Pn -p 3306,5432,6379,9104,9121,9187 db1.example.internal
```

```
LISTEN 0      200       192.0.2.21:5432      0.0.0.0:*    users:(("postgres",pid=812,fd=7))
LISTEN 0      200        127.0.0.1:5432      0.0.0.0:*    users:(("postgres",pid=812,fd=6))
LISTEN 0      151          0.0.0.0:3306      0.0.0.0:*    users:(("mysqld",pid=901,fd=24))
LISTEN 0      511        127.0.0.1:6379      0.0.0.0:*    users:(("redis-server",pid=644,fd=6))
LISTEN 0      4096                *:9187            *:*    users:(("prometheus-post",pid=1188,fd=3))
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    192.0.2.0/24
[ 2] 5432/tcp                   ALLOW IN    192.0.2.50
[ 3] 5432/tcp                   ALLOW IN    192.0.2.51
[ 4] 9187/tcp                   ALLOW IN    192.0.2.60

Nmap scan report for db1.example.internal (192.0.2.21)
PORT     STATE    SERVICE
3306/tcp filtered mysql
5432/tcp open     postgresql
6379/tcp filtered redis
9104/tcp filtered unknown
9121/tcp filtered unknown
9187/tcp filtered unknown
```

→ From app1 only PostgreSQL is reachable, as intended. But MySQL listens on `0.0.0.0` and only
UFW stands between it and every other host: one `ufw disable` during a debugging session and it is
exposed. Set `bind-address` to the private IP so that two layers must fail, not one.

**Hands-on lab (test VMs only)**

**Step 1 — Build.** Add one UFW rule per app host for each database port, for example
`sudo ufw allow from 192.168.56.11 to any port 5432 proto tcp comment 'app1 to PostgreSQL'`, and
confirm with nmap from app1 (open) and from your workstation (filtered).

**Step 2 — Break it.** On app1, run `docker run -d --name exposed -p 6380:6379 redis:7` and add
`sudo ufw deny 6380/tcp`. From db1, `redis-cli -h 192.168.56.11 -p 6380 PING` answers `PONG`
anyway: Docker's DNAT rules run before UFW's. Then see why the application must never be a
superuser: as `postgres`, `COPY (SELECT 1) TO PROGRAM 'id > /tmp/proof';` runs a shell command on
db1; as `app`:

```
ERROR:  permission denied to COPY to or from an external program
DETAIL:  Only roles with privileges of the "pg_execute_server_program" role may COPY to or from an external program.
HINT:  Anyone can COPY to stdout or from stdin. psql's \copy command also works for anyone.
```

**Step 3 — Fix it.** `docker rm -f exposed`; if a container must publish, use `-p 127.0.0.1:6380:6379`.
Set MySQL's `bind-address` to the private IP and restart. Delete `/tmp/proof` on db1.

**How it breaks**

| Finding | First command | Fix |
|---|---|---|
| Database port open from the internet | a scan from outside your network | listen address, firewall, security group |
| Port open despite `ufw deny` | `sudo iptables -t nat -L DOCKER -n` | Docker publishing: `127.0.0.1` or `DOCKER-USER` rules |
| Unknown cron jobs or SSH keys on a Redis host | `sudo crontab -l -u redis`, `CONFIG GET dir` | isolate, rebuild, rotate every secret on the host |
| `pg_hba.conf` has `trust` on a `host` line | `SELECT * FROM pg_hba_file_rules WHERE auth_method = 'trust';` | `scram-sha-256` |

**Why it matters for troubleshooting.** When a database host misbehaves in strange ways (high CPU
from an unknown process, odd new tables, changed configuration), exposure is the first hypothesis
to rule out, before tuning anything.

**Next step:** once a connection is allowed, what may it do?

### Roles, least privilege and secrets

**Level:** [L2 · Mid] → [L3 · Senior] · about 45 minutes

**Concept.** Give each kind of client its own identity with only the rights it needs:

| Identity | Rights | Why separate |
|---|---|---|
| Owner / migrations | owns the schema, runs DDL | used only by the migration job in CI (section 11) |
| Application runtime | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | a SQL injection cannot drop tables or run programs |
| Read-only | `SELECT` | reports, analysts, support tools |
| Monitoring | `pg_monitor` role; MySQL `PROCESS, REPLICATION CLIENT, SELECT` | exporters see statistics, not data changes |
| Backup | `REPLICATION` for base backups, or read access for dumps | stolen backup credentials cannot write |
| Humans | personal accounts, read-only by default | audit trail; no shared `postgres` password |

Never let an application connect as a superuser (`postgres`, MySQL `root`): superusers can run
programs, read server files and change configuration. PostgreSQL 15+ already stopped letting every
role create objects in the `public` schema; PostgreSQL 14+ added the predefined roles
`pg_read_all_data` and `pg_write_all_data`.

```bash
# In the lab, app already owns appdb and plays the "owner / migrations" identity
sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
CREATE ROLE app_rw LOGIN PASSWORD 'LabRw-123' CONNECTION LIMIT 100;
CREATE ROLE app_ro LOGIN PASSWORD 'LabRo-123';
CREATE ROLE monitoring LOGIN PASSWORD 'LabMon-123' IN ROLE pg_monitor;
\c appdb
REVOKE ALL ON DATABASE appdb FROM PUBLIC;
GRANT CONNECT ON DATABASE appdb TO app_rw, app_ro, monitoring;
GRANT USAGE ON SCHEMA public TO app_rw, app_ro;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;
-- tables that migrations (role app) create later get the same grants automatically
ALTER DEFAULT PRIVILEGES FOR ROLE app IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE app IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE app IN SCHEMA public GRANT SELECT ON TABLES TO app_ro;
SQL
```

The MySQL equivalent, with the host part of each account doing `pg_hba.conf`'s job:

```sql
CREATE USER 'app_rw'@'192.0.2.%' IDENTIFIED BY 'CHANGE_ME_RW';
GRANT SELECT, INSERT, UPDATE, DELETE ON appdb.* TO 'app_rw'@'192.0.2.%';
CREATE USER 'app_migrate'@'192.0.2.70' IDENTIFIED BY 'CHANGE_ME_MIGRATE';
GRANT ALL PRIVILEGES ON appdb.* TO 'app_migrate'@'192.0.2.70';
```

**Secrets.** Database passwords belong in GitLab masked and protected CI/CD variables, Docker or
Swarm secrets, Kubernetes Secrets (base64 is not encryption: enable encryption at rest) or a vault,
never in Git. Client files must be private: `~/.pgpass` and `~/.my.cnf` with mode 0600. Three
details that leak passwords in practice:

- `ALTER ROLE ... PASSWORD 'plaintext'` is written to the server log when `log_statement` is `ddl`
  or `all`, and to your `~/.psql_history`. Use psql's `\password app_rw`, which sends only the
  SCRAM hash.
- A password in a connection URL must be percent-encoded if it contains `@`, `:`, `/` or `%`, or
  the driver parses a different host or user; long random passwords without those characters avoid
  the problem.
- `mysql -pSECRET` puts the password in the process list and shell history; use a client config
  file or `mysql_config_editor`.

**Rotation without downtime.** Changing a role's password does not disconnect existing sessions,
so a rotation "works" until the pool reconnects at 3 a.m. Rotate deliberately: in MySQL 8.0.14+,
`ALTER USER 'app_rw'@'192.0.2.%' IDENTIFIED BY 'NEW' RETAIN CURRENT PASSWORD;` accepts both
passwords until you run `ALTER USER 'app_rw'@'192.0.2.%' DISCARD OLD PASSWORD;`. In PostgreSQL, use
two login roles that are members of one group role holding the grants, and switch the application
from one to the other.

**Auditing.** `log_connections = on` and `log_disconnections = on` record who connected from
where (also invaluable in connection storms). For statement-level audit use the **pgaudit**
extension (package `postgresql-16-pgaudit`, loaded through `shared_preload_libraries`, for example
`pgaudit.log = 'ddl, role'`). MySQL's general query log is far too heavy for auditing; use an audit
plugin.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Run the SQL above, then connect as `app_rw` from app1.

**Step 2 — Break it.** As `app_rw`, try `DROP TABLE orders;` and `CREATE TABLE x (id int);`. Then,
as `postgres`, set `log_statement = 'ddl'` (reload) and run `ALTER ROLE app_ro PASSWORD 'Visible-123';`,
and find the plaintext password in `/var/log/postgresql/postgresql-16-main.log`.

```
ERROR:  must be owner of table orders
ERROR:  permission denied for schema public
LOG:  statement: ALTER ROLE app_ro PASSWORD 'Visible-123';
```

**Step 3 — Fix it.** The first two errors are the design working. For the third, set the password
again with `\password app_ro` and look at the log: it now shows a `SCRAM-SHA-256$4096:…` hash.
Rotate the leaked password, and treat database logs as sensitive files.

**How it breaks**

| Symptom / error text | Cause | Fix |
|---|---|---|
| `permission denied for table orders` after a migration | new table, no grants | `ALTER DEFAULT PRIVILEGES FOR ROLE app` (as above) |
| `permission denied for schema public` | PostgreSQL 15+ default | `GRANT USAGE` (and `CREATE` only to the owner) |
| App works until the nightly reconnect, then `password authentication failed` | a password changed while sessions stayed open | rotate with two roles or dual passwords |
| `too many connections for role "app_rw"` | `CONNECTION LIMIT` reached | a pool leak, or raise the per-role limit deliberately |

**Why it matters for troubleshooting.** Permission errors after a deploy are one of the most common
"database" tickets, and the error text names the object and the missing right. Least privilege
turns a would-be breach into an error message.

**Next step:** encrypt the connection, and make it verify who it is talking to.

### TLS for database connections

**Level:** [L3 · Senior] · about 60 minutes

**Concept.** TLS on a database connection does two jobs: encryption (nobody on the network reads the
queries) and **server authentication** (the client is talking to the real database, not to
something in between). The second job only happens when the client verifies the certificate.

- **PostgreSQL.** Ubuntu enables `ssl = on` with a self-signed "snakeoil" certificate, so traffic
  is encrypted, but no client can verify it. Replace it with a certificate from your private CA
  (the same CA approach as Harbor in [Security & DevSecOps](37-learn-security-devsecops.md),
  "Distributing trust"), make remote `pg_hba.conf` lines `hostssl`, and have clients use
  `sslmode=verify-full` with the CA (`sslrootcert=FILE`, or `sslrootcert=system` to use the OS trust
  store, new in PostgreSQL 16). `sslmode=require` encrypts but does not check the certificate, unless a
  root certificate file exists, in which case it behaves like `verify-ca`.
- **MySQL 8.** TLS is on by default with auto-generated self-signed certificates. Point `ssl_ca`,
  `ssl_cert` and `ssl_key` at your own files, reload them online with `ALTER INSTANCE RELOAD TLS`,
  set `require_secure_transport = ON`, and use `--ssl-mode=VERIFY_IDENTITY` on clients.
- **Redis.** Supports TLS when built with it (`tls-port`, `tls-cert-file`); many teams keep Redis
  on a private network with ACLs instead. Decide explicitly.

PostgreSQL reloads its SSL configuration without a restart. Keep the key readable only by
`postgres` (mode 0600), and monitor certificate expiry like any other certificate.

```
# /etc/postgresql/16/main/conf.d/70-tls.conf
ssl = on
ssl_cert_file = '/etc/postgresql/tls/db1.example.internal.crt'
ssl_key_file = '/etc/postgresql/tls/db1.example.internal.key'
ssl_min_protocol_version = 'TLSv1.2'
```

**See it on a real system**

```bash
psql "host=db1.example.internal dbname=appdb user=app sslmode=verify-full sslrootcert=/usr/local/share/ca-certificates/example-internal-ca.crt" \
  -c "SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid();"
sudo mysql -e "SHOW SESSION STATUS LIKE 'Ssl_version'; SHOW GLOBAL VARIABLES LIKE 'require_secure_transport';"
```

```
 ssl | version |         cipher
-----+---------+------------------------
 t   | TLSv1.3 | TLS_AES_256_GCM_SHA384
(1 row)

+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| Ssl_version   |       |
+---------------+-------+
+--------------------------+-------+
| Variable_name            | Value |
+--------------------------+-------+
| require_secure_transport | OFF   |
+--------------------------+-------+
```

→ The PostgreSQL session is TLS 1.3 **and** verified against the CA and the host name. The MySQL
check ran over the local Unix socket (`sudo mysql`), which needs no TLS, so `Ssl_version` is empty;
check a TCP connection from the app host instead. `require_secure_transport` is off, so
unencrypted TCP connections are still accepted.

**Hands-on lab (test VMs only)**

**Step 1 — Build.** With your lab CA (module 37), issue a certificate for `db1.example.internal`
with that name in the subject alternative names. Install it with the conf file above, copy the
key with `sudo install -o postgres -g postgres -m 0600`, change the app1 line in `pg_hba.conf` to
`hostssl`, reload, and connect from app1 with `sslmode=verify-full`.

**Step 2 — Break it.** Connect by IP address instead of name, then with a CA file that is not
yours:

```
psql: error: connection to server at "192.168.56.21", port 5432 failed: server certificate for "db1.example.internal" does not match host name "192.168.56.21"
psql: error: connection to server at "db1.example.internal" (192.168.56.21), port 5432 failed: SSL error: certificate verify failed
```

→ Both refusals are verification doing its job: the first protects against connecting to the
wrong server, the second against a certificate from an unknown issuer.

**Step 3 — Fix it.** Use the name that is in the certificate (or add the IP as a SAN if clients
must use it), and distribute the right CA file to every client: application containers, CI jobs,
admin laptops.

**How it breaks**

| Error text | Cause | Fix |
|---|---|---|
| `server certificate for "…" does not match host name "…"` | client uses a name or IP not in the SAN | connect by the certificate's name, or reissue |
| `SSL error: certificate verify failed` | client does not trust the issuing CA | distribute the CA file; check `sslrootcert` |
| `root certificate file "/home/ops/.postgresql/root.crt" does not exist` | `verify-full` without `sslrootcert` | pass `sslrootcert=FILE` or `sslrootcert=system` |
| `no pg_hba.conf entry for host "…", user "app", database "appdb", no encryption` | a `hostssl` rule and a client without TLS | enable TLS in the client (`sslmode`) |
| Every connection fails on the morning a certificate expires | expiry | monitor expiry, automate renewal |

**Why it matters for troubleshooting.** TLS errors from database clients are as precise as the ones
from browsers. Reading which check failed (name, issuer, expiry, or "no encryption") tells you
which side to fix.

**Next step:** watch all of this continuously: monitoring and alerts.

---

## 9. Monitoring databases

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals (including Node Exporter), PromQL, then Alerting ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) Note: [Learn: Performance & observability](32-learn-performance-observability.md) for the Prometheus and Grafana stack and alert design · 3) KodeKloud: *Fundamentals of SRE* — Incident Management: Designing Effective Alerts ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* (68 min), only if ServiceMonitors and PodMonitors are new to you ([YouTube](https://www.youtube.com/watch?v=6xmWr7p5TE0)) · 5) Practice: add the exporters below to the lab and fire every alert once on purpose.

Every playbook in section 10 starts with a symptom someone noticed. The goal of monitoring is that
the someone is an alert, not a customer, and that it fires early enough to act: when connections
reach 80%, not 100%; when the disk will be full in four hours, not when it is full; when the backup
is 26 hours old, not when you need it.

### What to measure

**Level:** [L2 · Mid] → [L3 · Senior] · about 30 minutes

**Concept.** The same ten signals cover PostgreSQL, MySQL and Redis:

| Signal | Why | PostgreSQL | MySQL | Redis |
|---|---|---|---|---|
| Up and accepting connections | nothing else matters if not | `pg_up` | `mysql_up` | `redis_up` |
| Connections vs limit | "too many connections" before it happens | `numbackends` vs `max_connections` | `Threads_connected` vs `max_connections` | `connected_clients` vs `maxclients` |
| Long transactions | locks, bloat, replication conflicts | oldest `xact_start` | `innodb_trx` age, history list length | — |
| Query latency, top queries | "slow after deploy" | `pg_stat_statements` | slow log, `performance_schema` digests | `SLOWLOG`, latency |
| Replication | stale reads, failover safety | lag, slot retention | thread state, `Seconds_Behind_Source` | `master_link_status` |
| Disk space and growth rate | hours of warning, if you look at the trend | data directory, `pg_wal` | data directory, binlogs | RDB and AOF files |
| Errors | silent damage | deadlocks, rollbacks, checksum failures | deadlocks, `Aborted_connects` | `rejected_connections`, failed snapshots |
| Memory and cache | performance | cache hit ratio (`blks_hit` vs `blks_read`) | buffer pool hit rate | `used_memory` vs `maxmemory`, evictions |
| Maintenance | slow degradation | dead tuples, last autovacuum, transaction ID age | — | fragmentation |
| Backups | your real RPO | last successful backup and restore test | same | same |

Transaction ID age deserves a line of its own for PostgreSQL: if `age(datfrozenxid)` approaches
about 2 billion, PostgreSQL stops accepting writes to protect itself (wraparound). Autovacuum
normally prevents it; long transactions and broken autovacuum do not. Alert well before, for example
at 1 billion: `SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;`.

**Page or ticket?** Page a human only for symptoms that need action now: database down,
replication broken, disk full within hours, backups older than the RPO, snapshot writes failing.
Everything else (connections at 80%, a long transaction, a cache hit ratio dropping) is a ticket
for working hours. An alert that fires every night and is always ignored trains people to ignore the
one that matters.

**Hands-on lab.** For the lab stack, write one line per signal: the metric, the threshold, page or
ticket, and which section of this module the runbook link points to. The next two topics implement
that list.

**Why it matters for troubleshooting.** Good dashboards answer the first question of every playbook
("since when?") before you have logged in.

**Next step:** collect the metrics with exporters.

### Exporters for PostgreSQL, MySQL and Redis

**Level:** [L3 · Senior] · about 60 minutes

**Concept.** Prometheus scrapes small **exporters** that translate database statistics into
metrics: `postgres_exporter` (port 9187), `mysqld_exporter` (9104), `redis_exporter` (9121), plus
`node_exporter` (9100) for the host and for the textfile metrics your backup and restore-test
scripts write. Ubuntu packages all four. Each exporter needs a dedicated, low-privilege database
login; metric names differ between exporter versions, so confirm names with `curl` before writing
alert rules.

```bash
# PostgreSQL: the exporter runs as OS user "prometheus" and logs in over the Unix socket (peer auth)
sudo apt install -y prometheus-postgres-exporter prometheus-mysqld-exporter prometheus-redis-exporter
sudo -u postgres psql -c "CREATE ROLE prometheus LOGIN IN ROLE pg_monitor;"
grep DATA_SOURCE_NAME /etc/default/prometheus-postgres-exporter
```

```
DATA_SOURCE_NAME='user=prometheus host=/run/postgresql dbname=postgres'
```

→ Set (or check) that line, then `sudo systemctl restart prometheus-postgres-exporter`. With peer
authentication over the socket, there is no password to store.

```bash
# MySQL: a dedicated account, and a client config file that only the exporter can read
sudo mysql -e "CREATE USER 'exporter'@'127.0.0.1' IDENTIFIED BY 'LabExporter-123' WITH MAX_USER_CONNECTIONS 3; GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'127.0.0.1';"
sudo tee /etc/prometheus/mysqld-exporter.cnf >/dev/null <<'EOF'
[client]
user = exporter
password = LabExporter-123
host = 127.0.0.1
EOF
sudo chown prometheus:prometheus /etc/prometheus/mysqld-exporter.cnf
sudo chmod 0600 /etc/prometheus/mysqld-exporter.cnf
```

Point the exporter at it with `ARGS='--config.my-cnf=/etc/prometheus/mysqld-exporter.cnf'` in
`/etc/default/prometheus-mysqld-exporter` (mysqld_exporter 0.15 and later no longer read
`DATA_SOURCE_NAME`; older packages still do, so check `prometheus-mysqld-exporter --version` and
the comments in that file).
The account uses `127.0.0.1` rather than `localhost` because, with `skip_name_resolve = ON` from
section 3, TCP connections match accounts by IP. For Redis, give the exporter its own read-only ACL
user and pass it with `--redis.user` and the `REDIS_PASSWORD` environment variable.

```yaml
# prometheus.yml (excerpt)
scrape_configs:
  - job_name: node
    static_configs:
      - targets: ['db1.example.internal:9100', 'db2.example.internal:9100']
  - job_name: postgres
    static_configs:
      - targets: ['db1.example.internal:9187', 'db2.example.internal:9187']
  - job_name: mysql
    static_configs:
      - targets: ['db1.example.internal:9104']
  - job_name: redis
    static_configs:
      - targets: ['db1.example.internal:9121']
```

On Kubernetes, CloudNativePG instances expose PostgreSQL metrics on port 9187 themselves; scrape
them with a PodMonitor if you run the Prometheus Operator.

**See it on a real system**

```bash
curl -s localhost:9187/metrics | grep -E '^(pg_up|pg_settings_max_connections|pg_stat_database_numbackends\{.*datname="appdb")'
curl -s localhost:9104/metrics | grep -E '^(mysql_up|mysql_global_status_threads_connected|mysql_global_variables_max_connections) '
curl -s localhost:9121/metrics | grep -E '^(redis_up|redis_memory_used_bytes|redis_memory_max_bytes) '
cat /var/lib/prometheus/node-exporter/db_backup.prom
```

```
pg_settings_max_connections 100
pg_stat_database_numbackends{datid="16389",datname="appdb"} 23
pg_up 1
mysql_global_status_threads_connected 41
mysql_global_variables_max_connections 151
mysql_up 1
redis_memory_max_bytes 1.610612736e+09
redis_memory_used_bytes 1.299210312e+09
redis_up 1
db_backup_last_success_timestamp_seconds{db="appdb"} 1790993232
db_backup_size_bytes{db="appdb"} 1717986918
```

→ All three exporters can log in (`*_up 1`), and the backup script's textfile metric is visible
through node_exporter: last success at epoch 1790993232, which is 02:07:12 today, when the
nightly dump finished. If a `*_up` metric
is 0, the exporter is running but cannot reach the database: check its log with
`journalctl -u prometheus-postgres-exporter -n 20`, which usually shows the same authentication or
`pg_hba.conf` error an application would.

**Hands-on lab (test VMs only)**

**Step 1 — Build.** Install the exporters on db1, add the scrape jobs, and confirm in the
Prometheus UI (Status, then Targets) that every target is up.

**Step 2 — Break it.** Revoke the monitoring role's login (`ALTER ROLE prometheus NOLOGIN;`) and
watch `pg_up` drop to 0 while PostgreSQL itself is fine.

**Step 3 — Fix it.** `ALTER ROLE prometheus LOGIN;`. Note the lesson for the alert design: "the
exporter cannot log in" and "the database is down" look identical from Prometheus, so the runbook's
first step is always to connect yourself.

**Why it matters for troubleshooting.** Exporters turn the views you learned in sections 2 and 3
into history. History answers "since when?" and "what changed at that moment?", the two questions
that shorten every incident.

**Next step:** turn the metrics into a small set of alerts that deserve to wake someone.

### Alert rules that matter

**Level:** [L3 · Senior] · about 60 minutes

**Concept.** Fourteen rules cover the incidents in this module. Each rule on a fluctuating value
has a `for:` so a brief spike does not page (the two backup-age rules need none), every rule has a
`severity` label that Alertmanager routes (page or ticket), and a `runbook` annotation points to
the playbook (add one to the MySQL and Redis rules that still lack it once their runbooks exist). Adjust
thresholds to your own baseline after a few weeks of data, and adapt metric names to your exporter
versions.

```yaml
# /etc/prometheus/rules/databases.yml
groups:
  - name: databases
    rules:
      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: page
        annotations:
          summary: "PostgreSQL on {{ $labels.instance }} does not answer the exporter"
          runbook: "38-learn-databases-ops.md, section 10: app can't connect"

      - alert: PostgresConnectionsHigh
        expr: sum by (instance) (pg_stat_database_numbackends) / max by (instance) (pg_settings_max_connections) > 0.8
        for: 5m
        labels:
          severity: ticket
        annotations:
          summary: "{{ $labels.instance }} uses {{ $value | humanizePercentage }} of max_connections"
          runbook: "38-learn-databases-ops.md, section 10: too many connections"

      - alert: PostgresReplicationLagHigh
        expr: pg_replication_lag_seconds > 300
        for: 5m
        labels:
          severity: page
        annotations:
          summary: "Standby {{ $labels.instance }} is {{ $value | humanizeDuration }} behind"
          runbook: "38-learn-databases-ops.md, section 10: replication lag"

      - alert: PostgresInactiveReplicationSlot
        expr: pg_replication_slot_slot_is_active == 0
        for: 30m
        labels:
          severity: ticket
        annotations:
          summary: "Slot {{ $labels.slot_name }} on {{ $labels.instance }} is inactive and keeps WAL"
          runbook: "38-learn-databases-ops.md, section 10: disk full from WAL or binlogs"

      - alert: PostgresLongTransaction
        expr: max by (instance, datname) (pg_stat_activity_max_tx_duration) > 1800
        for: 5m
        labels:
          severity: ticket
        annotations:
          summary: "A transaction in {{ $labels.datname }} on {{ $labels.instance }} has been open for over 30 minutes"
          runbook: "38-learn-databases-ops.md, section 10: locks and blocked queries"

      - alert: DatabaseDiskFillsIn4h
        expr: predict_linear(node_filesystem_avail_bytes{mountpoint=~"/var/lib/(postgresql|mysql|redis)"}[6h], 4 * 3600) < 0
        for: 15m
        labels:
          severity: page
        annotations:
          summary: "{{ $labels.mountpoint }} on {{ $labels.instance }} will be full within 4 hours"
          runbook: "38-learn-databases-ops.md, section 10: disk full from WAL or binlogs"

      - alert: DatabaseBackupTooOld
        expr: time() - db_backup_last_success_timestamp_seconds > 26 * 3600
        labels:
          severity: page
        annotations:
          summary: "No successful {{ $labels.db }} backup on {{ $labels.instance }} for over 26 hours"
          runbook: "38-learn-databases-ops.md, section 4"

      - alert: DatabaseRestoreTestTooOld
        expr: time() - db_restore_test_last_success_timestamp_seconds > 8 * 86400
        labels:
          severity: ticket
        annotations:
          summary: "The {{ $labels.db }} restore test has not passed for over 8 days"
          runbook: "38-learn-databases-ops.md, section 4: restore tests"

      - alert: MySQLDown
        expr: mysql_up == 0
        for: 1m
        labels:
          severity: page
        annotations:
          summary: "MySQL on {{ $labels.instance }} does not answer the exporter"

      - alert: MySQLConnectionsHigh
        expr: mysql_global_status_threads_connected / mysql_global_variables_max_connections > 0.8
        for: 5m
        labels:
          severity: ticket
        annotations:
          summary: "{{ $labels.instance }} uses over 80% of max_connections"

      - alert: MySQLReplicationStopped
        # names follow SHOW SLAVE STATUS on MySQL 8.0 and SHOW REPLICA STATUS on 8.4
        expr: (mysql_slave_status_slave_sql_running or mysql_slave_status_replica_sql_running) == 0 or (mysql_slave_status_slave_io_running or mysql_slave_status_replica_io_running) == 0
        for: 2m
        labels:
          severity: page
        annotations:
          summary: "Replication stopped on {{ $labels.instance }}"
          runbook: "38-learn-databases-ops.md, section 5: MySQL replication with GTIDs"

      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: page
        annotations:
          summary: "Redis on {{ $labels.instance }} does not answer the exporter"

      - alert: RedisMemoryNearLimit
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9 and redis_memory_max_bytes > 0
        for: 10m
        labels:
          severity: ticket
        annotations:
          summary: "Redis {{ $labels.instance }} is above 90% of maxmemory"

      - alert: RedisSnapshotFailing
        expr: redis_rdb_last_bgsave_status == 0
        for: 5m
        labels:
          severity: page
        annotations:
          summary: "Redis {{ $labels.instance }} cannot write its snapshot; writes will fail with MISCONF"
```

The disk rule's `mountpoint` regex assumes the data directories are separate filesystems (a good
practice: a full database disk then cannot take the operating system down with it). If they live
on `/`, match that mount instead.

**See it on a real system**

```bash
promtool check rules /etc/prometheus/rules/databases.yml
curl -s localhost:9090/api/v1/rules | jq -r '.data.groups[].rules[] | "\(.state)\t\(.name)"'
```

```
Checking /etc/prometheus/rules/databases.yml
  SUCCESS: 14 rules found

inactive	PostgresDown
inactive	PostgresConnectionsHigh
firing	PostgresReplicationLagHigh
inactive	PostgresInactiveReplicationSlot
pending	PostgresLongTransaction
inactive	DatabaseDiskFillsIn4h
inactive	DatabaseBackupTooOld
inactive	DatabaseRestoreTestTooOld
inactive	MySQLDown
inactive	MySQLConnectionsHigh
inactive	MySQLReplicationStopped
inactive	RedisDown
inactive	RedisMemoryNearLimit
inactive	RedisSnapshotFailing
```

→ The rules load. One alert is firing (replication lag) and one is `pending`: its condition is true
but has not yet lasted for its `for:` duration. That is the replication lag playbook's starting
point.

**Hands-on lab (test VMs only): fire every alert once**

**Step 1 — Build.** Load the rules, route `severity="page"` to a test receiver in Alertmanager (an
email or chat webhook in the lab), and lower thresholds for the lab where waiting is impractical
(for example a 2-minute long-transaction rule).

**Step 2 — Break it, one at a time.** Stop PostgreSQL; run pgbench with 90 clients; pause replay on
db2 while pgbench runs; open a transaction and leave it; create the "ghost" slot from section 1;
disable the backup timer and edit the textfile timestamp to two days ago; reproduce Redis `MISCONF`.

**Step 3 — Fix it.** For each one, note how long it took from break to notification. If an alert
did not fire, the rule or the routing is wrong, and you just found that in a lab rather than during
an incident.

**How it breaks**

| Symptom | First check | Fix |
|---|---|---|
| Alert never fires | `promtool check rules`; does the metric exist under that name? (`curl` the exporter) | adapt the metric name to your exporter version |
| Alert fires constantly and is ignored | its history over a week | raise the threshold, add `for:`, or demote it to a ticket |
| `*_up` is 0 but the database works | the exporter's journal | the monitoring login (role, `pg_hba.conf`, password) |
| "Backup too old" fires after a server move | the textfile directory on the new host | deploy the backup script and its metric with the server |

**Why it matters for troubleshooting.** A good alert is the first step of its playbook, delivered
automatically, with the link to the next step attached.

**Next step:** the playbooks themselves.

---

## 10. Incident playbooks

> 📚 **Study path:** 1) Note: [Site down](25-playbook-site-down.md) for the layered method these playbooks reuse, and [Slow system](23-playbook-slow-system.md) for the host side of "slow" (refreshers, so they come first) · 2) KodeKloud: *Fundamentals of SRE* — Incident Management: Preparing for Incidents, then Root Cause Analysis ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) KodeKloud: *Linux Challenges* (free), timed scenarios that include fixing a broken database service ([course](https://kodekloud.com/courses/linux-challenges)) · 4) Practice: run each playbook on the lab VMs against a 20-minute timer after a colleague or a script breaks something, then write the five-line note.

These are the seven database incidents a DevOps engineer is expected to handle alone from the
Mid-level stage on. Each step has the same shape: the **goal**, the command, a realistic output,
**what it means**, **why this step comes now**, and the **next step** for each possible result.
Run them first in the lab, with the "break it" steps from sections 1 to 9, so that the real
incident feels like a rerun.

### First five minutes

**Level:** [L2 · Mid] · read before any playbook

Whatever the symptom, the first five minutes are the same, and they often point straight at the
right playbook:

```bash
# 1. Is it up, and what does it say about itself?
systemctl status postgresql@16-main --no-pager | head -n 4
sudo tail -n 20 /var/log/postgresql/postgresql-16-main.log
# 2. Is the host itself healthy? (disk, memory, load)
df -h /var/lib/postgresql /var/lib/mysql 2>/dev/null; free -m; uptime
# 3. Who is connected, and what are they waiting for?
sudo -u postgres psql -c "SELECT state, wait_event_type, count(*) FROM pg_stat_activity WHERE backend_type = 'client backend' GROUP BY 1, 2 ORDER BY 3 DESC;"
# 4. What changed? (deploys, migrations, package updates, config)
grep -E ' (upgrade|install) ' /var/log/dpkg.log | tail -n 5
```

Four habits go with it:

- **Write the time down** when the incident starts and at every action. PITR and the postmortem
  both need it.
- **Save evidence before you change anything.** Copy the `pg_stat_activity` or `SHOW PROCESSLIST`
  output into the ticket before terminating sessions; afterwards it is gone.
- **Prefer the gentle action.** Cancel a query before terminating a session, terminate one
  session before restarting the server, restart before restoring.
- **Say what you see.** A one-line update in the incident channel every 15 minutes ("connections
  full, cause found, fixing") stops five people from debugging the same thing.

| What you hear or see | Playbook |
|---|---|
| `FATAL:  sorry, too many clients already`, `ERROR 1040 (HY000): Too many connections` | Too many connections |
| `No space left on device`, database stopped or refusing writes | Disk full from WAL or binlogs |
| "I saved it and it disappeared", reports show old data | Replication lag |
| "Everything is slow since the release" | Slow queries after a deploy |
| Requests hang, a migration job "runs" forever | Locks and blocked queries |
| `Connection refused`, `timed out`, `no pg_hba.conf entry`, `password authentication failed` | App can't connect to the database |
| "We deleted rows by mistake, get them back" | Restore a single table |
| Redis errors (`OOM`, `MISCONF`, `READONLY`) | Section 6, common Redis incidents |

### Too many connections

**Level:** [L2 · Mid] · target: service stable in 15 minutes, cause found within the hour

The scenario: at 09:50 `shop-api` was scaled from 2 to 6 replicas in Dokploy. Since then about
half of the requests fail, and the API logs show `FATAL:  sorry, too many clients already` (a
MySQL-backed app would show `ERROR 1040 (HY000): Too many connections`).

**Step 1 — Confirm the ceiling and keep your own way in.**

**Goal:** prove the limit is PostgreSQL's, not a pooler's, and secure an admin session.

```bash
sudo -u postgres psql -Atc "SELECT count(*), current_setting('max_connections'), current_setting('superuser_reserved_connections') FROM pg_stat_activity WHERE backend_type = 'client backend';"
sudo grep -cE 'too many clients|remaining connection slots' /var/log/postgresql/postgresql-16-main.log
```

```
98|100|3
2214
```

**What it means:** 98 client sessions out of 100: 97 from applications, which is every slot not
reserved for superusers, plus your own. The last 3 slots are reserved for superusers, and the log
holds 2,214 refused connections. Your `sudo -u postgres` session got in through one of those
reserved slots: use this one session for everything and do not open more.

**Why this step (now):** PgBouncer refuses with a different message (`no more connections allowed
(max_client_conn)`), and a per-role limit with another (`too many connections for role "app"`).
Fixing the wrong layer wastes the incident, and without a working admin session you cannot
investigate at all.

**Next step:** Step 2. If the count is far below `max_connections`, the refusal comes from a pooler
or a role limit: check PgBouncer's `SHOW POOLS;` (section 2) or `SELECT rolname, rolconnlimit FROM pg_roles WHERE rolconnlimit <> -1;`.

**Step 2 — Group the sessions by client and state.**

**Goal:** find who holds the slots, and whether they are doing any work.

```bash
sudo -u postgres psql -c "SELECT usename, client_addr, application_name, state, count(*), max(now() - state_change) AS longest FROM pg_stat_activity WHERE backend_type = 'client backend' GROUP BY 1, 2, 3, 4 ORDER BY 5 DESC LIMIT 6;"
```

```
 usename | client_addr | application_name |        state        | count |     longest
---------+-------------+------------------+---------------------+-------+-----------------
 app     | 192.0.2.52  | shop-api         | idle                |    58 | 02:11:43.20391
 app     | 192.0.2.50  | shop-api         | idle                |    21 | 00:41:02.88112
 app     | 192.0.2.51  | shop-api         | active              |     9 | 00:00:01.20113
 app     | 192.0.2.50  | shop-worker      | idle in transaction |     6 | 00:37:15.00981
 grafana | 192.0.2.60  |                  | idle                |     3 | 00:12:00.51200
 postgres|             | psql             | active              |     1 | 00:00:00
(6 rows)
```

**What it means:** 88 of the 97 application sessions are idle or stuck; only 9 are working (the
last row is your own session). 58 idle sessions
from one host, some for over two hours, are oversized pools or a leak. The six `idle in
transaction` worker sessions hold locks and old snapshots: a bug of their own.

**Why this step (now):** "too many connections" is almost never too much *work*; it is too many
pools multiplied by pool size. The grouping names the client to fix and shows which sessions are
safe to end.

**Next step:** Step 3, before anything else fills the free slots.

**Step 3 — Free slots, gentlest first.**

**Goal:** restore service without restarting PostgreSQL.

```bash
# 1. Abandoned transactions first: they are rolled back, and their work was going nowhere
sudo -u postgres psql -c "SELECT pid, client_addr, application_name, pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND now() - state_change > interval '10 minutes';"
# 2. Then long-idle sessions from the leaking host, in one batch
sudo -u postgres psql -c "SELECT count(pg_terminate_backend(pid)) FROM (SELECT pid FROM pg_stat_activity WHERE client_addr = '192.0.2.52' AND state = 'idle' AND now() - state_change > interval '30 minutes' ORDER BY state_change LIMIT 30) AS s;"
```

```
  pid  | client_addr | application_name | pg_terminate_backend
-------+-------------+------------------+----------------------
 41187 | 192.0.2.50  | shop-worker      | t
 41190 | 192.0.2.50  | shop-worker      | t
 41201 | 192.0.2.50  | shop-worker      | t
 41204 | 192.0.2.50  | shop-worker      | t
 41262 | 192.0.2.50  | shop-worker      | t
 41263 | 192.0.2.50  | shop-worker      | t
(6 rows)

 count
-------
    30
(1 row)
```

**What it means:** 36 slots are free. Pools with health checks reconnect when they need to; the
idle sessions were doing nothing, and the six worker transactions were rolled back.

**Why this step (now):** it buys time with the smallest blast radius. A restart would drop all
sessions, including the 9 doing real work, empty the cache, and the pools would refill the server
within seconds anyway.

**Next step:** Step 4, because the slots will fill again.

> Never terminate `walsender`, `autovacuum` or other non-client processes, and never `kill -9` a
> PostgreSQL process from the shell: a backend killed with SIGKILL makes the postmaster end every
> session and run crash recovery, which is the outage you were trying to avoid.

**Step 4 — Make demand fit supply.**

**Goal:** find why demand exceeds the limit, and remove that reason.

```bash
docker service ls --filter name=shop-api --format '{{.Name}} {{.Replicas}}'
docker service inspect shop-api-4m9tqz --format '{{range .Spec.TaskTemplate.ContainerSpec.Env}}{{println .}}{{end}}' | grep -E 'POOL|WORKERS'
```

```
shop-api-4m9tqz 6/6
DB_POOL_SIZE=10
GUNICORN_WORKERS=4
```

**What it means:** 6 replicas × 4 workers × 10 connections = 240 possible connections against 97
usable slots. At 2 replicas it was 80, which fit. The scale-out at 09:50 broke the arithmetic from
section 2 ("max_connections and PgBouncer").

**Why this step (now):** until demand fits supply, Step 3 has to be repeated forever.

**Next step:** right now, scale back to the last good replica count or lower `DB_POOL_SIZE` (3 gives
72). This week, put PgBouncer in transaction mode in front of PostgreSQL (section 2) and set
`ALTER ROLE app SET idle_in_transaction_session_timeout = '5min';`. Raise `max_connections` only as
the last option, after checking memory, and remember it needs a restart.

**Step 5 — The MySQL version.**

**Goal:** the same diagnosis on MySQL.

```bash
sudo mysql -e "SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Max_used_connections','Max_used_connections_time','Connection_errors_max_connections');"
sudo mysql -e "SELECT user, substring_index(host, ':', 1) AS client, command, count(*), max(time) FROM information_schema.processlist GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 4;"
sudo mysql -Nse "SELECT concat('KILL ', id, ';') FROM information_schema.processlist WHERE command = 'Sleep' AND time > 1800 AND host LIKE '192.0.2.52:%';" > /tmp/kill-idle.sql
wc -l < /tmp/kill-idle.sql
```

```
+-----------------------------------+---------------------+
| Variable_name                     | Value               |
+-----------------------------------+---------------------+
| Connection_errors_max_connections | 1312                |
| Max_used_connections              | 152                 |
| Max_used_connections_time         | 2026-10-03 09:51:40 |
| Threads_connected                 | 152                 |
+-----------------------------------+---------------------+
+------+------------+---------+----------+-----------+
| user | client     | command | count(*) | max(time) |
+------+------------+---------+----------+-----------+
| app  | 192.0.2.52 | Sleep   |      104 |      7903 |
| app  | 192.0.2.50 | Sleep   |       31 |      2460 |
| app  | 192.0.2.51 | Query   |       11 |         2 |
| root | localhost  | Query   |        1 |         0 |
+------+------------+---------+----------+-----------+
46
```

**What it means:** the ceiling (151, plus the extra slot your `sudo mysql` session is using through
`CONNECTION_ADMIN`) was hit at 09:51:40, a minute after the scale-out. 104 connections from
192.0.2.52 are asleep, some for over two hours; the generated file holds 46 `KILL` statements for
those asleep longer than 30 minutes. Read it, then run it with `sudo mysql < /tmp/kill-idle.sql`.

**Why this step (now):** the logic is identical to Steps 2 and 3; `KILL ID` ends a connection and
rolls back its open transaction.

**Next step:** the arithmetic of Step 4. For MySQL also lower `wait_timeout` (for example
`SET PERSIST wait_timeout = 600;`) once you know every pool recycles connections sooner than that,
and consider ProxySQL as the pooler (section 3).

**After the incident**

- The 80% connections alert from section 9, so the next one is a ticket, not an outage.
- A capacity line in the deploy checklist: replicas × workers × pool size, before every scale-out.
- A pooler in front of the database, and `idle_in_transaction_session_timeout` for app roles.

### Disk full from WAL or binlogs

**Level:** [L2 · Mid] → [L3 · Senior] · target: stable in 20 minutes

The scenario: at 03:10 the `DatabaseDiskFillsIn4h` alert has been firing for an hour, and db1's
`/var/lib/postgresql` is at 98%. At 100% PostgreSQL stops with
`PANIC:  could not write to file "pg_wal/xlogtemp.4711": No space left on device` and every write
fails.

**Step 1 — Measure what is big.**

**Goal:** know which directory is growing before choosing a fix.

```bash
df -h /var/lib/postgresql
sudo du -sh /var/lib/postgresql/16/main/pg_wal /var/lib/postgresql/16/main/base
sudo -u postgres psql -Atc "SELECT pg_size_pretty(sum(size)) FROM pg_ls_waldir();" -c "SHOW max_wal_size;"
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb1        98G   95G  2.9G  98% /var/lib/postgresql
61G     /var/lib/postgresql/16/main/pg_wal
29G     /var/lib/postgresql/16/main/base
61 GB
1GB
```

**What it means:** WAL takes 61 GB, twice the size of the data and sixty times `max_wal_size`.
Something is holding WAL. Data growth is not today's problem.

**Why this step (now):** a full database disk has three unrelated causes (WAL retention, data
growth, logs or stray files), and this step picks one in a minute. Data growth belongs to
[Storage & disk](01-storage-disk.md) and capacity planning.

**Next step:** Step 2. If PostgreSQL has already stopped with `PANIC`, first free a little space
**outside** the data directory on the same filesystem (stray files, old copies; never anything in
`pg_wal`), start the service, let crash recovery finish, then continue with Step 2.

**Step 2 — Find what pins the WAL.**

**Goal:** identify which of the four retention reasons from section 1 applies.

```bash
sudo -u postgres psql -c "SELECT slot_name, slot_type, active, wal_status, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained FROM pg_replication_slots;"
sudo -u postgres psql -x -c "SELECT archived_count, last_archived_wal, failed_count, last_failed_wal FROM pg_stat_archiver;"
sudo ls /var/lib/postgresql/16/main/pg_wal/archive_status/ | grep -c '\.ready$'
sudo -u postgres psql -Atc "SHOW wal_keep_size;"
```

```
 slot_name | slot_type | active | wal_status | retained
-----------+-----------+--------+------------+----------
 db2       | physical  | t      | reserved   | 12 MB
 analytics | logical   | f      | extended   | 60 GB
(2 rows)

-[ RECORD 1 ]-----+-------------------------
archived_count    | 18834
last_archived_wal | 00000001000000210000004F
failed_count      | 0
last_failed_wal   |

3
0
```

**What it means:** the logical slot `analytics` is inactive and pins 60 GB: a change-data-capture
consumer (for example Debezium) that was switched off without dropping its slot. Archiving is
healthy (no failures; a few `.ready` segments waiting is normal), `wal_keep_size` is 0, and the
physical slot for db2 is active and current.

**Why this step (now):** each retention reason has its own fix, and the wrong one breaks
something else: dropping `db2` would break replication.

**Next step:** Step 3. If instead `failed_count` keeps growing, fix the archive target (mount,
permissions, credentials, space): the queued WAL drains by itself once archiving succeeds. Never
delete `.ready` files.

**Step 3 — Release the WAL safely.**

**Goal:** remove the reason and let PostgreSQL clean up after itself.

```bash
# Confirm with the slot's owner first: the consumer will need a fresh snapshot afterwards
sudo -u postgres psql -c "SELECT pg_drop_replication_slot('analytics');"
sudo -u postgres psql -c "CHECKPOINT;"
df -h /var/lib/postgresql
```

```
 pg_drop_replication_slot
--------------------------

(1 row)

CHECKPOINT
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb1        98G   35G   63G  36% /var/lib/postgresql
```

**What it means:** at the checkpoint PostgreSQL removed or recycled every segment that nothing
needs any more: 60 GB back.

**Why this step (now):** removing the reason is the only safe way to shrink `pg_wal`. Deleting WAL
files by hand loses committed data or leaves a server that refuses to start.

**Next step:** Step 5 to prevent a repeat; Step 4 if the full disk is a MySQL server.

> **Never** `rm` files in `pg_wal/` or `pg_wal/archive_status/`, and never run `pg_resetwal` on a
> production server to "fix" WAL: it is a last-resort tool for corrupted clusters and can silently
> lose committed transactions.

**Step 4 — The MySQL version: binlogs.**

**Goal:** free binlog space without breaking replicas or your PITR chain.

```bash
sudo ls /var/lib/mysql | grep -c '^binlog\.[0-9]'
sudo mysql -e "SHOW BINARY LOGS;" | sed -n '2p;$p'
sudo mysql -e "SHOW VARIABLES LIKE 'binlog_expire_logs_seconds';"
# on every replica: which source binlog is it still reading?
sudo mysql -e "SHOW REPLICA STATUS\G" | grep -E ' Source_Log_File|Relay_Source_Log_File'
```

```
70
binlog.001378	1073742004	No
binlog.001447	48211907	No
+----------------------------+---------+
| Variable_name              | Value   |
+----------------------------+---------+
| binlog_expire_logs_seconds | 2592000 |
+----------------------------+---------+
              Source_Log_File: binlog.001447
        Relay_Source_Log_File: binlog.001446
```

**What it means:** 30 days of binlogs (the default expiry) on a busy server: 70 files of about
1 GB. The replica reads `binlog.001447`, so older files are no longer needed **for replication**.
Whether they are needed for PITR depends on your backups: keep everything written since the oldest
full backup you would restore from (and copy binlogs to the backup server before purging).

**Why this step (now):** `PURGE BINARY LOGS` keeps MySQL's binlog index and its replicas
consistent; deleting the files with `rm` breaks both.

**Next step:** `sudo mysql -e "PURGE BINARY LOGS TO 'binlog.001400';"` and
`sudo mysql -e "SET PERSIST binlog_expire_logs_seconds = 604800;"` (7 days, longer than your
full-backup interval), then Step 5.

**Step 5 — Prevent the next one.**

**Goal:** turn a site-wide outage into a contained, alerted problem.

```bash
echo "max_slot_wal_keep_size = 20GB" | sudo tee /etc/postgresql/16/main/conf.d/61-slot-cap.conf
sudo -u postgres psql -c "SELECT pg_reload_conf();"
sudo -u postgres psql -Atc "SELECT name, setting, unit FROM pg_settings WHERE name IN ('max_slot_wal_keep_size', 'max_wal_size');"
```

```
max_slot_wal_keep_size = 20GB
 pg_reload_conf
----------------
 t
(1 row)

max_slot_wal_keep_size|20480|MB
max_wal_size|1024|MB
```

**What it means:** from now on a forgotten slot can pin at most 20 GB. Beyond that PostgreSQL
invalidates the slot (its consumer must resynchronise) instead of filling the disk.

**Why this step (now):** it is a trade-off (one consumer's inconvenience instead of everyone's
outage) that should be decided calmly, which is now, not at the next 3 a.m.

**Next step:** add the inactive-slot and disk-trend alerts from section 9; make "drop its slot"
part of decommissioning any replica or CDC tool; keep the data directory on its own filesystem;
then write the postmortem.

### Replication lag

**Level:** [L3 · Senior] · target: cause found in 15 minutes

The scenario: at 14:20 support reports that customers "save an order and it disappears for a
minute", the reporting dashboard (which reads from db2) shows numbers from a quarter of an hour
ago, and `PostgresReplicationLagHigh` is firing.

**Step 1 — Measure lag from the primary, in three parts.**

**Goal:** find where the WAL is waiting.

```bash
sudo -u postgres psql -x -c "SELECT application_name, client_addr, state, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn)) AS not_sent, pg_size_pretty(pg_wal_lsn_diff(sent_lsn, flush_lsn)) AS not_flushed, pg_size_pretty(pg_wal_lsn_diff(flush_lsn, replay_lsn)) AS not_replayed, replay_lag FROM pg_stat_replication;"
```

```
-[ RECORD 1 ]----+----------------
application_name | db2
client_addr      | 192.0.2.22
state            | streaming
not_sent         | 0 bytes
not_flushed      | 160 kB
not_replayed     | 7310 MB
replay_lag       | 00:14:31.118024
```

**What it means:** everything was sent and received, but 7.3 GB, about 14.5 minutes of changes,
waits to be **replayed**. The network and the standby's disk are keeping up; replay is slow or
blocked.

**Why this step (now):** the three columns turn "the replica is behind" into one of three causes
with different owners (section 5, "Measuring replication lag").

**Next step:** a large `not_replayed` → Step 2. A large `not_sent` or `not_flushed` → the network
or the standby's disk (`iostat -x 5 2` on db2, and [Network speed](24-playbook-network-speed.md)).
No row at all → the standby is disconnected: Step 4.

**Step 2 — On the standby: blocked or slow?**

**Goal:** tell "cannot keep up" from "is not allowed to continue".

```bash
# on db2
sudo -u postgres psql -x -c "SELECT pg_is_wal_replay_paused(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), now() - pg_last_xact_replay_timestamp() AS replay_age;"
sudo -u postgres psql -c "SELECT pid, now() - xact_start AS xact_age, state, left(query, 60) AS query FROM pg_stat_activity WHERE backend_type = 'client backend' AND xact_start IS NOT NULL ORDER BY xact_start LIMIT 3;"
sudo -u postgres psql -Atc "SHOW max_standby_streaming_delay;"
```

```
-[ RECORD 1 ]-----------+----------------
pg_is_wal_replay_paused | f
pg_last_wal_receive_lsn | 2A/9C1F0B28
pg_last_wal_replay_lsn  | 29/1B0E2A10
replay_age              | 00:14:29.33112

  pid  |    xact_age     | state  |                            query
-------+-----------------+--------+--------------------------------------------------------------
 41022 | 00:16:02.118211 | active | SELECT customer_id, sum(total) FROM orders GROUP BY customer
(1 row)

-1
```

**What it means:** replay is not paused, but a 16-minute report holds a snapshot that the incoming
WAL conflicts with, and `max_standby_streaming_delay = -1` tells replay to wait for it **forever**.
Someone set -1 so that reports would stop being cancelled, and traded it for unbounded lag.

**Why this step (now):** lag on a standby is either capacity (I/O or CPU; `iostat -x 5 2` shows
`%util` near 100) or a conflict, and the fixes have nothing in common.

**Next step:** Step 3.

**Step 3 — Unblock replay and watch it catch up.**

**Goal:** get the replica current, then fix the policy.

```bash
# on db2: cancel the report (it can be rerun), then watch the backlog drain
sudo -u postgres psql -c "SELECT pg_cancel_backend(41022);"
for i in 1 2 3 4 5 6; do sudo -u postgres psql -Atc "SELECT pg_size_pretty(pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()));"; sleep 10; done
```

```
 pg_cancel_backend
-------------------
 t
(1 row)

7310 MB
5104 MB
2290 MB
412 MB
0 bytes
0 bytes
```

**What it means:** once unblocked, replay drains more than 200 MB per second; the replica is current
within a minute.

**Why this step (now):** cancelling one report is cheaper than serving stale data to every customer.

**Next step:** fix the policy with the conflict table in section 5: `max_standby_streaming_delay`
back to `30s` on the replica that serves the application, and long reports on a separate replica
(or `hot_standby_feedback = on`, with the bloat it costs). Route read-your-writes requests to the
primary. Step 5 covers MySQL.

**Step 4 — If the standby is disconnected.**

**Goal:** decide between reconnecting and rebuilding.

```bash
# on db2
sudo grep -E 'FATAL' /var/log/postgresql/postgresql-16-main.log | tail -n 2
```

```
2026-10-03 14:31:02.118 UTC [2211] FATAL:  could not receive data from WAL stream: ERROR:  requested WAL segment 0000000100000029000000A1 has already been removed
2026-10-03 14:31:07.204 UTC [2214] FATAL:  could not receive data from WAL stream: ERROR:  requested WAL segment 0000000100000029000000A1 has already been removed
```

**What it means:** the primary no longer has WAL this standby needs: there was no slot, or
`max_slot_wal_keep_size` invalidated it. If the standby has a `restore_command` pointing at your WAL
archive, it fetches the missing segments by itself; otherwise it must be rebuilt.

**Why this step (now):** no restart brings back missing history, so do not spend time on restarts.

**Next step:** rebuild db2 with `pg_basebackup` (section 5, "Streaming replication"), and find out
why it was disconnected long enough to fall off: that gap needs an alert.

**Step 5 — The MySQL version.**

**Goal:** the same questions for a MySQL replica.

```bash
sudo mysql -e "SHOW REPLICA STATUS\G" | grep -E 'Replica_IO_Running|Replica_SQL_Running:|Seconds_Behind_Source|Last_SQL_Error:'
sudo mysql -e "SELECT WORKER_ID, APPLYING_TRANSACTION, APPLYING_TRANSACTION_START_APPLY_TIMESTAMP FROM performance_schema.replication_applier_status_by_worker WHERE APPLYING_TRANSACTION <> '';"
```

```
           Replica_IO_Running: Yes
          Replica_SQL_Running: Yes
        Seconds_Behind_Source: 1184
               Last_SQL_Error:
+-----------+----------------------------------------------+--------------------------------------------+
| WORKER_ID | APPLYING_TRANSACTION                         | APPLYING_TRANSACTION_START_APPLY_TIMESTAMP |
+-----------+----------------------------------------------+--------------------------------------------+
|         1 | 3e11fa47-71ca-11ee-9a3e-080027a1b2c3:9912044 | 2026-10-03 14:01:12.004118                 |
+-----------+----------------------------------------------+--------------------------------------------+
```

**What it means:** both threads run, but worker 1 has been applying one transaction for 20
minutes: typically a bulk `DELETE` or `UPDATE` of millions of rows committed as a single
transaction on the source. With row-based binlogs the replica applies it row by row, and parallel
workers cannot split a single transaction.

**Why this step (now):** it tells you whether to wait (one big transaction finishing) or act (a
stopped thread, which shows as `Seconds_Behind_Source: NULL` and a `Last_*_Error`).

**Next step:** let it finish, and ask the developers to batch bulk changes (for example 10,000 rows
per transaction). For a stopped thread, follow "MySQL replication with GTIDs" in section 5.

**After the incident**

- Lag and disconnection alerts with a sensible `for:` (section 9).
- Replicas with the same disk and memory as the primary; a separate replica for reports.
- Bulk jobs in batches, scheduled away from peak hours.

### Slow queries after a deploy

**Level:** [L2 · Mid] · target: mitigated in 15 minutes

The scenario: release `4f1c2a9` of `shop-api` went out at 14:00 through GitLab CI and Dokploy.
Since then the p95 latency rose from 120 ms to 3 s and db1's CPU sits at 95%.

**Step 1 — Confirm the database is the slow layer.**

**Goal:** prove it, and connect it to the deploy.

```bash
uptime
sudo -u postgres psql -c "SELECT count(*), max(now() - query_start) AS longest, left(query, 70) AS query FROM pg_stat_activity WHERE state = 'active' AND backend_type = 'client backend' GROUP BY 3 ORDER BY 1 DESC LIMIT 3;"
```

```
 14:21:44 up 41 days,  3:12,  2 users,  load average: 15.82, 14.97, 9.41
 count |     longest     |                                 query
-------+-----------------+------------------------------------------------------------------------
    38 | 00:00:03.118220 | SELECT * FROM orders WHERE customer_id = $1 AND status = $2 ORDER BY c
     4 | 00:00:00.051002 | SELECT id, name, price FROM products WHERE id = $1
     1 | 00:00:00        | SELECT count(*), max(now() - query_start) AS longest, left(query, 70)
(3 rows)
```

**What it means:** a load of 15.8 on a 4-vCPU server, and 38 copies of one query shape running for
up to 3 seconds each. The database is the slow layer, and one query dominates it.

**Why this step (now):** before touching the database, make sure it is the database. An app server
out of CPU or a slow DNS lookup also look like "slow since the deploy"
([Slow system](23-playbook-slow-system.md)).

**Next step:** Step 2.

**Step 2 — Rank query shapes by total time.**

**Goal:** find what costs the most database time, not just what is slowest once.

```bash
sudo -u postgres psql -d appdb -c "SELECT calls, round(total_exec_time) AS total_ms, round(mean_exec_time::numeric, 1) AS mean_ms, rows, left(query, 60) AS query FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 4;"
```

```
 calls | total_ms | mean_ms |  rows  |                            query
-------+----------+---------+--------+--------------------------------------------------------------
 16286 | 45726180 |  2807.7 | 325720 | SELECT * FROM orders WHERE customer_id = $1 AND status = $2 O
 91822 |  1901204 |    20.7 |  91822 | UPDATE pgbench_accounts SET abalance = abalance + $1 WHERE a
  4410 |   880312 |   199.6 |   4410 | SELECT sum(total) FROM orders WHERE created_at > $1
 12209 |    91104 |     7.5 |  12209 | SELECT id, name, price FROM products WHERE id = $1
(4 rows)
```

**What it means:** one query shape owns most of the database's time since the deploy: 2.8 s per
call to return 20 rows (325,720 rows / 16,286 calls). Twenty rows should take milliseconds.

**Why this step (now):** total time shows where a fix pays off most. If `pg_stat_statements` holds
weeks of history, a new query can hide below old totals, so also sort by `mean_exec_time` with
`calls > 100`.

**Next step:** Step 3.

**Step 3 — Read the plan.**

**Goal:** prove why it is slow.

```bash
sudo -u postgres psql -d appdb -c "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE customer_id = 4242 AND status = 'paid' ORDER BY created_at DESC LIMIT 20;"
```

```
                                                              QUERY PLAN
--------------------------------------------------------------------------------------------------------------------------------------
 Limit  (cost=27129.42..27131.75 rows=20 width=34) (actual time=2801.207..2810.322 rows=20 loops=1)
   Buffers: shared hit=2208 read=6122
   ->  Gather Merge  (cost=27129.42..27131.98 rows=22 width=34) (actual time=2801.205..2810.317 rows=20 loops=1)
         Workers Planned: 2
         Workers Launched: 2
         Buffers: shared hit=2208 read=6122
         ->  Sort  (cost=26129.40..26129.42 rows=9 width=34) (actual time=2794.112..2794.114 rows=7 loops=3)
               Sort Key: created_at DESC
               Sort Method: quicksort  Memory: 25kB
               ->  Parallel Seq Scan on orders  (cost=0.00..26129.21 rows=9 width=34) (actual time=31.442..2794.031 rows=7 loops=3)
                     Filter: ((customer_id = 4242) AND (status = 'paid'::text))
                     Rows Removed by Filter: 333326
                     Buffers: shared hit=2208 read=6122
 Planning Time: 0.211 ms
 Execution Time: 2810.441 ms
(15 rows)
```

**What it means:** a parallel sequential scan reads all million rows to find 20; no index serves
`customer_id` plus `status`. The release introduced this query (or a migration dropped the index it
relied on).

**Why this step (now):** the plan is the proof. Without it, "add an index" is a guess, and guesses
during incidents add load. `EXPLAIN ANALYZE` executes the statement, so wrap anything other than a
`SELECT` in `BEGIN; ... ROLLBACK;`.

**Next step:** Step 4. If the plan does use an index but estimated and actual row counts differ
wildly (`rows=1` estimated, 500,000 actual), statistics are stale after a bulk load and
`ANALYZE orders;` is the fix.

**Step 4 — Roll back, or add the index without blocking writes.**

**Goal:** remove the cause with the least risk.

```bash
sudo -u postgres psql -d appdb -c "SET lock_timeout = '5s';" -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_status_created ON orders (customer_id, status, created_at DESC);"
sudo -u postgres psql -d appdb -c "EXPLAIN (ANALYZE) SELECT * FROM orders WHERE customer_id = 4242 AND status = 'paid' ORDER BY created_at DESC LIMIT 20;"
```

```
SET
CREATE INDEX
                                                                        QUERY PLAN
---------------------------------------------------------------------------------------------------------------------------------------------------------
 Limit  (cost=0.42..80.31 rows=20 width=34) (actual time=0.031..0.088 rows=20 loops=1)
   ->  Index Scan using idx_orders_customer_status_created on orders  (cost=0.42..80.31 rows=20 width=34) (actual time=0.030..0.084 rows=20 loops=1)
         Index Cond: ((customer_id = 4242) AND (status = 'paid'::text))
 Planning Time: 0.402 ms
 Execution Time: 0.117 ms
(5 rows)
```

**What it means:** the same query now takes 0.1 ms instead of 2,800 ms: the index finds exactly the
20 rows, already in `created_at` order.

**Why this step (now):** `CONCURRENTLY` builds the index without blocking writes (a plain
`CREATE INDEX` blocks every `INSERT` and `UPDATE` on the table for the whole build), and
`lock_timeout` stops it from queuing behind a long transaction. If you cannot fix it confidently
within minutes, **roll the release back first** (redeploy the previous image tag in Dokploy, see
[Deployment patterns](35-deployment-patterns.md)) and add the index calmly afterwards.

**Next step:** if `CREATE INDEX CONCURRENTLY` fails, it leaves an `INVALID` index behind (`\d orders`
shows it): drop it with `DROP INDEX CONCURRENTLY` and retry. Then add the index to the release's
migrations (section 11) so every environment matches. Step 5 covers MySQL.

**Step 5 — The MySQL version.**

**Goal:** the same three moves with MySQL's tools.

```bash
sudo pt-query-digest --since '2026-10-03 14:00:00' --limit 3 /var/log/mysql/mysql-slow.log | sed -n '/Profile/,/^$/p'
sudo mysql appdb -e "EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 4242 AND status = 'paid' ORDER BY created_at DESC LIMIT 20\G"
sudo mysql appdb -e "ALTER TABLE orders ADD INDEX idx_customer_status_created (customer_id, status, created_at), ALGORITHM=INPLACE, LOCK=NONE;"
```

```
# Profile
# Rank Query ID                            Response time    Calls R/Call V/M   Item
# ==== =================================== ================ ===== ====== ===== ==============
#    1 0x5A3F2B18C0FFEE0123456789ABCDEF01  3392.1120 88.4%  1212 2.7988  0.02 SELECT orders
#    2 0x77D1E2A3B4C5D6E7F8091A2B3C4D5E6F   274.5911  7.2%   612 0.4487  0.01 SELECT products
#    3 0x0C9B8A7F6E5D4C3B2A19080706050403    96.3440  2.5%    44 2.1896  0.05 SELECT orders

*************************** 1. row ***************************
EXPLAIN: -> Limit: 20 row(s)  (actual time=2788.104..2788.109 rows=20 loops=1)
    -> Sort: orders.created_at DESC, limit input to 20 row(s) per chunk  (actual time=2788.102..2788.105 rows=20 loops=1)
        -> Filter: ((orders.customer_id = 4242) and (orders.`status` = 'paid'))  (cost=101532.25 rows=9970) (actual time=31.204..2787.911 rows=21 loops=1)
            -> Table scan on orders  (cost=101532.25 rows=997040) (actual time=0.103..2711.381 rows=1000000 loops=1)
```

**What it means:** the same story: a full table scan of a million rows for 20 results.
`ALGORITHM=INPLACE, LOCK=NONE` builds the index while reads and writes continue; if the change
cannot be done that way, MySQL refuses the statement instead of silently locking the table.

**Why this step (now):** the digest, the plan and the online index are the MySQL versions of
Steps 2 to 4.

**Next step:** on replicas the index build starts only after it finishes on the source, so expect
replication lag about as long as the build. For very large tables use `gh-ost` or
`pt-online-schema-change`.

**After the incident**

- Review new queries in merge requests with `EXPLAIN` on production-sized data; a copy restored by
  the section 4 restore test is perfect for that.
- Compare `pg_stat_statements` (or the slow-log digest) before and after every release.
- Canary releases catch this with 5% of the traffic instead of 100%
  ([Deployment patterns](35-deployment-patterns.md)).

### Locks and blocked queries

**Level:** [L2 · Mid] · target: queue drained in 10 minutes

The scenario: at 16:05 every request that touches `orders` hangs, API workers pile up, and the
GitLab CI job `migrate-production` has been "running" for six minutes.

**Step 1 — Draw the blocking tree.**

**Goal:** find the root blocker, not just the victims.

```bash
sudo -u postgres psql -d appdb -c "SELECT a.pid, pg_blocking_pids(a.pid) AS blocked_by, a.state, a.wait_event_type, now() - a.xact_start AS xact_age, left(a.query, 55) AS query FROM pg_stat_activity a WHERE a.datname = 'appdb' AND (cardinality(pg_blocking_pids(a.pid)) > 0 OR a.pid IN (SELECT unnest(pg_blocking_pids(b.pid)) FROM pg_stat_activity b)) ORDER BY a.xact_start LIMIT 6;"
```

```
  pid  | blocked_by |        state        | wait_event_type |    xact_age     |                          query
-------+------------+---------------------+-----------------+-----------------+---------------------------------------------------------
 30112 | {}         | idle in transaction | Client          | 00:41:12.502113 | UPDATE orders SET status = 'shipped' WHERE id = 991
 30455 | {30112}    | active              | Lock            | 00:06:03.118001 | ALTER TABLE orders ADD COLUMN gift_note text
 30461 | {30455}    | active              | Lock            | 00:05:58.004211 | SELECT * FROM orders WHERE customer_id = 4242 ORDER BY
 30470 | {30455}    | active              | Lock            | 00:05:51.771020 | UPDATE orders SET status = 'paid' WHERE id = 7
 30477 | {30455}    | active              | Lock            | 00:05:49.002914 | SELECT * FROM orders WHERE id = 1882
 30481 | {30455}    | active              | Lock            | 00:05:47.660130 | INSERT INTO orders (customer_id, status, total) VALUES
(6 rows)
```

**What it means:** the root is pid 30112: `idle in transaction` for 41 minutes, holding the locks of
its `UPDATE`. The migration's `ALTER TABLE` (30455) needs an exclusive lock and waits for 30112, and
every other query on `orders` queues behind the `ALTER`, even plain `SELECT`s that do not conflict
with 30112 at all. That is the lock queue from section 1, "Locks and blocking".

**Why this step (now):** terminating random waiting sessions frees nothing; only the root (or the
exclusive lock request in the middle) releases the queue.

**Next step:** Step 2.

**Step 2 — Identify the root blocker before you end it.**

**Goal:** know whose work you are about to roll back.

```bash
sudo -u postgres psql -x -c "SELECT pid, usename, application_name, client_addr, backend_start, xact_start, state_change, query FROM pg_stat_activity WHERE pid = 30112;"
```

```
-[ RECORD 1 ]----+---------------------------------------------------
pid              | 30112
usename          | app
application_name | psql
client_addr      | 198.51.100.23
backend_start    | 2026-10-03 15:21:40.118823+00
xact_start       | 2026-10-03 15:24:02.502113+00
state_change     | 2026-10-03 15:24:02.611402+00
query            | UPDATE orders SET status = 'shipped' WHERE id = 991
```

**What it means:** a person using `psql` from a VPN address started a transaction at 15:24, ran an
`UPDATE` and never committed; perhaps a support fix interrupted by a meeting. Note that `query`
shows the session's last statement, not necessarily the one that took the lock.

**Why this step (now):** ending a forgotten interactive session is an easy decision; ending an
application's batch job needs its owner. Thirty seconds of reading prevents the wrong call.

**Next step:** Step 3.

**Step 3 — Release the queue.**

**Goal:** end the root, or step the migration aside.

```bash
# Option A, the usual one: end the abandoned transaction (its UPDATE is rolled back)
sudo -u postgres psql -c "SELECT pg_terminate_backend(30112);"
# Option B, when the blocker must finish (an important batch): cancel the migration instead
# sudo -u postgres psql -c "SELECT pg_cancel_backend(30455);"
```

```
 pg_terminate_backend
----------------------
 t
(1 row)
```

**What it means:** 30112 is gone and its `UPDATE` was rolled back. The `ALTER` got its lock and
finished in milliseconds, and the queue drained; rerun Step 1 and it returns `(0 rows)`.

**Why this step (now):** `pg_cancel_backend` cannot help an `idle in transaction` session, because
nothing is running to cancel; it takes `pg_terminate_backend`. Option B is right when the blocker
matters more than the migration: cancelling the `ALTER` releases the queue instantly, and the
migration runs later.

**Next step:** tell the `psql` user that their `UPDATE` was rolled back, then Step 4.

**Step 4 — Make the migration fail fast next time.**

**Goal:** a migration that gives up after a few seconds instead of taking the site down.

```bash
sudo -u postgres psql -d appdb -c "SET lock_timeout = '3s';" -c "ALTER TABLE orders ADD COLUMN gift_note text;"
```

```
SET
ERROR:  canceling statement due to lock timeout
```

**What it means:** with a blocker present, the `ALTER` now gives up after 3 seconds, no queue
forms behind it, and the pipeline job fails visibly and can retry later.

**Why this step (now):** lock waits are normal; queues behind exclusive locks are outages.
`lock_timeout` converts the second into a harmless retry, and section 11 puts it into every
migration job.

**Next step:** add the server-side guard
`ALTER DATABASE appdb SET idle_in_transaction_session_timeout = '10min';` so abandoned transactions
end by themselves, and give humans a read-only role by default (section 8). Step 5 covers MySQL.

**Step 5 — The MySQL version: metadata locks.**

**Goal:** the same root-blocker logic with MySQL's views.

```bash
sudo mysql -e "SELECT waiting_pid, waiting_query, blocking_pid, blocking_account, sql_kill_blocking_connection FROM sys.schema_table_lock_waits\G" | head -n 6
sudo mysql -e "SELECT trx_mysql_thread_id, trx_started, trx_state, trx_rows_locked, trx_query FROM information_schema.innodb_trx ORDER BY trx_started LIMIT 3;"
```

```
*************************** 1. row ***************************
                 waiting_pid: 918
               waiting_query: ALTER TABLE orders ADD COLUMN gift_note TEXT
                blocking_pid: 912
            blocking_account: app@192.0.2.50
sql_kill_blocking_connection: KILL 912
+---------------------+---------------------+-----------+-----------------+-----------+
| trx_mysql_thread_id | trx_started         | trx_state | trx_rows_locked | trx_query |
+---------------------+---------------------+-----------+-----------------+-----------+
|                 912 | 2026-10-03 15:24:02 | RUNNING   |               1 | NULL      |
+---------------------+---------------------+-----------+-----------------+-----------+
```

**What it means:** as in section 3, connection 912 sleeps with an open transaction (`trx_query` is
NULL: nothing is running), the `ALTER` waits for a metadata lock behind it, and every query on
`orders` waits behind the `ALTER`.

**Why this step (now):** the logic is identical, and the `sys` view even prints the `KILL`
statement for you. Unlike `sys.innodb_lock_waits`, this view has no `blocking_query` column, which
is why `innodb_trx` is the second command.

**Next step:** `KILL 912;` (or `KILL QUERY 918;` to step the migration aside). In migrations, run
`SET SESSION lock_wait_timeout = 5;` before any DDL: the default is 31,536,000 seconds, one year.

**After the incident**

- The long-transaction alert from section 9.
- `lock_timeout` (PostgreSQL) or `lock_wait_timeout` (MySQL) in every migration job (section 11).
- `idle_in_transaction_session_timeout`, and read-only roles for people.

### App can't connect to the database

**Level:** [L1 · Junior] → [L2 · Mid] · target: gate found in 10 minutes

The scenario: `shop-api` has moved from the old Apache VM (192.0.2.50) to the Dokploy host
(192.0.2.52). The new containers cannot reach `db1.example.internal`. This walk follows the seven
gates from section 2 ("listen_addresses and pg_hba.conf"), from the application's side.

**Step 1 — Get the exact error, from the application's point of view.**

**Goal:** turn "it can't connect" into one gate.

```bash
docker service logs --since 10m shop-api-4m9tqz 2>&1 | grep -iE 'connect|password|pg_hba|refused|timed out|resolve' | tail -n 2
```

```
shop-api-4m9tqz.1.k2v9x8d1q3@dok1    | psycopg.OperationalError: connection failed: connection to server at "db1.example.internal" (192.0.2.21), port 5432 failed: Connection timed out
shop-api-4m9tqz.2.p7m4n2b8w6@dok1    | psycopg.OperationalError: connection failed: connection to server at "db1.example.internal" (192.0.2.21), port 5432 failed: Connection timed out
```

**What it means:** the name resolved to 192.0.2.21, so gate 1 (DNS) passed, and the TCP connection
timed out: gate 2, the network or a firewall.

**Why this step (now):** the exact error text eliminates five of the seven gates in ten seconds;
the table in section 2 maps every message to its gate.

**Next step:** `could not translate host name` → Step 2. `timed out` or `No route to host` →
Step 3. `Connection refused` → Step 4. `no pg_hba.conf entry`, `password authentication failed` or
`does not exist` → Step 5. `too many clients` → the first playbook in this section.

**Step 2 — DNS from inside the container (gate 1).**

**Goal:** resolve the name the way the application does.

```bash
docker exec $(docker ps -q -f name=shop-api | head -n 1) getent ahosts db1.example.internal
docker exec $(docker ps -q -f name=shop-api | head -n 1) cat /etc/resolv.conf
```

```
192.0.2.21      STREAM db1.example.internal
192.0.2.21      DGRAM
192.0.2.21      RAW
search example.internal
nameserver 127.0.0.11
options ndots:0
```

**What it means:** inside the container the name resolves correctly through Docker's embedded DNS
(127.0.0.11). When this fails while the host resolves fine, the usual cause is an internal zone
that only the host's resolver knows: see [DNS](08-dns.md) and [Learn: Docker](30-learn-docker.md).

**Why this step (now):** the application resolves names inside its own network namespace with its
own `resolv.conf`; a test on the host proves nothing about the container.

**Next step:** Step 3 (our error was a timeout).

**Step 3 — Network path and firewall (gate 2).**

**Goal:** find where the packets stop.

```bash
# from the application's network namespace
docker run --rm --network container:$(docker ps -q -f name=shop-api | head -n 1) nicolaka/netshoot nc -vz -w 3 192.0.2.21 5432
# on db1: do the packets arrive, and what does the firewall allow?
sudo tcpdump -ni any -c 3 'tcp port 5432 and host 192.0.2.52'
sudo ufw status | grep 5432
```

```
nc: connect to 192.0.2.21 port 5432 (tcp) timed out: Operation now in progress
14:02:11.113201 eth0  In  IP 192.0.2.52.48122 > 192.0.2.21.5432: Flags [S], seq 1712044127, win 64240, options [mss 1460,sackOK,TS val 3311 ecr 0,nop,wscale 7], length 0
14:02:12.140877 eth0  In  IP 192.0.2.52.48122 > 192.0.2.21.5432: Flags [S], seq 1712044127, win 64240, options [mss 1460,sackOK,TS val 4338 ecr 0,nop,wscale 7], length 0
14:02:14.188913 eth0  In  IP 192.0.2.52.48122 > 192.0.2.21.5432: Flags [S], seq 1712044127, win 64240, options [mss 1460,sackOK,TS val 6386 ecr 0,nop,wscale 7], length 0
5432/tcp                   ALLOW       192.0.2.50
5432/tcp                   ALLOW       192.0.2.51
```

**What it means:** SYN packets from 192.0.2.52 (the Dokploy host; containers leave through the
host's address) reach db1 and are never answered: UFW drops them, because its allowlist still names
the old Apache VM and its neighbour, not the new host. A migration checklist item nobody wrote down.

**Why this step (now):** a capture on the receiving side separates "packets never arrive" (routing,
a firewall in between) from "packets arrive and are dropped here" (the host firewall) with one
command.

**Next step:** `sudo ufw allow from 192.0.2.52 to any port 5432 proto tcp comment 'dokploy host'`,
rerun the `nc`, and continue with the step that matches the new error, if any. If no packets
arrive at all, follow the network walk in [Site down](25-playbook-site-down.md).

**Step 4 — The listen address (gate 3).**

**Goal:** confirm PostgreSQL listens where the clients connect.

```bash
sudo ss -ltnp 'sport = :5432'
sudo -u postgres psql -Atc "SHOW listen_addresses;"
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
LISTEN 0      200        127.0.0.1:5432      0.0.0.0:*    users:(("postgres",pid=812,fd=6))
localhost
```

**What it means:** PostgreSQL listens on loopback only (Ubuntu's default `listen_addresses =
'localhost'`), so remote clients get `Connection refused`. Set
`listen_addresses = 'localhost,192.0.2.21'` and **restart**: this setting cannot be reloaded. For
MySQL the equivalent is `bind-address`, also a restart.

**Why this step (now):** "refused" means the host answered and nothing listens on that address and
port; no firewall change can fix it.

**Next step:** Step 5.

**Step 5 — pg_hba, authentication and database (gates 4 to 6).**

**Goal:** read PostgreSQL's own reason for refusing.

```bash
sudo grep -E 'no pg_hba.conf entry|password authentication failed|does not exist' /var/log/postgresql/postgresql-16-main.log | tail -n 2
sudo -u postgres psql -c "SELECT line_number, type, database, user_name, address, auth_method, error FROM pg_hba_file_rules WHERE (type LIKE 'host%' AND address NOT IN ('127.0.0.1', '::1')) OR error IS NOT NULL;"
```

```
2026-10-03 14:09:31.552 UTC [9912] app@appdb FATAL:  no pg_hba.conf entry for host "192.0.2.52", user "app", database "appdb", SSL encryption
2026-10-03 14:09:31.561 UTC [9913] app@appdb FATAL:  no pg_hba.conf entry for host "192.0.2.52", user "app", database "appdb", no encryption
 line_number |  type   | database | user_name |  address   |  auth_method  | error
-------------+---------+----------+-----------+------------+---------------+-------
         118 | hostssl | {appdb}  | {app}     | 192.0.2.50 | scram-sha-256 |
         119 | hostssl | {appdb}  | {app}     | 192.0.2.51 | scram-sha-256 |
(2 rows)
```

**What it means:** the network works now, and PostgreSQL itself refuses: its rules list the old app
hosts only. (The pair of lines is the client trying TLS first, then without.) Add
`hostssl appdb app 192.0.2.52/32 scram-sha-256`, run `SELECT pg_reload_conf();`, and check that
`pg_hba_file_rules` shows the new line with an empty `error`. If the log says
`password authentication failed for user "app"` instead, its `DETAIL` line names the
`pg_hba.conf` line that matched; then compare the secret the container really has (the Dokploy
environment) and check that a password inside a `postgresql://` URL is percent-encoded. MySQL's
equivalents are `ERROR 1130` (no account for this host) and `ERROR 1045` (wrong password for the
account that matched), section 3.

**Why this step (now):** gates 4 to 6 are PostgreSQL's own decisions, and its log states the reason
exactly, while the application often reports only "connection failed".

**Next step:** Step 6.

**Step 6 — Prove the whole path, then make it repeatable.**

**Goal:** confirm from the application's own network namespace, before declaring victory.

```bash
docker run --rm --network container:$(docker ps -q -f name=shop-api | head -n 1) postgres:16 \
  pg_isready -h db1.example.internal -p 5432 -d appdb -U app
```

```
db1.example.internal:5432 - accepting connections
```

**What it means:** from inside the application's network, DNS, the route, the firewall and the
listener all work. `pg_isready` does not log in, so it does not test gates 4 to 6; the application's
own health check (or a real `psql` login) completes the proof.

**Why this step (now):** the incident is over when the real client path works, not when one gate
was fixed.

**Next step:** add this to the migration checklist used for the Apache to Dokploy moves
([Apache 443 and Dokploy](21-case-apache-443-dokploy.md)): every new application host needs DNS,
firewall and `pg_hba.conf` entries on every database it uses, tested with this command **before**
the cutover. Keep UFW rules and `pg_hba.conf` lines as code (for example in Ansible), named by role,
not just by IP.

### Restore a single table

**Level:** [L2 · Mid] → [L3 · Senior] · target: data back the same day

The scenario: at 11:52 a support script ran `DELETE FROM orders WHERE created_at < '2026-10-01'`,
missing its `AND status = 'cancelled'`. Every order older than 1 October is gone. The rest of the
database has kept changing since, so rolling the whole database back is not an option.

**Step 1 — Stop the damage and pin the time.**

**Goal:** no further damage, and an exact timestamp.

```bash
sudo grep 'DELETE FROM orders' /var/log/postgresql/postgresql-16-main.log | tail -n 1
sudo -u postgres psql -d appdb -Atc "SELECT count(*) FROM orders WHERE created_at < '2026-10-01';"
```

```
2026-10-03 11:52:07.311 UTC [7711] app@appdb LOG:  duration: 9182.412 ms  statement: DELETE FROM orders WHERE created_at < '2026-10-01'
0
```

**What it means:** the statement was logged because it ran longer than
`log_min_duration_statement`. The log time is when it **finished**; after 9.2 seconds of running, it
started around 11:51:58. All the older orders are gone. Disable the script (and any cron job that
runs it) and tell support before anything else.

**Why this step (now):** the time decides which backup can help, and a script that runs again
doubles the work.

**Next step:** Step 2.

**Step 2 — Choose the source.**

**Goal:** the cheapest source that meets the RPO for **these** rows.

```bash
sudo ls -lt /var/backups/db/ | head -n 3
sudo -u postgres psql -Atc "SELECT last_archived_time FROM pg_stat_archiver;"
```

```
total 6.2G
-rw------- 1 postgres postgres 1.6G Oct  3 02:07 appdb-2026-10-03_0200.dump
-rw------- 1 postgres postgres 1.6G Oct  2 02:07 appdb-2026-10-02_0200.dump
2026-10-03 11:58:01.442+00
```

**What it means:** two possible sources:

| Source | Gives you | Lost for these rows |
|---|---|---|
| This morning's `pg_dump` (02:00) | the table as of 02:00 | changes to these old rows between 02:00 and 11:51 |
| Base backup + WAL archive (archiving is current) | the table as of 11:51:57, by PITR on a side cluster (section 4) | nothing |

The deleted rows are orders older than 1 October; they rarely change, so the 02:00 dump is good
enough and is the fastest path. For recent or frequently changing rows, use PITR.

**Why this step (now):** the right source depends on the rows, not on the database as a whole.

**Next step:** Step 3 with the dump (or the PITR lab in section 4, then Step 4 from the side
cluster).

**Step 3 — Restore the table into a scratch database.**

**Goal:** a copy you can inspect, away from production.

```bash
sudo -u postgres createdb restore_orders
sudo -u postgres pg_restore -d restore_orders -t orders --no-owner /var/backups/db/appdb-2026-10-03_0200.dump
sudo -u postgres psql -d restore_orders -Atc "SELECT count(*) FROM orders WHERE created_at < '2026-10-01';"
```

```
400213
```

**What it means:** the scratch database holds `orders` as it was at 02:00, including the 400,213
deleted rows.

**Why this step (now):** never restore over production. `-t orders` restores only the table's
definition and rows (no indexes or constraints), which is all a scratch copy needs.

**Next step:** Step 4.

**Step 4 — Copy back only the missing rows.**

**Goal:** put back exactly what was deleted, safely and repeatably.

```bash
sudo -u postgres psql -d restore_orders -c "\copy (SELECT * FROM orders WHERE created_at < '2026-10-01') TO '/var/lib/postgresql/orders_restore.csv' WITH (FORMAT csv)"
sudo -u postgres psql -d appdb -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;
CREATE TEMP TABLE orders_restore (LIKE orders);
\copy orders_restore FROM '/var/lib/postgresql/orders_restore.csv' WITH (FORMAT csv)
INSERT INTO orders
SELECT r.* FROM orders_restore r
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.id = r.id);
SELECT count(*) AS now_present FROM orders WHERE created_at < '2026-10-01';
COMMIT;
SQL
```

```
COPY 400213
BEGIN
CREATE TABLE
COPY 400213
INSERT 0 400213
 now_present
-------------
      400213
(1 row)

COMMIT
```

**What it means:** all 400,213 rows are back, inserted in one transaction, skipping any id that
already exists.

**Why this step (now):** `NOT EXISTS` makes the step safe to run twice, and the single transaction
makes it all or nothing. Watch for foreign keys: if other tables referenced `orders` with
`ON DELETE CASCADE`, their rows were deleted too and must be restored the same way, parents first.
The CSV contains customer data: delete it when you are done.

**Next step:** Step 5.

**Step 5 — Verify, clean up, and close the hole.**

**Goal:** confirmation by someone who knows the data, and no leftovers.

```bash
sudo -u postgres psql -d appdb -c "SELECT min(created_at), max(created_at), count(*) FROM orders WHERE created_at < '2026-10-01';"
sudo -u postgres dropdb restore_orders
sudo rm /var/lib/postgresql/orders_restore.csv
```

```
            min            |            max             | count
---------------------------+----------------------------+--------
 2025-10-03 12:14:51.22+00 | 2026-09-30 23:59:41.903+00 | 400213
(1 row)
```

**What it means:** the range and the count match the scratch copy. Ask the application owner to
spot-check a few of the restored orders in the UI.

**Why this step (now):** "restored" is a claim until someone who knows the data confirms it, and
scratch copies of customer data must not linger.

**Next step:** the postmortem. Why could a support script delete 400,000 rows? Typical actions:
support tools get a role without `DELETE` (section 8); destructive scripts run inside `BEGIN` and
check the affected row count before `COMMIT`; and the time this restore took goes into your RTO
numbers (section 4).

**The MySQL version.** Restore the dump into a scratch schema on the same server
(`sudo mysql -e "CREATE DATABASE restore_orders"`, then load the dump into it), and copy the rows
across schemas, which MySQL allows within one server:
`INSERT INTO appdb.orders SELECT r.* FROM restore_orders.orders r WHERE r.created_at < '2026-10-01' AND NOT EXISTS (SELECT 1 FROM appdb.orders o WHERE o.id = r.id);`.
For an exact copy as of 11:51:57, restore the physical backup on a scratch instance and replay
binlogs up to the `DELETE` (section 4), then copy from there.

---

## 11. Schema migrations in CI/CD

> 📚 **Study path:** 1) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab (tests and services), then Continuous Deployment (environments) ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 2) Note: [Deployment patterns](35-deployment-patterns.md) for rolling, blue-green and canary releases, which are exactly why schema changes must be backward compatible · 3) KodeKloud: *Fundamentals of SRE* — Change Management for Reliability ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · 4) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) for the pipeline itself · 5) Read: [GitLab change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/) for a real change-request format · 6) Practice: the expand/contract lab below, then add a migration job to a test pipeline.

Application code can be rolled back in seconds; data cannot. That asymmetry is the whole subject
of this section. A deploy pipeline that ships code and schema changes together is only safe when
every schema change is compatible with both the old and the new code, takes no lock that stalls
the site, runs exactly once, and has a plan for when it fails halfway.

### Expand and contract

**Level:** [L3 · Senior] · about 60 minutes

**Concept.** During a rolling or blue-green deploy, the old release (N) and the new one (N+1) run
at the same time against **one** schema; during a rollback, release N runs against N+1's schema.
So every schema change must work with both. The pattern that guarantees it is **expand and
contract**, spread over several releases:

1. **Expand:** add the new thing (column, table, index) without removing or changing the old one.
2. **Migrate:** the code writes both, data is backfilled in batches, then reads switch to the new
   thing.
3. **Contract:** once no running release uses the old thing, remove it, in a later release.

Renaming `customer_id` to `client_id` the safe way:

| Release | Schema change | Application | Can roll back to the previous release? |
|---|---|---|---|
| N+1 | add `client_id` (nullable) | writes both columns, reads `customer_id` | yes |
| N+2 | backfill `client_id` in batches; add its index concurrently | writes both, reads `client_id` | yes |
| N+3 | none | writes and reads only `client_id` | yes, to N+2 |
| N+4 | drop `customer_id` | unchanged | only by restoring data: the contract step is the point of no return |

A backfill runs in small transactions, so it never holds locks for long or creates one huge
transaction for the replicas to replay:

```sql
-- repeat until it reports UPDATE 0; each run is one short transaction
UPDATE orders SET client_id = customer_id
WHERE id IN (SELECT id FROM orders WHERE client_id IS NULL LIMIT 10000);
```

Rules that follow from the pattern:

- Never rename or drop in the same release as the code change that stops using the old name.
- Treat production migrations as **forward-only**. "Down" migrations are rarely safe once real
  data has been written; fix forward, and make the application roll-back-able instead.
- Add `NOT NULL` columns as nullable (or with a constant default), backfill, then add the
  constraint (next topic).

**See it on a real system: even "instant" DDL takes the strongest lock.** In one session:

```bash
sudo -u postgres psql -d appdb -c "BEGIN;" -c "ALTER TABLE orders ADD COLUMN note text;" -c "SELECT locktype, relation::regclass, mode, granted FROM pg_locks WHERE relation = 'orders'::regclass;" -c "ROLLBACK;"
```

```
BEGIN
ALTER TABLE
 locktype | relation |        mode         | granted
----------+----------+---------------------+---------
 relation | orders   | AccessExclusiveLock | t
(1 row)

ROLLBACK
```

→ Adding a nullable column only changes the catalog, so it is fast, but for those milliseconds (or
for as long as the transaction stays open) it holds `AccessExclusiveLock`, which blocks even plain
`SELECT`s on the table. If it has to wait for that lock, everyone queues behind it: the locks
playbook in section 10.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Simulate release N: a loop that queries the old column, for example
`while true; do psql -h 127.0.0.1 -U app appdb -Atc "SELECT count(*) FROM orders WHERE customer_id = 4242;"; sleep 1; done`.

**Step 2 — Break it.** "Release N+1" renames the column in one step:
`ALTER TABLE orders RENAME COLUMN customer_id TO client_id;`. The loop immediately fails with
`ERROR:  column "customer_id" does not exist`, which is what every old instance does during a
rolling deploy, and what a rollback of the code would do too.

**Step 3 — Fix it.** Rename it back, then do it the expand/contract way: add `client_id`, backfill
in batches with the loop above until `UPDATE 0`, switch the reading loop to `client_id`, and only
then drop `customer_id`. The reading loop never fails.

**How it breaks**

| Symptom | Cause | Prevention |
|---|---|---|
| `column "…" does not exist` errors during a rolling deploy | rename or drop in the same release | expand/contract |
| Rollback of the app fails against the new schema | the migration was not backward compatible | review every migration against release N |
| Replicas lag for an hour after a migration | a backfill done as one huge transaction | batches of a few thousand rows |
| "Down" migration loses data written since the deploy | treating schema rollback like code rollback | forward-only fixes |

**Why it matters for troubleshooting.** Many "the deploy broke the site" incidents are schema
incompatibilities that only exist while two releases overlap. Knowing the pattern lets you read a
migration and predict the outage before it happens.

**Next step:** which DDL statements are safe on a busy table, and how to make the others safe.

### Safe and unsafe DDL

**Level:** [L3 · Senior] · about 45 minutes

**Concept.** Every DDL statement takes a lock; what matters is which lock, for how long, and
whether it rewrites or scans the table. PostgreSQL 16:

| Operation | Lock and work | Risk | Safer way |
|---|---|---|---|
| `ADD COLUMN`, nullable or with a constant default | ACCESS EXCLUSIVE, catalog only (constant defaults are metadata-only since PostgreSQL 11) | queues behind long transactions | `lock_timeout` and retry |
| `ADD COLUMN ... DEFAULT now()` or another volatile default | ACCESS EXCLUSIVE plus a full table rewrite | minutes of total blocking | add it nullable, backfill in batches, then set the default |
| `CREATE INDEX` | SHARE lock (blocks writes) for the whole build | writes stop | `CREATE INDEX CONCURRENTLY` (outside a transaction; on failure drop the `INVALID` index) |
| `DROP INDEX` | ACCESS EXCLUSIVE | brief, but queues | `DROP INDEX CONCURRENTLY` |
| `ALTER COLUMN ... TYPE` (most changes) | ACCESS EXCLUSIVE plus a rewrite | a long outage | new column, backfill, switch, drop |
| `SET NOT NULL` | ACCESS EXCLUSIVE plus a full scan | blocking scan | `ADD CONSTRAINT ... CHECK (col IS NOT NULL) NOT VALID`, then `VALIDATE CONSTRAINT`, then `SET NOT NULL` (PostgreSQL 12+ skips the scan) |
| `ADD FOREIGN KEY` | SHARE ROW EXCLUSIVE on both tables plus a validation scan | blocks writes | add it `NOT VALID`, then `VALIDATE CONSTRAINT` (a weaker lock) |
| `RENAME` a column or table, `DROP COLUMN` | ACCESS EXCLUSIVE, fast | breaks the release still running | expand/contract |

MySQL 8.0 (InnoDB):

| Operation | How it runs | Notes |
|---|---|---|
| `ADD COLUMN` | `ALGORITHM=INSTANT` (8.0.12+, at any position from 8.0.29) | still a brief metadata lock; a table allows a limited number of instant changes (64 row versions) before a rebuild |
| `ADD INDEX` | `ALGORITHM=INPLACE, LOCK=NONE` | online on the source; replicas apply it afterwards, so they lag by the build time |
| Change a column's type | `ALGORITHM=COPY` (table rebuild, writes blocked) | use `gh-ost` or `pt-online-schema-change` |
| `DROP COLUMN` | `INSTANT` from 8.0.29, otherwise an in-place rebuild | as with PostgreSQL, stop using it first |

Always spell out `ALGORITHM` and `LOCK`: if MySQL cannot do the change that way, it refuses the
statement instead of silently choosing a blocking method. And because MySQL DDL is **not**
transactional, a migration file with three statements that fails on the second leaves the first
one applied: keep one DDL statement per migration.

The two timeouts every migration session should set:

```sql
-- PostgreSQL: give up quickly instead of queuing the site behind you, and cap runaway statements
SET lock_timeout = '5s';
SET statement_timeout = '15min';
-- MySQL: the default lock_wait_timeout is one year
SET SESSION lock_wait_timeout = 5;
```

**Hands-on lab (test VM only)**

**Step 1 — Build.** Keep `pgbench -h 127.0.0.1 -U app -c 4 -T 600 appdb` running, and in another
terminal open a transaction that touches `orders` and leave it open (`BEGIN; UPDATE orders SET
status = status WHERE id = 1;`).

**Step 2 — Break it.** Run `CREATE INDEX idx_orders_created ON orders (created_at);` without
`CONCURRENTLY` and watch inserts into `orders` stop (try one) until it finishes. Then run
`ALTER TABLE orders ADD COLUMN note text;` without a `lock_timeout` and watch it wait for the open
transaction while new queries pile up behind it.

**Step 3 — Fix it.** Cancel both. Repeat with `CREATE INDEX CONCURRENTLY` (inserts continue) and
with `SET lock_timeout = '5s'` before the `ALTER` (it fails after 5 seconds with
`canceling statement due to lock timeout`, and nothing queues). Commit the open transaction, run
the `ALTER` again: it succeeds instantly.

**How it breaks**

| Error text | Cause | Fix |
|---|---|---|
| `ERROR:  CREATE INDEX CONCURRENTLY cannot run inside a transaction block` | the migration tool wraps every migration in a transaction | mark that migration as non-transactional (every major tool has an option) |
| `ERROR:  canceling statement due to lock timeout` | a blocker was present, as intended | retry later (the pipeline's `retry`), find the blocker if it persists |
| `ERROR:  canceling statement due to statement timeout` | the change needs a rewrite | redesign with expand/contract |
| `ERROR 1846 (0A000): ALGORITHM=INPLACE is not supported` | MySQL cannot do this change online | `gh-ost` or `pt-online-schema-change` |

**Why it matters for troubleshooting.** When the site stalls during a deploy, the first question is
"which DDL is running, and which lock does it hold or want?". This table is the answer key.

**Next step:** run migrations from the pipeline, once, with these protections built in.

### Migrations in GitLab CI

**Level:** [L3 · Senior] · about 60 minutes

**Concept.** Where and how migrations run decides whether they are boring:

- **Once, from one place.** Run them as their own pipeline job before the deploy, not in the
  application container's entrypoint: with six replicas starting together, six processes would
  race to migrate, and a health check could kill a container in the middle of a migration. Most
  migration tools (Flyway, Liquibase, Alembic, Django, Rails, Prisma, golang-migrate) keep a
  history table and take a lock so that two runs cannot overlap; GitLab's `resource_group` adds the
  same guarantee at the pipeline level.
- **Connected directly, not through a transaction pooler.** Advisory locks and session settings do
  not survive PgBouncer's transaction mode (section 2); give the migration job a direct connection
  or a session-mode pool.
- **With protections set.** `lock_timeout` and `statement_timeout` for every migration session (the
  `PGOPTIONS` environment variable passes them to any libpq client), and a check that a recent,
  restore-tested backup exists before anything runs.
- **Tested before production.** The test stage applies all migrations to an empty database (a
  GitLab CI service container) and runs the **previous** release's tests against the new schema,
  which is a direct test of backward compatibility.

```yaml
# .gitlab-ci.yml (excerpt). ./bin/migrate stands for your tool: alembic upgrade head, flyway migrate,
# rails db:migrate, prisma migrate deploy, ...
stages: [build, test, migrate, deploy]

variables:
  IMAGE: harbor.example.com/shop/api:$CI_COMMIT_SHORT_SHA

migration-test:
  stage: test
  image: $IMAGE
  services:
    - name: postgres:16
      alias: db
  variables:
    POSTGRES_DB: appdb
    POSTGRES_USER: app
    POSTGRES_PASSWORD: ci-only-password
    DATABASE_URL: postgresql://app:ci-only-password@db:5432/appdb
  script:
    - ./bin/migrate up                      # every migration applies cleanly from scratch
    - ./bin/test --suite db                 # this release's tests
    - ./bin/test-previous-release --suite db   # the previous release against the new schema

migrate-production:
  stage: migrate
  image: $IMAGE
  environment: production
  resource_group: production-db             # never two migration jobs at the same time
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
  variables:
    PGOPTIONS: "-c lock_timeout=5s -c statement_timeout=30min"
  script:
    - ./bin/check-backup-age --max-hours 26    # refuse to run without a fresh, restore-tested backup
    - ./bin/migrate up
  retry:
    max: 2
    when: script_failure                    # a lock timeout is retried, not escalated

deploy-production:
  stage: deploy
  image: curlimages/curl:8.10.1
  environment: production
  needs: [migrate-production]
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - curl -fsS -X POST "$DOKPLOY_DEPLOY_WEBHOOK"   # the app's deploy webhook, a masked CI/CD variable
```

`DATABASE_URL` for production comes from a **masked and protected** CI/CD variable available only
to protected branches, and it uses the migration identity from section 8, not the application's.
`./bin/check-backup-age` can be as simple as reading the `db_backup_last_success_timestamp_seconds`
and `db_restore_test_last_success_timestamp_seconds` metrics from Prometheus.

**See it on a real system.** In the job log of a successful run:

```
$ ./bin/check-backup-age --max-hours 26
OK: last backup 2026-10-03T02:07:12Z (12h ago), last restore test 2026-09-27T05:21:40Z
$ ./bin/migrate up
INFO  [migrate] Running upgrade 20260921_add_client_id -> 20261003_backfill_client_id
INFO  [migrate] Running upgrade 20261003_backfill_client_id -> 20261003_idx_client_id (no transaction)
Job succeeded
```

→ The guard passed, two migrations ran, and the index migration ran outside a transaction because
it uses `CREATE INDEX CONCURRENTLY`.

**Hands-on lab (lab GitLab project, or the KodeKloud [CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd))**

**Step 1 — Build.** Add the `migration-test` job to a test project with one migration that adds a
nullable column, and watch it pass with the `postgres:16` service.

**Step 2 — Break it.** Add a migration that renames a column. The "previous release" tests fail in
`migration-test`, before anything reached production. Then hold an open transaction on the lab
database and run the production-style job against it: it fails with
`canceling statement due to lock timeout`, retries, and fails again while the site stays up.

**Step 3 — Fix it.** Replace the rename with the expand step from the first topic, commit the open
transaction, rerun the job.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Two replicas both ran the migration; one failed with a duplicate column error | migrations in the container entrypoint | a single pipeline job, `resource_group` |
| The migration job hangs for the whole lock wait, the site is down meanwhile | no `lock_timeout` | `PGOPTIONS` as above, `lock_wait_timeout` for MySQL |
| `advisory lock` errors or two concurrent runs through PgBouncer | transaction pooling | direct connection for migrations |
| MySQL migration failed halfway; the history table says "not applied" but one column exists | DDL is not transactional in MySQL | one DDL statement per migration; fix forward |
| The new release deployed although the migration failed | `deploy` does not depend on `migrate` | `needs:` and the default "stop on failure" |

**Why it matters for troubleshooting.** A pipeline that runs migrations this way turns the worst
deploy incidents (a stalled site, a half-applied schema, a race between replicas) into a red job
and a retry.

**Next step:** database changes that are not migrations: patches, settings and maintenance.

### Database changes as changes

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 30 minutes

**Concept.** Package updates, configuration changes, failovers and major upgrades are changes like
any deploy, and they deserve the same discipline. One trap first: on Ubuntu, `unattended-upgrades`
installs security updates daily, and a PostgreSQL or MySQL package update **restarts the
database** at whatever time the timer runs. For a small database that restarts in two seconds that
may be acceptable. For anything important, exclude the database packages and patch them in a
planned window (replicas first, then a switchover):

```
// /etc/apt/apt.conf.d/51unattended-upgrades-databases
Unattended-Upgrade::Package-Blacklist {
    "postgresql-";
    "mysql-server";
    "redis-server";
};
```

```bash
grep -E 'postgresql|mysql|redis' /var/log/unattended-upgrades/unattended-upgrades.log | tail -n 3
grep -E 'postgresql|mysql' /var/log/apt/history.log | tail -n 3
```

Excluded packages still need patching: put a monthly database patch window in the calendar, or
the exclusion turns into months of missed security fixes.

**A checklist for any database change** (adapt it into your change-request template):

- What changes and why, in one paragraph a non-DBA understands.
- The newest successful backup and restore test, with times.
- Rehearsal: done on a restored copy with production-sized data, and how long it took.
- Locks taken, expected replication lag, and the timeouts set.
- Rollback or roll-forward plan, and the point of no return.
- The window, chosen away from backups, batch jobs and traffic peaks.
- Who watches which dashboard during the change, and the stop criteria.
- Who is informed before and after.

**Hands-on lab.** Write a change request in GitLab's format (criticality, steps, verification,
rollback) for "minor PostgreSQL update on db1 and db2", following the study path's link. Then
execute it on the lab pair: update db2, switch over, update db1, switch back, and record the
write downtime your pgbench client saw.

**Why it matters for troubleshooting.** "What changed?" is the first question of every incident.
When every database change goes through a written change, the answer is a search away instead of
a guess.

**Next step:** prove what you learned: the exit tests.

---

## 12. Self-check / exit test

> 📚 **Study path:** 1) Practice first: run each timed task below on the lab VMs without notes, then check yourself against the referenced section · 2) KodeKloud: *Linux Challenges* (free), as timed warm-ups between attempts ([course](https://kodekloud.com/courses/linux-challenges)) · 3) KodeKloud: [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) as the daily morning rep · 4) Note: the [career ladder](40-career-ladder.md) for how these tests map to your stage, and [SadServers](https://sadservers.com/scenarios) for timed scenarios on real broken servers.

Use these tests to decide when to move on. Answer the questions aloud or in writing without notes,
then check against the referenced section. Run the timed tasks on the lab VMs after someone else
(or a script) has prepared the breakage, so you do not know the answer in advance. Pass a stage's
test twice, a week apart, before you call it done.

### Fresher exit test

**Level:** [L0 · Fresher]

**Questions**

1. Name the four things that define a PostgreSQL server on Ubuntu (port, data directory,
   configuration files, log file), and the same four for MySQL. (sections 0, 2, 3)
2. What is the difference between a server (a "cluster" in PostgreSQL), a database, a schema and a
   table? (section 1)
3. Write the `psql` command that connects to `appdb` on db1 over TCP as `app`, and the `mysql`
   equivalent. (sections 2, 3)
4. What does `Connection refused` tell you that `Connection timed out` does not? (section 2)
5. Why is a replica not a backup? (section 4)
6. PostgreSQL does not start after a configuration change. Which file do you read first? (section 2)

**Timed tasks**

| Task | Time | Pass when |
|---|---|---|
| Install PostgreSQL 16 on a fresh Ubuntu 24.04 VM, create role `app` and database `appdb`, connect over TCP with a password | 15 min | `\conninfo` shows a TCP connection as `app` |
| Find the port, data directory, configuration files and log of PostgreSQL and MySQL without searching the web | 10 min | eight answers, each proven by a command |
| Dump `appdb` and restore it into `appdb_restore` | 15 min | row counts match |

**Ready for the next stage when** you can connect to, inspect and restore a database on your own,
and you explain every error message you meet before searching for it.

### Junior exit test

**Level:** [L1 · Junior]

**Questions**

1. List the seven gates of a database connection in order, with the error text of three of them.
   (section 2)
2. `pg_hba.conf` has a `reject` line above your `host` line. What happens, and why? (section 2)
3. In MySQL, why can `'app'@'%'` and `'app'@'192.0.2.50'` have different passwords, and which one
   is used for a client at 192.0.2.50? (section 3)
4. What does `pg_dump` not include, and what breaks if you forget it? (section 4)
5. What does `idle in transaction` mean, and why is it dangerous? (section 1)
6. What happens to `POSTGRES_PASSWORD` after the first start of a container? (section 7)
7. Redis answers `DENIED ... protected mode`. What are the two correct fixes? (section 6)

**Timed tasks**

| Task | Time | Pass when |
|---|---|---|
| Someone breaks one gate on db1 (listen address, UFW, `pg_hba.conf` or the password); make app1 connect | 20 min | fixed from the error text alone, with the gate named |
| Nightly dump with a systemd timer, plus a restore on db2, which has no `app` role | 30 min | the restore works because the globals were restored first |
| A MySQL account for app1 with data-only rights | 15 min | `SELECT` and `INSERT` work, `DROP TABLE` is refused |
| Redis bound to the private IP with an ACL user for the app | 15 min | app1 gets `PONG`, `FLUSHALL` is refused |

**Ready for the next stage when** "the app can't connect" and "restore last night's backup" are
routine for you, and you have restored more backups than you have taken.

### Mid-level exit test

**Level:** [L2 · Mid]

**Questions**

1. Explain the lock queue: why does a fast `ALTER TABLE` stall plain `SELECT`s? (sections 1, 10)
2. `pg_cancel_backend` or `pg_terminate_backend` for an `idle in transaction` blocker, and why?
   (section 10)
3. Name the four things that keep WAL in `pg_wal`. (section 1)
4. What does a large gap between `Rows_examined` and `Rows_sent` tell you? (section 3)
5. Why is raising `max_connections` usually the wrong fix? Do the arithmetic for 5 replicas,
   4 workers and a pool of 10 against `max_connections = 100`. (section 2)
6. Redis returns `MISCONF`. What are the likely causes, and what is the wrong fix? (section 6)
7. Which `maxmemory-policy` for a job queue, which for a cache, and why? (section 6)
8. Why does a published Docker port ignore `ufw deny`, and what do you do instead? (sections 7, 8)

**Timed tasks** (each from a prepared breakage, 20 minutes, no notes)

| Breakage | Pass when |
|---|---|
| Too many connections (pgbench with 120 clients against 100) | service restored without a restart, arithmetic explained |
| Lock outage (an open transaction plus an `ALTER TABLE`) | root blocker found within 5 minutes, queue drained, migration rerun with `lock_timeout` |
| Disk filling from a forgotten replication slot | fixed without touching any file in `pg_wal` |
| Slow query after a "deploy" | top query found in `pg_stat_statements`, plan proves the cause, index built concurrently |
| Redis `MISCONF` | real cause fixed, `BGSAVE` succeeds, no configuration hack |
| A Dokploy database exposed on an external port | found from outside, closed, admin access through `docker exec` |

**Ready for the next stage when** you run the section 10 playbooks without opening them, and your
incident notes name a root cause and a prevention, not just a fix.

### Senior exit test

**Level:** [L3 · Senior]

**Questions**

1. Walk through a point-in-time recovery to 12:41:07 onto a side cluster, file by file. (section 4)
2. What are the real RPO and RTO of each production database you run today, and how do you know?
   (section 4)
3. Synchronous versus asynchronous replication: what do you gain and what do you pay? Why is a
   single synchronous standby a trap? (section 5)
4. List the five parts of a failover, and what fencing prevents. (section 5)
5. Rename a column on a busy table without downtime: list the releases and what each one does.
   (section 11)
6. Which lock does `CREATE INDEX` take, and what does `CONCURRENTLY` change? (section 11)
7. Why is `replicas: 3` in a StatefulSet not a highly available database? (section 7)
8. Which alerts would you put on a database fleet, and which of them page a human? (section 9)

**Timed tasks**

| Task | Time | Pass when |
|---|---|---|
| PITR of deleted rows onto a side cluster, then copy them back | 60 min | rows restored, production never stopped |
| Build a streaming replica, stop it under load, explain the slot, bring it back | 45 min | replica current, retention explained in numbers |
| Manual failover with fencing, then `pg_rewind` the old primary | 45 min | measured RTO, no split brain, old primary rejoined as standby |
| Migration pipeline with `resource_group` and `lock_timeout`; prove a blocked migration fails safely | 45 min | the site stays up while the job fails and retries |
| Exporters and the alert rules; fire two alerts on purpose | 45 min | notifications arrive with runbook links |

**Ready for the next stage when** your databases have measured RPO and RTO, automated restore tests
and alerts that page only for real problems, and other engineers use your runbooks successfully
without you.

### Lead and SRE exit test

**Level:** [L4 · Lead/SRE]

**Questions** (for a discussion with a peer or your manager)

1. Agree RPO and RTO with the business for three services of different value, and show what each
   option costs. (sections 4, 7)
2. Defend in an ADR where each of your databases runs: VM, Dokploy, Kubernetes operator or RDS.
   (section 7 and [Senior architecture](39-learn-senior-architecture.md))
3. Design a restore-drill programme: what is tested automatically, what manually, how often, and
   who reads the results. (section 4)
4. Read GitLab's 2017 postmortem and list three controls that would have prevented or shortened it
   in your environment. (section 4)
5. Run incident command for a data-loss incident: roles, communication, and the decision between
   rolling back, restoring and fixing forward. (section 10 and [Senior architecture](39-learn-senior-architecture.md))

**Timed tasks**

| Task | Time | Pass when |
|---|---|---|
| Game day: a script deletes rows or kills the primary at a random moment | 2 h | detected by an alert, recovered within the RTO, postmortem published within 24 h |
| A one-page backup and DR policy for your real stack (Dokploy databases, VM databases) with measured restore times | half a day | a colleague can follow it without you |
| Capacity plan for connections and storage over the next 12 months | 2 h | derived from your metrics, with the date each limit will be reached |

**You are operating at this level when** database incidents in your area are rare, short and
followed by fixes that remove whole classes of problems, and when the people around you can do
most of this module because you taught it.

---

## 13. Where to go next

> 📚 **Study path:** 1) Note: [34 — Roadmap](34-roadmap.md) and the [career ladder](40-career-ladder.md), to place databases among your other topics · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* first, as planned ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)), then *Prep Course - Prometheus Certified Associate (PCA)* for the monitoring half of this module ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 3) Read: the [PostgreSQL documentation](https://www.postgresql.org/docs/) and the [MySQL documentation](https://dev.mysql.com/doc/) as references, one chapter at a time, whenever a topic here raises a question · 4) Practice: retake the section 12 test for your next stage once a quarter.

### Next modules by stage

- **Fresher and Junior:** [DNS](08-dns.md) and [Network](02-network.md) for the first two gates of
  every connection, [Storage & disk](01-storage-disk.md) for full disks, and the
  [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) for the container side of
  database incidents.
- **Mid-level:** [Learn: Performance & observability](32-learn-performance-observability.md) for
  the USE method, Prometheus and Grafana; [Slow system](23-playbook-slow-system.md) for the host
  side of "the database is slow".
- **Senior:** [Deployment patterns](35-deployment-patterns.md) and
  [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) for migrations and releases;
  [Cloud & AWS](36-learn-cloud-aws.md), section 7, for RDS; and
  [Security & DevSecOps](37-learn-security-devsecops.md) for PKI and secrets.
- **Lead and SRE:** [Senior architecture](39-learn-senior-architecture.md), section 5 (disaster
  recovery) and its ADRs, then the [career ladder](40-career-ladder.md).

### Reference reading

- The [PostgreSQL documentation](https://www.postgresql.org/docs/): Server Administration (client
  authentication, backup and restore, high availability, monitoring), and the release notes before
  every upgrade.
- The [MySQL documentation](https://dev.mysql.com/doc/): Backup and Recovery, Replication, and the
  InnoDB storage engine.
- The [Kubernetes documentation](https://kubernetes.io/docs/) on StatefulSets and persistent
  volumes, and the [Docker documentation](https://docs.docker.com/) on volumes and packet filtering.
- The [AWS documentation](https://docs.aws.amazon.com/) for Amazon RDS: Multi-AZ, automated backups
  and point-in-time restore.
- [GitLab's 2017 database outage postmortem](https://about.gitlab.com/2017/02/10/postmortem-of-database-outage-of-january-31/)
  and chapter 26 of the SRE book ([table of contents](https://sre.google/sre-book/table-of-contents/)).

### Your next four actions

1. **This week:** run the audit from "RPO, RTO and the 3-2-1 rule" on every real database you are
   responsible for, on the VMs and in Dokploy, and write down the RPO and RTO you actually have
   today.
2. **This month:** automate one restore test with a metric and an alert (section 4, section 9).
   It is the single change with the biggest effect on your real risk.
3. **With the Apache to Dokploy migration:** add database firewall rules, `pg_hba.conf` entries and
   a `pg_isready` check from the new host to the cutover checklist (the "app can't connect"
   playbook in section 10, and [Apache 443 and Dokploy](21-case-apache-443-dokploy.md)).
4. **After the CKA:** run CloudNativePG on the homelab and repeat the failover and restore labs from
   section 7 there; it is the bridge from this module to platform work.
