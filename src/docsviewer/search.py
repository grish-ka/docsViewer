"""In-memory full-text search over a docs folder.

Qt-free by design. The index is rebuilt whenever the folder changes; docs trees
are small enough that a linear scan beats maintaining an inverted index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .tree import extract_title, iter_markdown_files

DEFAULT_LIMIT = 200
SNIPPET_RADIUS = 60


@dataclass
class Hit:
    """One matching line within a document."""

    path: Path
    title: str
    line_no: int  # 1-based
    line: str
    col: int  # 0-based offset of the match within `line`

    def snippet(self, radius: int = SNIPPET_RADIUS, term_len: int = 0) -> str:
        """The matching line trimmed to a window around the match."""
        text = self.line.strip()
        if len(text) <= radius * 2:
            return text
        offset = self.col - (len(self.line) - len(self.line.lstrip()))
        start = max(0, offset - radius)
        end = min(len(text), offset + term_len + radius)
        return ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")


@dataclass
class Index:
    """Maps each Markdown file under a root to its title and lines."""

    root: Path
    documents: dict[Path, tuple[str, list[str]]] = field(default_factory=dict)

    @classmethod
    def build(cls, root: Path) -> Index:
        index = cls(root=Path(root))
        index.refresh()
        return index

    def refresh(self) -> None:
        """Re-read every document from disk."""
        documents: dict[Path, tuple[str, list[str]]] = {}
        for path in iter_markdown_files(self.root):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            documents[path] = (extract_title(path), text.splitlines())
        self.documents = documents

    def query(self, term: str, limit: int = DEFAULT_LIMIT) -> list[Hit]:
        """Case-insensitive substring search.

        Results are capped at `limit` so a one-character query cannot lock the UI.
        """
        term = term.strip()
        if not term:
            return []
        needle = term.lower()

        hits: list[Hit] = []
        for path in sorted(self.documents, key=lambda p: str(p).lower()):
            title, lines = self.documents[path]
            for line_no, line in enumerate(lines, start=1):
                col = line.lower().find(needle)
                if col == -1:
                    continue
                hits.append(Hit(path=path, title=title, line_no=line_no, line=line, col=col))
                if len(hits) >= limit:
                    return hits
        return hits

    def count(self) -> int:
        return len(self.documents)
