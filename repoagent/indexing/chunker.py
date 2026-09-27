"""tree-sitter based chunking: split a Python file into function/class chunks.

Per ARCHITECTURE.md: "Indexes the repo (tree-sitter AST chunks -> embeddings
-> pgvector/FAISS)" — chunk by function/class, not raw lines, so retrieval
returns whole, coherent units of code rather than arbitrary line windows.

Chunking rule, in order:
1. Each top-level function (including `async def`, and decorated functions
   like `@router.post(...)`) becomes one chunk, decorators included.
2. Each top-level class becomes one chunk (whole class body, including its
   methods) — small demo repos like our target rarely have classes large
   enough to need per-method sub-chunking, so we don't add it.
3. Whatever top-level code is left (imports, module-level assignments,
   engine/table setup, `app.include_router(...)` calls, ...) is bundled
   into one synthetic "module top-level" chunk per file. Without this,
   files like `app/db.py` — which is *all* top-level statements, no
   functions or classes — would be invisible to search_code entirely.
"""

from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Language, Node, Parser
import tree_sitter_python as tspython

_PY_LANGUAGE = Language(tspython.language())


@dataclass
class Chunk:
    file: str  # path relative to the repo root
    name: str  # function/class name, or "<module top-level>"
    kind: str  # "function" | "class" | "module"
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    code: str


def _get_parser() -> Parser:
    # tree-sitter Parser objects aren't documented as thread-safe; building
    # the index is single-threaded and small, so a fresh parser per call
    # is simplest and cheap enough.
    return Parser(_PY_LANGUAGE)


def _inner_definition(node: Node) -> Node:
    """Unwrap a decorated_definition to the function/class node it wraps."""
    if node.type != "decorated_definition":
        return node
    for child in node.named_children:
        if child.type in ("function_definition", "class_definition"):
            return child
    return node  # pragma: no cover — grammar guarantees a def is present


def _name_of(def_node: Node, source: bytes) -> str:
    name_node = def_node.child_by_field_name("name")
    if name_node is None:
        return "<anonymous>"  # pragma: no cover — defensive
    return source[name_node.start_byte:name_node.end_byte].decode("utf-8")


def chunk_source(source: str, file_path: str) -> list[Chunk]:
    """Chunk one Python file's source into function/class/module chunks."""
    source_bytes = source.encode("utf-8")
    tree = _get_parser().parse(source_bytes)

    chunks: list[Chunk] = []
    leftover_nodes: list[Node] = []

    for top_level in tree.root_node.named_children:
        target = _inner_definition(top_level)

        if target.type in ("function_definition", "class_definition"):
            kind = "function" if target.type == "function_definition" else "class"
            chunks.append(
                Chunk(
                    file=file_path,
                    name=_name_of(target, source_bytes),
                    kind=kind,
                    start_line=top_level.start_point[0] + 1,
                    end_line=top_level.end_point[0] + 1,
                    code=source_bytes[top_level.start_byte:top_level.end_byte].decode("utf-8"),
                )
            )
        else:
            leftover_nodes.append(top_level)

    if leftover_nodes:
        leftover_code = "\n\n".join(
            source_bytes[n.start_byte:n.end_byte].decode("utf-8") for n in leftover_nodes
        )
        # Skip a leftover chunk that's just imports with nothing else —
        # low retrieval value, mostly noise.
        meaningful = [n for n in leftover_nodes if n.type not in ("import_statement", "import_from_statement")]
        if meaningful:
            chunks.append(
                Chunk(
                    file=file_path,
                    name="<module top-level>",
                    kind="module",
                    start_line=leftover_nodes[0].start_point[0] + 1,
                    end_line=leftover_nodes[-1].end_point[0] + 1,
                    code=leftover_code,
                )
            )

    return chunks


def chunk_file(abs_path: str, file_path: str) -> list[Chunk]:
    """Read a file from disk and chunk it. `file_path` is the path recorded
    on each chunk (relative to the repo root, for stable/portable results)."""
    with open(abs_path, "r", encoding="utf-8") as f:
        source = f.read()
    return chunk_source(source, file_path)
