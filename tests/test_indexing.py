"""Phase 1 tests: chunking, indexing, search_code, read_file.

Per BUILD_PHASES.md, these are "plain unit tests against the index — no
LLM involved yet." search_code/build_index do call a local
sentence-transformers model, which is a one-time download on first run,
not an LLM call.
"""

from pathlib import Path

import pytest

from repoagent.indexing import search_code, read_file
from repoagent.indexing.build import build_index, chunk_repo
from repoagent.indexing.chunker import chunk_source

REPO_ROOT = Path(__file__).resolve().parent.parent / "target_repo" / "src"


@pytest.fixture(scope="session")
def index_dir(tmp_path_factory):
    """Build a real index over the target repo once per test session."""
    if not REPO_ROOT.exists():
        pytest.skip(f"target repo not found at {REPO_ROOT} — see README.md setup step 1")
    out_dir = tmp_path_factory.mktemp("faiss_index")
    build_index(REPO_ROOT, out_dir)
    return out_dir


# --- chunker: pure, no index needed ---------------------------------------

def test_chunks_top_level_functions_with_names_and_decorators():
    source = '''
from fastapi import APIRouter

router = APIRouter()

@router.get("/{id}/")
async def read_note(id: int):
    return id
'''
    chunks = chunk_source(source, "app/api/notes.py")
    funcs = [c for c in chunks if c.kind == "function"]
    assert len(funcs) == 1
    assert funcs[0].name == "read_note"
    assert "@router.get" in funcs[0].code  # decorator included in the chunk


def test_chunks_classes_whole():
    source = '''
from pydantic import BaseModel

class NoteSchema(BaseModel):
    title: str
    description: str
'''
    chunks = chunk_source(source, "app/api/models.py")
    classes = [c for c in chunks if c.kind == "class"]
    assert len(classes) == 1
    assert classes[0].name == "NoteSchema"
    assert "description: str" in classes[0].code


def test_module_level_code_with_no_functions_still_chunked():
    # app/db.py-shaped: no functions/classes, just top-level statements.
    source = '''
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = "pretend engine"
'''
    chunks = chunk_source(source, "app/db.py")
    assert len(chunks) == 1
    assert chunks[0].kind == "module"
    assert "DATABASE_URL" in chunks[0].code


def test_import_only_file_produces_no_leftover_chunk():
    chunks = chunk_source("from app.api import crud\n", "app/api/__init__.py")
    assert chunks == []


def test_chunk_repo_covers_all_target_files():
    if not REPO_ROOT.exists():
        pytest.skip(f"target repo not found at {REPO_ROOT}")
    chunks = chunk_repo(REPO_ROOT)
    files_seen = {c.file for c in chunks}
    # Every meaningful source file in the target repo should contribute at
    # least one chunk, including db.py which has no functions/classes.
    for expected in ("app/db.py", "app/main.py", "app/api/notes.py", "app/api/crud.py", "app/api/models.py"):
        assert expected in files_seen, f"{expected} missing from indexed chunks"


# --- search_code / read_file: the actual Phase 1 "done when" -------------

def test_search_code_finds_note_creation_code(index_dir):
    # NOTE: BUILD_PHASES.md's own example query is search_code("authentication"),
    # but the target repo (testdrivenio/fastapi-crud-async) has no auth code
    # at all — that's the point of picking it (see BUILD_SUMMARY.md). A query
    # for "authentication" would have nothing relevant to return, so we
    # verify against a query that matches what this repo actually contains.
    results = search_code("create a new note in the database", top_k=5, index_dir=index_dir)
    assert results, "expected at least one result"
    assert all({"file", "snippet", "score"} <= r.keys() for r in results)
    top_files = {r["file"] for r in results[:3]}
    assert "app/api/crud.py" in top_files or "app/api/notes.py" in top_files


def test_search_code_finds_database_setup(index_dir):
    # Phrased close to db.py's actual content (SQLAlchemy Table/Column
    # definitions + engine setup) rather than abstract terms like "schema"
    # that never appear verbatim — all-MiniLM-L6-v2 is a general-purpose
    # model over a 30-chunk corpus, not a code-search specialist, so
    # matching its vocabulary matters more than it would with a bigger
    # corpus or a code-tuned embedding model.
    results = search_code("notes table columns and the database engine setup", top_k=5, index_dir=index_dir)
    files = {r["file"] for r in results}
    assert "app/db.py" in files


def test_search_code_results_are_ranked_best_first(index_dir):
    results = search_code("delete a note by id", top_k=5, index_dir=index_dir)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_read_file_returns_numbered_lines():
    if not REPO_ROOT.exists():
        pytest.skip(f"target repo not found at {REPO_ROOT}")
    content = read_file("app/api/ping.py", repo_root=REPO_ROOT)
    lines = content.splitlines()
    # Line numbers are right-aligned to the file's width (e.g. " 1:" when
    # the file has >= 10 lines), so strip before checking the prefix.
    assert lines[0].lstrip().startswith("1:")
    assert any("async def pong" in line for line in lines)


def test_read_file_missing_raises():
    if not REPO_ROOT.exists():
        pytest.skip(f"target repo not found at {REPO_ROOT}")
    with pytest.raises(FileNotFoundError):
        read_file("app/does_not_exist.py", repo_root=REPO_ROOT)
