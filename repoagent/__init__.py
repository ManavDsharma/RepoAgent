"""RepoAgent — repository-aware coding agent.

This package holds RepoAgent's own orchestration code (Planner,
Implementation Agent, Test Agent, Diff+Explain, LangGraph wiring, tools,
indexing, and the API/frontend layers). It runs on the host; only calls
that touch the target repo's files or execute arbitrary code cross into
the Docker sandbox (see docker-compose.yml and TECH_STACK.md).

Subpackages (filled in as BUILD_PHASES.md phases land — see that file for
what belongs where and when):
    indexing/   Phase 1 — tree-sitter chunking + embeddings + search_code/read_file
    tools/      Phase 1-3 — write_file, run_tests, run_linter, git_diff, git_log
    graph/      Phase 2-3 — LangGraph nodes/edges (state schema: ARCHITECTURE.md)
    api/        Phase 4 — FastAPI service exposing the graph to the frontend
"""
