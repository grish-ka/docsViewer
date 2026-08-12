# Changelog

All notable changes to docsviewer are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] — 2026-08-12

### Fixed

- **Running `docsviewer` in a home directory scanned the entire user profile.** With no
  `docs/` folder present, the viewer fell back to "browse the current folder", which
  walked every directory beneath it, read every Markdown file found into the search
  index, and placed a recursive filesystem watch over all of it. On a real profile that
  is thousands of unrelated files and looks like a hang. Home directories, their
  ancestors, and drive or filesystem roots are no longer adopted automatically; the
  folder picker opens instead. A `docs/` subfolder in such a location is still used, and
  `--here` or an explicit path still opens them deliberately.
- Folder scans are now bounded — 10 levels deep, 5,000 directories, 2,000 Markdown files
  — so even a deliberately mis-aimed root stays responsive instead of running away. Real
  docs folders are orders of magnitude below these limits.

### Changed

- **`init` writes a skeleton again instead of copying docsviewer's own documentation.**
  1.0.0 shipped the manual as the scaffold so the two could not drift apart. That traded
  one problem for a worse one: every new project began life with pages describing the
  viewer rather than itself, and `--title` had no placeholders left to substitute. New
  projects now get headings and `TODO` markers to fill in, and `--title` works again.
- `changelog.md` remains complete rather than a skeleton — the Keep a Changelog and
  Semantic Versioning conventions are identical across projects, so there is nothing for
  the author to invent.
- The wheel no longer bundles docsviewer's `docs/` folder; it ships
  `docsviewer/templates/` instead.

## [1.0.0] — 2026-08-12

First release.

### Added

- **Desktop viewer** built on PySide6 and QtWebEngine — sidebar tree, rendered document
  pane, toolbar, and status bar in a native window.
- **Markdown rendering** via `markdown-it-py`: CommonMark plus tables, strikethrough,
  task lists, footnotes, definition lists, autolinks, and YAML front matter (hidden from
  output). Code blocks are highlighted with Pygments; unknown languages fall back to
  plain text rather than failing.
- **Sidebar tree** built from the folder structure. Titles come from each document's
  first `# H1` — ATX or setext, front matter skipped, headings inside code fences
  ignored — falling back to a prettified filename. `README.md` sorts first in each
  folder, then subfolders, then files alphabetically. Folders with no Markdown beneath
  them are pruned, and build/VCS directories are skipped.
- **Full-text search** across every document, case-insensitive, with line-numbered
  results and snippets. Results are capped so short queries stay responsive, and the
  search term is highlighted in the opened page.
- **Live reload** — a `watchdog` observer bridged onto the Qt event loop re-renders the
  open document when it changes on disk, preserving scroll position. Adding or removing
  files refreshes the sidebar and the search index.
- **Dark and light themes**, toggled with `Ctrl+D`, covering the document and the Qt
  chrome. Persisted along with window geometry and sidebar width via `QSettings`.
- **Link handling** — relative `.md` links navigate in-app, heading anchors scroll,
  `https://` links open in the system browser, and other local files open in their
  default application. Back/forward history included.
- **Zoom** at `Ctrl++` / `Ctrl+-` / `Ctrl+0`.
- **`docsviewer init`** — scaffolds a `docs/` folder into a project. Runs headless, never
  overwrites existing files without `--force`, and accepts `--title` to name the project
  in the generated pages.
- **`--here`** on the default command, to browse a folder without descending into its
  `docs/` subfolder.
- **`python -m docsviewer`** as an alternative to the console script, and
  **`docsviewerw`** on Windows for a launcher that never allocates a console.
- **Software rendering by default.** Qt's browser engine normally presents through a
  Direct3D swap chain, which overlay tools (MSI Afterburner / RivaTuner, the Discord
  overlay, GeForce Experience) treat as a game and hook with an FPS counter. A reader
  drawing static text gains nothing from GPU compositing, so it is off by default; set
  `DOCSVIEWER_GPU=1` to restore it. Also silences the GLES context warnings some
  machines print at startup.
- **Automatic console hiding on Windows.** Launching from a shortcut or Explorer no
  longer leaves an empty console behind the window. Detection keys off whether a shell
  shares the console rather than counting attached processes — a standalone launch can
  report two — so running from a terminal leaves that terminal alone.
- Documentation in `docs/`, covering commands, the interface, writing docs,
  configuration, troubleshooting, and development.
- `scripts/gui_smoke.py` — an end-to-end check that builds the real window and drives
  it: sidebar, rendering, search, theme toggling, live reload against a real file, and
  navigation driven by clicking links via JavaScript in the page.

### Notes

- `init` copies the project's own `docs/` folder, which ships inside the wheel at
  `docsviewer/docs/`. There is no separate templates directory, so the shipped manual and
  the scaffold cannot drift apart.
- A directory resolves to its `docs/` subfolder when it has one. Because nearly every
  project has a root `README.md`, keying the decision off "does this folder contain
  Markdown" would have meant `docs/` almost never won.
- Link clicks are dispatched on the next event-loop pass rather than handled inline.
  Loading a document from inside `acceptNavigationRequest` re-enters the page while Qt
  is still processing that navigation, which terminates the render process. Keep the
  deferral if you touch link handling — and exercise it with `scripts/gui_smoke.py`,
  since calling the handler directly runs outside the navigation machinery and cannot
  reproduce the fault.

[Unreleased]: https://github.com/grish-ka/docsViewer/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/grish-ka/docsViewer/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/grish-ka/docsViewer/releases/tag/v1.0.0
