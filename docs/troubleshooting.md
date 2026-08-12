# Troubleshooting

## "No Markdown files found"

The folder that was opened has no `.md` files anywhere beneath it. Either you're in the
wrong directory, or the files are in a folder on the
[skip list](writing-docs.md#which-files-appear) — anything dot-prefixed, `node_modules`,
`build`, and similar are ignored on purpose.

Use **Open Folder…** (`Ctrl+O`) to pick the right one, or run `docsviewer init` to create
a docs folder.

## It opened the wrong folder

Running `docsviewer` in a project root opens `./docs` rather than the root itself. That's
the intended behaviour — see
[how a path is resolved](commands.md#how-a-path-is-resolved).

To browse the folder itself:

```console
docsviewer . --here
```

## A file isn't in the sidebar

- Check the extension: only `.md`, `.markdown`, `.mdown`, and `.mkd` are picked up
- Check the folder isn't on the skip list, or dot-prefixed
- A folder appears only if it contains Markdown *somewhere* beneath it

## Live reload didn't fire

Some editors write via a temporary file and rename it, which can look like a delete plus
a create. The sidebar refreshes either way; if the open page looks stale, `Ctrl+R`
re-renders it. Reload also won't fire for files edited outside the opened folder.

## The window opens off-screen

Position is restored from the last session, which goes wrong if you've unplugged a
monitor. [Reset the saved settings](configuration.md#resetting) and relaunch.

## MSI Afterburner shows an FPS counter over the window

Overlay tools — MSI Afterburner and RivaTuner Statistics Server, the Discord overlay,
GeForce Experience — decide something is a game by looking for a Direct3D or OpenGL swap
chain. Qt's embedded browser creates one when GPU acceleration is on, so the docs reader
gets mistaken for a game and hooked with an FPS counter.

docsviewer renders in software by default for exactly this reason. Static text gains
nothing from GPU compositing, and turning it off also silences the GLES warnings below.

If you'd rather have hardware acceleration back:

```console
set DOCSVIEWER_GPU=1
docsviewer
```

The overlay will likely return. To keep acceleration *and* lose the overlay, add
`docsviewer.exe` to your overlay tool's exclusion list instead.

## An empty console window opens behind the app

It shouldn't — docsviewer hides the console Windows gives it when launched from a
shortcut or Explorer, while leaving your terminal alone when you run it from one.

If one still appears, use the GUI launcher, which never allocates a console at all:

```console
docsviewerw
```

Point any shortcut at `docsviewerw.exe` rather than `docsviewer.exe`. Note it prints
nothing, so use plain `docsviewer` when you want `init`'s output.

## Console warnings on startup

Messages like these on Windows and Linux are normal and harmless:

```
Failed to create GLES3 context, fallback to GLES2
GPUInfo not initialized on GpuInfoUpdate
QFontDatabase: Cannot find font directory …
```

They come from Qt's embedded browser negotiating graphics support, and the window works
regardless. If rendering is genuinely broken, force software rendering:

```console
set QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu
docsviewer
```

## Install fails with a long-path error

On Windows, `pip install` can fail with `[Errno 2] No such file or directory` on a very
long path inside `PySide6`. Qt's bundled files nest deeply, and the 260-character limit
is reached before the install finishes.

Either enable long-path support:

```console
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f
```

(needs an administrator prompt and a reboot), or create the virtual environment
somewhere shallower, like `C:\dev\myproject`.

## `docsviewer` isn't a recognised command

The virtual environment isn't active, or its `Scripts` directory isn't on your `PATH`.
Activate it, or use the module form:

```console
python -m docsviewer
```

## Images aren't showing

Use paths relative to the document, and keep the files inside the docs folder. Remote
images (`https://…`) do not load — pages render from a local file with no network
access.

## Search finds nothing

Search is plain case-insensitive substring matching over the raw Markdown — no regex,
no fuzzy matching, no stemming. Searching `install` won't match `installation`… but
`instal` will match both. It searches the source text, so a word split across a line
break won't match.
