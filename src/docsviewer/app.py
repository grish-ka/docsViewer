"""The Qt application: main window, sidebar, and web view.

Import order matters here -- QtWebEngineWidgets must be imported before a
QApplication is constructed, which is why `run()` lives in this module.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QKeySequence
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .renderer import render_document, render_error
from .runtime import apply_qt_attributes
from .search import Index
from .settings import Settings
from .tree import DocNode, build_tree, default_document, is_markdown
from .watcher import DocsWatcher

PATH_ROLE = Qt.ItemDataRole.UserRole
LINE_ROLE = Qt.ItemDataRole.UserRole + 1

SEARCH_DEBOUNCE_MS = 200
ZOOM_STEP = 0.1
ZOOM_RANGE = (0.5, 2.5)


class DocPage(QWebEnginePage):
    """A page that routes link clicks back into the viewer instead of navigating."""

    def __init__(self, window: MainWindow, parent=None) -> None:
        super().__init__(parent)
        self._window = window

    def acceptNavigationRequest(  # noqa: N802 (Qt override)
        self, url: QUrl, nav_type: QWebEnginePage.NavigationType, is_main_frame: bool
    ) -> bool:
        # Only clicks are intercepted; setHtml and in-page loads pass through.
        if nav_type != QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            return True

        if url.scheme() in ("http", "https", "mailto"):
            QDesktopServices.openUrl(url)
            return False

        if url.isLocalFile():
            path = Path(url.toLocalFile())
            anchor = url.fragment() or None
            if is_markdown(path):
                self._window.open_document(path, anchor=anchor)
            elif path.exists():
                QDesktopServices.openUrl(url)
            else:
                self._window.show_message(f"Link target not found: {path}")
            return False

        return False

    def createWindow(self, _type):  # noqa: N802 (Qt override)
        # Never spawn a second browser window; target="_blank" is handled above.
        return None


class MainWindow(QMainWindow):
    def __init__(self, root: Path, initial: Path | None = None) -> None:
        super().__init__()
        self.settings = Settings()
        self.root = Path(root)
        self.current: Path | None = None
        self.index = Index(root=self.root)

        self._history: list[Path] = []
        self._history_pos = -1
        self._pending_scroll = 0
        self._pending_anchor: str | None = None
        self._pending_find = ""
        self._suppress_tree_signal = False

        self._build_ui()
        self._build_actions()

        self.watcher = DocsWatcher(self)
        self.watcher.changed.connect(self._on_file_changed)

        self._restore_window_state()
        self._apply_theme(self.settings.theme)
        self.load_folder(self.root, initial=initial)

    # -- construction ---------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle("docsviewer")
        self.resize(1180, 780)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search docs…  (Ctrl+F)")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self._on_search_text)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setUniformRowHeights(True)
        self.tree.currentItemChanged.connect(self._on_tree_selection)

        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_result_activated)
        self.results.itemClicked.connect(self._on_result_activated)

        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.addWidget(self.tree)  # index 0
        self.sidebar_stack.addWidget(self.results)  # index 1

        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(6)
        layout.addWidget(self.search_box)
        layout.addWidget(self.sidebar_stack)

        self.view = QWebEngineView()
        self.view.setPage(DocPage(self, self.view))
        self.view.loadFinished.connect(self._on_load_finished)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(self.view)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([300, 880])
        self.splitter.setChildrenCollapsible(False)
        self.setCentralWidget(self.splitter)

        self.status_label = QLabel("")
        self.statusBar().addPermanentWidget(self.status_label)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._run_search)

    def _build_actions(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.act_open = QAction("Open Folder…", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.choose_folder)

        self.act_back = QAction("◀", self)
        self.act_back.setToolTip("Back (Alt+Left)")
        self.act_back.setShortcut(QKeySequence(Qt.Modifier.ALT | Qt.Key.Key_Left))
        self.act_back.triggered.connect(self.go_back)
        self.act_back.setEnabled(False)

        self.act_forward = QAction("▶", self)
        self.act_forward.setToolTip("Forward (Alt+Right)")
        self.act_forward.setShortcut(QKeySequence(Qt.Modifier.ALT | Qt.Key.Key_Right))
        self.act_forward.triggered.connect(self.go_forward)
        self.act_forward.setEnabled(False)

        self.act_theme = QAction("Dark Mode", self)
        self.act_theme.setShortcut(QKeySequence("Ctrl+D"))
        self.act_theme.triggered.connect(self.toggle_theme)

        self.act_reload = QAction("Reload", self)
        self.act_reload.setShortcut(QKeySequence.StandardKey.Refresh)
        self.act_reload.triggered.connect(lambda: self.reload_current(preserve_scroll=True))

        self.act_find = QAction("Find", self)
        self.act_find.setShortcut(QKeySequence.StandardKey.Find)
        self.act_find.triggered.connect(self._focus_search)

        self.act_zoom_in = QAction("Zoom In", self)
        self.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.act_zoom_in.triggered.connect(lambda: self._zoom(ZOOM_STEP))

        self.act_zoom_out = QAction("Zoom Out", self)
        self.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.act_zoom_out.triggered.connect(lambda: self._zoom(-ZOOM_STEP))

        self.act_zoom_reset = QAction("Reset Zoom", self)
        self.act_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        self.act_zoom_reset.triggered.connect(lambda: self.view.setZoomFactor(1.0))

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.act_quit.triggered.connect(self.close)

        self.act_about = QAction("About", self)
        self.act_about.triggered.connect(self._about)

        for action in (self.act_back, self.act_forward, self.act_open, self.act_theme):
            toolbar.addAction(action)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_reload)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.act_back)
        view_menu.addAction(self.act_forward)
        view_menu.addSeparator()
        view_menu.addAction(self.act_theme)
        view_menu.addSeparator()
        view_menu.addAction(self.act_find)
        view_menu.addSeparator()
        view_menu.addAction(self.act_zoom_in)
        view_menu.addAction(self.act_zoom_out)
        view_menu.addAction(self.act_zoom_reset)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.act_about)

    # -- folder / document loading --------------------------------------

    def load_folder(self, root: Path, initial: Path | None = None) -> None:
        """Point the viewer at a docs folder and show its first document."""
        self.root = Path(root).resolve()
        self.index = Index(root=self.root)
        self.index.refresh()
        self._history.clear()
        self._history_pos = -1
        self.current = None

        self.setWindowTitle(f"docsviewer — {self.root.name}")
        self._reload_tree()
        self.watcher.start(self.root)
        self.settings.last_folder = self.root

        target = initial if initial and initial.is_file() else default_document(self.root)
        if target is not None:
            self.open_document(target)
        else:
            self.view.setHtml(
                render_error(f"No Markdown files found in {self.root}", self.settings.theme)
            )
            self.status_label.setText(str(self.root))

    def open_document(
        self,
        path: Path,
        *,
        anchor: str | None = None,
        add_history: bool = True,
        preserve_scroll: bool = False,
        find_term: str = "",
    ) -> None:
        """Render `path` into the view."""
        path = Path(path).resolve()
        if not path.is_file():
            self.view.setHtml(render_error(f"File not found: {path}", self.settings.theme))
            return

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self.view.setHtml(render_error(f"Could not read {path}\n\n{exc}", self.settings.theme))
            return

        if add_history and (not self._history or self._history[self._history_pos] != path):
            del self._history[self._history_pos + 1 :]
            self._history.append(path)
            self._history_pos = len(self._history) - 1
            self._update_history_actions()

        self.current = path
        self._pending_anchor = anchor
        self._pending_find = find_term
        if not preserve_scroll:
            self._pending_scroll = 0

        html = render_document(text, self.settings.theme, title=path.name)
        # The base URL is what lets relative images and links resolve.
        self.view.setHtml(html, QUrl.fromLocalFile(str(path)))

        self._select_in_tree(path)
        self._show_status(path)

    def reload_current(self, *, preserve_scroll: bool = True) -> None:
        """Re-render the open document, optionally keeping the scroll position."""
        if self.current is None:
            return
        if not preserve_scroll:
            self.open_document(self.current, add_history=False)
            return
        self.view.page().runJavaScript("window.scrollY", self._reload_at_offset)

    def _reload_at_offset(self, offset) -> None:
        self._pending_scroll = int(offset or 0)
        if self.current is not None:
            self.open_document(self.current, add_history=False, preserve_scroll=True)

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            return
        if self._pending_anchor:
            anchor = self._pending_anchor.replace("\\", "\\\\").replace("'", "\\'")
            self.view.page().runJavaScript(
                f"var el=document.getElementById('{anchor}');"
                "if(el){el.scrollIntoView({behavior:'auto',block:'start'});}"
            )
            self._pending_anchor = None
        elif self._pending_scroll:
            self.view.page().runJavaScript(f"window.scrollTo(0, {self._pending_scroll});")
            self._pending_scroll = 0
        if self._pending_find:
            self.view.page().findText(self._pending_find)
            self._pending_find = ""

    # -- sidebar tree ---------------------------------------------------

    def _reload_tree(self) -> None:
        self._suppress_tree_signal = True
        self.tree.clear()
        nodes = build_tree(self.root)
        self._populate(self.tree.invisibleRootItem(), nodes)
        self.tree.expandAll()
        self._suppress_tree_signal = False
        if self.current is not None:
            self._select_in_tree(self.current)

    def _populate(self, parent: QTreeWidgetItem, nodes: list[DocNode]) -> None:
        for node in nodes:
            item = QTreeWidgetItem(parent, [node.title])
            item.setToolTip(0, str(node.path))
            if node.is_dir:
                item.setData(0, PATH_ROLE, None)
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                self._populate(item, node.children)
            else:
                item.setData(0, PATH_ROLE, str(node.path))

    def _select_in_tree(self, path: Path) -> None:
        target = str(path)
        iterator = _iter_items(self.tree.invisibleRootItem())
        for item in iterator:
            if item.data(0, PATH_ROLE) == target:
                self._suppress_tree_signal = True
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
                self._suppress_tree_signal = False
                return

    def _on_tree_selection(self, current: QTreeWidgetItem | None, _previous) -> None:
        if self._suppress_tree_signal or current is None:
            return
        stored = current.data(0, PATH_ROLE)
        if stored:
            self.open_document(Path(stored))

    # -- search ---------------------------------------------------------

    def _focus_search(self) -> None:
        self.search_box.setFocus()
        self.search_box.selectAll()

    def _on_search_text(self, text: str) -> None:
        if not text.strip():
            self._search_timer.stop()
            self.sidebar_stack.setCurrentIndex(0)
            self.results.clear()
            return
        self._search_timer.start()

    def _run_search(self) -> None:
        term = self.search_box.text().strip()
        if not term:
            return
        hits = self.index.query(term)
        self.results.clear()
        for hit in hits:
            try:
                relative = hit.path.relative_to(self.root)
            except ValueError:
                relative = hit.path
            item = QListWidgetItem(
                f"{hit.title}  ·  {hit.line_no}\n{hit.snippet(term_len=len(term))}"
            )
            item.setToolTip(f"{relative}:{hit.line_no}")
            item.setData(PATH_ROLE, str(hit.path))
            item.setData(LINE_ROLE, hit.line_no)
            self.results.addItem(item)

        if not hits:
            placeholder = QListWidgetItem(f"No matches for “{term}”")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.results.addItem(placeholder)

        self.sidebar_stack.setCurrentIndex(1)
        self.statusBar().showMessage(
            f"{len(hits)} match{'es' if len(hits) != 1 else ''} in {self.index.count()} files",
            4000,
        )

    def _on_result_activated(self, item: QListWidgetItem) -> None:
        stored = item.data(PATH_ROLE)
        if stored:
            self.open_document(Path(stored), find_term=self.search_box.text().strip())

    # -- history --------------------------------------------------------

    def go_back(self) -> None:
        if self._history_pos > 0:
            self._history_pos -= 1
            self._update_history_actions()
            self.open_document(self._history[self._history_pos], add_history=False)

    def go_forward(self) -> None:
        if self._history_pos < len(self._history) - 1:
            self._history_pos += 1
            self._update_history_actions()
            self.open_document(self._history[self._history_pos], add_history=False)

    def _update_history_actions(self) -> None:
        self.act_back.setEnabled(self._history_pos > 0)
        self.act_forward.setEnabled(self._history_pos < len(self._history) - 1)

    # -- theme ----------------------------------------------------------

    def toggle_theme(self) -> None:
        self.settings.theme = self.settings.toggled_theme()
        self._apply_theme(self.settings.theme)
        self.reload_current(preserve_scroll=True)

    def _apply_theme(self, theme: str) -> None:
        dark = theme == "dark"
        self.act_theme.setText("Light Mode" if dark else "Dark Mode")
        self.view.page().setBackgroundColor(QColor("#0d1117" if dark else "#ffffff"))
        self.setStyleSheet(_QSS_DARK if dark else _QSS_LIGHT)

    def _zoom(self, delta: float) -> None:
        low, high = ZOOM_RANGE
        self.view.setZoomFactor(max(low, min(high, self.view.zoomFactor() + delta)))

    # -- filesystem events ----------------------------------------------

    def _on_file_changed(self, changed: str) -> None:
        self.index.refresh()
        if not changed:
            self._reload_tree()
            return
        self._reload_tree()
        if self.current is not None and Path(changed) == self.current:
            self.reload_current(preserve_scroll=True)
            self.statusBar().showMessage("Reloaded", 1500)

    # -- misc -----------------------------------------------------------

    def choose_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Open docs folder", str(self.root))
        if chosen:
            self.load_folder(Path(chosen))

    def show_message(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)

    def _show_status(self, path: Path) -> None:
        try:
            self.status_label.setText(str(path.relative_to(self.root)))
        except ValueError:
            self.status_label.setText(str(path))

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About docsviewer",
            f"<b>docsviewer</b> {__version__}<br><br>"
            "A desktop reader for a project's <code>docs/</code> folder.<br>"
            "Run <code>docsviewer init</code> in a project to create one.",
        )

    def _restore_window_state(self) -> None:
        geometry = self.settings.geometry
        if geometry is not None:
            self.restoreGeometry(geometry)
        splitter_state = self.settings.splitter_state
        if splitter_state is not None:
            self.splitter.restoreState(splitter_state)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.settings.geometry = self.saveGeometry()
        self.settings.splitter_state = self.splitter.saveState()
        self.settings.sync()
        self.watcher.stop()
        super().closeEvent(event)


def _iter_items(parent: QTreeWidgetItem):
    """Depth-first walk of a QTreeWidget."""
    for i in range(parent.childCount()):
        child = parent.child(i)
        yield child
        yield from _iter_items(child)


_QSS_LIGHT = """
QMainWindow, QWidget { background: #ffffff; color: #1f2328; }
QToolBar { background: #f6f8fa; border-bottom: 1px solid #d1d9e0; spacing: 4px; padding: 3px; }
QMenuBar { background: #f6f8fa; }
QMenuBar::item:selected { background: #dde3ea; }
QLineEdit { padding: 5px 8px; border: 1px solid #d1d9e0; border-radius: 6px; background: #ffffff; }
QLineEdit:focus { border-color: #0969da; }
QTreeWidget, QListWidget { border: none; background: #ffffff; outline: none; }
QTreeWidget::item, QListWidget::item { padding: 3px 2px; border-radius: 4px; }
QTreeWidget::item:selected, QListWidget::item:selected { background: #ddf4ff; color: #0969da; }
QTreeWidget::item:hover, QListWidget::item:hover { background: #f0f3f6; }
QStatusBar { background: #f6f8fa; border-top: 1px solid #d1d9e0; color: #59636e; }
QSplitter::handle { background: #d1d9e0; width: 1px; }
"""

_QSS_DARK = """
QMainWindow, QWidget { background: #0d1117; color: #e6edf3; }
QToolBar { background: #161b22; border-bottom: 1px solid #2f3742; spacing: 4px; padding: 3px; }
QMenuBar { background: #161b22; }
QMenuBar::item:selected { background: #262c36; }
QMenu { background: #161b22; border: 1px solid #2f3742; }
QMenu::item:selected { background: #262c36; }
QLineEdit { padding: 5px 8px; border: 1px solid #2f3742; border-radius: 6px;
            background: #0d1117; color: #e6edf3; }
QLineEdit:focus { border-color: #4493f8; }
QTreeWidget, QListWidget { border: none; background: #0d1117; outline: none; }
QTreeWidget::item, QListWidget::item { padding: 3px 2px; border-radius: 4px; }
QTreeWidget::item:selected, QListWidget::item:selected { background: #1f2d3d; color: #4493f8; }
QTreeWidget::item:hover, QListWidget::item:hover { background: #161b22; }
QStatusBar { background: #161b22; border-top: 1px solid #2f3742; color: #9198a1; }
QSplitter::handle { background: #2f3742; width: 1px; }
QToolTip { background: #161b22; color: #e6edf3; border: 1px solid #2f3742; }
"""


def run(root: Path | None, initial: Path | None = None) -> int:
    """Start the GUI. Returns the process exit code.

    A `root` of None means nothing suitable was found on the command line, so we
    ask the user to pick a folder before building the window.
    """
    if QApplication.instance() is None:
        apply_qt_attributes()  # software OpenGL; must precede QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("docsviewer")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("docsviewer")

    if root is None:
        settings = Settings()
        start_at = settings.last_folder or Path.cwd()
        chosen = QFileDialog.getExistingDirectory(None, "Open docs folder", str(start_at))
        if not chosen:
            return 0
        root = Path(chosen)

    window = MainWindow(root, initial=initial)
    window.show()
    return app.exec()
