# syntax=docker/dockerfile:1
#
# Handbook janitor (compose service `janitor`): Python standard library only, it talks to the Docker
# Engine API over the mounted socket. It removes only what this project created (see janitor.py).
FROM python:3.12-slim AS handbook-janitor
LABEL devops-handbook.project="janitor" \
      org.opencontainers.image.title="devops-handbook-janitor" \
      org.opencontainers.image.description="Removes this handbook's own old builds, build cache and leftover lab machines"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN : devops-handbook-janitor
COPY janitor.py /app/janitor.py
RUN python3 -c "import ast; ast.parse(open('/app/janitor.py').read())"
CMD ["python3", "/app/janitor.py"]
