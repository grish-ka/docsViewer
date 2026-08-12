# Development

## Setup

```console
git clone https://github.com/grish-ka/docsViewer
cd docsViewer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

## Layout

```
docsViewer/
├── docs/                     these pages (docsviewer's own manual)
├── scripts/gui_smoke.py      end-to-end GUI check
├── src/docsviewer/
│   ├── templates/            the skeleton `init` copies into new projects
│   ├── cli.py                argument parsing, path resolution
│   ├── app.py                main window, sidebar, web view
│   ├── renderer.py           Markdown -> styled HTML
│   ├── tree.py               folder scan, sorting, title extraction
│   ├── search.py             in-memory full-text index
│   ├── scaffold.py           the `init` command
│   ├── watcher.py            filesystem events -> Qt signals
│   ├── settings.py           persisted theme and window state
│   └── assets/               CSS
└── tests/
```

`renderer`, `tree`, `search`, and `scaffold` import **no Qt**. That's deliberate: the
logic worth testing runs headlessly, and the Qt layer stays a thin binding over it. Keep
it that way when adding features.

## Tests

Two layers, and you want both before trusting a change.

### Unit tests — the core

```console
pytest
ruff check .
```

Fast, needs no display, covers `renderer`, `tree`, `search`, `scaffold`, `cli`, and
`runtime`.

### GUI check — the window

```console
python scripts/gui_smoke.py            # defaults to ./docs
python scripts/gui_smoke.py path/to/docs
python scripts/gui_smoke.py docs --show   # watch it happen in a real window
```

Builds the actual `MainWindow` and drives it: sidebar, rendering, search, theme
toggling, live reload against a real file on disk (restored afterwards), and
navigation.

**It clicks links by executing JavaScript in the page, not by calling the handlers.**
That distinction is the whole point. Calling `acceptNavigationRequest` directly runs it
outside Qt's navigation machinery, where loading a new document is harmless. A genuine
click runs it *during* navigation, where re-entering the page with `setHtml()` crashes
the renderer outright — a crash a handler-level test passes straight through. If you
touch link handling, run this script.

Exit code 0 means everything passed.

## Assets

Themes are plain CSS in `src/docsviewer/assets/`:

| File | Contents |
| --- | --- |
| `base.css` | Layout and typography, written against `--dv-*` custom properties |
| `light.css` / `dark.css` | Colour tokens only |
| `pygments-light.css` / `pygments-dark.css` | Generated code-highlighting rules |

To restyle, edit the colour tokens — `base.css` refers to them by name, so both themes
stay in step. The Pygments files are generated from a Pygments style:

```python
from pygments.formatters import HtmlFormatter
HtmlFormatter(style="github-dark").get_style_defs(".markdown-body pre")
```

The Qt chrome (sidebar, toolbar, status bar) is styled separately by the `_QSS_LIGHT`
and `_QSS_DARK` stylesheets in `app.py`; change both together or dark mode will end up
with a white sidebar.

## How `init` gets its content

From `src/docsviewer/templates/`, copied recursively with `{{project_name}}` and
`{{date}}` substituted. Because the folder sits inside the package, the same path
resolves from a wheel and from a source checkout — no fallback needed.

The templates are a **skeleton**: headings and `TODO` markers, plus a complete changelog
(that boilerplate is the same for every project; nothing else is).

1.0.0 briefly copied docsviewer's own `docs/` instead, on the theory that one folder
serving as both manual and scaffold couldn't drift. It removed the drift and introduced
a worse problem: every scaffolded project began life documenting the viewer rather than
itself, and `--title` had nothing to substitute. Keep the two separate.

Adding a template is just adding a file — `iter_template_files()` discovers whatever is
there.

## Branching

`main` stays releasable. Work happens on a branch and lands through a pull request:

```console
git switch -c feature/search-filters
# …commit…
git push -u origin feature/search-filters
```

CI runs on the pull request; merge once it's green.

## Continuous integration

`.github/workflows/ci.yml` runs on every pull request against `main`, and on pushes to
`main`. Two jobs:

| Job | What it does |
| --- | --- |
| **test** | `ruff check` and `pytest` across Python 3.9–3.13 on Linux, plus 3.12 on Windows and macOS |
| **build** | Builds the sdist and wheel, runs `twine check`, verifies the packaged data, and installs the wheel into a clean environment to run `docsviewer init` |

That last step exists because of a real failure mode: `assets/` and `docs/` are loaded
with `importlib.resources`, so a wheel built without them installs perfectly and only
breaks when someone uses it. CI fails the build instead.

The test job needs no display — the modules under test import no Qt.

## Releasing

Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

1. On a release branch, update `__version__` in `src/docsviewer/__init__.py`
2. Move the `[Unreleased]` entries under a new version heading in `CHANGELOG.md`, and
   add the highlights to `docs/changelog.md`
3. Open a PR, let CI pass, merge
4. Tag and publish a GitHub Release named `vMAJOR.MINOR.PATCH`

Publishing the release triggers `.github/workflows/cd.yml`, which checks the tag matches
`__version__`, builds, verifies the packaged data again, and uploads to PyPI.

A mismatched tag fails the build deliberately — releasing `v1.2.0` from a tree still
saying `1.1.0` would upload the wrong version number, which cannot be undone on PyPI.

### Trying it on TestPyPI first

Run the **CD** workflow manually from the Actions tab and pick `testpypi`. Then:

```console
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ docsviewer
```

The extra index is needed because TestPyPI doesn't carry PySide6.

### One-time PyPI setup

Publishing uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/), so no
API token is stored in the repository.

On PyPI, under *Publishing*, add a pending publisher:

| Field | Value |
| --- | --- |
| Owner | `grish-ka` |
| Repository | `docsViewer` |
| Workflow | `cd.yml` |
| Environment | `pypi` |

Repeat on TestPyPI with the environment `testpypi`. Then create both environments in the
GitHub repository settings — adding a required reviewer to `pypi` gives you a manual
approval gate before anything is uploaded.

> The distribution name `docsviewer` may already be taken on PyPI. If it is, change
> `name` in `pyproject.toml` — the import package can stay `docsviewer` — and update the
> URLs in the workflow.
