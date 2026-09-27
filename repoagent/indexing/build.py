"""Build the search index for a repo: walk -> chunk -> embed -> persist."""

from __future__ import annotations

from pathlib import Path

from repoagent.indexing import store
from repoagent.indexing.chunker import Chunk, chunk_file
from repoagent.indexing.embedder import embed

# Directories that never hold source worth indexing.
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "venv", ".venv", "node_modules"}


def iter_python_files(repo_root: Path) -> list[Path]:
    return sorted(
        p for p in repo_root.rglob("*.py")
        if not any(part in _SKIP_DIRS for part in p.relative_to(repo_root).parts)
    )


def chunk_repo(repo_root: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for abs_path in iter_python_files(repo_root):
        rel_path = str(abs_path.relative_to(repo_root).as_posix())
        chunks.extend(chunk_file(str(abs_path), rel_path))
    return chunks


def build_index(repo_root: str | Path, index_dir: str | Path = store.DEFAULT_INDEX_DIR) -> int:
    """Chunk every .py file under repo_root, embed the chunks, and persist
    a FAISS index + metadata to index_dir. Returns the number of chunks indexed."""
    repo_root = Path(repo_root)
    chunks = chunk_repo(repo_root)
    if not chunks:
        raise ValueError(f"No chunks found under {repo_root} — is that the right path?")

    texts = [f"{c.name} ({c.kind}) in {c.file}:\n{c.code}" for c in chunks]
    embeddings = embed(texts)

    store.build_and_save(chunks, embeddings, Path(index_dir))
    return len(chunks)
