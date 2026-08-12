import pytest

from docsviewer import scaffold
from docsviewer.scaffold import (
    format_result,
    init_docs,
    iter_template_files,
    template_root,
)


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "myproject"
    path.mkdir()
    return path


# -- the bundled source -------------------------------------------------


def test_template_root_is_a_real_docs_folder():
    root = template_root()

    assert root.is_dir()
    assert (root / "README.md").is_file()


def test_bundled_docs_are_discovered():
    names = {path.name for path in iter_template_files()}

    assert {"README.md", "changelog.md", "commands.md"} <= names


def test_iter_template_files_sorts_shallowest_first(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "deep.md").write_text("x", encoding="utf-8")
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "zebra.md").write_text("x", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("x", encoding="utf-8")

    files = [str(p) for p in iter_template_files(tmp_path)]

    assert files[0] == "README.md"
    assert files[-1].endswith("deep.md")
    assert not any("ignored" in f for f in files)


# -- init ---------------------------------------------------------------


def test_creates_every_bundled_document(project):
    result = init_docs(project)

    expected = iter_template_files()
    assert len(result.created) == len(expected)
    assert not result.skipped
    for relative in expected:
        assert (project / "docs" / relative).is_file()


def test_creates_readme_and_changelog(project):
    init_docs(project)

    assert (project / "docs" / "README.md").is_file()
    assert (project / "docs" / "changelog.md").is_file()


def test_nested_structure_is_preserved(project, monkeypatch, tmp_path):
    source = tmp_path / "source"
    (source / "reference").mkdir(parents=True)
    (source / "README.md").write_text("# Index", encoding="utf-8")
    (source / "reference" / "api.md").write_text("# API", encoding="utf-8")
    monkeypatch.setattr(scaffold, "template_root", lambda: source)

    init_docs(project)

    assert (project / "docs" / "reference" / "api.md").read_text(encoding="utf-8") == "# API"


def test_placeholders_are_substituted(project, monkeypatch, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("# {{project_name}}\n\n{{date}}\n", encoding="utf-8")
    monkeypatch.setattr(scaffold, "template_root", lambda: source)

    init_docs(project, title="Fancy Name")

    text = (project / "docs" / "README.md").read_text(encoding="utf-8")
    assert "Fancy Name" in text
    assert "{{project_name}}" not in text
    assert "{{date}}" not in text


def test_rerun_skips_instead_of_clobbering(project):
    init_docs(project)
    readme = project / "docs" / "README.md"
    readme.write_text("MY OWN NOTES", encoding="utf-8")

    result = init_docs(project)

    assert readme.read_text(encoding="utf-8") == "MY OWN NOTES"
    assert not result.created
    assert len(result.skipped) == len(iter_template_files())


def test_force_overwrites(project):
    init_docs(project)
    readme = project / "docs" / "README.md"
    readme.write_text("MY OWN NOTES", encoding="utf-8")

    result = init_docs(project, force=True)

    assert readme.read_text(encoding="utf-8") != "MY OWN NOTES"
    assert len(result.created) == len(iter_template_files())


def test_format_result_mentions_skips(project):
    init_docs(project)

    summary = format_result(init_docs(project))

    assert "skipped" in summary
    assert "--force" in summary
