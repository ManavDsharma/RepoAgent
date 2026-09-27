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

## Phase 1 — Foundation (repo indexing + tools)

**What we built this phase**

This is the "librarian" layer: it reads every Python file in the target
repo, cuts each one into meaningful pieces (a function, a class, or — for
files like `db.py` that are just top-level setup code with no functions at
all — the leftover top-level code as its own piece), turns each piece into
a vector via a small local embedding model, and stores those vectors in a
FAISS index on disk. On top of that sit the two tools the Planner and
Implementation agents will actually call later: `search_code(query)`,
which finds the most relevant pieces of code for a plain-English question,
and `read_file(path)`, which returns a file with line numbers so future
edits can be anchored precisely. Nothing here calls an LLM — it's plain
Python + a local model, verified with ordinary unit tests, exactly as
BUILD_PHASES.md asks for.

Key decision: FAISS over pgvector for the vector store. TECH_STACK.md
frames pgvector as the primary choice and FAISS as a "zero-infra fallback"
— we took the fallback deliberately. The sandbox already runs one Postgres
instance dedicated to the target app's own data; reusing it for the
agent's embeddings would mix two unrelated schemas in one database, and
standing up a *second* Postgres just to hold vectors is more infrastructure
than a local FAISS file for a demo of this size. This isn't a substitution
of an undecided library — TECH_STACK.md explicitly names FAISS as
acceptable — so it didn't need a stop-and-ask.

Embedding model: `all-MiniLM-L6-v2` (via sentence-transformers), a small,
general-purpose model, not one specialized for code. To compensate a
little, `search_code` does what ARCHITECTURE.md asks for — hybrid
semantic + keyword scoring — by adding a small, capped bonus when a
query's words appear verbatim in a chunk.

**What we skipped and why**

- BUILD_PHASES.md's own example, `search_code("authentication")`, doesn't
  apply to this target repo — it has no auth code at all (that's exactly
  why we picked it: so adding OAuth later is a real, meaningful change).
  We verified `search_code` instead with queries that match what the repo
  actually contains (e.g. "create a new note in the database"), which
  return the genuinely relevant files. Flagging this rather than quietly
  reinterpreting the spec, per CLAUDE.md's rule 5.
- Per-method sub-chunking inside classes — the target repo's classes
  (`NoteSchema`, `NoteDB`) are small Pydantic field declarations with no
  methods, so whole-class chunking is already the finest granularity that
  matters here. Worth revisiting if a future target repo has large classes.
- A code-specialized embedding model (e.g. a code-search-tuned
  sentence-transformer) — the general-purpose model is good enough for
  this repo's size (30 chunks) and keeps Phase 1 to one clear dependency;
  ranking isn't perfect (e.g. a "create a note" query ranks the `put`
  handler slightly above `post`), but every top result is genuinely
  relevant, which is what Phase 1's "done when" asks for.
