# Writing Docs

How docsviewer interprets a folder, so you can shape what the sidebar looks like.

## Sidebar titles

Each file's entry is titled by its **first `# H1`**:

```markdown
# Getting Started      ->  sidebar shows "Getting Started"
```

Both heading styles work, and a YAML front-matter block is skipped when looking:

```markdown
---
author: you
---

# Getting Started
```

```markdown
Getting Started
===============
```

With no H1, the filename is prettified instead — `getting-started.md` becomes
*Getting Started*. Headings inside fenced code blocks are ignored, so a `# comment` in
an example won't be mistaken for a title.

**Give every page an H1.** It's the difference between a sidebar that reads like a table
of contents and one that reads like a directory listing.

## Ordering

Within each folder:

1. `README.md`, then `index.md`, then `home.md`
2. Subfolders, alphabetically
3. Remaining files, alphabetically

There is no front-matter `order:` key — if you need a specific sequence, name the files
for it (`01-intro.md`, `02-setup.md`).

## Which files appear

Included: `.md`, `.markdown`, `.mdown`, `.mkd`.

Skipped entirely: `.git`, `.venv`, `venv`, `env`, `node_modules`, `__pycache__`,
`.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `site-packages`, `dist`, `build`,
`.idea`, `.vscode`, and any folder whose name starts with a dot.

Folders with no Markdown anywhere beneath them are hidden, so asset directories stay out
of the way.

## Links

Relative links resolve against the file they're written in:

```markdown
[Setup](guide/setup.md)          <- opens in the viewer
[Back to index](../README.md)    <- also fine
[Install steps](setup.md#install)<- opens the file, scrolls to the heading
[The spec](https://example.com)  <- opens your browser
```

Heading anchors are generated automatically by lowercasing the heading and replacing
spaces with hyphens — `## Live Reload` becomes `#live-reload`.

## Images

Relative paths work, resolved from the document's own location:

```markdown
![Architecture](images/architecture.png)
```

Images are capped at the content width. Keep them inside the docs folder — the
`images/` directory itself stays hidden from the sidebar.

## Supported Markdown

CommonMark, plus:

| Feature | Syntax |
| --- | --- |
| Tables | `\| a \| b \|` |
| Task lists | `- [x] done` |
| Strikethrough | `~~gone~~` |
| Footnotes | `text[^1]` / `[^1]: note` |
| Definition lists | `term` / `: definition` |
| Autolinks | bare `https://…` becomes a link |
| Front matter | `---` block at the top, hidden from output |
| Fenced code | ```` ```python ```` |

### Code blocks

Tag the fence with a language for highlighting:

````markdown
```python
def hello(name: str) -> str:
    return f"hello {name}"
```
````

Any language Pygments knows works. An unknown or missing tag still renders — just
without colours — so nothing breaks.

### Raw HTML

Inline HTML passes through, which is occasionally useful:

```markdown
<details>
<summary>Click to expand</summary>

Hidden content here.

</details>
```

Note that pages are rendered from a local file with no network access, so anything
pulling in a remote script, stylesheet, or image won't load.

## A suggested shape

```
docs/
├── README.md              index — what this is, links to everything
├── getting-started.md     install and first run
├── guide/
│   ├── configuration.md
│   └── deployment.md
├── reference/
│   └── api.md             the details
└── changelog.md           what changed, newest first
```

Keep pages short. If one grows past a couple of screens, split it and link the pieces —
the sidebar is cheaper to scan than a long page.
