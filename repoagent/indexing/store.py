"""Persisted vector index: FAISS + a JSON sidecar for chunk metadata.

TECH_STACK.md frames pgvector as the primary choice and FAISS as "a
zero-infra fallback". We use FAISS here: the sandbox already runs one
Postgres instance dedicated to the target app's own data (see
docker-compose.yml), and standing up a second database — or mixing the
agent's own index into the target app's schema — adds infra for a local
demo without buying anything pgvector would that FAISS doesn't at this
scale. FAISS is a plain file on disk, needs no running service, and is
trivial to rebuild. Logged here per CLAUDE.md's "explain deviations" rule,
though this isn't really a deviation — TECH_STACK.md names FAISS as a
sanctioned option, not a substitution.

FAISS only stores vectors, not payloads, so chunk metadata (file, name,
kind, line range, code) is stored alongside as a JSON list in the same
order as the vectors, and looked up by index position.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from repoagent.indexing.chunker import Chunk

DEFAULT_INDEX_DIR = Path("faiss_index")
_INDEX_FILE = "index.faiss"
_CHUNKS_FILE = "chunks.json"


def build_and_save(chunks: list[Chunk], embeddings: np.ndarray, index_dir: Path = DEFAULT_INDEX_DIR) -> None:
    if len(chunks) != embeddings.shape[0]:
        raise ValueError(f"chunk count ({len(chunks)}) != embedding count ({embeddings.shape[0]})")

    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product; embeddings are L2-normalized -> cosine similarity
    index.add(embeddings.astype("float32"))
    faiss.write_index(index, str(index_dir / _INDEX_FILE))

    (index_dir / _CHUNKS_FILE).write_text(
        json.dumps([asdict(c) for c in chunks], indent=2), encoding="utf-8"
    )


def load(index_dir: Path = DEFAULT_INDEX_DIR) -> tuple[faiss.Index, list[dict]]:
    index_dir = Path(index_dir)
    index_path = index_dir / _INDEX_FILE
    chunks_path = index_dir / _CHUNKS_FILE
    if not index_path.exists() or not chunks_path.exists():
        raise FileNotFoundError(
            f"No index found at {index_dir} — build it first, e.g. "
            f"`python scripts/build_index.py`."
        )
    index = faiss.read_index(str(index_path))
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    return index, chunks
