"""End-to-end GUI check: builds the real window and drives it.

`pytest` covers the Qt-free core. This covers the part it cannot: the window, the
web view, and -- importantly -- navigation driven by *real clicks* in the page
rather than by calling the handlers directly. A handler called directly runs
outside Qt's navigation machinery, so it will happily pass while a genuine click
crashes the renderer.

Usage:
    python scripts/gui_smoke.py [DOCS_DIR] [--show]

Defaults to ./docs. Runs offscreen unless --show is passed. Any file it edits
while testing live reload is restored before exit. Exit code 0 means everything
passed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SHOW = "--show" in sys.argv

DOCS = Path(ARGS[0] if ARGS else "docs").resolve()
if not DOCS.is_dir():
    sys.exit(f"Not a directory: {DOCS}")

if not SHOW:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from docsviewer.runtime import configure_rendering  # noqa: E402

configure_rendering()

from PySide6.QtCore import QTimer, QUrl  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from docsviewer.app import PATH_ROLE, MainWindow  # noqa: E402
from docsviewer.search import Index  # noqa: E402
from docsviewer.tree import build_tree  # noqa: E402

failures: list[str] = []
restore: dict[Path, str] = {}


def check(label: str, ok: bool, detail: str = "") -> None:
    if not ok:
        failures.append(f"{label} {detail}".strip())
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if not ok else ""), flush=True)


EXPECTED = build_tree(DOCS)
INDEX = Index.build(DOCS)
if not INDEX.documents:
    sys.exit(f"No Markdown found in {DOCS}")

app = QApplication([])
win = MainWindow(DOCS)
win.show()


# -- sidebar and rendering ---------------------------------------------


def step_tree() -> None:
    count = win.tree.topLevelItemCount()
    check("sidebar matches the folder", count == len(EXPECTED), f"{count} vs {len(EXPECTED)}")
    first = win.tree.topLevelItem(0).data(0, PATH_ROLE)
    check(
        "README sorts first",
        first is not None and Path(first).name.lower().startswith("readme"),
        str(first),
    )
    check("index covers every file", win.index.count() == INDEX.count())
    check("opened a document", win.current is not None and win.current.is_file())
    win.view.page().toHtml(step_html)


def step_html(html: str) -> None:
    check("body rendered", "markdown-body" in html)
    check("heading rendered", "<h1" in html)
    check("theme css inlined", "--dv-bg" in html)
    check("code highlighted", "<pre" in html)
    step_click_internal()


# -- real clicks --------------------------------------------------------

CLICK_JS = """
(function () {
  var links = document.querySelectorAll('a[href]');
  for (var i = 0; i < links.length; i++) {
    var href = links[i].getAttribute('href');
    if (%s) { links[i].click(); return href; }
  }
  return '';
})();
"""

PLAIN_LINK = "href.indexOf('.md') !== -1 && href.indexOf('#') === -1 && href.indexOf('://') === -1"
ANCHOR_LINK = "href.indexOf('.md#') !== -1 && href.indexOf('://') === -1"


def step_click_internal() -> None:
    """The regression that matters: a genuine click used to crash the renderer."""
    win.view.page().runJavaScript(CLICK_JS % PLAIN_LINK, lambda href: _after_click(href, next_step))


def _after_click(href, then) -> None:
    if not href:
        check("found an internal link to click", False)
        return then()
    print(f"       clicked {href}", flush=True)
    QTimer.singleShot(1200, then)


def next_step() -> None:
    check(
        "clicking a link navigates (no crash)",
        win.current is not None and win.current.is_file(),
        str(win.current),
    )
    check("history recorded the click", win.act_back.isEnabled())
    step_click_anchor()


def step_click_anchor() -> None:
    def handle(href):
        if href:
            _after_click(href, after_anchor)
        else:
            after_anchor()  # not every docs tree has a cross-file anchor link

    win.view.page().runJavaScript(CLICK_JS % ANCHOR_LINK, handle)


def after_anchor() -> None:
    check("anchor link survived", win.current is not None and win.current.is_file())
    step_external()


def step_external() -> None:
    # Called directly on purpose: a real click would launch a browser window.
    page = win.view.page()
    accepted = page.acceptNavigationRequest(
        QUrl("https://example.com"), page.NavigationType.NavigationTypeLinkClicked, True
    )
    check("external link is not navigated in-app", accepted is False)
    step_search()


# -- search, theme, reload ---------------------------------------------


def step_search() -> None:
    candidates = ("Trusted Publishing", "scroll position", "sidebar")
    term = next((t for t in candidates if len(INDEX.query(t)) == 1), None)
    if term is None:
        check("found a unique search term", False)
        return step_theme()

    win.search_box.setText(term)
    win._run_search()
    check("search returns one result", win.results.count() == 1)
    item = win.results.item(0)
    check("result carries its path", item.data(PATH_ROLE) is not None)
    win._on_result_activated(item)
    check("clicking a result opens that file", win.current == INDEX.query(term)[0].path)

    win.search_box.setText("zzzznotpresent")
    win._run_search()
    check("no-match placeholder is inert", win.results.item(0).data(PATH_ROLE) is None)
    step_theme()


def step_theme() -> None:
    before = win.settings.theme
    win.toggle_theme()
    check("theme toggles", win.settings.theme != before)
    win.toggle_theme()
    check("theme restores", win.settings.theme == before)
    step_reload()


def step_reload() -> None:
    target = sorted(INDEX.documents)[0]
    win.open_document(target)
    restore[target] = target.read_text(encoding="utf-8")
    target.write_text(restore[target] + "\n\n## Live Reload Marker\n", encoding="utf-8")
    QTimer.singleShot(2500, lambda: win.view.page().toHtml(check_marker))


def check_marker(html: str) -> None:
    check("live reload picked up an edit", "Live Reload Marker" in html)
    finish()


def finish() -> None:
    for path, text in restore.items():
        path.write_text(text, encoding="utf-8")
    if restore:
        print(f"\nrestored {len(restore)} edited file(s)", flush=True)

    if failures:
        print(f"\n{len(failures)} FAILED:")
        for item in failures:
            print("  -", item)
    else:
        print("\nall GUI checks passed")
    win.watcher.stop()
    app.exit(1 if failures else 0)


def on_first_load(_ok) -> None:
    win.view.loadFinished.disconnect(on_first_load)
    QTimer.singleShot(200, step_tree)


win.view.loadFinished.connect(on_first_load)
QTimer.singleShot(45000, lambda: (print("TIMEOUT"), finish()))
sys.exit(app.exec())
