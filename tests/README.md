# RepoAgent's own tests

Unit tests for RepoAgent's *own* code (indexing, tools, graph) — not the
target repo's tests, which live under `target_repo/src/tests/` and run
inside the sandbox.

Run from the repo root, using RepoAgent's own host venv (not the sandbox):

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

`test_indexing.py` (Phase 1) covers the chunker directly, plus
`search_code`/`read_file` against a real index built from `target_repo/`.
No LLM involved — the local sentence-transformers model is a one-time
download, not an API call.
