# RepoAgent

Repository-aware coding agent. See `CLAUDE.md` for the problem statement and
scope, `ARCHITECTURE.md` for the graph/state/tool design, `TECH_STACK.md`
for the chosen stack, and `BUILD_PHASES.md` for the order of work. Progress
and design decisions per phase are logged in `BUILD_SUMMARY.md`.

## Project layout

```
repoagent/          RepoAgent's own orchestration code (runs on the host)
  indexing/         Phase 1 — tree-sitter chunking, embeddings, search_code/read_file
  tools/            Phase 1/3 — write_file, run_tests, run_linter, git_diff, git_log
  graph/            Phase 2/3 — LangGraph state schema + nodes/edges
  api/              Phase 4 — FastAPI service
frontend/           Phase 4 — Streamlit demo page
tests/              RepoAgent's own unit tests (not the target repo's)
target_repo/        The FastAPI repo RepoAgent operates on (gitignored, cloned by setup)
docker/             Sandbox image (target repo deps + pytest/ruff)
docker-compose.yml  Sandbox: db (Postgres) + sandbox (target repo mounted as a volume)
scripts/            Operational helpers (e.g. resetting target_repo between demo runs)
```

## Target repo

[`testdrivenio/fastapi-crud-async`](https://github.com/testdrivenio/fastapi-crud-async) —
a small async Notes CRUD API (FastAPI + SQLAlchemy core + Postgres, pytest
suite with mocked DB calls). It has no auth yet, which is what makes "add
OAuth login" a meaningful, clearly-scoped multi-file change rather than one
that overlaps existing auth code.

## Setup

```bash
# 1. Clone the target repo (already done if you're reading this after Phase 0 setup)
git clone https://github.com/testdrivenio/fastapi-crud-async.git target_repo

# 2. Copy env template and fill in ANTHROPIC_API_KEY
cp .env.example .env

# 3. Build and start the sandbox (Postgres + target repo container)
docker compose up -d --build

# 4. Confirm the target repo's own tests pass inside the sandbox
docker compose exec sandbox pytest

# 5. (RepoAgent's own orchestration code, once it exists) — runs on the host:
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
```

Reset `target_repo/` to a clean state between demo runs with
`scripts/reset_target_repo.sh`.
