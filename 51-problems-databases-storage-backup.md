# 51 — Real-World Problems: Databases, Object Storage & Backups

This module is a problem library for the data layer: PostgreSQL, MySQL and MariaDB, Redis and Valkey, MongoDB, PgBouncer, MinIO and other S3-compatible storage, and the backup tools around them (pg_dump, restic, borg, pgBackRest, Velero, Proxmox Backup Server), whether they run on a VM, in Docker, under Dokploy or on Kubernetes. It collects 40 problems that people really hit. They come from GitHub issues sorted by reactions and comments, official docs, mailing lists, forum threads and public postmortems, and Stack Overflow and Reddit are reachable through search links. [Databases for DevOps](38-learn-databases-ops.md) teaches the fundamentals, and this module assumes them. Every command is documented for your own lab VMs or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Data problems are the ones you can't undo. A crashed proxy comes back with a restart; a deleted volume, a backup that never worked or a half-applied migration does not. That's why every entry here starts with evidence, copies data before repairing anything, and ends with a restore test or a check, not just a green deploy.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | entries 3.1, 1.1 and 2.1, and the safety rules below | you connect to Postgres and MySQL locally and remotely, and can explain why a password change in compose did nothing |
| Junior | L1 Operator | sections 1, 4 and 5 (every L1 entry) | you fix a container database that won't start, an exposed Redis and a locked backup repository without help |
| Mid-level | L2 Troubleshooter | sections 2, 3, 5 and 6 | you explain any "can't connect", "too many clients" or failed backup from logs and catalog views alone |
| Senior | L3 Platform | sections 6 to 9 | PITR backups, S3 targets behind your own CA, migrations as a pipeline stage and a node-loss drill all work in your lab |
| Senior/Lead | L4 SRE | entries 6.5, 8.3, 9.3 and the Self-check | you own measured RPO and RTO numbers, a restore calendar and a storage strategy others follow |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** build three lab VMs (Ubuntu 24.04, 2 vCPU and 4 GB RAM each): db1 runs Docker with Postgres, MySQL and Redis containers, plus the apt packages for the bare-metal entries; app1 is the client side (an app, a GitLab runner or Dokploy); bk1 holds an S3 server and a restic repository. Snapshot all three, break one thing at a time on purpose, fix it using only the entry, and write a five-line note: symptom, evidence, cause, fix, prevention. The Kubernetes entries need a kubeadm or k3s lab with two workers. Never practise on production data.

**Safety rules for data incidents:**

- Copy before you repair: snapshot the VM, or copy the volume into a second volume, before anything that writes.
- Never delete files in pg_wal, never run `docker compose down -v` or a prune with `--volumes` against data you haven't backed up, and run tools such as pg_resetwal only on a copy.
- Restore into a scratch database or namespace, never over the only copy.
- Write down what you ran and when. Data incidents end in a postmortem, and the timeline is its backbone.

**Placeholders and examples:** UPPERCASE words are placeholders (CONTAINER, VOLUME, REPO, BUCKET, ALIAS, NODE, POD, PID). The examples use a 10.0.1.0/24 lab network with db1 at 10.0.1.10, app1 at 10.0.1.20, the GitLab runner at 10.0.1.30, the S3 server at 10.0.1.40 (s3.example.com, console at console.example.com) and Proxmox Backup Server at 10.0.1.50; the Dokploy manager is 192.0.2.10, the public address 203.0.113.10, the admin user ops and the main database shop.

**First minute: symptom to entry.**

| You see | First check | Go to |
|---|---|---|
| password authentication failed right after a redeploy | the container log: was initialisation skipped? | 1.1 |
| a container database that exits or starts empty | `docker logs CONTAINER` and its mounts | 1.2, 1.3, 1.4 |
| Connection refused or no pg_hba.conf entry | `sudo ss -ltnp` on the database host | 2.1 |
| too many clients or Too many connections | sessions per state in pg_stat_activity | 2.2 |
| MISCONF or OOM command not allowed | `redis-cli INFO persistence` or `INFO memory` | 4.2, 4.3 |
| a backup job that "succeeded" but is tiny | size and date of the newest backup files | 5.4 |
| SignatureDoesNotMatch or a BSL marked Unavailable | the proxy route and the client's S3 settings | 6.1, 6.2 |
| a deploy that hangs at the migration step | blocking PIDs in pg_stat_activity | 7.1, 7.2 |
| disk filling on a database host | size of pg_wal and pg_replication_slots | 8.1 |
| a database pod stuck after a node died | `kubectl describe pod` events | 9.1 |

> 📚 **Study path:** KodeKloud *DevOps Pre-Requisite Course* — 2 Tier Applications ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) → *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts), then Docker Compose ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) → *Certified Kubernetes Administrator (CKA)* — Storage, then Cluster Maintenance: Backup and Restore Methods ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Cluster-Maintenance/Backup-and-Restore-Methods)) → *Fundamentals of SRE* — Incident Management ([course](https://kodekloud.com/courses/fundamentals-of-sre)) → handbook [Databases for DevOps](38-learn-databases-ops.md) (sections 4, 7 and 10 first) → docs: [PostgreSQL](https://www.postgresql.org/docs/current/), [MySQL](https://dev.mysql.com/doc/), [Redis](https://redis.io/docs/), [restic](https://restic.readthedocs.io/en/stable/077_troubleshooting.html) → lab: the three VMs above and the Self-check. KodeKloud has no database-operations or backup course in the verified map, so the handbook and the official docs lead here.

---

The problem library starts here. Sections 1 to 9 run from first-day container problems to platform and disaster-recovery work; each entry stands on its own.

## 1. Databases in Docker and Dokploy

Most of your databases run as containers, and most container database problems come from three facts: the image initialises only once, the data lives wherever the volume really points, and the container sees less of the host than you think (shared memory, CPU flags, networks).

### 1.1 New password in compose, login still fails

> **Seen as:** `FATAL:  password authentication failed for user "postgres"` (MySQL: `ERROR 1045 (28000): Access denied for user 'root'`) right after you changed POSTGRES_PASSWORD or MYSQL_ROOT_PASSWORD and redeployed · **Where:** official Postgres, MySQL, MariaDB and MongoDB images in Compose, Swarm or Dokploy · **Level:** [L1 · Junior] · **How common:** a classic; several highly reacted docker-library/postgres issues, plus Docker forum and app-project threads (Chatwoot, Outline)

**Why it happens:** the image's entrypoint reads POSTGRES_PASSWORD, POSTGRES_USER and POSTGRES_DB (and the `MYSQL_*`, `MARIADB_*` and `MONGO_INITDB_*` variables) only when the data directory is empty, at first initialisation. Once the volume holds a database, the variables are ignored and the old password stays. Two look-alikes: the client talks to a different instance than you think (an old container, a named volume reused under the same project name, or a PostgreSQL installed on the host), or the password contains characters such as @ or : that break the connection URL unless they are URL-encoded.

**Diagnose:**

```bash
# Which volume does the container really use?
docker inspect -f '{{range .Mounts}}{{.Name}} {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' CONTAINER
# Did the entrypoint skip initialisation?
docker logs CONTAINER 2>&1 | grep -iE 'skipping initialization|initdb'
# Is another PostgreSQL listening on the host itself?
sudo ss -ltnp 'sport = :5432'
```

```text
shop_pgdata /var/lib/docker/volumes/shop_pgdata/_data -> /var/lib/postgresql/data
PostgreSQL Database directory appears to contain a database; Skipping initialization
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      200        127.0.0.1:5432       0.0.0.0:*     users:(("postgres",pid=1184,fd=7))
```

**What the output tells you:** the volume already held a database, so the new variable was never applied. The host also runs its own PostgreSQL on 127.0.0.1:5432, so any tool on the host that connects to localhost reaches that one, not the container.

**Fix:**

```bash
# Keep the data: change the password inside the database (prompts, nothing lands in shell history)
docker exec -it CONTAINER psql -U postgres -c '\password postgres'
# MySQL (MariaDB 11+: use mariadb instead of mysql); root exists for localhost and % in the image
docker exec -it CONTAINER mysql -u root -p -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'NEW_PASSWORD'; ALTER USER 'root'@'%' IDENTIFIED BY 'NEW_PASSWORD';"
# Then set the same value in compose or the Dokploy environment, and URL-encode it for DATABASE_URL
python3 -c "import urllib.parse; print(urllib.parse.quote('p@ss:w0rd', safe=''))"
```

Only for throwaway data, such as a fresh dev stack, does `docker compose down -v` make sense: it deletes the volume so the entrypoint initialises again with the new variables. On anything real, that command is data loss.

**Why this fix works:** the password lives in the database catalog (pg_authid, mysql.user), not in the environment, so ALTER USER changes it where the server checks it; updating the secret keeps the next fresh install consistent. Deleting the volume "works" only because it destroys the database.

**Prevent it:** treat init variables as first-boot only, rotate passwords with SQL from a runbook, keep secrets in one place (the Dokploy environment or a secret manager), and check `docker volume ls` for an old volume with the same project name before a first deploy.

**Next step:** [Databases: Databases in Docker](38-learn-databases-ops.md) · [Docker: Storage](30-learn-docker.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forum: password authentication failed for user postgres](https://forums.docker.com/t/error-password-authentication-failed-for-user-postgres/119648) · [docker-library/postgres issues by reactions](https://github.com/docker-library/postgres/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+postgres+%22password+authentication+failed%22+POSTGRES_PASSWORD+volume) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=postgres+password+authentication+failed+volume&restrict_sr=1)

### 1.2 Postgres 18 ignores the mounted volume

> **Seen as:** the container exits with `there appears to be PostgreSQL data in: /var/lib/postgresql/data (unused mount/volume)`, or it starts with an empty database and the data "vanishes" on the next redeploy · **Where:** a compose file or Dokploy template that worked with postgres:16 or 17, bumped to postgres:18 or :latest · **Level:** [L1 · Junior] · **How common:** very common since PostgreSQL 18 shipped in September 2025; docker-library/postgres#1370, many downstream issues and several blog posts

**Why it happens:** from 18 the official image sets PGDATA to /var/lib/postgresql/18/docker and declares the volume at /var/lib/postgresql, so a later pg_upgrade --link can keep the old and new clusters side by side on one mount. A volume still mounted at the old path is now just a folder next to PGDATA: the server writes into the anonymous volume Docker creates for /var/lib/postgresql, and that data is lost when the container is recreated. If the old path already contains a cluster, the entrypoint refuses to start instead of guessing. And a 17 data directory can't be opened by 18 anyway, so the bump is also a hidden major upgrade (entry 1.4).

**Diagnose:**

```bash
docker logs CONTAINER 2>&1 | grep -i 'appears to be PostgreSQL data'
docker exec CONTAINER sh -c 'echo $PGDATA; ls -la /var/lib/postgresql'
docker inspect -f '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{"\n"}}{{end}}' CONTAINER
```

```text
/var/lib/postgresql/18/docker
total 16
drwxr-xr-x 4 postgres postgres 4096 Oct  3 09:12 .
drwxr-xr-x 1 root     root     4096 Sep 30 21:40 ..
drwxr-xr-x 3 postgres postgres 4096 Oct  3 09:12 18
drwxr-xr-x 2 root     root     4096 Oct  3 09:12 data
volume 9b1f0c3e5d7a28e4b6f1c0d3a5e7b9c1d2f4a6b8c0e2d4f6a8b0c2e4d6f8a0b2 -> /var/lib/postgresql
volume shop_pgdata -> /var/lib/postgresql/data
```

**What the output tells you:** PGDATA is under 18/docker inside the anonymous volume (the long hexadecimal name), while your named volume sits empty and unused at .../data. Every recreate of the container gets a fresh anonymous volume, which is exactly why the data "vanishes".

**Fix:**

```yaml
services:
  db:
    image: postgres:18-bookworm          # pin the major (and the Debian base), never :latest
    shm_size: 256mb                      # see entry 1.5
    volumes:
      - pgdata18:/var/lib/postgresql     # 18+: mount the parent; PGDATA lives in 18/docker
volumes:
  pgdata18:
```

Existing 17 data: go back to postgres:17 until you upgrade on purpose (entry 1.4: a dump into a fresh 18 volume, or pg_upgrade). If a tool insists on the old path for new 18 data, set PGDATA=/var/lib/postgresql/data explicitly, mount there, and write that down, because the next person will expect the new layout.

**Why this fix works:** with the volume on the parent directory, the versioned PGDATA lands inside your named volume and survives every recreate, and a future upgrade can place the next major's directory beside it. Copying files from the anonymous volume by hand without stopping the server risks a torn copy.

**Prevent it:** pin the major version and the Debian base, read the image's release notes before a bump, and test every bump on a copy of the volume in staging.

**Next step:** [Databases: Major version upgrades](38-learn-databases-ops.md) · [Docker: Storage](30-learn-docker.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts) · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [docker-library/postgres#1370](https://github.com/docker-library/postgres/issues/1370) · [PostgreSQL 18 won't take a volume at /var/lib/postgresql/data](https://basantbhattarai.com.np/writing/postgresql-18-docker-volume-path-change/) · [Postgres 18 Docker silently ignores your named volume](https://rdiachenko.com/posts/databases/postgresql/postgres-18-docker-silently-ignores-your-named-volume/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=postgres+18+docker+volume+%22%2Fvar%2Flib%2Fpostgresql%2Fdata%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=postgres+18+volume+%2Fvar%2Flib%2Fpostgresql%2Fdata&restrict_sr=1)

### 1.3 Data directory won't initialise on the mount

> **Seen as:** `chown: changing ownership of '/var/lib/postgresql/data': Operation not permitted`, `initdb: error: directory "/var/lib/postgresql/data" exists but is not empty`, or `FATAL:  data directory "/var/lib/postgresql/data" has wrong ownership` on the first start · **Where:** bind mounts, NFS shares and fresh Kubernetes PVCs (a block volume formatted with ext4) · **Level:** [L1 · Junior] · **How common:** three of the most-reacted docker-library/postgres issues (#116, #361, #435), #792 for NFS-backed PVCs, and a long discuss.kubernetes.io thread

**Why it happens:** the entrypoint wants to chown the data directory to the postgres user (UID 999 in the Debian image, 70 in the Alpine one), and initdb wants an empty directory with mode 0700. NFS with root_squash (and SMB or CIFS mounts) refuses the chown; a freshly formatted ext4 volume carries a lost+found folder, so the mount point is never empty; and a host directory owned by another UID, or a pod running as non-root without a matching fsGroup, gives "wrong ownership".

**Diagnose:**

```bash
ls -lan /srv/pgdata                              # numeric owner and mode of a bind mount
docker run --rm -v VOLUME:/d alpine ls -la /d    # lost+found on a fresh block volume?
kubectl logs POD --previous                      # Kubernetes: the error from the first start
findmnt -T /srv/pgdata                           # NFS? then check root_squash in /etc/exports on the NFS server
```

```text
total 24
drwxr-xr-x 3 0 0  4096 Oct  3 08:55 .
drwxr-xr-x 4 0 0  4096 Oct  3 08:55 ..
drwx------ 2 0 0 16384 Oct  3 08:55 lost+found
initdb: error: directory "/var/lib/postgresql/data" exists but is not empty
initdb: detail: It contains a lost+found directory, perhaps due to it being a mount point.
initdb: hint: Using a mount point directly as the data directory is not recommended.
Create a subdirectory under the mount point.
```

**What the output tells you:** the volume root belongs to root and contains lost+found, so initdb refuses to use the mount point itself; its hint already names the fix.

**Fix:**

```yaml
# Kubernetes: data in a subdirectory, group ownership set by the kubelet
spec:
  securityContext:
    runAsUser: 999
    fsGroup: 999
  containers:
    - name: postgres
      image: postgres:17-bookworm
      env:
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
      volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
```

On a Docker host, prefer a named volume. If you need a bind mount, pre-create a subdirectory owned by the postgres UID with mode 0700 (`sudo install -d -o 999 -g 999 -m 0700 /srv/pgdata/data`) and mount that. PostgreSQL 18's default layout already puts PGDATA in a subdirectory (entry 1.2), which avoids lost+found by design. Keep database files off NFS: use local disks or block storage (Longhorn, Ceph RBD, a cloud volume).

**Why this fix works:** a subdirectory starts empty and is created by the right user, even when the mount point itself can't be changed; fsGroup makes the mount point group-writable for that user before the container starts. Mode 777 or running the database as root hides the problem and weakens isolation, and NFS adds locking and fsync behaviour a database shouldn't depend on.

**Prevent it:** one storage pattern for databases in your templates: a local or block volume, PGDATA in a subdirectory, fsGroup set.

**Next step:** [Databases: StatefulSets and volumes](38-learn-databases-ops.md) · [Docker & K8s incidents: disk, storage and permissions](26-playbook-containers-k8s.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Storage · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [docker-library/postgres#792](https://github.com/docker-library/postgres/issues/792) · [Discuss Kubernetes: Postgres pod with a local directory for data](https://discuss.kubernetes.io/t/postgres-pod-with-local-directory-mounted-for-data/5517) · [docker-library/postgres most-reacted issues](https://github.com/docker-library/postgres/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Server Fault](https://serverfault.com/search?q=postgres+initdb+%22exists+but+is+not+empty%22+lost%2Bfound) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=postgres+pvc+lost%2Bfound+initdb&restrict_sr=1)

### 1.4 Postgres major bump: incompatible data files

> **Seen as:** a crash loop with `FATAL:  database files are incompatible with server` and `DETAIL:  The data directory was initialized by PostgreSQL version 16, which is not compatible with this version 17.6`, or, after an upgrade that worked, queries that are suddenly slow · **Where:** postgres:16 changed to postgres:17, or a :latest tag that pulled a new major on redeploy · **Level:** [L2 · Mid-level] · **How common:** the most-reacted issue in docker-library/postgres (#37, 140+ reactions, open for years); CircleCI's April 2025 incident came from stale statistics after a major upgrade

**Why it happens:** the on-disk format changes between major versions. New binaries can't open an old cluster, and the image doesn't run pg_upgrade for you, because pg_upgrade needs both the old and the new binaries and one image contains only one version. After pg_upgrade into a version before 18, the planner statistics are missing until ANALYZE runs, so queries get bad plans (18 keeps them). Upgrading into 18 or later has one more trap: initdb now enables data checksums by default, and pg_upgrade requires the old and new clusters to match.

**Diagnose:**

```bash
docker logs CONTAINER 2>&1 | grep -A1 incompatible
docker run --rm -v VOLUME:/data alpine cat /data/PG_VERSION    # the major that created the cluster
# After an upgrade: which tables were never analysed?
docker exec CONTAINER psql -U postgres -d shop -c "SELECT relname, last_analyze, last_autoanalyze FROM pg_stat_user_tables ORDER BY greatest(last_analyze, last_autoanalyze) NULLS FIRST LIMIT 5;"
```

```text
FATAL:  database files are incompatible with server
DETAIL:  The data directory was initialized by PostgreSQL version 16, which is not compatible with this version 17.6 (Debian 17.6-1.pgdg120+1).
16
```

**What the output tells you:** the volume holds a 16 cluster and the container runs 17. Nothing is corrupt; the tag moved. Roll back first, then plan the upgrade.

**Fix:**

```bash
# 1. Restore service: set the tag back to postgres:16 and redeploy.
# 2. Small or medium database: dump with the old version, load into a NEW volume
docker exec OLD_DB pg_dumpall -U postgres > all-16.sql
docker run -d --name db17 -e POSTGRES_PASSWORD=TEMP_PASSWORD -v pgdata17:/var/lib/postgresql/data postgres:17-bookworm
# wait for the final server: during first-start init a temporary server answers on the socket only
until docker exec db17 pg_isready -h 127.0.0.1 -U postgres; do sleep 2; done
docker exec -i db17 psql -U postgres < all-16.sql 2> restore-errors.log
grep ERROR restore-errors.log        # expected: only 'role "postgres" already exists'
# 3. Rebuild planner statistics (after a dump/restore, or after pg_upgrade into a version before 18)
docker exec db17 vacuumdb -U postgres --all --analyze-in-stages
```

Large databases: use pg_upgrade with both versions in one container (community images such as tianon/postgres-upgrade or pgautoupgrade), with --link when both data directories sit on one filesystem, after a backup. When the old cluster has no checksums and the target is 18 or later, initialise the new cluster with --no-data-checksums, or enable checksums on the stopped old cluster first with pg_checksums.

**Why this fix works:** a dump is version-independent SQL, so the new major builds its own files from it; pg_upgrade rewrites only the system catalogs and links or copies the data files, which is why it's fast but needs both binaries. ANALYZE gives the planner its row estimates back. Never point a new major at the old volume "to see if it works", and never edit PG_VERSION to make it start.

**Prevent it:** pin the major version, make upgrades a planned change with a tested rollback (keep the old volume until the new one has run for a week), and rehearse on a restored copy.

**Next step:** [Databases: Major version upgrades](38-learn-databases-ops.md) · [Deployment patterns](35-deployment-patterns.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [docker-library/postgres#37](https://github.com/docker-library/postgres/issues/37) · [CircleCI post-incident report, April 2025](https://discuss.circleci.com/t/post-incident-report-april-4-2025-delays-in-starting-workflows/53113) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22database+files+are+incompatible+with+server%22+docker) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=postgres+major+version+upgrade+docker&restrict_sr=1)

### 1.5 Shared memory: No space left on device

> **Seen as:** `ERROR:  could not resize shared memory segment "/PostgreSQL.1234" to 8388608 bytes: No space left on device` on big queries, parallel queries or index builds, while df on the host shows plenty of space · **Where:** Postgres in Docker, Swarm and Dokploy services, Kubernetes pods · **Level:** [L2 · Mid-level] · **How common:** recurring across docker-library/postgres#416, Nextcloud AIO, TimescaleDB and the pgsql mailing list; Dokploy#3975 asks for an SHM size setting on database services

**Why it happens:** Docker gives each container a 64 MB /dev/shm by default, and PostgreSQL's dynamic shared memory (parallel workers, hash joins, parallel index builds) lives there. Kubernetes pods get the same small /dev/shm unless you mount a memory-backed emptyDir. It isn't a disk problem, so the host's df looks fine.

**Diagnose:**

```bash
docker exec CONTAINER df -h /dev/shm
docker logs CONTAINER 2>&1 | grep -i 'shared memory segment' | tail -1
docker exec CONTAINER psql -U postgres -Atc 'SHOW dynamic_shared_memory_type;' -c 'SHOW max_parallel_workers_per_gather;'
```

```text
Filesystem      Size  Used Avail Use% Mounted on
shm              64M   64M     0 100% /dev/shm
2026-10-03 10:14:52.118 UTC [412] ERROR:  could not resize shared memory segment "/PostgreSQL.2891021530" to 8388608 bytes: No space left on device
posix
2
```

**What the output tells you:** /dev/shm is the 64 MB default and full while the query runs; POSIX shared memory with two parallel workers per query means every parallel plan competes for that space.

**Fix:**

```yaml
# Compose: a bigger /dev/shm (RAM, so keep it inside the memory limit)
services:
  db:
    image: postgres:17-bookworm
    shm_size: 256mb
```

```yaml
# Kubernetes: memory-backed /dev/shm; it counts against the pod's memory limit
spec:
  volumes:
    - name: dshm
      emptyDir:
        medium: Memory
        sizeLimit: 1Gi
  containers:
    - name: postgres
      volumeMounts:
        - name: dshm
          mountPath: /dev/shm
```

With docker run, use `--shm-size=256m`; a daemon-wide default is `"default-shm-size": "256M"` in /etc/docker/daemon.json. For Swarm services, including Dokploy databases, mount a tmpfs at /dev/shm with a size limit (`docker service update --mount-add type=tmpfs,destination=/dev/shm,tmpfs-size=268435456 SERVICE`, or the advanced mount settings in Dokploy), because `docker stack deploy` has long ignored shm_size for services (it prints "Ignoring unsupported options: shm_size"; check whether your Docker version still warns). Recreate the container afterwards; a restart keeps the old size.

**Why this fix works:** a larger /dev/shm gives the dynamic shared memory segments room. Switching dynamic_shared_memory_type to mmap or turning parallel query off also stops the error, by making queries slower or moving shared memory to disk; use that only as a stop-gap.

**Prevent it:** put shm_size (or the tmpfs mount) in every Postgres template, sized below the memory limit, and alert on this log line in your log pipeline.

**Next step:** [Databases: Databases in Docker](38-learn-databases-ops.md) · [Slow system: container slow, host fast](23-playbook-slow-system.md) · KodeKloud: *Docker Certified Associate* — Docker Engine – Security (namespaces, capabilities, cgroups, resource limits) · [Docker docs](https://docs.docker.com/)

**Community threads:** [docker-library/postgres#416](https://github.com/docker-library/postgres/issues/416) · [Dokploy#3975](https://github.com/Dokploy/dokploy/issues/3975) · [pgsql mailing list: could not resize shared memory segment](https://www.postgresql.org/message-id/20191216215314.qvrtgxaz4m755geq%40development) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22could+not+resize+shared+memory+segment%22+docker) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=could+not+resize+shared+memory+segment+docker&restrict_sr=1)

### 1.6 Dokploy's own Postgres won't start

> **Seen as:** the panel is down, dokploy-postgres logs `PANIC:  could not locate a valid checkpoint record` or `invalid record length`, and the panel logs `getaddrinfo ENOTFOUND dokploy-postgres` · **Where:** the Dokploy control plane after a restart loop (a failed update, low memory, Docker daemon restarts) · **Level:** [L3 · Senior] · **How common:** Dokploy#2436 (20 comments), with related threads #1869 (migration failed after a server restart) and #3883 (database wiped after a Docker path change)

**Why it happens:** Dokploy keeps projects, domains and settings in its own Postgres service. Repeated hard kills of that container (OOM kills on a small VPS, daemon restarts, short stop grace periods) on storage that loses writes can leave the WAL and checkpoint records inconsistent. Without a separate backup of that database and /etc/dokploy, recovery means rebuilding every project by hand.

**Diagnose:**

```bash
docker service ps dokploy-postgres --no-trunc --format '{{.Name}} {{.CurrentState}} {{.Error}}' | head -3
docker service logs dokploy-postgres --tail 50 2>&1 | grep -E 'PANIC|invalid record|interrupted'   # sample below: task prefix and timestamps trimmed
journalctl -k --since '-2 days' | grep -iE 'out of memory|killed process' | tail -1
df -h /var/lib/docker
```

```text
dokploy-postgres.1 Running 8 seconds ago
dokploy-postgres.1 Failed 41 seconds ago "task: non-zero exit (1)"
dokploy-postgres.1 Failed about a minute ago "task: non-zero exit (1)"
LOG:  database system was interrupted; last known up at 2026-10-02 23:58:11 UTC
LOG:  invalid record length at 0/1A2B3C8: expected at least 24, got 0
PANIC:  could not locate a valid checkpoint record
Oct 02 23:58:09 manager1 kernel: Out of memory: Killed process 2741 (postgres) total-vm:1184212kB, anon-rss:212044kB
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        40G   24G   15G  62% /
```

**What the output tells you:** an OOM kill interrupted Postgres mid-write; the checkpoint record the control file points to is now unreadable, so the server panics on every start and Swarm keeps restarting it. Disk space isn't the problem; memory is.

**Fix:**

```bash
docker service scale dokploy=0 dokploy-postgres=0           # stop the restart loop first
docker volume ls --format '{{.Name}}' | grep -i postgres    # find the panel's volume: PANEL_PG_VOLUME
docker run --rm -v PANEL_PG_VOLUME:/src:ro -v pg-pristine:/dst alpine cp -a /src/. /dst/
# Preferred: restore the latest Dokploy panel backup (Web Server > Backups) instead of repairing.
# Last resort, on a SECOND copy only: reset the WAL so the server can start, then dump at once
docker run --rm -v pg-pristine:/src:ro -v pg-work:/dst alpine cp -a /src/. /dst/
docker run --rm -u postgres -v pg-work:/var/lib/postgresql/data postgres:16 pg_resetwal -f /var/lib/postgresql/data
```

Then start a throwaway postgres:16 container on pg-work, pg_dump the dokploy database immediately, and restore that dump into a fresh volume for the real service. pg_resetwal discards WAL that wasn't checkpointed, so the latest changes may be lost or inconsistent; that's why it runs on a copy and why its result is dumped and reloaded rather than used as is.

**Why this fix works:** stopping the loop prevents further damage, the pristine copy keeps every option open, and a backup restore is consistent by construction, while pg_resetwal only makes the server start.

**Prevent it:** turn on Dokploy's panel backups to off-site S3 and test one restore (module 45, entry 10.4), give the manager enough RAM plus swap, and hold the Docker packages on the Dokploy node (`apt-mark hold`) so unattended upgrades can't restart the daemon under it.

**Next step:** [Dokploy: Restoring Dokploy on a new server](45-dokploy-and-self-hosted-paas.md) · [Memory](04-memory.md) · KodeKloud: *Fundamentals of SRE* — Incident Management · [Dokploy backups docs](https://docs.dokploy.com/docs/core/backups)

**Community threads:** [Dokploy#2436](https://github.com/Dokploy/dokploy/issues/2436) · [Dokploy issues about backups](https://github.com/Dokploy/dokploy/issues?q=is%3Aissue+backup+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=postgres+%22could+not+locate+a+valid+checkpoint+record%22+docker) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+postgres+corrupted&restrict_sr=1)

## 2. PostgreSQL connections and pooling

Connection problems come in layers: does a TCP connection arrive (listen address, firewall, network), does a rule admit it (pg_hba.conf, TLS), and is there a free slot (max_connections, pools)? Walk them in that order and each error message tells you which layer you're on.

### 2.1 Can't connect: refused, pg_hba or localhost

> **Seen as:** `connection to server at "10.0.1.10", port 5432 failed: Connection refused`, `FATAL:  no pg_hba.conf entry for host "10.0.1.20", user "shop", database "shop", no encryption`, or from a container `connect ECONNREFUSED 127.0.0.1:5432` and `getaddrinfo ENOTFOUND shop-db-x1y2z3` · **Where:** apps on another VM, GitLab runners, Dokploy apps talking to Dokploy databases, AWS RDS · **Level:** [L1 · Junior] · **How common:** one of the most viewed PostgreSQL questions for over a decade; Dokploy#507 (35 comments) and #2987 for container networks; back on RDS since PostgreSQL 15 parameter groups force SSL

**Why it happens:** each message names a different layer. *Refused* means nothing listens on that address: Ubuntu's package sets listen_addresses = 'localhost', the service is down, or a firewall rejects (a timeout instead points to a DROP rule or a security group). *No pg_hba.conf entry* means TCP arrived but no rule matches the client address, user, database and TLS state; on RDS for PostgreSQL 15 and later, rds.force_ssl=1 is the default, so clients without TLS get the "no encryption" variant. Inside a container, localhost is the container itself, and a Dokploy database answers only to its internal name on the network it shares with the app; an isolated Compose deployment sits on its own network.

**Diagnose:**

```bash
# On the database host
sudo ss -ltnp | grep 5432                         # 127.0.0.1:5432 means localhost only
sudo -u postgres psql -Atc 'SHOW listen_addresses;' -c 'SHOW hba_file;'
sudo tail -n 5 /var/log/postgresql/postgresql-16-main.log
# From the client (VM or container)
nc -vz -w 3 10.0.1.10 5432
docker exec APP_CONTAINER getent hosts shop-db-x1y2z3   # Dokploy: does the internal name resolve?
```

```text
LISTEN 0      200        127.0.0.1:5432       0.0.0.0:*    users:(("postgres",pid=1184,fd=6))
localhost
/etc/postgresql/16/main/pg_hba.conf
nc: connect to 10.0.1.10 port 5432 (tcp) failed: Connection refused
```

**What the output tells you:** the server listens only on loopback, so remote clients are refused before pg_hba.conf is even read. Fix the listener first; the next error you see, if any, will be the pg_hba.conf one. If getent prints nothing inside a container, the app is on the wrong network or uses the wrong name.

**Fix:**

```bash
# 1. Listen on the private address too (written to postgresql.auto.conf), then restart
sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses = 'localhost,10.0.1.10';"
sudo systemctl restart postgresql
# 2. Admit the app subnet with TLS and SCRAM, then reload (no restart needed)
echo "hostssl shop shop 10.0.1.0/24 scram-sha-256" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
sudo -u postgres psql -c 'SELECT pg_reload_conf();'
# 3. Firewall: only the app subnet may reach 5432
sudo ufw allow from 10.0.1.0/24 to any port 5432 proto tcp
```

Containers and Dokploy: use the Internal Connection URL from the database page (service name and internal port), keep the app on the same network (for an isolated Compose deployment, define the database in the same file, or attach the service to dokploy-network as an external network), and never use localhost. RDS: connect with sslmode=verify-full and the RDS CA bundle instead of switching rds.force_ssl off.

**Why this fix works:** listen_addresses opens the socket, pg_hba.conf decides who may use it (the first matching line wins, so specific rules go first), and the firewall limits who can reach it at all. Don't answer the error with `host all all 0.0.0.0/0 trust` or a published 5432: Docker-published ports bypass UFW, and open databases are found by scanners within minutes.

**Prevent it:** bind database ports to private addresses only, keep pg_hba.conf in Git (an Ansible template), and write down per project which network each app and database share.

**Next step:** [Databases: listen_addresses and pg_hba.conf](38-learn-databases-ops.md) · [Dokploy: App can't reach its database](45-dokploy-and-self-hosted-paas.md) · [Ports inventory](22-playbook-ports-inventory.md) · KodeKloud: *DevOps Pre-Requisite Course* — 2 Tier Applications · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [Fix "no pg_hba.conf entry for host" (cause map)](https://mydba.dev/blog/no-pg-hba-conf-entry-for-host-fix) · [AWS docs: SSL with PostgreSQL on RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html) · [Dokploy#2987](https://github.com/Dokploy/dokploy/issues/2987) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22no+pg_hba.conf+entry+for+host%22+listen_addresses) · [Server Fault](https://serverfault.com/search?q=postgresql+remote+connection+refused+listen_addresses) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+database+connection+internal&restrict_sr=1)

### 2.2 Too many clients already

> **Seen as:** `FATAL:  sorry, too many clients already`, `FATAL:  remaining connection slots are reserved for roles with the SUPERUSER attribute`, or MySQL `ERROR 1040 (HY000): Too many connections`, while the database CPU is idle · **Where:** after scaling an app, adding workers or deploying a connection leak · **Level:** [L2 · Mid-level] · **How common:** evergreen on every database forum; postmortems from incident.io (pool exhaustion) and GitHub (ProxySQL connection exhaustion) in Dan Luu's list

**Why it happens:** every app process opens its own pool, so the real number is replicas × processes × pool size, and it passes max_connections (PostgreSQL default 100, MySQL 151) faster than anyone expects. Leaked connections and sessions stuck "idle in transaction" hold slots; cron or serverless bursts open many short connections; and raising max_connections costs memory for every backend in PostgreSQL.

**Diagnose:**

```sql
-- Who holds the slots?
SELECT state, count(*) FROM pg_stat_activity GROUP BY 1 ORDER BY 2 DESC;
SELECT usename, application_name, client_addr, count(*)
FROM pg_stat_activity GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 3;
SHOW max_connections;
-- MySQL: SHOW GLOBAL STATUS LIKE 'Threads_connected'; SHOW PROCESSLIST;
```

```text
        state        | count
---------------------+-------
 idle                |    61
 idle in transaction |    27
 active              |     6
                     |     6
 usename  | application_name | client_addr | count
----------+------------------+-------------+-------
 shop     | shop-worker      | 10.0.1.21   |    48
 shop     | shop-web         | 10.0.1.20   |    40
 postgres | psql             |             |     1
 max_connections
-----------------
 100
```

**What the output tells you:** 27 sessions sit idle inside a transaction (a leak, or a missing commit in the worker), and two services already hold 88 of 100 slots. Raising max_connections would only move the cliff.

**Fix:**

```sql
-- Stop the bleeding: end sessions idle in a transaction for more than 10 minutes
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle in transaction' AND now() - state_change > interval '10 min';
-- Stop it coming back (per database; new sessions pick it up)
ALTER DATABASE shop SET idle_in_transaction_session_timeout = '5min';
```

Then fix the leak in the app, and size pools so that replicas × pool size stays below max_connections minus a reserve for admins and migrations. When many clients must share few connections, put PgBouncer in front (entries 2.3 and 2.4); for MySQL, ProxySQL plays that role, and wait_timeout ends idle sessions.

**Why this fix works:** terminating idle-in-transaction sessions frees slots and releases their locks; the timeout makes the database enforce what the app forgot; a connection budget turns "too many clients" into a capacity number you plan. Restarting the database also frees the slots, but it drops every healthy session and hides which client leaked.

**Prevent it:** alert when connections used divided by max_connections passes 80% (postgres_exporter or mysqld_exporter), keep a connection budget per service in the repository, and make pool size a reviewed setting, not a library default.

**Next step:** [Databases: max_connections and PgBouncer](38-learn-databases-ops.md) · [Databases: Too many connections](38-learn-databases-ops.md) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [PgBouncer config](https://www.pgbouncer.org/config.html)

**Community threads:** [incident.io: connection pool exhaustion](https://incident.io/blog/database-performance) · [PgBouncer configuration: pool sizes](https://www.pgbouncer.org/config.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22sorry%2C+too+many+clients+already%22) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=too+many+clients+already+pgbouncer&restrict_sr=1)

### 2.3 PgBouncer login fails, direct login works

> **Seen as:** `FATAL:  password authentication failed for user "shop"`, `ERROR:  no such user: shop` or `server login failed: wrong password type` through port 6432, while psql straight to 5432 works · **Where:** PgBouncer put in front of PostgreSQL 14 or later (SCRAM by default), often as a container next to the database in Dokploy or Kubernetes · **Level:** [L2 · Mid-level] · **How common:** a common setup question in the PgBouncer tracker and on Stack Overflow since password_encryption defaulted to scram-sha-256

**Why it happens:** PgBouncer authenticates the client itself, then logs in to PostgreSQL. auth_type must match how passwords are stored: a SCRAM verifier can't be used for md5 authentication. userlist.txt may miss the user, quote it wrongly, or hold an old hash after a password change; with auth_query, the auth_user may lack rights to read pg_authid, or the lookup function may not exist in that database. MD5 passwords are deprecated since PostgreSQL 18, so SCRAM is the direction anyway.

**Diagnose:**

```bash
docker logs PGBOUNCER 2>&1 | grep -iE 'login failed|no such user|password' | tail -1
sudo -u postgres psql -Atc "SELECT rolname, left(rolpassword, 14) FROM pg_authid WHERE rolname = 'shop';"
grep -E '^(auth_type|auth_file|auth_user|auth_query)' /etc/pgbouncer/pgbouncer.ini
psql 'host=10.0.1.10 port=6432 dbname=shop user=shop' -c 'SELECT 1'
```

```text
2026-10-03 11:02:41.510 UTC [1] WARNING C-0x55d3c1a2b0e0: shop/shop@10.0.1.20:51234 pooler error: password authentication failed
shop|SCRAM-SHA-256$
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
psql: error: connection to server at "10.0.1.10", port 6432 failed: FATAL:  password authentication failed
```

**What the output tells you:** the role stores a SCRAM verifier, but PgBouncer is configured for md5, so it can never check the client's password. Either switch PgBouncer to SCRAM, or stop keeping passwords in a file at all.

**Fix:**

```ini
[pgbouncer]
auth_type = scram-sha-256
; userlist.txt now holds only the auth user's SCRAM secret:
; "pgbouncer_auth" "SCRAM-SHA-256$4096:SALT$STOREDKEY:SERVERKEY"
auth_file = /etc/pgbouncer/userlist.txt
; every other password is looked up in PostgreSQL at login time
auth_user = pgbouncer_auth
auth_query = SELECT usename, passwd FROM pgbouncer.get_auth($1)
```

```sql
-- once per cluster
CREATE ROLE pgbouncer_auth LOGIN PASSWORD 'AUTH_PASSWORD';
-- in every database PgBouncer serves
CREATE SCHEMA pgbouncer;
GRANT USAGE ON SCHEMA pgbouncer TO pgbouncer_auth;
CREATE FUNCTION pgbouncer.get_auth(p_usename text)
RETURNS TABLE (usename name, passwd text)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog AS
$$ SELECT rolname, rolpassword FROM pg_authid WHERE rolname = p_usename AND rolcanlogin $$;
REVOKE ALL ON FUNCTION pgbouncer.get_auth(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pgbouncer.get_auth(text) TO pgbouncer_auth;
```

Reload PgBouncer after any change (RELOAD on the admin console, or SIGHUP). In containers, generate userlist.txt from secrets at start-up instead of baking it into the image.

**Why this fix works:** with matching auth types PgBouncer can verify the client and reuse the SCRAM secret to log in to the server; with auth_query the only copy of each password lives in PostgreSQL, so a password rotation needs no PgBouncer change. Don't "solve" it with auth_type = trust or a plain-text password file.

**Prevent it:** use auth_query, and add a CI or health check that logs in through PgBouncer, not only directly.

**Next step:** [Databases: max_connections and PgBouncer](38-learn-databases-ops.md) · [Security: Secrets management](37-learn-security-devsecops.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose · [PgBouncer config](https://www.pgbouncer.org/config.html)

**Community threads:** [PgBouncer config: auth_type, auth_file, auth_query](https://www.pgbouncer.org/config.html) · [pgbouncer issues: SCRAM and auth_query](https://github.com/pgbouncer/pgbouncer/issues?q=scram+auth_query) · Search: [Stack Overflow](https://stackoverflow.com/search?q=pgbouncer+scram-sha-256+%22password+authentication+failed%22) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=pgbouncer+scram+userlist&restrict_sr=1)

### 2.4 PgBouncer transaction mode breaks statements

> **Seen as:** random `ERROR:  prepared statement "S_1" does not exist` or `ERROR:  prepared statement "__asyncpg_stmt_1__" already exists`, plus session settings and advisory locks that seem to forget themselves · **Where:** PgBouncer switched to pool_mode = transaction to save connections · **Level:** [L3 · Senior] · **How common:** the best-known PgBouncer pitfall; JDBC, asyncpg, Prisma and Rails users all hit it; protocol-level prepared statement support arrived in PgBouncer 1.21

**Why it happens:** in transaction mode, two transactions from one client can run on two different server connections. A statement prepared on one backend doesn't exist on the next, and session state doesn't survive between transactions: SET, LISTEN/NOTIFY, session advisory locks, temporary tables and WITH HOLD cursors. Versions before 1.21, or max_prepared_statements = 0 (the default from 1.21 until 1.24 made it 200), don't track prepared statements at all.

**Diagnose:**

```bash
psql -h 10.0.1.10 -p 6432 -U pgbouncer_admin pgbouncer -c 'SHOW VERSION;'
psql -h 10.0.1.10 -p 6432 -U pgbouncer_admin pgbouncer -c 'SHOW CONFIG;' | grep -E 'pool_mode|max_prepared_statements'
grep -c 'prepared statement' /var/log/shop/app.log
```

```text
     version
------------------
 PgBouncer 1.21.0
 max_prepared_statements   | 0           | 0       | yes
 pool_mode                 | transaction | session | yes
412
```

**What the output tells you:** transaction pooling is on but prepared-statement tracking is off (0), so every driver that prepares server-side statements breaks whenever its next transaction lands on another backend.

**Fix:**

```ini
[databases]
shop = host=10.0.1.10 dbname=shop
; a session pool for clients that need a real session: migrations, LISTEN, advisory locks
shop_session = host=10.0.1.10 dbname=shop pool_mode=session

[pgbouncer]
pool_mode = transaction
; track protocol-level prepared statements per client (0 disables tracking)
max_prepared_statements = 200
```

If you can't upgrade yet (1.26 is current at the time of writing), turn server-side prepares off in the driver: JDBC prepareThreshold=0, asyncpg statement_cache_size=0, Prisma ?pgbouncer=true. Run migrations straight against PostgreSQL or through the session pool, never through the transaction pool.

**Why this fix works:** since 1.21 PgBouncer remembers protocol-level prepared statements per client and prepares them again on whichever server connection the next transaction lands on; session-dependent work gets its own pool, where a client keeps its backend. SQL-level PREPARE and the other session features still don't work in transaction mode, which is why you document who may use it.

**Prevent it:** a short list of services allowed on the transaction pool, and a CI test that runs each driver against PgBouncer in transaction mode.

**Next step:** [Databases: max_connections and PgBouncer](38-learn-databases-ops.md) · [CI/CD toolbox: Deploying from CI](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab (services) · [PgBouncer](https://www.pgbouncer.org/)

**Community threads:** [PgBouncer config: pool_mode, max_prepared_statements](https://www.pgbouncer.org/config.html) · [PgBouncer homepage and releases](https://www.pgbouncer.org/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=pgbouncer+%22prepared+statement%22+%22does+not+exist%22+transaction+mode) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=pgbouncer+transaction+mode+prepared+statements&restrict_sr=1)

## 3. MySQL and MariaDB

MySQL accounts are a user plus a host, Ubuntu logs root in through the socket, and every major version changes something about authentication. Most MySQL tickets are one of those three facts.

### 3.1 ERROR 1698 for root on a fresh install

> **Seen as:** `ERROR 1698 (28000): Access denied for user 'root'@'localhost'` for every password you try, and phpMyAdmin or the app can't log in as root · **Where:** MySQL 8.x or MariaDB just installed with apt on Ubuntu · **Level:** [L0 · Fresher] · **How common:** one of the most visited MySQL questions on Ask Ubuntu and Stack Overflow, with countless blog fixes

**Why it happens:** Ubuntu's packages create root with auth_socket (MySQL) or unix_socket (MariaDB): the server asks the kernel which OS user is on the other end of the socket, and only the OS root user may log in as MySQL root. Passwords are ignored for that account. Apps shouldn't use root anyway, so the real gap is a missing app user.

**Diagnose:**

```bash
sudo mysql -e "SELECT user, host, plugin FROM mysql.user;"
sudo journalctl -u mysql -n 5 --no-pager
```

```text
+------------------+-----------+-----------------------+
| user             | host      | plugin                |
+------------------+-----------+-----------------------+
| debian-sys-maint | localhost | caching_sha2_password |
| mysql.infoschema | localhost | caching_sha2_password |
| mysql.session    | localhost | caching_sha2_password |
| mysql.sys        | localhost | caching_sha2_password |
| root             | localhost | auth_socket           |
+------------------+-----------+-----------------------+
```

**What the output tells you:** root uses auth_socket, so `sudo mysql` works and `mysql -u root -p` never will, whatever the password. Nothing is broken.

**Fix:**

```sql
-- Admin work: just use `sudo mysql`. For the app, create its own database and user:
CREATE DATABASE shop;
CREATE USER 'shop'@'localhost' IDENTIFIED BY 'APP_PASSWORD';
GRANT ALL PRIVILEGES ON shop.* TO 'shop'@'localhost';
```

Only if a tool really needs password login for root: `ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'ROOT_PASSWORD';`. On MariaDB, `ALTER USER root@localhost IDENTIFIED VIA unix_socket OR mysql_native_password USING PASSWORD('ROOT_PASSWORD');` keeps socket login and adds a password.

**Why this fix works:** socket authentication ties database root to OS root, which is stronger than a password; an app user with rights on one database limits what a leaked app password can do.

**Prevent it:** keep root on socket auth, create one least-privilege user per app in your provisioning (the Ansible community.mysql.mysql_user module), and keep app passwords in your secret store.

**Next step:** [Databases: Install, layout and the mysql client](38-learn-databases-ops.md) · [Users & permissions](10-users-permissions-security.md) · KodeKloud: *DevOps Pre-Requisite Course* — 2 Tier Applications · [MySQL docs](https://dev.mysql.com/doc/)

**Community threads:** [phoenixNAP: Access denied for user root@localhost](https://phoenixnap.com/kb/access-denied-for-user-root-localhost) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22ERROR+1698%22+%22Access+denied+for+user%22+root+localhost+auth_socket) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=mysql+root+auth_socket&restrict_sr=1)

### 3.2 Host not allowed, bind-address and socket errors

> **Seen as:** `ERROR 1130 (HY000): Host '10.0.1.20' is not allowed to connect to this MySQL server`, `ERROR 2003 (HY000): Can't connect to MySQL server on '10.0.1.10:3306' (111)`, or inside a container `ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)` · **Where:** apps on another VM or in another container, GUI clients, CI jobs · **Level:** [L1 · Junior] · **How common:** evergreen top questions on Stack Overflow and Server Fault, and a run of docker-library/mysql issues

**Why it happens:** MySQL accounts are user plus host, so 'shop'@'localhost' can't log in from 10.0.1.20 (1130). Error 2003 with 111 (refused) means nothing listens there: Ubuntu's config sets bind-address = 127.0.0.1 (in /etc/mysql/mysql.conf.d/mysqld.cnf; 50-server.cnf for MariaDB), or a firewall rejects. Error 2002 is a client-side surprise: `-h localhost` tells the client to use the Unix socket, and in a client container there is no server socket. Use 127.0.0.1 or the service name.

**Diagnose:**

```bash
sudo ss -ltnp | grep ':3306 '                            # the space skips the X Protocol port 33060
sudo mysql -e "SELECT user, host FROM mysql.user WHERE user = 'shop';"
grep -R '^bind-address' /etc/mysql/
mysql -h 10.0.1.10 -P 3306 -u shop -p -e 'SELECT 1'     # from the client
```

```text
LISTEN 0      151        127.0.0.1:3306       0.0.0.0:*    users:(("mysqld",pid=2231,fd=23))
+------+-----------+
| user | host      |
+------+-----------+
| shop | localhost |
+------+-----------+
/etc/mysql/mysql.conf.d/mysqld.cnf:bind-address		= 127.0.0.1
ERROR 2003 (HY000): Can't connect to MySQL server on '10.0.1.10:3306' (111)
```

**What the output tells you:** two layers are closed: the server listens on loopback only (2003), and once that's fixed the account would still be localhost-only (1130).

**Fix:**

```bash
# 1. Listen on the private address, then restart
sudo sed -i 's/^bind-address.*/bind-address = 10.0.1.10/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql
# 2. An account for the app subnet (the host part matters)
sudo mysql -e "CREATE USER 'shop'@'10.0.1.%' IDENTIFIED BY 'APP_PASSWORD'; GRANT ALL PRIVILEGES ON shop.* TO 'shop'@'10.0.1.%';"
# 3. Firewall: only the app subnet
sudo ufw allow from 10.0.1.0/24 to any port 3306 proto tcp
```

In Compose, Swarm and Dokploy, connect to the service name and port 3306 (for example DB_HOST=shop-mysql), never localhost. The official mysql image creates root for any host by default (MYSQL_ROOT_HOST), so container 1130 errors usually involve accounts created later for localhost only.

**Why this fix works:** bind-address opens the listener on the right interface, a host-scoped account admits exactly the app subnet, and the firewall narrows who can try. 'shop'@'%' plus bind-address = 0.0.0.0 on a public interface also "works", and is how databases end up in breach reports.

**Prevent it:** host-restricted accounts per app, 3306 never published to the internet, and a ports inventory that flags any database listener on a public address.

**Next step:** [Databases: bind-address, users and grants](38-learn-databases-ops.md) · [Ports inventory](22-playbook-ports-inventory.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking (Configure Packet Filtering) · [MySQL docs](https://dev.mysql.com/doc/)

**Community threads:** [docker-library/mysql#275](https://github.com/docker-library/mysql/issues/275) · [docker-library/mysql#435](https://github.com/docker-library/mysql/issues/435) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22is+not+allowed+to+connect+to+this+MySQL+server%22) · [Server Fault](https://serverfault.com/search?q=mysql+bind-address+remote+connection+ERROR+2003) · [Reddit r/mysql](https://www.reddit.com/r/mysql/search/?q=Host+is+not+allowed+to+connect&restrict_sr=1)

### 3.3 MySQL 8.4 and MariaDB 11 bumps break clients

> **Seen as:** `ERROR 1524 (HY000): Plugin 'mysql_native_password' is not loaded`, `Public Key Retrieval is not allowed`, or after a MariaDB bump `/bin/sh: 1: mysqladmin: not found` and a healthcheck that never passes · **Where:** mysql:8.0 bumped to 8.4 (or :latest), RDS engine upgrades, mariadb:10.x bumped to 11.x in Compose stacks and CI services · **Level:** [L2 · Mid-level] · **How common:** very common since 8.4 (2024) disabled mysql_native_password by default, with more upgrades now that MySQL 8.0 reached end of life in 2026; MariaDB wrote a blog post because the missing mysqladmin surprised so many people

**Why it happens:** MySQL 8.0 made caching_sha2_password the default, 8.4 disables mysql_native_password unless you enable it, and 9.x removes it. Accounts created years ago still use the old plugin, default_authentication_plugin no longer exists in 8.4, and old client libraries can't speak caching_sha2 (and without TLS the client must be allowed to fetch the server's RSA key). On the MariaDB side, the 11.x official image dropped the mysql-named compatibility programs (mysql, mysqladmin, mysqldump), so copy-pasted healthchecks and backup scripts fail, and a major bump without mariadb-upgrade leaves the system tables old.

**Diagnose:**

```bash
docker exec -it MYSQL mysql -u root -p -e "SELECT user, host, plugin FROM mysql.user WHERE user NOT LIKE 'mysql.%'; SELECT VERSION();"
docker inspect --format '{{json .State.Health.Log}}' MARIADB | jq -r '.[-1].Output'
docker exec MARIADB sh -c 'ls /usr/bin | grep -xE "(mysql|mariadb)(-?admin|-?dump|-upgrade)?"'
```

```text
+------+-----------+-----------------------+
| user | host      | plugin                |
+------+-----------+-----------------------+
| root | %         | caching_sha2_password |
| shop | %         | mysql_native_password |
| root | localhost | caching_sha2_password |
+------+-----------+-----------------------+
+-----------+
| VERSION() |
+-----------+
| 8.4.6     |
+-----------+
/bin/sh: 1: mysqladmin: not found
mariadb
mariadb-admin
mariadb-dump
mariadb-upgrade
```

**What the output tells you:** the app account still uses mysql_native_password, which 8.4 no longer loads, and the MariaDB healthcheck calls a program its image doesn't ship any more. Neither database is broken.

**Fix:**

```sql
-- MySQL 8.4: move each old account to the current plugin
ALTER USER 'shop'@'%' IDENTIFIED WITH caching_sha2_password BY 'APP_PASSWORD';
```

```yaml
# MariaDB 11: the healthcheck script that ships in the image, and an automatic upgrade step
services:
  db:
    image: mariadb:11.4
    environment:
      MARIADB_AUTO_UPGRADE: "1"        # runs mariadb-upgrade after a major bump; back up first
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      retries: 5
```

Update client drivers, and use TLS (allowPublicKeyRetrieval=true in JDBC is for trusted networks only). The bridge `mysql_native_password=ON` in my.cnf exists only in 8.4; in 9.x it is gone. In scripts, replace mysql, mysqldump and mysqladmin with mariadb, mariadb-dump and mariadb-admin.

**Why this fix works:** moving accounts to the current plugin removes the dependency on a disabled one; the image's healthcheck.sh checks real readiness (connection and InnoDB initialised) rather than a ping that passes too early; mariadb-upgrade brings the system tables in line with the new server. Pinning 8.0 forever is not a fix: it's end of life.

**Prevent it:** before any major bump, inventory account plugins and client driver versions, pin an LTS line (mysql:8.4, mariadb:11.4) rather than latest, and keep healthchecks and backup scripts in the same repository as the compose file, tested in CI.

**Next step:** [Databases: MySQL and MariaDB operations](38-learn-databases-ops.md) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose · [MySQL 8.4 manual: caching_sha2_password](https://dev.mysql.com/doc/refman/8.4/en/caching-sha2-pluggable-authentication.html)

**Community threads:** [Mydbops: MySQL 8.4 incompatible changes](https://www.mydbops.com/blog/mydbops-mysql-8-4-incompatible-changes-upgrade-guide) · [AWS re:Post: upgrade to 8.4.3, unknown authentication method](https://repost.aws/questions/QUAYvOF4YxS3OFY-wgFjw9ZA/mysql-upgrade-to-8-4-3-unknown-authentication-method) · [MariaDB.org: healthcheck without mysqladmin](https://mariadb.org/mariadb-server-docker-official-images-healthcheck-without-mysqladmin/) · [wallabag/docker#381](https://github.com/wallabag/docker/issues/381) · [mage-os/github-actions#365](https://github.com/mage-os/github-actions/issues/365) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22Plugin+%27mysql_native_password%27+is+not+loaded%22) · [Reddit r/mysql](https://www.reddit.com/r/mysql/search/?q=mysql+8.4+mysql_native_password&restrict_sr=1)

### 3.4 mysqldump and import errors

> **Seen as:** on dump, `mysqldump: Error: 'Access denied; you need (at least one of) the PROCESS privilege(s) for this operation' when trying to dump tablespaces`; on import, `ERROR 1273 (HY000) at line 22: Unknown collation: 'utf8mb4_0900_ai_ci'`, `ERROR 1227 (42000): Access denied; you need (at least one of) the SUPER privilege(s) for this operation` or `ERROR 2006 (HY000): MySQL server has gone away` · **Where:** least-privilege backup jobs in cron or CI, migrations from MySQL 8 to MariaDB, restores into RDS · **Level:** [L2 · Mid-level] · **How common:** MySQL bug #100219 (after 8.0.21 and 5.7.31) and vendor knowledge-base pages (Acquia, Plesk, Broadcom); both import errors are top MySQL search results

**Why it happens:** since 8.0.21 and 5.7.31, dumping tablespace information needs the global PROCESS privilege. Dumps carry DEFINER clauses naming the original user and host, and a SET @@GLOBAL.GTID_PURGED line, which managed targets such as RDS reject without SUPER. utf8mb4_0900_ai_ci exists only in MySQL 8, so MariaDB and MySQL 5.7 don't know it. "Gone away" is usually one statement bigger than max_allowed_packet on the server or the client, an import idling past wait_timeout, or mysqld killed by the OOM killer mid-import. And without --single-transaction, InnoDB dumps are either inconsistent or lock tables while they run.

**Diagnose:**

```bash
sudo mysql -e "SHOW GRANTS FOR 'backup'@'localhost';"
grep -m2 -E 'DEFINER|GTID_PURGED' shop.sql; grep -c utf8mb4_0900_ai_ci shop.sql
sudo mysql -e "SHOW VARIABLES WHERE Variable_name IN ('max_allowed_packet','wait_timeout');"
journalctl -k | grep -i 'killed process' | tail -1        # did mysqld die during an import?
```

```text
Grants for backup@localhost
GRANT USAGE ON *.* TO `backup`@`localhost`
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON `shop`.* TO `backup`@`localhost`
SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '3e11fa47-71ca-11e1-9e33-c80aa9429562:1-48213';
/*!50013 DEFINER=`admin`@`%` SQL SECURITY DEFINER */
1184
Variable_name	Value
max_allowed_packet	67108864
wait_timeout	28800
```

**What the output tells you:** the backup user lacks PROCESS, so its job needs --no-tablespaces; the dump carries a GTID line and definers a managed target will refuse; 1,184 uses of a MySQL-8-only collation will stop a MariaDB import; and any single statement above 64 MB will drop the connection.

**Fix:**

```bash
# A dump a least-privilege user can take and most targets accept
# (credentials in a 0600 option file, not on the command line)
set -o pipefail
mysqldump --defaults-extra-file=/etc/mysql/backup.cnf --single-transaction --routines --triggers \
  --no-tablespaces --set-gtid-purged=OFF shop | gzip > shop.sql.gz
# Importing into MariaDB or MySQL 5.7: rewrite the collation on a copy
gunzip -c shop.sql.gz | sed 's/utf8mb4_0900_ai_ci/utf8mb4_unicode_ci/g' > shop-target.sql
# Managed targets without SUPER: strip definers (or set log_bin_trust_function_creators=1 in the RDS parameter group)
sed -i 's/DEFINER=[^ ]* //g' shop-target.sql
# Big rows: raise the packet size on the server (max_allowed_packet=256M in my.cnf) and on the client
mysql --max_allowed_packet=256M -h 10.0.1.10 -u shop -p shop < shop-target.sql
```

**Why this fix works:** --single-transaction takes a consistent InnoDB snapshot without locking; --no-tablespaces skips the part that needs PROCESS; --set-gtid-purged=OFF and stripped definers remove statements that need SUPER on the target; utf8mb4_unicode_ci is the nearest collation both engines know (it sorts a few characters differently, so watch for duplicate-key errors on unique text columns); a larger packet lets the biggest INSERT through. Granting the backup user SUPER or ALL is the wrong fix.

**Prevent it:** pipefail and a check for the "-- Dump completed" trailer in every backup script, dumps made with the target engine in mind, and a test import on a scratch instance of the target version before migration day. For very large databases use mydumper and myloader, or a physical backup tool, instead of one giant SQL file.

**Next step:** [Databases: Logical backups: pg_dump and mysqldump](38-learn-databases-ops.md) · [Databases: MySQL physical backups and binlog PITR](38-learn-databases-ops.md) · KodeKloud: *DevOps Pre-Requisite Course* — 2 Tier Applications · [MySQL manual: mysqldump](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)

**Community threads:** [MySQL Bugs #100219](https://bugs.mysql.com/bug.php?id=100219) · [Acquia: you need the PROCESS privilege](https://docs.acquia.com/acquia-cloud-platform/help/93231-drush-throws-access-denied-you-need-least-one-process-privileges-error-message) · [Plesk KB: Unknown collation utf8mb4_0900_ai_ci](https://support.plesk.com/hc/en-us/articles/12389036812567-Unable-to-migrate-or-import-MySQL-8-databases-Unknown-collation-utf8mb4-0900-ai-ci) · [TablePlus: MySQL server has gone away](https://tableplus.com/blog/2018/11/mysql-server-has-gone-away-solved.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22Unknown+collation%3A+%27utf8mb4_0900_ai_ci%27%22) · [Stack Overflow (PROCESS)](https://stackoverflow.com/search?q=mysqldump+%22PROCESS+privilege%22+%22no-tablespaces%22) · [Reddit r/mysql](https://www.reddit.com/r/mysql/search/?q=mysqldump+import+server+has+gone+away&restrict_sr=1)

## 4. Redis, Valkey and MongoDB

Valkey, the Linux Foundation fork of Redis 7.2, behaves the same for every problem here; use valkey-cli where your image has no redis-cli. MongoDB problems in self-hosting are mostly about the image and the VM, not the database itself.

### 4.1 Redis exposed, protected mode and NOAUTH

> **Seen as:** unknown keys, a changed dir or dbfilename, or a crypto-miner on the host days after `ports: - "6379:6379"` was added "for debugging"; or the reverse, `DENIED Redis is running in protected mode because protected mode is enabled and no password is set for the default user` and `NOAUTH Authentication required.` · **Where:** Redis and Valkey containers with published ports; bare-metal installs reached from another host · **Level:** [L1 · Junior] · **How common:** internet-wide scanning for open 6379 never stops; the official image's documentation warns that it turns protected mode off

**Why it happens:** the official Redis image disables protected mode so other containers can reach it over Docker networks, and it sets no password. A published port therefore exposes an unauthenticated Redis to the world, and Docker-published ports bypass UFW. On Redis before 7.0 (or on 7.x and Valkey with enable-protected-configs set to yes), attackers use CONFIG SET dir and dbfilename to make Redis write its snapshot where they want it (a cron spool, an SSH authorized_keys file). Since 7.0 those two settings are immutable at runtime by default, but an open instance still gets its data read, wiped or held for ransom, and anyone who can run EVAL can reach Lua-engine bugs such as CVE-2025-49844 (a CVSS 10 remote code execution, fixed in Redis 6.2.20, 7.2.11, 7.4.6, 8.0.4 and 8.2.2 and in Valkey 7.2.11, 8.0.6 and 8.1.4). On a bare-metal install protected mode is on, so legitimate remote clients are refused until you configure authentication.

**Diagnose:**

```bash
docker ps --format '{{.Names}} {{.Ports}}' | grep 6379
nc -vz -w 3 203.0.113.10 6379                       # run from OUTSIDE your network: must fail
docker exec REDIS redis-cli CONFIG GET dir
docker exec REDIS redis-cli ACL LIST
```

```text
shop-redis 0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp
Connection to 203.0.113.10 6379 port [tcp/redis] succeeded!
1) "dir"
2) "/var/spool/cron/crontabs"
1) "user default on nopass sanitize-payload ~* &* +@all"
```

**What the output tells you:** Redis answers from the internet with no password (default user, nopass), and dir points at the cron spool (this is a pre-7.0 Redis, where dir can still be changed at runtime): someone has already used it to write files. This is a security incident, not a configuration tweak.

**Fix:**

```yaml
services:
  redis:
    image: redis:7.4                       # 7.4.6 or later (CVE-2025-49844), or valkey/valkey:8
    command: ["redis-server", "/usr/local/etc/redis/redis.conf"]
    volumes:
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro   # Dokploy: ../files/redis.conf (a File Mount)
    # no "ports:" at all: apps reach it as redis:6379 on the shared network
    # host-only access if you really need it: "127.0.0.1:6379:6379"
```

```text
# redis.conf: named ACL users instead of an open default user
user default off
user shop on >APP_PASSWORD ~* &* +@all -@dangerous
user ops on >OPS_PASSWORD ~* &* +@all
```

If it was exposed and dir or dbfilename changed, or you find unknown cron entries, SSH keys or processes, treat the host as compromised: isolate it, keep evidence, rebuild from a known-good image and rotate every secret it held. Restarting Redis doesn't remove what was written to disk. On bare metal, keep protected mode on, bind to a private address and add the same ACL users.

**Why this fix works:** without a published port the only way in is the Docker network; ACL users give each client its own password and take dangerous commands such as CONFIG away from the app, which closes the file-write trick. Turning protected mode off on bare metal to "fix" DENIED repeats the exposure.

**Prevent it:** never publish database ports; add a CI or lint rule that rejects 6379, 5432, 3306 and 27017 under compose ports; scan your public addresses from outside on a schedule.

**Next step:** [Databases: Network exposure](38-learn-databases-ops.md) · [Security: incident response](37-learn-security-devsecops.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Redis docs](https://redis.io/docs/)

**Community threads:** [Docker Hub: redis official image (security note)](https://hub.docker.com/_/redis) · [docker-library/redis#58](https://github.com/docker-library/redis/issues/58) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22DENIED+Redis+is+running+in+protected+mode%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=redis+exposed+hacked+miner&restrict_sr=1)

### 4.2 MISCONF: Redis can't persist to disk

> **Seen as:** `MISCONF Redis is configured to save RDB snapshots, but it's currently unable to persist to disk. Commands that may modify the data set are disabled` on every write while reads still work, and `Can't save in background: fork: Cannot allocate memory` in the log · **Where:** Sidekiq, Celery, session stores and caches on a small VPS or a nearly full Docker host · **Level:** [L1 · Junior] · **How common:** one of the most viewed Redis errors ever; a GitHub gist about it has collected comments for years

**Why it happens:** Redis saves snapshots by forking. With vm.overcommit_memory = 0 the kernel may refuse the fork, because on paper the child could need a full copy of the dataset. The disk holding the RDB or AOF file can also be full, or the data directory not writable (wrong volume ownership, a read-only mount). With stop-writes-on-bgsave-error yes, the default, Redis then blocks writes to protect your data.

**Diagnose:**

```bash
docker exec REDIS redis-cli INFO persistence | grep -E 'rdb_changes_since_last_save|rdb_last_bgsave_status|aof_last_write_status'
docker logs REDIS 2>&1 | grep -iE 'fork|overcommit' | tail -2
sysctl vm.overcommit_memory; df -h /var/lib/docker
```

```text
rdb_changes_since_last_save:184522
rdb_last_bgsave_status:err
aof_last_write_status:ok
1:M 03 Oct 2026 03:12:40.118 # WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition. ...
1:M 03 Oct 2026 03:12:40.119 # Can't save in background: fork: Cannot allocate memory
vm.overcommit_memory = 0
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        40G   31G  7.2G  82% /
```

**What the output tells you:** the disk has room; the fork is what fails, and the kernel's overcommit setting is the reason. 184,522 changes are at risk until a save succeeds.

**Fix:**

```bash
# On the HOST: sysctls like this aren't per container; the file makes it survive reboots
echo 'vm.overcommit_memory = 1' | sudo tee /etc/sysctl.d/99-redis.conf
sudo sysctl --system
# Save now and confirm
docker exec REDIS redis-cli BGSAVE
docker exec REDIS redis-cli INFO persistence | grep rdb_last_bgsave_status
```

If the disk was full or the directory not writable, free space or fix the ownership of the data volume first (the official image runs Redis as the redis user). For a pure cache that can be rebuilt, turn persistence off instead (`save ""` and `appendonly no`).

**Why this fix works:** with overcommit set to 1 the kernel allows the fork and relies on copy-on-write, which only copies pages that change during the save. Setting stop-writes-on-bgsave-error to no makes the error disappear while your data silently stops being saved; don't.

**Prevent it:** the sysctl in your host baseline (Ansible), a maxmemory well below host RAM, and alerts on rdb_last_bgsave_status and disk usage.

**Next step:** [Databases: Persistence with RDB and AOF](38-learn-databases-ops.md) · [Memory](04-memory.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts) · [Redis docs](https://redis.io/docs/)

**Community threads:** [Netdata: MISCONF Redis is configured to save RDB snapshots](https://www.netdata.cloud/guides/redis/redis-misconf-rdb-snapshots/) · [GitHub gist with years of comments](https://gist.github.com/kapkaev/4619127?permalink_comment_id=2739426) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22MISCONF+Redis+is+configured+to+save+RDB+snapshots%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=redis+MISCONF&restrict_sr=1)

### 4.3 OOM command not allowed at maxmemory

> **Seen as:** `OOM command not allowed when used memory > 'maxmemory'.` under load, or jobs that silently vanish after someone switched the eviction policy to LRU · **Where:** one Redis or Valkey instance used as both cache and job queue (Celery, Sidekiq, BullMQ) · **Level:** [L2 · Mid-level] · **How common:** a common error with dedicated guides from Netdata and others

**Why it happens:** maxmemory is reached while maxmemory-policy is noeviction, the safe default for queues, so writes are refused. Memory grew because of keys without TTLs, a backlog of unprocessed jobs, or large values. A cache wants eviction and a queue must never evict, so mixing both in one instance makes every policy wrong for half the data; an LRU policy will happily evict queued jobs.

**Diagnose:**

```bash
docker exec REDIS redis-cli INFO memory | grep -E 'used_memory_human|maxmemory_human|maxmemory_policy'
docker exec REDIS redis-cli INFO keyspace
docker exec REDIS redis-cli LLEN queue:default
docker exec REDIS redis-cli --bigkeys | grep '^Biggest'     # summary lines only, not the progress lines
```

```text
used_memory_human:1.00G
maxmemory_human:1.00G
maxmemory_policy:noeviction
db0:keys=2841177,expires=1203,avg_ttl=0,subexpiry=0
(integer) 1864220
Biggest   list found "queue:default" has 1864220 items
Biggest string found "session:9f3c2a71" has 18342 bytes
```

**What the output tells you:** 1.86 million jobs are waiting, so the consumers are down or too slow and the queue has filled memory; only 1,203 of 2.8 million keys have a TTL. Raising maxmemory buys hours, not a fix.

**Fix:**

```bash
# 1. Fix the cause: get the consumers running again so the backlog drains
docker service scale shop_worker=4
# 2. Queue instance: keep noeviction, raise maxmemory within the container memory limit
docker exec REDIS redis-cli CONFIG SET maxmemory 1536mb
#    and persist it in redis.conf or the compose command (CONFIG SET is lost on restart)
# 3. Cache data in a SEPARATE instance that may evict:
#    maxmemory 512mb / maxmemory-policy allkeys-lru
```

**Why this fix works:** draining the backlog removes the memory pressure at its source, noeviction keeps queued jobs safe, and a separate cache instance can evict freely without touching them.

**Prevent it:** one purpose per instance, alerts on memory above 80% of maxmemory and on queue length, TTLs on every cache key, and a container memory limit above maxmemory plus fork overhead (entry 4.2).

**Next step:** [Databases: maxmemory and eviction](38-learn-databases-ops.md) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [Redis docs](https://redis.io/docs/)

**Community threads:** [Netdata: Redis OOM command not allowed](https://www.netdata.cloud/guides/redis/redis-oom-command-not-allowed/) · [Why switching to LRU can cost you data](https://www.codewithkarani.com/blog/redis-oom-command-not-allowed-eviction-policy) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22OOM+command+not+allowed+when+used+memory%22) · [Reddit r/redis](https://www.reddit.com/r/redis/search/?q=OOM+command+not+allowed+maxmemory&restrict_sr=1)

### 4.4 MongoDB: Authentication failed, right password

> **Seen as:** `MongoServerError: Authentication failed.` with the user and password from MONGO_INITDB_ROOT_USERNAME and MONGO_INITDB_ROOT_PASSWORD, or `MongoServerSelectionError: connect ECONNREFUSED 127.0.0.1:27017` · **Where:** the official mongo image in Compose or Dokploy, apps connecting to mongodb://root:PASSWORD@mongo:27017/shop · **Level:** [L1 · Junior] · **How common:** a classic in docker-library/mongo (#346), the MongoDB community forums and many blog notes

**Why it happens:** the root user lives in the admin database. A connection string that names another database authenticates against that database unless it adds ?authSource=admin. The `MONGO_INITDB_*` variables apply only at first initialisation with an empty /data/db, the same trap as entry 1.1. ECONNREFUSED to 127.0.0.1 means the app uses localhost inside its own container, or, on a bare-metal install, mongod isn't running on that host; remote clients refused at the server's private address point to bindIp set to 127.0.0.1 only.

**Diagnose:**

```bash
docker exec -it MONGO mongosh -u root -p --authenticationDatabase admin --quiet \
  --eval 'db.getSiblingDB("admin").getUsers().users.map(u => u.user + "@" + u.db)'
docker logs MONGO 2>&1 | grep 'Failed to authenticate' | tail -1
```

```text
[ 'root@admin' ]
{"t":{"$date":"2026-10-03T10:21:07.412+00:00"},"s":"I","c":"ACCESS","id":5286307,"ctx":"conn42","msg":"Failed to authenticate","attr":{"client":"10.0.1.21:40112","mechanism":"SCRAM-SHA-256","user":"root","db":"shop","error":"UserNotFound: Could not find user \"root\" for db \"shop\""}}
```

**What the output tells you:** the only user is root in admin, and the app tried to log in as root in shop. The password was right; the database was wrong.

**Fix:**

```bash
# Quick fix: tell the driver where the user lives
#   mongodb://root:PASSWORD@mongo:27017/shop?authSource=admin
# Better: an app user in the app database, and no root in the app at all
docker exec -it MONGO mongosh -u root -p --authenticationDatabase admin --eval '
  db.getSiblingDB("shop").createUser({user: "shop", pwd: passwordPrompt(), roles: [{role: "readWrite", db: "shop"}]})'
#   then: mongodb://shop:APP_PASSWORD@mongo:27017/shop
```

From other containers use the service name, never localhost. On bare metal, set net.bindIp to localhost plus the private address in /etc/mongod.conf and keep authorization enabled.

**Why this fix works:** authSource tells the driver which database holds the credentials; an app user created in its own database needs no authSource and can't touch other databases. Recreating the volume to "reset" users deletes the data with them.

**Prevent it:** one user per app database, connection strings kept in secrets, and 27017 never published.

**Next step:** [Databases: Databases in Docker](38-learn-databases-ops.md) · [Dokploy: App can't reach its database](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose · [MongoDB docs](https://www.mongodb.com/docs/)

**Community threads:** [MongoDB in Docker: authSource](https://notes.dt.in.th/MongoDBAuthSource) · [docker-library/mongo#346](https://github.com/docker-library/mongo/issues/346) · [MongoDB Community: docker compose authentication](https://www.mongodb.com/community/forums/t/docker-compose-authentication-doesnt-register/174875) · Search: [Stack Overflow](https://stackoverflow.com/search?q=mongodb+docker+%22Authentication+failed%22+authSource) · [Reddit r/mongodb](https://www.reddit.com/r/mongodb/search/?q=docker+authentication+failed+authSource&restrict_sr=1)

### 4.5 MongoDB exits with Illegal instruction

> **Seen as:** `WARNING: MongoDB 5.0+ requires a CPU with AVX support, and your current system does not appear to have that!`, then `Illegal instruction (core dumped)` and exit code 132, while the same compose file works on a laptop · **Where:** mongo containers (for UniFi, Graylog, Wekan, LibreChat and others) on Proxmox or other KVM virtual machines · **Level:** [L2 · Mid-level] · **How common:** very common in homelabs and self-hosting; docker-library/mongo#583, Graylog#13950 and Proxmox forum threads

**Why it happens:** MongoDB 5.0 and later x86 builds need AVX instructions (Sandy Bridge or newer). Proxmox's default virtual CPU models (kvm64 in older versions, x86-64-v2-AES in newer ones) hide AVX from the guest even when the physical CPU has it. Very old physical CPUs and some ARM boards lack the instructions entirely.

**Diagnose:**

```bash
grep -o -w avx /proc/cpuinfo | head -1              # inside the VM: empty output = no AVX
docker inspect -f '{{.State.ExitCode}}' MONGO        # 132 = 128 + SIGILL
qm config VMID | grep '^cpu'                         # on the Proxmox host
```

```text
132
cpu: x86-64-v2-AES
```

**What the output tells you:** the first command printed nothing, so the guest sees no AVX; exit 132 is an illegal instruction; and the VM uses x86-64-v2-AES, a model without AVX. The CPU model, not MongoDB, is the problem.

**Fix:**

```bash
# On the Proxmox host: a CPU model with AVX (host, or x86-64-v3 to keep live migration between similar hosts)
qm set VMID --cpu x86-64-v3
qm shutdown VMID && qm start VMID       # a full stop and start; a reboot inside the guest isn't enough
# Inside the VM afterwards: should print the number of vCPUs
grep -c -w avx /proc/cpuinfo
```

Choose host when the VM never migrates, or the highest model all your hosts support that still includes AVX (x86-64-v3 includes AVX and AVX2). Last resort: mongo:4.4, which is end of life and gets no security fixes, so plan your way off it.

**Why this fix works:** the guest sees only the instruction set its virtual CPU model advertises, and the model is fixed when QEMU starts, which is why it takes a cold start.

**Prevent it:** VM templates with a CPU model that includes AVX, and a /proc/cpuinfo flag check in your post-provisioning tests before databases are deployed.

**Next step:** [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · [Slow system: slow VM on a busy hypervisor](23-playbook-slow-system.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Inspect and Logs) · [Proxmox VE docs](https://pve.proxmox.com/pve-docs/)

**Community threads:** [docker-library/mongo#583](https://github.com/docker-library/mongo/issues/583) · [Graylog#13950](https://github.com/Graylog2/graylog2-server/issues/13950) · [Proxmox forum: AVX/AVX2 CPU flags](https://forum.proxmox.com/threads/feature-suggestion-avx-avx2-cpu-flags.114688/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=mongodb+docker+%22Illegal+instruction%22+AVX) · [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=mongodb+avx+cpu+type&restrict_sr=1)

## 5. Backups and restores

A backup is only a file until a restore proves otherwise. The entries run from the first restore you'll ever do to physical backups with point-in-time recovery.

### 5.1 Restore fails: wrong tool, roles, objects

> **Seen as:** `pg_restore: error: input file appears to be a text format dump. Please use psql.`, `ERROR:  role "olduser" does not exist`, or `ERROR:  relation "users" already exists` halfway through · **Where:** moving a database to Dokploy or a new server, or the first restore under pressure · **Level:** [L1 · Junior] · **How common:** perennial beginner questions; Dokploy has its own threads (#338 "How to restore a database backup", #1730 pg_restore retrying in a loop)

**Why it happens:** pg_dump's plain format (-Fp, the default) is SQL and restores with psql; the custom, directory and tar formats (-Fc, -Fd, -Ft) restore with pg_restore. Dumps contain OWNER and GRANT statements for roles, but pg_dump never dumps the roles themselves, so they're missing on a new server. Restoring into a database that isn't empty, or that has different extensions, collides with what's already there.

**Diagnose:**

```bash
head -c 5 shop.dump; echo                         # "PGDMP" = custom format; readable SQL = plain
pg_restore -l shop.dump | grep -E 'dbname|Format|Dumped from'
psql -h 10.0.1.10 -U postgres -c '\du'            # which roles exist on the target?
```

```text
PGDMP
;     dbname: shop
;     Format: CUSTOM
;     Dumped from database version: 16.4
                             List of roles
 Role name |                         Attributes
-----------+------------------------------------------------------------
 postgres  | Superuser, Create role, Create DB, Replication, Bypass RLS
```

**What the output tells you:** it's a custom-format dump, so it needs pg_restore, and the target has no shop role, so every OWNER TO shop statement would fail.

**Fix:**

```bash
# Roles first (from the source server), then an empty target database owned by the app role
pg_dumpall -h OLD_HOST -U postgres --globals-only > globals.sql
psql -h 10.0.1.10 -U postgres -f globals.sql
createdb -h 10.0.1.10 -U postgres -O shop shop
# Custom format: pg_restore, in parallel, stopping at the first error
pg_restore -h 10.0.1.10 -U postgres -d shop -j 4 --exit-on-error shop.dump
# Plain format instead:   psql -h 10.0.1.10 -U postgres -v ON_ERROR_STOP=1 -d shop -f shop.sql
# No roles available?     pg_restore ... --no-owner --no-acl --role=shop
```

For a Dokploy database, stream the dump into the container (`docker exec -i DB_CONTAINER pg_restore -U postgres -d shop --no-owner < shop.dump`) or use the UI restore, then compare row counts of the main tables with the source.

**Why this fix works:** the right tool reads the format, globals recreate the roles the dump refers to, an empty target means no collisions, and --exit-on-error turns a silent half-restore into a visible failure you can fix and rerun. Ignoring a screen of errors and declaring success is how half-restored databases reach production.

**Prevent it:** standardise on -Fc dumps plus a separate globals dump, and keep the exact restore command next to every backup job, in the runbook and in the repository.

**Next step:** [Databases: Logical backups: pg_dump and mysqldump](38-learn-databases-ops.md) · [Databases: Restore a single table](38-learn-databases-ops.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance: Backup and Restore Methods · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [Dokploy issues about restoring databases](https://github.com/Dokploy/dokploy/issues?q=is%3Aissue+restore+database+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22input+file+appears+to+be+a+text+format+dump%22) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=pg_restore+role+does+not+exist+no-owner&restrict_sr=1)

### 5.2 Backup repository is already locked

> **Seen as:** `Fatal: unable to create lock in backend: repository is already locked by PID 1234 on bk1 by root` (restic) or `Failed to create/acquire the lock /srv/borg/shop/lock.exclusive (timeout).` (borg), on every run after one bad night · **Where:** nightly restic or borg jobs after a reboot, an OOM kill, a network drop or overlapping cron runs · **Level:** [L1 · Junior] · **How common:** the most common restic and borg support topic; both projects document unlock and break-lock for it

**Why it happens:** a run that was killed leaves its lock file behind, and every later run sees the lock and gives up. Sometimes the lock is real: two jobs overlap (a slow backup still running when cron starts the next one, a second host using the same repository, prune during backup). Clock skew between hosts can make locks look fresh or stale when they aren't.

**Diagnose:**

```bash
restic -r REPO list locks --no-lock          # restic reads the password from RESTIC_PASSWORD_FILE
pgrep -a restic; pgrep -a borg               # on EVERY host that uses this repository
systemctl list-timers | grep -iE 'restic|borg'
```

```text
3a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9
Sun 2026-10-04 02:00:00 UTC 21h left Sat 2026-10-03 02:00:01 UTC 2h 4min ago restic.timer restic.service
```

**What the output tells you:** one lock exists, pgrep found no restic or borg process anywhere, and the last run started two hours ago: a stale lock left by a killed run.

**Fix:**

```bash
# Only after confirming nothing runs on any host:
restic -r REPO unlock                         # removes stale locks only
borg break-lock REPO                          # borg equivalent
# Stop overlaps: one instance at a time, and wait for a lock instead of failing at once
flock -n /run/backup.lock /usr/local/bin/backup.sh
restic -r REPO backup /srv --retry-lock 30m
```

**Why this fix works:** restic unlock removes only locks it considers stale (`--remove-all` would also remove active ones, so never use it while anything runs); flock, or a systemd timer, which never starts a unit that is still running, prevents the overlap that creates real conflicts. Deleting lock files by hand while a prune runs can damage the repository (entry 5.6).

**Prevent it:** one scheduler per repository, prune and forget outside the backup window, and an alert on the age of the last successful snapshot.

**Next step:** [Databases: Restore tests and backup alerts](38-learn-databases-ops.md) · [Services & systemd](07-services-systemd.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD · [restic troubleshooting](https://restic.readthedocs.io/en/stable/077_troubleshooting.html)

**Community threads:** [restic docs: troubleshooting](https://restic.readthedocs.io/en/stable/077_troubleshooting.html) · [BorgBackup FAQ](https://borgbackup.readthedocs.io/en/stable/faq.html) · Search: [Server Fault](https://serverfault.com/search?q=restic+%22repository+is+already+locked%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=borg+break-lock+failed+to+acquire+lock&restrict_sr=1)

### 5.3 Encrypted backup, lost password or key

> **Seen as:** `Fatal: wrong password or no key found` (restic) or `passphrase supplied in BORG_PASSPHRASE, by BORG_PASSCOMMAND or via BORG_PASSPHRASE_FD is incorrect.` (borg 1.2 and later) on the day you need the backup · **Where:** the server died and the repository is fine on the NAS or S3, but the password lived only in the dead server's script, or borg keyfile mode kept the key under /root/.config/borg/keys on that machine · **Level:** [L1 · Junior] · **How common:** recurring heartbreak threads; a restic forum topic asking for password recovery has 32 replies, and the borg FAQ stresses exporting keys

**Why it happens:** client-side encryption is real: without the password (restic) or the key plus passphrase (borg), nobody can decrypt the data, including the developers. The secret was stored only on the machine being backed up. Borg's keyfile mode keeps the key outside the repository; repokey mode keeps it inside, but you still need the passphrase.

**Diagnose:**

```bash
restic -r REPO key list                        # needs one working password
borg key export REPO /root/borg-key-shop.txt   # do this NOW, while the key still works
# Inventory: where does each backup secret live, and who can reach it without the server?
```

```text
 ID        User  Host  Created
------------------------------------------
*1a2b3c4d  root  db1   2025-03-14 09:12:44
------------------------------------------
```

**What the output tells you:** one key exists, created on db1, and nothing proves that anyone holds its password anywhere except on db1.

**Fix:**

```bash
# While you still have access: a second key held by someone else, and off-host copies of both
restic -r REPO key add                          # prompts for the new password
borg key export --paper REPO > borg-key-shop.paper.txt    # a printable copy for the safe
```

If a password is lost but another key still works, add a new key and remove the old one (`restic key remove ID`). If no key works, the data is gone: start a new repository today and treat it as an incident. Keep passwords and exported keys in the team password manager and on paper in a safe, never only on the hosts being backed up.

**Why this fix works:** a second key and an off-host copy remove the single point of failure; an export that sits on the same disk as the data is useless.

**Prevent it:** make "restore on a clean machine using only the password manager" part of every DR drill (entry 9.3), so the secret storage gets tested along with the data.

**Next step:** [Databases: RPO, RTO and the 3-2-1 rule](38-learn-databases-ops.md) · [Security: Secrets management](37-learn-security-devsecops.md) · KodeKloud: *Fundamentals of SRE* — Incident Management · [BorgBackup FAQ](https://borgbackup.readthedocs.io/en/stable/faq.html)

**Community threads:** [BorgBackup FAQ: key export, repokey vs keyfile](https://borgbackup.readthedocs.io/en/stable/faq.html) · [restic forum top topics](https://forum.restic.net/top?period=all) · Search: [Server Fault](https://serverfault.com/search?q=borg+backup+lost+key+passphrase) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=lost+restic+password&restrict_sr=1)

### 5.4 Backups stopped silently or are empty

> **Seen as:** `pg_dump: error: aborting because of server version mismatch` with `pg_dump: detail: server version: 17.6; pg_dump version: 16.10` in a log nobody reads, or no error at all: 20-byte .sql.gz files and a newest usable backup weeks old · **Where:** cron scripts, backup sidecar containers, GitLab CI jobs and built-in app backups that bring their own pg_dump · **Level:** [L2 · Mid-level] · **How common:** dozens of GitHub issues across backup images, a GitLab forum thread and a DigitalOcean KB article; it was the root cause of GitLab's empty S3 backups in 2017

**Why it happens:** pg_dump refuses to dump a server newer than itself, and the client in the backup image (or Ubuntu's postgresql-client package) lags the server you just upgraded. The failure then hides: `pg_dump ... | gzip > file` returns gzip's exit code, so the script "succeeds" and writes an empty gzip stream; cron runs with a minimal PATH and environment (no PGPASSWORD, no .pgpass for that user) and mails errors to a local mailbox nobody reads; and nobody watches backup age, size or restores.

**Diagnose:**

```bash
ls -lh --time-style=long-iso /backups/shop/ | tail -4
docker exec BACKUP_CONTAINER pg_dump --version
psql -h 10.0.1.10 -U shop -Atc 'SHOW server_version;'
```

```text
-rw-r--r-- 1 root root 48M 2026-09-12 02:00 shop-2026-09-12.sql.gz
-rw-r--r-- 1 root root  20 2026-09-13 02:00 shop-2026-09-13.sql.gz
-rw-r--r-- 1 root root  20 2026-10-02 02:00 shop-2026-10-02.sql.gz
-rw-r--r-- 1 root root  20 2026-10-03 02:00 shop-2026-10-03.sql.gz
pg_dump (PostgreSQL) 16.10
17.6
```

**What the output tells you:** backups shrank to 20 bytes, an empty gzip stream, the night after the server moved to 17, and nothing alerted. The newest usable backup is three weeks old: that's your real RPO today.

**Fix:**

```bash
#!/usr/bin/env bash
# /usr/local/bin/backup-shop.sh: fail loudly, verify, then report success
set -Eeuo pipefail
out="/backups/shop/shop-$(date +%F).dump"
# pg_dump from the database's own container, so client and server versions always match
docker exec shop-db pg_dump -U shop -Fc shop > "$out"
docker exec -i shop-db pg_restore -f /dev/null < "$out"        # reads every block: fails on a truncated archive
[ "$(stat -c %s "$out")" -gt 1000000 ] || { echo "dump too small: $out" >&2; exit 1; }
curl -fsS -m 10 https://hc.example.com/ping/shop-db-backup > /dev/null    # dead man's switch
```

Run it from a systemd timer whose service has OnFailure= pointing at a notification unit, instead of cron mail. If the dump must run elsewhere (a CI job, a backup host), use a client at least as new as the server: the postgres image of the server's major, or postgresql-client from the PGDG apt repository. Adjust the size floor to your database.

**Why this fix works:** pipefail and set -e make any failed step fail the job; the server's own pg_dump always matches its version; a full pg_restore into /dev/null proves the archive is readable to the end (pg_restore -l reads only the table of contents at the start, so it would miss a truncated tail); and the success ping turns silence into an alert, because the alert fires when the ping does *not* arrive. That's the only way to notice a job that stopped running at all.

**Prevent it:** alert when the newest backup is older than 26 hours or less than half the size of the previous one, change the backup image's major in the same merge request as the database's, and run a weekly automated test restore.

**Next step:** [Databases: Restore tests and backup alerts](38-learn-databases-ops.md) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [GitLab 2017 database outage postmortem](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) · [DigitalOcean KB: pg_dump server version mismatch](https://docs.digitalocean.com/support/how-do-i-fix-the-pg_dump-aborting-because-of-server-version-mismatch-error/) · [GitLab Forum: pg_dump server version mismatch](https://forum.gitlab.com/t/pg-dump-server-version-mismatch/80522) · [docker-postgres-backup-local#63](https://github.com/prodrigestivill/docker-postgres-backup-local/issues/63) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22aborting+because+of+server+version+mismatch%22) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=backups+never+tested+restore+failed&restrict_sr=1)

### 5.5 PBS datastore full after prune and GC

> **Seen as:** backup jobs from Proxmox VE fail with `ENOSPC: No space left on device` or `unable to update atime`, and pruning old snapshots plus garbage collection leaves the disk full, with chunks listed as "Pending removals" · **Where:** Proxmox Backup Server datastores on ZFS or ext4 · **Level:** [L2 · Mid-level] · **How common:** many near-identical Proxmox forum threads ("Proxmox Backup Server full", "Disk full - unable to run garbage collection")

**Why it happens:** prune only removes snapshot indexes; the chunks they referenced are freed later by garbage collection, and only once they've been unused for longer than the cutoff (24 hours and 5 minutes by default, because access times may lag a day with relatime). GC itself must update chunk access times, and on a 100% full ZFS pool even that fails, because copy-on-write needs free space to write anything. Underneath: no retention policy, no scheduled prune and GC, no quota, no alert before 90%.

**Diagnose:**

```bash
df -h /mnt/datastore/store1
zfs list -o name,used,avail,quota backup/store1
proxmox-backup-manager task list --limit 5          # find the last garbage-collection task, then read its log
```

```text
Filesystem      Size  Used Avail Use% Mounted on
backup/store1   3.6T  3.6T     0 100% /mnt/datastore/store1
NAME            USED  AVAIL  QUOTA
backup/store1  3.60T     0B   none
2026-10-03T04:00:12+00:00: Pending removals: 812.4 GiB (in 391022 chunks)
```

**What the output tells you:** the pool is at 100% with no quota, so GC can't even update access times, and 812 GiB are already waiting for a GC run that gets past the cutoff.

**Fix:**

```bash
# 1. Make a little room so GC can write (ZFS: drop an unneeded snapshot or dataset, or extend the pool)
zfs list -t snapshot -o name,used -s used backup | tail -3
# 2. Prune by your retention policy, then run GC (again after the cutoff has passed)
proxmox-backup-manager garbage-collection start store1
# 3. Once space is free: a quota below the pool size keeps a reserve that backups can't consume
zfs set quota=3.2T backup/store1
```

Configure prune jobs and a GC schedule per datastore (UI: Datastore, Prune & GC). Current PBS releases also let you shorten the cutoff with the gc-atime-cutoff datastore tuning option; keep gc-atime-safety-check enabled.

**Why this fix works:** GC needs free space to mark the chunks still in use; once it runs, everything older than the cutoff and unreferenced is deleted. The quota leaves headroom the datastore can never fill. Deleting files from the .chunks directory by hand breaks every backup that still references them.

**Prevent it:** alert at 80% datastore usage, size storage for retention times change rate, and schedule verify jobs so you know the chunks are still readable.

**Next step:** [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · [Storage & disk](01-storage-disk.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage · [PBS maintenance tasks](https://pbs.proxmox.com/docs/maintenance.html)

**Community threads:** [Proxmox forum: Disk full - unable to run garbage collection](https://forum.proxmox.com/threads/disk-full-unable-to-run-garbage-collection.81800/) · [Proxmox forum: Proxmox Backup Server full](https://forum.proxmox.com/threads/proxmox-backup-server-full.119897/) · [Proxmox forum: free space right after deleting backups](https://forum.proxmox.com/threads/proxmox-backup-server-pbs-how-to-immediately-free-space-after-deleting-specific-backups.168682/) · Search: [Server Fault](https://serverfault.com/search?q=proxmox+backup+server+datastore+full) · [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=PBS+datastore+full+garbage+collection&restrict_sr=1)

### 5.6 restic check: repository contains errors

> **Seen as:** `Fatal: repository contains errors`, `ciphertext verification failed` or `pack 2b8f1c0e contains 3 errors` from a scheduled check or a restore · **Where:** restic repositories on USB disks, NAS shares, SFTP boxes or S3, often after a power loss or on flaky hardware · **Level:** [L3 · Senior] · **How common:** top restic forum topics ("repository contains errors: how best to respond?", "Recovery options for damaged repositories"); the repair commands arrived in restic 0.16 and later

**Why it happens:** bad hardware (RAM, disks, USB bridges, cables) corrupts data, and the corruption comes back unless the hardware is fixed. Interrupted writes on storage without atomic renames (some network filesystems and cloud-sync folders) leave partial files. Old versions running prune and backup at once, or hand edits of repository files, damage the index.

**Diagnose:**

```bash
restic -r REPO check --read-data-subset=10%     # a sample; --read-data reads everything
sudo smartctl -A /dev/sdb | grep -E 'Reallocated|Pending|CRC'
sudo dmesg -T | grep -iE 'I/O error|usb .*reset' | tail -2
```

```text
read 10.0% of data packs
Pack ID does not match, want 2b8f1c0e, got 9d4e7a13
Fatal: repository contains errors
  5 Reallocated_Sector_Ct   0x0033   100   100   010    Pre-fail  Always       -       0
197 Current_Pending_Sector  0x0012   100   100   000    Old_age   Always       -       0
199 UDMA_CRC_Error_Count    0x003e   200   199   000    Old_age   Always       -       57
[Sat Oct  3 01:42:10 2026] usb 2-1: reset SuperSpeed USB device number 3 using xhci_hcd
```

**What the output tells you:** one pack's content no longer matches its name, the disk surface is fine, but the USB link shows CRC errors and resets: the cable or enclosure damages data in transit. Repairing the repository on this hardware would only corrupt it again.

**Fix:**

```bash
# 0. Fix the hardware first: replace the cable or enclosure; test RAM if ciphertext errors repeat
# 1. Stop forget/prune jobs and copy the repository (at least index/ and snapshots/) before repairing
# 2. Repair, upload current data again, then drop references to data that's gone for good
restic -r REPO repair index
restic -r REPO repair packs 2b8f1c0e
restic -r REPO backup /srv
restic -r REPO repair snapshots --forget
restic -r REPO check --read-data
```

**Why this fix works:** repair index rebuilds the index from the packs that exist, repair packs salvages what it can from damaged ones, a new backup uploads any blob that still exists on the source, and repair snapshots removes references to data that's lost. The order matters, and the copy makes a wrong step recoverable. Running prune on a damaged repository can delete data you could still have saved.

**Prevent it:** a weekly `restic check --read-data-subset` that rotates through the data, a second copy on different hardware (`restic copy` to another repository), and storage you'd trust with a database.

**Next step:** [Databases: RPO, RTO and the 3-2-1 rule](38-learn-databases-ops.md) · [Storage & disk](01-storage-disk.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage · [restic troubleshooting](https://restic.readthedocs.io/en/stable/077_troubleshooting.html)

**Community threads:** [restic docs: repairing a repository](https://restic.readthedocs.io/en/stable/077_troubleshooting.html) · [restic forum top topics](https://forum.restic.net/top?period=all) · Search: [Server Fault](https://serverfault.com/search?q=restic+check+%22repository+contains+errors%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=restic+%22repository+contains+errors%22&restrict_sr=1)

### 5.7 pgBackRest: WAL not archived, stanza mismatch

> **Seen as:** `ERROR: [082]: WAL segment 000000010000000000000003 was not archived before the 60000ms timeout` from pgbackrest check or the first backup, or `ERROR: [044]: PostgreSQL version 16, system-id ... do not match stanza version 15, system-id ...` right after a major upgrade · **Where:** pgBackRest with a local, SFTP or S3/MinIO repository for point-in-time recovery · **Level:** [L3 · Senior] · **How common:** error 082 is the most repeated pgBackRest issue title (#1569, #1714, #1717, #2345, #2451, plus mailing-list threads)

**Why it happens:** pgBackRest proves archiving works by forcing a WAL switch and waiting for that segment to reach the repository. It never arrives when archive_mode is off, when archive_command is wrong or names another stanza, when the postgres user can't reach the repository (SSH keys, the TLS server, S3 credentials or your private CA), or when the link is too slow for archive-timeout. After pg_upgrade, the stanza still describes the old cluster until stanza-upgrade runs.

**Diagnose:**

```bash
sudo -u postgres psql -Atc 'SHOW archive_mode;' -c 'SHOW archive_command;'
sudo -u postgres psql -c 'SELECT archived_count, failed_count, last_failed_wal FROM pg_stat_archiver;'
sudo -u postgres pgbackrest --stanza=main --log-level-console=info check
sudo grep -A1 'archive command failed' /var/log/postgresql/postgresql-16-main.log | tail -2
```

```text
on
pgbackrest --stanza=db archive-push %p
 archived_count | failed_count |     last_failed_wal
----------------+--------------+--------------------------
              0 |          214 | 000000010000000000000003
ERROR: [082]: WAL segment 000000010000000000000003 was not archived before the 60000ms timeout
2026-10-03 09:41:02.117 UTC [1201] LOG:  archive command failed with exit code 1
2026-10-03 09:41:02.117 UTC [1201] DETAIL:  The failed archive command was: pgbackrest --stanza=db archive-push pg_wal/000000010000000000000003
```

**What the output tells you:** archive_command names a stanza called db while the repository and the check use main, so every archive attempt fails: 214 failures and nothing archived. It also means pg_wal is growing (entry 8.1).

**Fix:**

```bash
# archive_command needs only a reload (archive_mode would need a restart)
sudo -u postgres psql -c "ALTER SYSTEM SET archive_command = 'pgbackrest --stanza=main archive-push %p';" -c 'SELECT pg_reload_conf();'
sudo -u postgres pgbackrest --stanza=main check
# After a major upgrade (pg_upgrade 15 to 16): update the stanza, then take a new full backup
sudo -u postgres pgbackrest --stanza=main --no-online stanza-upgrade
sudo -u postgres pgbackrest --stanza=main --type=full backup
```

For slow or distant repositories, raise archive-timeout and enable archive-async with a spool-path, so archiving keeps up with WAL switches.

**Why this fix works:** once archive_command and the repository agree, PostgreSQL retries the backlog by itself and archived_count starts climbing; stanza-upgrade records the new system id and version so archives from the upgraded cluster are accepted. A backup taken while archiving is broken can't be restored to a point in time.

**Prevent it:** pgbackrest check in the runbook after every change, an alert on pg_stat_archiver.failed_count, and a weekly restore to a scratch host with a target time.

**Next step:** [Databases: PostgreSQL PITR with WAL archiving](38-learn-databases-ops.md) · [Databases: Disk full from WAL or binlogs](38-learn-databases-ops.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance: Backup and Restore Methods · [pgBackRest](https://pgbackrest.org/)

**Community threads:** [pgbackrest#2451](https://github.com/pgbackrest/pgbackrest/issues/2451) · [pgbackrest#1569](https://github.com/pgbackrest/pgbackrest/issues/1569) · Search: [Stack Overflow](https://stackoverflow.com/search?q=pgbackrest+%22was+not+archived+before+the%22) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=pgbackrest+archive+timeout&restrict_sr=1)

## 6. Object storage: MinIO and S3-compatible

S3 clients sign every request with the key, the region, the host, the addressing style and the current time. Almost every S3-compatible failure is one of those not matching what the server expects; the rest are proxies changing the request on the way.

### 6.1 S3 targets fail: style, region, CA, clock

> **Seen as:** Velero `BackupStorageLocation "default" is unavailable` with `BucketRegionError: incorrect region, the bucket is not in 'us-west-2' region`, `x509: certificate signed by unknown authority`, `RequestTimeTooSkewed`, or Dokploy backup runs that fail although the destination's Test passed · **Where:** Velero, restic, pgBackRest, Dokploy, GitLab and the AWS CLI pointed at on-prem MinIO, Garage or Ceph behind your private CA · **Level:** [L2 · Mid-level] · **How common:** Velero #5511, #6691 and #7828 plus its MinIO quick-start page; Dokploy #416 (50 comments), #2731, #3516 and #1730 on backup destinations and restores

**Why it happens:** AWS SDKs default to virtual-host style (bucket.s3.example.com), while most self-hosted servers expect path style (s3.example.com/bucket). The region must match what the server reports (MinIO defaults to us-east-1). Clients in containers don't trust your private CA unless you give it to them, and a clock more than about 15 minutes off fails every signature. Tool-specific traps: Velero needs its AWS object-store plugin; Dokploy wants a full https:// endpoint on the S3 API port, not the console port, and some versions couldn't back up a database running on a Swarm worker.

**Diagnose:**

```bash
kubectl -n velero get backupstoragelocations
kubectl -n velero logs deploy/velero | grep -i 'fail to validate' | tail -1
openssl s_client -connect s3.example.com:443 -servername s3.example.com < /dev/null 2>/dev/null | grep -E '^issuer|Verify return'
timedatectl | grep synchronized
```

```text
NAME      PHASE         LAST VALIDATED   AGE   DEFAULT
default   Unavailable   12s              3d    true
level=error msg="fail to validate backup store" backupstoragelocation=velero/default error="rpc error: code = Unknown desc = BucketRegionError: incorrect region, the bucket is not in 'us-west-2' region at endpoint 'https://s3.example.com'"
issuer=CN = Example Internal CA
Verify return code: 20 (unable to get local issuer certificate)
System clock synchronized: yes
```

**What the output tells you:** the BSL uses a region the server doesn't, and this host doesn't trust the CA that signed the S3 certificate, so even with the right region the plugin would fail TLS inside its pod. The clock is fine here.

**Fix:**

```yaml
# Velero BackupStorageLocation for on-prem S3 (velero-plugin-for-aws installed as an init container)
apiVersion: velero.io/v1
kind: BackupStorageLocation
metadata:
  name: default
  namespace: velero
spec:
  provider: aws
  objectStorage:
    bucket: velero
    caCert: BASE64_OF_YOUR_CA_PEM      # base64 -w0 example-ca.pem
  config:
    region: us-east-1
    s3ForcePathStyle: "true"
    s3Url: https://s3.example.com
    checksumAlgorithm: ""              # see entry 6.3
```

The same settings exist in every client: the AWS CLI takes `aws configure set default.s3.addressing_style path`; restic takes `-o s3.bucket-lookup=path` where needed; a Dokploy destination needs endpoint https://s3.example.com (the API, not port 9001), region us-east-1, an existing bucket and a key limited to it. Put your CA into client images (update-ca-certificates, or SSL_CERT_FILE), exactly as for Harbor, and run chrony against an internal time source on every node. If a Dokploy database runs on a Swarm worker, check that your version can back it up there, or pin it to the manager.

**Why this fix works:** path style and the right region make the signed request match the server's own calculation, caCert lets the plugin verify TLS instead of skipping it, and synced clocks keep signatures valid. insecureSkipTLSVerify and similar flags make the error go away and turn your backups into a man-in-the-middle target.

**Prevent it:** one tested S3 client profile per tool in Git, your CA bundle in every image that talks to S3, a test restore after every destination change, and BSL phase plus backup status in Prometheus.

**Next step:** [Dokploy: S3 backups fail or were never restored](45-dokploy-and-self-hosted-paas.md) · [AWS: S3, encryption and KMS](36-learn-cloud-aws.md) · [Time & NTP](12-time-ntp.md) · KodeKloud: *Crash Course: AWS Basics* — S3 · [Velero MinIO quick start](https://velero.io/docs/main/contributions/minio/)

**Community threads:** [velero#5511](https://github.com/vmware-tanzu/velero/issues/5511) · [velero#6691](https://github.com/vmware-tanzu/velero/issues/6691) · [Dokploy docs: database backups](https://docs.dokploy.com/docs/core/databases/backups) · [Dokploy#2731](https://github.com/Dokploy/dokploy/issues/2731) · [Dokploy backup issues by comments](https://github.com/Dokploy/dokploy/issues?q=is%3Aissue+backup+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=velero+minio+%22BackupStorageLocation%22+unavailable) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=velero+minio+backupstoragelocation+unavailable&restrict_sr=1) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+backup+s3&restrict_sr=1)

### 6.2 SignatureDoesNotMatch behind a reverse proxy

> **Seen as:** `SignatureDoesNotMatch: The request signature we calculated does not match the signature you provided. Check your key and signing method.` from mc, restic or app SDKs while the console loads; console redirects to an internal name; presigned links that don't work · **Where:** MinIO, or another S3 server, published through Traefik, Dokploy or nginx · **Level:** [L2 · Mid-level] · **How common:** one of the top MinIO support topics (#1315, #11218, #19394, #20429, discussion #13768)

**Why it happens:** SigV4 signs the Host header, the path and some other headers. A proxy that rewrites Host, strips a path prefix, adds or changes signed headers, or drops the port breaks the signature even though the key is right. The API (9000) and the console (9001) routed to the wrong ports, or sharing one hostname without care, mix two different services. Without MINIO_SERVER_URL and MINIO_BROWSER_REDIRECT_URL set to the public URLs, presigned URLs and console redirects point at internal names.

**Diagnose:**

```bash
# How does the proxy route S3? (labels on the Swarm service)
docker service inspect minio --format '{{range $k, $v := .Spec.Labels}}{{$k}}={{$v}}{{"\n"}}{{end}}' | grep traefik
# Are the public URLs set for presigned links and console redirects?
docker exec MINIO_CONTAINER env | grep -E 'MINIO_(SERVER_URL|BROWSER_REDIRECT_URL)'
```

```text
traefik.http.middlewares.s3-strip.stripprefix.prefixes=/s3
traefik.http.routers.minio.middlewares=s3-strip,secure-headers@file
traefik.http.routers.minio.rule=Host(`files.example.com`) && PathPrefix(`/s3`)
traefik.http.services.minio.loadbalancer.server.port=9000
```

**What the output tells you:** S3 shares a hostname behind a path prefix that Traefik strips, so MinIO checks the signature against a different path than the client signed; a shared headers middleware rides along on the same router; and the env grep printed nothing, so presigned links and redirects use internal names.

**Fix:**

```yaml
# One hostname per port and no rewriting middlewares on the S3 router (Swarm stacks: under deploy.labels)
services:
  minio:
    environment:
      MINIO_SERVER_URL: https://s3.example.com
      MINIO_BROWSER_REDIRECT_URL: https://console.example.com
    labels:
      - traefik.enable=true
      - traefik.http.routers.s3.rule=Host(`s3.example.com`)
      - traefik.http.routers.s3.entrypoints=websecure
      - traefik.http.routers.s3.tls.certresolver=letsencrypt
      - traefik.http.routers.s3.service=s3
      - traefik.http.services.s3.loadbalancer.server.port=9000
      - traefik.http.routers.console.rule=Host(`console.example.com`)
      - traefik.http.routers.console.entrypoints=websecure
      - traefik.http.routers.console.tls.certresolver=letsencrypt
      - traefik.http.routers.console.service=console
      - traefik.http.services.console.loadbalancer.server.port=9001
```

With nginx in front instead: `proxy_set_header Host $http_host;`, no path rewrites, and `client_max_body_size 0;` plus `proxy_request_buffering off;` for large multipart uploads.

**Why this fix works:** with its own hostname and no rewriting, the request MinIO verifies is exactly the one the client signed; MINIO_SERVER_URL makes presigned URLs use the public name; the console gets its own router so its redirects work. Many S3 clients can't even address a server under a path prefix, which is one more reason to give S3 a hostname of its own.

**Prevent it:** test with mc and one real client (restic or the AWS CLI) after every proxy change, and keep S3 routers out of shared middleware chains.

**Next step:** [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) · [Dokploy: Uploads die after 60 seconds](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress (Traefik Overview) · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [minio#20429](https://github.com/minio/minio/issues/20429) · [minio discussion #13768](https://github.com/minio/minio/discussions/13768) · [minio#11218](https://github.com/minio/minio/issues/11218) · Search: [Stack Overflow](https://stackoverflow.com/search?q=minio+reverse+proxy+%22SignatureDoesNotMatch%22) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=minio+signature&restrict_sr=1)

### 6.3 New AWS SDK checksums break uploads

> **Seen as:** after upgrading Velero, its AWS plugin or another tool built on recent AWS SDKs: `V4 authentication signed header not found: accept-encoding`, `StatusCode: 400 ... api error InvalidArgument` on PutObject, or EOF on multipart uploads of backups larger than 5 MiB · **Where:** S3-compatible storage (Ceph RGW, older MinIO, Backblaze B2 and others) with unchanged credentials and endpoint · **Level:** [L3 · Senior] · **How common:** a chain of Velero issues: #7534 (checksum header breaks B2), #7828 (plugin 1.9.x vs S3-compatible), #9804 (an empty checksumAlgorithm doesn't stop trailing checksums on Ceph), #10543 (multipart uploads force CRC32)

**Why it happens:** AWS SDKs started sending new integrity headers and trailing checksums by default in early 2025, and many S3-compatible servers don't support them. SDK v2 also changed which headers are signed, which some gateways reject. Plugin options such as `checksumAlgorithm: ""` cover single PUTs but not always multipart uploads.

**Diagnose:**

```bash
kubectl -n velero logs deploy/velero | grep -iE 'checksum|InvalidArgument|signed header' | tail -2
kubectl -n velero get deploy velero -o jsonpath='{.spec.template.spec.initContainers[*].image}{"\n"}'
# Reproduce outside Velero with a small and a large object (the CLI switches to multipart above 8 MB)
head -c 1M /dev/urandom > small.bin; head -c 64M /dev/urandom > large.bin
aws --endpoint-url https://s3.example.com s3 cp small.bin s3://velero/test/
aws --endpoint-url https://s3.example.com s3 cp large.bin s3://velero/test/
```

```text
level=error msg="Error uploading log file" error="rpc error: code = Unknown desc = operation error S3: PutObject, https response error StatusCode: 400, api error InvalidArgument: ..."
velero/velero-plugin-for-aws:v1.13.0
upload: ./small.bin to s3://velero/test/small.bin
upload failed: ./large.bin to s3://velero/test/large.bin An error occurred (InvalidArgument) when calling the UploadPart operation: ...
```

**What the output tells you:** the plugin version changed recently, small uploads work and multipart uploads fail: that's the new SDK checksum behaviour, not credentials or the network.

**Fix:**

```yaml
# BackupStorageLocation for S3-compatible targets
spec:
  config:
    checksumAlgorithm: ""
```

```bash
# AWS CLI and boto3 against S3-compatible storage: send checksums only when an API requires them
export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
```

If multipart uploads still fail, pin the last plugin version that works with your storage and follow the open issues, or upgrade the storage server to a release that accepts the new checksums. Then run one small and one large test backup, and a restore.

**Why this fix works:** an empty checksumAlgorithm stops the plugin asking for the new checksums on PUTs, and the two variables bring back the "only when required" behaviour in AWS tools. Neither touches TLS or authentication; they only switch off an integrity extension your server doesn't speak.

**Prevent it:** upgrade backup tooling in staging first, against the real storage, with a large and a small backup plus a restore, and read the plugin's release notes for SDK changes.

**Next step:** [Learn Kubernetes: Storage](31-learn-kubernetes.md) · [CI/CD toolbox: GitOps with Argo CD and Flux](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance · [velero-plugin-for-aws README](https://github.com/vmware-tanzu/velero-plugin-for-aws/blob/main/README.md)

**Community threads:** [velero#7828](https://github.com/velero-io/velero/issues/7828) · [velero#9804](https://github.com/velero-io/velero/issues/9804) · [velero#10543](https://github.com/velero-io/velero/issues/10543) · Search: [Stack Overflow](https://stackoverflow.com/search?q=AWS_REQUEST_CHECKSUM_CALCULATION+when_required+s3+compatible) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=velero+checksum+s3+compatible&restrict_sr=1)

### 6.4 Distributed MinIO: drives offline, no quorum

> **Seen as:** `Waiting for a minimum of 2 disks to come online`, `Insufficient number of drives online`, `Read failed. Insufficient number of drives online`, drives stuck healing, or only some buckets listing · **Where:** multi-drive or multi-node MinIO after maintenance, a disk swap or a hostname change · **Level:** [L3 · Senior] · **How common:** among the most commented MinIO issues: #9052 (58 comments), #14247 (43), #15452 (42), #12426 (42)

**Why it happens:** erasure sets need read and write quorum, so with too many drives or nodes down, or drives mounted at different paths, the set stops serving. Nodes that can't resolve or reach each other (DNS, firewall, different MINIO_VOLUMES lists on different nodes) look like missing drives. A drive replaced or mounted elsewhere carries the wrong format.json, and a skewed clock on one node breaks its requests.

**Diagnose:**

```bash
mc admin info ALIAS
grep MINIO_VOLUMES /etc/default/minio                    # identical on every node?
findmnt -rn -o TARGET,SOURCE | grep '^/mnt/disk'            # which data drives are mounted?
getent hosts minio3.example.com || echo "minio3 does not resolve"
```

```text
●  minio1.example.com:9000
   Uptime: 2 hours
   Drives: 3/4 OK
●  minio3.example.com:9000
   Uptime: offline
   Drives: 0/4 OK
MINIO_VOLUMES="https://minio{1...4}.example.com:9000/mnt/disk{1...4}/minio"
/mnt/disk1 /dev/sdb1
/mnt/disk2 /dev/sdc1
/mnt/disk3 /dev/sdd1
minio3 does not resolve
```

**What the output tells you:** node minio3 is gone from the cluster's view because its name no longer resolves (a DNS change), and on this node disk4 isn't mounted. Two independent faults together cost the erasure set its quorum.

**Fix:**

```bash
# 1. Bring the missing pieces back; MinIO heals by itself once quorum returns
#    fix the DNS record for minio3 (or the managed hosts entries on every node)
sudo mount /mnt/disk4                     # and make /etc/fstab use UUID= with nofail
# 2. Same MINIO_VOLUMES and mounts on every node, then restart one node at a time
sudo systemctl restart minio
mc admin heal ALIAS                       # watch healing progress
```

Replace a failed drive with an empty one of the same size, mounted at the same path by UUID, and let healing rebuild it.

**Why this fix works:** quorum comes back as soon as enough drives answer, and healing rebuilds the missing shards from parity. Formatting or wiping a drive that is merely unreachable destroys data the cluster still needs.

**Prevent it:** fstab entries by UUID, stable DNS names on all nodes, MinIO's Prometheus metrics for drive state, and a rehearsed drive-loss and node-loss drill in the lab.

**Next step:** [Storage & disk](01-storage-disk.md) · [DNS](08-dns.md) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage (LVM, mount options) · [minio/minio repository](https://github.com/minio/minio)

**Community threads:** [MinIO issues sorted by comments](https://github.com/minio/minio/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=minio+%22Insufficient+number+of+drives+online%22) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=minio+distributed+drives+quorum&restrict_sr=1)

### 6.5 MinIO Community Edition is archived

> **Seen as:** `docker pull minio/minio` brings no updates, the console lost its admin pages, and the repository README says "THIS REPOSITORY IS NO LONGER MAINTAINED" · **Where:** any stack whose backups and artifacts depend on self-hosted MinIO (restic, Velero, Dokploy destinations, GitLab object storage, app buckets) · **Level:** [L4 · Senior/Lead] · **How common:** widely discussed through 2025 and 2026: the admin UI removal (June 2025), the end of binary and image distribution (MinIO's own "Docker release?" issue #21647, 41 comments), the archive notice, and many "MinIO alternatives" comparisons

**Why it happens:** the vendor moved users to its AIStor product (free and enterprise editions); the Community Edition went source-only (no pre-built binaries or images) and its GitHub repository was archived read-only on 25 April 2026; the code remains available under AGPLv3, without maintenance. Images pinned to an old tag keep running but get no security fixes, and a latest tag may vanish or go stale. User, policy and lifecycle management moved to the CLI (mc admin) in community builds.

**Diagnose:**

```bash
docker inspect -f '{{.Config.Image}} {{.Image}}' MINIO_CONTAINER
mc admin info ALIAS | grep -i version
# Who depends on this S3? List every client before changing anything
grep -rl 's3.example.com' /etc /srv 2>/dev/null
kubectl get backupstoragelocations -A
```

```text
minio/minio:latest sha256:5f0e1a9c2b7d4e6f8a0b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f
   Version: 2025-09-07T16-13-09Z
/etc/restic/env
/srv/gitlab/config/gitlab.rb
NAMESPACE   NAME      PHASE       LAST VALIDATED   AGE    DEFAULT
velero      default   Available   21s              212d   true
```

**What the output tells you:** the server runs an unmaintained latest from 2025, and restic, GitLab and Velero all depend on it (plus any Dokploy destinations). This is a planned migration, not an emergency, unless a security fix is needed.

**Fix:**

```bash
# Short term: pin what you run by digest, restrict network access, manage it with mc admin
docker pull minio/minio@sha256:DIGEST
# Migrate bucket by bucket to the new target, then switch clients one at a time
mc alias set new https://s3-new.example.com ACCESS_KEY SECRET_KEY
mc mirror --preserve old/backups new/backups
rclone sync old:gitlab-artifacts new:gitlab-artifacts --checksum --progress
```

Pick the target deliberately: AIStor Free (the vendor's edition), Garage (small, geo-distributed, AGPL), SeaweedFS (Apache-2.0, many features), RustFS (Apache-2.0, newer) or Ceph RGW (heavy but mature). Test every client against it (path style, checksums, entry 6.3), restore from the new target, and only then retire MinIO.

**Why this fix works:** pinning by digest stops surprise changes, the client inventory turns the cut-over into a checklist, and mirroring then restoring from the new target proves the move before you depend on it. The risk you're retiring is an unmaintained storage server holding your only backups.

**Prevent it:** a yearly review of upstream health (releases, licence, archive status) for every stateful dependency, and portable backups: restic and borg repositories and plain S3 objects move between servers without conversion.

**Next step:** [Senior architecture: Migration strategy](39-learn-senior-architecture.md) · [Senior architecture: Decision making](39-learn-senior-architecture.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [minio/minio repository](https://github.com/minio/minio)

**Community threads:** [minio/minio, archived](https://github.com/minio/minio) · [Blocks and Files: users complain after admin UI removed](https://www.blocksandfiles.com/ai-ml/2025/06/19/minio-users-complain-after-admin-ui-removed-from-community-edition/1610856) · [RustFS vs SeaweedFS vs Garage](https://blog.elest.io/rustfs-vs-seaweedfs-vs-garage-which-minio-alternative-should-you-pick/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=minio+alternative+s3+compatible+self-hosted) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=minio+alternative+garage+seaweedfs&restrict_sr=1)

## 7. Schema migrations in CI/CD

A migration is a deploy of the database. It needs what an app deploy needs: one runner, a timeout, a rollback story, and steps that the old and the new app version can both live with.

### 7.1 Liquibase lock or Flyway checksum mismatch

> **Seen as:** a deploy that hangs forever at `liquibase: Waiting for changelog lock....`, or a migrate job failing with `Validate failed: Migrations have failed validation` and `Migration checksum mismatch for migration version 2`, although it passed locally · **Where:** Liquibase and Flyway (Django, Prisma and Alembic have similar traps) in CI jobs and at app start-up · **Level:** [L2 · Mid-level] · **How common:** top results for both tools; Liquibase lock threads across many projects and Flyway #2983

**Why it happens:** a pod running migrations was killed (OOM, a rollout, a liveness probe) while it held the lock row in DATABASECHANGELOGLOCK, so every later run waits for a lock nobody will release. A checksum mismatch means someone edited an already-applied migration (even whitespace or a comment), two branches created conflicting versions, or environments applied migrations in a different order.

**Diagnose:**

```sql
-- Liquibase: who holds the lock, and since when?
SELECT id, locked, lockgranted, lockedby FROM databasechangeloglock;
-- Flyway: the last applied versions and their checksums
SELECT version, description, checksum, success FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 3;
```

```bash
git log --oneline -3 -- db/migration/V2__add_orders_status.sql     # was an applied file edited?
kubectl get pods -A | grep shop-web-7c9d5b6f4-x2k8q || echo "lock holder no longer exists"
```

```text
 id | locked |       lockgranted       |               lockedby
----+--------+-------------------------+---------------------------------------
  1 | t      | 2026-10-03 08:14:55.031 | shop-web-7c9d5b6f4-x2k8q (10.42.1.17)
 version |    description    |  checksum   | success
---------+-------------------+-------------+---------
 3       | add orders index  | -1043926154 | t
 2       | add orders status |   811043277 | t
 1       | init              | -1918410126 | t
4f2a9c1 fix typo in comment
a81c3e7 V2 add orders status
lock holder no longer exists
```

**What the output tells you:** two typical findings: the Liquibase lock belongs to a pod that no longer exists (killed mid-migration), and the Flyway project's V2 was edited after it had been applied, so its stored checksum no longer matches the file.

**Fix:**

```bash
# Liquibase: only after confirming no migration runs anywhere
liquibase release-locks
# (SQL equivalent: UPDATE databasechangeloglock SET locked = false, lockgranted = NULL, lockedby = NULL WHERE id = 1;)
# Flyway: put the applied file back exactly as it was, and make the change a NEW migration
git checkout a81c3e7 -- db/migration/V2__add_orders_status.sql
# Only if the edit was intentional and is already applied everywhere:
flyway repair
```

**Why this fix works:** releasing a dead lock lets the next run proceed; restoring the original file brings back the recorded checksum; flyway repair rewrites stored checksums to match the files, which is right only when the database really matches them. Releasing a lock while another migration runs lets two runners change the schema at once.

**Prevent it:** run migrations as one dedicated CI job or Kubernetes Job with enough memory and no liveness probe that can kill it, and add a CI check that rejects changes to applied migration files.

**Next step:** [Databases: Migrations in GitLab CI](38-learn-databases-ops.md) · [CI/CD toolbox: Deploying from CI](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Deployment · [Flyway#2983](https://github.com/flyway/flyway/issues/2983)

**Community threads:** [Liquibase: Waiting for changelog lock (course notes)](https://ucsb-cs156.github.io/topics/liquibase/waiting_for_changelog_lock.html) · [Kubernetes-aware Liquibase lock release](https://github.com/szintezisnet/Kubernetes-Liquibase-Lock-Release) · [flyway#2983](https://github.com/flyway/flyway/issues/2983) · Search: [Stack Overflow](https://stackoverflow.com/search?q=liquibase+%22Waiting+for+changelog+lock%22) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=flyway+checksum+mismatch+pipeline&restrict_sr=1)

### 7.2 A migration freezes the app: lock queue

> **Seen as:** a "quick" migration (add a column, a foreign key, an index) followed by minutes of timeouts across the site; pg_stat_activity full of queries with wait_event_type = Lock; with lock_timeout set, `ERROR:  canceling statement due to lock timeout` · **Where:** CI/CD pipelines running DDL on a busy table (MySQL has the same problem with metadata locks) · **Level:** [L3 · Senior] · **How common:** widely written up (postgres.ai, Xata, many engineering blogs); GitHub's availability reports describe outages caused by schema migrations

**Why it happens:** ALTER TABLE needs an ACCESS EXCLUSIVE lock. While it waits behind one long query or an idle-in-transaction session, every new query on that table queues behind the ALTER, so a migration that would take 50 ms blocks the whole app. Some DDL also rewrites or scans the whole table (type changes, a volatile default, validating a constraint, a plain CREATE INDEX that blocks writes). And migration sessions usually run without lock_timeout.

**Diagnose:**

```sql
SELECT pid, state, wait_event_type, now() - xact_start AS xact_age, left(query, 45) AS query
FROM pg_stat_activity WHERE datname = 'shop' AND xact_start IS NOT NULL ORDER BY xact_start LIMIT 4;
SELECT pid, pg_blocking_pids(pid) AS blocked_by, left(query, 45) AS query
FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0 LIMIT 3;
```

```text
  pid  |        state        | wait_event_type |    xact_age     |                     query
-------+---------------------+-----------------+-----------------+-----------------------------------------------
 21877 | idle in transaction | Client          | 02:41:13.402116 | SELECT * FROM orders WHERE id = $1 FOR UPDATE
 30114 | active              | Lock            | 00:01:52.118520 | ALTER TABLE orders ADD COLUMN status text
 30120 | active              | Lock            | 00:01:51.903114 | SELECT id, total FROM orders WHERE customer_i
 30121 | active              | Lock            | 00:01:51.877402 | INSERT INTO orders (customer_id, total) VALUE
  pid  | blocked_by |                     query
-------+------------+-----------------------------------------------
 30114 | {21877}    | ALTER TABLE orders ADD COLUMN status text
 30120 | {30114}    | SELECT id, total FROM orders WHERE customer_i
 30121 | {30114}    | INSERT INTO orders (customer_id, total) VALUE
```

**What the output tells you:** a session has sat idle inside a transaction for 2 h 41 min holding a row lock on orders; the ALTER waits for it, and every new query waits for the ALTER. The migration isn't slow; it's queued, and it's queueing everyone else.

**Fix:**

```sql
-- 1. Release the queue now: cancel the migration (the app recovers within seconds)
SELECT pg_cancel_backend(30114);
-- 2. Deal with the real blocker, after checking what it is
SELECT pg_terminate_backend(21877);
-- 3. Rerun the migration so it can never queue for long
SET lock_timeout = '3s';
SET statement_timeout = '15min';
ALTER TABLE orders ADD COLUMN status text;
```

Wrap the DDL in a retry loop with backoff in the migration job. For big tables use online patterns: CREATE INDEX CONCURRENTLY (outside a transaction block), ADD CONSTRAINT ... NOT VALID followed by VALIDATE CONSTRAINT, and batched backfills. Set idle_in_transaction_session_timeout so no forgotten session can hold a table for hours.

**Why this fix works:** cancelling the waiting ALTER removes the head of the queue; lock_timeout makes a migration give up in seconds instead of blocking traffic, and the retry catches the moment the table is free; CONCURRENTLY and NOT VALID avoid long exclusive locks. Running migrations "at night" doesn't help if a session from the afternoon is still open.

**Prevent it:** a migration linter in CI (squawk, strong_migrations), lock_timeout in every migration, and expand/contract steps for big tables (entry 7.3).

**Next step:** [Databases: Locks and blocked queries](38-learn-databases-ops.md) · [Databases: Safe and unsafe DDL](38-learn-databases-ops.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [postgres.ai: lock_timeout and retries](https://postgres.ai/blog/20210923-zero-downtime-postgres-schema-migrations-lock-timeout-and-retries) · [Xata: Postgres schema changes are still a PITA](https://xata.io/blog/postgres-schema-changes-pita) · [GitHub availability report, November 2021](https://github.blog/2021-12-01-github-availability-report-november-2021/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=postgres+alter+table+lock+queue+lock_timeout+migration) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=alter+table+lock+timeout+migration&restrict_sr=1)

### 7.3 Every replica migrates; old pods break

> **Seen as:** `ERROR:  relation "orders_status_idx" already exists` or `duplicate key value violates unique constraint "schema_migrations_pkey"` when several replicas start together, and old pods failing with `column "name" does not exist` during the rollout · **Where:** apps that run "migrate" in their entrypoint on Dokploy, Swarm or Kubernetes; deploys that rename or retype a column in one step · **Level:** [L3 · Senior] · **How common:** a classic design question for platform teams; public postmortems from CircleCI (2021, a deploy changed a field type) and GitHub (2021, migration load causing cascading failures)

**Why it happens:** the orchestrator starts several replicas at once and each runs the migration; without a working lock they race. Breaking schema changes deployed in one step meet the rolling update: for a few minutes old and new app versions run side by side, and the old one queries a column that no longer exists. Nobody owns a separate, observable migration stage with its own rollback plan.

**Diagnose:**

```bash
grep -rnE 'migrate|flyway|liquibase|alembic' Dockerfile docker-entrypoint.sh .gitlab-ci.yml 2>/dev/null
kubectl rollout history deploy/shop-web | tail -2
kubectl logs -l app=shop-web --since=30m --prefix | grep -E 'already exists|does not exist' | head -2
```

```text
docker-entrypoint.sh:4:npm run migrate && exec node server.js
41        image shop-web:1.8.2
42        image shop-web:1.9.0
[pod/shop-web-6b8c9d7f5-q8w2l/web] error: relation "orders_status_idx" already exists
[pod/shop-web-58f7d9c4b-h3j9k/web] error: column "name" does not exist
```

**What the output tells you:** migrations run in the container entrypoint, so every new replica tries them; one pod lost the race on an index, and a 1.8.2 pod still serves traffic against the schema that 1.9.0 changed.

**Fix:**

```yaml
# GitLab CI: migrate once per release, before the deploy, with the release image
migrate:
  stage: migrate
  image: harbor.example.com/shop/web:$CI_COMMIT_SHORT_SHA
  script:
    - npm run migrate
  resource_group: production-db        # never two migrations at once
  environment: production
deploy:
  stage: deploy
  needs: [migrate]
  script:
    - ./deploy.sh                       # Dokploy API, kubectl or an Argo CD sync
```

On Kubernetes the same idea is a Job, a Helm pre-upgrade hook or an Argo CD PreSync hook. Then change the schema in expand/contract steps: add the new column, deploy code that writes both, backfill, switch reads, and drop the old column only in a later release, so every release still works with the previous app version.

**Why this fix works:** one runner removes the race; resource_group serialises pipelines that touch the same database; expand/contract keeps the schema compatible with both versions during the rollout, so the app can still be rolled back. Rolling an app back over a schema you've already contracted is the one rollback you can't do.

**Prevent it:** a written migration policy (one runner, lock_timeout, expand/contract, reviewed in the merge request) and a rehearsal of rolling the app back over a migrated schema.

**Next step:** [Databases: Expand and contract](38-learn-databases-ops.md) · [Deployment patterns](35-deployment-patterns.md) · [CI/CD toolbox: GitOps](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Deployment · [Bytebase: Postgres schema migration without downtime](https://www.bytebase.com/blog/postgres-schema-migration-without-downtime/)

**Community threads:** [CircleCI incident report, November 2021](https://discuss.circleci.com/t/incident-report-november-8-2021-jobs-stuck-in-a-not-running-state/41890) · [GitHub availability report, November 2021](https://github.blog/2021-12-01-github-availability-report-november-2021/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubernetes+database+migration+multiple+replicas+job) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=database+migrations+kubernetes+deploy+job+init+container&restrict_sr=1)

## 8. PostgreSQL WAL, upgrades and hard limits

These failures build up for weeks before they bite: a slot nobody removed, an OS upgrade that changed the sort order, a counter nobody watched. The fixes are routine when you catch them early and painful when you don't.

### 8.1 pg_wal fills the disk: slots and archiving

> **Seen as:** the primary's disk grows for days while the tables don't, then `PANIC:  could not write to file "pg_wal/xlogtemp.123": No space left on device`; or a standby stuck on `requested WAL segment 0000000100000000000000A1 has already been removed` · **Where:** PostgreSQL with replicas, CDC tools such as Debezium, or WAL archiving · **Level:** [L3 · Senior] · **How common:** the top cause of surprise Postgres disk-full incidents; GitLab's 2017 outage began with a lagging replica whose WAL had already been removed

**Why it happens:** a replication slot whose consumer is gone (a removed replica, a stopped Debezium connector, a leftover from an upgrade) keeps all WAL forever, because max_slot_wal_keep_size defaults to -1, unlimited. A failing archive_command does the same: PostgreSQL keeps every segment until it has been archived. The opposite failure: no slot and a small wal_keep_size, so a standby that falls behind needs segments the primary has already recycled.

**Diagnose:**

```bash
sudo du -sh /var/lib/postgresql/16/main/pg_wal
```

```sql
SELECT slot_name, slot_type, active, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
FROM pg_replication_slots;
SELECT archived_count, failed_count FROM pg_stat_archiver;
SELECT client_addr, state, replay_lag FROM pg_stat_replication;
```

```text
71G	/var/lib/postgresql/16/main/pg_wal
   slot_name   | slot_type | active | wal_status | retained
---------------+-----------+--------+------------+----------
 replica2      | physical  | t      | reserved   | 112 kB
 debezium_shop | logical   | f      | extended   | 70 GB
 archived_count | failed_count
----------------+--------------
          18821 |            0
 client_addr |   state   |   replay_lag
-------------+-----------+-----------------
 10.0.1.12   | streaming | 00:00:00.001204
```

**What the output tells you:** archiving and the real replica are healthy; an inactive logical slot for a Debezium connector that no longer runs holds 70 GB of WAL. That slot is the whole problem.

**Fix:**

```sql
-- Drop a slot only after confirming its consumer is really gone (ask the team that owns CDC)
SELECT pg_drop_replication_slot('debezium_shop');
-- Cap what any slot may retain from now on (PostgreSQL 13+); a reload is enough
ALTER SYSTEM SET max_slot_wal_keep_size = '20GB';
SELECT pg_reload_conf();
```

WAL is removed at the next checkpoints once nothing needs it. If archiving is what's failing, fix archive_command as the postgres user (entry 5.7) and PostgreSQL drains the backlog by itself. A standby that is missing WAL must be seeded again with pg_basebackup, or fetch the segments through restore_command from your archive.

**Why this fix works:** without the slot nothing pins the old WAL; the cap turns a forgotten slot into an invalidated slot (wal_status lost) instead of a full disk, a trade-off that protects the primary. Never delete files in pg_wal by hand: the server may still need them for crash recovery, and removing the wrong one corrupts the cluster.

**Prevent it:** alerts on retained WAL per slot, on pg_stat_archiver.failed_count and on disk usage, and a rule that a slot is dropped in the same change that removes its replica or connector.

**Next step:** [Databases: Disk full from WAL or binlogs](38-learn-databases-ops.md) · [Databases: Streaming replication](38-learn-databases-ops.md) · [Storage & disk](01-storage-disk.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [PostgreSQL replication settings](https://www.postgresql.org/docs/current/runtime-config-replication.html)

**Community threads:** [Gunnar Morling: Mastering Postgres replication slots](https://www.morling.dev/blog/mastering-postgres-replication-slots/) · [GitLab 2017 database outage postmortem](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=postgres+pg_wal+full+replication+slot) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=pg_wal+full+replication+slot&restrict_sr=1)

### 8.2 Collation version mismatch after an OS upgrade

> **Seen as:** `WARNING:  database "shop" has a collation version mismatch` with `DETAIL:  The database was created using collation version 2.35, but the operating system provides version 2.39.` and a HINT to rebuild objects and run ALTER DATABASE ... REFRESH COLLATION VERSION · **Where:** Ubuntu 22.04 hosts upgraded to 24.04, or a postgres image moved to a newer Debian base, with the same data directory · **Level:** [L3 · Senior] · **How common:** frequent since glibc 2.28 changed the sort order; troubleshooting pages from Kali and others, many blog posts and pgsql-bugs threads

**Why it happens:** text indexes are sorted by the C library's collation rules. A new glibc can sort some strings differently, so existing btree indexes no longer match what the server computes, and lookups or unique checks can silently go wrong. Physical copies (volume reuse, pg_upgrade, rsync, streaming replicas) carry the old ordering across OS versions, and replicas on a different OS release than the primary have the same problem.

**Diagnose:**

```sql
SELECT datname, datcollate, datcollversion, pg_database_collation_actual_version(oid) AS os_version
FROM pg_database WHERE datname NOT LIKE 'template%';
-- optional: check a big unique text index for damage
CREATE EXTENSION IF NOT EXISTS amcheck;
SELECT bt_index_check('customers_email_key'::regclass, true);
```

```text
 datname  | datcollate  | datcollversion | os_version
----------+-------------+----------------+------------
 postgres | en_US.UTF-8 | 2.35           | 2.39
 shop     | en_US.UTF-8 | 2.35           | 2.39
ERROR:  item order invariant violated for index "customers_email_key"
```

**What the output tells you:** both databases were built with glibc 2.35 and the server now runs on 2.39, and at least one unique index is already out of order: rebuild it before it lets a duplicate in.

**Fix:**

```sql
-- Rebuild indexes without long locks (PostgreSQL 12+; run outside a transaction block),
-- then record that the rebuild was done (PostgreSQL 15+)
REINDEX DATABASE CONCURRENTLY shop;
ALTER DATABASE shop REFRESH COLLATION VERSION;
```

If a unique index fails to rebuild with a duplicate-key error, the old ordering has already let duplicates in: find them with `GROUP BY ... HAVING count(*) > 1`, fix the rows, and rebuild that index.

**Why this fix works:** REINDEX rebuilds every index with the current sort rules, and REFRESH COLLATION VERSION records that this happened, which silences the warning. Running only the REFRESH silences the warning and leaves the broken indexes in place.

**Prevent it:** move between OS releases with dump and restore or logical replication, keep primary and replicas on the same OS release, pin the image's Debian base (postgres:17-bookworm), or use ICU or the builtin C.UTF-8 provider (PostgreSQL 17+) for new clusters.

**Next step:** [Databases: Major version upgrades](38-learn-databases-ops.md) · [Packages](11-packages.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [PostgreSQL docs](https://www.postgresql.org/docs/current/)

**Community threads:** [Kali docs: PostgreSQL collation mismatch](https://www.kali.org/docs/troubleshooting/postgresql-collation-mismatch-error/) · [akrabat: fixing collation version mismatch](https://akrabat.com/fixing-postgresql-collation-version-mismatch/) · [pgsql-bugs #18029](https://www.postgresql.org/message-id/18029-6efd479fc5d023dc@postgresql.org) · Search: [Server Fault](https://serverfault.com/search?q=postgres+%22collation+version+mismatch%22) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=collation+version+mismatch+glibc&restrict_sr=1)

### 8.3 XID wraparound and integer key overflow

> **Seen as:** `WARNING:  database "shop" must be vacuumed within 9763571 transactions`, then `ERROR:  database is not accepting commands to avoid wraparound data loss in database "shop"` (newer versions say commands "that assign new transaction IDs"); or inserts into one table failing with `ERROR:  nextval: reached maximum value of sequence "orders_id_seq" (2147483647)` · **Where:** busy, long-lived databases; integer overflow hits MySQL too · **Level:** [L4 · Senior/Lead] · **How common:** famous postmortems: Sentry (2015) and Mandrill (2019) for wraparound; Strava, Basecamp, Heroku and GitHub for integer overflow

**Why it happens:** transaction IDs are 32-bit, so autovacuum must freeze old rows long before the counter wraps; long-running transactions, abandoned replication slots or prepared transactions, and a disabled or throttled autovacuum stop it. serial and int4 primary keys (and the foreign keys pointing at them) top out at about 2.1 billion. Neither limit is monitored by default, so both arrive as an outage.

**Diagnose:**

```sql
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC LIMIT 2;
SELECT relname, age(relfrozenxid) FROM pg_class WHERE relkind = 'r' ORDER BY 2 DESC LIMIT 2;
SELECT pid, now() - xact_start AS age, state FROM pg_stat_activity
WHERE xact_start IS NOT NULL ORDER BY 2 DESC LIMIT 1;
SELECT sequencename, last_value, round(100.0 * last_value / max_value, 1) AS pct
FROM pg_sequences WHERE last_value IS NOT NULL ORDER BY pct DESC LIMIT 1;
```

```text
 datname  |    age
----------+------------
 shop     | 1984220311
 postgres |   48211002
 relname |    age
---------+------------
 events  | 1984220311
 orders  |  211843002
 pid  |       age        |        state
------+------------------+---------------------
 9182 | 41 days 03:12:55 | idle in transaction
  sequencename  | last_value | pct
----------------+------------+------
 orders_id_seq  | 1771520311 | 82.5
```

**What the output tells you:** shop is about 160 million transactions away from the hard stop (2^31 is about 2.15 billion), held back by a session that has been idle in a transaction for 41 days, so autovacuum can't freeze events. Separately, orders_id_seq has used 82.5% of the int4 range and will run out within months.

**Fix:**

```sql
-- Wraparound: remove what holds the horizon back, then freeze the oldest tables first
SELECT pg_terminate_backend(9182);
VACUUM (FREEZE, VERBOSE) events;
-- Integer keys: move to bigint without a long lock
ALTER TABLE orders ADD COLUMN id_big bigint;
-- then: a trigger copies id into id_big for new rows, batched UPDATEs fill old rows,
-- CREATE UNIQUE INDEX CONCURRENTLY on id_big, swap columns and the primary key in one
-- short transaction, and repeat for every foreign-key column that points at orders.id
ALTER SEQUENCE orders_id_seq AS bigint;
```

If the database already refuses new transaction IDs, follow your version's documentation section on preventing transaction ID wraparound; recent versions advise a normal VACUUM of the oldest tables rather than single-user mode. As a stop-gap for integer keys while the migration runs, some teams restart the sequence in the negative range, if the application accepts negative IDs.

**Why this fix works:** freezing can only advance past rows that no open transaction might still need, which is why the blocker goes first; a bigint key has about 9.2 quintillion values. Restarting PostgreSQL doesn't reset the counter, and VACUUM FULL on a huge table during the emergency holds an exclusive lock for hours.

**Prevent it:** bigint or identity keys for every new table, autovacuum tuned for big tables (per-table scale factors, a higher cost limit), and alerts on XID age above 500 million and on sequence usage above 70% (postgres_exporter or a scheduled query).

**Next step:** [Databases: VACUUM, autovacuum and bloat](38-learn-databases-ops.md) · [Performance & observability: capacity planning](32-learn-performance-observability.md) · KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil · [pganalyze: not accepting commands to avoid wraparound](https://pganalyze.com/docs/log-insights/autovacuum/A62)

**Community threads:** [Sentry: transaction ID wraparound in Postgres](https://blog.sentry.io/2015/07/23/transaction-id-wraparound-in-postgres) · [Mailchimp: what we learned from the Mandrill outage](https://mailchimp.com/what-we-learned-from-the-recent-mandrill-outage/) · [Strava: the upload outage of July 29, 2014](https://engineering.strava.com/the-upload-outage-of-july-29-2014/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=postgres+%22to+avoid+wraparound+data+loss%22) · [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/search/?q=transaction+id+wraparound&restrict_sr=1)

## 9. Kubernetes data and disaster recovery

On Kubernetes the platform protects you from two writers on one disk and from losing manifests. It doesn't make a database backup consistent or a restore fast; those stay your job.

### 9.1 StatefulSet stuck: Multi-Attach error

> **Seen as:** `Warning  FailedAttachVolume  Multi-Attach error for volume "pvc-3f2a9c1e-..." Volume is already exclusively attached to one node and can't be attached to another`, with the database pod stuck in ContainerCreating (or its old copy stuck Terminating) · **Where:** Postgres or MySQL StatefulSets on ReadWriteOnce volumes (Longhorn, Ceph RBD, cloud disks) after a worker died or was powered off · **Level:** [L3 · Senior] · **How common:** long threads on discuss.kubernetes.io and in Longhorn discussions, plus vendor knowledge-base articles (Broadcom, IBM, Google Distributed Cloud)

**Why it happens:** a ReadWriteOnce volume attaches to one node at a time. When a node stops answering, the control plane can't tell whether it's dead or still writing, so it keeps the attachment, and by design leaves a StatefulSet pod on that node in Terminating instead of starting a second copy: two writers on one database disk would corrupt it. A stale VolumeAttachment can also linger after a node object has been deleted.

**Diagnose:**

```bash
kubectl -n shop get pod postgres-0 -o wide
kubectl -n shop describe pod postgres-0 | sed -n '/Events/,$p' | tail -1
kubectl get nodes
kubectl get volumeattachments | grep pvc-3f2a9c1e
```

```text
NAME         READY   STATUS              RESTARTS   AGE   IP       NODE      NOMINATED NODE   READINESS GATES
postgres-0   0/1     ContainerCreating   0          9m    <none>   worker2   <none>           <none>
  Warning  FailedAttachVolume  2m (x5 over 9m)  attachdetach-controller  Multi-Attach error for volume "pvc-3f2a9c1e-..." Volume is already exclusively attached to one node and can't be attached to another
NAME      STATUS     ROLES           AGE    VERSION
cp1       Ready      control-plane   210d   v1.34.1
worker1   NotReady   <none>          210d   v1.34.1
worker2   Ready      <none>          210d   v1.34.1
csi-8b1f04c2...   driver.longhorn.io   pvc-3f2a9c1e-...   worker1   true   12d
```

**What the output tells you:** worker1 is NotReady but still owns the attachment; someone already force-deleted the old pod, and its replacement on worker2 can't attach a disk that is still attached elsewhere. Before anything else, find out whether worker1 is really off.

**Fix:**

```bash
# 1. Make sure worker1 is really down (console, IPMI or hypervisor), so it can't still write
# 2. Tell Kubernetes the node is out of service: its pods and attachments get cleaned up
kubectl taint nodes worker1 node.kubernetes.io/out-of-service=nodeshutdown:NoExecute
kubectl -n shop get pod postgres-0 -w
# 3. When worker1 is repaired and back: remove the taint
kubectl taint nodes worker1 node.kubernetes.io/out-of-service=nodeshutdown:NoExecute-
```

Force-deleting a stuck pod, or deleting a stale VolumeAttachment that refers to a node that no longer exists, does the same job by hand, and is safe only after the node is fenced.

**Why this fix works:** the out-of-service taint (non-graceful node shutdown, GA since Kubernetes 1.28) is you telling the cluster what it can't know: the node is gone, so its pods may be removed and their volumes detached. The safety comes from fencing, not from the command: if worker1 is only cut off from the network and still runs Postgres, a second attachment means two writers.

**Prevent it:** run HA databases through an operator (CloudNativePG, Percona) with replicas on other nodes and automatic failover, rather than one pod on one RWO disk, and practise a node-loss drill in the lab.

**Next step:** [Databases: Operators and CloudNativePG](38-learn-databases-ops.md) · [Docker & K8s incidents: nodes, storage and control plane](26-playbook-containers-k8s.md) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Multi-Attach Volume Errors · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [Discuss Kubernetes: Multi-Attach error for volume](https://discuss.kubernetes.io/t/multi-attach-error-for-volume-pvc-volume-is-already-exclusively-attached-to-one-node-and-cant-be-attached-to-another/18951) · [Longhorn discussion #5369](https://github.com/longhorn/longhorn/discussions/5369) · [Broadcom KB: volumes can't attach after the node is deleted](https://knowledge.broadcom.com/external/article/327470/persistent-volumes-cannot-attach-to-a-ne.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22Multi-Attach+error+for+volume%22+statefulset) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=Multi-Attach+error+statefulset+node+down&restrict_sr=1)

### 9.2 Velero Completed, restored database empty

> **Seen as:** `velero backup describe` reports Completed (or PartiallyFailed) with no pod volume backups, and the first real restore brings back an empty database PVC, or a Postgres that runs crash recovery and is missing rows · **Where:** Velero backing up namespaces with Postgres or MySQL StatefulSets (file-system backup with Kopia, or CSI snapshots) · **Level:** [L3 · Senior] · **How common:** a frequent Velero surprise; hybrid snapshot and file-system questions and requests for data-only restores are long-running, highly reacted issues (#2671, #7345)

**Why it happens:** file-system backup is opt-in: volumes are skipped unless pods carry the backup.velero.io/backup-volumes annotation or Velero was installed with --default-volumes-to-fs-backup. Without a CSI snapshot class and driver, and without the node-agent DaemonSet, Velero saves only the manifests. And a file-level copy of a running database isn't consistent at one point in time unless hooks quiesce it, or you back it up with its own tools.

**Diagnose:**

```bash
velero backup describe nightly-20261003 --details | sed -n '/Backup Volumes/,$p' | head -6
kubectl -n velero get daemonset node-agent
kubectl get volumesnapshotclass
```

```text
Backup Volumes:
  Velero-Native Snapshots: <none included>

  CSI Snapshots: <none included>

  Pod Volume Backups: <none included>
Error from server (NotFound): daemonsets.apps "node-agent" not found
No resources found
```

**What the output tells you:** the backup holds manifests only: no snapshots, no pod volume backups, no node agent, no snapshot class. "Completed" only meant that everything Velero was asked to do succeeded.

**Fix:**

```bash
# Enable file-system backup with the node agent, then opt the database volume in
# (or add --default-volumes-to-fs-backup to back up every pod volume, opt-out style)
# (put the annotations in the StatefulSet's pod template so they survive restarts)
velero install --use-node-agent --provider aws ...
kubectl -n shop annotate pod postgres-0 backup.velero.io/backup-volumes=data --overwrite
kubectl -n shop annotate pod postgres-0 --overwrite \
  pre.hook.backup.velero.io/container=postgres \
  pre.hook.backup.velero.io/command='["/bin/sh","-c","psql -U postgres -c CHECKPOINT"]'
# Prove it: restore into a new namespace and count rows
velero restore create shop-drill --from-backup nightly-20261003 --namespace-mappings shop:shop-restore
kubectl -n shop-restore exec postgres-0 -- psql -U postgres -d shop -Atc 'SELECT count(*) FROM orders;'
```

**Why this fix works:** the node agent copies volume data with Kopia, and the annotation opts the volume in; a CHECKPOINT shortens crash recovery, but only a database-native backup (pg_dump, pgBackRest, an operator's backup) is consistent by design. The restore into a new namespace is the only proof that the backup contains data.

**Prevent it:** back up databases with database-native tools and use Velero for manifests and the other volumes; run a monthly restore test that checks row counts, not just the backup phase.

**Next step:** [Databases: Operators and CloudNativePG](38-learn-databases-ops.md) · [Learn Kubernetes: Storage](31-learn-kubernetes.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance: Backup and Restore Methods · [Velero file system backup](https://velero.io/docs/main/file-system-backup/)

**Community threads:** [Velero docs: File System Backup](https://velero.io/docs/main/file-system-backup/) · [Velero issues by reactions](https://github.com/vmware-tanzu/velero/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=velero+restore+pvc+empty+database) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=velero+restore+database+empty+pvc&restrict_sr=1)

### 9.3 No tested restore: RTO and RPO in the disaster

> **Seen as:** postmortem lines such as "restoring from the snapshot took over 18 hours" or "only daily backups were available", or ransomware that deleted the backups together with production · **Where:** any stack: pgBackRest, restic and borg, PBS, Velero, Dokploy backups, S3 · **Level:** [L4 · Senior/Lead] · **How common:** GitLab 2017 (rm -rf on the primary, an 18-hour-plus restore), Keepthescore (production database deleted, only daily backups) and other entries in Dan Luu's list, plus forum stories such as the restic "22TB restore" lessons

**Why it happens:** restore speed was never measured (network and disk throughput, decompression, WAL replay), so the RTO is a guess. Backups are reachable and deletable with the same credentials as production, so whatever deletes production can delete the backups too. There is no runbook and no owner, and the steps live in one person's head.

**Diagnose:**

```bash
# Measure, don't estimate: a full restore of the biggest database on a scratch host (PostgreSQL stopped there)
time sudo -u postgres pgbackrest --stanza=main --delta --type=time --target='2026-10-03 06:00:00+00' restore
# This times the file restore only: then start PostgreSQL and add the WAL replay time until it reaches the target
# Can the application's own key destroy backups? Try on a canary object: it must be denied
aws --endpoint-url https://s3.example.com --profile shop-app s3 rm s3://backups/canary.txt
aws --endpoint-url https://s3.example.com s3api get-object-lock-configuration --bucket backups
```

```text
real    4h12m38.551s
delete: s3://backups/canary.txt
An error occurred (ObjectLockConfigurationNotFoundError) when calling the GetObjectLockConfiguration operation: Object Lock configuration does not exist for this bucket
```

**What the output tells you:** the measured RTO for this database is over four hours, not the "about an hour" in the plan; the application's credentials can delete backups; and nothing is immutable. All three are findings for the risk register, discovered on a quiet day instead of during the disaster.

**Fix:**

```bash
# 3-2-1 with one immutable copy: a bucket with object lock, written by a backup-only key
aws --endpoint-url https://s3.example.com s3api create-bucket --bucket backups-locked --object-lock-enabled-for-bucket
aws --endpoint-url https://s3.example.com s3api put-object-lock-configuration --bucket backups-locked \
  --object-lock-configuration '{"ObjectLockEnabled":"Enabled","Rule":{"DefaultRetention":{"Mode":"COMPLIANCE","Days":30}}}'
# Append-only alternatives: borg behind an SSH forced command with --append-only,
# restic rest-server --append-only, PBS with credentials that production hosts don't have
```

Add point-in-time recovery for the important PostgreSQL databases (pgBackRest or WAL archiving, entry 5.7) so the RPO is minutes, not a day. Then run a quarterly game day: restore, run application-level checks, record the timings and update the runbook, with someone other than its author doing the restore.

**Why this fix works:** object lock or append-only storage means a stolen production key can add backups but not destroy them; PITR shrinks data loss to the last archived WAL segment; a timed drill turns RTO and RPO from hopes into numbers the business can accept or pay to improve. COMPLIANCE mode can't be shortened even by an administrator, so try retention lengths on a scratch bucket first.

**Prevent it:** a backup counts only when a restore test has passed. Put restore drills in the calendar like your CKA practice sessions, and keep the DR runbook somewhere you can read it when production is down.

**Next step:** [Senior architecture: Disaster recovery](39-learn-senior-architecture.md) · [Databases: RPO, RTO and the 3-2-1 rule](38-learn-databases-ops.md) · [CI/CD, IaC & SRE: the game day](33-learn-cicd-iac-sre.md) · KodeKloud: *Fundamentals of SRE* — Incident Management (Blameless Postmortem Culture) · [BorgBackup FAQ: append-only mode](https://borgbackup.readthedocs.io/en/stable/faq.html)

**Community threads:** [GitLab 2017 database outage postmortem](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) · [Dan Luu's post-mortems list](https://github.com/danluu/post-mortems) · Search: [Server Fault](https://serverfault.com/search?q=backup+ransomware+immutable+append-only) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=disaster+recovery+test+restore+backup&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises on the lab VMs (a two-worker Kubernetes lab for the last one). Snapshot first, break it exactly as described, then fix it using only the entry and write your five-line note.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Install MySQL with apt and try mysql -u root -p; then create an app user that can log in from app1 | 15 min | 3.1, 3.2 |
| 2 | Fresher | Start postgres:17 with a named volume, change POSTGRES_PASSWORD, redeploy; fix the login without losing data | 10 min | 1.1 |
| 3 | Junior | Bump a compose stack from postgres:17 to postgres:18 keeping the old mount path; find where the data went | 20 min | 1.2, 1.4 |
| 4 | Junior | Publish Redis on 6379 without a password, reach it from outside the lab, then close it and add ACL users | 20 min | 4.1 |
| 5 | Junior | Kill a restic backup halfway with kill -9 and make the next scheduled run succeed | 15 min | 5.2 |
| 6 | Mid-level | Upgrade the server past the backup image's pg_dump; catch the 20-byte files with an alert, then fix the script | 30 min | 5.4 |
| 7 | Mid-level | Publish MinIO behind Traefik under a stripped path prefix; reproduce SignatureDoesNotMatch and fix the routing | 30 min | 6.2, 6.1 |
| 8 | Senior | Create a logical slot, stop its consumer, generate WAL with pgbench until pg_wal grows; clean up and cap it | 30 min | 8.1 |
| 9 | Senior | Hold a transaction open, run ALTER TABLE from a CI job and watch the queue; redo it with lock_timeout and retries | 30 min | 7.2, 7.3 |
| 10 | Senior/Lead | Power off the worker running a Postgres StatefulSet; recover the pod, restore last night's backup into a new namespace and record the time | 60 min | 9.1, 9.2, 9.3 |

Quick questions to answer from memory:

1. Why does changing POSTGRES_PASSWORD in compose not change the password, and what does?
2. Which three layers does "can't connect to Postgres" walk through, and which error belongs to each?
3. Why does `pg_dump | gzip > file` hide a failed dump, and which one line in the script fixes it?
4. What keeps WAL on a primary forever, and which setting caps it?
5. What does Velero back up by default, and what does it skip?
6. Why must a node be fenced before you clear a Multi-Attach error?

---

## Where to go next

- [Databases for DevOps](38-learn-databases-ops.md): the fundamentals behind every entry here: connections, MVCC, locks, WAL, backups, replication, Redis, containers and migrations.
- [Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md): databases, volumes and S3 backups on your own platform (its section 10).
- [Observability stack problems](49-observability-stack-problems.md) and [Performance & observability](32-learn-performance-observability.md): exporters and alerts for connections, WAL, backup age and Redis memory.
- [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) and [Learn AWS](36-learn-cloud-aws.md): Proxmox Backup Server, S3, RDS and the VM layer under your databases.
- [Slow system](23-playbook-slow-system.md): when the database is slow because the host is (disk I/O, memory pressure, a busy hypervisor).
- [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) and [Deployment patterns](35-deployment-patterns.md): migrations as a pipeline stage, and releases that can still roll back.
- [Wazuh & security tools](48-wazuh-and-security-tools.md) and [Security & DevSecOps](37-learn-security-devsecops.md): exposed databases, secrets for backup keys, and incident response.
- [Senior architecture](39-learn-senior-architecture.md) and [Career ladder](40-career-ladder.md): turn a measured restore drill and an RPO/RTO table into senior-level evidence.
- Official docs: [PostgreSQL](https://www.postgresql.org/docs/current/) · [MySQL](https://dev.mysql.com/doc/) · [Redis](https://redis.io/docs/) · [PgBouncer](https://www.pgbouncer.org/config.html) · [pgBackRest](https://pgbackrest.org/) · [restic](https://restic.readthedocs.io/en/stable/077_troubleshooting.html) · [BorgBackup](https://borgbackup.readthedocs.io/en/stable/faq.html) · [Velero](https://velero.io/docs/main/file-system-backup/) · [Proxmox Backup Server](https://pbs.proxmox.com/docs/)
