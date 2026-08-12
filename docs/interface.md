# The Interface

```
┌─ docsviewer — docs ───────────────────────────────────┐
│ ◀ ▶  Open Folder…  Dark Mode                          │  toolbar
├────────────────────┬──────────────────────────────────┤
│ [Search docs…    ] │  # Getting Started               │
│                    │                                  │
│ Docs               │  Install with pip.               │
│ ├ Getting Started  │                                  │
│ ├ Reference        │  ```python                       │
│ │ └ Api            │  import docsviewer               │
│ └ Changelog        │  ```                             │
├────────────────────┴──────────────────────────────────┤
│                                    getting-started.md │  status bar
└───────────────────────────────────────────────────────┘
```

## The sidebar

Mirrors your folder structure. Folder names are shown in bold; file entries are titled
by each document's first `# H1`, falling back to a prettified filename. `README.md`
sorts to the top of its folder, then subfolders, then everything else alphabetically.

Folders containing no Markdown at any depth are hidden, so an `images/` directory won't
clutter the tree.

## Search

Type in the box above the tree. After a short pause the tree is replaced by a list of
matching lines, each showing the document title, the line number, and a snippet:

```
Commands  ·  42
…pass --here to browse the folder itself…
```

Search is case-insensitive substring matching across every Markdown file in the tree.
Click a result to open that document; the term is highlighted in the page. Clear the box
to bring the tree back.

Results are capped so a one-letter query can't lock up the window, and the status bar
reports how many matches were found across how many files.

## The document view

Real rendered HTML — tables, task lists, footnotes, definition lists, images, and
syntax-highlighted code blocks.

Links behave the way you'd expect:

| Link | Behaviour |
| --- | --- |
| `[text](other.md)` | Opens in the viewer |
| `[text](#a-heading)` | Scrolls to that heading |
| `[text](guide/setup.md#install)` | Opens the file *and* scrolls to the heading |
| `[text](https://example.com)` | Opens in your normal browser |
| `[text](diagram.png)` | Opens in your system's default application |

Back and forward move through the documents you've visited, as in a browser.

## Live reload

The folder is watched while the window is open. Save a file in your editor and the page
re-renders within a moment, **keeping your scroll position** — so you can write in one
window and read in the other without losing your place. Adding, renaming, or deleting
files refreshes the sidebar and the search index too.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+F` | Focus the search box |
| `Ctrl+D` | Toggle dark / light theme |
| `Ctrl+O` | Open a different folder |
| `Ctrl+R` | Reload the current page |
| `Alt+←` | Back |
| `Alt+→` | Forward |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |
| `Ctrl+Q` | Quit |

On macOS, use `Cmd` in place of `Ctrl`.
