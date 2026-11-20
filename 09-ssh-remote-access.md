# 09 — SSH & Remote Access

Typical symptoms: connection refused/timeout, "Permission denied (publickey)",
painfully slow login, host key warnings, broken file transfers.

---

## 1. The debugging workhorse: `ssh -v`

```bash
ssh -v user@host               # verbose — shows each auth step
ssh -vvv user@host             # maximum detail (key offers, kex, everything)
```
What to look for in `-v` output:
```
debug1: Connecting to host [10.0.1.20] port 22.        ← reaches TCP?
debug1: Offering public key: /home/me/.ssh/id_ed25519  ← is YOUR key offered?
debug1: Authentications that can continue: publickey   ← server allows which methods?
Permission denied (publickey).                          ← server rejected all offers
```

Connection-level quick checks:
```bash
nc -zv host 22                 # port reachable at all? refused vs timeout (see 02-network.md)
ssh -p 2222 user@host          # non-standard port
ssh -i ~/.ssh/special_key user@host    # explicit key
ssh -o IdentitiesOnly=yes -i key user@host   # offer ONLY this key
                               # (fixes "Too many authentication failures" when the
                               #  agent spams many keys)
ssh -o StrictHostKeyChecking=accept-new user@host   # first-contact automation
ssh -J bastion user@internal   # jump through a bastion host
ssh -o ConnectTimeout=5 user@host
```

## 2. Server side — where the real answer usually is

```bash
systemctl status sshd                          # running?
journalctl -u sshd -f                          # watch WHILE the client retries —
                                               # server logs say exactly why it refused
tail -f /var/log/auth.log                      # Debian/Ubuntu (RHEL: /var/log/secure)
sshd -t                                        # config syntax check BEFORE restart
sshd -T | grep -iE "permitroot|passwordauth|pubkey|allowusers|port"
                                               # EFFECTIVE config (after all includes/matches)
ss -tlnp sport = :22                           # actually listening? on which address?
```
Common server log lines and meaning:

- `Authentication refused: bad ownership or modes for directory /home/user` →
  **permissions problem** (fix below)
- `User app not allowed because account is locked` → `passwd -u app` / check `/etc/shadow` (`!` prefix)
- `no matching key exchange method` → ancient client/server → algo mismatch
- `Did not receive identification string` → something TCP-connects but isn't SSH (probe/LB healthcheck)
- nothing at all logged → traffic never arrives → network/firewall (02-network.md)

### The permissions checklist (cause of most "publickey" denials)
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_ed25519            # private keys (client side)
chown -R user:user ~/.ssh
# home dir itself must not be group/world-writable:
chmod go-w /home/user
```
Also verify the key really is in the file:
```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub           # fingerprint of your key
ssh-add -l                                      # fingerprints in your agent
grep "$(cut -d' ' -f2 ~/.ssh/id_ed25519.pub)" ~user/.ssh/authorized_keys  # on server
```

## 3. Keys & agent

```bash
ssh-keygen -t ed25519 -C "me@work"     # generate modern key
ssh-copy-id user@host                  # install your pubkey (password auth once)
eval "$(ssh-agent)" && ssh-add         # start agent, load default keys
ssh-add -l                             # what's loaded
ssh -A user@bastion                    # agent forwarding (use sparingly — risk on shared hosts)
```

Host key warnings:
```
WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!
```
Legit causes: host rebuilt/reimaged (very common with cloud instances reusing IPs).
If expected: `ssh-keygen -R host` removes the old entry. If NOT expected, stop and
verify — it can indicate interception.

## 4. Slow logins

| Symptom | Cause | Fix |
|---|---|---|
| ~10s pause pre-password | server reverse-DNS of your IP | `UseDNS no` in sshd_config |
| pause mid-auth | GSSAPI attempts | `GSSAPIAuthentication no` |
| pause after auth | systemd/logind session setup, or slow shell rc files | check `journalctl`, profile your .bashrc |
| every command laggy | packet loss | `mtr host` (02-network.md) |

Session drops on idle → keepalives, client side:
```text
# ~/.ssh/config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

## 5. File transfer

```bash
scp file user@host:/path/                       # simple copy
scp -r dir user@host:/path/                     # recursive
scp -P 2222 file user@host:/path/               # note: -P (capital) for port
rsync -avz --progress dir/ user@host:/path/     # resumable, incremental — prefer for big/many files
rsync -avz --partial --append-verify big.iso user@host:/data/   # resume interrupted transfer
rsync -avzn dir/ user@host:/path/               # -n DRY RUN — always test rsync --delete first!
sftp user@host                                  # interactive
```
rsync also debugs itself: run with `-vvv` to see why files are skipped.

## 6. Tunnels (test connectivity through bastions / expose remote services)

```bash
ssh -L 5433:db.internal:5432 user@bastion   # local 5433 → db.internal:5432 (via bastion)
psql -h 127.0.0.1 -p 5433                   # then test the DB locally
ssh -R 8080:localhost:80 user@public        # remote forward (expose your local :80)
ssh -D 1080 user@bastion                    # SOCKS proxy (browser via bastion)
ssh -N -f -L ...                            # -N no shell, -f background
```

## 7. AWS-flavored alternatives when SSH is blocked

```bash
aws ssm start-session --target i-0abc123               # Session Manager: no port 22,
                                                       # no public IP, no key needed
aws ec2-instance-connect send-ssh-public-key ...       # EC2 Instance Connect (temp key)
aws ec2 get-console-output --instance-id i-0abc123     # boot log when nothing else works
```
Prereqs for SSM: instance role with `AmazonSSMManagedInstanceCore`, SSM agent
running, outbound 443 (or VPC endpoints).

## Decision tree

```
ssh fails
├── timeout            → network path: nc -zv host 22 → 02-network.md (AWS: SG allows 22 from you?)
├── connection refused → sshd down / wrong port / listening on wrong iface → server: systemctl status sshd, ss -tlnp
├── permission denied  → ssh -vvv (is key offered?) + server auth.log (why rejected?)
│                        → 90%: authorized_keys content, ~/.ssh perms, wrong username
│                        (ubuntu vs ec2-user vs admin vs root — AMIs differ!)
├── host key changed   → rebuilt host? ssh-keygen -R host; else investigate
└── hangs after auth   → shell rc files, disk full on server, or dead NFS home dir
```
