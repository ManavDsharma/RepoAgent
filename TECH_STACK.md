# Tech Stack — RepoAgent

| Layer | Choice | Why |
|---|---|---|
| Language | Python | Matches the repos being modified (simplifies AST parsing); consistent with existing experience |
| LLM | Claude (Sonnet) via Anthropic API | Strong tool-use reliability, large context for repo-scale work |
| Orchestration | **LangGraph** | Explicit nodes/edges map directly to the Planner → Implement → Test → (loop) architecture; makes the retry loop demoable as an actual graph |
| Code parsing | `tree-sitter` (Python bindings) | Industry-standard AST parser; chunk by function/class, not raw lines |
| Embeddings + search | `sentence-transformers` (local) or Voyage/OpenAI embeddings + **pgvector** (FAISS as a zero-infra fallback) | Structured, queryable vector store; pgvector keeps infra simple for a local demo |
| Execution sandbox | **Docker container**, mounting the target repo as a volume | All `write_file`, `run_tests`, `run_linter` calls execute inside the container — never on the host. This is a required safety boundary, not optional |
| Test/lint | `pytest` + `ruff` | Fast, structured, easy-to-parse output to feed back into the retry loop |
| Version control ops | `GitPython` or direct `git` subprocess calls | Keep this thin — just `git_diff` / `git_log` wrappers |
| API layer | FastAPI | Exposes the graph as a service the frontend calls |
| Frontend | **Streamlit**, single page | One input box for the request, a live view of the current graph node/state, and the final diff + explanation. This is a demo aid, not a product — do not invest in styling or multi-page flows |
| Tracing/logging | Structured JSON logs to a local file or SQLite (LangSmith if already using LangGraph and want a UI for it) | Needed so you can show the full decision trace, including retries, in an interview |

## Docker sandbox details

- One container image with Python + the target repo's dependencies installed.
- The target repo is mounted as a volume so file edits persist and are
  inspectable from the host after a run.
- `run_tests` and `run_linter` execute via `docker exec` (or an equivalent
  subprocess-into-container call) — the agent process itself can run outside
  the container, but anything that touches repo files or runs arbitrary code
  must go through it.
- Reset the container (or the mounted repo copy) between demo runs so each
  run starts from a clean state.

## Explicitly out of scope for this stack

- No Kubernetes, no cloud deployment — Docker Compose locally is sufficient.
- No MCP server for tools yet — plain function-calling tools first.
- No multi-language tree-sitter grammars — Python only for v1.
- No frontend framework (React etc.) — Streamlit is enough for the demo.
