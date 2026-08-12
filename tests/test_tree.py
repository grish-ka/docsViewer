from docsviewer.tree import (
    ScanBudget,
    build_tree,
    default_document,
    extract_title,
    iter_markdown_files,
)


def write(path, text=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_readme_sorts_first(tmp_path):
    write(tmp_path / "zebra.md", "# Zebra")
    write(tmp_path / "README.md", "# Index")
    write(tmp_path / "alpha.md", "# Alpha")

    nodes = build_tree(tmp_path)

    assert [n.path.name for n in nodes] == ["README.md", "alpha.md", "zebra.md"]


def test_directories_sort_between_index_and_files(tmp_path):
    write(tmp_path / "README.md", "# Index")
    write(tmp_path / "zzz.md", "# Z")
    write(tmp_path / "guide" / "setup.md", "# Setup")

    nodes = build_tree(tmp_path)

    assert [n.path.name for n in nodes] == ["README.md", "guide", "zzz.md"]
    assert nodes[1].is_dir
    assert [c.path.name for c in nodes[1].children] == ["setup.md"]


def test_skips_noise_directories(tmp_path):
    write(tmp_path / "keep.md", "# Keep")
    write(tmp_path / "node_modules" / "pkg" / "readme.md", "# Nope")
    write(tmp_path / ".git" / "notes.md", "# Nope")
    write(tmp_path / "__pycache__" / "x.md", "# Nope")

    names = [n.path.name for n in build_tree(tmp_path)]

    assert names == ["keep.md"]


def test_prunes_folders_without_markdown(tmp_path):
    write(tmp_path / "keep.md", "# Keep")
    (tmp_path / "images").mkdir()
    write(tmp_path / "images" / "logo.png", "not markdown")

    names = [n.path.name for n in build_tree(tmp_path)]

    assert names == ["keep.md"]


def test_directory_titles_are_prettified(tmp_path):
    write(tmp_path / "api-reference" / "a.md", "# A")

    (node,) = build_tree(tmp_path)

    assert node.is_dir
    assert node.title == "Api Reference"


def test_dotted_directory_name_is_not_truncated(tmp_path):
    write(tmp_path / "v1.2" / "a.md", "# A")

    (node,) = build_tree(tmp_path)

    assert node.title == "V1.2"


def test_title_comes_from_h1(tmp_path):
    path = write(tmp_path / "getting-started.md", "Some intro\n\n# Real Title\n")
    assert extract_title(path) == "Real Title"


def test_title_falls_back_to_prettified_filename(tmp_path):
    path = write(tmp_path / "getting-started.md", "no heading here")
    assert extract_title(path) == "Getting Started"


def test_title_skips_front_matter(tmp_path):
    path = write(tmp_path / "a.md", "---\ntitle: meta\n---\n\n# Actual\n")
    assert extract_title(path) == "Actual"


def test_title_ignores_headings_inside_code_fences(tmp_path):
    path = write(tmp_path / "a.md", "```\n# Not a heading\n```\n\n# Yes\n")
    assert extract_title(path) == "Yes"


def test_setext_heading_is_recognised(tmp_path):
    path = write(tmp_path / "a.md", "Underlined Title\n================\n")
    assert extract_title(path) == "Underlined Title"


def test_default_document_prefers_readme(tmp_path):
    write(tmp_path / "aaa.md", "# A")
    write(tmp_path / "README.md", "# Index")

    assert default_document(tmp_path).name == "README.md"


def test_default_document_is_none_when_empty(tmp_path):
    assert default_document(tmp_path) is None


# -- scan budget: keeps a mis-aimed root from walking the filesystem ----


def test_file_ceiling_is_enforced(tmp_path):
    for i in range(20):
        write(tmp_path / f"doc{i:02}.md", "# Doc")

    budget = ScanBudget(max_files=5)
    nodes = build_tree(tmp_path, budget)

    assert len(nodes) == 5
    assert budget.truncated


def test_depth_ceiling_is_enforced(tmp_path):
    deep = tmp_path
    for i in range(6):
        deep = deep / f"level{i}"
    write(deep / "buried.md", "# Buried")
    write(tmp_path / "top.md", "# Top")

    budget = ScanBudget(max_depth=2)
    names = [n.path.name for n in build_tree(tmp_path, budget)]

    assert names == ["top.md"]  # the buried one is out of reach
    assert budget.truncated


def test_directory_ceiling_is_enforced(tmp_path):
    for i in range(30):
        write(tmp_path / f"dir{i:02}" / "a.md", "# A")

    budget = ScanBudget(max_dirs=5)
    build_tree(tmp_path, budget)

    assert budget.truncated
    assert budget.dirs_seen <= 5


def test_iter_markdown_files_respects_the_file_ceiling(tmp_path):
    for i in range(20):
        write(tmp_path / f"doc{i:02}.md", "# Doc")

    budget = ScanBudget(max_files=3)
    found = list(iter_markdown_files(tmp_path, budget))

    assert len(found) == 3
    assert budget.truncated


def test_a_normal_docs_tree_is_not_truncated(tmp_path):
    write(tmp_path / "README.md", "# Index")
    write(tmp_path / "guide" / "setup.md", "# Setup")
    write(tmp_path / "reference" / "api.md", "# API")

    budget = ScanBudget()
    build_tree(tmp_path, budget)

    assert not budget.truncated


def test_budget_is_shared_across_the_whole_traversal(tmp_path):
    """Each subfolder must draw from the same pool, not get a fresh one."""
    for d in range(4):
        for f in range(4):
            write(tmp_path / f"dir{d}" / f"doc{f}.md", "# Doc")

    budget = ScanBudget(max_files=6)
    nodes = build_tree(tmp_path, budget)

    total = sum(len(n.children) for n in nodes if n.is_dir)
    assert total == 6
    assert budget.truncated
