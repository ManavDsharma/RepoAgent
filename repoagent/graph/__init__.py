"""LangGraph wiring — Phases 2-3.

Will hold the RepoAgentState TypedDict schema and the graph nodes/edges
from ARCHITECTURE.md: Planner -> Implementation Agent -> Test Agent ->
(loop on failure / proceed on pass) -> Diff+Explain.

Read ARCHITECTURE.md in full before adding anything here — it has the
state schema and the conditional-edge retry logic this package implements.

Empty scaffold for now.
"""
