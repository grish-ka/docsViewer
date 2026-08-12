"""Command line entry point.

`init` is deliberately Qt-free -- PySide6 is only imported once we actually need
a window, so scaffolding works fine on a headless box.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .tree import is_markdown

DOCS_DIRNAME = "docs"

_EPILOG = """\
examples:
  docsviewer                 read ./docs (or the current folder) in the GUI
  docsviewer path/to/docs    read a specific folder
  docsviewer notes/api.md    open a single file
  docsviewer . --here        read the current folder, ignoring its docs/
  docsviewer init            create ./docs with starter pages
  docsviewer init . --title "My Project"
"""


def _has_markdown(folder: Path) -> bool:
    """True if `folder` contains Markdown at any depth (cheap early exit)."""
    from .tree import iter_markdown_files

    for _ in iter_markdown_files(folder):
        return True
    return False


def _docs_subfolder(path: Path) -> Path | None:
    """Return `<path>/docs` when it exists and holds Markdown."""
    nested = path / DOCS_DIRNAME
    return nested if nested.is_dir() and _has_markdown(nested) else None


def resolve_target(raw: str | None, *, here: bool = False) -> tuple[Path | None, Path | None]:
    """Work out which folder to open and which file to show first.

    A project directory resolves to its `docs/` subfolder when it has one. That
    preference is deliberate: nearly every project has a `README.md` at its root,
    so keying off "does this folder contain Markdown" would mean `docs/` almost
    never won. Pass `here=True` to browse the folder itself instead.

    Returns `(root, initial_file)`; `root` is None when nothing suitable was
    found and the GUI should ask the user to pick a folder.
    """
    if raw:
        path = Path(raw).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"No such file or directory: {path}")
        path = path.resolve()
        if path.is_file():
            if not is_markdown(path):
                raise ValueError(f"Not a Markdown file: {path}")
            return path.parent, path
        if not here:
            nested = _docs_subfolder(path)
            if nested is not None:
                return nested, None
        return path, None

    cwd = Path.cwd().resolve()
    if not here:
        nested = _docs_subfolder(cwd)
        if nested is not None:
            return nested, None
    if _has_markdown(cwd):
        return cwd, None
    return None, None


def _cmd_view(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="docsviewer",
        description="Read a project's Markdown docs in a desktop window.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="docs folder or Markdown file to open "
        f"(default: ./{DOCS_DIRNAME}, else the current folder)",
    )
    parser.add_argument(
        "--here",
        action="store_true",
        help=f"browse the folder itself instead of descending into its {DOCS_DIRNAME}/",
    )
    parser.add_argument("--version", action="version", version=f"docsviewer {__version__}")
    # 'init' never reaches this parser -- main() routes it first; it is documented
    # in the epilog instead.
    args = parser.parse_args(argv)

    try:
        root, initial = resolve_target(args.path, here=args.here)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
        return 2  # unreachable; parser.error exits

    if root is None:
        print(
            f"No Markdown found in {Path.cwd()} or ./{DOCS_DIRNAME}.\n"
            "Opening a folder picker — or run 'docsviewer init' to create a docs folder.",
            file=sys.stderr,
        )

    from .runtime import configure_rendering, hide_own_console

    # Must happen before the Qt import below: QtWebEngine reads its Chromium flags
    # from the environment as it loads.
    configure_rendering()
    hide_own_console()

    from .app import run  # imported late: pulls in Qt

    return run(root, initial=initial)


def _cmd_init(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="docsviewer init",
        description=f"Create a {DOCS_DIRNAME}/ folder with starter documentation.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="project directory (default: current directory)"
    )
    parser.add_argument("--title", help="project name used in the templates (default: folder name)")
    parser.add_argument(
        "--force", action="store_true", help="overwrite files that already exist"
    )
    args = parser.parse_args(argv)

    target = Path(args.path).expanduser()
    if not target.exists():
        parser.error(f"No such directory: {target}")
    if not target.is_dir():
        parser.error(f"Not a directory: {target}")

    from .scaffold import format_result, init_docs

    result = init_docs(target, title=args.title, force=args.force)
    summary = format_result(result)
    if summary:
        print(summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "init":
        return _cmd_init(argv[1:])
    return _cmd_view(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
