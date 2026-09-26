# RepoAgent — Repository-Aware Coding Agent

## Problem Statement

Most AI coding tools generate code in isolation — they don't understand *this*
codebase's architecture, conventions, or how a change ripples across files, and
they don't verify their own work.

RepoAgent takes a natural-language change request (e.g. "Add OAuth login to
this FastAPI app"), understands the existing repo, makes the change across
however many files it touches, runs the test suite, fixes its own failures in
a loop, and hands back a reviewable diff with a plain-English explanation.

The centerpiece is the **test-and-retry loop**: act → observe test output →
replan → act again. That loop is what makes this an *agent* and not a linear
LLM pipeline — most of the engineering effort should go there, not into adding
more stages.

## Architecture (high level — full detail in ARCHITECTURE.md)

```
User request
     │
     ▼
Planner Agent  ──uses──> Repo Context Builder (search_code, read_file)
     │
     ▼
Implementation Agent ◄────────────┐
     │                            │
     ▼                            │
Test Agent (run_tests, run_linter)│
     │  fail (retries left) ──────┘
     │  pass
     ▼
Diff + Explain (git_diff + LLM explanation)
     │
     ▼
Human review / approval
```

Read ARCHITECTURE.md before writing any LangGraph node — it has the full
state schema and tool signatures.

## Explicit scope cuts — do not add these without asking first

- No Review Agent (LLM critiquing its own diff) — low signal for the effort.
- No MCP protocol wrapping for tools — plain Python function-calling tools
  only, for now.
- No multi-language support — Python/FastAPI repos only.
- No Kubernetes or cloud deployment — Docker Compose locally is enough.
- No fancy frontend — one basic screen to submit a request and watch it run.

If you think one of these should be added, flag it and explain why before
building it — don't silently expand scope.

## How to work through this project

1. Follow BUILD_PHASES.md in order. Do not start Phase 2 work until Phase 1's
   "done when" criteria are met, even if it looks quick to jump ahead.
2. Read TECH_STACK.md before installing/choosing any library — the stack is
   already decided; don't substitute alternatives without flagging it.
3. All file writes and test/lint execution happen inside the Docker sandbox
   described in TECH_STACK.md — never run agent-generated code directly on
   the host.
4. At the end of every phase, update `BUILD_SUMMARY.md` (create it if it
   doesn't exist yet) with two short sections in plain, non-jargon language:
   - **What we built this phase** — a few sentences a non-engineer could
     follow, plus the key design decision(s) made and why.
   - **What we skipped and why** — anything cut from the original spec,
     deferred, or simplified, with the reason.
   Keep entries short — this file is for explaining the project in an
   interview, not a commit log.
5. If something in the spec turns out to be wrong or impractical once you're
   actually building it, say so and propose the change rather than quietly
   deviating.
