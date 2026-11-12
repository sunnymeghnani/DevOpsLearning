# Databases, backups & monitoring

Data services fail in ways that look alike from the application: the server does not answer, a session or a lock blocks everyone, the data is gone and the backup does not restore, or nobody was alerted. Work from the outside in: does it answer in its own protocol (`pg_isready`, `redis-cli ping`), what is it doing (`pg_stat_activity`, the processlist, `INFO`), what can you restore and how fast, and finally the monitoring that should have told you. One rule runs through every backup card: **a green backup job is not a tested restore**; only a timed restore into a scratch target, checked with a row count and the newest timestamp, measures your real RPO and RTO.

| If you would reach for | Prefer | Because |
|---|---|---|
| "the backup job is green" | a scheduled restore into a scratch database, then `count(*)` and `max(created_at)` | exit 0 proves a file was written; only a restore proves it is complete, fresh, and how long recovery takes |
| `pg_restore -l` as the backup check | `pg_restore -f /dev/null FILE`, or a real restore | `-l` reads only the table of contents at the start; a truncated dump still lists fine |
| `ps -u postgres` or `top` | `psql -c "… FROM pg_stat_activity …"` with `pg_blocking_pids()` | the process title shows a state, not the query, what it waits for or who blocks it |
| `nc -zv db 5432` for "is the database up?" | `pg_isready -h db`, `mysqladmin ping`, `redis-cli -h db ping`, then a real login | the probes speak the protocol, but `pg_isready` and `mysqladmin ping` never log in: only a login proves the rest |
| `restic snapshots` showing last night | `restic check --read-data-subset=5%`, then `restic restore` to a scratch path | a listing proves snapshots exist, not that their data can be read back |
| `cp -a` of a running data directory | `pg_dump`, `pg_basebackup -X stream`, pgBackRest, XtraBackup | files change during the copy; these tools make a copy that starts |
| `CONFIG SET stop-writes-on-bgsave-error no` against `MISCONF` | fix the disk or permissions, then `redis-cli BGSAVE` | the "fix" hides the error and leaves Redis without persistence |
| editing alert rules, then reloading | `promtool check rules`, `amtool check-config`, `amtool config routes test` | a failed reload keeps the old rules, and a routing mistake pages nobody |

### psql — which sessions are running, waiting or blocking, and on what?
Match: psql
Instead of: ps -u postgres, top
Safety: read-only for SELECT and meta-commands · changes state: other SQL runs at once (`-c` commits by itself); `pg_terminate_backend()` ends a session and rolls back its transaction

**In one line:** `psql` is PostgreSQL's client; `-c` runs one statement and exits, turning the server's own views, such as `pg_stat_activity`, into one-line checks.

**Read the command:** `sudo -u postgres psql -c "SELECT pid, now()-query_start AS runtime, state, wait_event_type, left(query,70) AS query FROM pg_stat_activity WHERE state <> 'idle' ORDER BY runtime DESC LIMIT 8;"`

| Part | Meaning |
|---|---|
| `sudo -u postgres` | peer authentication on the local socket: superuser, no password |
| `-c "…"` | run the string as one transaction, print, exit |
| `pg_stat_activity` | one row per server process: sessions and background workers |
| `now()-query_start`, `state <> 'idle'` | runtime of the current (or last) statement; idle sessions left out |
| `wait_event_type` | what it waits for: `Lock`, `IO`, `LWLock`, `Client`; empty means running |
| `-h 127.0.0.1 -p 5433 -U app appdb` | TCP (here through an SSH tunnel), role `app`, database `appdb` |
| `-x`, `-Atc`, `-X -v ON_ERROR_STOP=1` | vertical output / bare values for scripts / no `.psqlrc`, stop on error |

**What the output tells you:**

```
  pid  |     runtime     |        state        | wait_event_type |                        query
-------+-----------------+---------------------+-----------------+-----------------------------------------------------
 30112 | 00:41:12.502113 | idle in transaction | Client          | UPDATE orders SET status = 'shipped' WHERE id = 991
 30455 | 00:06:03.118001 | active              | Lock            | ALTER TABLE orders ADD COLUMN gift_note text
 30461 | 00:05:58.004211 | active              | Lock            | SELECT * FROM orders WHERE customer_id = 4242
```

30112 opened a transaction 41 minutes ago and never committed, so it keeps its locks; the `ALTER` waits for it, and every query on `orders` queues behind the `ALTER`.

**Why it is effective:** `pid` is the PID in `top`, so "postgres at 100% CPU" becomes "this statement, from this client"; adding `pg_blocking_pids(pid)` turns the waiters into a tree whose root is the session to end.

**Compared with `ps -u postgres`:** each backend's process title shows user, database, client and state: enough to count connections, not the statement, the wait or the blocker.

**Trap:** `query` is the *last* statement, not necessarily the one that took the lock. `pg_cancel_backend()` cannot stop an `idle in transaction` session (nothing runs); `pg_terminate_backend()` can, rolling its work back. Without `-h`, psql uses the socket and your OS user name as role and database.

**Next step:** root blocker → the same view with `-x` and `WHERE pid = N` to see whose it is, then `SELECT pg_terminate_backend(N)`. Mostly `IO` → `iostat -xz 1`. Slow, not waiting → `pg_stat_statements`, `EXPLAIN (ANALYZE, BUFFERS)`.

### pg_dump / pg_dumpall — one database as a consistent, portable file, plus the roles it needs
Match: pg_dump, pg_dumpall
Instead of: cp -a of a running data directory
Safety: read-only for the data, but every dumped table keeps an ACCESS SHARE lock until the end, so `ALTER`, `DROP` and `TRUNCATE` wait for the whole dump · the globals file holds password hashes

**In one line:** `pg_dump` exports **one database** from a single snapshot while the application keeps writing; `pg_dumpall --globals-only` adds what it leaves out: roles, passwords and tablespaces.

**Read the command:** `pg_dump -Fc -f /var/backups/db/appdb-$(date +%F_%H%M).dump appdb`

| Part | Meaning |
|---|---|
| `-Fc` | custom format: compressed, for `pg_restore` (selective, parallel); the default `-Fp` is plain SQL for `psql` |
| `-f FILE` | write here, not to stdout |
| `$(date +%F_%H%M)` | the shell adds a timestamp: `appdb-2026-10-03_1205.dump` |
| `appdb` | the database |
| `-h HOST -U labadmin -d postgres -t orders --data-only` | TCP as `labadmin`, database `postgres`, only the rows of `orders` |
| `pg_dumpall --globals-only -f globals.sql` | roles and tablespaces as SQL, for `psql -f` |

**What the output tells you:** nothing when it works: exit status 0. A failure:

```
pg_dump: error: aborting because of server version mismatch
pg_dump: detail: server version: 17.6; pg_dump version: 16.10
```

pg_dump refuses a server of a newer major version. Behind `| gzip` without `set -o pipefail`, this becomes a 20-byte file and a green job.

**Why it is effective:** one repeatable-read snapshot gives a consistent copy without stopping writes, and the file is portable: another server, a newer major version, one table alone.

**Compared with `cp -a` of the data directory:** a file copy of a running server mixes moments and may not start; it is a backup only with PostgreSQL stopped.

**Trap:** no roles in the file: on a new server every `OWNER TO` fails unless the globals go first. The locks last the whole run, so a 02:00 migration waits behind the dump and everything queues behind the migration. `docker exec -t` corrupts a binary dump.

**Next step:** prove the file → the `pg_restore` card. Version mismatch → pg_dump from the server's own container, or a newer client. RPO of minutes → pgBackRest or WAL archiving.

### pg_restore / createdb / dropdb — does the dump really restore, and how long does it take?
Match: pg_restore, createdb, dropdb, vacuumdb
Instead of: pg_restore -l, a green backup job
Safety: changes state: writes into the database named by `-d` (`--clean` drops its objects first) · `createdb` creates a database · `dropdb` deletes one, with no undo

**In one line:** `pg_restore` rebuilds a custom-format dump in a database you choose; into a scratch database it proves a backup complete and fresh, and times the recovery.

**Read the command:** `pg_restore -d appdb_restore -j 4 --no-owner --role=app /var/backups/db/appdb-2026-10-03_1205.dump`

| Part | Meaning |
|---|---|
| `-d appdb_restore` | target, made first with `createdb -O app appdb_restore`; never production |
| `-j 4` | 4 parallel jobs (needs a file, not stdin) |
| `--no-owner` | skip `ALTER … OWNER TO`, so missing roles do not fail |
| `--role=app` | `SET ROLE app` first: restored objects belong to `app` |
| `-l FILE` | only list the header and table of contents |
| `-t orders` | only this table and its rows, without its indexes, constraints or sequence |
| `--exit-on-error` | stop at the first error instead of carrying on |

**What the output tells you:**

```
real    0m41.322s
$ psql -d appdb_restore -Atc "SELECT count(*), max(created_at) FROM orders"
1000000|2026-10-03 12:04:58.113+00
$ pg_restore -d appdb appdb-2026-10-03_0200.dump        # fresh server, no globals
pg_restore: error: could not execute query: ERROR:  role "app" does not exist
pg_restore: warning: errors ignored on restore: 9
```

`real` (from `time`) is your measured RTO; `max(created_at)`, the copy's freshness, is your real RPO; the count catches a valid backup of the wrong database. `errors ignored`: rows arrived, ownership did not, exit status 1.

**Why it is effective:** the job's exit 0 proves only that a file was written. A restore proves the file reads to the end and holds the right data, and times recovery on a quiet day.

**Compared with `pg_restore -l`:** -l reads only the header and table of contents at the start, enough to check versions and contents. A dump cut short by a full disk still lists fine; a restore, or `-f /dev/null`, reads every block.

**Trap:** pg_restore carries on after errors: check the exit status. A plain-SQL dump fails with `input file appears to be a text format dump. Please use psql.` Restore with a pg_restore at least as new as the pg_dump. `dropdb` has no undo: drop the old copy only after the new one checks out.

**Next step:** it worked → run it weekly from a timer, with duration and row count as metrics. Missing roles → `psql -f globals.sql` first. One table lost → copy its rows over with `\copy`. New major version → `vacuumdb --all --analyze-in-stages`.

### pg_basebackup — copy the whole running cluster, for point-in-time recovery or a new standby
Match: pg_basebackup
Instead of: cp -a or rsync of a running data directory
Safety: read-only on the source (a checkpoint, a replication connection, read load) · `-C` creates a replication slot that keeps WAL on the primary until dropped · writes the target directory, which must be empty

**In one line:** `pg_basebackup` copies the **whole cluster** (every database) over a replication connection, with the WAL written meanwhile, so the copy starts consistently: the base for PITR or a new standby.

**Read the command:** `pg_basebackup -D /srv/basebackup/base1 -Fp -Xs -P -c fast -v`

| Part | Meaning |
|---|---|
| `-D /srv/basebackup/base1` | target directory: empty or absent |
| `-Fp` | plain files: a data directory you can start (`-Ft`: tar) |
| `-Xs` | `-X stream`: stream the WAL during the copy, so the backup is self-contained |
| `-P`, `-v` | progress, and each step |
| `-c fast` | an immediate checkpoint instead of a spread one |
| `-h PRIMARY -U replicator` | from another server, as a `REPLICATION` role (pg_hba.conf needs a `replication` line) |
| `-C -S db2 -R` | create and use slot `db2`; write `standby.signal` and `primary_conninfo`: it starts as a standby |

**What the output tells you:**

```
pg_basebackup: initiating base backup, waiting for checkpoint to complete
pg_basebackup: write-ahead log start point: 0/5C000028 on timeline 1
1931211/1931211 kB (100%), 1/1 tablespace
pg_basebackup: write-ahead log end point: 0/5C000138
pg_basebackup: base backup completed
```

The start and end points bracket the copy; recovery must replay at least that WAL. `pg_verifybackup DIR` then checks every file against `backup_manifest`.

**Why it is effective:** it coordinates with the server (checkpoint, backup mode, the WAL in between), so the copy is consistent once that WAL is replayed; one command also seeds a standby.

**Compared with `cp -a` or `rsync`:** they copy files at different moments, without the matching WAL; the result may not start or may hide corruption. Fine only with PostgreSQL stopped.

**Trap:** without `-c fast` it first waits for a spread checkpoint, which looks like a hang. A `-C` slot outlives a dead standby and keeps WAL until the disk fills (`max_slot_wal_keep_size` caps it). Ubuntu's config in `/etc/postgresql/` is not copied. PITR also needs the WAL archive.

**Next step:** standby → `pg_stat_replication` on the primary. PITR → a test recovery in a side cluster. Many backups to a repository → pgBackRest.

### pg_lsclusters / pg_ctlcluster — which clusters run on this Ubuntu host; start, stop or promote one
Match: pg_lsclusters, pg_ctlcluster, pg_createcluster, pg_dropcluster, pg_upgradecluster
Instead of: systemctl status postgresql
Safety: read-only for `pg_lsclusters` · changes state: `pg_ctlcluster` starts, stops and promotes; `pg_createcluster` adds a cluster; `pg_dropcluster` deletes a cluster's data and config for good; `pg_upgradecluster` converts one to a new major version

**In one line:** Debian and Ubuntu run PostgreSQL as **clusters** (version plus name, such as `16/main`), each with its own port, data directory, config and log; these postgresql-common tools list and control them.

**Read the command:** `pg_ctlcluster 16 main promote`

| Part | Meaning |
|---|---|
| `16 main` | the cluster: major version and name (unit `postgresql@16-main`) |
| `promote` | end recovery: this standby becomes a primary, on a new timeline |
| `start`, `stop`, `restart`, `reload` | the other actions |
| `pg_lsclusters` | every cluster with port, status, data directory and log |
| `pg_createcluster 16 pitr --port 5433` | a new, empty side cluster |
| `pg_dropcluster 17 main --stop` | stop it, then delete its data and config |
| `pg_upgradecluster -v 17 -m upgrade --link 16 main` | upgrade to 17 with pg_upgrade, hard-linking the files |

**What the output tells you:**

```
Ver Cluster Port Status Owner    Data directory              Log file
16  main    5433 down   postgres /var/lib/postgresql/16/main /var/log/postgresql/postgresql-16-main.log
17  main    5432 online postgres /var/lib/postgresql/17/main /var/log/postgresql/postgresql-17-main.log
```

After the upgrade the new cluster owns 5432 and the old one is stopped on 5433; a standby shows `online,recovery`. The log file column is where errors go on Ubuntu, not the journal.

**Why it is effective:** one line per cluster answers "which version serves 5432, and where is its log?", the questions behind "I changed the config and nothing happened" (another cluster) and "the app sees an empty database" (the new major's automatic `main`).

**Compared with `systemctl status postgresql`:** that umbrella unit says `active (exited)` even while the server is down; `postgresql@16-main` shows one cluster only.

**Trap:** `promote` while the old primary can come back gives two primaries: fence it first. After `--link` the old cluster must never start again. `pg_dropcluster` asks nothing: read the version twice. A newly installed major creates an empty `main` on the next free port.

**Next step:** `down` → its log file. Promoted → `SELECT pg_is_in_recovery()` must return `f`; repoint the app. Upgraded → `vacuumdb --all --analyze-in-stages`, then drop the old cluster once verified.

### pg_isready / mysqladmin ping — is the database answering on that host and port?
Match: pg_isready, mysqladmin
Instead of: nc -zv HOST 5432
Safety: read-only · neither logs in · other `mysqladmin` commands (`shutdown`, `kill`, `flush-*`) change state

**In one line:** both connect and read the server's reply in its own protocol, telling "the database answers and takes connections" apart from "something listens on the port".

**Read the command:** `pg_isready -h db01.example.com -p 5432`

| Part | Meaning |
|---|---|
| `-h db01.example.com -p 5432` | host and port; without `-h`, the local socket |
| `-U app -d appdb` | names for the probe (healthchecks); no password is ever sent |
| `-q` | silent: only the exit status, for `until …; do sleep 2; done` |
| exit `0` `1` `2` `3` | accepting / rejecting (starting, stopping, recovering) / no response / bad parameters |
| `mysqladmin -h db01.example.com -u monitor -p ping` | MySQL's probe; `-p` prompts; prints `mysqld is alive` |

**What the output tells you:**

```
db01.example.com:5432 - accepting connections
db01.example.com:5432 - no response
mysqld is alive
```

`rejecting connections` means starting, stopping or recovering; `no response` means down, firewalled, or the wrong host or port.

**Why it is effective:** cheap, credential-free and protocol-aware: it fails while the server recovers, when a port check would pass, which is why healthchecks and wait loops use it.

**Compared with `nc -zv HOST 5432`:** nc proves that something accepts TCP on the port (docker-proxy, a load balancer), not that PostgreSQL answers or is ready.

**Trap:** neither logs in: `accepting connections` also appears when every slot is taken (`too many clients`) or the password is wrong, and `mysqladmin ping` exits 0 even on `Access denied`. The official PostgreSQL image's first start runs a socket-only temporary server: probe with `-h 127.0.0.1`.

**Next step:** `no response` → `nc -zv`, then `ss -ltnp` and the firewall on the server. Accepting but the app fails → a real login (`psql -h HOST -U app -c 'SELECT 1'`). Rejecting → the server log.

### pgbackrest — is WAL reaching the repository, and which backups can I restore?
Match: pgbackrest
Instead of: pg_stat_archiver alone, a green backup timer
Safety: read-only for `info`; `check` forces a WAL switch (one extra archived segment) · changes state: `backup` writes to the repository, `stanza-upgrade` rewrites its metadata, `restore` writes the data directory (PostgreSQL stopped)

**In one line:** pgBackRest takes full, differential and incremental backups and archives every WAL segment, so you can restore to any moment the chain covers; `check` and `info` show whether it is intact.

**Read the command:** `pgbackrest --stanza=main --log-level-console=info check`

| Part | Meaning |
|---|---|
| `--stanza=main` | one PostgreSQL cluster and its repositories, from pgbackrest.conf |
| `--log-level-console=info` | print each step, not only errors |
| `check` | verify the setup, force a WAL switch, wait (60 s by default) for that segment in the repository |
| `info` | backups with times and sizes, and the archived WAL range |
| `--type=full backup` | a full backup (default: `incr`) |
| `--delta --type=time --target='2026-10-03 06:00:00+00' restore` | rewrite only differing files in the stopped data directory, recover to that moment |
| `--no-online stanza-upgrade` | after a major upgrade, record the new version, without connecting to PostgreSQL |

**What the output tells you:**

```
stanza: main
    status: ok
    db (current)
        wal archive min/max (16): 000000010000002A00000012/000000010000002B0000004F
        full backup: 20260928-010002F
            timestamp start/stop: 2026-09-28 01:00:02+00 / 2026-09-28 01:21:47+00
```

Labels end in `F`, `D` or `I` (full, differential, incremental). The WAL `max` is how far forward you can recover: if it stops moving, archiving is broken. A failing `check` ends with `[082]` … `was not archived before the 60000ms timeout`.

**Why it is effective:** a backup without the WAL after it restores only to its own start; `check` tests the whole archive path (command, credentials, network, repository) at once.

**Compared with `pg_stat_archiver`:** the view counts archive failures from the server's side, not what the repository holds or which backups are usable.

**Trap:** `status: ok` with a week-old backup is still "ok": compare the times with now. An `archive_command` naming another stanza fails every segment while old backups look fine. `restore` overwrites the data directory it targets, and its time covers only the file copy; WAL replay comes after.

**Next step:** `[082]` → `SHOW archive_command;`, the PostgreSQL log, repository access as postgres. Major upgrade → `stanza-upgrade`, then a full backup. Prove it → a timed `--type=time` restore on a scratch host.

### pgbench — put a known, repeatable load on PostgreSQL
Match: pgbench
Instead of: —
Safety: changes state: `-i` drops and recreates the `pgbench_*` tables; the default script updates rows and writes WAL; never point it at a production connection string

**In one line:** `pgbench` runs many concurrent clients through a small TPC-B-like transaction (`-S`: selects only) and reports throughput and latency: a repeatable load for labs, connection limits and poolers.

**Read the command:** `pgbench -h 127.0.0.1 -U app -c 120 -j 4 -T 20 appdb`

| Part | Meaning |
|---|---|
| `-h 127.0.0.1 -U app appdb` | TCP as role `app` to database `appdb` (`-p 6432`: through PgBouncer) |
| `-c 120` | 120 concurrent client connections |
| `-j 4` | 4 pgbench threads drive them |
| `-T 20` | run for 20 seconds |
| `-i -s 20` | initialise: recreate the tables, 20 × 100,000 rows in `pgbench_accounts` |
| `-S` | the built-in select-only script |

**What the output tells you:**

```
pgbench: error: connection to server at "127.0.0.1", port 5432 failed: FATAL:  remaining connection slots are reserved for roles with the SUPERUSER attribute
pgbench: error: could not create connection for client 97
```

120 clients met `max_connections = 100` with three slots reserved for superusers: client 97 (counted from 0) was the first refused. A normal run ends with `latency average` and `tps`.

**Why it is effective:** it turns "it breaks under load" into an experiment you control (clients, duration, direct or through the pooler) while you watch `pg_stat_activity`, WAL growth or replica lag.

**Trap:** with a scale factor below the client count, clients fight over the same `pgbench_branches` rows: you measure lock contention, not the server. Its transaction is not your application's; never quote its tps as capacity. `-i` drops and recreates its tables without asking.

**Next step:** connection errors → pool sizing, PgBouncer. Latency rising with clients → waits in `pg_stat_activity`, `iostat -xz 1`.

### mysql — what MySQL is doing right now, and with which settings
Match: mysql
Instead of: top on mysqld
Safety: read-only for SELECT and SHOW · changes state: `SET GLOBAL`, `SET PERSIST` (survives restarts), `KILL`, DDL and writes act at once

**In one line:** the `mysql` client runs SQL against MySQL or MariaDB; `-e` runs one statement and exits, so the processlist, status counters and variables become one-line checks.

**Read the command:** `sudo mysql -e "SELECT id, user, time, state, left(info,70) AS query FROM information_schema.processlist WHERE command <> 'Sleep' ORDER BY time DESC LIMIT 8;"`

| Part | Meaning |
|---|---|
| `sudo mysql` | Ubuntu's `root@localhost` uses auth_socket: OS root logs in through the socket |
| `-e "…"` | execute, print a table, exit |
| `information_schema.processlist` | one row per connection; `id` is what `KILL` takes |
| `command <> 'Sleep'`, `time` | hide idle connections; seconds in the current state |
| `-h HOST -P 3306 -u app -p appdb` | TCP login; `-p` alone prompts (`-pSECRET` stays in shell history and can show in `ps`) |
| `\G`, `-Nse` | one column per line / bare tab-separated values |

**What the output tells you:**

```
+-----+--------+------+---------------------------------+-----------------------------------------+
| id  | user   | time | state                           | query                                   |
+-----+--------+------+---------------------------------+-----------------------------------------+
| 918 | deploy |   35 | Waiting for table metadata lock | ALTER TABLE orders ADD COLUMN note TEXT |
| 920 | app    |   34 | Waiting for table metadata lock | SELECT * FROM orders WHERE id=7         |
+-----+--------+------+---------------------------------+-----------------------------------------+
```

The migration waits for a metadata lock and every query on `orders` queues behind it. The session holding the lock is not in this list.

**Why it is effective:** `top` shows one `mysqld` at 300% CPU; this shows which statement, from which client, for how long. The same `-e` reads counters such as `SHOW GLOBAL STATUS LIKE 'Threads_connected'`.

**Compared with `top`:** it proves mysqld is busy, not which connection makes it busy.

**Trap:** the blocker is usually a `Sleep` connection with an open transaction, hidden by this filter: `sys.innodb_lock_waits` and `sys.schema_table_lock_waits` name the `blocking_pid`. `KILL` rolls back, which can take as long as the transaction ran. MariaDB 11 images ship `mariadb`, not `mysql`.

**Next step:** blocker → `KILL 912;`, or `KILL QUERY 918;` to step the migration aside. Many `Sleep` → `wait_timeout`, the app's pool. Slow statements → the slow log and `pt-query-digest`.

### mysqldump — a consistent logical dump of MySQL or MariaDB
Match: mysqldump, mariadb-dump, pt-show-grants
Instead of: cp -a /var/lib/mysql on a running server
Safety: read-only for the data; with `--single-transaction` writes go on, but DDL on a table being dumped aborts the dump · writes SQL to stdout

**In one line:** `mysqldump` writes SQL that recreates schemas and rows; `--single-transaction` reads every InnoDB table from one snapshot, so the dump is consistent while the application keeps writing.

**Read the command:** `mysqldump --single-transaction --routines --events --source-data=2 appdb`

| Part | Meaning |
|---|---|
| `--single-transaction` | one consistent-snapshot transaction for InnoDB, no table locks (MyISAM gets no such guarantee) |
| `--routines --events` | add procedures, functions and scheduled events (triggers are in by default) |
| `--source-data=2` | write the binlog file and position as a comment: where PITR replay starts (8.0.26+; older: `--master-data`) |
| `appdb` | one database; `--all-databases` for all |
| `--defaults-extra-file=/etc/mysql/backup.cnf` | credentials from a mode-600 option file; must be the first option |
| `--no-tablespaces`, `--set-gtid-purged=OFF` | skip what needs the PROCESS privilege, and the GTID line that RDS-like targets reject |

**What the output tells you:**

```
-- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='binlog.000003', SOURCE_LOG_POS=48211907;
…
-- Dump completed on 2026-10-03 12:10:31
```

The commented coordinates are where `mysqlbinlog` replay starts. A complete dump ends with `-- Dump completed`; one that died halfway does not.

**Why it is effective:** a consistent copy without stopping writes, readable with `zcat | grep`, portable across versions, and one database or table can come back alone.

**Compared with copying `/var/lib/mysql`:** a file copy of a running server mixes pages from different moments; use XtraBackup, or stop mysqld first.

**Trap:** `mysqldump … | gzip > FILE` returns gzip's status, so a failed dump still "succeeds": `set -o pipefail`, and check the trailer. A migration during the dump aborts it (`Table definition has changed`). Users and grants are not in a one-database dump (`pt-show-grants`).

**Next step:** prove it → `mysql -e "CREATE DATABASE appdb_restore"`, `zcat FILE | mysql appdb_restore`, count rows. Large database → XtraBackup. Import errors → the collation, `DEFINER` and GTID lines. Users and grants → `pt-show-grants > grants-$(date +%F).sql` (Percona Toolkit, read-only) prints every account as `CREATE USER` and `GRANT` statements in a stable order, so two days' files diff cleanly and replay with `mysql`.

### mysqlbinlog — find the bad transaction, then replay everything before it
Match: mysqlbinlog
Instead of: restoring last night's dump and losing the day
Safety: read-only when printing · changes state when piped into `mysql`: the selected events run again

**In one line:** `mysqlbinlog` decodes the binary log, MySQL's record of every committed change: find the transaction that did the damage and its byte position, then re-apply everything before it on a restored backup.

**Read the command:** `mysqlbinlog --base64-output=DECODE-ROWS -v --start-datetime="2026-10-03 13:10:00" --stop-datetime="2026-10-03 13:15:00" /var/lib/mysql/binlog.000003`

| Part | Meaning |
|---|---|
| `--base64-output=DECODE-ROWS` | hide the base64 `BINLOG` blobs of row events |
| `-v` | show each row change as commented pseudo-SQL |
| `--start-datetime`, `--stop-datetime` | only events in this window, in the time zone of the machine running mysqlbinlog |
| `/var/lib/mysql/binlog.000003` | the file (`SHOW BINARY LOGS;` lists them) |
| `--start-position=48211907 --stop-position=51200433` | replay from the backup's coordinates up to, not including, the bad transaction |
| `… | mysql` | execute the selected events |

**What the output tells you:**

```
$ mysqlbinlog … binlog.000003 | grep -n -B18 -m1 'DELETE FROM `appdb`.`orders`'
1411-# at 51200433
1412-#261003 13:12:40 server id 1  end_log_pos 51200512 CRC32 0x4f1d2a7c   Anonymous_GTID ...
…
1428-#261003 13:12:40 server id 1  end_log_pos 51208851 CRC32 0x22c1f0aa   Delete_rows: table id 92
1429:### DELETE FROM `appdb`.`orders`
```

`# at N` is the byte position where an event starts; the bad transaction begins at its GTID event, 51200433: the stop position.

**Why it is effective:** "someone deleted orders around lunch" becomes one transaction at one position, so recovery keeps everything before it and nothing of it.

**Trap:** `DECODE-ROWS` output is for reading; piped into `mysql` it replays no row changes. Times depend on the local time zone, positions do not. Start exactly at the backup's coordinates (else `Duplicate entry`), and give several binlog files to one command.

**Next step:** restore the base on a side server, replay up to the position, compare counts, copy rows back. Binlogs purged → raise `binlog_expire_logs_seconds` and stream copies off the server.

### xtrabackup — a hot physical copy of MySQL that restores at file-copy speed
Match: xtrabackup
Instead of: mysqldump for a large database
Safety: `--backup` reads the whole data directory (heavy I/O) and writes the target · `--prepare` rewrites the backup's files · changes state: `--copy-back` fills the data directory, which must be empty, with MySQL stopped

**In one line:** Percona XtraBackup copies InnoDB files while MySQL runs and records the redo log written meanwhile; `--prepare` makes the copy consistent, and restoring is a file copy plus a start.

**Read the command:** `xtrabackup --backup --user=root --target-dir=/srv/xtrabackup/full-2026-10-03 2>&1`

| Part | Meaning |
|---|---|
| `--backup` | phase 1: copy the files and the redo log written during the copy |
| `--user=root` | connect to MySQL (socket, under `sudo`) for locks and the binlog position |
| `--target-dir=…` | where the backup goes |
| `2>&1` | XtraBackup logs to stderr; this lets `tail` read it |
| `--prepare --target-dir=…` | phase 2: apply the redo log so the files are consistent |
| `--copy-back --datadir=/var/lib/mysql` | phase 3: copy the prepared files into the empty data directory |

**What the output tells you:**

```
2026-10-03T13:02:10.112933-00:00 0 [Note] [MY-011825] [Xtrabackup] completed OK!
2026-10-03T13:03:41.520771-00:00 0 [Note] [MY-011825] [Xtrabackup] completed OK!
binlog.000003	48211907
```

One `completed OK!` per phase (backup, then prepare); any other last line means that phase failed. The third line is `xtrabackup_binlog_info`: where binlog replay starts.

**Why it is effective:** restoring means copying files, not hours of `INSERT`s and index builds, so a large database fits an RTO that a dump cannot.

**Compared with `mysqldump`:** a dump is portable (another version, one table) but restores slowly; XtraBackup restores the whole server, to the same MySQL series only.

**Trap:** an unprepared backup does not start. XtraBackup must match the server's series (8.0 for 8.0, 8.4 for 8.4) and can fail after a server minor upgrade until it is updated too. After `--copy-back`, `chown -R mysql:mysql /var/lib/mysql`, or MySQL will not start. MariaDB uses `mariadb-backup`.

**Next step:** test it → prepare and restore on a scratch VM, timed. PITR → `mysqlbinlog` from `xtrabackup_binlog_info`. Fails after an upgrade → `xtrabackup --version`.

### pt-query-digest / mysqldumpslow — which query shapes cost the most time?
Match: pt-query-digest, mysqldumpslow
Instead of: tail of the slow log
Safety: read-only · parsing a multi-gigabyte log costs minutes of CPU: run it on a copy or another host

**In one line:** both read MySQL's slow query log, replace literal values so identical queries collapse into one fingerprint, and rank the fingerprints, by total time unless asked otherwise.

**Read the command:** `pt-query-digest --since '2026-10-03 14:00:00' --limit 3 /var/log/mysql/mysql-slow.log`

| Part | Meaning |
|---|---|
| `--since '2026-10-03 14:00:00'` | only entries from then on (`2h` works too) |
| `--limit 3` | the top 3 query classes |
| `/var/log/mysql/mysql-slow.log` | written when `slow_query_log = ON`, for statements over `long_query_time` |
| `mysqldumpslow -s t -t 5 FILE` | the tool shipped with MySQL: sorted by total time, top 5 |

**What the output tells you:**

```
# Profile
# Rank Query ID                            Response time  Calls R/Call V/M   Item
# ==== =================================== ============== ===== ====== ===== ===========
#    1 0x5A3F2B18C0FFEE0123456789ABCDEF01  1840.1120 71.3%  6120 0.3007  0.02 SELECT orders
#    2 0x77D1E2A3B4C5D6E7F8091A2B3C4D5E6F   374.5911 14.5%   612 0.6121  0.01 SELECT orders
```

Rank 1 is 71% of all logged time, 6,120 calls of 0.3 s: one index there pays off most. `V/M` (variance-to-mean) near 0 means steady. The per-class detail below compares `Rows examine` with `Rows sent`: millions examined for a dozen sent is a missing index.

**Why it is effective:** the slowest single query is rarely the costliest; a 0.3 s query run 6,000 times outweighs a 30 s report run once, and only grouping shows it.

**Compared with `tail` of the slow log:** tail shows single entries, good for one example. `mysqldumpslow` groups and counts too, without the variance or per-class detail.

**Trap:** only logged statements count: those under `long_query_time` are absent however often they run. `Query_time` includes waiting for locks, so a "slow" query may only be blocked. On Ubuntu the log may be `HOSTNAME-slow.log` in the data directory.

**Next step:** rank 1 → `EXPLAIN ANALYZE` on a sample from the report, then an online index (`ALGORITHM=INPLACE, LOCK=NONE`). High `V/M` → lock waits. Nothing logged → `SHOW VARIABLES LIKE 'slow_query%'`.

### redis-cli INFO / CONFIG — memory, clients, persistence and settings, from Redis itself
Match: redis-cli info, redis-cli config
Instead of: free -h, ps for redis-server
Safety: read-only for `INFO` and `CONFIG GET` · changes state: `CONFIG SET` changes the running server at once and is lost at restart unless `CONFIG REWRITE` saves it to redis.conf

**In one line:** `INFO SECTION` prints Redis's own counters as `field:value` lines; `CONFIG GET` and `CONFIG SET` read and change settings on the running server.

**Read the command:** `redis-cli INFO memory`

| Part | Meaning |
|---|---|
| `INFO memory` | used and RSS memory, `maxmemory`, the eviction policy, fragmentation |
| `INFO clients` / `stats` | connected and blocked clients / `evicted_keys`, hits, misses, `latest_fork_usec` |
| `INFO persistence` / `replication` / `keyspace` | last save and its status / role and link / keys per database |
| `CONFIG GET maxmemory*` | settings matching a pattern, as name and value pairs |
| `CONFIG SET maxmemory-policy noeviction` | change it now, until restart |
| `CONFIG SET appendonly yes` | switch AOF on at runtime; Redis writes the AOF from the data in memory |
| `CONFIG REWRITE` | save the running settings into redis.conf |

**What the output tells you:**

```
used_memory_human:1.21G
used_memory_rss_human:1.43G
maxmemory_human:1.50G
maxmemory_policy:allkeys-lru
mem_fragmentation_ratio:1.18
```

Data uses 1.21 GB of a 1.5 GB limit; the process holds 1.43 GB of RAM. At the limit `allkeys-lru` evicts keys silently, while `noeviction` (the default) fails writes with `OOM`. `maxmemory:0` means no limit at all.

**Why it is effective:** each error word in the application log maps to one section: `OOM` to `memory`, `MISCONF` to `persistence` (`rdb_last_bgsave_status:err`), `READONLY` to `replication` (`role:slave`).

**Compared with `free -h` or `ps`:** they show the RSS of `redis-server`, not how much is data or fragmentation, or whether the limit will evict or refuse.

**Trap:** `used_memory` excludes fragmentation, client buffers and the copy-on-write of a fork: keep `maxmemory` well below the RAM or container limit. Editing `appendonly yes` into the file and restarting can load an empty AOF: switch with `CONFIG SET`. `CONFIG SET stop-writes-on-bgsave-error no` silences `MISCONF` and leaves you without persistence.

**Next step:** full → `redis-cli --bigkeys`, a stopped queue consumer. `rdb_last_bgsave_status:err` → the Redis log, disk space, `vm.overcommit_memory`. Sessions being evicted → a separate instance for them.

### redis-cli — reach Redis as the app does, find blocking commands, force a snapshot
Match: redis-cli, redis-benchmark, redis-server
Instead of: nc -zv HOST 6379
Safety: read-only for `PING` and `SLOWLOG GET` · changes state: `SET` writes, `BGSAVE` forks and writes a snapshot, `FLUSHALL` deletes every key, `redis-benchmark` writes test keys

**In one line:** `redis-cli` sends a command to Redis or Valkey with the host, port and ACL user the app uses, so one `PING` tests reachability, protected mode, authentication and permissions.

**Read the command:** `redis-cli -h redis01.example.com -p 6379 ping`

| Part | Meaning |
|---|---|
| `-h redis01.example.com -p 6379` | server and port (defaults: 127.0.0.1, 6379) |
| `ping` | `PONG` once connected and authorised; command names are case-insensitive |
| `--user app --askpass` | log in as ACL user `app`, prompting for the password (`-a` leaves it in history and `ps`) |
| `SLOWLOG GET 10` | the 10 latest commands slower than `slowlog-log-slower-than` (10 ms by default) |
| `BGSAVE` | fork and write an RDB snapshot now |
| `redis-benchmark -t set -n 2000000 -r 1000000 -d 100 -q` | separate load tool: 2 million SETs of 100-byte values on up to 1 million random keys |

**What the output tells you:**

```
PONG
(error) NOAUTH Authentication required.
(error) NOPERM User app has no permissions to run the 'flushall' command
(error) DENIED Redis is running in protected mode because protected mode is enabled and no password is set for the default user. …
```

`NOAUTH` or `WRONGPASS`: the credentials. `NOPERM`: logged in, but the ACL forbids that command (good, for `FLUSHALL`). `DENIED`: protected mode refuses remote clients while the default user has no password. `Connection refused`: `bind` or the service.

**Why it is effective:** every reply names the failing gate, from the client's own position; `SLOWLOG` finds the `KEYS *` that froze every client for a second.

**Compared with `nc -zv HOST 6379`:** nc proves the port answers; it cannot see protected mode, authentication or ACLs, where most Redis connection errors live.

**Trap:** `PONG` without credentials means the default user needs no password: anyone reaching the port can do what it may. SLOWLOG times execution only, not network or queueing. `BGSAVE` answers before the save ends: check `rdb_last_bgsave_status` in `INFO persistence`. `FLUSHALL` deletes everything without asking.

**Next step:** refused → `ss -ltnp 'sport = :6379'`, the `bind` line. `KEYS` in the slow log → `SCAN`; a huge `DEL` → `UNLINK`. Related: `redis-server --version` prints the installed server binary's version (`Redis server v=7.0.15 …`); after an image name, `redis-server --maxmemory 180mb --maxmemory-policy allkeys-lru` starts Redis with each `--name value` overriding the config file, which `CONFIG GET maxmemory` confirms.

### restic backup / forget — take a snapshot, then apply retention
Match: restic backup, restic forget
Instead of: tar or rsync to another disk
Safety: changes state: `backup` adds a snapshot (reads every file, uploads what is new) · `forget --prune` deletes snapshots and the data only they used, permanently

**In one line:** `restic backup` stores an encrypted, deduplicated snapshot of paths in a repository (local disk, SFTP, S3, MinIO); `forget --prune` keeps the snapshots your policy names and frees the rest.

**Read the command:** `restic backup --tag dokploy-1 /var/lib/docker/volumes/shop-uploads/_data /etc/dokploy /var/backups/db --exclude /etc/dokploy/traefik/dynamic/access.log`

| Part | Meaning |
|---|---|
| `backup` | read the paths, upload only chunks the repository lacks, record a snapshot |
| `--tag dokploy-1` | a label that `snapshots`, `forget` and `restore` can filter on |
| three paths | a volume, the config, and `/var/backups/db`, where a database dump was written first |
| `--exclude …/access.log` | skip a constantly changing file not worth keeping |
| `RESTIC_REPOSITORY`, `RESTIC_PASSWORD_FILE` | environment: the repository, and the file holding its password (or `-r REPO`) |
| `--retry-lock 30m` | wait for another job's lock instead of failing at once |
| `forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune` | keep the newest snapshot of each of the last 7 days, 4 weeks and 6 months; delete the data only the rest used |

**What the output tells you:**

```
Files:          12 new,     3 changed, 18810 unmodified
Added to the repository: 41.204 MiB (12.118 MiB stored)
processed 18825 files, 2.104 GiB in 0:09
snapshot e90c41f5 saved
```

2.1 GiB scanned, 12 MiB stored. Exit status 0: a complete snapshot; 3: some files could not be read, so the snapshot is incomplete.

**Why it is effective:** deduplication makes a nightly full snapshot cheap, encryption makes an off-site bucket safe, and retention is one command.

**Compared with `tar` or `rsync`:** they copy files too, rsync quickly, but keep one version (or a full copy each time) and encrypt nothing.

**Trap:** files of a running database may not restore: dump first, as here. `snapshot saved` proves the upload, not a restore. `forget` without `--prune` frees nothing; with it, nothing comes back. Never prune a damaged repository.

**Next step:** prove it → the `restic restore / check` card. `already locked` → the `restic / borg` card. Schedule → a systemd timer that writes a success metric last, and an alert on its age.

### restic restore / check — can the backup really be read back?
Match: restic restore, restic check
Instead of: restic snapshots, a green backup job
Safety: `check` only reads (it takes a lock; `--read-data` downloads every pack: slow, and paid egress on S3) · changes state: `restore` writes files under `--target`, overwriting what is there

**In one line:** `restore` brings a snapshot's files back into a directory you choose; `check` verifies the repository's structure and, with `--read-data` or a subset, that the stored data still decrypts and matches.

**Read the command:** `restic restore latest --tag dokploy-1 --target /srv/restore-test --include /var/backups/db`

| Part | Meaning |
|---|---|
| `restore latest --tag dokploy-1` | the newest snapshot with this tag (or a snapshot ID) |
| `--target /srv/restore-test` | a scratch directory; full paths are kept: `/srv/restore-test/var/backups/db/…` |
| `--include /var/backups/db` | only this part of the snapshot |
| `check` | index, snapshots, directory trees and the list of packs: the structure |
| `--read-data-subset=5%` | also download and verify a random 5% of the data packs |
| `--read-data` | verify every pack: the full test, as slow as a full restore |

**What the output tells you:**

```
restoring snapshot e90c41f5 of [/etc/dokploy /var/backups/db …] at 2026-10-06 09:52:33 by root@dokploy-1 to /srv/restore-test
Summary: Restored 3 files/dirs (41.2 MiB) in 0:01
read 10.0% of data packs
Pack ID does not match, want 2b8f1c0e, got 9d4e7a13
Fatal: repository contains errors
```

The first two lines: the dump came back. The last three come from a 10% check of another repository: one pack no longer matches its ID, so its data is lost, and only a read test says so before the day you need it. A healthy check ends with `no errors were found`.

**Why it is effective:** **a green backup job is not a tested restore.** The job proves that a snapshot was recorded; only reading it back proves the bytes survived disk, network and encryption, and the restore's duration is your measured RTO.

**Compared with `restic snapshots`:** the listing proves that snapshots and their metadata exist, not whether the data behind them can be read.

**Trap:** plain `check` reads no file data. A restored file is not a restored service: `pg_restore` the dump into a scratch database and run a real query. Never use `--target /` on a live host. A check failing on flaky hardware fails again after a repair: fix cables, USB enclosures or RAM first.

**Next step:** it worked → time it, schedule it monthly, record a success metric. `contains errors` → copy the repository, then repair (the `restic / borg` card). Dump restored → the `pg_restore` card.

### restic / borg — list snapshots, clear a stale lock, keep the keys, repair the repository
Match: restic, borg
Instead of: deleting lock files by hand
Safety: read-only for `snapshots`, `key list`, `list locks --no-lock` · changes state: `unlock` and `borg break-lock` remove locks; `key add` and `key remove` change who can decrypt; `repair` rewrites index, packs or snapshots; `init` creates a repository

**In one line:** the restic commands around the backup itself, plus borg's equivalents: which snapshots exist, why the repository is locked, who can decrypt it, and how to repair it.

**Read the command:** `restic snapshots --latest 3`

| Part | Meaning |
|---|---|
| `snapshots --latest 3` | the 3 newest snapshots per host and path set |
| `-r sftp:backup@HOST:/srv/restic` | the repository (also a path, `s3:`, `rest:`), instead of `RESTIC_REPOSITORY` |
| `list locks --no-lock`, `unlock` | lock IDs, read without locking / remove stale locks (`--remove-all`: live ones too) |
| `key list`, `key add` | the passwords that open the repository / add one |
| `repair index`, `repair packs ID`, `repair snapshots --forget` | rebuild the index / salvage a pack / drop references to lost data (0.16+) |
| `borg break-lock REPO` | borg's unlock |
| `borg key export --paper REPO` | borg's key as printable text, for the safe |

**What the output tells you:**

```
ID        Time                 Host        Tags        Paths
------------------------------------------------------------------------
71b2d0e8  2026-10-02 01:42:51  dok-01      nightly     /var/backups/stage
e40a6c19  2026-10-03 01:44:02  dok-01      nightly     /var/backups/stage
------------------------------------------------------------------------
2 snapshots
```

One snapshot a night, the newest from today: the job runs. A newest snapshot days old means it stopped, whatever the job's status says.

**Why it is effective:** in seconds: is the newest snapshot fresh, is a lock stale (no restic running on any host that uses the repository), and does anyone besides this server hold a working key.

**Compared with deleting lock files by hand:** `unlock` removes only locks restic considers stale; deleting files under `locks/` during a prune can damage the repository.

**Trap:** run `pgrep -a restic` on every host before `unlock`, and stop overlaps (one timer, `flock`). Lose every password, or borg's key, and the data is gone: add a second key and keep copies off the host today. Before `repair`, copy the repository and fix the hardware.

**Next step:** stale lock → `unlock`, then `--retry-lock` in the job. One key → `key add`, the password manager. Errors → `check --read-data`, then repair: index, packs, a new backup, snapshots.

### mc / rclone — what is in the bucket, is MinIO healthy, and copy buckets elsewhere
Match: mc, rclone
Instead of: the MinIO web console, aws s3 ls
Safety: read-only for `ls` and `admin info` · changes state: `cp` and `mirror` write objects; `alias set` stores the keys in mc's config file; `admin heal` starts healing; `rclone sync` **deletes** destination files missing from the source

**In one line:** `mc`, the MinIO client, talks to any S3-compatible storage through named aliases (`ALIAS/bucket/prefix`) and adds `mc admin` for MinIO's own health; `rclone` copies and syncs between many kinds of storage.

**Read the command:** `mc ls --recursive minio/backups/shop-db/`

| Part | Meaning |
|---|---|
| `minio/backups/shop-db/` | alias `minio` (endpoint and keys from `mc alias set`), bucket `backups`, prefix `shop-db/` |
| `--recursive` | everything below the prefix, not just one level |
| `cp minio/backups/shop-db/FILE .` | download one object |
| `alias set new https://s3-new.example.com ACCESS_KEY SECRET_KEY` | define an alias |
| `mirror --preserve old/backups new/backups` | copy a bucket with its object metadata; deletes nothing on the target without `--remove` |
| `admin info ALIAS`, `admin heal ALIAS` | MinIO nodes, versions and drives online / start or watch healing |
| `rclone sync old:B new:B --checksum --progress` | make `new` identical to `old`, comparing checksums |

**What the output tells you:**

```
[2026-10-03 02:00:11 UTC] 1.9GiB STANDARD shop-2026-10-03T020000.dump
[2026-10-04 02:00:16 UTC] 2.0GiB STANDARD shop-2026-10-04T020000.dump
```

A dump every night at 02:00 with a steady size: the backup writes. A missing night, or a file that suddenly shrinks, is the alarm. In `mc admin info` every node should be online with all drives OK.

**Why it is effective:** it inspects the backup target from outside the backup job: is the newest object there, how big, and is the storage itself healthy.

**Compared with the console or `aws s3 ls`:** both list the same objects, enough to browse; `mc admin` adds MinIO's node, drive and healing state, in a form scripts can read.

**Trap:** on Ubuntu, `mc` may be Midnight Commander (the `mc` package); the MinIO client is sometimes installed as `mcli`. `rclone sync` deletes on the destination: start with `--dry-run`, or use `rclone copy`. An object in a bucket is not a restore: download it and `pg_restore` it.

**Next step:** newest dump missing or tiny → the backup job's log and exit status. Node offline → its DNS, mounts and `MINIO_VOLUMES`. `SignatureDoesNotMatch` → clock skew, proxy headers, path-style addressing.

### promtool / amtool check-config — validate rules, config and routing before you reload
Match: promtool, amtool check-config, amtool config
Instead of: reloading and reading the logs
Safety: read-only · parses files and walks the routing tree locally; sends no alert

**In one line:** `promtool` parses Prometheus's config and rule files and runs rule unit tests; `amtool check-config` parses alertmanager.yml, and `amtool config routes test` prints the receiver a set of labels reaches.

**Read the command:** `promtool check rules /etc/prometheus/rules/databases.yml`

| Part | Meaning |
|---|---|
| `check rules FILE` | parse each rule: YAML, the PromQL expression, label and annotation templates |
| `check config prometheus.yml` | the main config plus the rule files it lists |
| `test rules tests/*.yml` | unit tests: given these series, expect these alerts |
| `docker exec prometheus promtool …` | promtool ships in the Prometheus image (amtool in Alertmanager's) |
| `amtool check-config alertmanager.yml` | parse the Alertmanager config: routes, receivers, templates |
| `amtool config routes test --config.file=… severity=critical alertname=TargetDown` | print the receiver these labels route to |
| `--verify.receivers=ops-teams` | exit non-zero unless that is the receiver: a CI gate |

**What the output tells you:**

```
Checking /etc/prometheus/rules/databases.yml
  SUCCESS: 12 rules found

$ amtool config routes test --config.file=alertmanager.yml severity=critical alertname=TargetDown
oncall
```

`SUCCESS` with the rule count you expect, or `FAILED:` with the parser error and a non-zero exit. The routes test answers `oncall`: a critical TargetDown pages the on-call receiver.

**Why it is effective:** Prometheus keeps the old rules when a reload fails, and the only signs are a log line and `prometheus_config_last_reload_successful` at 0. Checking first, in CI, keeps a typo from freezing your alerting unnoticed.

**Compared with reloading and reading the logs:** the reload reports the same error, but only after the bad file reached the server, where it also breaks the next restart.

**Trap:** valid is not working: a rule on a misspelled metric parses and never fires (`promtool test rules` or an `absent()` alert catch it). Neither tool proves delivery: SMTP, webhook and chat failures show only in Alertmanager's log and `alertmanager_notifications_failed_total`.

**Next step:** checks pass → reload (`curl -X POST http://127.0.0.1:9090/-/reload` needs `--web.enable-lifecycle`) and look at `/rules`. Alert never fires → run its expression in the UI. Delivery → a test alert with `amtool alert add`.

### amtool — what is firing, and silence it during maintenance
Match: amtool, amtool alert, amtool silence
Instead of: the Alertmanager web UI
Safety: read-only for `alert query` and `silence query` · changes state: `silence add` stops notifications for matching alerts until it expires; `silence expire` ends one; `alert add` injects a real alert that is routed and notified

**In one line:** `amtool` is Alertmanager's command line: list what is firing and whether it is silenced, add and expire silences with an author and a reason, and inject a test alert to prove routing end to end.

**Read the command:** `amtool silence add instance=lab-vm1 --duration=2h --author="$USER" --comment="resize LV, CHG-0042"`

| Part | Meaning |
|---|---|
| `silence add instance=lab-vm1` | silence alerts whose `instance` label equals `lab-vm1` exactly (`=~` for a regex) |
| `--duration=2h` | it expires by itself after 2 hours |
| `--author`, `--comment` | who and why, shown to whoever is on call |
| `silence query`, `silence expire ID` | list silences / end one early |
| `alert query alertname=HostHighLoad -o extended` | firing alerts, filtered, with all their labels |
| `--alertmanager.url=http://10.10.0.10:9093` | which Alertmanager (or set it in amtool's config file) |
| `alert add alertname=PagingTest severity=page …` | create an alert by hand, to test routes and receivers |

**What the output tells you:**

```
Alertname                Starts At                Summary                                   State
DiskSpaceAbove85Percent  2026-10-03 10:12:44 UTC  Filesystem / on lab-vm1 is 91% full       active
SystemdUnitFailed        2026-10-03 10:20:01 UTC  lab-fail.service failed on lab-vm1        active
```

`active` alerts notify; `suppressed` ones are silenced or inhibited. `silence add` prints the new silence's ID, which `expire` needs.

**Why it is effective:** a silence scoped to one host, with an expiry and a change number, stops the noise of planned work without muting anything else, and records who did it.

**Compared with the web UI:** the same alerts and silences, fine by hand; amtool is scriptable and works over SSH.

**Trap:** labels match exactly: `instance` is often `lab-vm1:9100`, so `instance=lab-vm1` silences nothing; check with `alert query -o extended` first. A silence stops notifications only: the alert still fires in Prometheus. `alert add` really pages people; the test alert resolves by itself after `resolve_timeout` (5 minutes by default).

**Next step:** firing in Prometheus but not here → Prometheus's `alerting:` block and its log. Here but no notification → `amtool config routes test`, then Alertmanager's log for receiver errors.

### logcli — query Loki from the shell: how much a query reads, and which label explodes
Match: logcli
Instead of: Grafana Explore
Safety: read-only · a wide selector over a long range makes Loki read gigabytes, the same load a dashboard panel causes

**In one line:** `logcli` is Loki's command-line client: it runs LogQL queries, lists streams and labels, and with `--stats` reports how much data a query really scanned.

**Read the command:** `logcli --addr=http://10.10.0.10:3100 query --stats --since=24h --limit=10 '{service="shop-web"} |= "error"'`

| Part | Meaning |
|---|---|
| `--addr=http://10.10.0.10:3100` | the Loki server (or `LOKI_ADDR`) |
| `query` | run a LogQL query and print matching lines |
| `--stats` | print query statistics, on stderr (hence `2>&1` before `grep`) |
| `--since=24h`, `--limit=10` | look back 24 hours (default 1 hour); print at most 10 lines |
| `{service="shop-web"} |= "error"` | stream selector, then a line filter: lines containing `error` |
| `series --analyze-labels '{host=~".+"}'` | count streams, and the distinct values of each label |

**What the output tells you:**

```
Summary.TotalBytesProcessed   41 GB
Summary.ExecTime              58.1s
Total Streams:  41211
Label Name  Unique Values  Found In Streams
container   40987          41211
```

The 24-hour search read 41 GB to print ten lines and took almost a minute: a dashboard with a dozen such panels times out. A `container` label with 40,987 values is why Loki hits its stream limit and rejects pushes with `429`.

**Why it is effective:** Grafana shows that a panel is slow or empty; `--stats` shows why (the bytes behind it), and `--analyze-labels` names the high-cardinality label in one command.

**Compared with Grafana Explore:** Explore runs the same LogQL and its query inspector shows statistics too; logcli is scriptable and still works when Grafana is what is down.

**Trap:** `--limit` caps the lines printed, not the data scanned: the selector and time range decide the cost, and line filters run after the chunks are read. Without `--since` you search only the last hour, and may conclude "no errors".

**Next step:** huge bytes → narrower labels, shorter ranges, recording rules. Exploding label → move it out of the labels in Alloy. Limits hit → Loki's `limits_config`.

### filebeat — can Filebeat reach and log in to its output, and load what the indexer needs?
Match: filebeat
Instead of: systemctl status filebeat
Safety: read-only for `test output` and `test config` · changes state: `setup` loads ingest pipelines, index templates and lifecycle policies into the cluster; `keystore add --force` replaces a stored secret

**In one line:** Filebeat ships log files to an output (in Wazuh, alerts to the indexer); its subcommands test that connection, load the cluster objects its modules need, and keep secrets out of filebeat.yml.

**Read the command:** `filebeat test output`

| Part | Meaning |
|---|---|
| `test output` | connect as the service would: DNS, TCP, TLS, then a request to the server |
| `test config` | parse filebeat.yml and the enabled modules |
| `setup --pipelines` | load the ingest pipelines of the enabled modules |
| `setup --index-management -E output.logstash.enabled=false` | load the index template and lifecycle settings; `-E` overrides one setting for this run |
| `keystore add password --stdin --force` | store the secret `password` (used as `${password}` in the config) from stdin, replacing the old one |

**What the output tells you:**

```
elasticsearch: https://127.0.0.1:9200...
  parse url... OK
  connection...
    dns lookup... OK
    dial up... OK
  TLS...
    handshake... OK
  talk to server... ERROR 401 Unauthorized: …Unable to authenticate user [admin]…
```

Trimmed; each stage passes or fails on its own line: `dial up` failing is the network or a stopped indexer, `handshake` a certificate (`x509: certificate is valid for 192.0.2.10, not 10.0.5.20`), `401` a stale keystore password. Healthy ends with `talk to server... OK` and a version.

**Why it is effective:** it walks the whole path with the service's own config and credentials, and names the layer that fails.

**Compared with `systemctl status filebeat`:** status shows that the process runs, not whether events reach the indexer.

**Trap:** a passing test proves the connection, not the flow: inputs, enabled modules and file permissions can still be wrong (Filebeat's log shows harvester errors). With Wazuh, `version: 7.10.2` is expected: the indexer reports a compatibility version. `keystore add --force` overwrites the old secret without asking. Use `sudo`; config and keystore are root-only.

**Next step:** `401` → set the password with Wazuh's tool, then `keystore add … --force` and restart Filebeat. `x509` → certificates for the new address. OK but no alerts → `filebeat test config`, the module's state.

### liquibase release-locks / flyway repair — unstick a schema migration
Match: liquibase, flyway
Instead of: editing the lock or history table by hand
Safety: changes state: `release-locks` clears the lock row, even one a running migration holds; `repair` rewrites stored checksums and removes failed entries in the history table

**In one line:** two fixes for the two classic migration hangs: a Liquibase lock left by a killed runner, and a Flyway checksum mismatch after someone edited an applied migration.

**Read the command:** `liquibase release-locks`

| Part | Meaning |
|---|---|
| `release-locks` | set `locked = false` in `DATABASECHANGELOGLOCK`, whoever holds it |
| `SELECT id, locked, lockgranted, lockedby FROM databasechangeloglock` | look first: who holds the lock, since when |
| `flyway repair` | realign stored checksums and descriptions in `flyway_schema_history` with the files; remove failed entries (databases without transactional DDL, such as MySQL) |

**What the output tells you:**

```
 id | locked |       lockgranted       |               lockedby
----+--------+-------------------------+---------------------------------------
  1 | t      | 2026-10-03 08:14:55.031 | shop-web-7c9d5b6f4-x2k8q (10.42.1.17)
```

A lock since 08:14 held by a pod that no longer exists (`kubectl get pods -A` does not list it): a runner killed mid-migration. Every later run waits at `Waiting for changelog lock....` forever.

**Why it is effective:** both tools stop on purpose; these commands remove exactly the obstacle, once you have proved it stale, instead of hand edits to their tables.

**Compared with editing the tables by hand:** `UPDATE databasechangeloglock SET locked = false …` does what `release-locks` does and is fine without the CLI; Flyway checksums are error-prone to edit, while `repair` computes them.

**Trap:** releasing a lock that a live migration holds lets two runners change the schema at once. `flyway repair` makes the history match the files, right only if the database matches them too; for an edited applied migration, restore the file from Git and put the change in a new migration.

**Next step:** rerun the migrate job. Then run migrations as one dedicated CI job or Kubernetes Job without a liveness probe that can kill it, and reject edits to applied migrations in CI.
