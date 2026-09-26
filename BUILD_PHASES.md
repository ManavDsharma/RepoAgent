# Build Phases — RepoAgent

Work through these in order. Do not start a phase until the previous one's
"done when" criteria are met. At the end of each phase, update
`BUILD_SUMMARY.md` per the instructions in CLAUDE.md.

## Phase 0 — Scaffolding

- Repo/project structure, `requirements.txt` / `pyproject.toml`, Docker
  image + Compose file skeleton (even if empty), `.env.example` for API keys.
- Pick and clone one small real FastAPI repo to use as the test target
  (not a trivial hello-world app — needs enough surface area for OAuth-style
  changes to be meaningful).
- **Done when:** container builds, target repo runs and its existing tests
  pass inside the container.

## Phase 1 — Foundation (repo indexing + tools)

- `tree-sitter`-based chunking for the target repo (functions/classes).
- Embed chunks, store in pgvector (or FAISS fallback).
- Implement `search_code` and `read_file` as standalone functions, tested
  outside any agent/LLM loop first (plain unit tests against the index).
- **Done when:** you can call `search_code("authentication")` from a script
  and get back sensible, relevant file/snippet results — no LLM involved yet.

## Phase 2 — Planner + Implementation

- Planner: single LLM call, request + repo context in, structured task list
  out (use the `Task` schema from ARCHITECTURE.md).
- Implementation Agent: takes one task, produces a unified diff using
  `read_file` / `search_code` / `write_file`.
- Wire these two into a minimal LangGraph graph (no test loop yet).
- Test end-to-end on a trivial change first (e.g., "add a docstring to
  function X") before attempting anything OAuth-level.
- **Done when:** a trivial request produces a correct, applied diff.

## Phase 3 — The test-and-retry loop (core of the project)

- Wire `run_tests` + `run_linter` into the graph as the Test Agent node.
- Implement the conditional edge: failure + retries remaining → back to
  Implementation Agent with the failure text in context; failure + retries
  exhausted → `status = "failed"`, stop; pass → proceed to Diff+Explain.
- Budget the most debugging time here — this is the part interviewers will
  ask about in depth.
- **Done when:** you can run the OAuth-login request end-to-end, watch it
  fail at least once, self-correct, and pass.

## Phase 4 — Diff/Explain, frontend, polish

- `git_diff` + one LLM call to explain the change in plain English.
- Streamlit page: request input, live status of current graph node, final
  diff + explanation output.
- Pick 2-3 demo requests: OAuth login (multi-file), one smaller single-file
  change, and one that's designed to fail once so you can show the recovery
  loop on demand.
- Write the final `BUILD_SUMMARY.md` pass: make sure the "what we skipped
  and why" section is complete and honest — this is what gets talked through
  in interviews.
- **Done when:** you can run all 3 demo requests live without manual
  intervention, from the Streamlit page, with the container sandboxed.

## After Phase 4 (optional, only if time allows)

- MCP wrapping of the existing tools.
- Review Agent (LLM critiques its own diff before human approval).
- `git_log`-based context for the Planner.

Do not pull these forward into earlier phases even if they seem easy — they
are explicitly deferred in CLAUDE.md.
