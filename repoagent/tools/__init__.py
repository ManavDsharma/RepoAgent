"""Agent tools — plain Python function-calling tools (ARCHITECTURE.md).

Will hold: write_file/apply_patch, run_tests, run_linter, git_diff, git_log.
All of these execute against the target repo inside the Docker sandbox
(TECH_STACK.md) — never directly on the host. search_code/read_file live in
repoagent.indexing instead, since Phase 1 treats them as part of the Repo
Context Builder.

Plain function-calling only — no MCP wrapping (CLAUDE.md scope cut).

Empty scaffold for now — lands in Phase 1 (read_file only, via indexing) and
Phase 3 (run_tests/run_linter/git_diff, wired into the Test Agent node).
"""
