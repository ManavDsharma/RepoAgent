"""Repo Context Builder (Phase 1).

tree-sitter chunking (chunker.py) -> local embeddings (embedder.py) ->
FAISS index (store.py) -> search_code/read_file (search.py), orchestrated
by build.py. No LLM involved anywhere in this package — that starts with
the Planner in Phase 2.
"""

from repoagent.indexing.search import read_file, search_code

__all__ = ["search_code", "read_file"]
