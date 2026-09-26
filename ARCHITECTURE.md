# Architecture — RepoAgent

## Graph nodes

1. **Planner** — takes the user request + repo context, produces an ordered
   task list. Single well-prompted LLM call; does not need its own tool loop.
2. **Repo Context Builder** — not a graph node, a plain service/tool layer.
   Indexes the repo (tree-sitter AST chunks → embeddings → pgvector/FAISS) and
   exposes `search_code` / `read_file` so the Planner and Implementation
   agents can retrieve relevant files.
3. **Implementation Agent** — takes one task at a time, produces a patch
   (unified diff format, not a full file rewrite) using `read_file`,
   `search_code`, `write_file`/`apply_patch`.
4. **Test Agent** — runs `run_tests` + `run_linter` inside the Docker sandbox,
   parses output into a compact failure summary.
5. **Diff + Explain** — runs `git_diff`, then one LLM call to explain the
   change in plain English.

Conditional edges: Test Agent → Implementation Agent on failure (with the
failure summary appended to state) while `retry_count < max_retries`; Test
Agent → Diff+Explain on pass; on exhausted retries, stop and surface the
failure to the human reviewer rather than looping forever.

## LangGraph state schema

```python
from typing import TypedDict, Literal

class Task(TypedDict):
    id: str
    description: str
    status: Literal["pending", "in_progress", "done", "failed"]

class RepoAgentState(TypedDict):
    request: str                      # original user request
    repo_path: str                    # path to repo inside the sandbox
    repo_context: list[str]           # relevant file paths/snippets retrieved
    task_list: list[Task]
    current_task_index: int
    patch: str                        # current unified diff being tested
    test_output: str                  # raw stdout/stderr from last test run
    test_passed: bool
    lint_output: str
    retry_count: int
    max_retries: int                  # start with 3
    final_diff: str
    explanation: str
    status: Literal["running", "awaiting_review", "failed", "done"]
```

## Tool specs

| Tool | Signature | Notes |
|---|---|---|
| `search_code(query: str, top_k: int = 5) -> list[dict]` | returns `{file, snippet, score}` | semantic + keyword hybrid over AST chunks |
| `read_file(path: str) -> str` | returns content with line numbers | needed for precise, line-anchored edits |
| `write_file(path: str, patch: str) -> bool` | applies a unified diff, not a full overwrite | safer, closer to how real coding agents operate |
| `run_tests(test_path: str = None) -> dict` | returns `{passed: bool, output: str}` | runs `pytest` inside Docker sandbox |
| `run_linter(path: str = None) -> dict` | returns `{issues: list, output: str}` | `ruff` — run before burning a test cycle |
| `git_diff() -> str` | returns unified diff of working tree | |
| `git_log(n: int = 10) -> list[str]` | optional, for "why is this code the way it is" context | not required for v1 |

All tools are exposed as plain Python functions passed to the LLM as
function-calling tools first. MCP wrapping is a stretch goal only after the
core loop works end-to-end — do not build it first.

## Failure handling

- Cap retries at `max_retries` (default 3). On exhaustion, set
  `status = "failed"` and surface the last test output to the user rather
  than silently giving up or looping indefinitely.
- Every Implementation Agent retry must receive the actual test failure
  text in its prompt — don't just re-ask it to "try again" with no feedback.
