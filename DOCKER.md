# Running the handbook with Docker

Docker builds the site from the Markdown sources and serves it, so no local Python is needed.

| You want to | Run |
|---|---|
| Start it, or rebuild after editing a module | `docker compose up -d --build` |
| Open it | http://localhost:8173 |
| See the access log | `docker compose logs -f` |
| Stop it | `docker compose down` |
| Rebuild without the test gate | `docker compose build --build-arg RUN_TESTS=false && docker compose up -d` |
| Get `index.html` and `artifact.html` into this folder (for the offline copy or publishing) | `docker build --target export --output type=local,dest=. .` |

## What happens

1. **Build stage** (`python:3.12-slim`, `markdown==3.5.2`, the same versions as the local build): it runs `build_site.py`, then the unit tests (`RUN_TESTS=true` by default, so a broken build never replaces a working one), then makes gzip copies of the pages.
2. **Serve stage** (`nginxinc/nginx-unprivileged:stable-alpine`): nginx holds only the two generated pages and `docker/nginx.conf`. It sends the 14 MB page gzipped (about 4 MB), marks it `no-cache` so a rebuild shows up on the next refresh, and answers `/healthz` for the health check.
3. **Export stage**: `--target export` hands the two pages back to you. They are byte-identical to `python3 build_site.py` output.

## Hardening in `compose.yaml`

- **Network:** published on `127.0.0.1:8173` only, so it is not reachable from other machines.
- **Container:** runs as a non-root user (nginx-unprivileged) on a read-only root filesystem, with a tmpfs for `/tmp`, all Linux capabilities dropped and `no-new-privileges` set.
- **Restarts:** `restart: unless-stopped`, so after `up -d` it comes back after a reboot until you run `docker compose down`.

## Notes

- **What goes into the image:** `.dockerignore` sends only what the build reads: the modules, the Python build files, `roadmap.json`, `interview/`, `commands/`, `labs/` (the room texts for the Labs page; the page never includes answers, scripts or walkthroughs), `tests/` and the JSON catalogs in `research/`. Backups, briefs and notes stay out.
- **Port 8173:** the old `python3 -m http.server 8173` is no longer needed. If both are started, the second one fails with "address already in use".
- **Claude preview:** inside Claude Code, the `handbook-docker` entry in `.claude/launch.json` runs `docker compose up` for the in-app preview.

## Automatic cleanup (the `janitor` service)

`docker compose up -d` also starts `devops-handbook-janitor`. Two minutes after it starts, and then every hour, it removes what **this project** left behind. It selects only what it can prove this project made (table below). Anything it cannot prove is left alone.

| What | When it goes | How it is recognised |
|---|---|---|
| Older builds of the handbook, controller, lab and janitor images (untagged after a rebuild) | at the next pass | the `devops-handbook.*` labels in our Dockerfiles, or the labels Compose puts on images it built for this project's own services. An image that Compose built for another project is never ours, even if it inherits our labels from a `FROM` |
| The tagged lab images `devops-handbook-lab:base` and `devops-handbook-labs-controller` | after `JANITOR_IMAGE_KEEP_DAYS` (7) days without labs use, and only while the labs are off | the same labels. "Last used" is when the janitor last saw the labs running: it looks every 5 minutes and keeps that time in the `devops-handbook-janitor-state` volume |
| Build cache of our Dockerfiles | after `JANITOR_CACHE_KEEP_HOURS` (48) hours unused | every stage of our Dockerfiles starts with a no-op `RUN : devops-handbook-<stage>` (or `: devlab-<stage>`). That record is unique to our Dockerfiles, and everything built on top of it is ours. A record is removed only together with all its children, one record at a time by ID |
| Lab machines (label `devlab=1`) | when the labs controller is not running (a crash left them), or one hour past the lifetime limit | the label |

The lab controller itself destroys a lab machine after 30 minutes idle, or `LABS_MAX_SECONDS` (3 hours) after it started, busy or not.

**Never touched:**
- other projects' containers and images;
- any volume or network;
- base images and their "pulled from …" cache records, which other projects may share;
- generic cache steps such as `WORKDIR /src`, which BuildKit shares between Dockerfiles. For the same reason, stage names are never used to recognise our cache;
- the running handbook image and the janitor's own image.

Images are never force-removed: an image that any container uses, even a stopped one, is kept. The janitor has no network (`network_mode: none`), a read-only filesystem, no Linux capabilities, and a 128 MB memory and 64 process limit. Its only access is the Docker socket, the same as the labs controller. The socket is root-equivalent, which is why the selection rules above are tested in `tests/test_janitor.py`.

| You want to | Run |
|---|---|
| See what it did | `docker logs devops-handbook-janitor` |
| See what it would remove now, without removing anything | `python3 docker/janitor/janitor.py --once --dry-run` (a run from the host has no record of labs use, so it leaves the tagged lab images alone) |
| Clean now, ignoring the keep windows | `python3 docker/janitor/janitor.py --once --now` |
| Change the windows | put e.g. `JANITOR_CACHE_KEEP_HOURS=24` in a `.env` file next to `compose.yaml`, then `docker compose up -d` |
| Turn it off | `docker compose stop janitor` (it stays off until the next `docker compose up -d`) |

**Why an image pulled today can say "3 weeks ago":** `docker images` shows `CREATED`, which is when the publisher **built** the image, not when it reached your machine. The labels inside it (`org.opencontainers.image.created`) carry the same build date, and our handbook image inherits nginx's date that way.

Docker keeps no reliable "pulled at" date. `docker image inspect -f '{{.Metadata.LastTagTime}}' IMAGE` is set only by a local build or `docker tag`. A pulled image shows `0001-01-01` there (checked on Docker 29.2, overlay2 storage). On that storage driver, the image's config file is written when the image arrives, so its time is a close guess (needs root):

```bash
sudo stat -c '%y' /var/lib/docker/image/overlay2/imagedb/content/sha256/$(docker image inspect -f '{{.Id}}' IMAGE | cut -d: -f2)
```

If you need pull dates for audits, record them yourself: pull through a script that logs the date, or use your registry's pull log (Harbor keeps one). On this Docker setup, base images pulled during a build do not show up in `docker images` at all; they live in the build cache. The janitor only judges age by `CREATED` for images this project built itself, where that date is our own build time.

## Hands-on labs (optional, profile `labs`)

The **Hands-on labs** page (sidebar group *Labs*) works read-only everywhere. To run the rooms, start the lab server next to the handbook:

| You want to | Run |
|---|---|
| Start the labs (first time: builds the lab image, a few minutes) | `docker compose --profile labs up -d --build` |
| Open them | http://localhost:8173/#m-labs |
| Rebuild after changing a room or the lab image while the labs run | `docker compose --profile labs down`, then `docker compose --profile labs up -d --build` (rebuilding in place stops the old controller, which deletes `devlab-net` on its way out, so the new one fails once with `network devlab-net not found`; running the same `up` again also recovers) |
| Stop the labs and the handbook (every lab container and `devlab-net` are removed) | `docker compose --profile labs down` |
| Then bring back only the handbook | `docker compose up -d` |
| Stop only the labs, keep the handbook running | `docker compose --profile labs rm --stop --force labs-controller` |
| Controller log | `docker compose --profile labs logs -f labs-controller` |
| Remove everything the labs ever created | `labs/clean.sh` (`--all` also deletes your progress, `--dry-run` only lists) |
| Test the platform end to end (builds, runs the pilot room, stops, cleans) | `python3 labs/smoke_platform.py` |
| Test every room (setup, failing checks, solve, passing checks) | `python3 labs/test_rooms.py` (needs the lab image and a running labs profile, or `devlab-net`) |

How it fits together:

- **`labs-controller`** (`labs/controller/`, Python standard library plus the docker CLI) serves `/api/labs/` and starts one disposable lab machine per room: `devops-handbook-lab:base` (`labs/base/Dockerfile`, Ubuntu 24.04 with real systemd, user `lab` with passwordless sudo, ttyd for the browser terminal).
- **nginx** in the handbook container proxies `/api/labs/` to the controller and `/lab-term/<session>/` (websocket) to ttyd in lab `devlab-<session>`. It looks names up per request through Docker's DNS (`resolver 127.0.0.11`), so the handbook starts and works with the labs off; those two routes then answer 502 and the page shows the read-only view. Only the page's probe, `GET /api/labs/health`, answers 200 `{"ok":false,"labs":"off"}` instead, so the console stays clean.
- **`lab-base`** is a build-only service (`scale: 0`): compose builds the lab image but never runs it.
- **Progress** (finished rooms and points) lives in the volume `devops-handbook-labs-progress`. `down` keeps it; `labs/clean.sh --all` removes it.

Isolation, and the one privileged piece:

- **The Docker socket.** The controller mounts `/var/run/docker.sock`, which is root-equivalent on this machine. That is why it is limited by code and by its container: it only runs the lab image with the exact options in `labs/SPEC.md` (`lab_run_argv`, compared with the SPEC by `tests/test_labs_platform.py`), only execs into and removes containers labelled `devlab=1`, and only manages `devlab-net` (attaching the handbook while labs run). It publishes no port, runs read-only with all capabilities dropped and `no-new-privileges`, and has `restart: "no"`.
- **Lab machines** are not privileged: all capabilities dropped except the 11 systemd needs, 768 MB memory, 1 CPU, 512 processes, a private cgroup namespace, and only the internal network `devlab-net` (no internet, no route out, no published ports). They never restart on their own.
- **Requests from inside a lab are refused.** The controller treats every address on `devlab-net` as a lab except the handbook's own, and also rejects calls that reached nginx over `devlab-net` (nginx's `X-Lab-Via`, trusted only on requests that really come from nginx), so a lab cannot drive the controller, even while it is still booting.
- **Labs cannot open each other's terminals.** Labs share `devlab-net`, so each lab's ttyd needs basic auth with a random per-session credential (`ttyd -c lab:<token>`). Only the controller knows it; it hands it to nginx on the terminal's auth check (`X-Lab-Auth`), and nginx sends it to ttyd as `Authorization`, replacing anything the client sent. A lab that tries `http://devlab-<other>:7681` directly gets 401; through nginx it gets 403. The token is not in the page, the API answers or the logs.
- **Web guards.** The controller also refuses foreign `Host` headers, cross-site `Origin`s and non-JSON POSTs (DNS-rebinding and CSRF guards), and serves no files: never `solve.sh`, `answers.test.json`, answer hashes or check scripts (they are not even in its image).
- **Nothing is left behind.** Labs are destroyed on *Finish*, *Reset*, after 30 minutes idle, when the controller starts (leftovers) and when it stops. On stop it also detaches the handbook from `devlab-net` and deletes the network, so with the labs off there is no lab container and no lab network. Nothing is installed on the host and nothing is added to boot.
- **After an ungraceful controller death** (SIGKILL, the OOM killer, `docker kill`, a crash of the Docker daemon) the controller's own cleanup never runs: its lab containers keep running, they and the handbook stay attached to `devlab-net`, and `docker compose --profile labs down` can fail because devlab-net still "has active endpoints". Run `labs/clean.sh` then: it removes the lab containers, detaches the handbook (which keeps running) and deletes the network. The next controller start would also remove the leftover labs, but only `labs/clean.sh` is the reliable cleanup.
- **Answers and checks are a learning aid.** Answer hashes stay on the controller, but there is no rate limit on answers or Check: you are meant to try again until it passes. Progress is a record for you, not an exam.
- **Limit:** a lab is root-capable inside its container (`sudo`, `CAP_SYS_ADMIN` for systemd, AppArmor unconfined). It is a practice sandbox for your own use, not a boundary against hostile code: run only the handbook's rooms in it.

`labs/test_rooms.py` needs the lab image and `devlab-net` without the controller. Create the network with compose's labels, so a later `docker compose --profile labs up` adopts it instead of failing:

```bash
docker compose --profile labs build lab-base
docker network create --internal --label com.docker.compose.project=troubleshooting \
  --label com.docker.compose.network=devlab-net devlab-net
```

If compose reports `network devlab-net was found but has incorrect label`, the network was created without those labels. Run `labs/clean.sh`, then start the profile again. Do not run `test_rooms.py` while you use the labs in the browser: the controller removes every `devlab=1` container when it starts and stops.
