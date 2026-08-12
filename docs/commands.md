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

## `init`

```console
docsviewer init [PATH] [--title NAME] [--force]
```

Creates a `docs/` folder with starter documentation.

| Argument | Effect |
| --- | --- |
| `PATH` | Project directory to scaffold into (default: current directory) |
| `--title NAME` | Replaces `{{project_name}}` placeholders (default: the folder's name) |
| `--force` | Overwrite files that already exist |

The pages `init` writes are a copy of docsviewer's own documentation — the same pages
you're reading. They describe the viewer, so treat them as a starting skeleton to
overwrite with your project's content, not as text about your project.

`--title` and `{{date}}` are substituted during the copy wherever those placeholders
appear. The bundled pages contain none, so `--title` has no visible effect on them; it
matters if you replace the pages with templates of your own.

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
