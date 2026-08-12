"""The `docsviewer init` command: create a docs/ folder in a project.

Writes a skeleton for the target project to fill in -- headings and structure,
with real boilerplate only where it is genuinely reusable (the changelog). It
deliberately does NOT copy docsviewer's own `docs/`: those pages describe the
viewer, and a new project inheriting them starts out documenting the wrong thing.

Runs headless: no Qt import here, so it works over SSH and in scripts.
"""

from __future__ import annotations

import importlib.resources as resources
from dataclasses import dataclass
from datetime import date
from pathlib import Path

TEMPLATE_PACKAGE_DIR = "templates"

MARKDOWN_SUFFIXES = frozenset({".md", ".markdown", ".mdown", ".mkd"})


class TemplateSourceMissing(RuntimeError):
    """Raised when the bundled docs folder cannot be located."""


@dataclass
class ScaffoldResult:
    created: list[Path]
    skipped: list[Path]
    docs_dir: Path


def template_root() -> Path:
    """Locate the template folder that `init` copies.

    It lives inside the package, so the same path resolves whether docsviewer was
    installed from a wheel or from a source checkout.
    """
    packaged = resources.files("docsviewer") / TEMPLATE_PACKAGE_DIR
    try:
        if packaged.is_dir():
            return Path(str(packaged))
    except (OSError, TypeError):  # pragma: no cover - exotic loaders
        pass

    raise TemplateSourceMissing(
        "Could not find the bundled templates folder. This usually means the package "
        "was built without its data files; reinstall docsviewer."
    )


def iter_template_files(root: Path | None = None) -> list[Path]:
    """Every Markdown file in the template source, sorted for stable output.

    Paths are returned relative to the template root.
    """
    root = root or template_root()
    files = [
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in MARKDOWN_SUFFIXES
    ]
    # Shallowest first, then alphabetical -- README lands at the top of the output.
    return sorted(files, key=lambda p: (len(p.parts), str(p).lower()))


def _render(source: Path, project_name: str) -> str:
    text = source.read_text(encoding="utf-8")
    return text.replace("{{project_name}}", project_name).replace(
        "{{date}}", date.today().isoformat()
    )


def init_docs(
    target: Path | str = ".",
    *,
    title: str | None = None,
    force: bool = False,
    docs_dirname: str = "docs",
) -> ScaffoldResult:
    """Create `<target>/docs/` from the bundled docs folder.

    Existing files are left alone unless `force` is set -- `init` is safe to
    re-run in a project that already has docs.
    """
    target = Path(target).expanduser().resolve()
    docs_dir = target / docs_dirname
    project_name = title or target.name or "Project"

    source_root = template_root()
    created: list[Path] = []
    skipped: list[Path] = []

    for relative in iter_template_files(source_root):
        destination = docs_dir / relative
        if destination.exists() and not force:
            skipped.append(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(_render(source_root / relative, project_name), encoding="utf-8")
        created.append(destination)

    if not created and not skipped:
        docs_dir.mkdir(parents=True, exist_ok=True)

    return ScaffoldResult(created=created, skipped=skipped, docs_dir=docs_dir)


def format_result(result: ScaffoldResult) -> str:
    """Human-readable summary for the CLI."""
    root = result.docs_dir.parent
    lines = []
    for path in result.created:
        lines.append(f"  created  {_relative(path, root)}")
    for path in result.skipped:
        lines.append(f"  skipped  {_relative(path, root)}  (exists)")

    if result.created:
        lines.append("")
        lines.append(f"Docs folder ready at {result.docs_dir}")
        lines.append("Run 'docsviewer' from this directory to read them.")
    elif result.skipped:
        lines.append("")
        lines.append("Nothing written. Pass --force to overwrite the existing files.")
    return "\n".join(lines)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
