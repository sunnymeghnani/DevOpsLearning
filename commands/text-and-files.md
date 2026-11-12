# Reading output: text, files & JSON

Many commands in this handbook end in a pipe into one of these tools: they turn a million log lines or a page of JSON into the five lines that answer your question. Work in this order: pick the right files and lines (`find`, `ls`, `zgrep`, `tail`, `grep`), cut out the field you need (`awk`, `cut`, `jq`), then count and rank (`sort | uniq -c | sort -rn`, `wc`). Before you change anything, keep evidence with `tee`, `tar`, `diff` and `sha256sum`.

| If you would reach for | Prefer | Because |
|---|---|---|
| `cat` on a big log, or opening it in an editor | `tail -n 200`, `less +G`, `grep -n` | they read only the part you need; cat floods the screen and an editor loads gigabytes |
| `tail -f /var/log/app.log` | `tail -F /var/log/app.log` | after logrotate, `-f` keeps watching the renamed old file; `-F` reopens the new one |
| `grep PATTERN access.log` | `zgrep -h PATTERN access.log*`, `zcat -f access.log*` | most of the history sits in the rotated `.1` and `.gz` files |
| `uniq -c` on unsorted lines | `sort`, then `uniq -c`, then `sort -rn` | uniq merges only neighbouring duplicates |
| `cut -d' ' -f2` on `ps`, `df` or `ss` output | `awk '{print $2}'` | cut treats every single space as a separator; awk splits on runs of blanks |
| `sudo echo line > /etc/file` | `echo line`, piped into `sudo tee -a /etc/file` | the `>` is opened by your own shell, without root |
| `grep '"Status"'` on `docker inspect` output | `jq -r '.[0].State.Status'` | jq follows the JSON structure; grep only sees lines |
| `sed -i 's/…/…/' FILE` straight away | the same `sed` without `-i` as a preview, then `sed -i.bak`, then `diff -u` | you see the effect first, keep a backup and prove what changed |

### grep — which lines match, in which file and line, and how many?
Match: grep, egrep
Instead of: egrep, fgrep
Safety: read-only · configs and logs under /etc and /var/log often need sudo or the adm group

**In one line:** `grep` prints the lines matching a pattern, in files or a whole tree, with file name and line number: "where is this configured or logged?" in one command.

**Read the command:** `sudo grep -RniE 'ServerName|ServerAlias|ProxyPass|SetHandler|DocumentRoot|CustomLog' /etc/apache2/sites-enabled/`

| Part | Meaning |
|---|---|
| `-R` | recursive, following symlinks: `sites-enabled` holds symlinks, which `-r` skips |
| `-n` · `-i` | line numbers · ignore case |
| `-E` | extended regex: alternatives (a bar between the words), `+`, `?`, `{5}`, groups |
| `-v` · `-c` | lines that do **not** match · only the number of matching lines |
| `-B 3 -A 10` | 3 lines of context before and 10 after each hit |
| `-o` · `-h` · `-F` | only the matched text · no file names · fixed string (a dot is a dot) |

**What the output tells you:**

```
/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:3:    ServerName api.example.com
/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:7:    ProxyPass / http://127.0.0.1:3000/
/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:10:  CustomLog ${APACHE_LOG_DIR}/shop_access.log combined
```

`file:line:text` per hit, each with the place to open next. Exit status: 0 = matched, 1 = no match, 2 = error (unreadable file, bad regex).

**Why it is effective:** one pass over many files with exact locations; `-v` strips noise (`grep -viE "$NOISE"` drops monitors and bots) and `-o` feeds a ranking: `grep -oE 'AH[0-9]{5}' error.log | sort | uniq -c | sort -rn`.

**Compared with `egrep` / `fgrep`:** old names for `grep -E` and `grep -F`; GNU grep 3.8 and later warns that they are obsolescent.

**Trap:** `.` matches any character (`127.0.0.1` matches `127x0y0z1`: use `-F`), and `grep ':80'` matches `:8080`. `-c` counts lines, not occurrences. Behind `tail -f`, grep buffers what it passes down the pipe: add `--line-buffered`. Under `set -e`, a grep that finds nothing ends the script.

**Next step:** hit in a log → read around it (`-B`/`-A`), then rank with `sort | uniq -c`. Nothing found → right files? (rotated `.gz` → `zgrep`; symlinks → `-R`; case → `-i`). JSON → `jq`.

### zgrep / zcat — search and read rotated, compressed logs without unpacking them
Match: zgrep, zcat, zless
Instead of: grep, gunzip
Safety: read-only · /var/log/apache2 and auth.log need sudo or the adm group

**In one line:** logrotate compresses old logs (`.2.gz` … `.14.gz`), so most history is gzip data that plain grep cannot read; `zgrep` searches it and `zcat -f` streams plain and compressed files alike into a pipeline.

**Read the command:** `zcat -f /var/log/apache2/other_vhosts_access.log* | awk '{print $1}' | sort | uniq -c | sort -rn`

| Part | Meaning |
|---|---|
| `zcat` | decompress to stdout (same as `gunzip -c`); the `.gz` files stay untouched |
| `-f` | pass uncompressed files (the live log, `.log.1`) through instead of rejecting them |
| `other_vhosts_access.log*` | every rotation: the live file, `.1`, `.2.gz` … `.14.gz` |
| `awk`, `sort`, `uniq -c`, `sort -rn` | field 1 (`vhost:port` in this format), counted and ranked |
| `zgrep -h 'Failed password' /var/log/auth.log*` | grep through every rotation; `-h` drops file names, and any grep flag works |

**What the output tells you:**

```
 182340 app1.example.com:443
  20311 app2.example.com:443
     14 legacy.example.com:443
```

Requests per vhost over all retained days (14 for Ubuntu's Apache logs): 14 hits in two weeks is a monitor or a bot, not users.

**Why it is effective:** the live file often covers only the hours since midnight. Reading every rotation turns "nothing in the log" into a real answer, without unpacking files onto a disk that may already be full.

**Compared with `grep`:** fine for the live file; on a `.gz` it searches compressed bytes and finds nothing. `gunzip` writes each file out at full size and removes the `.gz`.

**Trap:** the glob sorts by name (`.10.gz` before `.2.gz`): when time order matters, feed files oldest first with `for f in $(ls -tr FILE*); do zcat -f "$f"; done`. Without `-f`, zcat skips the plain files (`not in gzip format`), losing the newest lines.

**Next step:** spike or top talker → narrow by time with `awk` on the timestamp. History too short → raise `rotate` in `/etc/logrotate.d/`, or ship logs to Loki or Elasticsearch. Related: `zless FILE.gz` pages through one compressed file as `less` would.

### tail — the newest lines of a log, and following it live across rotations
Match: tail, multitail
Instead of: cat, tail -f
Safety: read-only · system logs need sudo or the adm group

**In one line:** `tail` prints the end of a file or stream, where the newest log lines are; with `-F` it keeps printing new lines as they arrive, even after logrotate replaces the file.

**Read the command:** `tail -F /var/log/app.log`

| Part | Meaning |
|---|---|
| `-F` | follow by **name** and retry: reopen the file after a rotation, or when it appears later |
| `-f` | follow the open file: after a rename it keeps reading the old, now silent one |
| `-n 200` · `-n +2` | the last 200 lines (default 10) · everything from line 2, skipping a header |
| several files | each block is headed `==> FILE <==` |
| `--pid=PID` | with `-f`, stop when that process exits (`timeout 30 tail --pid=PID -f /dev/null` waits for a stop) |

**What the output tells you:**

```
2026-10-03T09:14:02Z ERROR db timeout after 5000 ms
tail: '/var/log/app.log' has been replaced;  following new file
2026-10-03T09:14:05Z INFO  pool reconnected
```

`has been replaced` is logrotate creating a new file (`file truncated`: a copytruncate rotation). With `-f` the screen would go quiet here and the app would look idle.

**Why it is effective:** in an incident the newest lines matter, and tail reads only the end of the file, so a 5 GB log answers instantly.

**Compared with `cat`:** a log floods the screen. **Compared with `tail -f`:** identical until the first rotation, then stuck on the renamed file (`app.log.1`).

**Trap:** last written is not most relevant: on a busy log, health checks push your error out of the last 10 lines. `tail -f … | grep X | awk …` looks dead because grep buffers (`--line-buffered`). A journal-only service has no file to tail.

**Next step:** error seen → `grep -n` it and read around it (`less +G`). Journal-only → `journalctl -u UNIT -f`. Container → `docker logs -f --tail 50 NAME`. Nothing new at all → where does it write? `ls -l /proc/PID/fd`. Related: `multitail /var/log/nginx/*.log` (if installed) follows several files in split windows.

### head — the first lines of files, or the top N of a ranking
Match: head
Instead of: cat
Safety: read-only

**In one line:** `head` prints the start of each file or stream, then stops; after `sort` it turns a ranking into "the top 5".

**Read the command:** `sudo head -n 5 /etc/apache2/sites-available/*.conf | grep -E '^==>|#'`

| Part | Meaning |
|---|---|
| `-n 5` | the first 5 lines of each file (`head -5` is the old short form; default 10) |
| `sites-available/*.conf` | several files: head writes `==> FILE <==` before each one |
| the `grep -E` after the pipe | keeps only those headers and `#` comments: who set up each vhost, and why |
| `-c 512` | the first 512 bytes instead of lines (a binary, or JSON on one huge line) |

**What the output tells you:**

```
==> /etc/apache2/sites-available/intranet.example.com.conf <==
# Intranet v1 - HR team (contact: hr-it@example.com) - legacy, replaced by SaaS 2024?
==> /etc/apache2/sites-available/shop.example.com.conf <==
```

A comment naming a team, a ticket or a date is inventory evidence; a header with nothing under it means no comment at the top.

**Why it is effective:** head stops reading once it has its lines, so a 5 GB file costs nothing, and `sort -rn | head -5` is "top 5" in two commands.

**Compared with `cat`:** cat prints everything: fine for one short file, while 30 vhost files or a log bury the answer.

**Trap:** head of an unsorted stream gives the first lines, not the biggest: sort first. When head exits early, the command feeding it gets SIGPIPE, so under `set -o pipefail` the pipeline can return 141 and look like a failure.

**Next step:** need the end → `tail`. Need to search → `less`. No comments → continue the owner hunt with `stat`, `git log` and the CMDB.

### less — page through a big file, search it, read a script before running it
Match: less
Instead of: cat, vim
Safety: read-only (pressing `v` opens the file in an editor)

**In one line:** `less` shows a file one screen at a time and reads only what it displays: a multi-gigabyte log opens instantly, and you can search, jump to the end or follow new lines.

**Read the command:** `less +F file.log`

| Part | Meaning |
|---|---|
| `+F` | start in follow mode like `tail -f`; **Ctrl-C** stops following to scroll and search, **F** resumes |
| `+G` · `g` · `G` · `q` | start at the end · jump to the start · to the end · quit |
| `/text` · `?text` · `n` · `N` | search forward · backward · next hit · previous hit |
| `&text` | show only matching lines, a live grep; `&` alone shows all lines again |
| `-S` · `-N` | chop long lines instead of wrapping · show line numbers |

**What the output tells you:** the bottom line is the prompt: the file name or `:` while browsing, `(END)` at the end of the file, a "waiting for data" message while following, `Pattern not found` after a failed search.

**Why it is effective:** an editor loads the whole file, can choke on 2 GB and can change it; less starts instantly and only reads. `less dokploy-install.sh` before running it as root is the minimum review of an installer.

**Compared with `cat`:** fine for 30 lines; beyond that the start scrolls away and there is no search. **Compared with `vim`:** vim can edit, the very risk on a live log or config.

**Trap:** without `+F` you see the file as it was when opened (press `G` again for new lines). `.gz` rotations need `zless`: plain less unpacks them only through a `LESSOPEN` helper, which `sudo` drops.

**Next step:** error found → note its time, then `journalctl --since … --until …` or `grep -B3 -A10` around it. Only new lines needed → `tail -F`.

### cat — print a small file whole: /proc and /sys values, configs, scripts
Match: cat
Instead of: —
Safety: read-only · `sudo cat` reads root-only files · a `cat > FILE` redirect overwrites FILE

**In one line:** `cat` copies files to the screen unchanged: right for the kernel's tiny generated files in `/proc` and `/sys` and for short configs, wrong for logs.

**Read the command:** `cat /proc/loadavg`

| Part | Meaning |
|---|---|
| `/proc/loadavg` | generated by the kernel when read: size 0 in `ls`, content in `cat` |
| `cat /sys/fs/cgroup/system.slice/app.service/cpu.max` | the unit's cgroup v2 CPU limit |
| `sudo cat FILE` | the reading runs as root (a `<` redirect would run as you) |
| `cat -A FILE` | show the invisible: tab `^I`, Windows line end `^M$` |

**What the output tells you:**

```
$ cat /proc/loadavg
7.82 5.10 2.31 9/412 51022
$ cat /sys/fs/cgroup/system.slice/app.service/cpu.max
50000 100000
```

loadavg: the 1-, 5- and 15-minute load, runnable/existing scheduling entities (9 running or waiting for a CPU, 412 in total), then the newest PID. cpu.max: 50 000 µs of CPU per 100 000 µs, half a CPU (`CPUQuota=50%`); `max 100000` means no limit.

**Why it is effective:** `/proc` and `/sys` are the kernel answering directly, and they work in minimal containers and rescue shells where `ps` or `systemctl` are missing.

**Trap:** on a big log cat floods the terminal; on a binary it can garble it (`reset` repairs that). `cat FILE | grep x` is one process too many (ShellCheck SC2002). `/proc` values are snapshots: read twice to see a rate.

**Next step:** a log → `tail -n 200`, `less +G`, `grep`. Invisible characters → `file`, `od -c`. Many small files → `grep -H . FILES` prints one `file:value` line each.

### awk — pick fields, filter rows by value, count or sum per key
Match: awk
Instead of: cut -d' '
Safety: read-only (a program can still write with `print > FILE` or run commands with `system()`)

**In one line:** `awk` splits each line into fields `$1 … $NF` and runs `condition { action }` on the matching lines; arrays and an `END` block give per-key counts and sums in one pass.

**Read the command:** `awk '$9 >= 500 {print $4, $7, $9}' /var/log/apache2/access.log | tail -5`

| Part | Meaning |
|---|---|
| `'…'` | single quotes, so the shell leaves `$9` alone |
| `$9 >= 500` | condition: field 9, the HTTP status, is 500 or more; a condition alone prints the line |
| `{print $4, $7, $9}` | action: timestamp, path and status (`tail -5` then keeps the last five) |
| `-F:` | split on `:`: `awk -F: '$3==0' /etc/passwd` lists every UID-0 account |
| `$NF` · `NR > 1` · `{c[$1]++} END {for (k in c) print c[k], k}` | last field · skip the header line · count per key, printed at the end |

**What the output tells you:**

```
[03/Oct/2026:09:14:41 /v1/orders 502
[03/Oct/2026:09:14:44 /v1/orders 502
[03/Oct/2026:09:15:02 /checkout 503
```

The latest server errors with time and URL: one endpoint failing since 09:14 points at its backend, every URL failing points at the proxy or the app.

**Why it is effective:** it splits on runs of blanks the way you read columns, so logs, `ps`, `df` and `ss` work without counting characters, and filtering, counting and summing happen in one pass.

**Compared with `cut -d' '`:** fine for one-character separators (`:` in `/etc/passwd`), but each extra space becomes an empty field, and cut cannot filter or sum.

**Trap:** fields depend on the format: `other_vhosts_access.log` puts `vhost:port` first, so the status is `$10`, and a malformed request line shifts everything. Ubuntu's awk is mawk, without gawk extras such as `strtonum`. In double quotes the shell eats `$9`.

**Next step:** rank → `sort | uniq -c | sort -rn`. When did it start → `awk '{print substr($4, 2, 17)}' LOG | uniq -c` counts per minute. Unknown format → `head -3 FILE` and count the fields.

### sort / uniq — what is most frequent, biggest, or duplicated?
Match: sort, uniq, shuf
Instead of: uniq -c without sort
Safety: read-only · `sort -o FILE` writes FILE

**In one line:** `sort` orders lines (text, numbers, human sizes, month names) and `uniq` collapses identical **neighbouring** lines; `sort | uniq -c | sort -rn` is the "top N" behind most log answers.

**Read the command:** `awk '{print $9}' /var/log/apache2/access.log | sort | uniq -c | sort -rn`

| Part | Meaning |
|---|---|
| `awk '{print $9}'` | the status code of each request |
| `sort` | brings equal values together, which uniq needs |
| `uniq -c` | one line per run of equal lines, prefixed with its count |
| `sort -rn` | numeric, reversed: biggest count first |
| `sort -rh` | human sizes (`2G` above `512M`), the partner of `du -sh` |
| `sort -t/ -k3,3n -k2,2M -k1,1n` | split on `/`, sort by year, month name, day: `03/Oct/2026` dates in order |
| `uniq -d` · `sort -u` | only repeated lines · sort and drop duplicates |

**What the output tells you:**

```
  18342 200
   2210 304
    731 404
     96 502
     12 500
```

Count, then value. 96 × 502 means Apache got no valid answer from a backend: compare with yesterday's file before calling it new.

**Why it is effective:** "the log looks bad" becomes numbers for a ticket (status mix, top IPs, URLs, error codes), from any field of any text.

**Compared with `uniq -c` alone:** it merges only adjacent lines, so on unsorted input the same value appears many times with small counts.

**Trap:** without `-n`, `100` sorts before `20`; `-n` reads `2G` as 2 (use `-h`). The locale changes the order (`LC_ALL=C` is byte order, and faster). sort reads all input before printing, so it never works behind `tail -f`.

**Next step:** one value dominates → filter it (`awk '$9 == 502'`) and look at the times. Unknown top client → reverse DNS, `whois`, the CMDB. Related: `shuf` shuffles lines: `shuf -n 5 FILE` picks five at random, `shuf -i 1-20 -n 1` one number from 1 to 20.

### wc — how many lines, words or bytes?
Match: wc
Instead of: —
Safety: read-only

**In one line:** `wc` counts lines, words and bytes; `wc -l` at the end of a filter turns any listing into one number you can compare.

**Read the command:** `ss -Htn state established '( sport = :443 )' | wc -l`

| Part | Meaning |
|---|---|
| `ss -Htn state established '( sport = :443 )'` | one line per live TCP connection to local port 443 (see the `ss` card) |
| `-H` | no header line, so the count is not one too high |
| `wc -l` | count newline characters, i.e. lines |
| `wc -l < FILE` | the number alone (`wc -l FILE` prints `12 FILE`) |
| `-c` · `-w` · `-m` | bytes · words · characters (not bytes: they differ in UTF-8) |

**What the output tells you:** one number, for example `18`: eighteen connections right now. Sampled in a loop or with `watch -n 2 "…"`, it shows whether traffic drains after a DNS move or climbs during an attack.

**Why it is effective:** numbers compare (before and after a change, host A and host B) faster and more honestly than two screens of lines.

**Trap:** a header (`ps`, `docker ps`, `ss` without `-H`) adds one, and a last line without a trailing newline is not counted. `grep PATTERN FILE | wc -l` equals `grep -c PATTERN FILE`. Host-side `ss` misses connections Docker DNAT-ed into a container.

**Next step:** more than expected → see *who*: `awk` the client column, then `sort | uniq -c | sort -rn`. Zero → test the filter on a few lines (`… | head`) before trusting it.

### cut / tr — keep fields by one delimiter; translate, squeeze or delete characters
Match: cut, tr
Instead of: —
Safety: read-only

**In one line:** `cut` keeps chosen fields of each line, split on one delimiter character (or chosen character positions); `tr` replaces, squeezes or deletes single characters in a stream.

**Read the command:** `tr '\0' ' ' < /proc/2210/cmdline; echo`

| Part | Meaning |
|---|---|
| `'\0' ' '` | replace each NUL byte (the kernel's separator between arguments) with a space |
| `< /proc/2210/cmdline` · `; echo` | tr reads only stdin · add the missing final newline |
| `tr -d '\r'` · `tr -s ' '` · `tr ',' '\n'` | delete carriage returns · squeeze runs of spaces · one item per line |
| `cut -d: -f1,7 /etc/passwd` | fields 1 and 7 (user, shell) of a `:`-separated file |
| `cut -d= -f2` · `cut -c1-12` | the value of `KEY=value` · characters 1–12 (a short container ID) |

**What the output tells you:**

```
$ tr '\0' ' ' < /proc/2210/cmdline; echo
node /srv/crm/server.js
$ cut -d: -f1,7 /etc/passwd | grep -v nologin
root:/bin/bash
deploy:/bin/bash
```

The exact command line the process started with, and the accounts with a real login shell.

**Why it is effective:** both are tiny and predictable inside scripts and `$( )`, and tr fixes `/proc` formats and Windows line ends in one step.

**Trap:** cut takes one delimiter character and counts every single space, so on space-aligned output (`ps`, `df`, `ss`) fields come out empty: use `awk '{print $2}'`, or `tr -s ' '` first. tr maps characters, not strings: `tr 'abc' 'xyz'` turns each `a` into `x`. `cut -d= -f2` truncates a value that contains `=` (use `-f2-`).

**Next step:** conditions or sums → `awk`. JSON → `jq`. A process's environment → `sudo cat /proc/PID/environ | tr '\0' '\n'`, minus secrets before you share it.

### sed — print a range of lines, or change a config file reproducibly
Match: sed
Instead of: the same hand edit in an editor on every server
Safety: read-only without `-i` · changes state: `-i` rewrites the file in place (as a new file)

**In one line:** `sed` edits a stream line by line: print only a range (`-n '…p'`) or substitute text (`s/old/new/`); with `-i` it writes back into the file, a config change you can review and repeat.

**Read the command:** `sudo sed -i.bak 's/^PORT=3000$/PORT=3001/' /opt/api/.env`

| Part | Meaning |
|---|---|
| `-i.bak` | edit in place, keeping the original as `/opt/api/.env.bak` |
| `s/OLD/NEW/` | replace the first match on each line |
| `^PORT=3000$` | anchored: exactly `PORT=3000`, never `PORT=30000` or `EXPORT=3000` |
| `s#127\.0\.0\.1:3000#127.0.0.1:3001#g` | another delimiter when the text holds `/`; `\.` a literal dot; `g` every match on the line |
| `sed -n '1,25p'` · `sed -n '/09:14/,/09:16/p'` | print only lines 1–25 · only from the first `09:14` line to the next `09:16` line |

**What the output tells you:** `-i` prints nothing; prove the edit with `diff -u /opt/api/.env.bak /opt/api/.env`, whose hunk reads:

```
@@ -1,3 +1,3 @@
 NODE_ENV=production
 DB_HOST=127.0.0.1
-PORT=3000
+PORT=3001
```

One changed line is what you meant; dozens mean the pattern matched more than you thought.

**Why it is effective:** the change is a command: reviewed once, repeated identically on five servers, pasted into the change request, with the backup made in the same step. Without `-i` it is a harmless preview.

**Trap:** `-i` writes a **new file** and renames it over the old: a symlink becomes a regular file (GNU sed: `--follow-symlinks`), and a file bind-mounted into a container keeps its old content until the container restarts. Without a suffix there is no backup: preview without `-i` first.

**Next step:** preview right → `-i.bak`, `diff -u`, config test (`apache2ctl configtest`, `nginx -t`), then reload. Range runs to the end → the end pattern never matched. YAML or JSON → `yq` or `jq`, not a regex.

### jq / yq — pick values out of JSON (and YAML) by their path
Match: jq, yq
Instead of: grep on JSON
Safety: read-only · acme.json is root-only (mode 600) and holds private keys: never paste it

**In one line:** `jq` parses JSON and prints exactly the values you name by path (`.key.sub[]`), keeps the items you `select()`, and reshapes them into lines or tables; `yq` does the same for YAML.

**Read the command:** `sudo jq -r '.letsencrypt.Certificates[].domain.main' /etc/dokploy/traefik/dynamic/acme.json`

| Part | Meaning |
|---|---|
| `-r` | raw strings without JSON quotes, ready for `sort` or loops |
| `.letsencrypt` | top-level key of Traefik's certificate store: the resolver's name |
| `.Certificates[]` · `.domain.main` | `[]` iterates over the array · then the field inside each element |
| `.[0]` · `keys` · `length` | first element (`docker inspect` returns an array) · key names · count |
| `select(.State.Status != "running")` · `.x // "none"` | keep only matching items · fallback when a value is null or missing |
| `yq '.db_host' FILE` | the same path on YAML (two different tools are called yq: check `yq --version`) |

**What the output tells you:**

```
dokploy.example.com
app.example.com
shop.example.com
```

Every name Traefik holds a Let's Encrypt certificate for. A domain with a router but missing here was never issued: look for `acme` errors in `docker logs dokploy-traefik`.

**Why it is effective:** Docker, Kubernetes, the Traefik API, `ip -j` and the AWS CLI all speak JSON; jq follows the structure, so the answer stays right however the text is laid out, and `@tsv` turns it into columns.

**Compared with `grep`:** grep finds the line with `"main"` but not the object it belongs to, and on minified JSON (one line) it returns everything.

**Trap:** `Cannot index array with "x"` means you skipped a level: add `.[]` or `.[0]`. A wrong path prints `null`, not an error. `parse error: Invalid numeric literal` means the input is not JSON (an HTML error page, a log line).

**Next step:** a certificate's dates → `select(.domain.main=="app.example.com") | .certificate`, then `base64 -d` into `openssl x509 -noout -enddate`. Unknown structure → `jq 'keys'`, one level at a time.

### base64 — read a Kubernetes secret value or any encoded blob
Match: base64
Instead of: —
Safety: read-only · the decoded output is the secret itself: keep it out of tickets, chat and shell history

**In one line:** base64 writes any bytes as letters, digits, `+`, `/` and `=`, so certificates and secrets survive JSON and YAML; `base64 -d` turns them back and shows what a pod really receives.

**Read the command:** `kubectl get secret mysecret -n app -o jsonpath='{.data.password}' | base64 -d`

| Part | Meaning |
|---|---|
| `get secret mysecret -n app` | the Secret object `mysecret` in namespace `app` |
| `-o jsonpath='{.data.password}'` | only the encoded value of its key `password` |
| `base64 -d` · `base64 -d > FILE` | decode to stdout · straight into a file (a certificate, an AWS report) |
| `base64 -w 0` | encode on one line; GNU base64 wraps at 76 characters otherwise |
| `printf '%s' 'value'` into `base64` | encode without the newline that `echo` adds |

**What the output tells you:**

```
$ kubectl get secret mysecret -n app -o jsonpath='{.data.password}' | base64 -d | od -c
0000000   e   x   a   m   p   l   e  \n
0000010
```

A clean value ends with no newline (the next prompt sticks to it). Here `od -c` shows `\n`: the secret was made with `echo`, not `echo -n`, so the login fails although "the password is right".

**Why it is effective:** `kubectl describe secret` shows only sizes, so a stray newline or space stays hidden; decoding shows the exact bytes.

**Trap:** base64 is encoding, not encryption: whoever can read the Secret (or an unencrypted etcd backup) has the value. Without `-w 0`, long values wrap and break YAML. `base64: invalid input` usually means the whole JSON, line breaks, or URL-safe base64 (`-` and `_`).

**Next step:** wrong value → recreate it with `--from-literal` (no newline), then `kubectl rollout restart`, since env vars do not reload. Who can read secrets → `kubectl auth can-i get secrets`. Real protection → encryption at rest, Vault.

### column / paste / numfmt — aligned columns, one joined line, human-readable sizes
Match: column, paste, numfmt, fold
Instead of: —
Safety: read-only

**In one line:** three formatters for the end of a pipe: `numfmt` turns byte counts into `4.0G`, `column -t` aligns fields into a table, and `paste -sd,` joins many lines into one.

**Read the command:** `sudo find /var -xdev -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -5 | numfmt --field=1 --to=iec`

| Part | Meaning |
|---|---|
| `find … -printf '%s\t%p\n' 2>/dev/null` | size in bytes, a tab, the path; errors hidden (see `find`) |
| `sort -rn`, `head -5` | the five biggest |
| `numfmt --field=1 --to=iec` | field 1 in powers of 1024: `4294967296` becomes `4.0G` (`--to=iec-i`: `4.0Gi`) |
| `column -t` · `-s "$TAB"` · `-s,` | align fields into columns · split on tabs only · on commas (CSV, HAProxy stats) |
| `paste -sd, -` | join all lines from stdin (`-`) into one, comma-separated |

**What the output tells you:**

```
4.0G    /var/lib/docker/overlay2/9c1e…/diff/data/db.dump
1.2G    /var/log/journal/3f2a…/system@0006…journal
512M    /var/lib/mysql/ibdata1
```

The biggest files under `/var`, readable at a glance: the L0 exit-test question in one line.

**Why it is effective:** the data was already there; these make it readable and paste-able into a ticket, and `paste -sd,` builds the comma lists that options and SQL `IN (…)` expect.

**Trap:** `column` reads all input before printing, so it cannot follow a live stream, and a separator inside a value (a comma in a quoted CSV field) breaks the alignment. `paste -d ', '` uses comma and space in turn, not as one two-character separator. numfmt stops at a non-number such as a header unless you add `--header`.

**Next step:** directories instead of files → `du -xh --max-depth=1 /var | sort -rh`. Filter rows first → `awk`, then `column -t`. Related: `fold -s -w 100` wraps long lines at 100 characters, breaking at spaces.

### find — which files are big, old, new, or owned by the wrong user?
Match: find
Instead of: ls -R
Safety: read-only · changes state: `-delete` and `-exec rm` remove every match at once, and `-delete` must come last

**In one line:** `find` walks a tree and selects files by type, size, age, name, owner or permissions: "what filled the disk?" and "what changed in the last hour?".

**Read the command:** `sudo find / -xdev -type f -size +1G`

| Part | Meaning |
|---|---|
| `/` · `-xdev` | start at `/`, stay on that filesystem: no `/proc`, `/sys`, other disks, NFS or container mounts |
| `-type f` · `-size +1G` | regular files · bigger than 1 GiB (sizes round up to the unit) |
| `-mtime +30` · `-mmin -60` | modified over 30 days ago · in the last 60 minutes |
| `-newermt "2026-08-08"` · `-perm -4000` · `! -user app` | changed since a date · setuid files · not owned by `app` |
| `-printf '%s\t%p\n'` · `2>/dev/null` | size and path, for `sort -rn` · hide `Permission denied` noise |
| `-delete` | delete the matches: last in the expression, after a `-print` preview |

**What the output tells you:**

```
/var/lib/docker/overlay2/9c1e…/diff/data/db.dump
/var/log/journal/3f2a…/system@0006…journal
/srv/backup/site-2026-09-01.tar.gz
```

Every file over 1 GiB on the root filesystem: a dump in `overlay2/…/diff` was written inside a container, not a volume; journal files mean the journal's size limit; a forgotten backup is the classic.

**Why it is effective:** `df` says the disk is full and `du` which directory; find names the files and filters by age in one pass, and `find /etc -xdev -type f -mmin -60` answers "what changed in the last hour?" after an incident.

**Compared with `ls -R`:** it lists everything with no size or age filter, and walks into `/proc` and network mounts.

**Trap:** ages count whole days with the fraction dropped: `-mtime +30` means at least 31 days. Sizes round up, so `-size -1G` matches only empty files. `-delete` before the tests deletes everything. A deleted file still held open frees nothing (`lsof +L1`).

**Next step:** big file → who writes it (`lsof FILE`), then rotate or remove it in a change. Nothing big but `/` full → `du -xh --max-depth=1 /`, `df -i`, `lsof +L1`. New setuid file → a security finding: `diff` against your baseline.

### ls — what is in this directory, newest first, with owner and mode
Match: ls
Instead of: —
Safety: read-only · root-only directories and other users' `/proc/PID/fd` need sudo

**In one line:** `ls -l` shows each entry's type, permissions, owner, group, size and modification time; `-t` sorts newest first, which shows the log being written right now.

**Read the command:** `ls -lt --time-style=long-iso /var/log/apache2/ | head -20`

| Part | Meaning |
|---|---|
| `-l` | long format: mode, link count, owner, group, size, time, name |
| `-t` · `-tr` | newest modification first · oldest first, for time-ordered loops |
| `--time-style=long-iso` | `2026-10-03 09:41` for every file, old or new |
| `-d` · `-h` · `-a` | the directory itself (`ls -ld /var/www`) · sizes like `1.7G` · dot files too |
| `ls -l /proc/1201/fd` | a process's open files: each fd links to its file, socket or pipe |

**What the output tells you:**

```
total 25496
-rw-r----- 1 root adm 18234112 2026-10-03 09:41 api_access.log
-rw-r----- 1 root adm  6120448 2026-10-03 09:41 shop_access.log
-rw-r----- 1 root adm    91238 2026-10-03 09:40 intranet_access.log
```

`head -20` keeps the newest. First character: `-` file, `d` directory, `l` symlink. `rw-r-----` is owner, group, others: group `adm` may read, which is why the adm group reads Apache logs without sudo. A `+` after the mode means an ACL.

**Why it is effective:** time order answers "which log is live?" and "what changed last?" at a glance, and mode and owner explain most `Permission denied` errors before you touch anything.

**Trap:** the time is the **modification** time: reading does not change it, and a directory's time moves only when entries are added, removed or renamed. Sizes are apparent: a sparse VM image shows 100G while using 3G (`du -h`). Never loop over `ls` output (ShellCheck SC2045): use a glob.

**Next step:** permissions → `stat -c '%A %U:%G %n' FILE`, `namei -l PATH`. Who writes a file → `lsof FILE`. Space → `du -sh`, `find -size`.

### stat / readlink — exact owner, mode and times; where a link or a process really points
Match: stat, readlink
Instead of: ls -l
Safety: read-only · the `/proc/PID` links of other users' processes need sudo

**In one line:** `stat` prints a file's facts (owner, octal mode, size, timestamps) in the format you choose; `readlink` resolves a symlink, including a process's binary (`/proc/PID/exe`) and working directory (`/proc/PID/cwd`).

**Read the command:** `stat -c '%U:%G %y %n' /var/www/* /opt/api`

| Part | Meaning |
|---|---|
| `-c '…'` · `%n` | print only these fields, one line per file · the file name |
| `%U:%G` | owner and group names (`%u:%g`: numeric IDs, what a container or NFS sees) |
| `%y` · `%a` · `%A` | last modification, to the nanosecond · mode in octal (`640`) · as `ls` shows it |
| `stat -fc %T /sys/fs/cgroup` | `-f` = the filesystem: `cgroup2fs` means cgroup v2, `tmpfs` v1 |
| `readlink /proc/2210/exe` · `readlink -f /etc/resolv.conf` | a process's binary · follow every link to the final file |

**What the output tells you:**

```
root:root 2023-02-14 09:02:10.418220511 +0000 /var/www/docs
www-data:www-data 2026-10-01 11:20:44.731902118 +0000 /var/www/shop
$ readlink -f /etc/resolv.conf
/run/systemd/resolve/stub-resolv.conf
```

docs untouched since 2023, shop changed two days ago. resolv.conf belongs to systemd-resolved, so hand edits will not last. An `exe` link ending in `(deleted)` means the binary was replaced on disk and the process still runs the old one.

**Why it is effective:** one exact, script-friendly line per file with full timestamps and numeric modes: inventory and audit evidence instead of `ls` columns that round dates.

**Compared with `ls -l`:** the same owner and mode at a glance, but old files show only a date, and there is no filesystem type.

**Trap:** a directory's mtime moves only when entries are added, removed or renamed directly in it: a site whose PHP files change daily can keep an old directory date. Numeric IDs matter across containers and NFS: `www-data` is 33 on Ubuntu but 82 in Alpine images.

**Next step:** wrong owner or mode → `chown`/`chmod` in a change, `namei -l PATH`. `(deleted)` binary → restart its unit. cgroup v1 on a new host → check your Docker and Kubernetes versions first (Kubernetes keeps v1 only in maintenance mode).

### file / od — what is really in this file: text, CRLF, binary, a filesystem?
Match: file, od, strings, hexdump
Instead of: cat
Safety: read-only · `file -s` on a block device needs sudo

**In one line:** `file` names a file's content from its bytes, not its name (script, ELF binary, gzip, ext4 filesystem, or plain `data`); `od -c` prints every byte, so a hidden `\r` or trailing `\n` shows.

**Read the command:** `file docker-entrypoint.sh`

| Part | Meaning |
|---|---|
| `file FILE…` | what each file really is: `ASCII text`, `ELF 64-bit LSB pie executable`, `gzip compressed data` |
| `sudo file -s /dev/xvdf` | `-s` reads a block device: `data` = no filesystem yet; `ext4 filesystem data` = in use |
| `-L` | follow a symlink (by default file reports `symbolic link to …`) |
| `od -c` | each byte as a character or escape (`\r`, `\n`, `\0`); the first column is the offset, in octal |

**What the output tells you:**

```
$ file docker-entrypoint.sh
docker-entrypoint.sh: Bourne-Again shell script, ASCII text executable, with CRLF line terminators
$ head -c 12 docker-entrypoint.sh | od -c
0000000   #   !   /   b   i   n   /   b   a   s   h  \r
0000014
```

Saved on Windows: the kernel looks for an interpreter named `bash\r`, and the container dies with `exec /docker-entrypoint.sh: no such file or directory` although the file exists. od shows the culprit byte.

**Why it is effective:** CRLF line ends, a BOM, a trailing newline or a binary where text was expected are invisible in `cat` and editors, and the errors they cause point elsewhere. `file -s` before `mkfs` tells an empty volume from one holding data.

**Compared with `cat`:** cat hides `\r`; `cat -A` shows line ends as `^M$`, but not every byte.

**Trap:** file guesses from patterns: `data` means "not recognised", not "empty", and a partitioned disk shows only its partition table (check `/dev/xvdf1`, or `lsblk -f`).

**Next step:** CRLF → `sed -i 's/\r$//' FILE`, plus `*.sh text eol=lf` in `.gitattributes`. `data` on a new volume → `mkfs`; a filesystem → mount it, never format it. Related: `strings` prints the readable runs inside binary data (`etcdctl get … | strings` exposes an unencrypted Secret); `hexdump -C` shows offset, hex bytes and ASCII side by side.

### tee — keep a copy of the output, and write root-owned files through sudo
Match: tee
Instead of: sudo cmd > /root/file, sudo echo … > /etc/file
Safety: changes state: creates or overwrites every file it is given (`-a` appends)

**In one line:** `tee` copies its input to stdout **and** into files; as `sudo tee FILE` the writing runs as root, which a shell redirect after `sudo` does not.

**Read the command:** `sudo ss -tulpn | sudo tee /root/listeners-before-$(date +%F).txt >/dev/null`

| Part | Meaning |
|---|---|
| `sudo ss -tulpn` | the evidence: every listener with its process |
| `sudo tee FILE` | tee, fed by the pipe, runs as root, so it may write into `/root` |
| `$(date +%F)` | today's date in the name: `listeners-before-2026-10-03.txt` |
| `>/dev/null` · `-a` | do not echo it to the terminal · append instead of overwrite |
| `2>&1` before the pipe | capture errors too: `bash install.sh 2>&1` into `tee install.log` keeps the whole run |

**What the output tells you:** nothing on screen; `sudo ls -l /root/listeners-before-*` shows the file. After the change, capture again into an `-after` file and compare with `diff -u`.

**Why it is effective:** you see the output and keep a dated, root-owned copy in one step: how the handbook records the "before" state of every change.

**Compared with `sudo cmd > FILE`:** it works only where your own user may write: your shell opens the `>` before sudo starts, so in `/root` or `/etc` it fails with `Permission denied` (`sudo echo x > /etc/file` too). `sudo sh -c 'cmd > FILE'` works, but its extra quoting is easy to break.

**Trap:** without `-a`, tee empties the file first: one line piped into `sudo tee /etc/hosts` leaves a one-line hosts file. A pipeline returns tee's status, so `bash install.sh 2>&1 | tee log && next-step` continues after a failed install unless `set -o pipefail` (or check `${PIPESTATUS[0]}`).

**Next step:** installer failed under tee → read its log from the first error. Before and after differ → explain every line. Saved `environ` or `docker inspect` output → keep it root-only: it can hold secrets.

### diff — what exactly changed between two files, or since the baseline?
Match: diff
Instead of: comparing two files by eye
Safety: read-only

**In one line:** `diff` compares two files, or a file and a command's output, line by line and prints only the differences; `-u` gives the unified format Git and patches use.

**Read the command:** `diff -u /etc/apache2/ports.conf.bak /etc/apache2/ports.conf`

| Part | Meaning |
|---|---|
| `-u` | unified format: each change with 3 lines of context |
| first · second file | old · new: `-` lines exist only in the old, `+` lines only in the new |
| `diff baseline.txt -` · `diff <(CMD1) <(CMD2)` | a baseline against stdin · two commands' outputs (bash process substitution) |
| `-r` · `-w` · `--strip-trailing-cr` | directory trees · ignore whitespace · ignore Windows line ends |

**What the output tells you:**

```
--- /etc/apache2/ports.conf.bak	2026-10-03 10:31:02.118220511 +0000
+++ /etc/apache2/ports.conf	2026-10-03 10:33:47.902113745 +0000
@@ -1,4 +1,5 @@
 Listen 80
+Listen 192.0.2.10:8081
 
 <IfModule ssl_module>
 	Listen 443
```

`@@ -1,4 +1,5 @@`: from line 1, four old lines became five. One added line is the change you meant; anything else needs explaining before a reload. Exit status: 0 = same, 1 = different, 2 = trouble.

**Why it is effective:** a five-line edit in a 300-line config is reviewed in seconds, and a saved baseline (`find / -xdev -perm -4000 -type f | sort > suid-baseline.txt`) turns "anything new?" into output cron can mail.

**Compared with comparing by eye:** two terminals side by side work for a few lines; a changed character, a trailing space or a tab never shows.

**Trap:** both sides must be in the same order, or every line looks moved: `sort` listings first. Windows line ends or re-indentation make every line differ (`--strip-trailing-cr`, `-w`). diff cannot tell which side is correct: name files clearly.

**Next step:** unexpected lines → find who changed them (`stat`, the journal, the config's Git log). Only your change → config test, then reload. Recurring audits → baseline in Git, or AIDE.

### sha256sum — is this file byte for byte the one I expect?
Match: sha256sum, md5sum
Instead of: md5sum, comparing sizes and dates
Safety: read-only · the `> SHA256SUMS` redirect writes the list file

**In one line:** `sha256sum` prints a SHA-256 fingerprint per file; the same fingerprint later proves that not one bit changed, and `-c` re-checks a whole list.

**Read the command:** `sudo sh -c "cd $B && sha256sum * > SHA256SUMS"`

| Part | Meaning |
|---|---|
| `sudo sh -c "…"` | the whole line, redirect included, runs in a root shell (the backup directory is root-only) |
| `cd $B && sha256sum *` | enter the backup directory so the list holds bare names; per file: 64 hex characters, two spaces, the name |
| `> SHA256SUMS` | keep the list beside the files, and copy both off the host |
| `sha256sum -c SHA256SUMS` | later, or on the backup server: recompute and compare every file |
| `sha256sum dokploy-install.sh` | record exactly which installer you reviewed and ran |

**What the output tells you:**

```
$ sha256sum -c SHA256SUMS
etc-apache2.tgz: OK
mysql-all.sql.gz: OK
var-www.tgz: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
```

`FAILED` = changed since the list was made: an incomplete copy, disk corruption or tampering. The exit status is then 1, so a restore script can stop.

**Why it is effective:** size and date can match while content differs; a hash changes completely with any change, so "the backup copy is complete" and "this is the installer we reviewed" become yes or no.

**Compared with `md5sum`:** same usage and output, fine for accidental corruption, but MD5 collisions can be made on purpose, so it proves nothing against tampering.

**Trap:** a list stored on the same host as the files catches corruption, not an attacker who can rewrite both. A download is only trustworthy against a hash or signature the vendor publishes separately.

**Next step:** `FAILED` backup → copy it again and re-check. Installer hash differs from the change request → stop and `diff` the two copies. Proof of origin → a GPG or cosign signature.

### tar — pack a tree with owners and modes, list it, restore it
Match: tar
Instead of: cp -r
Safety: read-only for the source when creating or listing · changes state: `-x` overwrites files under the target without asking

**In one line:** `tar` packs a tree, owners, modes, timestamps and symlinks included, into one archive (usually gzip-compressed) that you can list, checksum, copy off the host and unpack exactly where it came from.

**Read the command:** `sudo tar -czpf "$B/etc-apache2.tgz" -C / etc/apache2`

| Part | Meaning |
|---|---|
| `-c` · `-z` · `-p` | create · gzip it (`-J` xz, `--zstd`) · on extract, apply the stored permissions exactly |
| `-f "$B/etc-apache2.tgz"` | the archive file (without `-f`, Ubuntu's tar uses stdin/stdout: `docker save IMAGE` into `tar tv`) |
| `-C / etc/apache2` | change to `/` first, then store the **relative** path `etc/apache2/…` |
| `tar -tzf FILE` | list without unpacking: proof the archive is readable |
| `tar -xzpf FILE -C /` | **extract**: put the tree back under `/`, overwriting what is there |

**What the output tells you:**

```
$ sudo tar -tzf "$B/etc-apache2.tgz" | head -n 3
etc/apache2/
etc/apache2/sites-available/
etc/apache2/sites-available/api.example.com-le-ssl.conf
```

No leading `/`: the archive unpacks relative to whatever `-C` names, so you can open it on a staging VM or in a scratch directory first. `-tv` adds mode, owner, size and date.

**Why it is effective:** one file per tree with owners and symlinks intact (Let's Encrypt's `live/` links into `archive/`), easy to checksum and move off-host; a restore is one command.

**Compared with `cp -r`:** `cp -a` next to the original suits a quick rollback on the same host; plain `cp -r` gives the copies your ownership and new timestamps, and a directory of copies is harder to move and verify than one archive.

**Trap:** `-x` overwrites without asking and leaves files added since the backup. With absolute paths GNU tar strips the leading `/` (with a warning) and a restore lands relative to your current directory: use `-C /`. A live database directory archives inconsistently: dump it instead. A listing proves readable, not complete.

**Next step:** archive made → `sha256sum`, then copy it off the host (`rsync`). Restore → extract into a scratch directory, `diff -r` against the live tree, then extract for real.

### gzip / gunzip — compress a stream as it is written, restore without unpacking to disk
Match: gzip, gunzip
Instead of: gunzip FILE.gz before reading or restoring
Safety: changes state: `gzip FILE` replaces FILE with FILE.gz and `gunzip FILE.gz` does the reverse · in a pipe or with `-c` no file is touched

**In one line:** `gzip` compresses a file or a stream (SQL dumps and logs often shrink 5–10×); in a pipe it compresses a backup as it is written, and `gunzip -c` feeds it back without storing the uncompressed copy.

**Read the command:** `sudo mysqldump --single-transaction --routines --events --all-databases | gzip | sudo tee "$B/mysql-all.sql.gz" >/dev/null`

| Part | Meaning |
|---|---|
| `mysqldump --single-transaction --routines --events --all-databases` | every database as SQL from one consistent InnoDB snapshot, with procedures and events |
| `gzip` in the middle | compress the stream as it passes: no uncompressed dump on disk |
| `sudo tee "$B/…" >/dev/null` | write into the root-only backup directory (see `tee`) |
| `gunzip -c FILE.sql.gz` | decompress to stdout and keep the `.gz`: pipe into `mysql` or `psql` to restore |
| `gzip -t` · `gzip -k` | test integrity (silent, exit 0 when intact) · compress but keep the original |

**What the output tells you:** the pipe prints nothing, so check the result:

```
$ gzip -t mysql-all.sql.gz && echo intact
intact
$ gunzip -c mysql-all.sql.gz | tail -n 1
-- Dump completed on 2026-10-03 10:03:12
```

mysqldump writes `Dump completed` last: if it is missing, the dump stopped part-way, however big the file looks.

**Why it is effective:** compressing in the pipe needs no space for an uncompressed copy, and `gunzip -c` restores the same way, which matters most when the disk is the problem.

**Compared with `gunzip FILE.gz`:** it writes the full uncompressed file (possibly tens of GB) and deletes the `.gz`, so your only backup copy changes form.

**Trap:** `mysqldump … | gzip > FILE` succeeds even when mysqldump fails: a pipeline returns the last command's status, leaving a small, valid `.gz` of half a dump. Use `set -o pipefail` and check the last line. `gzip -l` misreports sizes from 4 GiB up.

**Next step:** every backup → `gzip -t`, the last line, `sha256sum`, and regular test restores into a scratch database. Slow on big dumps → `pigz` or `zstd -T0`.

### rsync — copy only what changed, resume big transfers, dry-run first
Match: rsync
Instead of: scp, cp -r
Safety: changes state: writes the destination, and `--delete` removes destination files missing from the source · `-n` changes nothing

**In one line:** `rsync` copies locally or over SSH, sends only what differs, keeps permissions, times and links, resumes interrupted transfers, and shows what it would do before doing it.

**Read the command:** `rsync -avzn dir/ user@host:/path/`

| Part | Meaning |
|---|---|
| `-a` | archive: recursive, keeping permissions, times, symlinks, group and owner (owner only if the receiver runs as root) |
| `-v` · `-z` | list each file · compress in transit (wasted CPU on a fast LAN or for `.gz` files) |
| `-n` | dry run: show what would happen, change nothing |
| `dir/` then `user@host:/path/` | trailing slash: copy the **contents** of dir (without it rsync creates `/path/dir/`); the target over SSH |
| `--partial --append-verify` | keep and resume a partly sent file, then verify the whole file |
| `--info=progress2` · `--bwlimit=20000` | one overall progress line · cap at about 20 MB/s (unit KiB/s) |
| `-aHAXS --numeric-ids` | full fidelity for `/var/lib/docker`: hard links, ACLs, xattrs, sparse files, raw IDs |

**What the output tells you:**

```
sending incremental file list
config.yml
static/app.js

sent 1,204 bytes  received 64 bytes  2,536.00 bytes/sec
total size is 48,301,551  speedup is 38,093.02 (DRY RUN)
```

Two files differ from the target, and `(DRY RUN)` confirms nothing was written.

**Why it is effective:** repeated runs send only changes, a dropped transfer of a big dump resumes instead of restarting, and `-n` shows the effect first (with `--delete`, what would be removed).

**Compared with `scp`:** fine for one small file; it re-sends everything every time, cannot resume and has no dry run.

**Trap:** the trailing slash decides where files land: `dir/` and `dir` differ by one level. `--delete` with a wrong path empties the destination: run it with `-n` first. Over SSH one CPU core does all the encryption, which is why the handbook tries `-e 'ssh -c aes128-gcm@openssh.com -o Compression=no'` on fast links.

**Next step:** slow → measure the network alone (`iperf3`) and the disks (`iostat -xz 1`). Done → compare `sha256sum` on both sides for critical files. Regular backups → restic or borg.

### date — stamps for file names, epoch seconds for APIs, the time this server believes
Match: date
Instead of: —
Safety: read-only for printing · changes state: `date -s` sets the system clock at once (root)

**In one line:** `date` prints the time in any format and converts between dates and Unix epoch seconds: it stamps backups and evidence files, builds time windows for APIs, and shows the box's time zone.

**Read the command:** `date -d '1 hour ago' +%s`

| Part | Meaning |
|---|---|
| `-d '1 hour ago'` | a moment other than now (GNU: `yesterday`, `2026-10-03 09:14`, `@1791018852`) |
| `+%s` | seconds since 1970-01-01 UTC, the Unix epoch |
| `$(…)000` | three zeros appended: milliseconds, as `aws logs … --start-time` expects |
| `+%F` · `+%F_%H%M` | `2026-10-03` · `2026-10-03_1014`: names that sort in time order |
| `-u` · `-Is` · `-s "…"` | UTC · ISO 8601 with offset · **set** the clock (labs only) |

**What the output tells you:**

```
$ date -Is; date -u -Is
2026-10-03T15:44:12+05:30
2026-10-03T10:14:12+00:00
$ date -d '1 hour ago' +%s
1791018852
```

One instant in the server's zone (+05:30) and in UTC. Logs, `journalctl --since`, cron and cloud consoles may each use another zone; compare timestamps without the offset and events land hours apart. Epoch seconds have no zone, which is why APIs want them.

**Why it is effective:** sortable stamps (`%F`) make `ls` order time order, so the right backup is picked under stress, and relative times build API windows without arithmetic.

**Trap:** `%M` is minutes and `%m` the month: `+%Y%M%d` is a classic bug. `-d` is GNU only (macOS uses `-v`/`-j`). date shows the clock's value, not whether it is synchronised. `date -s` on a box with NTP gets pulled back, and the jump confuses TLS, TOTP, cron and log order.

**Next step:** clock wrong → `timedatectl`, `chronyc tracking`. Zones differ between logs → work in UTC (`date -u`, `journalctl --utc`). Epoch in a log → `date -d @1791018852`.

### mktemp / basename — safe temporary files and clean file names in scripts
Match: mktemp, basename
Instead of: fixed temp names such as /tmp/script.tmp
Safety: `mktemp` creates a file (mode 600) or a directory (mode 700): remove it when done

**In one line:** `mktemp` creates a file or directory with an unpredictable name and prints its path, so runs never collide; `basename` strips the directory (and optionally a suffix) from a path.

**Read the command:** `mktemp /var/lib/node_exporter/textfile/backup.prom.XXXX`

| Part | Meaning |
|---|---|
| `/var/lib/node_exporter/textfile/` | create it in the target directory, so the final `mv` is an atomic rename |
| `backup.prom.XXXX` | the `X`s become random characters; not ending in `.prom`, the file is ignored by node_exporter meanwhile |
| `tmp=$(mktemp …)` · `mktemp -d` | capture the printed path · a private directory instead |
| `basename /etc/apache2/conf-available/php*-fpm.conf .conf` | drop the directory and the `.conf` suffix: `php8.3-fpm` |

**What the output tells you:**

```
$ mktemp /var/lib/node_exporter/textfile/backup.prom.XXXX
/var/lib/node_exporter/textfile/backup.prom.k3Qz
$ basename /etc/apache2/conf-available/php*-fpm.conf .conf
php8.3-fpm
```

An empty file the script owns: write the metrics, then `mv "$tmp" …/backup.prom`. basename yields the PHP-FPM name, which is also its unit name.

**Why it is effective:** node_exporter never reads a half-written file, overlapping runs never share one, and nobody can pre-create `/tmp/script.tmp` as a symlink to a file that root then overwrites.

**Compared with a fixed name:** `/tmp/backup.tmp` works until two runs overlap or someone else creates that name first.

**Trap:** mktemp files are mode 600: `chmod 644` before the `mv` when another account (node_exporter runs as its own user) must read the result. Temp files outlive a crashed script unless `trap 'rm -f "$tmp"' EXIT` removes them. If the glob matches two PHP versions, basename fails with `extra operand`.

**Next step:** scheduled script → `flock` against overlapping runs, and `shellcheck` before deploying it. Metric missing → check the file's name and mode, and `node_textfile_scrape_error`.

### shellcheck — what will break in this script before it ever runs?
Match: shellcheck
Instead of: bash -n
Safety: read-only · it analyses the file and never runs it

**In one line:** ShellCheck reads a shell script and reports the bugs that only show with unusual input or on a bad day (unquoted variables, an unchecked `cd`, loops over `ls`), each with a code and usually a fix.

**Read the command:** `shellcheck /usr/local/bin/health-report.sh`

| Part | Meaning |
|---|---|
| `shellcheck FILE` | analyse the script; its shebang decides the dialect (`bash`, `sh`) |
| `-S warning` | report only warnings and errors, hiding `info` and `style` findings |
| `-x` | also follow files the script `source`s |
| `-f gcc` | one line per finding (`file:line:col: warning: …`) for CI logs |
| `# shellcheck disable=SC2034` | on the line before: silence one finding there, with a comment saying why |
| exit status | 0 = clean, 1 = findings, so a CI job fails on them |

**What the output tells you:**

```
$ shellcheck /usr/local/bin/health-report.sh; echo "exit=$?"
exit=0
$ shellcheck lab/bad.sh
In lab/bad.sh line 3:
cd $dir
^-----^ SC2164 (warning): Use 'cd ... || exit' or 'cd ... || return' in case cd fails.
   ^--^ SC2086 (info): Double quote to prevent globbing and word splitting.
```

The report script is clean. In the lab script, `^--^` marks the column, then code and severity. SC2164: a failed `cd` lets the rest run in the wrong directory, deadly before an `rm`. SC2086: a `$dir` with a space or `*` splits into several words.

**Why it is effective:** quoting and error-handling bugs pass every test on your laptop and fail on the first file name with a space; ShellCheck finds them statically in a second, and a CI job keeps them out of production.

**Compared with `bash -n`:** syntax only (a missing `fi`), nothing about quoting, failed `cd`s or logic.

**Trap:** `-S warning` hides SC2086, which is `info`: the most common quoting bug vanishes from the report. A disable comment without a reason hides real bugs later. A clean report is not a test: run the script on a VM with odd input.

**Next step:** findings → fix rather than silence them, and rerun until clean. Add a `shellcheck` job for every `*.sh` to the GitLab pipeline. Scheduled script → `set -Eeuo pipefail`, `trap … EXIT`, `flock`.
