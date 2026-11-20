"""Pure helpers for the verify VM (labs/vm/README.md): no Docker, no VM, nothing is executed.

* extract the ```bash blocks of the NN-*.md modules and split them into complete shell statements;
* decide which statements must not run (placeholders, VM-killers / run-breakers);
* classify a statement's result (PASS, USAGE, MISSING, EXTERNAL, CONTEXT, TIMEOUT);
* read the lab image's apt package list from labs/base/Dockerfile.

All classifier and denylist rules live in this one file and are unit-tested in tests/test_vm_verify.py.
The only process ever started here is `bash -n` (parse only, never executes) to find statement ends.
"""
from __future__ import annotations

import functools
import os
import re
import subprocess
from dataclasses import dataclass, field

SKIP_MODULES = {"17-windows.md", "20-macos.md"}     # PowerShell / macOS: not runnable on Ubuntu
MODULE_RE = re.compile(r"^\d\d-.+\.md$")

# --------------------------------------------------------------------------- blocks
FENCE_OPEN = re.compile(r"^([ \t]*)(`{3,}|~{3,})[ \t]*([A-Za-z0-9_+-]*)[^\n]*$")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t#]*$")


@dataclass
class Block:
    module: str
    line: int                 # line number (1-based) of the first code line
    heading: str
    lines: list[str]
    index: int = 0            # block number within the module (0-based)


def iter_blocks(text: str, module: str = "", langs=("bash",)):
    """Yield the fenced code blocks whose info string is one of `langs`, with the nearest heading."""
    heading = ""
    rows = text.split("\n")
    i, n, idx = 0, len(rows), 0
    while i < n:
        m = FENCE_OPEN.match(rows[i])
        if not m:
            h = HEADING.match(rows[i])
            if h:
                heading = h.group(2).strip()
            i += 1
            continue
        indent, fence, lang = m.group(1), m.group(2), m.group(3).lower()
        close = re.compile(r"^" + re.escape(indent) + r"[ \t]*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$")
        body, j = [], i + 1
        while j < n and not close.match(rows[j]):
            body.append(rows[j][len(indent):] if rows[j].startswith(indent) else rows[j].lstrip())
            j += 1
        if lang in langs:
            yield Block(module, i + 2, heading, body, idx)
            idx += 1
        i = j + 1


# lines that look like command OUTPUT, not commands (a block made mostly of them is a sample output)
OUTPUT_LINE = re.compile(
    r"^\s*(?:[●○×↳]|[└├│─]|"
    r"(?:Active|Loaded|Main PID|Tasks|Memory|CGroup|Docs|Process|Status):\s|"
    r"(?:tcp|udp|tcp6|udp6)\s+(?:LISTEN|ESTAB|UNCONN|\d)|"
    r"[A-Z][A-Z%]+(?:\s{2,}[A-Z%][A-Z%-]+){2,}\s*$|"                       # a table header: NAME   READY  STATUS
    r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d|"                                        # log lines
    r"(?:[A-Z][a-z]{2} [ \d]\d \d\d:\d\d:\d\d)|"                             # syslog lines
    r"HTTP/\d(?:\.\d)? \d{3}\b)")


# a block whose first line is the handbook's own OS label ("# macOS (Terminal), not Linux", "# macOS client ...")
# holds macOS Terminal commands (BSD top/route/netstat options, fs_usage, tmutil): not runnable on Ubuntu
PLATFORM_LABEL = re.compile(r"^\s*#\s*(macOS)\b")


def platform_reason(lines):
    """SKIPPED reason for a whole block labelled for another OS, or None."""
    first = next((ln for ln in lines if ln.strip()), "")
    m = PLATFORM_LABEL.match(first)
    return f"other platform: {m.group(1)} block" if m else None


def is_output_block(lines) -> bool:
    body = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not body:
        return False
    if all(ln.lstrip().startswith("$ ") is False for ln in body):
        hits = sum(1 for ln in body if OUTPUT_LINE.match(ln))
        return hits * 2 >= len(body) and hits >= 1
    return False


# --------------------------------------------------------------------------- statements
HEREDOC = re.compile(r"(?<![<\\])<<(?!<)(-?)[ \t]*(?:'([^'\n]+)'|\"([^\"\n]+)\"|\\?([A-Za-z_][A-Za-z0-9_]*))")
CONTINUES = re.compile(r"(?:\\|\||&&|\|\|)\s*$")
_CLEAN_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C"}


@functools.lru_cache(maxsize=65536)
def bash_parses(chunk: str, bash: str = "bash") -> bool:
    """True if `bash -n` (parse only, nothing is executed) accepts the chunk."""
    try:
        p = subprocess.run([bash, "--norc", "--noprofile", "-n"], input=chunk + "\n", capture_output=True,
                           text=True, env=_CLEAN_ENV, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0 and "syntax error" not in p.stderr and "unexpected" not in p.stderr


SIMPLE_LINE = re.compile(r"^[^'\"`$(){}\[\]<>\\#;&|]*$")
RESERVED = re.compile(r"(?:^|\s)(?:if|then|elif|else|fi|for|while|until|do|done|case|esac|select|function|in)(?:\s|$)")


def _heredoc_delims(line: str):
    out = []
    for m in HEREDOC.finditer(_strip_quoted(line)):
        delim = m.group(2) or m.group(3) or m.group(4)
        out.append((delim, m.group(1) == "-"))
    return out


def _strip_quoted(line: str) -> str:
    """The line with single-quoted strings blanked (heredoc markers inside quotes are not markers).
    Quoted heredoc delimiters such as <<'EOF' survive: the quote directly follows <<."""
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "'":
            j = line.find("'", i + 1)
            if j < 0:
                break
            if re.search(r"<<-?[ \t]*$", "".join(out)):
                out.append(line[i:j + 1])          # a quoted heredoc delimiter: keep it
            else:
                out.append("''")
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _ends_continued(chunk_lines) -> bool:
    for ln in reversed(chunk_lines):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        return bool(CONTINUES.search(s))
    return False


def _complete(chunk_lines) -> bool:
    if _ends_continued(chunk_lines):
        return False
    if len(chunk_lines) == 1 and SIMPLE_LINE.match(chunk_lines[0]) and not RESERVED.search(chunk_lines[0]):
        return True
    return bash_parses("\n".join(chunk_lines))


def _only_comments(lines) -> bool:
    return all(not ln.strip() or ln.lstrip().startswith("#") for ln in lines)


def split_statements(lines, first_line: int = 1):
    """Split a block into complete shell statements: [(line_number, text), ...].

    Lines are accumulated until the chunk has no open heredoc, does not end in a continuation
    (`\\`, `|`, `&&`, `||`) and `bash -n` accepts it. A chunk that never becomes valid is emitted one
    line at a time (each will show its own syntax error when run). Comment-only chunks are dropped."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        if not lines[i].strip() or lines[i].lstrip().startswith("#"):
            i += 1
            continue
        start, chunk, pending, done = i, [], [], False
        j = i
        while j < n:
            ln = lines[j]
            chunk.append(ln)
            j += 1
            if pending:
                delim, dash = pending[0]
                if (ln.lstrip("\t") if dash else ln).rstrip() == delim:
                    pending.pop(0)
                if pending:
                    continue
            else:
                pending.extend(_heredoc_delims(ln))
                if pending:
                    continue
            if _complete(chunk):
                done = True
                break
        if not done:                       # never valid: emit the first line alone and go on from the next
            chunk, j = [lines[start]], start + 1
        while chunk and (not chunk[-1].strip() or chunk[-1].lstrip().startswith("#")):
            chunk.pop()
        if chunk and not _only_comments(chunk):
            out.append((first_line + start, "\n".join(chunk)))
        i = j
    return out


# --------------------------------------------------------------------------- shell text helpers
def code_text(stmt: str, bodies: bool = True) -> str:
    """The statement without comments (quotes kept; heredoc bodies kept unless bodies=False).
    A shell-aware scanner: `#` starts a comment only at the start of a word, outside quotes and heredocs."""
    out_lines, pending = [], []
    for ln in stmt.split("\n"):
        if pending:
            if bodies:
                out_lines.append(ln)
            delim, dash = pending[0]
            if (ln.lstrip("\t") if dash else ln).rstrip() == delim:
                pending.pop(0)
            continue
        res, i, n, q = [], 0, len(ln), None
        while i < n:
            c = ln[i]
            if q == "'":
                res.append(c)
                if c == "'":
                    q = None
            elif q == '"':
                res.append(c)
                if c == "\\" and i + 1 < n:
                    res.append(ln[i + 1])
                    i += 1
                elif c == '"':
                    q = None
            else:
                if c == "\\" and i + 1 < n:
                    res.append(c + ln[i + 1])
                    i += 2
                    continue
                if c in "'\"":
                    q = c
                elif c == "#" and (i == 0 or ln[i - 1] in " \t;&|("):
                    break
                res.append(c)
            i += 1
        line = "".join(res).rstrip()
        out_lines.append(line)
        pending.extend(_heredoc_delims(line))
    return "\n".join(out_lines)


def unquoted_text(stmt: str, bodies: bool = False) -> str:
    """Comments (and heredoc bodies) removed, the contents of '...' and "..." blanked."""
    t = code_text(stmt, bodies)
    t = re.sub(r"'[^'\n]*'", "''", t)
    return re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', t)


# --------------------------------------------------------------------------- not shell at all
# Lines of SQL, YAML, INI or config that a block shows for typing into another program (psql, an editor).
SQL_HEAD = re.compile(r"^(?:SELECT|CREATE|ALTER|INSERT|UPDATE|DELETE|DROP|GRANT|REVOKE|BEGIN|COMMIT|ROLLBACK|"
                      r"EXPLAIN|SHOW|VACUUM|ANALYZE|WITH|TRUNCATE|REINDEX|CLUSTER|LOCK|REFRESH|CHECKPOINT|"
                      r"SET\s+(?:SESSION|LOCAL|GLOBAL|search_path|statement_timeout|lock_timeout)|FLUSH|PURGE|"
                      r"STOP\s+SLAVE|START\s+SLAVE|CHANGE\s+(?:MASTER|REPLICATION)|RESET|USE\s+\w+;)\b")


def not_shell_reason(stmt: str):
    first = stmt.lstrip().split("\n", 1)[0].strip()
    if SQL_HEAD.match(first) or re.match(r"^\\[a-z]{1,3}\b", first):
        return "not shell: SQL / psql input"
    if re.match(r"^\[[A-Za-z][\w .:-]*\]$", first):
        return "not shell: INI section"
    if re.match(r"^[A-Za-z_][\w.-]*:(?:\s|$)", first) and not re.match(r"^\w+:\s*\S*/", first):
        return "not shell: YAML / key: value"
    if re.match(r"^(?:<[A-Za-z/]|[}\]]\s*$|\{\s*$|server\s*\{|location\s|upstream\s|listen\s+\d)", first):
        return "not shell: config text"
    return None


# --------------------------------------------------------------------------- placeholders
HTML_TAGS = {
    "html", "head", "body", "title", "meta", "link", "script", "style", "div", "span", "p", "a", "b", "i", "u",
    "br", "hr", "pre", "code", "ul", "ol", "li", "table", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6",
    "form", "input", "img", "strong", "em", "small", "label", "button", "section", "header", "footer", "nav",
    "main", "article", "center", "font", "iframe", "svg", "xml", "virtualhost", "location", "directory",
    "ifmodule", "files", "filesmatch", "proxy", "limit", "limitexcept", "locationmatch", "directorymatch",
    "ifdefine", "requireall", "requireany", "defunct", "none", "stdin", "stdout", "eof", "address",
    "smtp_server", "logall", "logall_json", "ossec_config", "global", "localfile", "command", "frequency",
    "rule", "group", "decoder", "list", "client", "server", "syscheck", "directories", "ignore", "alerts",
    "email_notification", "email_to", "email_from", "log_alert_level", "email_alert_level", "wodle",
    "remote", "connection", "port", "protocol", "level", "rules_id", "force", "description", "match",
}
ANGLE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9_.:-]*)((?:[ -][A-Za-z0-9_.:-]+){0,4})>")
CAPS = re.compile(r"(?<![\w$/.{%:@=,-])([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*)(?![\w=({,])")
STAND_INS = {
    "CONTAINER", "CONTAINER_ID", "POD", "POD_IP", "NS", "NAMESPACE", "PID", "TID", "IMAGE", "KEY", "SHA",
    "TOKEN", "PASSWORD", "NEW_PASSWORD", "OLD_IP", "NEW_IP", "VM_IP", "IP", "HOST", "PORT", "IFACE", "NIC",
    "DEVICE", "DOMAIN", "URL", "EMAIL", "VPC_ID", "SUBNET_ID", "INSTANCE_ID", "LB_ARN", "TG_ARN",
    "VMID", "UNIT", "SERVICE", "NODE", "APPUSER", "REPO", "MAC", "CTID", "JOB", "BRANCH",
    "CLUSTER", "REGION", "BUCKET", "ACCOUNT_ID", "ROLE_ARN", "ARN", "DIGEST",
    "USERNAME", "VM_B", "VM_A", "PROJECT", "APP", "SECRET", "DBNAME",
}
CAPS_STANDIN = re.compile(r"^(?:(?:OLD|NEW|YOUR|MY|SOME|TARGET|REMOTE|LOCAL|OTHER)_[A-Z0-9_]+|(?:GOOD|BAD)[A-Z]{2,}|"
                          r"[A-Z0-9_]+_(?:IP|ID|ARN|HOST|DIR|USER|KEY|SHA|DOMAIN|IFACE|POD|NODE|PID|NIC|CIDR))$")
# commands whose ALL_CAPS words are keywords or variable NAMES, not stand-ins
CAPS_OK_HEADS = re.compile(r"(?:^|[;&|(]\s*|sudo\s+)(?:dig|host|nslookup|drill|kdig|delv|resolvectl|unset|printenv|"
                           r"export|declare|typeset|readonly|env|sar|psql|mysql|redis-cli|sqlite3)\b")


def placeholder_reason(stmt: str):
    """Why this statement holds a stand-in the reader must fill in, or None."""
    code = code_text(stmt)
    if "…" in code:
        return "placeholder: …"
    if re.search(r"(?<![.\w/])\.\.\.(?![.\w/])", unquoted_text(stmt)):
        return "placeholder: ..."
    for m in ANGLE.finditer(code):
        tag = m.group(2).lower()
        if m.group(1) or tag in HTML_TAGS or re.fullmatch(r"h[1-6]", tag):
            continue
        if code[max(0, m.start() - 1):m.start()] == "<":          # << heredoc / <<< herestring
            continue
        return f"placeholder: {m.group(0)}"
    shell = code_text(stmt, bodies=False)
    defined = set(re.findall(r"(?:^|[\s;&|(])(?:export\s+|local\s+|readonly\s+|declare\s+(?:-\w+\s+)?)?([A-Z][A-Z0-9_]*)=", shell))
    defined |= set(re.findall(r"\bfor\s+([A-Z][A-Z0-9_]*)\s+in\b", shell))
    for m in re.finditer(r"\bread\s+(?:-\w+\s+(?:\S+\s+)?)*([A-Z][A-Z0-9_ ]*)", shell):
        defined |= set(m.group(1).split())
    caps_ok = bool(CAPS_OK_HEADS.search(shell))
    for m in CAPS.finditer(unquoted_text(stmt).replace("''", " ").replace('""', " ")):
        tok = m.group(1)
        if tok in defined or len(tok) < 2:
            continue
        if tok in STAND_INS and not (caps_ok and tok in ("NS", "HOST", "PORT", "PASSWORD", "TOKEN", "KEY")):
            return f"placeholder: {tok}"
        if CAPS_STANDIN.match(tok) and not caps_ok:
            return f"placeholder: {tok}"
    m = re.search(r"\b([A-Z][A-Z_]+)@([A-Z][A-Z_.]+)\b", shell)
    if m:
        return f"placeholder: {m.group(0)}"
    return None


# --------------------------------------------------------------------------- denylist
# C: the start of a command (line start or after ; & | ( ` $( and, optionally, sudo/env/time/nohup/exec)
C = (r"(?:^|[;&|(`{'\"]|\$\(|\b(?:then|do|else)\b)\s*"
     r"(?:(?:sudo|doas|exec|nohup|time|command|builtin|env|nice|ionice|setsid|timeout\s+\S+)\s+(?:-\S+\s+)*(?:\w+=\S*\s+)*)*")
B = r"(?:^|(?<=[\s;&|(`'\"!{]))"          # start of any word
E = r"(?=[\s;&|)`'\"]|$)"                  # end of a word
SYSDIRS = (r"(?:/|/\*|/(?:etc|usr|bin|sbin|lib|lib32|lib64|boot|var|var/lib|var/lib/dpkg|var/lib/apt|home|root|dev|"
           r"proc|sys|run|srv|opt|snap)/?\*?)")
# the VM's only disk is virtio /dev/vda: commands aimed at /dev/sdX or /dev/xvdX find no device there and fail harmlessly
DISK = r"/dev/(?:vd[a-z]|disk/|root\b)"
FIREWALL_READ = re.compile(
    r"^(?:iptables|ip6tables|iptables-legacy|iptables-nft)\s+(?:-[tw]\s*\S+\s+|--table\s+\S+\s+|-w\s+)*"
    r"(?:-[nvxLS]+|--list|--list-rules|-[nvx]*L[nvx]*|-[nvx]*S[nvx]*|--line-numbers|-C)\b"
    r"|^(?:iptables|ip6tables)-save\b|^nft\s+(?:-[a-z]+\s+)*(?:list|-c|--check|monitor|describe)\b"
    r"|^ufw\s+(?:status|show|app\s+(?:list|info)|--dry-run|version)\b|^ufw\s+--version\b"
    r"|^firewall-cmd\s+(?:--state|--list|--get|--query|--info|--permanent\s+--list)")

DENY = [
    (C + r"(?:reboot|shutdown|poweroff|halt|kexec|telinit)" + E, "reboots or powers off the VM"),
    (C + r"init\s+[06S]" + E, "reboots or powers off the VM"),
    (C + r"systemctl\s+(?:-\S+\s+)*(?:reboot|poweroff|halt|kexec|isolate|emergency|rescue|suspend|hibernate|"
     r"hybrid-sleep|soft-reboot|default|exit)" + E, "changes the VM's run state"),
    (C + r"systemctl\s+(?:-\S+\s+)*(?:stop|disable|mask|kill)\s+(?:-\S+\s+)*[^;&|\n]*?(?<![\w-])"
     r"(?:ssh|sshd|ssh\.socket|ssh\.service|systemd-networkd|systemd-networkd\.socket|networking|"
     r"NetworkManager|vfy-runner|systemd-journald|dbus|dbus\.socket|systemd-logind)(?![\w-])", "stops SSH or networking"),
    (C + r"(?:mkfs(?:\.\w+)?|mke2fs|mkswap|wipefs|blkdiscard|sfdisk(?!\s+(?:-l|-d|--dump|--list|-J|--json)\b)|"
     r"cfdisk|gdisk|cgdisk|fdisk(?!\s+-l)|parted(?!\s+(?:-\S+\s+)*(?:-l|--list|\S+\s+(?:unit\s+\S+\s+)?print))|"
     r"sgdisk(?!\s+(?:-p|--print|-v|--verify))|pvcreate|pvremove|vgremove|lvremove|lvreduce|cryptsetup|"
     r"mdadm\s+(?:--create|-C|--zero-superblock|--add|--fail|--remove|--grow)|e2fsck(?!\s+-n)|fsck(?:\.\w+)?(?!\s+-n)|"
     r"xfs_repair|tune2fs\s+(?!-l)|nvme\s+(?:format|sanitize)|hdparm\s+(?!-[tTI]+\s))"
     r"\s[^;&|\n]*" + DISK, "writes to the VM's own disk"),
    (C + r"(?:mkfs(?:\.\w+)?|wipefs|sfdisk|sgdisk|blkdiscard)\s[^;&|\n]*\$\{?(?!LOOP|loop|lo\b)[A-Za-z_]",
     "formats a device given by a variable"),
    (C + r"dd\s[^;&|\n]*\bof=/dev/(?!null|stdout|stderr|loop)", "dd onto a device"),
    (r"(?:>|tee\s+(?:-a\s+)?)\s*" + DISK, "writes onto a block device"),
    (C + r"shred\s[^;&|\n]*/dev/", "shreds a device"),
    (C + r"rm\s+(?:-\S*[rRf]\S*\s+|--recursive\s+|--force\s+|--no-preserve-root\s+)+(?:--\s+)?" + SYSDIRS + E,
     "rm -rf of / or a system directory"),
    (C + r"(?:chmod|chown|chgrp|setfacl)\s+(?:-\S+\s+)*-[a-zA-Z]*R[a-zA-Z]*\s+(?:\S+\s+)?" + SYSDIRS + E,
     "recursive mode/owner change on / or a system directory"),
    (C + r"(?:chmod|chown)\s+(?:\S+\s+)/" + E, "mode/owner change on /"),
    (C + r"ip\s+(?:-\S+\s+)*l(?:ink|i|nk)?\s+set\s+[^;&|\n]*\b(?:down|mtu|address|name|netns|nomaster|master|arp\s+off)\b",
     "takes the VM's link down or changes it"),
    (C + r"ip\s+(?:-\S+\s+)*l(?:ink)?\s+(?:del|delete)\b", "deletes a link"),
    (C + r"ip\s+(?:-\S+\s+)*(?:a|addr|address)\s+(?:flush|del|delete|change|replace)\b", "removes the VM's address"),
    (C + r"ip\s+(?:-\S+\s+)*(?:r|ro|route)\s+(?:del|delete|flush|change|replace)\b", "removes or changes the VM's routes"),
    (C + r"ip\s+(?:-\S+\s+)*(?:r|ro|route)\s+add\s+(?:\S+\s+)*?default\b", "adds a default route"),
    (C + r"ip\s+(?:-\S+\s+)*rule\s+(?:add|del|delete|flush)\b", "changes policy routing"),
    (C + r"ip\s+(?:-\S+\s+)*(?:n|neigh|neighbour)\s+(?:flush|del)\b", "flushes the neighbour table"),
    (C + r"(?:netplan\s+(?:apply|try)|ifdown|ifup|dhclient\s+-[rx]|dhcpcd\s+-[kx]|"
     r"networkctl\s+(?:down|reconfigure|reload|forcerenew|renew)|resolvectl\s+revert)" + E, "re-applies or downs the VM's network"),
    (C + r"nmcli\s+(?:-\S+\s+)*(?:c|con|connection|d|dev|device|n|networking|r|radio)\s+"
     r"(?:up|down|modify|mod|delete|del|reload|disconnect|set|reapply|off|connect|add)\b", "changes NetworkManager state"),
    (C + r"tc\s+(?:-\S+\s+)*qdisc\s+(?:add|change|replace)\b", "shapes or drops the VM's only link"),
    (C + r"(?:ethtool\s+(?:-s|-K|-G|-L|-A|-C|--change|--offload|--set-ring|--set-channels)|brctl\s+(?:addif|delif|delbr)|"
     r"ovs-vsctl\s+(?:add|del))" + E, "reconfigures the VM's NIC"),
    (C + r"(?:swapoff\s+-a|sysctl\s+(?:-w\s+)?vm\.overcommit_memory=2)" + E, "can make the VM unusable"),
    (C + r"kill\s+(?:-\S+\s+)*(?:--\s+)?-1\s*(?:$|[;&|])", "kills every process"),
    (C + r"kill\s+(?:-\S+\s+)*1\s*(?:$|[;&|])", "kills PID 1"),
    (C + r"(?:pkill|killall)\s+(?:-\S+\s+)*[^;&|\n]*\b(?:sshd?|python3?|systemd|init|bash|sh|dbus-daemon|"
     r"systemd-networkd|sleep|agetty)\b", "kills the session or SSH"),
    (r"sysrq", "SysRq trigger"),
    (C + r"(?:userdel|deluser|usermod|passwd|chage|chsh|gpasswd\s+-d)\s[^;&|\n]*(?<![\w-])(?:lab|root)(?![\w-])",
     "changes the lab or root account"),
    (C + r"(?:apt|apt-get|dpkg|snap)\s+(?:-\S+\s+)*(?:remove|purge|autoremove\s+--purge|-r|-P|--purge|--remove)\s[^;&|\n]*"
     r"\b(?:openssh|python3|systemd|sudo|bash|coreutils|libc6|util-linux|dbus|netplan|iproute2|cloud-init|ufw)",
     "removes a package the VM or the run needs"),
    (C + r"(?:apt|apt-get|dpkg|snap)\s+(?:-\S+\s+)*(?:remove|purge|-r|-P|--purge|--remove)\b[^\n]*|"
     r"(?:docker\.io|containerd|runc|podman-docker)[^\n]*\n?[^\n]*(?:apt|apt-get)\s+(?:-\S+\s+)*(?:remove|purge)\b",
     "removes Docker, which the rest of the module needs (the VM is offline: no replacement can be installed)"),
    (C + r"(?:mount\s+[^;&|\n]*remount,ro|umount\s+(?:-\S+\s+)*(?:/|/boot|/sys|/proc|/run|/dev|-a)" + E + ")",
     "unmounts or freezes a system filesystem"),
    (r">\s*/proc/sys/(?:kernel/(?:panic|sysrq)|vm/(?:overcommit_memory|nr_hugepages))", "can freeze or panic the VM"),
    (C + r"(?:fallocate\s+(?:-\S+\s+)*-l\s*(?:[3-9]\d*|[1-9]\d+)(?:\.\d+)?\s*[GT]|"
     r"truncate\s+-s\s*\+?(?:[3-9]|\d\d+)[GT]\s+/(?!tmp))", "fills the VM's disk"),
    (C + r"(?:yes|cat\s+/dev/(?:zero|urandom))\s*>(?!\s*/dev/null)", "fills the VM's disk"),
    (r":\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}|(\w+)\s*\(\)\s*\{\s*\1\s*\|\s*\1\s*&", "fork bomb"),
    (C + r"crontab\s+-r" + E, "removes root's crontab"),
    (C + r"(?:modprobe\s+-r|rmmod)\s+(?:-\S+\s+)*(?:virtio\w*|e1000\w*|ext4|kvm\w*)" + E, "unloads a driver the VM runs on"),
    (r"(?:>|tee\s+(?:-a\s+)?)\s*/etc/(?:ssh/sshd_config|sudoers|pam\.d/(?:sshd|sudo|common-\w+)|nsswitch\.conf)(?![\w./-])",
     "overwrites SSH, sudo or PAM config"),
    (B + r"(?:DenyUsers|AllowUsers|AllowGroups|DenyGroups)\s", "restricts SSH logins"),
]
DENY_RE = [(re.compile(pat, re.M), why) for pat, why in DENY]
DOCKER_PKGS = re.compile(r"\b(?:docker\.io|docker-ce|containerd(?:\.io)?|runc|podman-docker|docker-compose(?:-v2)?)\b")
FIREWALL_HEAD = re.compile(C + r"(?:iptables|ip6tables|iptables-legacy|iptables-nft|iptables-restore|ip6tables-restore|"
                           r"nft|ufw|firewall-cmd|ebtables|arptables|ipset)" + E, re.M)


def simple_commands(code: str):
    """Rough list of simple commands (prefixes such as sudo/env/time stripped), for the firewall rule."""
    parts = re.split(r"\$\(|`|&&|\|\||[;|&(){}\n]", code)
    out = []
    for p in parts:
        w = p.strip()
        while True:
            m = re.match(r"^(?:sudo(?:\s+-[A-Za-z]+(?:\s+\w+)?)*|env(?:\s+\w+=\S*)*|time|nohup|exec|command|"
                         r"timeout\s+\S+|nice(?:\s+-n\s*-?\d+)?|ionice(?:\s+-c\s*\d)?|watch(?:\s+-n\s*\S+)?|xargs(?:\s+-\S+)*|"
                         r"do|then|else|!|\w+=\S*)\s+", w)
            if not m:
                break
            w = w[m.end():]
        if w:
            out.append(w)
    return out


def deny_reason(stmt: str):
    """Why this statement must never run in the verify VM (it would kill the VM or the run), or None."""
    code = code_text(stmt)            # heredoc bodies included: a script written now may be run next
    for rx, why in DENY_RE:
        if rx.search(code):
            if why.startswith("removes Docker") and not DOCKER_PKGS.search(code):
                continue
            return f"denylist: {why}"
    if FIREWALL_HEAD.search(code):
        for cmd in simple_commands(code):
            if re.match(r"(?:iptables|ip6tables|iptables-legacy|iptables-nft|iptables-restore|ip6tables-restore|nft|ufw|"
                        r"firewall-cmd|ebtables|arptables|ipset)\b", cmd) and not FIREWALL_READ.match(cmd):
                return "denylist: changes firewall rules (could cut SSH to the VM)"
    return None


def skip_reason(stmt: str):
    """SKIPPED reason for a statement, or None when it may run in the VM."""
    return not_shell_reason(stmt) or deny_reason(stmt) or placeholder_reason(stmt)


# --------------------------------------------------------------------------- classifier
EXTERNAL = {
    # The user's list (cloud, Kubernetes, IaC) plus tools that are not in Ubuntu's archive or belong to another
    # platform (RHEL, Proxmox, macOS). Tools Ubuntu can install are MISSING instead, with the apt hint.
    "kubectl", "kubeadm", "kubelet", "kubectx", "kubens", "k9s", "kind", "minikube", "k3s", "k3d", "crictl",
    "helm", "helmfile", "kustomize", "flux", "argocd", "istioctl", "linkerd", "cilium", "calicoctl", "velero",
    "eksctl", "aws", "az", "gcloud", "gsutil", "doctl", "oci", "terraform", "tofu", "terragrunt", "packer",
    "vault", "bao", "consul", "nomad", "ansible", "ansible-playbook", "ansible-inventory", "ansible-vault",
    "ansible-galaxy", "ansible-lint", "ansible-doc", "ansible-config", "trivy", "grype", "syft", "cosign",
    "gitleaks", "trufflehog", "semgrep", "checkov", "tfsec", "kube-bench", "kube-score", "kubeconform", "conftest",
    "glab", "gitlab-runner", "gitlab-rake", "gitlab-ctl", "gitlab-backup", "sops", "kubeseal", "stern", "popeye",
    "pluto", "kubent", "krew", "kubetail", "qm", "pct", "pvecm", "pveversion", "pvesm", "pvesh", "pveam", "pvenode",
    "pveperf", "proxmox-backup-client", "proxmox-backup-manager", "vzdump", "ha-manager", "cscli", "crowdsec",
    "wazuh-control", "agent_control", "manage_agents", "wazuh-logtest", "wazuh-keystore", "ossec-control",
    "tailscale", "headscale", "netbird", "zerotier-cli", "amtool", "logcli", "mimirtool", "lokitool",
    "mongosh", "kafka-topics", "kafka-topics.sh", "kafka-consumer-groups", "kafka-consumer-groups.sh",
    "dokploy", "traefik", "coolify", "nerdctl", "buildctl", "regctl", "crane", "dive", "lazydocker", "ctop",
    "dnf", "yum", "microdnf", "zypper", "firewall-cmd", "getenforce", "setenforce", "semanage", "sestatus",
    "restorecon", "chcon", "setsebool", "getsebool", "sealert", "launchctl", "brew", "py-spy", "rbspy",
    "filebeat", "metricbeat", "auditbeat", "logstash", "fluent-bit", "otelcol", "otelcol-contrib", "grafana-cli",
    "loki", "promtail", "k6", "mysqlsh", "cqlsh", "nodetool", "influx", "step", "powershell", "pwsh",
    "elasticsearch-reset-password", "harbor", "openstack", "eksctl", "kops", "rke2", "talosctl", "pg_activity",
}
USAGE_PATTERNS = [   # the tool rejected the command line itself
    r"unrecognized option", r"unrecognised option", r"invalid option", r"unknown option", r"illegal option",
    r"unknown flag", r"unknown shorthand flag", r"flag provided but not defined", r"option requires an argument",
    r"requires an argument", r"invalid argument ['‘\"][^'’\"]*['’\"] for ['‘\"]?-", r"invalid (?:value|choice) for",
    r"unrecognized arguments?:", r"unknown argument", r"unknown long option", r"bad option", r"invalid flag",
    r"unknown command(?: verb)?\b", r"unknown subcommand", r"is not a [\w-]+ command", r"unknown operation",
    r"object \"[^\"]+\" is unknown", r"command line is not complete", r"error: argument [^\n]* is wrong",
    r"unknown verb", r"invalid command\b", r"unknown action", r"no such option", r"invalid number of arguments",
    r"syntax error near unexpected token", r"syntax error: unexpected end of file", r"bash: syntax error",
    r"unexpected eof while looking for matching", r"invalid (?:time|output) format", r"unknown field",
    r"unknown column", r"unknown format", r"accepts (?:at most|exactly|at least) \d+ arg",
    r"requires (?:at least|exactly|at most) \d+ arg", r"option '[^']+' is ambiguous",
    r"error: unknown (?:property|key)", r"failed to parse (?:argument|option)", r"invalid filter",
    r"unknown property name", r"unknown output field", r"unknown predicate", r"unknown primary or operator",
    r"unknown parameter", r"invalid usage", r"wrong number of arguments",
]
# bare usage text: many tools print it after ANY failure (no such pid/file/user), so it counts only when
# stderr shows no such context error first
WEAK_USAGE_PATTERNS = [r"(?:^|\n)\s*usage:\s", r"try ['‘`][^'’`]*--help['’`]", r"try --help", r"missing operand",
                       r"too many arguments", r"missing argument"]
CONTEXT_FIRST = re.compile(
    r"no such (?:file|process|user|device|container|object)|can't (?:get|stat|find|open|resolve)|cannot (?:access|open|stat|find)|"
    r"does not exist|not found|permission denied|problems finding|connection refused|unknown user|invalid user|"
    r"is not running|could not|failed to (?:connect|open|find)|unable to|is not a directory|not a block device|"
    r"error encountered when reading a file", re.I)
# the tool ran fine but its world is missing: not a doc error even if it then complains about the command line
# (`git diff --staged` outside a repository turns into `git diff --no-index`, which has no --staged)
CONTEXT_ANY = re.compile(r"not a git repository|outside (?:a )?repository|error encountered when reading a file|"
                         r"error: argument [^\n]*: can't open|usage: git diff --no-index", re.I)
USAGE_RE = re.compile("|".join(f"(?:{p})" for p in USAGE_PATTERNS), re.I)
WEAK_USAGE_RE = re.compile("|".join(f"(?:{p})" for p in WEAK_USAGE_PATTERNS), re.I)
# the name may hold ':' (APT config such as `Unattended-Upgrade::Automatic-Reboot "true";` typed into a bash block)
NOT_FOUND_RE = re.compile(r"(?:^|\n)(?:[^\n:]*: )*(?:line \d+: )?([A-Za-z0-9_.+-]+(?:::?[A-Za-z0-9_.+-]+)*): "
                          r"(?:command not found|not found)\s*$", re.M)
SUDO_NOT_FOUND_RE = re.compile(r"sudo: ([A-Za-z0-9_.+-]+): command not found")
# GNU wrappers (env, nice, timeout, ...) report a missing program as "env: 'cgi-fcgi': No such file or directory"
WRAPPER_NOT_FOUND_RE = re.compile(r"(?:^|\n)(?:env|nice|nohup|timeout|stdbuf|ionice|setsid|chroot|xargs|taskset|chrt|"
                                  r"numactl|strace|ltrace|watch): [‘'`\"]?([A-Za-z0-9_.+-]+)[’'`\"]?: "
                                  r"No such file or directory\s*$", re.M)
# a line of sysctl keys typed into a bash block (`fs.file-max   # comment`, `kernel.pid_max ; kernel.threads-max`)
SYSCTL_KEY = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z0-9_-]+)+")
TIMEOUT_RC = 124


@dataclass
class Verdict:
    cls: str                       # PASS USAGE MISSING EXTERNAL CONTEXT TIMEOUT
    detail: str = ""
    commands: list = field(default_factory=list)   # the missing command names


def missing_commands(err: str):
    names = ([m.group(1) for m in NOT_FOUND_RE.finditer(err)] + SUDO_NOT_FOUND_RE.findall(err)
             + WRAPPER_NOT_FOUND_RE.findall(err))
    seen, out = set(), []
    for n in names:
        if n not in seen and not n.endswith(".sh") and "/" not in n:
            seen.add(n)
            out.append(n)
    return out


EMPTY_ARG = re.compile(r"requires (?:at least|exactly) \d+ arg|missing operand|must follow -p|requires an argument|"
                       r"(?:^|\n)\s*usage:\s|missing argument", re.I)


FUNC_DEF = re.compile(r"(?:^|\n)\s*(?:function\s+)?([A-Za-z_][\w-]*)\s*\(\)\s*\{?")


def defined_functions(texts) -> frozenset:
    """Shell function names defined by any of these statements (e.g. every statement of a module)."""
    return frozenset(m.group(1) for t in texts for m in FUNC_DEF.finditer(t))


def classify(rc, out: str, err: str, timed_out: bool = False, stmt: str = "", functions=frozenset()) -> Verdict:
    """One verdict per statement. Order: TIMEOUT, MISSING/EXTERNAL, USAGE, PASS, CONTEXT.
    A missing command, a usage complaint or (in a pipeline) a context error on stderr counts even when the
    pipeline hid it behind rc 0."""
    err = err or ""
    if timed_out or rc == TIMEOUT_RC and not err.strip():
        return Verdict("TIMEOUT", "no result within the time limit")
    missing = missing_commands(err)
    textish = [m for m in missing if m[0].isupper() or m[0] == "-"]
    if missing and len(textish) == len(missing):
        return Verdict("USAGE", "not a command: config or list text inside a bash block (" + ", ".join(textish) + ")")
    if (missing and all(SYSCTL_KEY.fullmatch(m) for m in missing)
            and re.fullmatch(r"[\w.-]+(?:\s*;\s*[\w.-]+)*\s*;?", code_text(stmt).strip())):
        return Verdict("USAGE", "not a command: sysctl keys inside a bash block (" + ", ".join(missing) + ")")
    if missing and all(m in functions for m in missing):
        return Verdict("CONTEXT", "a shell function defined in another block of this module: " + ", ".join(missing))
    if missing:
        ext = [m for m in missing if m in EXTERNAL]
        if len(ext) == len(missing):
            return Verdict("EXTERNAL", ", ".join(ext), ext)
        return Verdict("MISSING", ", ".join(m for m in missing if m not in EXTERNAL),
                       [m for m in missing if m not in EXTERNAL])
    if CONTEXT_ANY.search(err):
        return Verdict("PASS" if rc == 0 else "CONTEXT", CONTEXT_ANY.search(err).group(0))
    m = USAGE_RE.search(err)
    if not m:
        w = WEAK_USAGE_RE.search(err) or (WEAK_USAGE_RE.search(out or "") if rc not in (0, None) else None)
        src = err if w and w.string is err else (out or "")
        if w and not CONTEXT_FIRST.search(src) and not re.search(r"usage", stmt or "", re.I):
            m = w                    # (a snippet that prints its own "usage:" line is not a doc error)
    if m and EMPTY_ARG.search(m.group(0)) and re.search(r"\$\(|`|\$\{?[A-Za-z_]|\|\s*xargs\b", stmt or ""):
        return Verdict("CONTEXT", "an argument from $(...) or a variable was empty: " + m.group(0).strip())
    if m:
        return Verdict("USAGE", m.group(0).strip())
    if rc == 0 and stmt and re.search(r"(?<!\|)\|(?![|&])", unquoted_text(stmt)):
        hidden = next((ln.strip() for ln in err.splitlines() if CONTEXT_FIRST.search(ln)), "")
        if hidden:                   # `grep x /var/log/missing.log | tail` exits 0 although grep failed
            return Verdict("CONTEXT", "a pipeline's exit 0 hid a failure: " + hidden[:160])
    if rc == 0:
        return Verdict("PASS")
    if rc == TIMEOUT_RC:
        return Verdict("TIMEOUT", "timeout exit status")
    if rc == 127:                    # not found, but its error went to a file or /dev/null
        heads = [c.split()[0] for c in simple_commands(code_text(stmt or "", bodies=False)) if c.split()]
        if heads and heads[0] in EXTERNAL:
            return Verdict("EXTERNAL", heads[0], [heads[0]])
        return Verdict("CONTEXT", "exit 127: a command or script was not found (its error was redirected)"
                       if not err.strip() else "exit 127")
    return Verdict("CONTEXT", f"exit {rc}")


# --------------------------------------------------------------------------- the lab image's packages
def base_packages(dockerfile_text: str):
    """Package names of the `apt-get install` in labs/base/Dockerfile (the lab machine's tools)."""
    text = re.sub(r"\\\n", " ", dockerfile_text)
    m = re.search(r"apt-get install\s+((?:-\S+\s+)*)(.*?)(?:&&|$)", text, re.M)
    if not m:
        return []
    return [w for w in m.group(2).split() if re.fullmatch(r"[a-z0-9][a-z0-9.+-]+", w)]
