# Hands-on labs: design spec (shared by the platform and room builders)

Goal: devopslabs.dev-style rooms inside the handbook.
- **Layout:** the left pane holds an incident brief, tasks, answer boxes, hints and points. The right pane is a live terminal on a disposable lab machine.
- **Checking:** each task is verified ON the machine by check scripts. The next task, and then the next room in the path, unlocks only when the check passes.
- **The 3D map is not changed.**

## Hard constraints (the user's)
- **Nothing may affect the host:**
  - no host installs, no host services, nothing added to boot;
  - lab containers are destroyed on Finish, on Reset, after 30 min idle, when the controller starts (leftovers), and on `docker compose --profile labs down`.
- **Rooms come from real incidents engineers reported online with solutions:** GitHub issues, forums, postmortems, and the catalogs in `research/*.json`. Do not centre the user's own incidents. Each room cites its source (title and URL) and says "adapted".
- **Never run lab scenarios on the host.** Run them only inside lab containers.

## Lab machine (image `devops-handbook-lab:base`, built from `labs/base/Dockerfile`)
Ubuntu 24.04 with real systemd. It is started ONLY with exactly these options (tested on 2026-10-20: systemd runs, nginx starts, the cgroup is namespaced):

```
docker run -d -t --name devlab-<session> --hostname lab --label devlab=1 --label devlab.room=<room-id>
  --cgroupns=private --tmpfs /run --tmpfs /run/lock --tmpfs /tmp
  --cap-drop ALL --cap-add SYS_ADMIN --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER
  --cap-add SETUID --cap-add SETGID --cap-add KILL --cap-add NET_BIND_SERVICE --cap-add SYS_CHROOT
  --cap-add AUDIT_WRITE --cap-add NET_RAW
  --security-opt apparmor=unconfined
  --memory 768m --cpus 1 --pids-limit 512
  --network devlab-net            # internal: true -> no internet, no host ports published
  --entrypoint sh devops-handbook-lab:base -c 'mount -o remount,rw /sys/fs/cgroup && exec /sbin/init'
```

- **Boot:** systemd boots in about 5 s. `systemctl is-system-running` currently says "degraded"; find the failed unit and mask it in the Dockerfile.
- **Contents:** all tools a room needs are baked in (no internet in labs). Room-specific files come from the room's `setup.sh`, which is copied in and run with `docker exec`.
- **Terminal:** `ttyd` is in the image. The controller starts it inside the lab and the page embeds it through nginx (below). The exact command (`TTYD_ARGV` in the controller; `tests/test_labs_platform.py` compares it with this block word for word, with `<token>` filled in):

  ```text
  ttyd -W -p 7681 -m 3 -c lab:<token> -t fontSize=14 -t disableLeaveAlert=true
    -t 'theme={"background":"#0e1621","foreground":"#d9e4ef","cursor":"#4ade80"}' login -f lab
  ```

  `<token>` is a random per-session secret made by the controller. Labs share `devlab-net`, so without it lab A could open `http://devlab-<B>:7681` and get a shell in lab B. Only nginx gets the token: `/api/labs/term-auth` returns it as `X-Lab-Auth: Basic <base64(lab:token)>`, and nginx sends that to ttyd as `Authorization` (it replaces any client header). It never appears in the handbook page, the API JSON or the logs. (ttyd's own client inside the terminal iframe does read it from ttyd's `/token` through nginx, because ttyd also checks it on the websocket; that stays in the browser, which a lab cannot reach.)

## Room format: `labs/rooms/<NN-id>/`
- `room.json`:
  ```json
  {"id": "l0-files-permissions", "title": "…", "level": "L0", "map_node": "files-permissions",
   "path": "fresher", "order": 3, "minutes": 20, "difficulty": "easy",
   "source": {"title": "…", "url": "https://…", "note": "adapted"},
   "brief": "markdown: the incident page / ticket, in the voice of the on-call message",
   "tasks": [
     {"id": "t1", "title": "…", "text": "markdown", "points": 40, "hints": ["…", "…"],
      "questions": [{"id": "q1", "prompt": "Which file …?", "format": "/path/to/file",
                     "answer_sha256": "<sha256 of the normalised answer>"}],
      "checks": [{"id": "c1", "describe": "the service is active and survives a restart",
                  "script": "checks/t1.sh"}]}
   ],
   "walkthrough": "markdown shown only after Finish: the commands, why each step, the real-world source"}
  ```
- **Answers:** normalise with lower-case, trimmed, and inner whitespace collapsed, then sha256. Never put plaintext answers in `room.json`.
- `setup.sh`: runs once inside a fresh lab (as root) to create the broken state. It must be idempotent and fast (under 10 s), and must not need the internet.
- `checks/<task>.sh`: runs inside the lab as root. Exit 0 means pass; any other code fails, and stdout holds a one-line reason shown to the learner. Checks verify the real state, including whether the fix persists (for example, the unit is enabled), not the commands typed.
- `solve.sh` (for tests only, never served to the browser): applies the documented fix, so tests can prove the checks go fail → pass.
- **Room test**, run by `labs/test_rooms.py`:
  1. start a lab;
  2. run `setup.sh`;
  3. confirm every check FAILS;
  4. run `solve.sh`;
  5. confirm every check PASSES;
  6. confirm every question's hash matches `solve.sh`'s documented answer (in `answers.test.json`, also never served);
  7. destroy the lab.

## Controller (`labs/controller/`, Python 3 stdlib only, image `devops-handbook-labs-controller`)
- **Placement:** it runs as a compose service under profile `labs`, `restart: "no"`, on `devlab-net` plus the default network. It uses the Docker CLI through `/var/run/docker.sock`; that is the one privileged piece, so it is documented in `DOCKER.md`.
- **What it may start:** only `devops-handbook-lab:base`, only with the options above.
- **API (JSON):**
  - `GET /api/labs/health`
  - `GET /api/labs/rooms`: no answers, no `solve.sh`
  - `POST /api/labs/rooms/<id>/start` returns a session id
  - `POST /api/labs/sessions/<sid>/answer {question, answer}`
  - `POST /api/labs/sessions/<sid>/check {task}`: runs that task's checks with `docker exec`
  - `POST /api/labs/sessions/<sid>/finish`: destroys the lab and records progress
  - `POST /api/labs/sessions/<sid>/reset`: destroys the lab and starts a fresh one
  - `GET /api/labs/progress`
- **Progress:** a JSON file on a named volume. Task gating: the next task opens only when all questions and checks of the current one pass. Path gating: room N+1 opens when room N is finished.
- **Reaper:** destroys sessions idle for 30 min and, at start, any container labelled `devlab=1`. At most 2 labs run at once.

## Web
- **nginx** (`docker/nginx.conf`) gets `resolver 127.0.0.11 valid=10s` and variable-based proxying, so it still starts when labs are off and answers 502 (except `GET /api/labs/health`, which then answers 200 `{"ok":false,"labs":"off"}` so the page's probe leaves no console error):
  - `/api/labs/` → `labs-controller:8080`
  - `/lab-term/<sid>/` → `devlab-<sid>:7681` (with websocket upgrade)

  The handbook nginx service also joins `devlab-net`.
- **New sidebar group "Labs"** with one generated page, "Hands-on labs" (`labs_site.py`, generated like `interview_site.py`), and no change to the 3D map:
  - **Room list:** grouped by path, each room locked or open, with its source link.
  - **Room view:** split screen, with brief, tasks, answer boxes, Check buttons, hints, points and the terminal iframe on the right.
  - **Without the controller** (offline file, published artifact): the briefs and tasks show read-only, with "Start the lab server: `docker compose --profile labs up -d --build`".
- **Size:** the published page must stay under 16 MB (now 15.1 MB). Ship room text compactly: briefs and tasks only, with no walkthroughs in the static page. The controller serves walkthroughs after Finish.

## Full cleanup (user requirement, 2026-10-20)
Stopping labs must leave nothing behind:
- `docker compose --profile labs down` plus the controller's shutdown remove all `devlab=1` containers and the `devlab-net` network.
- One command, `labs/clean.sh` (also documented in DOCKER.md), removes everything labs ever created:
  - the lab containers;
  - the network;
  - the controller container;
  - the images `devops-handbook-lab:base` and `devops-handbook-labs-controller`;
  - dangling build cache for them;
  - the progress volume, only with `--all`.

  It prints what it removed and never touches the handbook container, its image, or any other container on the machine (filter by label and name only).
