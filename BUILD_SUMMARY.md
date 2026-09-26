# Build Summary

Plain-language log of what got built each phase and what was deliberately
cut or deferred — written for talking through in an interview, not as a
commit log. See BUILD_PHASES.md for the phase definitions.

## Phase 0 — Scaffolding

**What we built this phase**

We set up the project skeleton and picked the "customer" codebase the agent
will actually modify later: `testdrivenio/fastapi-crud-async`, a small
FastAPI Notes API with a Postgres database and a real pytest suite. It has
no login system yet, which matters — it means "add OAuth login" in a later
phase will be a genuine, multi-file change instead of something that
overlaps code that's already there.

The key design decision was how to sandbox that repo. The spec calls for
all file writes and test/lint runs to happen inside Docker, never on the
host — so we built a two-container setup (`docker-compose.yml`): one
container runs Postgres (the target app actually connects to a real
database on startup, so it can't run standalone), and the other has the
target repo's dependencies pre-installed with the repo itself mounted in
live, so edits show up immediately without rebuilding the image. RepoAgent's
own code (the part that will do the planning and LLM calls) is a separate
Python environment that runs on the host — only the actions that touch
repo files or execute code cross into the containers.

One real snag: the target repo pins FastAPI/Starlette from late 2022 but
never pinned `anyio`, so a plain `pip install` today pulls in a much newer
`anyio` whose API changed just enough to break every test at import time —
before we'd changed a single line of the app's own code. We fixed this by
pinning an era-matching `anyio` version in our own Docker image rather than
editing the target repo's `requirements.txt`, so the target repo stays an
untouched, resettable checkout (`scripts/reset_target_repo.sh` puts it back
to a clean state between demo runs).

Verified end-to-end inside the container: the image builds, the app boots
and answers requests (`/ping` → `{"ping":"pong!"}`), its full test suite
passes (15/15), and `ruff` runs clean.

**What we skipped and why**

- Everything past scaffolding — indexing, the LLM tools, the LangGraph
  wiring, the frontend. BUILD_PHASES.md is explicit that Phase 1 doesn't
  start until Phase 0's "done when" criteria are met, so none of that is
  built yet; this phase is purely repo/Docker setup.
- `pyproject.toml` in favor of `requirements.txt` for RepoAgent's own deps —
  simpler for a straightforward pip-install flow, no packaging needed yet.
- A vector store choice for embeddings isn't locked in yet (that's Phase
  1's call); TECH_STACK.md allows either pgvector or FAISS and we haven't
  needed to decide until indexing actually gets built.
