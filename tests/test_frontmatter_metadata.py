from pathlib import Path

import pytest

from pyomd.exceptions import InvalidFrontmatterError
from pyomd.metadata import Frontmatter


class TestFrontmatter:
    class Test_to_string:
        def test_empty(self):
            meta = Frontmatter("")

            assert meta.to_string() == ""

        def test_simple(self):
            meta = Frontmatter("")
            meta.metadata = {"title": ["My Note"], "tags": ["python", "testing"]}

            result = meta.to_string()

            assert result.startswith("---\n")
            assert result.endswith("---\n")
            assert "title: My Note\n" in result
            assert "tags: [ python, testing ]\n" in result

        def test_none_values(self):
            meta = Frontmatter("")
            meta.metadata = {"title": ["Note"], "empty": None}

            result = meta.to_string()

            assert "empty" not in result
            assert "title: Note\n" in result

    def test_update_content(self):
        meta = Frontmatter("")
        meta.metadata = {"title": ["New Title"]}
        content = "---\ntitle: Old Title\n---\nHello world!"
        updated = meta._update_content(content)
        assert "title: New Title" in updated
        assert "Hello world!" in updated

    class Test_parse:
        def test_valid_frontmatter(self):
            content = "---\ntitle: Test Note\ntags:\n  - python\n  - omd\nyear: 2023\n---\nBody content"
            meta = Frontmatter("")

            parsed = meta.parse(content)

            assert parsed["title"] == ["Test Note"]
            assert parsed["tags"] == ["python", "omd"]
            assert parsed["year"] == ["2023"]

        def test_invalid_frontmatter(self):
            content = "---\ntitle: [unclosed list\n---\nBody"
            meta = Frontmatter("")

            with pytest.raises(InvalidFrontmatterError):
                meta.parse(content)

        def test_none_value(self):
            content = "---\ntitle: Test\nempty_field:\n---\nBody content"
            meta = Frontmatter("")
            parsed = meta.parse(content)

            assert parsed["title"] == ["Test"]
            assert parsed["empty_field"] == []

    def test_erase_frontmatter(self):
        content = "---\ntitle: Note\n---\nThis is the content."
        meta = Frontmatter("")

        erased = meta.erase(content)

        assert erased.strip() == "This is the content."

    class Test_is_frontmatter_valid:
        def test_nonexistent_file(self, tmp_path: Path):
            fake_path = tmp_path / "does_not_exist.md"

            assert Frontmatter.is_frontmatter_valid(fake_path) is False

        def test_valid_success(self, tmp_path: Path):
            valid_file = tmp_path / "valid.md"
            valid_file.write_text("---\ntitle: Valid\n---\nContent")

            assert Frontmatter.is_frontmatter_valid(valid_file) is True
