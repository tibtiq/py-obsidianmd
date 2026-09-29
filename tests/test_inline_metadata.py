from __future__ import annotations

import pytest

from pyomd.metadata.inline import InlineMetadata


class TestInlineMetadata:
    class Test_to_string:
        def test_returns_empty_when_no_metadata(self):
            inline_metadata = InlineMetadata("")

            result = inline_metadata.to_string()

            assert result == ""

        def test_renders_standard_format(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"author": ["Alice"], "tags": ["python", "code"]}

            result = inline_metadata.to_string(tml="standard")

            assert result == "author:: Alice\ntags:: python, code"

        def test_renders_callout_format(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"status": ["active"]}

            result = inline_metadata.to_string(tml="callout")

            assert result == "> [!info]- metadata\n> status :: active"

        def test_ignores_specified_key_string(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"author": ["Alice"], "draft": ["true"]}

            result = inline_metadata.to_string(ignore_k="draft")

            assert result == "author:: Alice"

        def test_ignores_specified_key_list(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {
                "author": ["Alice"],
                "draft": ["true"],
                "temp": ["yes"],
            }

            result = inline_metadata.to_string(ignore_k=["draft", "temp"])

            assert result == "author:: Alice"

        def test_renders_with_custom_callable_template(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"key": ["value"]}

            result = inline_metadata.to_string(tml=lambda d: "custom:: " + d["key"][0])

            assert result == "custom:: value"

    class Test_parse:
        def test_extracts_inline_metadata_successfully(self):
            content = "Some note content\nauthor:: Alice\ntags:: python, testing\nMore content"
            inline_metadata = InlineMetadata("")

            parsed_metadata = inline_metadata.parse(content)

            assert parsed_metadata["author"] == ["Alice"]
            assert parsed_metadata["tags"] == ["python", "testing"]

        def test_ignores_enclosed_dataview_fields(self):
            content = "Check out (author:: Bob) and [tags:: embedded]"
            inline_metadata = InlineMetadata("")

            parsed_metadata = inline_metadata.parse(content)

            assert len(parsed_metadata) == 0

    class Test_erase:
        def test_removes_inline_metadata_lines(self):
            content = "Header\nauthor:: Alice\nBody text\ntags:: python"
            inline_metadata = InlineMetadata("")

            erased_content = inline_metadata.erase(content)

            assert erased_content == "Header\nBody text"

        def test_removes_callout_artefacts(self):
            content = "Body text\n> [!info]- metadata\n> author :: Alice"
            inline_metadata = InlineMetadata("")

            erased_content = inline_metadata.erase(content)

            assert "Body text" in erased_content
            assert "metadata" not in erased_content

    class Test_update_content:
        def test_appends_metadata_at_bottom_by_default(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"status": ["complete"]}
            content = "Note body text."

            updated_content = inline_metadata._update_content(
                content, position="bottom", inplace=False
            )

            assert updated_content.startswith("Note body text.")
            assert "status:: complete" in updated_content

        def test_prepends_metadata_at_top(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"status": ["draft"]}
            content = "Note body text."

            updated_content = inline_metadata._update_content(
                content, position="top", inplace=False
            )

            assert updated_content.startswith("status:: draft")
            assert "Note body text." in updated_content

        def test_raises_not_implemented_error_for_invalid_position(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"status": ["draft"]}
            content = "Note body text."

            with pytest.raises(NotImplementedError):
                inline_metadata._update_content(
                    content, position="middle", inplace=False
                )

        def test_updates_content_inplace(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"author": ["Bob"]}
            content = "author:: Alice\nSome text."

            updated_content = inline_metadata._update_content(
                content, position="bottom", inplace=True
            )

            assert "author:: Bob" in updated_content
            assert "author:: Alice" not in updated_content
            assert "Some text." in updated_content

        def test_removes_deleted_inplace_fields_and_redundant_keys(self):
            inline_metadata = InlineMetadata("")
            inline_metadata.metadata = {"author": ["Bob"]}
            content = (
                "author:: Alice\nauthor:: Charlie\nremoved_field:: value\nSome text."
            )

            updated_content = inline_metadata._update_content(
                content, position="bottom", inplace=True
            )

            assert "author:: Bob" in updated_content
            assert "author:: Alice" not in updated_content
            assert "author:: Charlie" not in updated_content
            assert "removed_field:: value" not in updated_content
            assert "Some text." in updated_content

    class TestGetSepNewlines:
        def test_get_sep_newlines_top(self):
            assert InlineMetadata._get_sep_newlines("abc", position="top") == "\n\n"
            assert InlineMetadata._get_sep_newlines("\nabc", position="top") == "\n"
            assert InlineMetadata._get_sep_newlines("\n\nabc", position="top") == ""
            assert InlineMetadata._get_sep_newlines("", position="top") == ""

        def test_get_sep_newlines_bottom(self):
            assert InlineMetadata._get_sep_newlines("abc", position="bottom") == "\n\n"
            assert InlineMetadata._get_sep_newlines("abc\n", position="bottom") == "\n"
            assert InlineMetadata._get_sep_newlines("abc\n\n", position="bottom") == ""
            assert InlineMetadata._get_sep_newlines("", position="bottom") == ""

        def test_get_sep_newlines_unknown_position(self):
            assert InlineMetadata._get_sep_newlines("abc", position="unknown") == ""

    def test_removes_deleted_inplace_fields_and_redundant_keys(self):
        inline_metadata = InlineMetadata("")
        inline_metadata.metadata = {"author": ["Bob"]}
        content = "author:: Alice\nauthor:: Charlie\nremoved_field:: value\nSome text."

        updated_content = inline_metadata._update_content(
            content, position="bottom", inplace=True
        )

        assert "author:: Bob" in updated_content
        assert "author:: Alice" not in updated_content
        assert "author:: Charlie" not in updated_content
        assert "removed_field:: value" not in updated_content
        assert "Some text." in updated_content

    def test_ignores_enclosed_fields_during_inplace_update(self):
        inline_metadata = InlineMetadata("")
        inline_metadata.metadata = {}
        content = "Check out (removed_field:: value) in text."

        updated_content = inline_metadata._update_content(
            content, position="bottom", inplace=True
        )

        assert "(removed_field:: value)" in updated_content

    class TestTemplates:
        def test_tml_standard_with_none(self):
            assert InlineMetadata._tml_standard(None) == ""

        def test_tml_callout_with_none(self):
            assert InlineMetadata._tml_callout(None) == "> [!info]- metadata"
