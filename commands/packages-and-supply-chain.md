# Packages, secrets & supply chain

Packages reach a host from repositories that apt trusts through signing keys; dpkg records every file they install, and holds and unattended-upgrades decide when versions change. Ask before you change anything: which version is installed and from where (`apt-cache policy`, `dpkg -S`), what an upgrade would do (`apt list --upgradable`, `-s`), and what changed last (`/var/log/apt/history.log`, `dnf history`). The second half follows your own software: scan images (trivy), list their contents (syft), sign them (cosign), keep secrets out of Git (gitleaks, sops) and serve them from Vault or OpenBao.

| If you would reach for | Prefer | Because |
|---|---|---|
| `apt update && apt upgrade -y` | `apt-get update` (read its `W:` lines), `apt list --upgradable`, `apt-get -s upgrade` | a broken repository, and a plan that removes or restarts things, show up before anything changes |
| `apt show nginx` for "which version will I get?" | `apt-cache policy nginx` | installed and candidate side by side, with the repository and priority behind every version |
| guessing a binary's package from its name | `dpkg -S /usr/sbin/nginx`, then `dpkg -V nginx` | the real owner of the file, and which of its files were edited |
| `rm /var/lib/dpkg/lock*` | wait for the holder, or `apt-get -o DPkg::Lock::Timeout=600` | another dpkg is running; two writers corrupt the status database |
| `apt-key add` or `[trusted=yes]` | a key file in `/etc/apt/keyrings` named by `signed-by` | the key vouches for one repository only, and verification stays on |
| a scan gate that fails on every finding | `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1` | it stops only on what a rebuild can fix today |
| trusting an image tag | `cosign verify --key cosign.pub IMAGE@sha256:…` | proves your pipeline signed exactly that content |
| a Vault policy on `secret/app/*` that "should" work | `vault token capabilities secret/data/app/db` | KV v2 API paths contain `data/`; this shows what the token may really do |

### apt / apt-get — which front end for which job, and what is installed or upgradable?
Match: apt, apt-get, apk
Instead of: apt in scripts
Safety: read-only for `list`, `show`, `search` and `changelog` · changes state: `apt-get clean` deletes cached `.deb` files (they download again when needed)

**In one line:** `apt` and `apt-get` drive the same library, repositories and logs: `apt` is the friendlier terminal front end, `apt-get` keeps its output stable for scripts. This card covers the queries.

**Read the command:** `apt list --upgradable 2>/dev/null`

| Part | Meaning |
|---|---|
| `list --upgradable` | installed packages with a newer candidate, as of the last `apt update` |
| `2>/dev/null` | hide `WARNING: apt does not have a stable CLI interface`, printed when apt is piped |
| `list --installed` | installed packages; `[installed,automatic]` marks dependencies |
| `show PKG`, `changelog PKG` | the candidate's details, `APT-Sources:` included / its changelog: which revision fixed which CVE |
| `apt-get clean` | **changes state**: empty `/var/cache/apt/archives` to free disk space |

**What the output tells you:**

```
Listing...
openssh-server/noble-updates 1:9.6p1-3ubuntu13.14 amd64 [upgradable from: 1:9.6p1-3ubuntu13.13]
libssl3t64/noble-updates,noble-security 3.0.13-0ubuntu3.6 amd64 [upgradable from: 3.0.13-0ubuntu3.5]
docker-ce/noble 5:29.0.1-1~ubuntu.24.04~noble amd64 [upgradable from: 5:28.5.2-1~ubuntu.24.04~noble]
```

The suite after `/` is the source: `-security` a security fix (unattended-upgrades installs it), `-updates` a bug fix, `noble` from Docker's repository a vendor release, here a new major engine: read its release notes first.

**Why it is effective:** every pending update and its source before anything changes; `apt changelog PKG | grep CVE-…` answers "is this fix in my version?".

**Compared with `apt` in scripts:** same packages, but its output may change between releases and it warns when piped; scripts use `apt-get`, `apt-cache` and `apt-mark`.

**Trap:** the list is as fresh as the last `apt update`; on 22.04+ it can show a phased update that `upgrade` keeps back. `Could not get lock /var/lib/dpkg/lock-frontend`: another apt or unattended-upgrade is running; wait, never delete the lock files.

**Next step:** not yet → `apt-mark hold PKG`. Which repository → `apt-cache policy PKG`. Lock held → `sudo fuser -v /var/lib/dpkg/lock-frontend`; in scripts, `apt-get -o DPkg::Lock::Timeout=600 …` waits instead of failing. Related: Alpine images use `apk`: `apk add --no-cache curl bind-tools` installs without keeping the package index in the image (`bind-tools` brings `dig`).

### apt update / upgrade — are the package lists fresh, and what will an upgrade change?
Match: apt update, apt-get update, apt upgrade, apt-get upgrade, apt full-upgrade, apt-get full-upgrade, apt dist-upgrade, apt-get dist-upgrade
Instead of: apt update && apt upgrade -y
Safety: needs root · `update` rewrites only the package lists · changes state: `upgrade` and `full-upgrade` install packages whose scripts restart services; `full-upgrade` can remove packages

**In one line:** `apt update` refreshes every repository's package lists and installs nothing; `upgrade` installs newer versions of what is installed; `full-upgrade` may also add and **remove** packages.

**Read the command:** `apt-get update 2>&1 | grep -E 'NO_PUBKEY|legacy|Release file|disabled'`

| Part | Meaning |
|---|---|
| `update` | fetch the signed `InRelease` and package lists of every configured source |
| `2>&1 | grep -E '…'` | stderr (`W:`, `E:`) into the pipe; `-E` makes `|` mean "or": missing keys, the deprecated keyring, Release file errors, disabled repositories |
| `upgrade` | **changes state**: never removes; `apt-get upgrade` never adds a package either |
| `full-upgrade` (`dist-upgrade`) | **changes state**: may add packages and **remove** installed ones |
| `-s` | simulate: print the plan, change nothing |

**What the output tells you:**

```
W: An error occurred during the signature verification. The repository is not updated and the previous index files will be used. GPG error: https://apt.example.com/ubuntu noble InRelease: The following signatures couldn't be verified because the public key is not available: NO_PUBKEY 9BDF2468A1C3E5F7
$ sudo apt-get upgrade
The following packages have been kept back:
  linux-generic linux-headers-generic linux-image-generic
0 upgraded, 0 newly installed, 0 to remove and 3 not upgraded.
```

`NO_PUBKEY`: the `signed-by` key is missing or was rotated; the old lists stay in use, so that repository silently stops updating. `kept back`: the kernel metapackages need a new package, which `apt-get upgrade` never installs and `apt upgrade` does; holds and phased updates look the same.

**Why it is effective:** update's warnings are the only sign of a broken repository, and the summary line shows before you answer Y whether anything will be removed.

**Compared with `apt update && apt upgrade -y`:** fine on a lab VM; on a server it scrolls past the `W:` lines and accepts a plan nobody read.

**Trap:** package scripts restart services: a docker-ce or containerd upgrade restarts every container. Proxmox needs `full-upgrade`; elsewhere read its `REMOVED` list first. `DEBIAN_FRONTEND=noninteractive` silences debconf only: an edited config file that the package also changed stops dpkg (`EOF on stdin at conffile prompt`) unless `-o Dpkg::Options::=--force-confold` keeps yours.

**Next step:** `NO_PUBKEY` or `legacy trusted.gpg keyring` → the gpg card. `Release file … is not valid yet` → the clock: `timedatectl`. Kept back → `apt-cache policy PKG`, `apt-mark showhold`.

### apt-cache policy — which version is installed, which would install, and from which repository?
Match: apt-cache, apt policy
Instead of: apt show, apt list -a
Safety: read-only · no root needed

**In one line:** `apt-cache policy PKG` shows the installed version, the candidate apt would install, and every available version with its repositories and priorities: the data apt chooses from.

**Read the command:** `apt-cache policy apache2`

| Part | Meaning |
|---|---|
| `policy apache2` | versions, sources and priorities of one or more packages (`apt policy` is the same); no name: every repository |
| `madison docker-ce` | one line per version and repository: the exact string for `install PKG=VERSION` |
| `rdepends --installed apache2-bin` | installed packages that depend on it: what a removal would take along |

**What the output tells you:**

```
apache2:
  Installed: 2.4.58-1ubuntu8.4
  Candidate: 2.4.58-1ubuntu8.5
  Version table:
     2.4.58-1ubuntu8.5 500
        500 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages
 *** 2.4.58-1ubuntu8.4 100
        100 /var/lib/dpkg/status
```

`***` marks the installed version; under each version, its sources and priority: 500 a normal repository, 100 the installed copy. The candidate is the highest priority, the newest among equals; pins in `/etc/apt/preferences.d/` change the numbers, and only a priority above 1000 downgrades. `(phased 30%)`: that version waits for this host's turn (22.04+).

**Why it is effective:** the only view that shows *why* apt picks a version or refuses yours, and where the installed one came from: the archive, a PPA, a vendor repository.

**Compared with `apt show` and `apt list -a`:** `apt show PKG` describes the candidate (with `APT-Sources:`), `apt list -a PKG` lists versions; neither shows the priorities that decide.

**Trap:** it reads the local lists: `apt update` after editing sources. A held package still shows a newer candidate: holds are not priorities. madison prints the epoch (`5:` in `5:27.3.1-1~ubuntu.24.04~noble`), and `install PKG=VERSION` fails without it.

**Next step:** the wrong repository wins → fix that source or pin it. Another version → copy it from `madison` into `apt install PKG=VERSION`, then `apt-mark hold`. A removal looks too big → `apt-get -s remove PKG`.

### apt install / remove / purge — add or take away packages, and see what goes with them
Match: apt install, apt-get install, apt remove, apt-get remove, apt purge, apt-get purge, apt autoremove, apt-get autoremove
Instead of: dpkg -i, deleting a package's files by hand
Safety: changes state: installs or removes packages and runs their maintainer scripts, which start, stop or restart services · needs root · `purge` also deletes the package's config files

**In one line:** `apt install` resolves dependencies and conflicts, then downloads and configures packages (usually starting the service); `remove` keeps the config files, `purge` deletes them, `autoremove` clears unneeded dependencies.

**Read the command:** `apt install nginx=1.24.0-1ubuntu1`

| Part | Meaning |
|---|---|
| `install` | **changes state**: the package plus missing dependencies |
| `nginx=1.24.0-1ubuntu1` | this exact version (upstream 1.24.0, Debian revision 1, first Ubuntu change) |
| `-y` | answer yes; downgrades and held packages still need `--allow-downgrades` / `--allow-change-held-packages` |
| `./pkg.deb` | a local file (`./` makes it a path); apt fetches its dependencies |
| `--fix-broken install` (`-f`) | **changes state**: repair a half-done dependency state |
| `remove` / `purge` | **changes state**: uninstall, keeping / deleting the config files |
| `autoremove --purge` | **changes state**: purge dependencies nothing needs (old kernels) |

**What the output tells you:**

```
$ sudo apt-get install docker-ce docker-ce-cli containerd.io
The following packages will be REMOVED:
  containerd docker.io runc
The following NEW packages will be installed:
  containerd.io docker-ce docker-ce-cli
0 upgraded, 3 newly installed, 3 to remove and 12 not upgraded.
```

Read `REMOVED` and the summary first: Docker's packages conflict with Ubuntu's `docker.io`, so this "install" swaps the engine under every container, and `-y` would not have asked. `-s` prints the plan without changing anything; in a purge each package carries a `*`.

**Why it is effective:** apt solves dependencies and conflicts first and shows the whole change as one plan; remove versus purge decides whether `/etc/nginx` survives.

**Compared with `dpkg -i`:** it installs just that file; a missing dependency leaves it unconfigured until `apt-get -f install` finishes. `apt install ./pkg.deb` does both.

**Trap:** the service starts during the install, so a port clash fails it (`post-installation script subprocess returned error exit status 1`). `autoremove` takes anything installed only as a dependency (`apt-mark manual PKG` keeps it); `-f install` may repair by removing. `purge` leaves data such as `/var/lib/docker`.

**Next step:** postinst failed → `journalctl -u SERVICE`, fix the cause, `dpkg --configure -a`. Version not found → `apt-cache madison PKG`. Leftovers → `dpkg -l | grep '^rc'`.

### apt-mark — freeze a package at its version, and see what is frozen
Match: apt-mark
Instead of: unattended-upgrades' Package-Blacklist alone
Safety: read-only for `showhold`, `showmanual` and `showauto` · changes state: `hold`, `unhold`, `manual` and `auto` apply to every later apt run, scripts and unattended-upgrades included · needs root

**In one line:** `apt-mark hold` makes apt leave a package at its installed version (no upgrade, downgrade or removal) until `unhold`; `showhold` lists what is frozen.

**Read the command:** `apt-mark hold kubelet kubeadm kubectl`

| Part | Meaning |
|---|---|
| `hold` | **changes state**: mark the packages held (`hi` in `dpkg -l`) |
| `kubelet kubeadm kubectl` | the whole set that must move together |
| `unhold` / `showhold` | release them (**changes state**) / list held packages |
| `manual PKG` | **changes state**: mark a dependency as wanted, so `autoremove` keeps it |

**What the output tells you:**

```
kubelet set on hold.
kubeadm set on hold.
kubectl set on hold.
$ sudo apt-get remove -y kubectl
E: Held packages were changed and -y was used without --allow-change-held-packages.
```

`upgrade` now lists them as kept back, and a scripted change fails instead of asking: that is how an Ansible run stops on a host where someone held packages.

**Why it is effective:** one command protects a version from every path that could move it: a colleague's `apt upgrade`, a playbook, unattended-upgrades. The Kubernetes docs prescribe it; on a Dokploy or Swarm host it keeps docker-ce from restarting every container at a random hour.

**Compared with u-u's `Package-Blacklist`:** it stops only unattended-upgrades; people and playbooks still upgrade. A pin in `/etc/apt/preferences.d/` can choose a version range or repository; a hold cannot.

**Trap:** hold the set: a held `docker-ce` with an unheld `containerd.io` can still drift apart. `you have held broken packages` usually involves no hold at all: it is apt's generic "cannot solve the dependencies". A forgotten hold is an unpatched package: review `showhold` every patch window.

**Next step:** kept back → `apt-mark showhold`, `apt-cache policy PKG`. Planned upgrade → `unhold`, `apt-get install -y PKG=VERSION`, `hold` again. RHEL → `dnf versionlock`.

### dpkg — which package owns this file, what state is it in, and were its files changed?
Match: dpkg, dpkg-query, debsums
Instead of: dpkg -l | grep NAME
Safety: read-only for `-l`, `-S`, `-L`, `-s`, `-V` and `dpkg-query` · changes state: `--configure -a`, `-i` and `--purge` configure, install or remove packages and run their scripts (needs root)

**In one line:** dpkg is the installer under apt and holds the database of every installed package and file: who owns a file, what a package installed, each package's state, and whether its files changed.

**Read the command:** `dpkg -l | grep -v '^ii'`

| Part | Meaning |
|---|---|
| `-l` | list packages with state letters, version and description |
| `| grep -v '^ii'` | `-v` drops the healthy `ii` lines: the header and every unhealthy package remain |
| `-S /usr/sbin/nginx` | which package owns this file |
| `-L nginx` / `-s nginx` | the files it installed / its state, version and dependencies |
| `-V apache2` | compare its files with the recorded checksums |
| `--configure -a` | **changes state**: finish configuring every half-done package |

**What the output tells you:**

```
Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name                         Version                       Architecture Description
+++-============================-=============================-============-==========================
iF  linux-image-6.8.0-85-generic 6.8.0-85.85                   amd64        Signed kernel image generic
rc  apache2                      2.4.58-1ubuntu8.4             amd64        Apache HTTP Server
hi  docker-ce                    5:28.5.2-1~ubuntu.24.04~noble amd64        Docker: the open-source application container engine
```

First letter: what was asked (`i` install, `r` remove, `h` hold); second: the real state (`i` installed, `c` config only, `U` unpacked, `F` half-configured); uppercase means trouble. `iF`: a failed configure step (a service that would not start, a full /boot); `rc`: config left behind. `-V` prints `??5?????? c /etc/apache2/apache2.conf`: a config file (`c`) whose checksum (`5`) changed.

**Why it is effective:** from a binary path in `ps`, `ss` or `/proc/PID/exe`, `-S` names the package, hence its config, logs and updates; `-V` tells "edited" from "replaced"; the states explain apt's `error code (1)`.

**Compared with `dpkg -l | grep NAME`:** fine for "is it installed?", but guessing by name misses that `/usr/sbin/apache2` belongs to `apache2-bin`, and anything installed by hand.

**Trap:** on usr-merged Ubuntu (22.04+) a package may have registered `/sbin/X`, so `dpkg -S /usr/sbin/X` finds nothing: try `dpkg -S '*bin/X'` before concluding "not packaged". `-i` installs without dependencies; `--configure -a` re-runs the failing script, so fix its cause first.

**Next step:** `iF` or `iU` → `sudo dpkg --configure -a`, fix the first error, repeat, then `apt-get -f install`. A changed binary (no `c`) → `apt install --reinstall PKG`; suspect tampering. Inventory → `dpkg-query -W -f='${Package} ${Version}\n' PKG`. Related: `debsums -c` (package debsums) lists packaged files whose checksum changed, like `dpkg --verify` and `rpm -Va`.

### gpg — which key does apt trust for this repository?
Match: gpg, apt-key
Instead of: apt-key add, [trusted=yes]
Safety: read-only for `--list-keys` · changes state: `--dearmor -o`, `--import` and `--delete-keys` write the key files that decide which repositories apt trusts · needs root under `/etc/apt` and `/usr/share/keyrings`

**In one line:** apt checks each repository's signed `InRelease` against OpenPGP keys; gpg turns a vendor's key into the file a `signed-by=` entry names, and manages the old shared keyring.

**Read the command:** `curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg`

| Part | Meaning |
|---|---|
| `curl -fsSL URL |` | download the key (fail on HTTP errors, silent but show errors, follow redirects) into gpg |
| `sudo gpg --dearmor -o /etc/apt/keyrings/…gpg` | convert the text form (`-----BEGIN PGP PUBLIC KEY BLOCK-----`) to binary and write it, as root, where `signed-by=` points |
| `--no-default-keyring --keyring /etc/apt/trusted.gpg --list-keys` | list the keys in that file only |
| `--batch --yes --delete-keys FINGERPRINT` | **changes state**: delete one key without prompting |
| `--keyring gnupg-ring:FILE --import` | **changes state**: import into FILE in the classic format apt reads |

**What the output tells you:**

```
/etc/apt/trusted.gpg
--------------------
pub   rsa4096 2017-02-22 [SCEA]
      3F1A9C0E5B7D2468ACE013579BDF2468A1C3E5F7
uid           [ unknown] Example Repo Signing Key <repo@example.com>
```

`NO_PUBKEY 9BDF2468A1C3E5F7` quotes the fingerprint's last 16 digits; `[ unknown]` is gpg's own trust opinion, irrelevant to apt.

**Why it is effective:** with `signed-by`, each repository is checked against exactly the key file it names; these commands show which key vouches for what and empty the legacy keyring, where any key signs for all.

**Compared with `apt-key add` and `[trusted=yes]`:** apt-key put every key into `/etc/apt/trusted.gpg`, trusted for all repositories (deprecated, gone after Ubuntu 24.04); `[trusted=yes]` silences the error by switching verification off.

**Trap:** an armored key file must end in `.asc`, a binary one in `.gpg`; a plain `--keyring FILE --import` creates a keybox file apt rejects (hence `gnupg-ring:`). apt verifies as the `_apt` user, so key files must be world-readable. A re-run of `--dearmor -o` stops at `Overwrite? (y/N)`: add `--yes`.

**Next step:** `NO_PUBKEY` → the vendor's current key into the `signed-by` file. Legacy keyring warning → move the key to `/etc/apt/keyrings/`, add `signed-by`, delete it from `trusted.gpg`. Before trusting a key file → `gpg --show-keys FILE` against the vendor's fingerprint. Related: `apt-key list` shows the keys in the legacy keyrings, trusted for every repository: move each to its own `signed-by` file.

### unattended-upgrade — what will tonight's automatic run install, and what will it skip?
Match: unattended-upgrade, unattended-upgrades, apt-config
Instead of: reading 50unattended-upgrades by eye
Safety: needs root · `--dry-run` installs nothing but downloads the packages · without `--dry-run` it installs the updates now, restarting services · `apt-config dump` is read-only

**In one line:** `unattended-upgrade --dry-run --debug` runs the daily job's logic (allowed origins, blacklist, holds) without installing and names what it would upgrade; `apt-config dump` shows the merged settings.

**Read the command:** `unattended-upgrade --dry-run --debug 2>&1 | grep -E 'Allowed origins|Packages that will be upgraded|blacklist'`

| Part | Meaning |
|---|---|
| `--dry-run` | simulate: download, do not install |
| `--debug` | log every decision: origins, each package checked, why one is skipped |
| `2>&1 | grep -E '…'` | all messages into grep (`-E`: `|` means "or"); keep the origins, the blacklist and the upgrade list |
| `apt-config dump` | apt's configuration merged from every file in `/etc/apt/apt.conf.d/` |

**What the output tells you:**

```
Allowed origins are: o=Ubuntu,a=noble, o=Ubuntu,a=noble-security, o=UbuntuESMApps,a=noble-apps-security, o=UbuntuESM,a=noble-infra-security
Initial blacklist: docker-ce docker-ce-cli containerd.io
Packages that will be upgraded: libssl3t64 openssl
$ apt-config dump | grep -E 'Periodic::(Update-Package-Lists|Unattended-Upgrade)'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "0";
```

Only the release, `-security` and ESM are installed automatically; `-updates`, PPAs and vendor repositories are left to you. `Unattended-Upgrade "0"`: the timer still fires, installs nothing, and nothing warns.

**Why it is effective:** settings are spread over several files, later ones adding to lists and overriding values; the dry run evaluates the merged result as tonight's run will.

**Compared with reading `50unattended-upgrades`:** the shipped file documents every option, but a later file or a `//` comment changes the outcome; only the dump and the dry run show it.

**Trap:** Ubuntu's own `containerd` and `docker.io` come from the archive, so their security updates *are* installed, restarting every container. `Automatic-Reboot "true"` reboots after kernel updates. A running job holds the dpkg lock (`unattended-upgr` in the lock error): wait, never kill it.

**Next step:** a risky package listed → `Package-Blacklist` or `apt-mark hold`, then patch it in a window. Switched off → `"1"` in `20auto-upgrades`, plus an alert when the log goes quiet. Schedule and history → `systemctl list-timers 'apt-daily*'`, `/var/log/unattended-upgrades/`.

### pro — is this Ubuntu host covered by security updates, and is this CVE fixed here?
Match: pro, canonical-livepatch
Instead of: ssh -V or a banner scan
Safety: read-only for `status` and `security-status` · changes state: `fix` installs the fixed packages when they are missing (`--dry-run` only shows the plan); `attach` and `enable` add Ubuntu Pro services · needs root to change anything

**In one line:** `pro` is the Ubuntu Pro client: `fix` checks a CVE against Ubuntu's advisories for the installed packages, `security-status` counts packages by support source, `status` lists Pro services.

**Read the command:** `pro fix CVE-2024-6387`

| Part | Meaning |
|---|---|
| `fix CVE-2024-6387` | check this CVE (OpenSSH's "regreSSHion"; `USN-…` works too) for this release's installed packages; install the fix if it is missing |
| `--dry-run` | show what `fix` would install |
| `security-status` | packages from main, universe and third parties, and what covers them |
| `status` | `esm-infra`, `esm-apps`, `livepatch`: entitled? enabled? |

**What the output tells you:**

```
CVE-2024-6387: OpenSSH vulnerability
 - https://ubuntu.com/security/CVE-2024-6387
1 affected source package is installed: openssh
(1/1) openssh:
A fix is available in Ubuntu standard updates.
The update is already installed.
✔ CVE-2024-6387 is resolved.
```

`standard updates`: the fix is in the normal archive; `resolved`: the installed revision carries the backported fix.

**Why it is effective:** Ubuntu backports fixes into the shipped version (`1:8.9p1-3ubuntu0.10` fixed this on 22.04), so banner scanners still see 8.9p1 and flag it; `pro fix` checks Ubuntu's advisories and gives dated evidence.

**Compared with `ssh -V` and version scanners:** they show the upstream version, not the backport; the package revision (`dpkg-query -W openssh-server`) and the advisory decide.

**Trap:** without `--dry-run`, `fix` installs packages on the spot. "Resolved" covers files, not running processes: restart sshd and libssl users, reboot for the kernel (`needrestart -b`). Canonical covers universe only through ESM Apps; containers and `/opt` are invisible here.

**Next step:** not installed → `pro fix CVE-ID` in a window, then restart. Only in Pro → attach it or record an exception. No fix yet → the Ubuntu CVE tracker and a dated exception. Related: `canonical-livepatch status` shows whether the running kernel is covered and its livepatches applied (`pro enable livepatch` turns it on).

### update-alternatives — which of several installed programs does this command name run?
Match: update-alternatives
Instead of: ls -l /usr/bin/java, relinking by hand
Safety: read-only for `--display` · changes state: `--set`, `--config` and `--auto` repoint the link for every user and service at once · needs root

**In one line:** several packages can provide one command (`iptables`, `java`) through links in `/etc/alternatives`; update-alternatives shows which one runs and why, and switches it.

**Read the command:** `update-alternatives --display iptables`

| Part | Meaning |
|---|---|
| `--display iptables` | the link group: mode, current target, every candidate with its priority |
| `--set iptables /usr/sbin/iptables-nft` | **changes state**: point the group at this path, in manual mode |
| `--config java` | **changes state**: pick from a numbered menu |
| `--auto NAME` | **changes state**: back to automatic mode |

**What the output tells you:**

```
iptables - auto mode
  link best version is /usr/sbin/iptables-nft
  link currently points to /usr/sbin/iptables-nft
  …
  slave iptables-save is /usr/sbin/iptables-save
/usr/sbin/iptables-legacy - priority 10
…
/usr/sbin/iptables-nft - priority 20
```

`auto mode`: the highest priority wins, and package updates may switch it; `manual mode` (after `--set` or `--config`) stays put. Slaves such as `iptables-save` follow their master.

**Why it is effective:** the wrong variant still "works" (legacy rules nobody sees, Jenkins on Java 17), so the symptom points elsewhere; one display shows the real target and whether someone pinned it.

**Compared with `ls -l /usr/bin/java`:** it shows only the first hop, `/etc/alternatives/java`; `iptables -V` alone says which backend runs.

**Trap:** switching the iptables backend moves no rules: Docker and kube-proxy keep theirs in the old one until they restart, so switch `ip6tables` too and reboot in a window. Each Java tool is its own group, and a service with its own `JAVA_HOME` ignores the link.

**Next step:** after the reboot → `iptables-legacy -S` shows only the default policies. All Java tools at once → `update-java-alternatives`.

### dnf / rpm — what changed on this RHEL or Rocky host, and who owns or changed this file?
Match: dnf, yum, rpm, package-cleanup
Instead of: rpm -qa --last, find / -name
Safety: read-only for `history`, `list`, `info`, `repolist`, `rpm -q…` and `rpm -V` · changes state: `install`, `remove`, `update`, `downgrade` and `history undo` change packages; `config-manager --set-disabled` edits repository files; `rpm --rebuilddb` rewrites the database · needs root to change

**In one line:** dnf (`yum` on RHEL 8+ is dnf) installs from the repositories in `/etc/yum.repos.d/` and records every transaction; rpm beneath it is RHEL's dpkg.

**Read the command:** `dnf history info 42`

| Part | Meaning |
|---|---|
| `history` / `history info 42` | the transactions / one in full: who, which command, each package's versions |
| `history undo 42` | **changes state**: reverse it (old versions must still be in a repository) |
| `--showduplicates list nginx` | every available version by repository (`install nginx-1.24.0` takes one) |
| `config-manager --set-disabled repo` | **changes state**: switch a broken repository off (dnf-plugins-core) |
| `rpm -qf /usr/sbin/nginx`, `rpm -ql` / `-qc PKG` | the file's owner / a package's files, or its config files |
| `rpm -V nginx`, `rpm -Va` | compare one or every package's files with the rpm database |

**What the output tells you:**

```
ID     | Command line             | Date and time    | Action(s)      | Altered
-------------------------------------------------------------------------------
    43 | update                   | 2026-10-02 06:12 | I, U           |       14
    42 | install httpd            | 2026-09-30 14:20 | Install        |        9
$ sudo rpm -V nginx
S.5....T.  c /etc/nginx/nginx.conf
..5....T.    /usr/sbin/nginx
```

Transaction 43 installed and upgraded 14 packages (`I, U`): `info` lists each change, `undo` reverses them. In `rpm -V` each letter is a failed test (`S` size, `M` mode, `5` checksum, `U`/`G` owner, `T` mtime) and `c` marks config, so the binary is the worrying line.

**Why it is effective:** "it worked yesterday" becomes a transaction you can read and reverse, and "did someone change this server?" a short list of files.

**Compared with `rpm -qa --last`:** newest-installed first, enough to spot what is new, but not which run changed them, and no undo.

**Trap:** `undo` needs the old packages in a repository, and undoing a security update reopens the hole. One unreachable repository can fail every dnf command (`Failed to download metadata for repo`): `--disablerepo=NAME`. Root can edit the rpm database too: a clean `rpm -V` is evidence, not proof.

**Next step:** `No match for argument` → a disabled repository (`dnf repolist -v`) or EPEL (`dnf install -y epel-release`). Corrupt metadata → `dnf clean all && dnf makecache`. Changed binary → `dnf reinstall PKG`. Freeze → `dnf versionlock add PKG`. Related: `package-cleanup --problems` (yum-utils) lists broken dependencies on older hosts; `dnf check` does it with dnf.

### snap — which snaps are installed, which services do they run, and did they update themselves?
Match: snap
Instead of: apt list --installed, dpkg -l
Safety: read-only for `list`, `services` and `changes` · changes state: `install`, `refresh`, `revert` and `remove` change software at once, and a refresh restarts the snap's services · needs root to change

**In one line:** snaps are self-contained packages under `/snap`, run by snapd outside apt and dpkg and refreshed automatically.

**Read the command:** `snap install aws-cli --classic`

| Part | Meaning |
|---|---|
| `install aws-cli` | **changes state**: download the snap from the Snap Store and mount it |
| `--classic` | no sandbox, host access like a deb (only for snaps published that way) |
| `list` / `services NAME` | installed snaps with revision and channel / their daemons: enabled? active? |
| `refresh` / `changes` | update now (**changes state**) / what snapd did, and when |

**What the output tells you:**

```
$ snap list
Name              Version   Rev    Tracking       Publisher   Notes
amazon-ssm-agent  3.3.987   9881   latest/stable  aws✓        classic
$ sudo snap services amazon-ssm-agent
Service                            Startup  Current  Notes
amazon-ssm-agent.amazon-ssm-agent  enabled  active   -
```

`Rev` is the running revision (older ones stay for `snap revert`); services run as units named `snap.NAME.SERVICE.service`.

**Why it is effective:** snaps never appear in `dpkg -l` or `apt list` and update themselves, so this is the only inventory of that part of the host.

**Compared with `apt list --installed`:** complete for debs, blind to snaps: how a host ends up with two `docker` binaries (`type -a docker`).

**Trap:** snapd checks for refreshes itself (four times a day by default) and restarts services without a change ticket. Strict confinement hides paths: snap Docker fails bind mounts from `/srv` or `/mnt`.

**Next step:** unplanned update → `snap changes`, `snap revert NAME`, then a window: `sudo snap set system refresh.timer=fri,23:00-01:00`. Service down → `snap logs NAME`.

### pip / npm — which language packages are installed, do they fit together, and are any vulnerable?
Match: pip, pip3, npm, pip-audit
Instead of: pip freeze, npm install and hope
Safety: read-only for `pip list`, `pip check`, `npm audit`, `npm config get` and `npm ping` · changes state: `pip install` and `npm install` change the environment (outside a virtualenv, `pip install` can break OS tools); `npm audit fix` rewrites `package.json` and the lockfile

**In one line:** apt does not track Python or Node libraries: `pip list` and `pip check` show what an environment holds and whether it is consistent, `npm audit` checks a project's locked dependencies against known advisories.

**Read the command:** `npm audit --omit=dev --audit-level=high`

| Part | Meaning |
|---|---|
| `audit` | send the tree from `package-lock.json` to the registry; list known advisories |
| `--omit=dev` | skip devDependencies (build and test tools that never reach production) |
| `--audit-level=high` | exit non-zero only for high or critical findings: the CI gate |
| `npm config get registry`, `npm ping` | which registry npm uses (a Nexus proxy?) / does it answer |
| `pip list`, `pip check` | installed packages / requirements that are missing or conflict |

**What the output tells you:**

```
$ npm audit --omit=dev --audit-level=high
…
2 vulnerabilities (1 moderate, 1 high)
$ echo $?
1
$ pip check
app-client 2.3.0 has requirement urllib3<2, but you have urllib3 2.2.1.
```

`--audit-level` sets the exit code, not the report: the moderate finding is listed but would not fail the job alone. `pip check`: a library outside another's supported range, which breaks at the first call into the changed API.

**Why it is effective:** most application CVEs and "works on my machine" breakages live in these libraries, where apt's tools never look.

**Compared with `pip freeze`:** same packages, enough to pin an environment, without checking that they fit together.

**Trap:** `pip` may not be the app's interpreter: use `python3 -m pip` in its virtualenv. Ubuntu 24.04's system Python refuses `pip install` (`externally-managed-environment`): use a venv, not `--break-system-packages`. `npm audit` needs a lockfile.

**Next step:** a high finding → upgrade the dependency, re-run in CI. A conflict → pin compatible versions and rebuild the venv (`pip install -r requirements.txt`). 401 from the registry → `npm config get registry`, then `.npmrc`. Related: `pip-audit -r requirements.txt` checks Python requirements against known vulnerabilities, like `npm audit`.

### trivy — which known vulnerabilities and secrets does this image carry, and which can you fix now?
Match: trivy
Instead of: trivy image IMAGE with every default
Safety: read-only for the image or directory · downloads its vulnerability database unless cached, and pulls the image if it is not local · `--exit-code 1` deliberately fails a CI job

**In one line:** Trivy matches an image's packages (OS and language libraries) against a vulnerability database it downloads, also flags secrets and config mistakes, and its exit code makes the result a CI gate.

**Read the command:** `trivy image --severity HIGH,CRITICAL --ignore-unfixed shop-web:dev`

| Part | Meaning |
|---|---|
| `image shop-web:dev` | scan this image, from the local engine or the registry |
| `--severity HIGH,CRITICAL` | report only these severities |
| `--ignore-unfixed` | hide findings without a fixed version: what remains, a rebuild or upgrade can fix |
| `--scanners vuln,secret` | what to look for (an image's default); `misconfig` adds config checks |
| `--exit-code 1`, `--format json --output F` | exit 1 when findings remain (the CI gate) / a JSON report for the job's artifacts |
| `fs .` / `config ./Dockerfile` / `sbom FILE` | a source tree's lockfiles / a Dockerfile or manifests / an existing SBOM |

**What the output tells you:**

```
shop-web:dev (debian 13.1)
Total: 2 (HIGH: 2, CRITICAL: 0)
│ Library    │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version   │
│ libexpat1  │ CVE-YYYY-NNNNN │ HIGH     │ fixed  │ 2.7.1-2           │ 2.7.1-2+deb13u1 │
```

The header names the detected OS, whose advisories set severity and fixed version. `fixed`: a rebuild on a fresh base (`docker build --pull`) clears it; `affected` or `will_not_fix` (hidden by `--ignore-unfixed`) need a triage decision instead.

**Why it is effective:** an image's age says nothing about its CVEs; Trivy names package, version and fix, so "23 findings" becomes "3 a rebuild fixes", the ones worth stopping a pipeline for.

**Compared with plain `trivy image IMAGE`:** every severity and every unfixed finding: right for an audit, but as a gate it fails on what nobody can fix, and people learn to bypass it.

**Trap:** results belong to the database date: an unchanged image can fail tomorrow (`trivy --version` shows `UpdatedAt`). A failed DB download (`TOOMANYREQUESTS`) fails the job before scanning: `--cache-dir`, `--db-repository`. A binary added with `curl` is invisible, and Trivy trusts the system CA store, not `/etc/docker/certs.d`.

**Next step:** `fixed` → rebuild with `--pull`, rescan. Unfixable and unreachable → `.trivyignore.yaml` (`--ignorefile`) with a statement and `expired_at`. Dockerfiles → `trivy config` in merge requests.

### syft — what exactly is inside this image?
Match: syft
Instead of: docker run --rm IMAGE dpkg -l
Safety: read-only · reads the image from the registry or the local engine; `-o FORMAT=FILE` writes files

**In one line:** syft lists every package in an image, directory or archive (OS and language libraries, with version and type) and writes it as an SBOM in standard formats.

**Read the command:** `syft scan harbor.example.com/shop/api:1.8.1 -o spdx-json=sbom.spdx.json -o cyclonedx-json=sbom.cdx.json`

| Part | Meaning |
|---|---|
| `scan harbor.example.com/shop/api:1.8.1` | catalogue the image you ship (`registry:` in front reads it without Docker; `dir:.` a directory) |
| `-o spdx-json=sbom.spdx.json` | write SPDX JSON to this file |
| `-o cyclonedx-json=sbom.cdx.json` | and CycloneDX JSON to another: `-o` repeats (`-o table` prints a list) |

**What the output tells you:**

```
NAME        VERSION        TYPE
adduser     3.152          deb
certifi     2025.8.3       python
$ jq '.components | length' sbom.cdx.json
187
```

`TYPE` is the ecosystem (`deb`, `python`, `go-module`…): an image SBOM includes the OS packages that a source-tree scan misses.

**Why it is effective:** when the next xz-style CVE lands, `jq` over stored SBOMs answers "which releases contain it?" in minutes without pulling an image; `trivy sbom` re-checks them against today's database.

**Compared with `docker run --rm IMAGE dpkg -l`:** lists one image's OS packages, enough for a quick look, but misses pip, npm, Go and Java components and writes no standard file.

**Trap:** generate it from the pushed image, by digest: `syft scan dir:.` lists only what the lockfiles name. Read whole version strings: `5.6.1+really5.4.5` is 5.4.5.

**Next step:** tie it to the digest → `cosign attest --type cyclonedx --predicate sbom.cdx.json IMAGE@DIGEST`. A new CVE in old releases → `trivy sbom sbom.cdx.json`.

### cosign — was this exact image signed by our pipeline's key?
Match: cosign
Instead of: trusting a tag, docker pull and docker inspect
Safety: read-only for `verify` and `verify-attestation` · changes state: `sign` and `attest` push signatures and attestations to the registry and, by default, record an entry in the public Rekor transparency log; `generate-key-pair` writes `cosign.key` (keep it out of Git)

**In one line:** cosign signs an image **digest** with your key, stores the signature beside the image in the registry and verifies it before deploying; `attest` attaches an SBOM the same way.

**Read the command:** `cosign verify --key cosign.pub "harbor.example.com/shop/api@${DIGEST}"`

| Part | Meaning |
|---|---|
| `verify --key cosign.pub` | find the image's stored signatures and check them against this public key |
| `…/shop/api@${DIGEST}` | the image by digest (`sha256:…`), never by tag |
| `sign --yes --key cosign.key IMAGE@DIGEST` | **changes state**: sign; `--yes` answers the prompt a CI job cannot |
| `generate-key-pair` | **changes state**: `cosign.key` (encrypted with `COSIGN_PASSWORD`) and `cosign.pub` |
| `attest` / `verify-attestation --type cyclonedx` | **changes state**: attach a signed SBOM (`--predicate sbom.cdx.json`) / check it |

**What the output tells you:**

```
Verification for harbor.example.com/shop/api@sha256:4b1e0c2d… --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key
```

Checks go to stderr, the signed payload (repository and digest) to stdout, so `cosign verify … >/dev/null && echo verified` gates a deploy. `no signatures found`: nothing signed this digest (the tag moved); `no matching signatures`: another key signed it.

**Why it is effective:** anyone with push rights can move a tag; a signature over the digest proves the content came from your CI's key, and Harbor or an admission controller can refuse the rest.

**Compared with `docker pull` and `docker inspect`:** they show the digest you received, enough to pin it, not who built it.

**Trap:** `verify IMAGE:TAG` checks whatever the tag points to now: deploy digests and make tags immutable. Key-based signing still publishes the image name and digest to the public log by default. Sign and verify with the same cosign version.

**Next step:** `no signatures found` → `docker buildx imagetools inspect IMAGE:TAG`. SBOM → `verify-attestation … | jq -r '.payload' | base64 -d`. Enforce → Harbor's cosign policy, Kyverno `verifyImages`.

### gitleaks — has a secret ever been committed to this repository, and where?
Match: gitleaks
Instead of: grep -r password, deleting the file in a new commit
Safety: read-only: scans files and Git history · a report written without `--redact` contains the secrets themselves

**In one line:** gitleaks searches a repository's whole Git history, deleted files included, for tokens, keys and passwords, using rules for known formats plus entropy, and exits non-zero when it finds any.

**Read the command:** `gitleaks git --redact -v .`

| Part | Meaning |
|---|---|
| `git .` | scan this repository's Git history (gitleaks 8.19+; older releases: `detect --source .`) |
| `--redact` | print `REDACTED` instead of the secret, so the output can go into tickets and CI logs |
| `-v` | verbose: every finding with rule, file, line, commit and date |
| `--report-format json --report-path leak.json` | also write the findings to a file; `--pre-commit --staged` scans only staged changes |

**What the output tells you:**

```
Finding:     HARBOR_PASSWORD=REDACTED
RuleID:      generic-api-key
File:        deploy/harbor.env
Commit:      9b1e44c0d2a5f6e7b8c9d0e1f2a3b4c5d6e7f809
Date:        2026-10-02T08:41:30Z
…
11:52AM WRN leaks found: 1
```

`Commit` and `Date` say since when the value has been exposed; the `File` may be long gone from the working tree. Exit code 1 means leaks, 0 clean: a CI gate.

**Why it is effective:** a secret deleted in a later commit is still in history and every clone; gitleaks reads all of it with rules for real token formats, where `grep` sees only today's files.

**Compared with `grep -rn password .`:** it finds obvious strings in current files, fine for a quick look, but is blind to history and to tokens without a keyword nearby.

**Trap:** deleting the file or rewriting history does not un-leak it: rotate the credential first. Without `--redact`, the report and the job log expose the secret again. A shallow CI clone (`GIT_DEPTH`) holds only the latest commits.

**Next step:** a live secret → rotate it, check its use, then `git filter-repo`, a forced push and re-clones. A false positive → its fingerprint in `.gitleaksignore`. Prevent → a pre-commit hook plus a CI job.

### sops / age — keep secret values encrypted in Git, and control who can decrypt them
Match: sops, age, age-keygen
Instead of: plaintext secrets in Git, a shared password file
Safety: `-d` only prints · changes state: `-e -i` rewrites the file encrypted, `edit` re-encrypts on save, `updatekeys` changes who can decrypt; `age-keygen -o` writes a private key that must never be committed · `sops -d > FILE` leaves plaintext on disk

**In one line:** sops encrypts only the values of YAML, JSON, ENV or INI files (keys stay readable for diffs) for the recipients in `.sops.yaml`; age supplies their key pairs.

**Read the command:** `sops -e -i secrets/prod.yaml`

| Part | Meaning |
|---|---|
| `-e` | encrypt, for the recipients of the first `.sops.yaml` rule whose `path_regex` matches |
| `-i secrets/prod.yaml` | in place: overwrite this file instead of printing to stdout |
| `-d FILE` / `edit FILE` | decrypt to stdout (pipe it, never redirect it into the repository) / edit in `$EDITOR`, re-encrypted on save |
| `updatekeys FILE` | re-encrypt the file's data key for the recipients now in `.sops.yaml` |
| `age-keygen -o FILE` | **changes state**: a key pair; FILE holds the private key, the `age1…` public key goes into `.sops.yaml` |

**What the output tells you:**

```
db_password: ENC[AES256_GCM,data:Yp7n2T0kQ8vGx1sA2w==,iv:…,tag:…,type:str]
sops:
    age:
        - recipient: age1ql3z7hjy…
```

Key names stay visible, so a merge request shows "db_password changed" without the password; the `sops:` block lists who can decrypt. With one recipient, losing that key loses the secrets.

**Why it is effective:** secrets live next to their config, versioned and reviewable, while a leaked repository or CI log shows only ciphertext.

**Compared with plaintext in Git:** simple and diffable, but every clone, fork and backup keeps the secret for ever.

**Trap:** `Error getting data key: 0 successful groups required, got 0`: your key is not a recipient, or sops cannot find it (`SOPS_AGE_KEY_FILE`). A new recipient decrypts nothing until `updatekeys`; a removed one keeps what they decrypted, so rotate the values. Older releases spell `sops edit` as `sops FILE`.

**Next step:** CI → its private key as a protected File variable named by `SOPS_AGE_KEY_FILE`. Recipients change → edit `.sops.yaml`, then `sops updatekeys` each file. Short-lived, audited secrets → Vault or OpenBao.

### vault kv — read or write a secret, and see the API path behind it
Match: vault kv, bao kv
Instead of: secrets in .env files or CI variables
Safety: read-only for `get` and `-output-curl-string` · changes state: `put` writes a new version of the whole secret (KV v2 keeps older versions) · values typed on the command line end up in shell history

**In one line:** `vault kv` (or `bao kv`) reads and writes key/value secrets; on KV version 2 every write is a new version, and the CLI path `secret/shop/db` is the API path `secret/data/shop/db`, which policies name.

**Read the command:** `vault kv get -mount=secret shop/harbor`

| Part | Meaning |
|---|---|
| `kv get` | read the latest version of a secret (`-version=N` for an older one) |
| `-mount=secret shop/harbor` | the engine's mount, then the path inside it (same as `secret/shop/harbor`) |
| `-field=password` | print only this value, for a pipe into `docker login --password-stdin` |
| `kv put … password='…'` | **changes state**: write all fields as a new version; fields you leave out are dropped |
| `-output-curl-string` | print the equivalent curl request instead of sending it: the real API path |

**What the output tells you:**

```
=== Secret Path ===
secret/data/shop/harbor
======= Metadata =======
version            3
====== Data ======
password    REPLACE_ME
user        robot$shop+gitlab-ci
```

`Secret Path` shows the `data/` the CLI inserted: a policy on `secret/shop/*` matches nothing; reading needs `secret/data/shop/*`, listing `secret/metadata/shop/*`. `version 3`: older versions still exist.

**Why it is effective:** the 403 on a path the policy "obviously" allows is the classic KV v2 mistake, and this output names the path the policy needs; `-field` passes one value on without a file.

**Compared with `.env` files and CI variables:** no server needed, but whoever has the file or project has every secret, unaudited and rarely rotated; Vault adds short-lived tokens, policies and an audit trail.

**Trap:** `kv put` replaces every field (`kv patch` changes one). A value typed after `password=` stays in shell history; `password=@FILE` reads it from a file. `permission denied` can also mean an expired token; KV version 1 mounts have no `data/`.

**Next step:** 403 → `vault token capabilities secret/data/PATH`, `vault token lookup`, then fix the policy. Sealed → the `vault / bao` card. CI → log in with the job's ID token (`vault write auth/jwt/login …`).

### vault / bao — is the server sealed, who may do what, and is every request audited?
Match: vault, bao
Instead of: curl /v1/sys/health, restarting the container
Safety: read-only for `status`, `token lookup`, `token capabilities`, `audit list` and `operator raft list-peers` · changes state: `operator init` and `unseal`, `policy write`, `auth enable`, `secrets enable`, `audit enable`, `write auth/…` and `token create`/`revoke` act at once · `server -dev` is an in-memory lab server with a known root token: never production

**In one line:** the `vault` CLI (OpenBao: `bao`) talks to the server on port 8200: seal state, unsealing, the policies and auth roles that decide who reads what, and audit devices.

**Read the command:** `vault status`

| Part | Meaning |
|---|---|
| `status` | seal state, storage, HA role; exit 0 = unsealed, 2 = sealed, 1 = error |
| `operator unseal` | **changes state**: enter one key share; repeat until the threshold is reached |
| `operator init -key-shares=5 -key-threshold=3` | **changes state**: once per cluster: 5 key shares, any 3 unseal, plus a root token |
| `policy write shop-ci -`, `auth enable jwt` | **changes state**: a policy from stdin / GitLab job logins |
| `token lookup`, `token capabilities PATH` | your token's policies and TTL / what it may do on one API path |
| `audit list -detailed`, `operator raft list-peers` | audit devices and where they write / cluster members and the leader |

**What the output tells you:**

```
Key                Value
---                -----
Seal Type          shamir
Sealed             true
Total Shares       5
Threshold          3
Unseal Progress    0/3
Storage Type       raft
```

`Sealed true` at `0/3`: the server restarted and nobody has unsealed it, so clients get `503 Vault is sealed` until three key holders run `operator unseal`. Exit code 2 makes this a monitoring probe.

**Why it is effective:** a sealed server, a token or policy problem and failed audit devices all look like "the app cannot read its secrets"; these commands rule each out in seconds.

**Compared with `curl /v1/sys/health` and a restart:** health returns status codes (200 active, 429 standby, 501 not initialized, 503 sealed) for load balancers, without threshold or progress; a restart just seals it again.

**Trap:** with the default Shamir seal every restart (reboot, recreated container, OOM kill) seals it: plan auto-unseal or a runbook, and keep key shares off the host. If every audit device fails (a full disk), Vault refuses every request. `server -dev` runs in memory, unsealed, over HTTP: labs only.

**Next step:** sealed → key holders run `operator unseal`, then plan auto-unseal (transit, KMS). 403 → the `vault kv` card. Every request fails → `audit list -detailed`, the audit disk. After setup → `token revoke -self` on the root token.
