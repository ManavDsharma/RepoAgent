"""search_code / read_file — ARCHITECTURE.md's Repo Context Builder tools.

Plain functions, no LLM involved (BUILD_PHASES.md Phase 1's "done when").
These are the two tools the Planner and Implementation agents will call
starting in Phase 2 — but they're built and tested standalone first.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from repoagent.indexing import store
from repoagent.indexing.embedder import embed

DEFAULT_REPO_ROOT = os.environ.get("TARGET_REPO_PATH", "target_repo/src")

_WORD_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def _keywords(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text) if len(w) > 2}


def _keyword_boost(query_words: set[str], chunk: dict) -> float:
    """Small additive boost for exact keyword overlap, per ARCHITECTURE.md's
    "semantic + keyword hybrid" spec. Kept deliberately modest (capped) so
    it nudges ties/near-ties rather than overriding semantic similarity."""
    if not query_words:
        return 0.0
    haystack = _keywords(chunk["name"] + " " + chunk["code"])
    overlap = len(query_words & haystack)
    return min(overlap * 0.03, 0.15)


def search_code(query: str, top_k: int = 5, index_dir: str | Path = store.DEFAULT_INDEX_DIR) -> list[dict]:
    """Hybrid semantic + keyword search over the indexed repo.

    Returns a list of {file, snippet, score} dicts, most relevant first.
    """
    index, chunks = store.load(index_dir)

    # Over-fetch from FAISS so the keyword boost can re-rank within a wider
    # candidate pool, then trim back to top_k.
    fetch_k = min(max(top_k * 4, 20), len(chunks))
    query_emb = embed([query])
    scores, idxs = index.search(query_emb, fetch_k)

    query_words = _keywords(query)
    results = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx == -1:
            continue
        chunk = chunks[idx]
        results.append(
            {
                "file": chunk["file"],
                "snippet": chunk["code"],
                "score": float(score) + _keyword_boost(query_words, chunk),
                "name": chunk["name"],
                "kind": chunk["kind"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            }
        )

    results.sort(key=lambda r: -r["score"])
    return results[:top_k]


def read_file(path: str, repo_root: str | Path = DEFAULT_REPO_ROOT) -> str:
    """Return a file's content with 1-indexed line numbers prefixed, so the
    Implementation Agent can produce precise, line-anchored edits."""
    full_path = Path(repo_root) / path
    if not full_path.is_file():
        raise FileNotFoundError(f"{path} not found under {repo_root}")
    lines = full_path.read_text(encoding="utf-8").splitlines()
    width = len(str(len(lines)))
    return "\n".join(f"{i + 1:>{width}}: {line}" for i, line in enumerate(lines))
