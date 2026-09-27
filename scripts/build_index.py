#!/usr/bin/env python
"""Build the FAISS search index for the target repo.

Usage:
    python scripts/build_index.py [repo_root] [index_dir]

Defaults to target_repo/src -> faiss_index/, matching .env.example.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repoagent.indexing.build import build_index  # noqa: E402

if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "target_repo/src"
    index_dir = sys.argv[2] if len(sys.argv) > 2 else "faiss_index"
    n = build_index(repo_root, index_dir)
    print(f"Indexed {n} chunks from {repo_root} -> {index_dir}")
