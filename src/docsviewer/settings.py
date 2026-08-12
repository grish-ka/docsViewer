"""Persisted preferences, backed by QSettings (registry on Windows)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings

from .renderer import THEMES

ORGANISATION = "docsviewer"
APPLICATION = "docsviewer"


class Settings:
    """Thin, typed wrapper over QSettings."""

    def __init__(self) -> None:
        self._store = QSettings(ORGANISATION, APPLICATION)

    # -- theme ----------------------------------------------------------

    @property
    def theme(self) -> str:
        value = str(self._store.value("theme", "light"))
        return value if value in THEMES else "light"

    @theme.setter
    def theme(self, value: str) -> None:
        if value in THEMES:
            self._store.setValue("theme", value)
            self._store.sync()

    def toggled_theme(self) -> str:
        return "dark" if self.theme == "light" else "light"

    # -- window state ---------------------------------------------------

    @property
    def geometry(self) -> QByteArray | None:
        value = self._store.value("window/geometry")
        return value if isinstance(value, QByteArray) and not value.isEmpty() else None

    @geometry.setter
    def geometry(self, value: QByteArray) -> None:
        self._store.setValue("window/geometry", value)

    @property
    def splitter_state(self) -> QByteArray | None:
        value = self._store.value("window/splitter")
        return value if isinstance(value, QByteArray) and not value.isEmpty() else None

    @splitter_state.setter
    def splitter_state(self, value: QByteArray) -> None:
        self._store.setValue("window/splitter", value)

    # -- last opened folder ---------------------------------------------

    @property
    def last_folder(self) -> Path | None:
        value = self._store.value("last_folder")
        if not value:
            return None
        path = Path(str(value))
        return path if path.is_dir() else None

    @last_folder.setter
    def last_folder(self, value: Path) -> None:
        self._store.setValue("last_folder", str(value))

    def sync(self) -> None:
        self._store.sync()
