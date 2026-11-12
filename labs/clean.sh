#!/usr/bin/env bash
# Remove everything the hands-on labs created (labs/SPEC.md, "Full cleanup").
#
#   labs/clean.sh          lab containers (label devlab=1), the controller container, the devlab-net
#                          network, the images devops-handbook-lab:base and devops-handbook-labs-controller
#                          (and older untagged builds of them), and their build cache (via docker/janitor/janitor.py)
#   labs/clean.sh --all    the same, plus the progress volume devops-handbook-labs-progress
#                          (finished rooms and points)
#   labs/clean.sh --dry-run   print what would be removed, remove nothing
#
# Selection is by label and exact name only. The handbook container (devops-handbook), its image
# (devops-handbook:local) and every other container, image, network and volume on the machine are
# left alone. The one exception is a network attachment: while labs run, the controller attaches
# the handbook container to devlab-net; if a crashed controller left it attached, this script detaches
# it (the handbook keeps running) so the lab network can be deleted.
set -uo pipefail

ALL=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --all) ALL=1 ;;
    --dry-run|-n) DRY=1 ;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

LAB_IMAGE="devops-handbook-lab:base"
CTL_IMAGE="devops-handbook-labs-controller"
CTL_NAME="devops-handbook-labs"
NETWORK="devlab-net"
VOLUME="devops-handbook-labs-progress"
IMAGE_LABEL="devops-handbook.labs"           # set by labs/base/Dockerfile and labs/controller/Dockerfile
# Build cache is removed by docker/janitor/janitor.py --labs-cache: every record under the no-op
# `RUN : devlab-base` / `RUN : devlab-controller` that starts each lab Dockerfile stage (those records are
# unique to our Dockerfiles), and nothing else. Stage names and step text are not used: BuildKit shares
# generic steps between Dockerfiles, so they could match other projects' build cache.
JANITOR="$(cd "$(dirname "$0")/.." && pwd)/docker/janitor/janitor.py"

if ! command -v docker >/dev/null 2>&1; then echo "docker CLI not found" >&2; exit 1; fi
if ! docker info >/dev/null 2>&1; then echo "cannot talk to the Docker daemon" >&2; exit 1; fi

removed=0
say() { printf '  %s\n' "$*"; }
run() {   # run "$@" unless --dry-run; count successes
  if [ "$DRY" = 1 ]; then return 0; fi
  "$@" >/dev/null 2>&1
}
R="removed"; D="detached"; DONE="removed"
if [ "$DRY" = 1 ]; then echo "Dry run: nothing is removed."; R="would remove"; D="would detach"; DONE="to remove"; fi

# 1. the controller first: a graceful stop lets it remove its labs and devlab-net itself
echo "Labs controller container:"
ctl_ids=$( { docker ps -aq --filter "name=^/${CTL_NAME}\$" --filter "label=com.docker.compose.service=labs-controller"
             docker ps -aq --filter "ancestor=${CTL_IMAGE}"; } 2>/dev/null | sort -u)
if [ -z "$ctl_ids" ]; then say "none"; fi
for id in $ctl_ids; do
  name=$(docker inspect -f '{{.Name}}' "$id" 2>/dev/null | sed 's#^/##')
  [ "$name" = "devops-handbook" ] && continue          # never the handbook (belt and braces)
  run docker stop -t 60 "$id"
  if run docker rm -f "$id"; then say "$R container $name"; removed=$((removed + 1)); else say "could not remove $name"; fi
done

# 2. lab machines: everything labelled devlab=1, plus anything started from the lab image
echo "Lab containers (label devlab=1):"
lab_ids=$( { docker ps -aq --filter "label=devlab=1"; docker ps -aq --filter "ancestor=${LAB_IMAGE}"; } 2>/dev/null | sort -u)
if [ -z "$lab_ids" ]; then say "none"; fi
for id in $lab_ids; do
  name=$(docker inspect -f '{{.Name}}' "$id" 2>/dev/null | sed 's#^/##')
  case "$name" in devops-handbook|"$CTL_NAME") continue ;; esac
  if run docker rm -f -v "$id"; then say "$R container $name"; removed=$((removed + 1)); else say "could not remove $name"; fi
done

# 3. the lab network
echo "Network ${NETWORK}:"
if docker network inspect "$NETWORK" >/dev/null 2>&1; then
  for name in $(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$NETWORK" 2>/dev/null); do
    if run docker network disconnect -f "$NETWORK" "$name"; then say "$D $name from ${NETWORK} (the container itself is untouched)"; fi
  done
  if run docker network rm "$NETWORK"; then say "$R network ${NETWORK}"; removed=$((removed + 1)); else say "could not remove ${NETWORK}: $(docker network rm "$NETWORK" 2>&1 | tail -n1)"; fi
else
  say "none"
fi

# 4. images: the two tags, then any older untagged build that carries the labs label
echo "Images:"
img_found=0
for ref in "$LAB_IMAGE" "$CTL_IMAGE"; do
  if docker image inspect "$ref" >/dev/null 2>&1; then
    img_found=1
    if run docker image rm -f "$ref"; then say "$R image $ref"; removed=$((removed + 1)); else say "could not remove image $ref"; fi
  fi
done
for id in $(docker images -aq --filter "label=${IMAGE_LABEL}" 2>/dev/null | sort -u); do
  img_found=1
  tags=$(docker image inspect -f '{{join .RepoTags ","}}' "$id" 2>/dev/null)
  case ",$tags," in *",devops-handbook:local,"*) continue ;; esac   # never the handbook image
  if run docker image rm -f "$id"; then say "$R image ${id} ${tags:-(untagged older build)}"; removed=$((removed + 1)); fi
done
[ "$img_found" = 0 ] && say "none"

# 5. build cache of the lab Dockerfiles (the janitor follows each record's children, leaves first)
echo "Build cache:"
if command -v python3 >/dev/null 2>&1 && [ -f "$JANITOR" ]; then
  if [ "$DRY" = 1 ]; then
    python3 -I "$JANITOR" --labs-cache --dry-run | sed 's/^[0-9-]* [0-9:]* janitor: /  /'
  else
    python3 -I "$JANITOR" --labs-cache | sed 's/^[0-9-]* [0-9:]* janitor: /  /'
  fi
else
  say "skipped: needs python3 and docker/janitor/janitor.py"
fi

# 6. progress (only with --all)
echo "Progress volume ${VOLUME}:"
if docker volume inspect "$VOLUME" >/dev/null 2>&1; then
  if [ "$ALL" = 1 ]; then
    if run docker volume rm "$VOLUME"; then say "$R volume ${VOLUME}"; removed=$((removed + 1)); else say "could not remove ${VOLUME} (in use?)"; fi
  else
    say "kept (your finished rooms and points); add --all to remove it"
  fi
else
  say "none"
fi

left=$(docker ps -aq --filter "label=devlab=1" | wc -l)
echo "Done: ${removed} item(s) ${DONE}; lab containers left: ${left}."
[ "$DRY" = 1 ] || [ "$left" -eq 0 ]
