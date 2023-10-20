import json

import pytest
from src.updates import update_readme

# Test data
test_plugins_dir = "tests/plugins"
test_readme_file = "tests/README.md"

test_manifests = [
    {
        "name": "Plugin 1",
        "version": "1.0.0",
        "author": "Author 1",
        "authorUrl": "http://example.com/author1",
    },
    {
        "name": "Plugin 2",
        "version": "2.0.0",
        "author": "Author 2",
        "authorUrl": "http://example.com/author2",
    },
    {
        "name": "Plugin 3",
        "version": "3.0.0",
        "author": "Author 3",
        "authorUrl": "http://example.com/author3",
    },
]


@pytest.fixture
def setup_test_files(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    for i, manifest in enumerate(test_manifests):
        plugin_dir = plugins_dir / f"plugin{i+1}"
        plugin_dir.mkdir()
        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

    readme_file = tmp_path / "README.md"
    readme_file.touch()

    return plugins_dir, readme_file


def test_update_readme(setup_test_files):
    plugins_dir, readme_file = setup_test_files

    update_readme(readme_file, plugins_dir)

    with open(readme_file, "r") as f:
        content = f.read()

    # Check that the Markdown table was written to the file
    assert "Integrated Plugins" in content
    assert "| Plugin Name | Version | Author |" in content
    assert "| Plugin 1 | 1.0.0 | [Author 1](" in content
    assert "| Plugin 2 | 2.0.0 | [Author 2](" in content
    assert "| Plugin 3 | 3.0.0 | [Author 3](" in content
