# docsviewer

A desktop reader for a project's `docs/` folder, plus a scaffolder that creates one.
Point it at a folder of Markdown and get a sidebar, properly rendered HTML, full-text
search, and live reload — in a native window rather than a browser tab.

```console
docsviewer init     # create ./docs with starter pages
docsviewer          # read them
```

## Contents

| Page | What's in it |
| --- | --- |
| [Getting Started](getting-started.md) | Install it and open your first folder |
| [Commands](commands.md) | Every command and flag, and how a path is resolved |
| [The Interface](interface.md) | Window tour, search, keyboard shortcuts |
| [Writing Docs](writing-docs.md) | How the sidebar is built, links, supported Markdown |
| [Configuration](configuration.md) | Themes and what's remembered between sessions |
| [Troubleshooting](troubleshooting.md) | When something looks wrong |
| [Development](development.md) | Repo layout, tests, releasing |
| [Changelog](changelog.md) | Release notes |

## What it does

- **Renders real HTML** — GFM tables, task lists, footnotes, definition lists, and
  syntax-highlighted code, not a plain-text approximation
- **Builds a sidebar from your folders** — titles come from each file's `# H1`
- **Searches every document** — with line-level results you can click
- **Reloads as you write** — save in your editor, the page updates, scroll position kept
- **Dark and light themes** — toggled with `Ctrl+D`, remembered next launch
- **Handles links sensibly** — `[text](other.md)` navigates in-app, `https://` links
  open in your real browser

## Why a docs folder

The tool assumes one convention: **each project keeps its documentation in a `docs/`
folder at its root.** `docsviewer init` creates that folder, and running `docsviewer`
inside a project finds it automatically — see
[how a path is resolved](commands.md#how-a-path-is-resolved).
