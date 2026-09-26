# Sandbox image: Python + the TARGET repo's own dependencies, plus the
# test/lint tools RepoAgent needs to run against it (pytest, ruff).
#
# TECH_STACK.md is explicit that all write_file / run_tests / run_linter
# calls happen inside this container, never on the host. The target repo's
# source is mounted as a volume at runtime (see ../docker-compose.yml), so
# this image only needs to bake in dependencies, not the code itself.

FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Build deps for psycopg2 / asyncpg wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc git \
    && rm -rf /var/lib/apt/lists/*

# Install the target repo's own runtime + test dependencies (baked at build
# time). The source itself is mounted as a volume, so this layer only goes
# stale if requirements.txt changes.
COPY target_repo/src/requirements.txt /tmp/target-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/target-requirements.txt \
    # The target repo pins fastapi==0.87.0/starlette==0.21.0 (late 2022) but
    # not anyio. Unpinned, pip resolves today's anyio, which removed the
    # start_blocking_portal API that this Starlette's TestClient needs —
    # breaking every test at import time with no code change of our own.
    # Pin the era-appropriate anyio instead of patching the target repo's
    # own requirements.txt, so target_repo/ stays an unmodified checkout.
    && pip install --no-cache-dir "anyio==3.6.2"

# Linter is RepoAgent's own tool, not a target repo dependency.
RUN pip install --no-cache-dir ruff==0.6.9

# Keep the container running so the agent can `docker compose exec` into it
# for individual write_file / run_tests / run_linter calls.
CMD ["sleep", "infinity"]
