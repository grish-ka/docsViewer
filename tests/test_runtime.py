import sys

from docsviewer.runtime import (
    GPU_ENV_VAR,
    SHELL_IMAGES,
    SOFTWARE_RENDERING_FLAGS,
    configure_rendering,
    console_is_ours,
    gpu_requested,
    hide_own_console,
)


def test_software_rendering_is_the_default(monkeypatch):
    monkeypatch.delenv(GPU_ENV_VAR, raising=False)
    monkeypatch.delenv("QTWEBENGINE_CHROMIUM_FLAGS", raising=False)

    assert configure_rendering() is True
    import os

    assert os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] == SOFTWARE_RENDERING_FLAGS


def test_gpu_opt_in_leaves_flags_alone(monkeypatch):
    monkeypatch.setenv(GPU_ENV_VAR, "1")
    monkeypatch.delenv("QTWEBENGINE_CHROMIUM_FLAGS", raising=False)

    assert configure_rendering() is False

    import os

    assert "QTWEBENGINE_CHROMIUM_FLAGS" not in os.environ


def test_user_supplied_flags_are_not_clobbered(monkeypatch):
    monkeypatch.delenv(GPU_ENV_VAR, raising=False)
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--my-flag")

    configure_rendering()

    import os

    assert os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] == "--my-flag"


def test_gpu_env_var_accepts_common_truthy_values(monkeypatch):
    for value in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv(GPU_ENV_VAR, value)
        assert gpu_requested() is True

    for value in ("0", "false", "no", "", "off"):
        monkeypatch.setenv(GPU_ENV_VAR, value)
        assert gpu_requested() is False


def test_hide_own_console_is_a_noop_off_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert hide_own_console() is False


def test_hide_own_console_never_raises():
    """Cosmetic tweak -- it must not be able to stop the app from starting."""
    assert hide_own_console() in (True, False)


def test_console_is_not_ours_when_running_under_a_shell():
    """The suite runs from a terminal, so the console belongs to the shell.

    Guards the failure that actually matters: hiding the user's own terminal.
    """
    assert console_is_ours() is False


def test_common_shells_are_recognised():
    assert {"cmd.exe", "powershell.exe", "pwsh.exe", "bash.exe"} <= SHELL_IMAGES
    assert all(name == name.lower() for name in SHELL_IMAGES)


def test_console_is_ours_is_false_off_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert console_is_ours() is False
