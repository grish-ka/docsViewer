# Commands

docsviewer has two commands: the default **viewer**, and **`init`**.

## The default command

```console
docsviewer [PATH] [--here] [--version]
```

Opens the GUI. With no arguments it works out what to show from the current directory.

| Argument | Effect |
| --- | --- |
| *(none)* | Open `./docs` if it exists, otherwise the current folder |
| `PATH` (folder) | Open that folder — or its `docs/` subfolder, if it has one |
| `PATH` (`.md` file) | Open that file, with its containing folder as the tree |
| `--here` | Use the folder as given; never descend into `docs/` |
| `--version` | Print the version and exit |

```console
docsviewer                      # ./docs, else the current folder
docsviewer path/to/docs         # a specific folder
docsviewer notes/api.md         # a single file
docsviewer . --here             # this folder, ignoring its docs/
```

If nothing suitable is found, a folder picker opens instead of failing.

### How a path is resolved

A directory resolves to its `docs/` subfolder whenever it has one containing Markdown.

This preference is deliberate, and it is the one rule worth understanding. Nearly every
project has a `README.md` at its root, so a rule like *"use this folder if it contains
Markdown"* would match the root every time and `docs/` would essentially never win.
Running `docsviewer` in a project root should show you the project's documentation, not
its README plus every stray Markdown file in the tree.

```
my-project/
├── README.md         <- not what you want to browse
└── docs/             <- this is opened instead
    └── ...
```

When you *do* want the folder itself — to browse a repository root, say — pass `--here`.

### Home and root directories

Your home directory, anything above it, and a drive or filesystem root are never scanned
automatically. Running `docsviewer` in `C:\Users\you` opens the folder picker rather than
treating your whole profile as a docs folder — which would mean walking every directory
in it, reading every Markdown file into the search index, and watching the lot for
changes.

A `docs/` subfolder there is still honoured, since that is cheap and unambiguous. To
browse such a folder deliberately, pass `--here` or name it explicitly.

Every scan is also bounded — 10 levels deep, 5,000 directories, 2,000 Markdown files —
so even a deliberate one stays responsive. Real docs folders are nowhere near these
limits.

## `init`

```console
docsviewer init [PATH] [--title NAME] [--force]
```

Creates a `docs/` folder with starter documentation.

| Argument | Effect |
| --- | --- |
| `PATH` | Project directory to scaffold into (default: current directory) |
| `--title NAME` | Project name written into the pages (default: the folder's name) |
| `--force` | Overwrite files that already exist |

It writes a **skeleton**, not prose: headings and structure with `TODO` markers for you
to fill in.

```
docs/
├── README.md            index — contents list, one-line summary
├── getting-started.md   requirements, install, usage
├── changelog.md         ready to use as-is
└── reference/
    └── api.md           a table and an example to adapt
```

`changelog.md` is the exception — it arrives complete, with the Keep a Changelog and
Semantic Versioning conventions written out and an `[Unreleased]` section ready for your
first entry. That boilerplate is genuinely the same for every project; the rest is not.

`--title` fills the `{{project_name}}` placeholders throughout, and `{{date}}` becomes
today's date in the changelog.

```console
docsviewer init
docsviewer init . --title "My Project"
docsviewer init ../other-project
docsviewer init --force
```

`init` prints what it did:

```
  created  docs\README.md
  created  docs\getting-started.md
  created  docs\reference\api.md
  created  docs\changelog.md

Docs folder ready at C:\path\to\my-project\docs
Run 'docsviewer' from this directory to read them.
```

Re-running is safe — existing files are skipped, never clobbered:

```
  skipped  docs\README.md  (exists)

Nothing written. Pass --force to overwrite the existing files.
```

`init` never opens a window, so it works fine over SSH or inside a script.

## `python -m docsviewer`

Every form above also works through the module, which is handy when the console script
isn't on your `PATH`:

```console
python -m docsviewer
python -m docsviewer init --title "My Project"
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success — including closing the window normally, or cancelling the folder picker |
| `2` | Bad arguments: a path that doesn't exist, or a file that isn't Markdown |
