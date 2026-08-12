# Configuration

There is no configuration file. docsviewer remembers a handful of things by itself, and
everything else is a command-line flag.

## What's remembered

| Setting | Set by | Restored |
| --- | --- | --- |
| Theme (light / dark) | `Ctrl+D`, or the toolbar button | On every launch |
| Window size and position | Moving or resizing the window | On every launch |
| Sidebar width | Dragging the splitter | On every launch |
| Last opened folder | Opening a folder | Used as the starting directory in the folder picker |

Zoom level is deliberately *not* persisted — it resets to 100% each launch, since a zoom
you set for one document is rarely the one you want next time.

## Where it's stored

Qt's own settings store, which means the platform-native location:

| Platform | Location |
| --- | --- |
| Windows | Registry, `HKEY_CURRENT_USER\Software\docsviewer\docsviewer` |
| macOS | `~/Library/Preferences/com.docsviewer.docsviewer.plist` |
| Linux | `~/.config/docsviewer/docsviewer.conf` |

Nothing is written into your project — a docs folder stays exactly as you left it.

### Resetting

Delete that key or file and the next launch starts fresh: light theme, default window
size. This is the fix if the window ever restores off-screen after unplugging a monitor.

On Windows:

```console
reg delete "HKCU\Software\docsviewer\docsviewer" /f
```

## Environment variables

| Variable | Effect |
| --- | --- |
| `DOCSVIEWER_GPU=1` | Re-enable GPU acceleration (off by default, see below) |
| `QTWEBENGINE_CHROMIUM_FLAGS` | Passed straight to Qt's browser engine; set it yourself and docsviewer won't override it |

### Why GPU acceleration is off

Qt's embedded browser normally renders through a Direct3D swap chain. Overlay tools that
look for one — MSI Afterburner / RivaTuner, the Discord overlay, GeForce Experience —
take that as proof the process is a game and attach an FPS counter to the window.

A reader that draws static text gains nothing from GPU compositing, so it's disabled by
default. This also avoids the "Failed to create GLES3 context" warnings some machines
print at startup. Set `DOCSVIEWER_GPU=1` if you want it back.

## Launchers on Windows

| Command | Console | Use for |
| --- | --- | --- |
| `docsviewer` | Hidden automatically when launched from a shortcut; kept when run from a terminal | Everything, including `init` |
| `docsviewerw` | Never created | Shortcuts and Start Menu entries |

`docsviewerw` prints nothing at all, so `init`'s summary is invisible there.

## Themes

Two built-in themes, toggled with `Ctrl+D`. The choice is saved immediately, so it
survives a crash as well as a clean exit.

Both themes style the whole window, not just the document — sidebar, toolbar, and status
bar included. Code highlighting switches with them.

Custom themes aren't supported through configuration. They live in the package as plain
CSS, so editing them is straightforward if you install from a checkout — see
[Development](development.md#assets).
