# syntax=docker/dockerfile:1
#
# Labs controller (Python 3 standard library + the docker CLI). Build context: labs/
#
#   docker compose --profile labs up -d --build      (builds this, the lab base image and the handbook)
#
# The image holds the controller and the rooms' public files. Each room's solve.sh and
# answers.test.json are test-only: Dockerfile.dockerignore keeps them out of the build context,
# and the RUN below fails the build if one ever slips in.
FROM docker:29.2.1-cli AS dockercli

FROM python:3.12-slim AS devlab-controller
LABEL devops-handbook.labs="controller" \
      org.opencontainers.image.title="devops-handbook-labs-controller" \
      org.opencontainers.image.description="Starts and checks the handbook's disposable lab machines"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LABS_ROOMS_DIR=/app/rooms LABS_DATA_DIR=/data
RUN : devlab-controller
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
WORKDIR /app
COPY controller/controller.py /app/controller.py
COPY rooms/ /app/rooms/
RUN leaks="$(find /app -name solve.sh -o -name answers.test.json)" \
 && if [ -n "$leaks" ]; then echo "test-only files in the controller image: $leaks" >&2; exit 1; fi \
 && python3 -c "import ast,sys; ast.parse(open('/app/controller.py').read())" \
 && mkdir -p /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8080/api/labs/health', timeout=4)" || exit 1
STOPSIGNAL SIGTERM
CMD ["python3", "/app/controller.py"]
