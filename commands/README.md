# How to write Command Decoder cards (not published)

The website's **Command Decoder** page and the "🔍 Decode the commands used in this submodule" boxes are generated from this folder by `command_decoder.py`, called from `build_site.py`. INTRO.md is the page intro; every other `.md` file here (listed in `ORDER`) is one command family.

## Family file

```
# <Family title>

<2–4 sentences: what this family covers and the order in which you usually use these commands.>

| If you would reach for | Prefer | Because |
|---|---|---|
| <the naive command> | <the better one> | <one line> |

### <card 1>
...
```

Do not use `##` headings inside a family file. The page makes the family a `##` and each card a `###`.

## Card

```
### <name> — <the question this command answers>
Match: <key>, <key>
Instead of: <the weaker commands people reach for first, or —>
Safety: <read-only | changes state: what it changes | needs root: why>

**In one line:** ...

**Read the command:** `<a real invocation from the handbook>`

| Part | Meaning |
|---|---|
| `-x` | ... |

**What the output tells you:** <optional short sample in a fenced block, then the fields that matter>

**Why it is effective:** <what it shows that the obvious alternative hides>

**Compared with `<weaker>`:** <what the weaker one DOES show, what it cannot, when it is enough>   (optional, but expected whenever "Instead of" names a command)

**Trap:** <how the output misleads>

**Next step:** <where each possible answer sends you>
```

- **name**: the command as typed (`mtr`, `docker logs`, `kubectl get`, `systemctl restart / start / stop`). It must be unique across all families; it becomes the anchor `#cmd-<slug>`.
- **Match keys**: lower-case command words. The head is first, then subcommand words if needed: `docker logs`, `docker compose logs`, `kubectl rollout`, `aws ec2`, `systemctl restart`. A section's command matches the most specific key: for `docker compose logs -f web`, the matcher tries `docker compose logs`, then `docker compose`, then `docker`. Subcommand words are the first words after the head that do not start with `-`. The values of `-n/--namespace/-f/--file/-p/--profile/--region/-C/--context/-H/-s` are skipped. A tool gets subcommand matching only if at least one of its keys has two or more words, so give every such tool a **fallback card** keyed by the head alone (`docker`), which covers its rarer subcommands. Several small, related commands may share one card (`Match: pvs, vgs, lvs`). Each key may belong to only one card.
- **Read the command**: pick a flag combination the handbook really uses (see your brief), and decode every flag in it. Do not invent flags. If you are not certain a flag exists and does what you say, leave it out.
- **Length**: 180–420 words per card. Tables have at most 8 rows. Sample output has at most 10 lines.
- **Honesty**: compare fairly. The weaker command usually shows *something* (ping does print end-to-end loss), so say what it shows and what it cannot. Mark commands that change state.
- **Samples**: use documentation addresses (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 10.x, example.com) and generic names (`ops`, `deploy`, `app`, `web01`). Never use real people, real hostnames, keys or tokens.

## Check

Run the checker from the project root. It parses Markdown and runs nothing else:

```
python3 command_decoder.py --check commands/network.md --heads "ping mtr traceroute ip ss"
python3 command_decoder.py --coverage
```
