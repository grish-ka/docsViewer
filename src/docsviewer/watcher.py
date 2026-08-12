"""Live reload: watchdog filesystem events bridged onto the Qt event loop.

watchdog runs its observer on a background thread, and Qt widgets must never be
touched from there. This module's only job is to turn those events into a Qt
signal -- Qt queues cross-thread signal delivery onto the GUI thread for us.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .tree import MARKDOWN_SUFFIXES

DEBOUNCE_MS = 250


class _Handler(FileSystemEventHandler):
    """Forwards Markdown-file events to a callback. Runs on the watchdog thread."""

    def __init__(self, emit) -> None:
        super().__init__()
        self._emit = emit

    def _relevant(self, event: FileSystemEvent) -> str | None:
        if event.is_directory:
            return ""  # directory change -> tree may need rebuilding
        for attribute in ("dest_path", "src_path"):
            raw = getattr(event, attribute, "")
            if raw:
                path = Path(_decode(raw))
                if path.suffix.lower() in MARKDOWN_SUFFIXES:
                    return str(path)
        return None

    def on_any_event(self, event: FileSystemEvent) -> None:
        changed = self._relevant(event)
        if changed is not None:
            self._emit(changed)


def _decode(value) -> str:
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)


class DocsWatcher(QObject):
    """Watches a docs folder and emits `changed(path)` on the GUI thread.

    `path` is the changed Markdown file, or "" when the folder structure itself
    changed. Events are debounced -- editors typically fire several per save.
    """

    changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._observer: Observer | None = None
        self._root: Path | None = None
        self._pending: set[str] = set()

        # Lives on the GUI thread because DocsWatcher does; the watchdog thread
        # only ever calls start() on it via a queued signal.
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DEBOUNCE_MS)
        self._timer.timeout.connect(self._flush)

        self._raw = _RawBridge()
        self._raw.event.connect(self._on_raw)

    def start(self, root: Path) -> None:
        """Begin watching `root` recursively, replacing any previous watch."""
        self.stop()
        root = Path(root)
        if not root.is_dir():
            return
        self._root = root
        observer = Observer()
        observer.schedule(_Handler(self._raw.event.emit), str(root), recursive=True)
        observer.daemon = True
        observer.start()
        self._observer = observer

    def stop(self) -> None:
        """Stop the observer thread. Safe to call repeatedly."""
        self._timer.stop()
        self._pending.clear()
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=2.0)
            except RuntimeError:
                pass
            self._observer = None
        self._root = None

    def _on_raw(self, path: str) -> None:
        """Runs on the GUI thread (queued from the watchdog thread)."""
        self._pending.add(path)
        self._timer.start()

    def _flush(self) -> None:
        pending, self._pending = self._pending, set()
        # A structural change ("") supersedes individual file edits.
        if "" in pending:
            self.changed.emit("")
            pending.discard("")
        for path in sorted(pending):
            self.changed.emit(path)


class _RawBridge(QObject):
    """Signal carrier used to hop from the watchdog thread to the GUI thread."""

    event = Signal(str)
