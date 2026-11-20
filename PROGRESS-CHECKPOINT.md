# Progress checkpoint, 20 November 2026

Read this first when continuing on another machine. Everything listed below is committed. The full history is in `recent_updated.md`, and the project overview is in `PROJECT-SUMMARY.md`.

## Done, independently QA'd: GO

1. **Verify VM** (`labs/vm/`, guide at `labs/vm/README.md`, the "Verify VM" section of `DOCKER.md`).
   - What it is: a throwaway Ubuntu 24.04 VM. QEMU runs inside the container `devops-handbook-vm:local` with `/dev/kvm`, all capabilities dropped, and no network during verify.
   - What it runs: the handbook's commands, then the 25 lab rooms.
   - Results: `reports/verify/verify-2026-11-15.md`. Rooms: 22 PASS, plus 3 DIFFERS (03, 14 and 19 behave differently on a real VM).
   - Commands:
     ```bash
     python3 labs/vm/vmctl.py check
     python3 labs/vm/vmctl.py prepare
     python3 labs/vm/vmctl.py verify [--commands] [--modules N,M] [--rooms N,M] [--keep-going]
     python3 labs/vm/vmctl.py report --run STAMP
     python3 labs/vm/vmctl.py clean [--runs]
     ```
2. **Focus mode** (`focus_site.py`).
   - Opening a roadmap topic shows only that topic's sections, using URLs like `#read.TOPIC.ANCHOR`.
   - Each section has Previous/Next and an end card.
   - Unreached topics are locked in the whole-module view.
   - "Show whole module" shows only that module.
   - Area-wide "Sources" lists become a "Related incidents (N) ›" link.
   - Nested sections are de-duplicated.
3. **Key commands explained** (`keycmd_site.py`, `keycmd_notes.tsv`).
   - Every roadmap key command (455 uses, 416 unique) gets a one-line summary, a safety badge (read-only / adds load / changes state / dangerous) and a "Decode ›" link to its Command Decoder card.
   - A fact-check pass corrected 40 of the summaries. The safety policy is in the TSV header.
4. **Janitor** (`docker/janitor/`). It removes only this project's own old images and build cache.

## Committed but NOT yet independently QA'd

- **A. Whole-module end card.** In learning mode it leads with the map's "Next topic: …". "Next module in the book: X (🔒 N locked) ›" is now a secondary button, shown only when that module has unlocked sections.
- **B. Content fixes from the verify VM report,** in modules 09, 13, 14, 23, 24, 27, 32, 33, 37, 38, 40, 42, 47 and 52, plus `commands/cloud-iac-cicd.md` and `roadmap.json`:
  - the `sudo -iu … bash -c` heredoc;
  - the psql typo lab;
  - `df --output` without `-i`;
  - sysctl, prose and mcelog text inside bash blocks;
  - config text in the wrong fences;
  - macOS labels;
  - install hints for certbot-dns-cloudflare, git-filter-repo and `docker debug`;
  - `sudo nft … | sudo tee`.
- **State:** 221 unit tests pass, and the build reports no warnings.

## Next steps

1. **Re-run the VM check on the changed modules.** A run started on 17 November was interrupted by a shutdown, so its partial report is not committed. Run the command below, which takes about 40–60 minutes, then compare the results against `verify-2026-11-15`:
   ```bash
   python3 labs/vm/vmctl.py verify --commands --modules 9,13,14,23,24,27,30,32,33,37,38,39,40,42,44,45,47,52 --keep-going
   ```
   The VM needs a Linux host with KVM and Docker.
2. **Get an independent QA of A and B,** plus the VM results.
3. **Publish:** log the work in `recent_updated.md`, commit and push, then republish the claude.ai artifact after running `python3 research/prepublish_scan.py artifact.html`.
4. **Open items:**
   - Module 38's lab state leaking between blocks: check that it is fixed.
   - chrony is not in the VM image.
   - `/proc/PID` stand-ins are not detected by the runner.
   - In narrow windows (≤ 800 px), the top bar overlaps the focus bar.

## Rules that still apply

- **Never** run handbook troubleshooting commands on the host. Run them only in lab containers or the verify VM.
- Labs and VMs are ephemeral: no host installs and no boot services.
- Never touch, stop or prune other containers or images on the machine.
- This repo is **public**:
  - no personal names, paths, emails or tokens in content;
  - commit with the GitHub noreply email;
  - never force-push;
  - scan staged files before every push.
- Rooms and drills come from community-reported incidents only.
- `index.html` must stay at or under 15,950,000 bytes.

## Build and test

```bash
python3 build_site.py
python3 -m unittest discover -s tests
python3 -m http.server 8174   # then open http://localhost:8174/index.html
```
