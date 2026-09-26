# RepoAgent's own tests

Unit tests for RepoAgent's *own* code (indexing, tools, graph) — not the
target repo's tests, which live under `target_repo/src/tests/` and run
inside the sandbox.

Phase 1 per BUILD_PHASES.md: plain unit tests for `search_code`/`read_file`
against the index, no LLM involved. Empty for now.
