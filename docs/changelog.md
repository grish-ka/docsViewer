# Changelog

Release notes for docsviewer. Versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) — `MAJOR.MINOR.PATCH`, where
a **major** bump breaks existing usage, a **minor** bump adds features compatibly, and a
**patch** bump fixes bugs.

The full itemised list lives in `CHANGELOG.md` at the repository root.

## 1.0.0 — 2026-08-12

First release. Everything below is new.

### Reading

A native window with a sidebar tree on the left and rendered HTML on the right. The tree
mirrors your folders and titles each page by its first `# H1`, with `README.md` sorted to
the top of each folder. Build and VCS directories are skipped, and folders with no
Markdown in them are hidden.

Documents render as real HTML — tables, task lists, footnotes, definition lists, and
Pygments-highlighted code. Relative `.md` links navigate inside the viewer, heading
anchors scroll, and `https://` links open in your normal browser. Back and forward work
as they do in one.

### Searching

A search box over the tree matches case-insensitively across every document, listing
each hit with its line number and a snippet. Clicking one opens the document with the
term highlighted.

### Writing

The folder is watched while the window is open. Saving a file re-renders it immediately
and **keeps your scroll position**, so you can write in one window and read in another.
Adding or deleting files updates the sidebar and search index.

### Appearance

Dark and light themes, toggled with `Ctrl+D`, covering the whole window rather than just
the document. Your choice, window size, and sidebar width are remembered between
sessions. Zoom with `Ctrl++` / `Ctrl+-` / `Ctrl+0`.

### Scaffolding

`docsviewer init` creates a `docs/` folder in any project. It never overwrites your files
without `--force`, and runs without opening a window, so it works over SSH and in
scripts.

### Command line

`docsviewer` opens `./docs` when a project has one, falling back to the current folder;
`--here` overrides that. A folder, a single `.md` file, or nothing at all are all valid
arguments. See [Commands](commands.md) for the full reference.
