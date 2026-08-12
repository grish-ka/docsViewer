# docsviewer

A small desktop app for reading a project's `docs/` folder, plus a scaffolder that
creates one. Point it at a folder of Markdown and get a sidebar, real rendered HTML,
search, and live reload — without leaving a native window.

```console
docsviewer init     # create ./docs with starter pages
docsviewer          # read them
```

## Features

- **Rendered Markdown** — GFM tables, task lists, footnotes, definition lists, and
  syntax-highlighted code via Pygments
- **Sidebar tree** — built from your folder structure, titled from each file's `# H1`
- **Full-text search** — across every document, with line-level hits
- **Live reload** — save a file in your editor and the open page updates, scroll
  position intact
- **Dark / light themes** — toggle with `Ctrl+D`, remembered between sessions
- **Sane links** — `[text](other.md)` navigates in-app, `https://` links open in your
  real browser

## Install

Requires Python 3.9+.

```console
git clone <your-repo-url>
cd docsViewer
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .
```

## Usage

```console
docsviewer                      # read ./docs, else the current folder
docsviewer path/to/docs         # read a specific folder
docsviewer notes/api.md         # open a single file
docsviewer . --here             # read this folder, ignoring its docs/
docsviewer init                 # scaffold ./docs
docsviewer init . --force       # overwrite existing starter files
```

A project directory resolves to its `docs/` subfolder when it has one — nearly every
project has a root `README.md`, so keying off "contains Markdown" would mean `docs/`
never won. Use `--here` to browse the folder itself.

`init` never overwrites your work — existing files are reported as `skipped` unless you
pass `--force`. The pages it writes are a copy of **this project's own `docs/` folder**,
so there is no separate templates directory to keep in sync.

Full documentation lives in [`docs/`](docs/README.md) — read it with the tool itself:

```console
docsviewer
```

Release notes are in [`CHANGELOG.md`](CHANGELOG.md).

### Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+F` | Focus search |
| `Ctrl+D` | Toggle dark / light |
| `Ctrl+O` | Open another folder |
| `Ctrl+R` | Reload current page |
| `Alt+←` / `Alt+→` | Back / forward |
| `Ctrl+±` / `Ctrl+0` | Zoom in, out, reset |

## Development

```console
pip install -r requirements-dev.txt
pytest
ruff check .
```

The core modules (`renderer`, `tree`, `search`, `scaffold`) import no Qt, so the whole
test suite runs headlessly.

## Layout

| Module | Responsibility |
| --- | --- |
| `renderer.py` | Markdown → styled standalone HTML |
| `tree.py` | Folder scan, sorting, title extraction |
| `search.py` | In-memory full-text index |
| `scaffold.py` | The `init` command — copies `docs/` into new projects |
| `watcher.py` | watchdog events bridged onto the Qt event loop |
| `settings.py` | Persisted theme and window state |
| `app.py` | Main window and web view |
| `cli.py` | Argument parsing and entry point |

## License

MIT
