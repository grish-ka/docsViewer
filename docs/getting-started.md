# Getting Started

## Requirements

| Requirement | Version |
| --- | --- |
| Python | 3.9 or newer |
| OS | Windows, macOS, or Linux |

Qt and its web engine arrive automatically with PySide6 — there is nothing to install
separately. The download is large (a few hundred MB), so the first install takes a
minute.

## Install

From a checkout:

```console
git clone https://github.com/grish-ka/docsViewer
cd docsViewer
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -e .
```

Confirm it landed:

```console
docsviewer --version
```

## Your first docs folder

Go to any project and scaffold one:

```console
cd path\to\my-project
docsviewer init
```

That writes:

```
docs/
├── README.md
├── getting-started.md
├── changelog.md
└── reference/
    └── api.md
```

`init` never overwrites your work. Run it again in the same project and every existing
file is reported as `skipped` — pass `--force` if you genuinely want them replaced.

## Read them

From the same directory:

```console
docsviewer
```

The window opens with the folder tree on the left and the first document rendered on the
right. Leave it running while you edit: saving a file re-renders it immediately.

## Where to go next

- [Commands](commands.md) — every flag, and the rules for which folder gets opened
- [The Interface](interface.md) — search and keyboard shortcuts
- [Writing Docs](writing-docs.md) — how to control sidebar titles and ordering
