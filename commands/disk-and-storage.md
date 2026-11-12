# Disk, filesystems & storage

Storage incidents come in two kinds: something ran out (bytes, inodes, or space still held by deleted files), or the storage is slow or sick (deep queues, high latency, failing media). Work from the verdict to the cause: which filesystem and which counter is full (`df -h`, `df -i`), what fills it (`du -x`), how the stack is built (`lsblk`, `findmnt`, LVM), whether a device is saturated (`iostat -x`) or failing (`smartctl`); only then grow, repair or benchmark. Many commands here rewrite partitions, filesystems or swap and cannot be undone: their Safety line and Trap say so.

| If you would reach for | Prefer | Because |
|---|---|---|
| `df -h` | `df -hT -x tmpfs -x squashfs -x overlay` **and** `df -i` | a filesystem can run out of inodes with gigabytes free, and pseudo filesystems only add noise |
| `du -sh /*` | `du -xh --max-depth=1 / | sort -h` | `-x` stays on the full filesystem instead of adding up other disks, /proc and NFS shares |
| `rm` on a huge log that is still being written | `truncate -s 0 FILE`, or reload the writer | a deleted file stays allocated while a process holds it open, so rm frees nothing |
| `top` showing `wa`, or `%util` at 100 | `iostat -xyz 1 3`: await, aqu-sz, f_await | latency and queue depth show saturation; `%util` misleads on SSD, NVMe and RAID |
| `dd if=/dev/zero of=FILE bs=1M` as a benchmark | `fio --direct=1` with the workload's block size and depth | dd times one sequential stream, often cached; databases live on random 4 KiB I/O and fsync latency |
| `smartctl -H` says PASSED | `smartctl -A`: raw values of 5, 187, 197, 198 | PASSED only means no threshold was crossed; rising raw counts mean the disk is dying |
| `umount -l` when the target is busy | `fuser -vm MOUNT`, then stop the holder | a lazy unmount hides the mount while processes keep using the filesystem |
| editing fstab, then rebooting | `findmnt --verify`, then `mount -a` | a wrong UUID found now is a quick fix; found at boot it is emergency mode |

### df — which filesystem is full, in bytes or in inodes?
Match: df
Instead of: —
Safety: read-only · it asks every mounted filesystem, so it hangs on a dead NFS server; `-x nfs -x nfs4` (or `-l`) skips network filesystems

**In one line:** `df` asks each mounted filesystem for its size, used and free space, or with `-i` its inodes, so you learn **which** filesystem is full and **which counter** ran out.

**Read the command:** `df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay`

| Part | Meaning |
|---|---|
| `-h` | sizes in powers of 1024 (G = GiB) |
| `-T` | add the filesystem type |
| `-x tmpfs -x devtmpfs` | hide RAM-backed pseudo filesystems |
| `-x squashfs -x overlay` | hide snap images (always 100%) and Docker's per-container overlay mounts |
| `-i` | inodes instead of blocks |
| `df -h /var/log` | only the filesystem that holds this path |
| `-t tmpfs`, `--output=avail -B1` | only this type / one field in bytes, for scripts |

**What the output tells you:**

```
$ df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   48G   28G   18G  61% /
/dev/sdb1                         xfs   500G  490G   10G  98% /data
$ df -i /
Filesystem                         Inodes   IUsed IFree IUse% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv 3145728 3145728     0  100% /
```

Every file needs one **inode** (its metadata record) plus data **blocks**. ext4 fixes the inode count at mkfs time (by default one per 16 KiB), so millions of tiny files (PHP sessions, caches) exhaust inodes while bytes are free; XFS creates them on demand. Here `/` has 18G free but no inodes, so every new file fails with "No space left on device"; /data is short of bytes. `Use%` leaves out ext4's 5% root reserve: 100% means full for normal users, not yet for root.

**Why it is effective:** it answers the first two questions of any disk-full incident: **which** filesystem (often not the one you think: a separate /var/lib/docker, a small /boot) and **which counter**. Without `-i`, an inode-full disk looks healthy.

**Trap:** df and du disagree when a **deleted file is still open** (df counts it, du cannot see a file without a name) or files hide **under a mount point**. On a dead NFS mount df hangs: add `-x nfs -x nfs4`, or use `findmnt`.

**Next step:** bytes full → `du -xh --max-depth=1 MOUNT | sort -h`. Inodes full → `du --inodes -x MOUNT | sort -n | tail`. df far above du → `lsof -nP +L1`. Free space but writes fail → `findmnt -no OPTIONS -T PATH` and `dmesg`. Old size after a disk grew → `lsblk`, then `growpart`.

### du / ncdu — what is actually using the space?
Match: du, ncdu
Instead of: ls -lh, find / -size +1G
Safety: read-only · walks every file below the path (heavy I/O on big trees); without sudo it silently skips what it cannot read

**In one line:** `du` walks a directory tree and adds up the **disk blocks** its files occupy, naming the directories that fill a filesystem; `ncdu` does the walk once and lets you browse the result.

**Read the command:** `du -xh --max-depth=1 / | sort -rh`

| Part | Meaning |
|---|---|
| `-x` | stay on this filesystem: skip /proc, other disks and NFS mounts below the path |
| `-h` | human-readable sizes (K, M, G) |
| `--max-depth=1` | one total per directory one level down, plus the path itself |
| `| sort -rh` | biggest first (`sort -h` understands K, M, G) |
| `sudo … 2>/dev/null` | read every directory (without root, totals come out low) and hide "Permission denied" noise |
| `-sh /var/*`, `-ah` | one total per argument / files as well as directories |
| `--inodes` | count inodes instead of blocks: where millions of small files live |
| `ncdu -x /` | the same walk, browsed with the arrow keys; `d` deletes (**changes state**) |

**What the output tells you:**

```
$ sudo du -xh --max-depth=1 / 2>/dev/null | sort -rh | head -3
45G	/
41G	/var
3.1G	/usr
$ sudo du -xh --max-depth=1 /var/lib 2>/dev/null | sort -rh | head -2
36G	/var/lib
34G	/var/lib/docker
```

The first line is the path's own total. Drill into the biggest entry one level at a time: here /var, /var/lib, then Docker.

**Why it is effective:** df says the filesystem is full; du names the directory. `-x` makes the numbers add up: without it, `du /` also counts /proc, other disks and NFS shares, and may hang on a dead share.

**Compared with `ls -lh` / `find / -size +1G`:** ls shows one directory and each file's **apparent** size (its length), not the blocks it uses; `find -size +1G` finds single huge files but misses 40 GB of small ones.

**Trap:** du cannot see a deleted file that is still open (df counts it; `lsof -nP +L1` finds it), nor files written into a directory **before** a disk was mounted over it: bind-mount the parent (`mount --bind / /mnt/rootonly`) and run du there. It counts allocated blocks, so a sparse 2 GB image looks almost empty (`--apparent-size` shows the length).

**Next step:** a directory you recognise → its own cleanup (`journalctl --vacuum-size`, `docker system df`, logrotate). du total far below df's Used → `lsof +L1`, then the bind-mount check. Inodes → `du --inodes -x / | sort -n | tail`.

### fallocate / truncate — make a file of a given size, or empty one in place
Match: fallocate, truncate
Instead of: rm on a log that is still open, dd if=/dev/zero to make big files
Safety: changes state: truncate discards the content at once, with no undo; fallocate takes real disk space immediately

**In one line:** `truncate -s` sets a file's length: `-s 0` empties it **in place** (same inode, so the writer keeps its descriptor and the space comes back at once), a larger size makes a sparse file; `fallocate -l` reserves real blocks instantly, for swap files and disk-full labs.

**Read the command:** `truncate -s 0 /proc/2290/fd/12`

| Part | Meaning |
|---|---|
| `-s 0` | new length 0 bytes: content dropped, blocks freed, inode kept |
| `/proc/2290/fd/12` | descriptor 12 of PID 2290: reaches a **deleted** log the process still holds open |
| `-s 0 /var/lib/docker/containers/ID/ID-json.log` | empty a runaway container log; the daemon keeps writing into it |
| `-s 2G /var/tmp/lab-disk.img` | length 2 GiB with nothing written: a **sparse** file (`ls -l` 2G, `du` almost 0) |
| `fallocate -l 2G /swapfile` | allocate 2 GiB of real blocks; nothing is written, so it is instant |

**What the output tells you:** both print nothing; the effect shows in lsof and df:

```
$ sudo lsof -nP +L1
COMMAND  PID USER   FD  TYPE DEVICE   SIZE/OFF NLINK    NODE NAME
java    2290 deploy 12w  REG  253,0 6442450944     0 1835412 /opt/app/logs/app.log.1 (deleted)
$ sudo truncate -s 0 /proc/2290/fd/12 && df -h / | tail -1
/dev/mapper/ubuntu--vg-ubuntu--lv   48G   39G  6.9G  85% /
```

`NLINK 0` and `(deleted)`: 6 GB held only by descriptor 12 of PID 2290. After the truncate, df gets them back without a restart.

**Why it is effective:** `rm` removes only the **name**: while a process holds the file open, its blocks stay allocated. truncate frees them now and keeps the inode the process writes to. fallocate makes a 2 GB file in milliseconds where dd writes every byte.

**Compared with `rm` / `dd`:** rm is right for a file nobody has open (`fuser FILE`); for an open log the lasting fix is a reload or logrotate's `copytruncate`. dd from /dev/zero writes every block: slower, the fallback when swapon rejects a fallocated file.

**Trap:** the content is gone for good: save what the incident needs first. A writer that did **not** open the file in append mode keeps writing at its old offset, so the file returns to its old length, sparse (`ls -l` big, `du` small). Truncating a json log empties `docker logs` too. A sparse image reserves nothing and can fill the disk later.

**Next step:** after emptying a log, fix rotation (`log-opts` in daemon.json, logrotate with a reload). Swap file → `chmod 600`, `mkswap`, `swapon`. Lab image → `losetup --find --show --partscan`.

### lsblk / blkid — which disks, partitions and filesystems exist, and how are they stacked?
Match: lsblk, blkid
Instead of: fdisk -l, ls /dev/sd*
Safety: read-only · run blkid with sudo: as a normal user it may print cached, unverified data

**In one line:** `lsblk` draws the storage stack as a tree (disk → partition → LVM, RAID or crypt → mount point) from the kernel's view; `lsblk -f` and `blkid` add each filesystem's type, label and **UUID**, the name fstab should use.

**Read the command:** `lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS`

| Part | Meaning |
|---|---|
| `-o NAME,SIZE,TYPE,…` | choose the columns; TYPE is `disk`, `part`, `lvm`, `raid1`, `crypt`, `loop` … |
| `FSTYPE` | `ext4`, `xfs`, `swap`, `LVM2_member`, `linux_raid_member`; empty = nothing recognised |
| `MOUNTPOINTS` | every place it is mounted (older util-linux has only `MOUNTPOINT`) |
| `-f` | filesystem view: FSTYPE, LABEL, UUID, FSAVAIL, FSUSE% |
| `-d -o NAME,ROTA,TRAN,MODEL` | whole disks only: rotational?, transport (sata, nvme, iscsi), model |
| `-o NAME,SERIAL` | on EC2 Nitro the NVMe serial is the EBS volume ID |
| `blkid -s UUID -o value /dev/sdb1` | only the UUID, for fstab or a script |

**What the output tells you:**

```
NAME                      SIZE TYPE FSTYPE      MOUNTPOINTS
sda                       100G disk
├─sda2                      2G part ext4        /boot
└─sda3                     48G part LVM2_member
  └─ubuntu--vg-ubuntu--lv  48G lvm  ext4        /
sdb                       500G disk
```

The disk is 100 GB, but sda3 and the LV are 48 GB: the disk grew and no layer above it followed. `sdb` has no partition, filesystem or mount: attached but never set up, the usual "new disk not showing up".

**Why it is effective:** one screen shows every layer and the gaps: unused disk space, an LV without a mount, a disk the kernel never saw (then it is the hypervisor, a cable or a rescan). The UUID keeps fstab right when `sdb` and `sdc` swap names at boot.

**Compared with `fdisk -l` / `ls /dev/sd*`:** fdisk -l prints partition tables in sectors but not LVM, RAID or mount points; `ls /dev/sd*` misses NVMe (`nvme0n1`) and virtio (`vda`) disks and shows no relationships.

**Trap:** sizes are the kernel's view: an enlarged virtual disk keeps its old size until the guest rescans it (`echo 1 | sudo tee /sys/class/block/sda/device/rescan`). `ROTA` is unreliable in VMs. mkfs gives a filesystem a **new** UUID: update fstab afterwards.

**Next step:** disk bigger than its partition → `growpart`. No FSTYPE where data should be → check (`wipefs -n`, backups) before any mkfs. UUID for fstab → `blkid`, then `findmnt --verify`. Unknown disk on EC2 → `lsblk -o NAME,SERIAL` against the volume IDs.

### findmnt — what is mounted where, with which options, and is fstab valid?
Match: findmnt
Instead of: mount | grep, cat /etc/fstab
Safety: read-only · the plain listing reads the kernel's mount table without touching the filesystems, so it works while df hangs on a dead NFS server

**In one line:** `findmnt` lists mounts as a tree or filtered by mount point, path or type, shows the exact options each one runs with (`ro`, `noexec`, `hard`), and `--verify` checks /etc/fstab before a reboot does.

**Read the command:** `findmnt -no OPTIONS -T /tmp`

| Part | Meaning |
|---|---|
| `-T /tmp` | `--target`: the mount that holds this path, even a file deep inside it |
| `-o OPTIONS` | print only the options column (also `TARGET,SOURCE,FSTYPE`) |
| `-n` | no header line, for scripts |
| `findmnt /data` | that mount point only; prints nothing and exits 1 if nothing is mounted there |
| `-t nfs,nfs4,cifs` | only these types: the network mounts |
| `--verify` (`--verbose`) | check every /etc/fstab line: source exists, target, type, options (and list the passed checks) |
| `-rn -o TARGET,SOURCE` | raw, header-less columns for a pipe |

**What the output tells you:**

```
$ findmnt -no OPTIONS -T /tmp
rw,nosuid,nodev,noexec,relatime
$ sudo findmnt --verify
/data
   [E] unreachable source: UUID=5a7c9d3e-1111-4abc-8def-0123456789ab: No such file or directory

0 parse errors, 1 error, 0 warnings
```

`noexec` on /tmp: a script run from there gets "Permission denied" whatever its mode bits say; `ro` on `/` would mean the kernel remounted it after errors. Each `[E]` line in `--verify` is a mount that will fail at boot: here a UUID no disk has.

**Why it is effective:** noexec denials, "Read-only file system" and "which disk is this path on?" are all mount questions, answered in one line each, and `--verify` catches the stale UUID that otherwise shows up as emergency mode at the next reboot.

**Compared with `mount | grep` / `cat /etc/fstab`:** `mount` prints the same table as long lines, and `grep nfs` also matches `nfsd`; fstab shows what **should** be mounted, not what is.

**Trap:** if `-T` on a directory that should be its own disk answers `/`, the mount is missing and the data went to the root filesystem. `--verify` checks sources that exist **now**; it cannot know whether a network share will answer at boot. Options are shown as the kernel applies them, defaults included.

**Next step:** `ro` → `dmesg -T | grep -iE 'ext4|xfs|i/o error'` before any remount. noexec in the way → run the script from elsewhere. `[E]` lines → fix the line (UUID from `blkid`), add `nofail` to data disks, then `mount -a`. NFS options → `nfsstat -m`.

### mount — attach a filesystem, change its options, or test fstab
Match: mount
Instead of: rebooting to find out whether fstab works
Safety: changes state: attaches filesystems or changes their options at once, until reboot unless fstab has them · plain `mount` only lists (`findmnt` reads better)

**In one line:** `mount` attaches a filesystem (partition, LV, NFS export, or a directory with `--bind`) to a directory now; `-o remount` changes the options of a mounted one, and `-a` mounts every fstab entry not mounted yet.

**Read the command:** `mount -t nfs4 -o hard 127.0.0.1:/srv/export /mnt/share`

| Part | Meaning |
|---|---|
| `-t nfs4` | filesystem type: detected for disks, named for NFS |
| `-o hard` | NFS: retry forever while the server is silent (the default); `soft` returns an error after `retrans` tries |
| `127.0.0.1:/srv/export` | the source: server and exported path (for a disk: `/dev/xvdf1` or `UUID=…`) |
| `/mnt/share` | the mount point; its previous contents are hidden while mounted |
| `-o remount,rw /` | **changes state** in place: here read-only → read-write |
| `-a` | mount every fstab entry not yet mounted (not `noauto`): the test before a reboot |
| `--bind / /mnt/rootonly` | show `/` again without the mounts on top: reveals files hidden under mount points |

**What the output tells you:** nothing on success. Failures are specific: `wrong fs type, bad option, bad superblock` (unformatted, wrong type or damaged), `can't find LABEL=labdata` (device absent), `mount.nfs: access denied by server` (export list or client address), `mount.nfs: Connection timed out` (network, firewall, server down). After an fstab edit, a `(hint)` that systemd still uses the old version asks for `systemctl daemon-reload`.

**Why it is effective:** the options set here decide later behaviour: `hard` or `soft` decides whether a dead NFS server freezes processes or returns errors; `noexec` and `ro` decide what fails. `mount -a` proves an fstab change while you still have a shell.

**Compared with rebooting:** a reboot applies fstab too, but a bad line then fails without a usable shell (emergency mode; root is locked on Ubuntu). `findmnt --verify` plus `mount -a` finds the same error safely.

**Trap:** `remount,rw` on a filesystem the kernel made read-only after I/O errors writes onto damaged metadata: find the cause first. Mounting over a non-empty directory hides its files and the space they use. `soft` on a writable share risks silent data corruption. Linux's NFS client refuses most option changes on remount, `hard`/`soft` and `timeo` included: unmount and mount again.

**Next step:** bad superblock or wrong type → `lsblk -f`, then `fsck -n`. Missing UUID or LABEL → `blkid`, fix fstab. NFS refused or timing out → `exportfs -v` on the server, `nc -zv SERVER 2049`. Read-only root → `dmesg` first, then fsck from rescue.

### umount — detach a filesystem, and what to do when it is busy
Match: umount
Instead of: rebooting, umount -l by reflex
Safety: changes state: detaches the filesystem; `-l` hides it while processes keep using it; `-f` aborts pending NFS requests, and unwritten data is lost

**In one line:** `umount` flushes and detaches a mounted filesystem, and refuses with `target is busy` while a process has a file open, a current directory or a mapped library in it.

**Read the command:** `umount -f -l /mnt/share`

| Part | Meaning |
|---|---|
| `/mnt/share` | the mount point (or the device) to detach |
| `-l` | lazy: remove it from the directory tree now, finish when the last user lets go |
| `-f` | force: for an unreachable NFS server, abort the requests waiting on it |
| `umount /data` | the normal case: flush and detach, or "busy" |
| `umount /mnt/shared || umount -l /mnt/shared` | the handbook's stale-handle fix: clean first, lazy as the fallback |

**What the output tells you:**

```
$ sudo umount /data
umount: /data: target is busy.
$ sudo fuser -vm /data
                     USER        PID ACCESS COMMAND
/data:               root     kernel mount /data
                     deploy     3121 ..c.. bash
                     app        2290 F.... java
```

A shell sits in the directory (`c`, current directory) and java has a file open for writing (`F`): leave the shell, stop java through its service, then unmount cleanly.

**Why it is effective:** a cleanly unmounted filesystem is the only one safe to fsck, shrink, detach or unplug; "busy" names a real dependency to find, not to force past.

**Compared with a reboot or `umount -l` by reflex:** a reboot unmounts everything, with downtime, and can hang on the same dead NFS server. `-l` returns at once, but processes keep their files and the device stays in use, so a later fsck, detach or new mount on that path causes damage or confusion.

**Trap:** after `-l` the filesystem vanishes from `findmnt` and `df` but stays in use by whoever had it open. Busy with no process listed usually means a mount below it, an NFS export, a loop device or a swap file on it.

**Next step:** busy → `fuser -vm MOUNT` or `lsof +f -- MOUNT`, then stop the holder or `cd /`. Nothing listed → `findmnt -R MOUNT`, `losetup -l`, `swapon --show`, `exportfs -v`. Dead NFS server, share not needed → `umount -f -l`. Unmounted for repair → `fsck -n` or `xfs_repair -n`.

### fuser — which processes hold this mount, file or port?
Match: fuser
Instead of: lsof +f -- MOUNT
Safety: read-only with `-v` · `-k` sends SIGKILL to every process found; with `-m` on a path that is not a mount point, that is everything using the root filesystem

**In one line:** `fuser` lists the processes using a file, a whole mounted filesystem (`-m`) or a TCP/UDP port, and how each one uses it: open file, current directory, executable or mapped library.

**Read the command:** `fuser -vm /data`

| Part | Meaning |
|---|---|
| `-v` | verbose table: USER, PID, ACCESS, COMMAND (without it, only PIDs) |
| `-m /data` | every process using any file on the filesystem mounted at /data |
| `443/tcp`, `-n udp 53` | a port instead of a file |
| `/var/lib/dpkg/lock-frontend` | one file: which apt or dpkg process holds the lock |
| `-M` | act only if the name is a mount point: the seat belt for `-km` |
| `-k` | **changes state**: kill them all, with SIGKILL unless another signal is named |

**What the output tells you:**

```
$ sudo fuser -v 80/tcp 443/tcp
                     USER        PID ACCESS COMMAND
80/tcp:              root       1234 F.... apache2
                     www-data   2206 F.... apache2
443/tcp:             root       1234 F.... apache2
                     www-data   2206 F.... apache2
```

ACCESS: `F` open for writing (sockets show this way), `f` open, `c` current directory, `e` executable, `r` root directory, `m` mapped file or library; with `-m`, `kernel mount` is the mount itself. The `root` PID is Apache's parent: act on its service, not on the workers.

**Why it is effective:** "target is busy", "address already in use" and "could not get lock" all mean some process has it open; fuser names it in one line, for a whole mount at once, and the access letter says how to free it: `c` is a shell to `cd` out of, `F` a service to stop.

**Compared with `lsof`:** `lsof +f -- /data` shows the same holders with file names and descriptors, but is slower on busy hosts; for sockets `ss -ltnp` is the better view.

**Trap:** `-k` kills masters and workers alike, bypassing systemd (which may just restart them) and losing in-flight work. `fuser -km /data` while /data is **not** mounted targets the root filesystem, almost every process: add `-M`. Without sudo, other users' processes are missing.

**Next step:** a service holds it → `systemctl status PID` names the unit, then `systemctl stop UNIT`. A shell → `cd /` there. Wrong program on a port → `ss -ltnp 'sport = :443'`. dpkg lock → let unattended-upgrades finish (`ps -fp PID`); never delete the lock file.

### iostat — is a disk the bottleneck, and how badly?
Match: iostat
Instead of: top, vmstat (wa)
Safety: read-only (package sysstat)

**In one line:** `iostat -x` prints per device and per interval how many I/Os completed, how big they were, how long each took **including the queue**, how many were in flight, and how much of the time the device was busy.

**Read the command:** `iostat -xyz 1 3`

| Part | Meaning |
|---|---|
| `-x` | extended statistics: latency, queue, request size, `%util` |
| `-y` | skip the first report, which is the average **since boot** |
| `-z` | hide devices with no I/O in the interval |
| `1 3` | 1-second interval, 3 reports (without a count: until Ctrl-C) |
| `-N` | device-mapper names (`ubuntu--vg-ubuntu--lv`) instead of `dm-0` |

**What the output tells you** (columns trimmed):

```
Device   r/s    rkB/s r_await rareq-sz    w/s   wkB/s w_await wareq-sz   f/s f_await aqu-sz %util
sda     2.00    16.00    0.61     8.00  14.00  112.00    0.94     8.00  3.00    0.67   0.02   1.60
sdb   381.00 48768.00   71.24   128.00 162.00 3112.00  148.92    19.21 21.00  210.33  56.79 100.00
```

`r_await`/`w_await`: ms per request, queue included (normal: NVMe under 1, SATA SSD 1–5, HDD 5–15). `aqu-sz`: requests in flight on average (≈ IOPS × await in seconds); sustained above 1 on one HDD is a queue. `rareq-sz`/`wareq-sz`: KB per request, 4–16 random, 128 and up sequential. `f/s`, `f_await`: flushes from fsync, i.e. commit latency. `%util`: share of time with **at least one** request in flight. Here sdb, an HDD, serves a backup's sequential reads while writes wait 149 ms and flushes 210 ms: every commit queues behind it.

**Why it is effective:** it separates slow from busy from capped: IOPS flat at a round number with rising await is a cloud or QoS limit, small writes with high `f_await` an fsync problem, a deep queue of large reads a batch job.

**Compared with `top` / `vmstat`:** their `wa` only says CPUs sat idle while I/O was pending, not which device, what pattern or how slow.

**Trap:** `%util` is honest only for one spinning disk: NVMe, SSD, RAID and SAN or cloud volumes serve requests in parallel, so 100% can mean "never idle, still fast"; judge them by await and aqu-sz against their normal. Without `-y` the first block is the since-boot average and looks calm. Ignore guides that use `svctm`: current sysstat removed it.

**Next step:** a slow device → `iotop -oPa` or `pidstat -d 1`. High `f_await` → `fio --fdatasync=1` on that filesystem. IOPS flat at a round number → the volume's limits. One RAID member slower than the rest → `smartctl -A` on it.

### iotop — which process is doing the disk I/O right now?
Match: iotop, iotop-c
Instead of: top
Safety: read-only · needs root; the IO> and SWAPIN columns need kernel delay accounting, off by default on newer kernels (`sysctl kernel.task_delayacct=1`)

**In one line:** `iotop` shows disk read and write traffic **per process** (rates, or totals with `-a`) and the share of time each one waited for I/O, so you can name the backup, build or database behind a busy device.

**Read the command:** `iotop -boPa -d 5 -n 3`

| Part | Meaning |
|---|---|
| `-b` | batch mode: plain text for `head` or a file, instead of the full-screen view |
| `-o` | only processes that actually did I/O |
| `-P` | processes, not individual threads |
| `-a` | accumulated totals since iotop started, instead of current rates |
| `-d 5`, `-n 3` | 5 seconds between refreshes, 3 refreshes, then exit |

**What the output tells you** (total lines trimmed):

```
    PID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
  10421 be/4 root          2.61 G      0.00 B  0.00 % 86.41 % rsync -a /srv/docker-volumes/ /mnt/backup/volumes/
   1290 be/4 999           0.00 B     81.20 M  0.00 % 41.12 % postgres: walwriter
    398 be/3 root          0.00 B     12.04 M  0.00 % 18.90 % [jbd2/sdb1-8]
```

`IO>` is the share of time the process waited for I/O: rsync is the consumer, postgres (container UID 999) the victim. Kernel threads point at other subsystems: `jbd2/…` is the ext4 journal (fsync load), `kswapd` memory pressure, `md…_resync` a RAID rebuild.

**Why it is effective:** iostat says a device is saturated; iotop says **who** saturates it, which decides the fix: throttle a batch job, tune an application, or follow a kernel thread elsewhere.

**Compared with `top`:** a process blocked on disk just looks idle in top. `pidstat -d 1` also gives per-process kB/s, with an `iodelay` column.

**Trap:** buffered writes are counted when a process dirties the page cache, while the device writes happen later in kernel threads, so per-process and device numbers do not match second by second. Without delay accounting `IO>` shows `?unavailable?`. `iotop-c`, a C rewrite, takes the same main flags.

**Next step:** a batch job → a cgroup limit (`systemd-run --scope -p IOWriteBandwidthMax='/dev/sdb 20M' CMD`) or another schedule. The database itself → `iostat` f_await, `fio --fdatasync=1`. `kswapd` → `vmstat 1`. `md…_resync` → `cat /proc/mdstat`. Related: `iotop-c -oPa` is the same view in the C rewrite (package iotop-c).

### fio — how fast is this storage for the workload you actually run?
Match: fio
Instead of: dd, copying a big file
Safety: changes state: creates a test file of `--size` and loads the disk for `--runtime`; pointed at a device (`--filename=/dev/sdX`), a write test destroys its data

**In one line:** `fio` generates a precisely described I/O workload (pattern, block size, queue depth, cached or direct, with or without fsync, duration) and reports IOPS, bandwidth and the full latency distribution.

**Read the command:** `fio --name=rand --filename=/var/tmp/fio.test --size=1G --direct=1 --rw=randread --bs=4k --ioengine=libaio --iodepth=32 --runtime=30 --time_based --group_reporting`

| Part | Meaning |
|---|---|
| `--name=rand --filename=/var/tmp/fio.test` | job name; a test **file** inside a filesystem, never a device |
| `--size=1G` | size of the test file, the region the job works on |
| `--direct=1` | O_DIRECT: bypass the page cache, or you measure RAM |
| `--rw=randread --bs=4k` | random 4 KiB reads, like a database; `read`/`write` with `--bs=1M` for backups |
| `--ioengine=libaio --iodepth=32` | asynchronous I/O with 32 requests in flight (a synchronous engine keeps one per job) |
| `--runtime=30 --time_based` | run exactly 30 s, looping over the file |
| `--group_reporting` | one summary for all jobs (`--numjobs=4` runs four in parallel) |

**What the output tells you** (trimmed):

```
  read: IOPS=45.2k, BW=177MiB/s (185MB/s)(5.18GiB/30001msec)
    clat percentiles (usec):
     | 50.00th=[  685], 90.00th=[  930], 99.00th=[ 1336], 99.90th=[ 2474]
```

IOPS × block size = bandwidth (45.2k × 4 KiB ≈ 177 MiB/s). `clat` is completion latency, and the **percentiles** matter more than the average: p99 is what the slowest 1% of requests feel. In a commit-latency test (`--rw=write --fdatasync=1`, an fdatasync after every write) read `sync percentiles`: etcd wants p99 below about 10 ms.

**Why it is effective:** storage has three numbers (IOPS, throughput, latency), and each workload depends on a different one; fio asks exactly the one that matters (4 KiB random for a database, 1 MiB sequential for a backup target, fdatasync latency for etcd) and leaves a baseline for later.

**Compared with `dd` / copying a file:** dd measures one sequential stream at queue depth 1: fine for "does it do 100 MB/s sequentially?", not for "why is the database slow?". A copy adds the source disk, the network and the tool.

**Trap:** without `--direct=1` you benchmark the page cache. Shared storage and cloud volumes with burst credits vary from run to run, and the test hurts neighbours: repeat it, off-peak. fio leaves its test file behind (`--filename`, or `NAME.0.0` in `--directory`): delete it.

**Next step:** far below the device class (HDD ~150 random IOPS, SATA SSD tens of thousands, NVMe hundreds of thousands) → `iostat -x` during the run, `smartctl`, the volume's limits. fdatasync p99 too high → faster storage (NVMe, or SSD with power-loss protection), not tuning.

### dd — copy raw bytes, and why it is a weak benchmark
Match: dd, hdparm
Instead of: —
Safety: read-only only when `of=` is `/dev/null` · changes state: `of=` a file writes it; `of=` a device **overwrites the disk** without asking

**In one line:** `dd` copies data from `if=` to `of=` in blocks of the size you choose and reports bytes and speed at the end: a quick sequential read or write figure, and also the tool that silently wipes a disk when `of=` is wrong.

**Read the command:** `dd if=/dev/zero of=/data/testfile bs=1M count=1024 oflag=direct`

| Part | Meaning |
|---|---|
| `if=/dev/zero` | input: endless zeros, nothing read from disk |
| `of=/data/testfile` | output: a test file on the filesystem under test (**a device here destroys it**) |
| `bs=1M`, `count=1024` | 1 MiB per read and write, 1024 times: 1 GiB sequential |
| `oflag=direct` | write with O_DIRECT, past the page cache (otherwise you time RAM) |
| `if=/data/testfile of=/dev/null iflag=direct` | the read test: read the file back uncached, discard it |
| `status=progress` | show the transfer rate while it runs |
| `if=/dev/zero of=/dev/null bs=1 count=500000` | 1-byte blocks: a syscall-cost demo, not a disk test |

**What the output tells you:**

```
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB, 1.0 GiB) copied, 4.21 s, 255 MB/s
```

`1024+0`: 1024 full blocks, no partial ones. The last line is the average speed of this one sequential stream (MB = 1,000,000 bytes).

**Why it is effective:** it is on every Linux box and answers one narrow question fast: can this file or filesystem be read or written sequentially at the expected speed? Reading a real backup file to `/dev/null` separates "the source disk is slow" from "the network is slow".

**Compared with `fio`:** fio controls pattern, queue depth and fsync and reports latency percentiles; dd is one sequential stream at queue depth 1, meaningless for databases, VMs or etcd.

**Trap:** without `oflag=direct` (or `conv=fdatasync`) a write test ends in the page cache and reports RAM speed, and a recently read file comes back from cache (`fincore FILE` shows it). Zeros compress to nothing on ZFS with compression and many SANs. `if` and `of` are one typo apart: `of=/dev/sdb` overwrites a disk with no prompt.

**Next step:** sequential speed fine but the app slow → `fio` with the app's block size and `--fdatasync=1`. Read speed low → `iostat -x` while it runs, then `smartctl`. Cloning a failing disk → `ddrescue`, not dd. Related: `hdparm -tT /dev/sda` is a two-second read check (`-T` cached reads, `-t` buffered reads from the disk); like dd it measures sequential reads only.

### smartctl — is this physical disk failing, even if it says PASSED?
Match: smartctl
Instead of: smartctl -H alone, waiting for I/O errors in dmesg
Safety: read-only for -H, -i, -A, -a and -l · `-t short|long` starts a self-test inside the drive (extra load, results later); needs root

**In one line:** `smartctl` reads the drive's own SMART data: an overall verdict, counters of bad and remapped sectors and cable errors, NVMe wear, and the drive's error and self-test logs.

**Read the command:** `smartctl -H -A /dev/sdb`

| Part | Meaning |
|---|---|
| `-H` | the overall verdict: `PASSED` or `FAILED` |
| `-A` | the vendor attribute table (ATA and SATA disks) |
| `/dev/sdb` | the whole disk, not a partition; NVMe: `/dev/nvme0` |
| `-a`, `-i` | everything / identity only (model, serial, firmware) |
| `-t short`, `-t long` | **start** a self-test (minutes / hours); read results later with `-l selftest` (`-l error`: the drive's error log) |
| `-d megaraid,1` | disk 1 behind a MegaRAID/PERC controller (`-l scterc` shows a disk's error-recovery timeout) |

**What the output tells you:**

```
SMART overall-health self-assessment test result: PASSED
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  5 Reallocated_Sector_Ct   0x0033   188   188   140    Pre-fail  Always       -       364
197 Current_Pending_Sector  0x0032   200   200   000    Old_age   Always       -       8
199 UDMA_CRC_Error_Count    0x0032   200   200   000    Old_age   Always       -       0
```

Read **RAW_VALUE**: VALUE, WORST and THRESH are normalised scores, and FAILED appears only when the drive decides a pre-fail score crossed its threshold. The attributes that matter: **5** sectors already remapped to spares, **197** unreadable sectors waiting to be remapped, **198** sectors found uncorrectable, **187** (Reported_Uncorrect) errors ECC could not fix. Any of them rising means the disk is dying. **199** counts transfer errors between disk and controller: the cable or backplane, not the disk. Here: PASSED, yet 364 remapped and 8 unreadable sectors. Replace it.

**Why it is effective:** a failing disk is often just **slow** for weeks (internal retries) before it fails; the raw counts show the decay while redundancy still exists, and 199 keeps you from replacing a good disk for a bad cable.

**Compared with `-H` alone / dmesg:** `-H` catches only drives that already admit failure; many die without ever saying FAILED, and dmesg I/O errors arrive when data is already unreadable.

**Trap:** VMs and cloud volumes have no SMART to read: the hypervisor or provider owns the disks. Behind hardware RAID, `/dev/sda` is the controller's virtual disk: use `-d megaraid,N` or the vendor tool.

**Next step:** 5, 197 or 198 rising → replace it (in RAID, see `mdadm`); without RAID, copy the data off first. 199 rising → reseat or replace the cable. NVMe → `nvme smart-log`. Many disks → smartd with mail alerts.

### nvme — NVMe drive inventory, wear and errors
Match: nvme
Instead of: —
Safety: read-only as used here (`list`, `smart-log`, `id-ctrl`); needs root · other subcommands such as `format` and `sanitize` erase the drive

**In one line:** `nvme` (package nvme-cli) talks to NVMe drives directly: `nvme list` maps each `/dev/nvmeXnY` to its model, serial and firmware, and `nvme smart-log` prints the drive's standard health log.

**Read the command:** `nvme smart-log /dev/nvme0`

| Part | Meaning |
|---|---|
| `smart-log` | the NVMe SMART / health log |
| `/dev/nvme0` | the controller; `/dev/nvme0n1` is its first namespace, the block device you partition |
| `nvme list` | every NVMe namespace with node, serial, model, usage and firmware |
| `id-ctrl /dev/nvme1n1` | the controller's identify data; on EC2 the handbook greps it for the volume's attachment name |

**What the output tells you** (trimmed; layout varies between nvme-cli versions):

```
critical_warning                    : 0
available_spare                     : 100%
available_spare_threshold           : 10%
percentage_used                     : 41%
data_units_written                  : 61,800,112
media_errors                        : 0
num_err_log_entries                 : 12
```

`critical_warning` not 0: the drive itself flags trouble (spare low, temperature, read-only mode). `percentage_used`: the vendor's estimate of rated endurance used; 100 means rated wear reached, not that the drive stops. `available_spare` near its threshold: replacement blocks are running out. `media_errors` above 0: data the drive could not read or write correctly. `data_units_written` × 512,000 bytes = total written (about 31.6 TB here).

**Why it is effective:** the health log is short and standard, so these fields mean the same on every vendor's drive, and `nvme list` ties device names to serial numbers before you pull a disk.

**Compared with `smartctl`:** `smartctl -a /dev/nvme0` reads the same log and is enough if smartmontools is what you have; nvme-cli adds NVMe-specific commands and JSON output (`-o json`).

**Trap:** EBS volumes on EC2 Nitro appear as NVMe devices, but no physical disk of yours is behind them: rely on AWS status checks. Names can swap between boots: identify drives by serial. `num_err_log_entries` also counts commands the drive merely rejected. Never run `format` or `sanitize` to "check" a drive: both erase it.

**Next step:** `critical_warning`, `media_errors` or low spare → back up and replace. `percentage_used` near 100 → plan the replacement. EC2 volume mapping → `lsblk -o NAME,SERIAL`. Healthy but slow → `iostat -x`.

### mdadm — the state of a software RAID array, and replacing a member
Match: mdadm
Instead of: cat /proc/mdstat alone
Safety: read-only for --detail · changes state: --fail, --remove and --add change the array's members at once; --add starts a rebuild that reads every sector of the surviving disks

**In one line:** `mdadm` manages Linux software RAID (`/dev/md0`): `--detail` shows the array's state, members and any rebuild, and `--fail`, `--remove` and `--add` swap a member out and a new disk in.

**Read the command:** `mdadm --manage /dev/md0 --fail /dev/sdb3 --remove /dev/sdb3`

| Part | Meaning |
|---|---|
| `--manage /dev/md0` | act on this running array (implied when the array comes first: `mdadm /dev/md0 --add …`) |
| `--fail /dev/sdb3` | mark the member faulty, so md stops using it |
| `--remove /dev/sdb3` | take it out of the array; only a failed or spare member can be removed |
| `--add /dev/sdb3` | add a new, partitioned device: md rebuilds onto it |
| `--detail /dev/md0` | full status: state, device counts, rebuild progress, member list |
| `cat /proc/mdstat` | the kernel's short view of every array: `[2/1] [U_]`, recovery % |

**What the output tells you:**

```
             State : clean, degraded, recovering
    Active Devices : 1
   Working Devices : 2
    Failed Devices : 0
    Rebuild Status : 27% complete
    Number   Major   Minor   RaidDevice State
       0       8        3        0      active sync   /dev/sda3
       2       8       19        1      spare rebuilding   /dev/sdb3
```

`degraded`: no full redundancy, so one more failure in RAID1 or RAID5 loses data. `active sync` members are healthy, `spare rebuilding` is the new disk being filled, `faulty` or `removed` slots are the problem. In `/proc/mdstat`, `[2/1] [U_]` reads "2 members expected, 1 up, the second missing".

**Why it is effective:** it says exactly which member failed, whether a rebuild runs and how far it got: what you need to pull the **right** disk and to judge the risk while the array is degraded.

**Compared with `/proc/mdstat`:** mdstat is enough to spot `[U_]` and watch progress, but shows neither member states nor failure counts.

**Trap:** before `--fail`, confirm with `--detail` that every **other** member is `active sync`: failing the last good one stops the array. Identify the physical disk by serial (`ls -l /dev/disk/by-id/`), never by sdX alone. The new disk needs the same partition layout first (`sgdisk -R`, then `-G`). `mdadm --create` over existing members to "repair" an array can destroy its metadata.

**Next step:** member failed → `smartctl -a` on it, then `--fail`, `--remove`, swap, partition, `--add`, `watch cat /proc/mdstat`. OS array → `grub-install` on the new disk too. Rebuild hurting production → lower `dev.raid.speed_limit_max`. Alerts → `MAILADDR` in mdadm.conf.

### fdisk / parted / sgdisk — read or change a disk's partition table
Match: fdisk, parted, sgdisk
Instead of: —
Safety: read-only for `fdisk -l` and `parted -l` · changes state: `fdisk DISK` writes on `w`; `parted` applies **each command immediately**; `sgdisk -R` overwrites the target's table

**In one line:** all three read and write the partition table (GPT, or MBR on old systems) that divides a disk: `fdisk -l` and `parted -l` list it, `fdisk DISK` edits it interactively, `parted -s` and `sgdisk` change it from scripts.

**Read the command:** `parted -s "$LOOP" mklabel gpt mkpart data ext4 1MiB 100%`

| Part | Meaning |
|---|---|
| `-s` | script mode: **no confirmations** |
| `"$LOOP"` | the target disk, here the lab's loop device |
| `mklabel gpt` | write a new, empty GPT table: every existing partition is forgotten |
| `mkpart data ext4 1MiB 100%` | one partition named `data` from 1 MiB (alignment) to the end; `ext4` is only a type hint, no filesystem is made |
| `fdisk -l`, `parted -l` | list every disk's table in sectors, with types (read-only) |
| `fdisk /dev/xvdf` | interactive: `p` print, `n` new, `w` write and quit, `q` quit **without** saving |
| `sgdisk /dev/sda -R /dev/sdb` | copy sda's table **onto** sdb: the disk after `-R` is overwritten |
| `sgdisk -G /dev/sdb` | give sdb and its partitions new random GUIDs after the copy |

**What the output tells you:**

```
Disk /dev/sda: 100 GiB, 107374182400 bytes, 209715200 sectors
Disklabel type: gpt
Device       Start       End   Sectors Size Type
/dev/sda2     4096   4198399   4194304   2G Linux filesystem
/dev/sda3  4198400 104855551 100657152  48G Linux filesystem
```

Partition 3 ends at sector 104855551 of 209715200: about 50 GB after it are unused, the space `growpart` can give to sda3. On an enlarged disk fdisk also warns that the backup GPT table is not at the end: expected, and fixed when the table is next written.

**Why it is effective:** the Start sector is the one number that must never change under existing data; these tools show it exactly, before you grow a partition or replace a RAID member.

**Trap:** fdisk changes nothing until `w`, but parted writes each command at once, and `-s` removes the last prompt: one wrong device name and the old table is gone. Recreating a partition to "grow" it keeps the data only if it starts at **exactly** the same sector; growpart does that for you. On a disk in use, the kernel may keep the old table until `partprobe` or a reboot.

**Next step:** free space after the last partition → `growpart DISK N`. New disk → table, partition, then `mkfs` or `pvcreate`. RAID replacement → `sgdisk -R`, `sgdisk -G`, then `mdadm --add`.

### growpart / resize2fs / xfs_growfs — grow a partition and its filesystem into new space
Match: growpart, resize2fs, xfs_growfs, pvresize
Instead of: deleting and recreating the partition in fdisk
Safety: changes state: moves the partition's end, then grows the filesystem, both online; growing in the right order is safe, shrinking is not (XFS cannot shrink at all)

**In one line:** once the disk itself is bigger, `growpart` moves the end of one partition to the end of the disk without touching its start; then `resize2fs` (ext4, given the device) or `xfs_growfs` (XFS, given the mount point) grows the filesystem into it while it stays mounted.

**Read the command:** `growpart /dev/nvme0n1 1`

| Part | Meaning |
|---|---|
| `/dev/nvme0n1` | the **disk** … |
| `1` | … and the partition **number**, as a separate word (not `/dev/nvme0n1p1`) |
| `--dry-run` (`-N`) | show what would change, change nothing |
| `resize2fs /dev/nvme0n1p1` | grow ext4 to fill its device; works while mounted |
| `xfs_growfs /` | grow the XFS **mounted at /**: it takes a mount point, not a device |
| `pvresize /dev/sda3` | LVM layout: tell LVM the partition grew, then `lvextend -r` |

**What the output tells you:**

```
$ sudo growpart /dev/nvme0n1 1
CHANGED: partition=1 start=227328 old: size=41715679 end=41943007 new: size=209487839 end=209715167
$ sudo resize2fs /dev/nvme0n1p1
Filesystem at /dev/nvme0n1p1 is mounted on /; on-line resizing required
The filesystem on /dev/nvme0n1p1 is now 26185979 (4k) blocks long.
```

`CHANGED` with the same `start` and a larger `size` is the goal. `NOCHANGE: … it cannot be grown` means no free space follows the partition: the disk did not grow, or the guest has not seen it yet. resize2fs answering `Nothing to do!` means the device under it still has the old size.

**Why it is effective:** storage is a stack, and each layer is grown on its own: disk, partition, LVM PV and LV if present, then the filesystem. These commands grow each layer **without unmounting and without moving data**, so the job takes a minute on a live server.

**Compared with deleting and recreating the partition:** fdisk can do the same if the new partition starts at exactly the old sector; one wrong digit and the filesystem is gone. growpart computes the new end and keeps the start.

**Trap:** order matters: growing the filesystem before its device does nothing. On Ubuntu's LVM layout the chain is `growpart` → `pvresize` → `lvextend -r`, and resize2fs on the partition fails, because it holds an LVM PV, not a filesystem. XFS never shrinks; ext4 shrinks only unmounted. growpart can only use free space directly after the partition.

**Next step:** guest still sees the old disk size → `echo 1 | sudo tee /sys/class/block/sda/device/rescan`, or reboot. LVM → `pvresize`, then `lvextend -r -l +100%FREE`. Done → confirm with `df -h`.

### pvs / vgs / lvs — how the LVM stack is built, and where free space is waiting
Match: pvs, vgs, lvs, pvdisplay, vgdisplay, lvdisplay
Instead of: df -h, lsblk
Safety: read-only · run as root, or the tools print warnings instead of data

**In one line:** LVM pools disks or partitions (physical volumes, **PV**) into a volume group (**VG**) and carves logical volumes (**LV**) out of it, each holding a filesystem; `pvs`, `vgs` and `lvs` print one line per PV, VG and LV.

**Read the command:** `pvs -o +pv_used`

| Part | Meaning |
|---|---|
| `pvs` | each PV: its VG, format, attributes, size (PSize) and unallocated space (PFree) |
| `-o +pv_used` | add a column (`+` keeps the defaults): space already given to LVs |
| `vgs` | each VG: number of PVs, LVs and snapshots, VSize and **VFree** (unallocated) |
| `lvs` | each LV: VG, attributes, LSize, and snapshot or thin-pool usage when relevant |
| `pvdisplay`, `vgdisplay`, `lvdisplay` | the same in long form: extent size, Free PE, LV Path, LV Status |

**What the output tells you:**

```
$ sudo pvs -o +pv_used; sudo vgs; sudo lvs
  PV         VG        Fmt  Attr PSize   PFree  Used
  /dev/sda3  ubuntu-vg lvm2 a--  <98.00g 48.00g 50.00g
  VG        #PV #LV #SN Attr   VSize   VFree
  ubuntu-vg   1   1   0 wz--n- <98.00g 48.00g
  LV        VG        Attr       LSize  Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  ubuntu-lv ubuntu-vg -wi-ao---- 50.00g
```

48 GB of the VG are unallocated, so `/` can grow online right now; the Ubuntu Server installer leaves part of the VG free on purpose. `<98.00g` means slightly less than shown. In the LV attributes `a` = active, `o` = open (mounted). The LV is `/dev/ubuntu-vg/ubuntu-lv`, also `/dev/mapper/ubuntu--vg-ubuntu--lv` (dashes doubled), the name df prints.

**Why it is effective:** VFree answers "can I grow this without touching the disk?" in one line, and PFree after a disk resize shows whether `pvresize` is still missing.

**Compared with `df -h` / `lsblk`:** df shows a full filesystem on `/dev/mapper/…` and nothing about free extents; lsblk shows the tree (disk → PV → LV) but not the unallocated space in the VG.

**Trap:** VFree 0 although the disk grew means the partition or the PV was not grown (`growpart`, `pvresize`). A VG spread over two disks with plain linear LVs has no redundancy: losing either disk can take the LVs on it down. `#SN` above 0 means snapshots, and a classic (thick) snapshot that fills up becomes invalid.

**Next step:** VFree above 0 → `lvextend -r -l +100%FREE VG/LV`. VFree 0, disk bigger → `growpart`, then `pvresize`. No space anywhere → add a disk with `pvcreate` and `vgextend`.

### pvcreate / vgextend / lvextend — add a disk to LVM and grow a volume online
Match: pvcreate, vgextend, lvextend, vgcreate, lvcreate
Instead of: a new disk mounted at a second path
Safety: changes state: pvcreate writes LVM metadata onto the device (and offers to wipe old signatures); lvextend grows the LV and, with -r, its filesystem, online

**In one line:** `pvcreate` makes a disk or partition an LVM physical volume, `vgextend` adds it to a volume group, and `lvextend` gives a logical volume more of the group's free space; `-r` grows the filesystem in the same step.

**Read the command:** `lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv`

| Part | Meaning |
|---|---|
| `-r` | `--resizefs`: also grow the filesystem on the LV (ext4 or XFS) |
| `-l +100%FREE` | add all free extents of the VG (`-l` counts extents or percentages) |
| `-L +50G` | the alternative: add exactly 50 GiB |
| `/dev/ubuntu-vg/ubuntu-lv` | the LV to grow (`ubuntu-vg/ubuntu-lv` works too) |
| `pvcreate /dev/sdc` | initialise a new, empty disk as a PV |
| `vgextend vgdata /dev/sdc` | add that PV's space to the VG `vgdata` |

**What the output tells you:**

```
  Size of logical volume ubuntu-vg/ubuntu-lv changed from 50.00 GiB (12800 extents) to <98.00 GiB (25087 extents).
  Logical volume ubuntu-vg/ubuntu-lv successfully resized.
```

These two lines are LVM's; extents are its allocation unit, 4 MiB by default. With `-r`, the filesystem tool's messages follow (resize2fs: `… is now 25689088 (4k) blocks long`); without it, df keeps showing the old size although the LV grew.

**Why it is effective:** it is the no-downtime way to give `/`, `/var/lib/docker` or a database more room: no unmount, no data copy, seconds of work. Keeping /var/lib/docker on its own LV also means a runaway build fills that LV, not `/`.

**Compared with a new disk mounted at a second path:** that adds space somewhere else, so the full directory stays full until you move data and change paths; LVM grows the same path.

**Trap:** without `-r` only the LV grows (fix: `resize2fs DEVICE` or `xfs_growfs MOUNTPOINT`). `pvcreate` on the wrong device destroys what is on it: check `lsblk -f` first, and answer **no** when it offers to wipe a signature you did not expect. A VG over two disks without RAID means one dead disk takes down the LVs on it. Never `lvreduce` before shrinking the filesystem; XFS cannot shrink at all.

**Next step:** confirm with `df -h` and `lvs`. No free space in the VG → `pvcreate` and `vgextend` a new disk, or `growpart` and `pvresize` after enlarging the current one. Keep some VFree for a snapshot before risky upgrades (`lvcreate -s`). Building LVM from scratch: `vgcreate VG PV…` makes the group and `lvcreate -n NAME -L SIZE VG` a volume; both change state.

### fsck / xfs_repair — check and repair an unmounted filesystem
Match: fsck, fsck.ext4, e2fsck, xfs_repair, xfs_db
Instead of: mount -o remount,rw and carrying on
Safety: changes state: a repair rewrites metadata and may move files to lost+found; `-n` only reads · never on a mounted read-write filesystem

**In one line:** `fsck` (for ext4 the program `e2fsck`, also installed as `fsck.ext4`) and `xfs_repair` check a filesystem's metadata (inodes, block maps, directories, free-space counts) and repair what is inconsistent, on an **unmounted** device.

**Read the command:** `fsck.ext4 -f /dev/vg_data/lv_data`

| Part | Meaning |
|---|---|
| `fsck.ext4` | the ext4 checker, the same program as `e2fsck` |
| `-f` | force a full check even when the filesystem is marked clean |
| `/dev/vg_data/lv_data` | the device, not the mount point; unmount it first |
| `fsck -n /dev/xvdb1` | the generic front end; `-n` opens read-only and answers "no" to every fix: a dry run |
| `fsck -y /dev/xvdb1` | answer "yes" to every fix: unattended repair |
| `xfs_repair -n /dev/xvdb1`, `xfs_repair /dev/xvdb1` | XFS: check only, change nothing / repair (unmounted) |

**What the output tells you:**

```
Pass 1: Checking inodes, blocks, and sizes
Pass 2: Checking directory structure
Pass 3: Checking directory connectivity
Pass 4: Checking reference counts
Pass 5: Checking group summary information
/dev/vg_data/lv_data: 41237/6553600 files (0.4% non-contiguous), 8921453/26214400 blocks
```

Problems appear as questions and answers between the passes; the last line gives inodes and blocks in use. The exit code sums up: 0 clean, 1 errors fixed, 2 fixed and a reboot needed (root filesystem), 4 errors left uncorrected, 8 operational error.

**Why it is effective:** after an unclean shutdown, a storage hiccup or a read-only remount, it is the only way to make the metadata consistent again, and the dry run (`-n`) shows how bad it is before anything changes.

**Compared with remounting read-write and carrying on:** `mount -o remount,rw` stops the errors for a while, but you keep writing onto a filesystem the kernel already found damaged, which spreads the damage.

**Trap:** a repair on a mounted read-write filesystem corrupts it: unmount, or check the root filesystem from rescue mode. `fsck` on XFS checks nothing (`fsck.xfs` just exits successfully, because XFS replays its log at mount): use `xfs_repair`. If xfs_repair says the log needs replaying, mount and unmount once first; `-L` (zero the log) discards the latest metadata changes and is the last resort. `-y` accepts every fix, including moving files to lost+found.

**Next step:** errors with `-n` → snapshot or back up if you can, then repair. Errors that come back → `smartctl`, `dmesg` I/O errors, the hypervisor's storage: fix the cause first. Repaired → `tune2fs -l` (`Filesystem state: clean`), mount, look in `lost+found`. XFS fragmentation, read-only: `xfs_db -r -c frag /dev/sdb1` (it only reports; nothing is changed).

### tune2fs / mkfs.ext4 — read or change ext4's settings, or create a filesystem
Match: tune2fs, dumpe2fs, mkfs.ext4, mkfs.xfs, e4defrag
Instead of: reformatting to change a setting
Safety: read-only for `tune2fs -l` and `dumpe2fs -h` · changes state: `tune2fs -m` and other setters change the live superblock · `mkfs.*` **destroys everything** on the device

**In one line:** `tune2fs -l` prints an ext4 filesystem's superblock (state, error behaviour, inode and block counts, the root reserve), `tune2fs -m` changes the reserve, and `mkfs.ext4` creates a filesystem, fixing its inode count for good.

**Read the command:** `tune2fs -l /dev/mapper/ubuntu--vg-ubuntu--lv | grep -E 'Inode count|Reserved block count|Block count|Filesystem state'`

| Part | Meaning |
|---|---|
| `-l` | list the superblock contents; changes nothing |
| `/dev/mapper/ubuntu--vg-ubuntu--lv` | the device, here Ubuntu's root LV |
| `| grep -E '…'` | keep only the lines that matter here |
| `-m 1` | **changes state**: set the root-only reserve to 1% (default 5%) |
| `mkfs.ext4 -L labdata DEV` | create ext4 with a label (**wipes DEV**) |
| `mkfs.ext4 -F -N 2000 …` | `-F` skip the safety questions; `-N` about this many inodes (rounded up): the lab's tiny count |
| `dumpe2fs -h DEV` | the same superblock view as `tune2fs -l` |
| `mkfs.xfs -f DEV` | XFS: `-f` overwrites an existing filesystem |

**What the output tells you:**

```
Filesystem state:         clean
Inode count:              3276800
Block count:              13106176
Reserved block count:     655308
```

655,308 reserved blocks × 4 KiB ≈ 2.5 GiB that only root may use: why df's Avail is smaller than Size minus Used, and why root services keep writing after normal users get "No space left". The inode count (one per 16 KiB here) was fixed at mkfs time. In the full listing, `clean with errors` and `FS Error count` show whether the kernel has already found damage.

**Why it is effective:** the superblock answers what df cannot: how many inodes this filesystem will ever have, how much is held back for root, and whether ext4 has recorded errors.

**Compared with reformatting:** mkfs is the only way to get more inodes (`-N`, or a smaller bytes-per-inode ratio with `-i`), and it destroys the data; the reserve and the label change in place with tune2fs.

**Trap:** lowering the reserve on `/` buys space but removes root's emergency room; it is fine on big data disks. With `-F`, mkfs on the wrong device is instant and silent: check `lsblk -f` and `wipefs -n DEV` first. A new filesystem has a new UUID: update fstab. XFS has no tune2fs: read its settings with `xfs_info MOUNTPOINT`.

**Next step:** inodes exhausted → delete the small files (`du --inodes`), or rebuild with `mkfs.ext4 -i 8192` or XFS. Errors recorded → plan `fsck.ext4 -f` from rescue. New filesystem → `blkid`, fstab, `findmnt --verify`, `mount -a`. ext4 fragmentation: `e4defrag -c /path` only reports a score; without `-c` it defragments.

### losetup — turn an image file into a disk for safe practice
Match: losetup
Instead of: practising on a real disk
Safety: changes state: creates or removes /dev/loopN devices (needs root); whatever you then write lands in the image file

**In one line:** `losetup` attaches a regular file to a loop device such as `/dev/loop7`, which the kernel then treats like a disk: partition it, format it, mount it, build LVM on it, and delete the file afterwards.

**Read the command:** `losetup --find --show --partscan /var/tmp/lab-disk.img`

| Part | Meaning |
|---|---|
| `--find` (`-f`) | use the first unused loop device |
| `--show` | print the device it picked, so `LOOP=$(…)` can capture it |
| `--partscan` (`-P`) | let the kernel see partitions inside the image (`/dev/loop7p1`) |
| `/var/tmp/lab-disk.img` | the backing file, here a sparse 2 GiB file from `truncate -s 2G` |
| `-d "$LOOP"`, `-l` | detach the device (unmount first) / list loop devices and their files |

**What the output tells you:**

```
$ LOOP=$(sudo losetup --find --show --partscan /var/tmp/lab-disk.img); echo "$LOOP"
/dev/loop7
$ losetup -l
NAME       SIZELIMIT OFFSET AUTOCLEAR RO BACK-FILE                              DIO LOG-SEC
/dev/loop7         0      0         0  0 /var/tmp/lab-disk.img                    0     512
/dev/loop3         0      0         1  1 /var/lib/snapd/snaps/core22_1380.snap    0     512
```

`/dev/loop7` is the lab disk. The read-only (`RO 1`) entries on Ubuntu are snap packages, each a squashfs image on its own loop device, which is why the handbook filters `-x squashfs`.

**Why it is effective:** partitioning, mkfs, LVM, fstab and disk-full drills destroy data on real disks; on a loop device a mistake costs one file, and the commands are exactly the ones you will type on a server.

**Trap:** loop devices do not survive a reboot, so an fstab line for one fails at the next boot (the lab adds `nofail`). Deleting the image while it is attached frees nothing: the loop device holds it open, the deleted-but-open effect again. Use the name `--show` printed, never a guessed `/dev/loopN`.

**Next step:** partition → `parted -s "$LOOP" mklabel gpt …`. Format → `mkfs.ext4 "${LOOP}p1"`. LVM lab → `pvcreate` on two loop devices. Clean up → `umount`, `losetup -d "$LOOP"`, then remove the image.

### swapon / swapoff / mkswap — which swap is active, and how to add or remove it
Match: swapon, swapoff, mkswap
Instead of: free -h
Safety: read-only for `swapon --show` · changes state: mkswap overwrites its target; swapon and swapoff act at once and last until reboot; swapoff on a box short of RAM can start the OOM killer

**In one line:** `swapon --show` lists the active swap areas with size, use and priority; `mkswap` formats a file or partition as swap, `swapon` enables it, and `swapoff` moves its pages back into RAM and disables it.

**Read the command:** `fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile`

| Part | Meaning |
|---|---|
| `fallocate -l 2G /swapfile` | reserve 2 GiB of real blocks for the file |
| `chmod 600` | root only: swap holds copies of memory, passwords and keys included |
| `mkswap /swapfile` | write the swap signature into the file |
| `swapon /swapfile` | start using it now |
| `&&` | each step runs only if the previous one succeeded |
| `swapon --show` | NAME, TYPE, SIZE, USED and PRIO of every active area |
| `swapoff -a` | disable all swap: the Kubernetes node requirement |

**What the output tells you:**

```
$ swapon --show
NAME       TYPE  SIZE   USED PRIO
/swap.img  file    4G 420.5M   -2
/swapfile  file    2G     0B   -3
```

Some USED with no ongoing swapping (`si` and `so` near 0 in `vmstat 1`) is harmless: idle pages were moved out. Constant swapping in and out is the problem, not the size of USED. The area with the higher PRIO is used first.

**Why it is effective:** "is swap why this box is slow, and is there any?" needs both facts, how much exists and how much is in use, next to `free -h` and `vmstat`. A small swap file is quick relief for a build host whose RAM spikes, and `swapoff -a` is the first fix for kubeadm's swap preflight check.

**Compared with `free -h`:** free shows total and used swap, enough for a glance, not which file holds it or its priority.

**Trap:** all of it lasts only until reboot: add `/swapfile none swap sw 0 0` to fstab to keep it, and comment out the swap line to keep it off, or kubelet fails again after the next boot. swapon only warns about wrong permissions (`insecure permissions 0644, 0600 suggested`) and activates the file anyway. `swapoff` must bring every swapped page back into RAM: slow, and OOM-prone when RAM is short.

**Next step:** constant swapping → `vmstat 1` (si, so), find the memory user (`ps aux --sort=-rss | head`), fix the leak or add RAM. Kubernetes node → `swapoff -a`, fstab, `journalctl -u kubelet`. swapon rejects the file → dmesg, then recreate it with dd.

### sync / fincore — flush dirty data to disk, and see what the page cache holds
Match: sync, fincore
Instead of: echo 3 > /proc/sys/vm/drop_caches to "free memory"
Safety: sync is safe but can take minutes, and it hangs while an NFS server holding dirty data is unreachable · fincore is read-only

**In one line:** `sync` makes the kernel write every dirty page (changed in RAM, not yet on disk) and pending metadata, and returns when that is done; `fincore` shows how much of a file sits in the page cache right now (read at RAM speed).

**Read the command:** `sync; echo 1 | sudo tee /proc/sys/vm/drop_caches >/dev/null`

| Part | Meaning |
|---|---|
| `sync` | flush the dirty pages of all filesystems, then return |
| `echo 1 | sudo tee /proc/sys/vm/drop_caches` | then drop **clean** page-cache pages (2 = dentries and inodes, 3 = both); `tee` because in `sudo echo 1 > FILE` the redirect runs without root |
| `>/dev/null` | hide tee's echo of the "1" |
| `fincore /var/lib/mysql/ibdata1` | RES (bytes cached), PAGES, SIZE and FILE for one file |
| `sync -f /data` | flush only the filesystem that holds /data |

**What the output tells you:** sync prints nothing (`Dirty:` and `Writeback:` in `/proc/meminfo` drain while it runs).

```
$ sudo fincore /var/lib/mysql/ibdata1
   RES  PAGES   SIZE FILE
  1.2G 314572   1.5G /var/lib/mysql/ibdata1
```

1.2 GB of this 1.5 GB file is cached (314,572 pages of 4 KiB): reads of it never touch the disk. After `drop_caches` RES falls toward 0 and the next reads come from disk.

**Why it is effective:** writes normally return once they reach the page cache; sync is when they are really on disk. That matters before a forced reboot (the handbook's `init=/bin/bash` recovery has no clean shutdown), before pulling a disk, and before `drop_caches`, which drops only pages already written. fincore puts a number, per file, on "the cache is doing its job".

**Compared with dropping caches to free memory:** drop_caches makes `free` look better, but cache is reclaimed on demand anyway; on a production database it causes a burst of disk reads and slow queries while the cache refills. Keep it for test VMs.

**Trap:** after a large write, sync waits for gigabytes of dirty data, and on a dead NFS mount it hangs; `sync -f PATH` limits it to one filesystem. Application durability comes from its own fsync calls, not from your sync. fincore sees only the page cache, not a database's own buffer pool.

**Next step:** Dirty stays high and writes stall → `iostat -x` (the device cannot keep up), then `vm.dirty_ratio`. Benchmark too good to be true → fincore on the test file, rerun with `--direct=1`.

### lsattr / chattr — why even root gets "Operation not permitted"
Match: lsattr, chattr
Instead of: ls -l, chmod
Safety: lsattr is read-only · chattr changes state: `+i` makes a file unchangeable for everyone, root included, until `-i`

**In one line:** `lsattr` lists the attribute flags a filesystem keeps for each file, and `chattr` sets them; the ones that matter in incidents are `i` (immutable: no write, delete, rename or link) and `a` (append only).

**Read the command:** `chattr +i /srv/site/index.html`

| Part | Meaning |
|---|---|
| `+i` | set the immutable flag (`-i` clears it, `=` sets exactly the listed flags) |
| `/srv/site/index.html` | the file; on a directory, nothing inside can be created, removed or renamed |
| `+a` | append only: data can be added, not overwritten or deleted |
| `lsattr FILE` | show the flags; `-d DIR` shows a directory's own flags instead of its contents |

**What the output tells you:**

```
$ sudo rm /srv/site/index.html
rm: cannot remove '/srv/site/index.html': Operation not permitted
$ lsattr /srv/site/index.html
----i---------e------- /srv/site/index.html
```

Each position is one flag: `i` is set, and `e` (extents) is normal on ext4. Root got "Operation not permitted", not "Permission denied": the hint that a flag or a security layer, not the mode bits, is in the way.

**Why it is effective:** mode bits, owner and sudo all look right and the change still fails: only lsattr shows this layer. Classic cases: `/etc/resolv.conf` replaced by a file and pinned with `+i`, so DNS changes never apply; a deploy that cannot overwrite a web file.

**Compared with `ls -l` / `chmod`:** ls -l shows owner, group and mode but no attributes, and chmod cannot override `i`.

**Trap:** only root (with CAP_LINUX_IMMUTABLE) can set or clear `i` and `a`, so someone set it on purpose, a hardening script or an intruder: find out why before clearing it. lsattr reads only regular files and directories: on a symlink such as Ubuntu's default `/etc/resolv.conf` it reports "Operation not supported", so check the file the link points to. Copies and restores usually drop the flags.

**Next step:** an unexpected flag → find who set it, then `chattr -i` and fix the real configuration (netplan or systemd-resolved for DNS). Still denied without flags → `getfacl`, `findmnt -no OPTIONS -T PATH` (`ro`, `noexec`), then AppArmor or SELinux.

### exportfs / nfsstat — what the NFS server exports, and how the client really mounted it
Match: exportfs, nfsstat, showmount
Instead of: cat /etc/exports, showmount -e
Safety: read-only for `exportfs -v` and `nfsstat` · changes state: `exportfs -ra` applies the exports files at once, and clients of a removed export start getting errors

**In one line:** on the server, `exportfs -v` lists what the kernel exports right now, with every option filled in, and `exportfs -ra` applies the exports files; on the client, `nfsstat -m` shows each NFS mount's negotiated options and `nfsstat -c` the RPC counters.

**Read the command:** `nfsstat -m`

| Part | Meaning |
|---|---|
| `nfsstat -m` | every NFS mount on this client with its effective options: `vers`, `rsize`/`wsize`, `hard`/`soft`, `timeo`, `retrans`, `proto` |
| `nfsstat -c` | client counters since boot: RPC `calls`, and `retrans` (calls re-sent after a timeout) |
| `exportfs -v` | server: each export, the clients allowed and all options in effect |
| `exportfs -ra` | server: re-export everything in /etc/exports and /etc/exports.d, drop what was removed |

**What the output tells you:**

```
$ nfsstat -m
/mnt/share from 192.0.2.40:/export/app
 Flags: rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,namlen=255,hard,proto=tcp,timeo=600,retrans=2,sec=sys,clientaddr=192.0.2.15,local_lock=none,addr=192.0.2.40
$ sudo exportfs -v
/export/app   192.0.2.0/24(sync,wdelay,hide,no_subtree_check,sec=sys,rw,secure,root_squash,no_all_squash)
```

`hard` with `timeo=600` (tenths of a second: 60 s) and `retrans=2`: when the server goes silent, processes wait in state D until it returns. `vers=4.2` and 1 MiB rsize/wsize are what both sides agreed, which can differ from fstab. On the server, `root_squash` maps the client's root to an anonymous user, so "Permission denied" for root on the client is expected.

**Why it is effective:** NFS trouble is more often options than network: an unexpected `soft`, an old `vers=3`, a small wsize, a client subnet missing from the export. These commands show what both ends actually use.

**Compared with `cat /etc/exports` / `showmount -e`:** the file shows what was written, not what is exported (an edit without `exportfs -ra` changes nothing); `showmount -e` lists exports without options, and NFSv4-only servers may not answer it.

**Trap:** `nfsstat -c` counts since boot: compare two readings taken while the problem happens; rising `retrans` means a slow server or lost packets. `exportfs -ra` after deleting or recreating an export hits clients at once (a recreated directory gives them "Stale file handle"); `fsid=` on each export keeps handles stable across restores and failovers.

**Next step:** client options wrong → fix fstab, then unmount and mount (not remount). Hangs → `findmnt -t nfs4`, dmesg "not responding", `nc -zv SERVER 2049`. Stale handles → remount the client. Slow transfers → `iperf3` between the hosts, then `iostat -x` on the server. From a client, `showmount -e SERVER` lists what an NFSv3 server exports (NFSv4-only servers may not answer it).

### zfs — where ZFS space went: datasets, snapshots, quotas and reservations
Match: zfs, zpool
Instead of: df -h, du on a ZFS dataset
Safety: read-only for `zfs list` and `zpool status` · changes state: `zfs destroy` deletes a snapshot or dataset with no undo; `zfs set` and `zfs create` change limits at once

**In one line:** `zfs list` shows each dataset's space the ZFS way (used, available, the part held only by snapshots, quota, reservation), and `zfs destroy`, `set` and `create` free space or set the limits that keep a pool from filling up.

**Read the command:** `zfs list -o name,used,avail,usedbysnapshots backup/store1`

| Part | Meaning |
|---|---|
| `-o name,used,avail,usedbysnapshots` | columns: total used (snapshots and children included), available, the part snapshots hold |
| `backup/store1` | pool `backup`, dataset `store1` (no name: every dataset) |
| `list -t snapshot -o name,used -s used` | the snapshots, sorted by the space each one holds **alone** |
| `destroy backup/store1@SNAP` | **changes state**: delete one snapshot; `destroy -nv` first shows what would be freed |
| `set quota=3.2T backup/store1` | **changes state**: cap the dataset, snapshots and children included |
| `create -o reservation=100G backup/headroom` | **changes state**: an empty dataset holding back 100 GB as emergency space |
| `zpool status -x`, `zpool list` | pool health ("all pools are healthy") / pool size, allocation, fragmentation |

**What the output tells you:**

```
$ zfs list -o name,used,avail,usedbysnapshots backup/store1
NAME            USED  AVAIL  USEDSNAP
backup/store1  3.60T  1.90G      612G
$ zfs list -t snapshot -o name,used -s used backup/store1 | tail -2
backup/store1@autosnap_2026-09-01_00:00:01_monthly   143G
backup/store1@autosnap_2026-08-01_00:00:02_monthly   201G
```

612 GB of the full dataset are held only by snapshots (a snapshot tool's monthly ones, on a Proxmox Backup Server datastore). Deleting files frees nothing while snapshots still reference them.

**Why it is effective:** on ZFS, snapshots, child datasets, reservations and quotas all take space that `du` cannot see; these columns show which one it is before you delete anything.

**Compared with `df -h` / `du`:** df's Used on a dataset is only what the live dataset references, and its Size is that plus available, so it shrinks as the pool fills; du counts only live files. Neither shows snapshots.

**Trap:** a snapshot's USED is only what it holds **alone**: blocks shared by two snapshots appear in neither, so destroying several can free more than their sum; `zfs destroy -nv` tells you first. Without `@`, destroy targets the dataset itself. A full pool can fail even to delete, because copy-on-write needs free space: that is what the reserved dataset is for (`zfs set reservation=none backup/headroom` in a crisis).

**Next step:** snapshots hold the space → fix the snapshot policy, then destroy old ones. Pool nearly full → quotas per dataset, more disks, and stay below about 80%. Pool health → `zpool status -x`.

### ceph — is the cluster healthy, and which OSD will fill up first?
Match: ceph
Instead of: the Proxmox GUI health badge
Safety: read-only for `-s`, `-w`, `osd df`, `osd pool ls detail` and `balancer status` · changes state: `osd set/unset noout` changes how the cluster reacts to failures; `reweight-by-utilization` moves data between OSDs

**In one line:** `ceph -s` prints the cluster's health, its daemons and the state of its placement groups (PGs); `ceph osd df` shows how full each OSD (one per disk) is, which is where the real capacity limit lies.

**Read the command:** `ceph osd df`

| Part | Meaning |
|---|---|
| `osd df` | per OSD: size, raw use, `%USE`, `VAR` (use relative to the average), PG count, status |
| `-s`, `-w` | health, monitors, OSDs up and in, usage, PG states / the same, then follow the cluster log |
| `osd pool ls detail` | each pool's replica `size` and `min_size`, PG count and rule |
| `osd set noout`, `osd unset noout` | **changes state**: down OSDs are not marked out, so nothing re-replicates during planned maintenance |
| `balancer status` | whether the automatic balancer is on, and its mode |
| `osd reweight-by-utilization 110` | **changes state**: lower the weight of OSDs above 110% of the average fill, which moves data |

**What the output tells you** (columns trimmed):

```
ID  CLASS  SIZE     RAW USE  AVAIL    %USE   VAR   PGS  STATUS
 0    ssd  476 GiB  410 GiB   66 GiB  86.13  1.15   68      up
 1    ssd  476 GiB  331 GiB  145 GiB  69.54  0.93   61      up
```

osd.0 is at 86% while the average is about 75% (`VAR 1.15`): it passes `nearfull` (85% by default) first, recovery stops writing to it at `backfillfull` (90%), and at `full` (95%) the cluster stops accepting writes, long before the pool looks full. In `ceph -s`, `undersized+degraded` PGs have fewer copies than `size` but still serve; below `min_size` they block I/O, and VMs freeze.

**Why it is effective:** HEALTH_WARN covers anything from "one OSD is rebooting" to "writes are about to stop"; these commands say which, and name the OSD that limits your capacity.

**Compared with the GUI badge:** the Proxmox panel shows the same health text and a usage bar, enough to notice a warning, but not per-OSD and per-PG detail.

**Trap:** forgetting `unset noout` after maintenance means a disk that really fails later is never re-replicated. `reweight-by-utilization` starts data movement: `ceph osd test-reweight-by-utilization 110` shows the plan first. Never lower `min_size` to 1 to get I/O back: writes would then exist in one place only.

**Next step:** OSD down → `systemctl status ceph-osd@ID`, its disk (`smartctl`), then `ceph -w` until HEALTH_OK. Nearfull → balance, delete data or add OSDs before 80%. Slow or blocked I/O → the network between nodes and the OSDs' disks (`iostat -x`).
