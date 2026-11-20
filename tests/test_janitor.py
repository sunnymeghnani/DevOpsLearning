"""The janitor (docker/janitor/janitor.py) must only ever select what this project created."""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("janitor", ROOT / "docker" / "janitor" / "janitor.py")
J = importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)

NOW = 2_000_000_000.0
H = 3600.0
D = 86400.0


def iso(t):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.123456789Z")


def rec(rid, desc, age_h, parents=(), key="Parents", in_use=False, size=1000):
    r = {"ID": rid, "Description": desc, "LastUsedAt": iso(NOW - age_h * H), "CreatedAt": iso(NOW - age_h * H),
         "InUse": in_use, "Size": size, "Type": "regular"}
    if parents:
        r[key] = list(parents)
    return r


def snap(containers=(), images=(), cache=(), project="troubleshooting", self_image="sha256:janitor"):
    return {"containers": list(containers), "images": list(images), "cache": list(cache),
            "project": project, "self_image": self_image}


def kinds(actions, kind):
    return {a[1] for a in actions if a[0] == kind}


class CacheSelection(unittest.TestCase):
    def test_marks_and_descendants_are_ours_and_nothing_else(self):
        cache = [
            rec("base", "pulled from docker.io/library/python:3.12-slim@sha256:aa", 500),
            rec("root", "mount / from exec /bin/sh -c : devops-handbook-build", 500, ["base"]),
            rec("wd", "[handbook-build 3/7] WORKDIR /src", 500, ["root"]),
            rec("copy", "[handbook-build 6/7] COPY . .", 500, ["wd"], key=" Parents"),   # Docker 29.2 spelling
            rec("lab", "mount / from exec /bin/sh -c : devlab-base", 500, ["ubuntu"]),
            rec("vm", "mount / from exec /bin/sh -c : devops-handbook-vm", 500, ["ubuntu"]),
            rec("vmapt", "mount / from exec /bin/sh -c apt-get update && apt-get install -y qemu-system-x86", 500, ["vm"]),
            rec("labapt", "mount / from exec /bin/sh -c apt-get update && apt-get install -y nginx-light ttyd", 500,
                ["lab"]),
            rec("export", "[handbook-export 1/1] COPY --from=handbook-build /src/index.html /src/artifact.html /", 500),
            # other projects: never ours, even when a generic step carries one of our stage names
            # (BuildKit shares `WORKDIR /src` between Dockerfiles and keeps the first description)
            rec("sharedwd", "[handbook-build 2/6] WORKDIR /src", 500, ["base"]),
            rec("theirs", "[build 3/6] COPY requirements.txt ./", 500, ["sharedwd"]),
            rec("theirpip", "mount / from exec /bin/sh -c pip install -r requirements.txt", 500, ["theirs"]),
            rec("go", "[build 3/6] COPY go.mod go.sum ./", 500, ["base"]),
            rec("nginx", "[build 3/7] COPY docker/nginx.conf /etc/nginx/conf.d/default.conf", 500),
            rec("site", "mount / from exec /bin/sh -c python3 build_site.py", 500),
            rec("md", 'mount / from exec /bin/sh -c pip install "markdown==3.5.2"', 500),
            rec("ctl", "[devlab-controller 2/6] COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker", 500),
            rec("noop", "mount / from exec /bin/sh -c : devops-handbook-build && rm -rf /", 500),
            rec("jenkins", "pulled from docker.io/jenkins/jenkins:lts@sha256:bb", 500),
        ]
        self.assertEqual(J.our_cache_ids(cache), {"root", "wd", "copy", "lab", "labapt", "vm", "vmapt", "export"})

    def test_a_parent_goes_only_with_all_its_children(self):
        cache = [rec("root", "mount / from exec /bin/sh -c : devops-handbook-build", 99),
                 rec("old", "[handbook-build 4/5] COPY . .", 99, ["root"]),
                 rec("fresh", "[handbook-build 4/5] COPY . .", 1, ["root"])]   # parent LastUsedAt is stale
        self.assertEqual(kinds(J.plan(snap(cache=cache), NOW, {}, keep_cache_h=48), "cache"), {"old"})
        cache[2] = rec("fresh", "[handbook-build 4/5] COPY . .", 60, ["root"])
        self.assertEqual(kinds(J.plan(snap(cache=cache), NOW, {}, keep_cache_h=48), "cache"), {"root", "old", "fresh"})

    def test_keep_window_and_in_use(self):
        cache = [rec("old", "mount / from exec /bin/sh -c : devops-handbook-build", 49),
                 rec("fresh", "mount / from exec /bin/sh -c : devops-handbook-serve", 47),
                 rec("busy", "mount / from exec /bin/sh -c : devlab-base", 99, in_use=True)]
        got = kinds(J.plan(snap(cache=cache), NOW, {}, keep_cache_h=48), "cache")
        self.assertEqual(got, {"old"})
        got = kinds(J.plan(snap(cache=cache), NOW, {}, keep_cache_h=0), "cache")
        self.assertEqual(got, {"old", "fresh"})

    def test_parents_key_spellings(self):
        self.assertEqual(J.parents({"Parents": ["a"]}), ["a"])
        self.assertEqual(J.parents({" Parents": ["b"]}), ["b"])           # Docker 29.2
        self.assertEqual(J.parents({"Parent": "c"}), ["c"])
        self.assertEqual(J.parents({}), [])

    @unittest.skipUnless((ROOT / "Dockerfile").is_file(), "Dockerfiles are not in the image build context")
    def test_every_stage_of_ours_starts_with_its_mark(self):
        """The first step after FROM in every stage of ours is a no-op RUN whose record is ours."""
        files = [ROOT / "Dockerfile", ROOT / "labs" / "base" / "Dockerfile",
                 ROOT / "labs" / "controller" / "Dockerfile", ROOT / "docker" / "janitor" / "Dockerfile",
                 ROOT / "labs" / "vm" / "Dockerfile"]
        for f in files:
            stages = re.split(r"^(?=FROM )", f.read_text(), flags=re.M)[1:]
            for block in stages:
                head = block.split("\n", 1)[0]
                stage = head.split(" AS ")[-1].strip() if " AS " in head else ""
                if stage in ("dockercli", "export") or head.startswith("FROM handbook-serve"):
                    continue                             # a copy source / aliases without steps of their own
                steps = [ln for ln in block.splitlines()[1:]
                         if re.match(r"(RUN|COPY|ADD|WORKDIR)\b", ln)]
                if stage == "handbook-export":           # FROM scratch: no shell, its COPY is the mark
                    self.assertTrue(J.CACHE_MARKS.search(f"[{stage} 1/1] " + steps[0]), f.name)
                    continue
                self.assertTrue(steps[0].startswith("RUN : "), f"{f.name} {stage}: {steps[0]}")
                desc = "mount / from exec /bin/sh -c " + steps[0][4:]
                self.assertTrue(J.CACHE_MARKS.search(desc), f"{f.name} {stage}: {desc}")
        vm = (ROOT / "labs" / "vm" / "Dockerfile").read_text()
        self.assertIn('LABEL devops-handbook.project="vm"', vm)   # the janitor sees its old builds as ours
        hb = (ROOT / "Dockerfile").read_text()
        self.assertIn('LABEL devops-handbook.project="handbook"', hb)
        self.assertIn("AS export", hb)                   # `docker build --target export` still works


class ImageSelection(unittest.TestCase):
    def img(self, iid, tags=(), labels=None, age_d=3):
        return {"Id": iid, "RepoTags": list(tags) or ["<none>:<none>"], "Labels": labels or {},
                "Created": int(NOW - age_d * D)}

    def test_only_our_untagged_builds(self):
        compose_ours = {"com.docker.compose.project": "troubleshooting", "com.docker.compose.service": "handbook"}
        images = [
            self.img("old-hb", labels=compose_ours),
            self.img("old-new", labels={"devops-handbook.project": "handbook"}),
            self.img("other-project", labels={"com.docker.compose.project": "handyman",
                                              "com.docker.compose.service": "backend"}),
            self.img("same-project-unknown-service", labels={"com.docker.compose.project": "troubleshooting",
                                                             "com.docker.compose.service": "something"}),
            self.img("no-labels"),
            self.img("in-use", labels=compose_ours),
            self.img("too-young", labels=compose_ours, age_d=0.001),
            self.img("hb", ["devops-handbook:local"], {"devops-handbook.project": "handbook"}),
            self.img("sha256:janitor", ["devops-handbook-janitor:local"], {"devops-handbook.project": "janitor"}),
            self.img("theirs-tagged", ["handyman-backend:latest"], {"com.docker.compose.project": "handyman"}),
            # built by another compose project FROM one of ours: it inherits our label, but is not ours
            self.img("inherits", labels={"devops-handbook.project": "handbook",
                                         "com.docker.compose.project": "someone-else",
                                         "com.docker.compose.service": "web"}),
        ]
        containers = [{"Id": "c1", "ImageID": "in-use", "State": "exited", "Names": ["/someone"], "Labels": {}}]
        got = kinds(J.plan(snap(containers, images), NOW, {}), "image")
        self.assertEqual(got, {"old-hb", "old-new"})

    def test_lab_images_expire_only_when_labs_are_idle_long_enough(self):
        lab = self.img("labimg", ["devops-handbook-lab:base"], {"devops-handbook.labs": "base"}, age_d=30)
        ctl = self.img("ctlimg", ["devops-handbook-labs-controller:latest"], {"devops-handbook.labs": "controller"},
                       age_d=30)
        self.assertEqual(kinds(J.plan(snap(images=[lab, ctl]), NOW, {}), "image"), {"labimg", "ctlimg"})
        recent = {"labs_last_seen": NOW - 2 * D}
        self.assertEqual(kinds(J.plan(snap(images=[lab, ctl]), NOW, recent), "image"), set())
        running = [{"Id": "x", "ImageID": "ctlimg", "State": "running", "Names": ["/devops-handbook-labs"],
                    "Labels": {}}]
        state = {}
        self.assertEqual(kinds(J.plan(snap(running, [lab, ctl]), NOW, state), "image"), set())
        self.assertEqual(state["labs_last_seen"], NOW)   # remembered for the keep window
        # a host run with no record of labs use leaves the tagged lab images alone
        self.assertEqual(kinds(J.plan(snap(images=[lab, ctl]), NOW, {}, keep_image_d=None), "image"), set())


class ContainerSelection(unittest.TestCase):
    def c(self, cid, labels, age_h=2, state="running", name=None):
        return {"Id": cid, "Labels": labels, "State": state, "Created": int(NOW - age_h * H),
                "Names": ["/" + (name or cid)], "ImageID": "img-" + cid}

    def test_only_lab_machines_and_only_when_orphaned_or_too_old(self):
        others = [self.c("handyman-frontend", {"com.docker.compose.project": "handyman"}),
                  self.c("portainer", {}), self.c("ollama-web", {}, state="exited"),
                  self.c("devops-handbook", {"com.docker.compose.project": "troubleshooting"})]
        lab = self.c("devlab-aaaaaaaaaaaa", {"devlab": "1"})
        young = self.c("devlab-bbbbbbbbbbbb", {"devlab": "1"}, age_h=0.05)
        # controller not running: the lab machine is a leftover
        self.assertEqual(kinds(J.plan(snap(others + [lab, young]), NOW, {}), "container"), {"devlab-aaaaaaaaaaaa"})
        # controller running: only past the lifetime limit plus an hour
        ctl = self.c("devops-handbook-labs", {}, name="devops-handbook-labs")
        self.assertEqual(kinds(J.plan(snap(others + [ctl, lab]), NOW, {}, lab_max_h=3), "container"), set())
        old = self.c("devlab-cccccccccccc", {"devlab": "1"}, age_h=4.5)
        self.assertEqual(kinds(J.plan(snap(others + [ctl, old]), NOW, {}, lab_max_h=3), "container"),
                         {"devlab-cccccccccccc"})


class Timestamps(unittest.TestCase):
    def test_ts(self):
        self.assertEqual(J.ts("2026-06-07T14:59:13.878475628Z"), J.ts("2026-06-07T14:59:13.878475Z"))
        self.assertAlmostEqual(J.ts("2026-06-07T20:29:13+05:30"), J.ts("2026-06-07T14:59:13Z"))
        self.assertIsNone(J.ts("0001-01-01T00:00:00Z"))
        self.assertIsNone(J.ts(None))
        self.assertEqual(J.ts(1700000000), 1700000000.0)


class ComposeService(unittest.TestCase):
    @unittest.skipUnless((ROOT / "compose.yaml").is_file(), "compose.yaml is not in the image build context")
    def test_janitor_is_locked_down(self):
        compose = (ROOT / "compose.yaml").read_text()
        block = re.search(r"^  janitor:\n(.*?)(?=^  \S|^\S)", compose, re.M | re.S).group(1)
        for needle in ("network_mode: none", "read_only: true", "- ALL", "no-new-privileges:true",
                       "/var/run/docker.sock:/var/run/docker.sock", "image: devops-handbook-janitor:local"):
            self.assertIn(needle, block)
        for banned in ("ports:", "privileged", "profiles:"):
            self.assertNotIn(banned, re.sub(r"#.*", "", block))

    def test_janitor_never_uses_broad_prune(self):
        src = (ROOT / "docker" / "janitor" / "janitor.py").read_text()
        code = re.sub(r"#.*", "", re.sub(r'""".*?"""', "", src, flags=re.S))
        for banned in ("system prune", "/images/prune", "/containers/prune", "/volumes", "/networks"):
            self.assertNotIn(banned, code)
        self.assertNotIn('"force"', code.split("def execute")[1].split('elif kind == "image"')[1].split("else:")[0])
        self.assertIn('"filters": {"id": [oid]}', code)   # build cache only by record id


if __name__ == "__main__":
    unittest.main()
