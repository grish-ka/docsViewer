from docsviewer.renderer import render_body, render_document, render_error, stylesheet


def test_fenced_code_is_highlighted():
    html = render_body("```python\nimport os\n```")
    assert "<pre>" in html
    assert 'class="k"' in html or 'class="kn"' in html  # Pygments token spans


def test_unknown_language_degrades_to_plain_text():
    html = render_body("```notalanguage\na < b\n```")
    assert "a &lt; b" in html


def test_tables_render():
    html = render_body("| a | b |\n| --- | --- |\n| 1 | 2 |")
    assert "<table>" in html
    assert "<th>a</th>" in html


def test_task_lists_render():
    html = render_body("- [x] done\n- [ ] todo")
    assert 'type="checkbox"' in html


def test_headings_get_anchors():
    html = render_body("## Getting Started")
    assert 'id="getting-started"' in html


def test_strikethrough_and_autolink():
    html = render_body("~~gone~~ and https://example.com")
    assert "<s>gone</s>" in html
    assert 'href="https://example.com"' in html


def test_front_matter_is_not_rendered():
    html = render_body("---\ntitle: Hi\n---\n\n# Real Heading")
    assert "title: Hi" not in html
    assert "Real Heading" in html


def test_render_document_inlines_css_and_title():
    html = render_document("# Hi", theme="dark", title="notes.md")
    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    assert "--dv-bg" in html  # theme tokens are inlined
    assert "<title>notes.md</title>" in html


def test_themes_differ():
    assert stylesheet("light") != stylesheet("dark")


def test_unknown_theme_falls_back_to_light():
    assert stylesheet("chartreuse") == stylesheet("light")


def test_render_error_escapes_input():
    html = render_error("<script>boom</script>")
    assert "<script>boom</script>" not in html
    assert "&lt;script&gt;" in html
