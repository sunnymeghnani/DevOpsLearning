# syntax=docker/dockerfile:1
#
# DevOps Field Handbook: build the offline page from the Markdown sources, then serve it.
#
#   docker compose up -d --build                                    -> http://localhost:8173
#   docker build --target export --output type=local,dest=. .       -> writes index.html + artifact.html here
#   docker compose build --build-arg RUN_TESTS=false                -> skip the test gate
#
# Stage 1 (handbook-build) runs build_site.py and the unit tests; stage 2 (handbook-serve) is an
# unprivileged nginx that only holds the two generated pages; stage 3 (export) hands the pages back to you.
# Each stage starts with a no-op `RUN : devops-handbook-<stage>`: its build cache record is unique to
# this Dockerfile, so docker/janitor/janitor.py can tell this project's cache from other projects'.

ARG PYTHON_VERSION=3.12

# --------------------------------------------------------------------------- build
FROM python:${PYTHON_VERSION}-slim AS handbook-build
RUN : devops-handbook-build
ARG RUN_TESTS=true
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
# node: the tests syntax-check every inline <script> with `node --check` (build stage only)
RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*
# same Markdown version as the local build, so the output is identical
RUN pip install --root-user-action=ignore "markdown==3.5.2"
COPY . .
RUN python3 build_site.py \
 && if [ "$RUN_TESTS" = "true" ]; then python3 -m unittest discover -s tests; fi \
 && gzip -9 --keep index.html artifact.html

# --------------------------------------------------------------------------- serve
FROM nginxinc/nginx-unprivileged:stable-alpine AS handbook-serve
LABEL devops-handbook.project="handbook"
RUN : devops-handbook-serve
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=handbook-build /src/index.html /src/index.html.gz /src/artifact.html /src/artifact.html.gz /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1

# --------------------------------------------------------------------------- export
FROM scratch AS handbook-export
COPY --from=handbook-build /src/index.html /src/artifact.html /
FROM handbook-export AS export

# the default target is the web server
FROM handbook-serve
