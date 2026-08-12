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

# Ceilings for a single scan. A docs folder is small; these are far above any
# real one. Without them, pointing the viewer at a home directory or a drive root
# walks the entire filesystem, reads every Markdown file it finds into the search
# index, and puts a recursive filesystem watch over all of it.
DEFAULT_MAX_DEPTH = 10
DEFAULT_MAX_DIRS = 5_000
DEFAULT_MAX_FILES = 2_000

_H1 = re.compile(r"^\s{0,3}#\s+(.+?)\s*#*\s*$")
_SETEXT = re.compile(r"^=+\s*$")


@dataclass
class DocNode:
    """A file or folder in the docs tree."""

    path: Path
    title: str
    is_dir: bool = False
    children: list[DocNode] = field(default_factory=list)


@dataclass
class ScanBudget:
    """Shared limits for one scan, so a mis-aimed root cannot run away.

    Pass the same instance through a whole traversal -- the counters are what stop
    it, not the per-call arguments.
    """

    max_depth: int = DEFAULT_MAX_DEPTH
    max_dirs: int = DEFAULT_MAX_DIRS
    max_files: int = DEFAULT_MAX_FILES
    dirs_seen: int = 0
    files_seen: int = 0
    truncated: bool = False

    def take_dir(self) -> bool:
        """Claim one directory visit. False once the ceiling is reached."""
        if self.dirs_seen >= self.max_dirs:
            self.truncated = True
            return False
        self.dirs_seen += 1
        return True

    def take_file(self) -> bool:
        """Claim one Markdown file. False once the ceiling is reached."""
        if self.files_seen >= self.max_files:
            self.truncated = True
            return False
        self.files_seen += 1
        return True

    def too_deep(self, depth: int) -> bool:
        if depth > self.max_depth:
            self.truncated = True
            return True
        return False


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


def build_tree(root: Path, budget: ScanBudget | None = None) -> list[DocNode]:
    """Build the docs tree under `root`.

    Folders containing no Markdown at any depth are pruned. Pass a `ScanBudget` to
    inspect afterwards whether the scan was cut short (`budget.truncated`).
    """
    return _build_tree(Path(root), budget if budget is not None else ScanBudget(), depth=0)


def _build_tree(root: Path, budget: ScanBudget, depth: int) -> list[DocNode]:
    if budget.too_deep(depth) or not budget.take_dir():
        return []

    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return []

    nodes: list[DocNode] = []
    for entry in entries:
        if entry.is_dir():
            if _should_skip_dir(entry.name):
                continue
            children = _build_tree(entry, budget, depth + 1)
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
            if not budget.take_file():
                break
            nodes.append(DocNode(path=entry, title=extract_title(entry)))

    nodes.sort(key=_sort_key)
    return nodes


def iter_markdown_files(root: Path, budget: ScanBudget | None = None):
    """Yield every Markdown file under `root`, honouring the skip list and budget."""
    budget = budget if budget is not None else ScanBudget()
    stack = [(Path(root), 0)]
    while stack:
        current, depth = stack.pop()
        if budget.too_deep(depth) or not budget.take_dir():
            continue
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if not _should_skip_dir(entry.name):
                    stack.append((entry, depth + 1))
            elif is_markdown(entry):
                if not budget.take_file():
                    return
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
