import pytest

from docsviewer.search import Index


@pytest.fixture
def docs(tmp_path):
    (tmp_path / "reference").mkdir()
    (tmp_path / "README.md").write_text("# Index\n\nThe quick brown fox.\n", encoding="utf-8")
    (tmp_path / "reference" / "api.md").write_text(
        "# API\n\nCall the FOX endpoint.\nAnother line.\n", encoding="utf-8"
    )
    (tmp_path / "notes.txt").write_text("fox in a non-markdown file", encoding="utf-8")
    return tmp_path


def test_indexes_markdown_only(docs):
    index = Index.build(docs)
    assert index.count() == 2


def test_finds_term_across_files_case_insensitively(docs):
    hits = Index.build(docs).query("fox")

    assert len(hits) == 2
    assert {hit.path.name for hit in hits} == {"README.md", "api.md"}


def test_hit_records_line_number_and_title(docs):
    (hit,) = Index.build(docs).query("endpoint")

    assert hit.path.name == "api.md"
    assert hit.title == "API"
    assert hit.line_no == 3
    assert "endpoint" in hit.line


def test_empty_query_returns_nothing(docs):
    index = Index.build(docs)
    assert index.query("") == []
    assert index.query("   ") == []


def test_limit_is_respected(tmp_path):
    (tmp_path / "big.md").write_text("needle\n" * 500, encoding="utf-8")

    hits = Index.build(tmp_path).query("needle", limit=10)

    assert len(hits) == 10


def test_refresh_picks_up_new_files(docs):
    index = Index.build(docs)
    (docs / "new.md").write_text("# New\n\nfox again\n", encoding="utf-8")

    assert len(index.query("fox")) == 2
    index.refresh()
    assert len(index.query("fox")) == 3


def test_snippet_trims_long_lines(tmp_path):
    long_line = "x" * 300 + " needle " + "y" * 300
    (tmp_path / "a.md").write_text(long_line, encoding="utf-8")

    (hit,) = Index.build(tmp_path).query("needle")
    snippet = hit.snippet(radius=20, term_len=6)

    assert "needle" in snippet
    assert len(snippet) < 100
    assert snippet.startswith("…") and snippet.endswith("…")
