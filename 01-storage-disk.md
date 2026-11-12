# 01 — Storage & Disk Troubleshooting

Typical symptoms: "No space left on device", app can't write files, slow I/O,
read-only filesystem, disk not visible.

---

## 1. Disk space usage

### `df` — filesystem free space
Shows mounted filesystems and how full they are. **First command for any "disk full" issue.**

```bash
df -h                 # human-readable sizes
df -h /var/log        # only the filesystem containing this path
df -T                 # include filesystem type (ext4/xfs/nfs...)
df -i                 # INODE usage — disk can be "full" with free space!
```

Example:
```
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       50G   48G  2.0G  97% /
/dev/xvdb1      100G   20G   80G  20% /data
tmpfs           7.8G     0  7.8G   0% /dev/shm
```
→ Root is at 97%: find what's eating it with `du` (below).

**Gotcha — "No space left on device" but `df -h` shows space:** run `df -i`.
Millions of tiny files (mail spools, PHP sessions, cache dirs) can exhaust inodes:
```
$ df -i
Filesystem      Inodes  IUsed  IFree IUse% Mounted on
/dev/xvda1     3276800 3276800     0  100% /
```

### `du` — directory space usage
Answers "*what* is filling the disk".

```bash
du -sh /var/*                          # size of each dir under /var
du -sh /var/log                        # total size of one dir
du -ah /var/log | sort -rh | head -20  # 20 biggest files/dirs under /var/log
du -xh --max-depth=1 / | sort -rh      # top-level usage, -x = don't cross filesystems
```

Example:
```
$ du -sh /var/* 2>/dev/null | sort -rh | head -5
35G   /var/log
8.2G  /var/lib
1.1G  /var/cache
```

### `ncdu` — interactive du (if installed)
```bash
ncdu /            # browse disk usage with arrow keys, delete with 'd'
ncdu -x /         # stay on one filesystem
```

### Deleted-but-open files (classic trap)
`du` doesn't match `df` because a process holds a **deleted** log file open —
space isn't freed until the process closes it.

```bash
lsof +L1                       # list open files with link count 0 (deleted)
lsof | grep deleted            # alternative
```
Example:
```
$ lsof +L1
COMMAND  PID USER  FD  TYPE DEVICE SIZE/OFF NLINK NODE NAME
java    2134 app   4w  REG  202,1  21474836480  0  131 /var/log/app.log (deleted)
```
Fix: restart/reload the process (`systemctl restart app`), or truncate via
`> /proc/2134/fd/4`. **Never `rm` an active log — `truncate -s 0 file` instead.**

### Finding big/old files fast
```bash
find / -xdev -type f -size +1G                      # files over 1 GB
find /var/log -type f -mtime +30 -name "*.gz"       # compressed logs older than 30 days
find /tmp -type f -atime +7 -delete                 # (careful) purge old tmp files
truncate -s 0 /var/log/huge.log                     # empty a file safely, keeps fd valid
```

---

## 2. Block devices & partitions

### `lsblk` — list block devices (disks, partitions, LVM, RAID)
**First command when a disk "isn't showing up".**

```bash
lsblk                          # tree of disks → partitions → mounts
lsblk -f                       # + filesystem type, LABEL, UUID
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL
```
Example:
```
$ lsblk
NAME    MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
xvda    202:0    0   50G  0 disk
└─xvda1 202:1    0   50G  0 part /
xvdf    202:80   0  500G  0 disk            ← attached but NOT partitioned/mounted
```

### `blkid` — UUIDs and filesystem types
```bash
blkid                          # UUID + TYPE of every formatted device
blkid /dev/xvdf1
```
Use UUIDs in `/etc/fstab` — device names (`/dev/sdX`) can change across reboots,
especially on AWS (NVMe renaming).

### `fdisk` / `parted` — partition tables
```bash
fdisk -l                       # list all disks and partition tables (read-only)
parted -l                      # same, also shows GPT labels
fdisk /dev/xvdf                # INTERACTIVE — modifies partition table, be careful
```

### `mount` / `findmnt` / `umount`
```bash
findmnt                        # tree of all mounts (nicer than plain `mount`)
findmnt /data                  # details of a single mountpoint
findmnt --verify               # sanity-check /etc/fstab (catch typos BEFORE reboot!)
mount | grep nfs               # show NFS mounts
mount -o remount,rw /          # remount read-only root as read-write
mount /dev/xvdf1 /data         # manual mount
umount /data                   # unmount; fails with "target is busy" if in use
```

**"umount: target is busy"** — find who's using it:
```bash
lsof +f -- /data               # processes with open files on the mount
fuser -vm /data                # same idea
fuser -km /data                # kill them (destructive — last resort)
```

**Read-only filesystem errors** — kernel remounts ro after disk errors:
```bash
dmesg -T | grep -iE "error|ext4|xfs|i/o"
mount | grep " / "             # look for (ro,...)
```
On AWS this often means the EBS volume had an issue → check volume status; on-prem
check RAID/SMART. After fixing, `fsck` then remount.

### Growing a filesystem (very common on AWS after EBS resize)
```bash
growpart /dev/xvda 1           # grow partition 1 to fill the disk
resize2fs /dev/xvda1           # ext4: grow filesystem (online)
xfs_growfs /                   # xfs: grow by MOUNTPOINT (online)
lsblk                          # verify new size
```

---

## 3. Disk performance / I/O

### `iostat` — per-device I/O stats (package: sysstat)
```bash
iostat -xz 1                   # extended stats, 1s interval, skip idle devices
```
Example:
```
Device   r/s   w/s   rkB/s   wkB/s  await  %util
xvda    05.0  210.0   20.0  8400.0  35.20  99.6
```
Key columns:

- `%util` ~100% → device saturated
- `await` (ms) → avg latency; >20ms on SSD/EBS gp3 is bad
- `avgqu-sz`/`aqu-sz` → queue depth; sustained >1 per disk = backlog

### `iotop` — which PROCESS is doing the I/O (needs root)
```bash
iotop -oPa                     # only active processes, accumulated totals
```

### `pidstat -d` — per-process disk I/O (sysstat)
```bash
pidstat -d 1                   # kB read/written per process per second
```

### `vmstat` — check `wa` (I/O wait)
```bash
vmstat 1 5
```
High `wa` column = CPUs idle waiting on disk → storage is the bottleneck.

### Quick throughput sanity tests (test volumes only — writes data!)
```bash
dd if=/dev/zero of=/data/testfile bs=1M count=1024 oflag=direct   # write test
dd if=/data/testfile of=/dev/null bs=1M iflag=direct              # read test
fio --name=randread --rw=randread --bs=4k --size=1G --numjobs=4 --runtime=30 --group_reporting
hdparm -tT /dev/sda            # simple read benchmark (on-prem)
```
On AWS: if throughput tops out suspiciously flat, you're hitting **EBS IOPS/
throughput limits or EC2 instance EBS bandwidth limits** — check CloudWatch
`VolumeQueueLength`, and whether burst credits (gp2/st1) are exhausted.

---

## 4. Filesystem integrity

### `fsck` — check/repair ext filesystems (**unmounted only!**)
```bash
fsck -n /dev/xvdb1             # dry-run, report only
fsck -y /dev/xvdb1             # auto-fix (unmount first!)
```
Never run fsck on a mounted rw filesystem — you will corrupt it.

### XFS equivalents
```bash
xfs_repair -n /dev/xvdb1       # dry-run
xfs_repair /dev/xvdb1          # repair (unmounted)
```

### `tune2fs` — ext filesystem parameters
```bash
tune2fs -l /dev/xvda1          # show superblock info (mount count, reserved blocks)
tune2fs -m 1 /dev/xvda1        # reduce root-reserved space 5%→1% (reclaims space)
```

---

## 5. LVM (Logical Volume Manager)

```bash
pvs ; pvdisplay                # physical volumes (disks in LVM)
vgs ; vgdisplay                # volume groups (pools)
lvs ; lvdisplay                # logical volumes (what you mount)
```
Example:
```
$ vgs
  VG     #PV #LV #SN Attr   VSize    VFree
  vgdata   2   3   0 wz--n- <500.00g 100.00g     ← 100G unallocated
```

Extend a logical volume + filesystem (online):
```bash
pvcreate /dev/sdc                    # new disk into LVM
vgextend vgdata /dev/sdc             # add it to the volume group
lvextend -L +50G /dev/vgdata/lvlogs  # grow LV by 50G   (-l +100%FREE for all)
resize2fs /dev/vgdata/lvlogs         # ext4 — or: xfs_growfs /mountpoint
```

---

## 6. Software RAID (mdadm) — on-premise

```bash
cat /proc/mdstat               # RAID health at a glance — look for [UU] vs [U_]
mdadm --detail /dev/md0        # full array status
mdadm /dev/md0 --add /dev/sdc1 # add replacement disk (starts rebuild)
watch cat /proc/mdstat         # watch rebuild progress
```
`[U_]` = one member failed/missing. Replace disk, re-add, monitor rebuild.

---

## 7. Physical disk health — on-premise (and detectable in dmesg anywhere)

### `smartctl` — SMART data (package: smartmontools)
```bash
smartctl -H /dev/sda           # overall health PASSED/FAILED
smartctl -a /dev/sda           # all attributes — watch Reallocated_Sector_Ct,
                               # Current_Pending_Sector, UDMA_CRC_Error_Count
smartctl -t short /dev/sda     # run a short self-test
```

### Kernel-level disk errors
```bash
dmesg -T | grep -iE "i/o error|sector|ata|scsi|nvme"
journalctl -k | grep -i error
```

### NVMe tools
```bash
nvme list                      # list NVMe devices
nvme smart-log /dev/nvme0      # health/wear info
```

---

## 8. NFS / network storage

```bash
showmount -e nfsserver         # what the server exports
mount -t nfs nfsserver:/export /mnt/nfs
nfsstat -c                     # client-side NFS stats (retransmits = network issue)
# soft/hard, timeo and retrans cannot be changed with "-o remount" (NFS rejects it): mount again
umount /mnt/nfs && mount -t nfs -o soft,timeo=30,retrans=3 nfsserver:/export /mnt/nfs
```
Processes stuck in `D` (uninterruptible sleep) forever are the classic symptom of
a **dead NFS server with a hard mount** — they can't be killed; fix the server or
force-unmount: `umount -f -l /mnt/nfs` (lazy unmount). A `soft` mount returns an I/O
error instead of hanging (`timeo` is in tenths of a second), but it can lose writes:
use it only for read-mostly data, and keep `hard` for anything the application writes.

---

## Decision tree: "No space left on device"

```
df -h shows 100%?  → du -xh --max-depth=1 / | sort -rh   → delete/rotate/truncate
df -h shows space? → df -i (inodes full?)                → delete masses of small files
inodes fine too?   → lsof +L1 (deleted-but-open files)   → restart holding process
still weird?       → mount (read-only fs? overlay full?) → dmesg for fs errors
```
