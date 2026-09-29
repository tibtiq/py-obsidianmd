from __future__ import annotations

import pytest
from icecream import ic

ic.configureOutput(includeContext=True)
from pyomd.config import CONFIG
from pyomd.exceptions import ArgTypeError
from pyomd.metadata import (
    Frontmatter,
    InlineMetadata,
    MetadataType,
    NoteMetadata,
    NoteMetadataBatch,
    return_metaclass,
)
from pyomd.misc import Order
from pyomd.note import Note


class TestNoteMetadata:
    class TestParseArgMetaType:
        def test_returns_all_when_none(self):
            result = NoteMetadata._parse_arg_meta_type(None)
            assert result == MetadataType.ALL

        def test_returns_same_when_valid_metadata_type(self):
            result = NoteMetadata._parse_arg_meta_type(MetadataType.FRONTMATTER)
            assert result == MetadataType.FRONTMATTER

        def test_raises_arg_type_error_when_invalid(self):
            with pytest.raises(ArgTypeError):
                NoteMetadata._parse_arg_meta_type("invalid_type")

    class TestGetDefaultMetadata:
        def test_returns_configured_default_field_meta(self):
            note_metadata = NoteMetadata("content")
            result = note_metadata.get_default_metadata(None)
            assert result is not None

        def test_returns_field_specific_default_meta(self):
            note_metadata = NoteMetadata("content")
            CONFIG.cfg["fields"]["test_field"] = {"default_meta": "frontmatter"}

            result = note_metadata.get_default_metadata("test_field")

            assert result == MetadataType.FRONTMATTER

    class TestGet:
        def test_returns_frontmatter_when_inline_is_none(self):
            content = "---\ntitle: Front\n---"
            note_metadata = NoteMetadata(content)

            result = note_metadata.get("title", None)

            assert result == ["Front"]

        def test_returns_inline_when_frontmatter_is_none(self):
            content = "title:: Inline"
            note_metadata = NoteMetadata(content)

            result = note_metadata.get("title", None)

            assert result == ["Inline"]

        def test_returns_none_when_both_are_none(self):
            content = "No metadata"
            note_metadata = NoteMetadata(content)

            result = note_metadata.get("title", None)

            assert result is None

        def test_uses_default_meta_type(self):
            content = "---\ntitle:: Front\n---"
            note_metadata = NoteMetadata(content)

            result = note_metadata.get("title", MetadataType.DEFAULT)

            assert result == ["Front"]

        def test_returns_frontmatter_explicitly_when_both_exist(self):
            content = "---\ntitle: Front Note\n---\ntitle:: Inline Note"
            note_metadata = NoteMetadata(content)

            result = note_metadata.get("title", MetadataType.FRONTMATTER)

            assert result == ["Front Note"]

        def test_returns_combined_frontmatter_and_inline_values(self):
            content = "---\ntags: [python]\n---\ntags:: testing"
            note_metadata = NoteMetadata(content)

            result = note_metadata.get("tags", None)

            assert result == ["python", "testing"]

    class TestHas:
        def test_has_inline_specific(self):
            content = "tags:: python"
            note_metadata = NoteMetadata(content)

            assert note_metadata.has("tags", "python", MetadataType.INLINE) is True

        def test_has_returns_true_when_present_in_either_metadata_type(self):
            content = "---\ntitle: Front Note\n---\nauthor:: Alice"
            note_metadata = NoteMetadata(content)

            assert note_metadata.has("title", "Front Note", None) is True
            assert note_metadata.has("author", "Alice", None) is True
            assert note_metadata.has("missing", "val", None) is False

        def test_has_raises_not_implemented_error_for_invalid_meta_type(self):
            content = "author:: Alice"
            note_metadata = NoteMetadata(content)

            with pytest.raises(NotImplementedError):
                note_metadata.has("author", "Alice", MetadataType.ALL)

        def test_has_frontmatter_specific(self):
            content = "---\ntags: python\n---\ntags:: other"
            note_metadata = NoteMetadata(content)

            assert note_metadata.has("tags", "python", MetadataType.FRONTMATTER) is True
            assert note_metadata.has("tags", "other", MetadataType.FRONTMATTER) is False

    class TestRemove:
        def test_remove_frontmatter_only(self):
            content = "---\nkey: val\n---\nkey:: val"
            note_metadata = NoteMetadata(content)

            note_metadata.remove("key", meta_type=MetadataType.FRONTMATTER)

            assert note_metadata.frontmatter.get("key") is None
            assert note_metadata.inline.get("key") == ["val"]

        def test_remove_inline_only(self):
            content = "---\nkey: val\n---\nkey:: val"
            note_metadata = NoteMetadata(content)

            note_metadata.remove("key", meta_type=MetadataType.INLINE)

            assert note_metadata.frontmatter.get("key") == ["val"]
            assert note_metadata.inline.get("key") is None

        def test_removes_from_both_when_meta_type_is_none(self):
            content = "---\nkey: val\n---\nkey:: val"
            note_metadata = NoteMetadata(content)

            note_metadata.remove("key", l=None, meta_type=None)

            assert note_metadata.frontmatter.get("key") is None
            assert note_metadata.inline.get("key") is None

    class TestRemoveEmpty:
        def test_remove_empty_frontmatter_and_inline(self):
            content = "---\nempty_fm:\n---\nempty_il::"

            note_metadata = NoteMetadata(content)

            note_metadata.remove_empty(MetadataType.FRONTMATTER)
            note_metadata.remove_empty(MetadataType.INLINE)

            assert "empty_fm" not in note_metadata.frontmatter.metadata

        def test_removes_empty_from_both_frontmatter_and_inline(self):
            content = "---\nempty_fm:\n---\nempty_il::"
            note_metadata = NoteMetadata(content)

            note_metadata.remove_empty(MetadataType.ALL)

            assert "empty_fm" not in note_metadata.frontmatter.metadata
            assert "empty_il" not in note_metadata.inline.metadata

    class TestMove:
        def test_move_all_default_fields(self):
            CONFIG.cfg["fields"]["migrated"] = {"default_meta": "frontmatter"}
            content = "migrated:: value"
            note_metadata = NoteMetadata(content)

            note_metadata.move(k=None, fr=None, to=None)

            assert note_metadata.frontmatter.get("migrated") == ["value"]

        def test_move_specific_key_list(self):
            content = "author:: Alice"
            note_metadata = NoteMetadata(content)

            note_metadata.move(
                k=["author"], fr=MetadataType.INLINE, to=MetadataType.FRONTMATTER
            )

        def test_moves_field_between_inline_and_frontmatter(self):
            content = "author:: Alice"
            note_metadata = NoteMetadata(content)

            note_metadata.move(
                k="author", fr=MetadataType.INLINE, to=MetadataType.FRONTMATTER
            )

            assert "author" not in note_metadata.inline.metadata
            assert note_metadata.frontmatter.metadata["author"] == ["Alice"]

        def test_moves_default_fields_when_no_args(self):
            content = "author:: Alice"
            note_metadata = NoteMetadata(content)

            note_metadata.move(k=None, fr=None, to=None)

        def test_moves_all_fields_when_key_is_none(self):
            content = "author:: Alice\nyear:: 2023"
            note_metadata = NoteMetadata(content)

            note_metadata.move(
                k=None, fr=MetadataType.INLINE, to=MetadataType.FRONTMATTER
            )

            assert len(note_metadata.inline.metadata) == 0
            assert note_metadata.frontmatter.get("author") == ["Alice"]
            assert note_metadata.frontmatter.get("year") == ["2023"]

    class TestAdd:
        def test_adds_to_frontmatter(self):
            note_metadata = NoteMetadata("")

            note_metadata.add("key", "value", MetadataType.FRONTMATTER)

            assert note_metadata.frontmatter.get("key") == ["value"]

        def test_adds_to_inline(self):
            note_metadata = NoteMetadata("")

            note_metadata.add("key", "value", MetadataType.INLINE)

            assert note_metadata.inline.get("key") == ["value"]

        def test_adds_using_default_meta_type_configuration(self):
            CONFIG.cfg["fields"]["category"] = {"default_meta": "inline"}
            note_metadata = NoteMetadata("")

            note_metadata.add("category", "tech", MetadataType.DEFAULT)

            assert note_metadata.inline.get("category") == ["tech"]

    class TestRemoveDuplicateValues:
        def test_removes_duplicates_all_types(self):
            content = "---\ntags: [a, a]\n---\ntags:: b, b"
            note_metadata = NoteMetadata(content)

            note_metadata.remove_duplicate_values(k=None, meta_type=MetadataType.ALL)

            assert note_metadata.frontmatter.metadata["tags"] == ["a"]
            assert note_metadata.inline.metadata["tags"] == ["b"]

        def test_raises_arg_type_error_on_invalid_meta_type(self):
            note_metadata = NoteMetadata("")

            with pytest.raises(ArgTypeError):
                note_metadata.remove_duplicate_values(k=None, meta_type="invalid")

        def test_removes_duplicates_inline_only(self):
            content = "---\ntags: [a, a, b]\n---\ntags:: c, c, d"
            note_metadata = NoteMetadata(content)

            note_metadata.remove_duplicate_values(
                k="tags", meta_type=MetadataType.INLINE
            )

            assert note_metadata.frontmatter.metadata["tags"] == ["a", "a", "b"]
            assert note_metadata.inline.metadata["tags"] == ["c", "d"]

        def test_removes_duplicates_frontmatter_only(self):
            content = "---\ntags: [a, a, b]\n---\ntags:: c, c, d"
            note_metadata = NoteMetadata(content)

            note_metadata.remove_duplicate_values(
                k="tags", meta_type=MetadataType.FRONTMATTER
            )

            assert note_metadata.frontmatter.metadata["tags"] == ["a", "b"]
            assert note_metadata.inline.metadata["tags"] == ["c", "c", "d"]

        def test_raises_value_error_for_unsupported_meta_type_branch(self, monkeypatch):
            content = ""
            note_metadata = NoteMetadata(content)
            monkeypatch.setattr(
                NoteMetadata, "_parse_arg_meta_type", lambda self, mt: "UNSUPPORTED"
            )

            with pytest.raises(ValueError):
                note_metadata.remove_duplicate_values(k=None, meta_type=None)

    class TestOrderValues:
        def test_orders_values_frontmatter(self):
            content = "---\ntags: [b, a]\n---"
            note_metadata = NoteMetadata(content)

            note_metadata.order_values(
                k="tags", how=Order.ASC, meta_type=MetadataType.FRONTMATTER
            )

            assert note_metadata.frontmatter.metadata["tags"] == ["a", "b"]

        def test_raises_arg_type_error_on_invalid_meta_type(self):
            note_metadata = NoteMetadata("")

            with pytest.raises(ArgTypeError):
                note_metadata.order_values(meta_type="invalid")

        # todo this test looks wrong
        def test_orders_values_inline(self):
            content = "tags:: [b, a]"
            note_metadata = NoteMetadata(content)

            note_metadata.order_values(
                k="tags", how=Order.ASC, meta_type=MetadataType.INLINE
            )

            assert note_metadata.inline.metadata["tags"] == ["[b", "a]"]

        # todo this test is wrong
        def test_orders_values_all(self):
            content = "---\ntags:: [b, a]\n---\nother:: [d, c]"
            note_metadata = NoteMetadata(content)

            note_metadata.order_values(
                k=None, how=Order.ASC, meta_type=MetadataType.ALL
            )

            ic(note_metadata.frontmatter.metadata)
            assert note_metadata.frontmatter.metadata["tags:"] == ["a", "b"]
            assert note_metadata.inline.metadata["other"] == ["[d", "c]"]

        def test_raises_value_error_for_unsupported_meta_type_branch(self, monkeypatch):
            note_metadata = NoteMetadata("")
            monkeypatch.setattr(
                NoteMetadata, "_parse_arg_meta_type", lambda self, mt: "UNSUPPORTED"
            )

            with pytest.raises(ValueError):
                note_metadata.order_values(k=None, how=Order.ASC, meta_type=None)

    class TestOrderKeys:
        def test_orders_keys_all_types(self):
            content = "---\nb: 1\na: 2\n---"
            note_metadata = NoteMetadata(content)

            note_metadata.order_keys(how=Order.ASC, meta_type=MetadataType.ALL)

            assert list(note_metadata.frontmatter.metadata.keys()) == ["a", "b"]

        def test_orders_keys_inline_only(self):
            content = "---\nb: 1\na: 2\n---\ny:: 1\nx:: 2"
            note_metadata = NoteMetadata(content)

            note_metadata.order_keys(how=Order.ASC, meta_type=MetadataType.INLINE)

            assert list(note_metadata.frontmatter.metadata.keys()) == ["b", "a"]
            assert list(note_metadata.inline.metadata.keys()) == ["x", "y"]

        def test_raises_value_error_for_unsupported_meta_type_branch(self, monkeypatch):
            note_metadata = NoteMetadata("")
            monkeypatch.setattr(
                NoteMetadata, "_parse_arg_meta_type", lambda self, mt: "UNSUPPORTED"
            )

            with pytest.raises(ValueError):
                note_metadata.order_keys(how=Order.ASC, meta_type=None)

        def test_orders_keys_frontmatter_only(self):
            content = "---\nb: 1\na: 2\n---\ny:: 1\nx:: 2"
            note_metadata = NoteMetadata(content)

            note_metadata.order_keys(how=Order.ASC, meta_type=MetadataType.FRONTMATTER)

            assert list(note_metadata.frontmatter.metadata.keys()) == ["a", "b"]
            assert list(note_metadata.inline.metadata.keys()) == ["y", "x"]

        def test_raises_arg_type_error_on_invalid_meta_type(self):
            note_metadata = NoteMetadata("")

            with pytest.raises(ArgTypeError):
                note_metadata.order_keys(meta_type="invalid")

    class TestOrder:
        def test_orders_keys_and_values(self):
            content = "---\nb: [2, 1]\na: [4, 3]\n---"
            note_metadata = NoteMetadata(content)

            note_metadata.order(
                k=None,
                o_keys=Order.ASC,
                o_values=Order.ASC,
                meta_type=MetadataType.FRONTMATTER,
            )

            assert list(note_metadata.frontmatter.metadata.keys()) == ["a", "b"]
            assert note_metadata.frontmatter.metadata["a"] == ["3", "4"]

        def test_raises_arg_type_error_on_invalid_meta_type(self):
            note_metadata = NoteMetadata("")

            with pytest.raises(ArgTypeError):
                note_metadata.order(meta_type="invalid")

        def test_orders_inline_only(self):
            content = "---\nb: [2, 1]\na: [4, 3]\n---\ny:: 2\nx:: 4"
            note_metadata = NoteMetadata(content)

            note_metadata.order(
                k=None,
                o_keys=Order.ASC,
                o_values=Order.ASC,
                meta_type=MetadataType.INLINE,
            )

            assert list(note_metadata.frontmatter.metadata.keys()) == ["b", "a"]
            assert list(note_metadata.inline.metadata.keys()) == ["x", "y"]

        def test_raises_value_error_for_unsupported_meta_type_branch(self, monkeypatch):
            note_metadata = NoteMetadata("")
            monkeypatch.setattr(
                NoteMetadata, "_parse_arg_meta_type", lambda self, mt: "UNSUPPORTED"
            )

            with pytest.raises(ValueError):
                note_metadata.order(
                    k=None, o_keys=Order.ASC, o_values=Order.ASC, meta_type=None
                )


class TestNoteMetadataBatch:
    class TestBatchOperations:
        def test_batch_add_and_remove(self, tmp_path, make_markdown_file):
            file1 = make_markdown_file("content 1", filename="n1.md")
            file2 = make_markdown_file("content 2", filename="n2.md")
            notes = [Note(file1), Note(file2)]
            batch = NoteMetadataBatch(notes)

            batch.add("status", "active", MetadataType.FRONTMATTER)
            for note in notes:
                assert note.metadata.frontmatter.metadata["status"] == ["active"]

            batch.remove("status", None, MetadataType.FRONTMATTER)
            for note in notes:
                assert "status" not in note.metadata.frontmatter.metadata

        def test_batch_move_and_order(self, tmp_path, make_markdown_file):
            file1 = make_markdown_file("status:: active", filename="n1.md")
            notes = [Note(file1)]
            batch = NoteMetadataBatch(notes)

            batch.move(k="status", fr=MetadataType.INLINE, to=MetadataType.FRONTMATTER)
            batch.order(
                k=None, o_keys=Order.ASC, o_values=Order.ASC, meta_type=MetadataType.ALL
            )
            batch.remove_duplicate_values(k=None, meta_type=MetadataType.ALL)

            assert notes[0].metadata.frontmatter.metadata["status"] == ["active"]


class TestReturnMetaclass:
    def test_returns_correct_classes(self):
        assert return_metaclass(MetadataType.FRONTMATTER) == Frontmatter
        assert return_metaclass(MetadataType.INLINE) == InlineMetadata
        assert return_metaclass(MetadataType.ALL) == NoteMetadata
        assert return_metaclass(MetadataType.DEFAULT) is None
