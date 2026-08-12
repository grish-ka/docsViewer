"""Windows/desktop runtime tweaks applied before the GUI starts.

Kept separate from `app.py` because one of these must run *before* QtWebEngine is
imported, and import order inside a module is fragile. `cli.py` calls into here,
then imports the app.
"""

from __future__ import annotations

import os
import sys

# Chromium flags used when GPU acceleration is off (the default).
SOFTWARE_RENDERING_FLAGS = "--disable-gpu --disable-gpu-compositing"

# Set DOCSVIEWER_GPU=1 to keep hardware acceleration.
GPU_ENV_VAR = "DOCSVIEWER_GPU"

SW_HIDE = 0

# If one of these shares our console, we were launched from a terminal and the
# window belongs to the user, not to us.
SHELL_IMAGES = frozenset(
    {
        "cmd.exe",
        "powershell.exe",
        "pwsh.exe",
        "bash.exe",
        "sh.exe",
        "zsh.exe",
        "fish.exe",
        "wt.exe",
        "windowsterminal.exe",
        "openconsole.exe",
        "conemu.exe",
        "conemu64.exe",
        "alacritty.exe",
        "wezterm-gui.exe",
        "hyper.exe",
        "far.exe",
    }
)

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def gpu_requested() -> bool:
    return os.environ.get(GPU_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def configure_rendering() -> bool:
    """Render in software unless the user opts into GPU acceleration.

    QtWebEngine's accelerated path creates a Direct3D swap chain and presents
    frames through it. Overlay tools that look for exactly that -- MSI Afterburner
    and RivaTuner Statistics Server, Discord's overlay, GeForce Experience --
    conclude the process is a game and hook it with an FPS counter.

    A documentation reader draws static text, so it gains nothing from GPU
    compositing and loses the false positive by turning it off. This also silences
    the "Failed to create GLES3 context" warnings seen on some machines.

    Returns True when software rendering was applied. Respects a
    QTWEBENGINE_CHROMIUM_FLAGS value you set yourself.
    """
    if gpu_requested():
        return False

    # Never clobber flags the user supplied.
    if not os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS"):
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = SOFTWARE_RENDERING_FLAGS
    return True


def apply_qt_attributes() -> None:
    """Ask Qt itself for software OpenGL, for the same reason as above.

    Must be called before a QApplication exists.
    """
    if gpu_requested():
        return
    from PySide6.QtCore import QCoreApplication, Qt

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)


def _image_name(kernel32, pid: int) -> str | None:
    """Executable name for a pid, lowercased, or None if it can't be read."""
    import ctypes

    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        size = ctypes.c_uint32(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value.replace("/", "\\").rsplit("\\", 1)[-1].lower()
    finally:
        kernel32.CloseHandle(handle)
    return None


def console_is_ours() -> bool:
    """True when the console window was created for us rather than by a terminal.

    Counting attached processes is not enough -- a standalone launch can show two
    (the launcher and the interpreter), so "exactly one" produces false negatives.
    What actually distinguishes the two cases is whether a *shell* is attached.

    Unknown process names are treated as "not ours": showing a stray console is a
    cosmetic annoyance, whereas hiding the user's terminal is data loss.
    """
    if sys.platform != "win32":
        return False

    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if not kernel32.GetConsoleWindow():
        return False

    buffer = (ctypes.c_uint32 * 64)()
    attached = kernel32.GetConsoleProcessList(buffer, 64)
    if attached < 1:
        return False

    import os

    for pid in list(buffer[: min(attached, 64)]):
        if pid == os.getpid():
            continue
        name = _image_name(kernel32, pid)
        if name is None or name in SHELL_IMAGES:
            return False
    return True


def hide_own_console() -> bool:
    """Hide the console window Windows opens behind the GUI, when it is ours.

    Launching `docsviewer` from Explorer, a shortcut, or `Start-Process` gives the
    process a console window of its own, which sits behind the app doing nothing.
    Run from a terminal, that console belongs to the shell and is left alone.

    Returns True if a console was hidden.
    """
    if sys.platform != "win32":
        return False

    try:
        import ctypes

        if not console_is_ours():
            return False

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)

        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return False

        user32.ShowWindow(hwnd, SW_HIDE)
        return True
    except Exception:
        # Never let a cosmetic tweak stop the app from starting.
        return False
