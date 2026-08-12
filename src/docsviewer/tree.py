"""Scan a docs folder into a sorted tree of Markdown documents.

Qt-free by design -- `build_tree` returns plain dataclasses so it can be tested
headlessly; `app.py` does the QTreeWidget binding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

MARKDOWN_SUFFIXES = frozenset({".md", ".markdown", ".mdown", ".mkd"})

SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "site-packages",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }
)

# Files that should sort to the top of their folder, in this order.
INDEX_NAMES = ("readme", "index", "home")

_H1 = re.compile(r"^\s{0,3}#\s+(.+?)\s*#*\s*$")
_SETEXT = re.compile(r"^=+\s*$")


@dataclass
class DocNode:
    """A file or folder in the docs tree."""

    path: Path
    title: str
    is_dir: bool = False
    children: list[DocNode] = field(default_factory=list)


def is_markdown(path: Path) -> bool:
    return path.suffix.lower() in MARKDOWN_SUFFIXES


def _should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or (name.startswith(".") and name not in {".", ".."})


def extract_title(path: Path, max_lines: int = 60) -> str:
    """Return the document's first H1, falling back to a prettified filename.

    Skips a leading YAML front-matter block and understands both ATX (`# Foo`)
    and setext (`Foo\\n===`) headings.
    """
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = []
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                lines.append(line.rstrip("\n"))
    except OSError:
        return _pretty_name(path)

    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in {"---", "..."}:
                start = i + 1
                break

    in_fence = False
    for i in range(start, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _H1.match(line)
        if match:
            return match.group(1).strip()
        # Setext H1: a non-empty line underlined with '='.
        if stripped and i + 1 < len(lines) and _SETEXT.match(lines[i + 1].strip()):
            return stripped

    return _pretty_name(path)


def _pretty_name(path: Path) -> str:
    """`getting-started.md` -> `Getting Started`."""
    stem = path.stem
    if stem.lower() in INDEX_NAMES:
        return stem.upper() if stem.isupper() else stem.capitalize()
    return _prettify(stem)


def _pretty_dir_name(path: Path) -> str:
    """`api-reference/` -> `Api Reference`.

    Uses the whole directory name, not `Path.stem` -- a folder called `v1.2`
    would otherwise be truncated to `v1`.
    """
    return _prettify(path.name)


def _prettify(text: str) -> str:
    return re.sub(r"[-_]+", " ", text).strip().title() or text


def _sort_key(node: DocNode) -> tuple:
    """Index files first, then subfolders, then remaining files -- each alphabetical."""
    stem = node.path.stem.lower()
    if not node.is_dir and stem in INDEX_NAMES:
        return (0, INDEX_NAMES.index(stem), node.path.name.lower())
    if node.is_dir:
        return (1, 0, node.path.name.lower())
    return (2, 0, node.path.name.lower())


def build_tree(root: Path) -> list[DocNode]:
    """Build the docs tree under `root`.

    Folders containing no Markdown at any depth are pruned.
    """
    root = Path(root)
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return []

    nodes: list[DocNode] = []
    for entry in entries:
        if entry.is_dir():
            if _should_skip_dir(entry.name):
                continue
            children = build_tree(entry)
            if children:  # prune empty branches
                nodes.append(
                    DocNode(
                        path=entry,
                        title=_pretty_dir_name(entry),
                        is_dir=True,
                        children=children,
                    )
                )
        elif is_markdown(entry):
            nodes.append(DocNode(path=entry, title=extract_title(entry)))

    nodes.sort(key=_sort_key)
    return nodes


def iter_markdown_files(root: Path):
    """Yield every Markdown file under `root`, honouring the skip list."""
    root = Path(root)
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if not _should_skip_dir(entry.name):
                    stack.append(entry)
            elif is_markdown(entry):
                yield entry


def default_document(root: Path) -> Path | None:
    """Pick the document to show on open: the tree's first file, depth-first."""
    for node in build_tree(root):
        found = _first_file(node)
        if found is not None:
            return found
    return None


def _first_file(node: DocNode) -> Path | None:
    if not node.is_dir:
        return node.path
    for child in node.children:
        found = _first_file(child)
        if found is not None:
            return found
    return None
