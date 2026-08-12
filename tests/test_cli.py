import pytest

from docsviewer.cli import main, resolve_target


def write(path, text="# Doc"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_explicit_folder(tmp_path):
    write(tmp_path / "a.md")
    root, initial = resolve_target(str(tmp_path))
    assert root == tmp_path.resolve()
    assert initial is None


def test_explicit_file_opens_its_folder(tmp_path):
    path = write(tmp_path / "guide" / "a.md")
    root, initial = resolve_target(str(path))
    assert root == path.parent.resolve()
    assert initial == path.resolve()


def test_project_root_prefers_nested_docs_folder(tmp_path):
    write(tmp_path / "docs" / "README.md")
    root, _ = resolve_target(str(tmp_path))
    assert root == (tmp_path / "docs").resolve()


def test_docs_folder_wins_over_root_markdown(tmp_path):
    """The common case: a project root has a README, but docs/ is what you want."""
    write(tmp_path / "README.md")
    write(tmp_path / "docs" / "other.md")

    root, _ = resolve_target(str(tmp_path))

    assert root == (tmp_path / "docs").resolve()


def test_here_flag_overrides_the_docs_preference(tmp_path):
    write(tmp_path / "README.md")
    write(tmp_path / "docs" / "other.md")

    root, _ = resolve_target(str(tmp_path), here=True)

    assert root == tmp_path.resolve()


def test_here_flag_applies_to_the_cwd_too(tmp_path, monkeypatch):
    write(tmp_path / "README.md")
    write(tmp_path / "docs" / "other.md")
    monkeypatch.chdir(tmp_path)

    root, _ = resolve_target(None, here=True)

    assert root == tmp_path.resolve()


def test_empty_docs_folder_is_ignored(tmp_path):
    """A docs/ with no Markdown shouldn't hijack a folder that has some."""
    write(tmp_path / "README.md")
    (tmp_path / "docs").mkdir()

    root, _ = resolve_target(str(tmp_path))

    assert root == tmp_path.resolve()


def test_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_target(str(tmp_path / "nope"))


def test_non_markdown_file_raises(tmp_path):
    path = write(tmp_path / "notes.txt", "hi")
    with pytest.raises(ValueError):
        resolve_target(str(path))


def test_cwd_docs_folder_is_found(tmp_path, monkeypatch):
    write(tmp_path / "docs" / "README.md")
    monkeypatch.chdir(tmp_path)
    root, _ = resolve_target(None)
    assert root == (tmp_path / "docs").resolve()


def test_no_markdown_anywhere_returns_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_target(None) == (None, None)


def test_init_subcommand_scaffolds(tmp_path, capsys):
    exit_code = main(["init", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "docs" / "README.md").is_file()
    assert "created" in capsys.readouterr().out


def test_init_force_flag(tmp_path):
    main(["init", str(tmp_path)])
    (tmp_path / "docs" / "README.md").write_text("mine", encoding="utf-8")

    main(["init", str(tmp_path), "--force"])

    assert (tmp_path / "docs" / "README.md").read_text(encoding="utf-8") != "mine"


def test_init_title_flag_is_accepted(tmp_path):
    """--title only fills {{project_name}} placeholders.

    The bundled docs contain none, so it is a no-op there; the substitution
    itself is covered in test_scaffold.py against a synthetic source.
    """
    exit_code = main(["init", str(tmp_path), "--title", "Zebra Project"])

    assert exit_code == 0
    assert (tmp_path / "docs" / "README.md").is_file()


def test_init_rejects_missing_directory(tmp_path):
    with pytest.raises(SystemExit):
        main(["init", str(tmp_path / "nope")])


def test_version_flag_exits_cleanly():
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
