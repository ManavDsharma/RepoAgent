"""Local embeddings via sentence-transformers.

TECH_STACK.md: "sentence-transformers (local) or Voyage/OpenAI embeddings".
We use the local option — no extra API key, no extra network dependency
for a step that runs before any LLM call, keeping Phase 1 fully offline
after the model's one-time download.

Model: all-MiniLM-L6-v2 — small (~80MB), fast on CPU, the default choice
for sentence-transformers-based semantic search. It's a general-purpose
sentence embedding model, not code-specific; Phase 1's hybrid keyword
scoring (see search.py) compensates for the cases where that matters.
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts, L2-normalized so inner product == cosine similarity."""
    model = get_model()
    return np.asarray(
        model.encode(texts, normalize_embeddings=True, convert_to_numpy=True),
        dtype="float32",
    )
