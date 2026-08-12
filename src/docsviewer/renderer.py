"""Markdown -> HTML rendering.

Deliberately free of any Qt import so it can be unit-tested headlessly.
"""

from __future__ import annotations

import html
import importlib.resources as resources
from functools import cache

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight as _pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

THEMES = ("light", "dark")

# nowrap=True: markdown-it adds the surrounding <pre><code> itself.
_FORMATTER = HtmlFormatter(nowrap=True)


def _highlight(code: str, lang: str, _attrs: str) -> str:
    """Pygments highlighter for fenced code blocks.

    Returns escaped plain text when the language is unknown or missing, so an
    unrecognised fence degrades gracefully instead of raising.
    """
    if lang:
        try:
            lexer = get_lexer_by_name(lang, stripall=False)
        except ClassNotFound:
            lexer = None
        if lexer is not None:
            return _pygments_highlight(code, lexer, _FORMATTER)
    return html.escape(code, quote=False)


def _build_parser() -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"highlight": _highlight, "linkify": True, "html": True})
    md = (
        md.use(front_matter_plugin)
        .use(footnote_plugin)
        .use(deflist_plugin)
        .use(tasklists_plugin, enabled=True)
        # Heading ids power in-page "#anchor" links and the sidebar outline.
        .use(anchors_plugin, max_level=4, permalink=False)
    )
    md.enable("table")
    md.enable("strikethrough")
    return md


_MD = _build_parser()


@cache
def _asset(name: str) -> str:
    """Read a bundled CSS asset. Cached -- these never change at runtime."""
    return (resources.files("docsviewer") / "assets" / name).read_text(encoding="utf-8")


def render_body(text: str) -> str:
    """Render Markdown to an HTML fragment (no <html>/<style> wrapper)."""
    return _MD.render(text)


def stylesheet(theme: str = "light") -> str:
    """Concatenated CSS for a theme: layout + colour tokens + Pygments."""
    if theme not in THEMES:
        theme = "light"
    return "\n".join(
        (
            _asset("base.css"),
            _asset(f"{theme}.css"),
            _asset(f"pygments-{theme}.css"),
        )
    )


def render_document(text: str, theme: str = "light", title: str = "") -> str:
    """Render Markdown to a complete standalone HTML document.

    All CSS is inlined so the page needs no external requests -- the base URL is
    reserved for resolving the document's own relative images and links.
    """
    return (
        "<!doctype html>\n"
        '<html><head><meta charset="utf-8">'
        f"<title>{html.escape(title or 'docsviewer')}</title>"
        f"<style>{stylesheet(theme)}</style>"
        "</head><body>"
        f'<article class="markdown-body">{render_body(text)}</article>'
        "</body></html>"
    )


def render_error(message: str, theme: str = "light") -> str:
    """A styled page used for unreadable/missing files."""
    return (
        "<!doctype html>\n"
        '<html><head><meta charset="utf-8">'
        f"<style>{stylesheet(theme)}</style></head><body>"
        f'<article class="markdown-body"><div class="dv-error">{html.escape(message)}</div>'
        "</article></body></html>"
    )
