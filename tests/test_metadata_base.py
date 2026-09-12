import pytest
from icecream import ic

from pyomd.exceptions import ArgTypeError, InvalidFrontmatterError
from pyomd.metadata import Metadata, MetadataType
from pyomd.metadata.base import MetaDict

ic.configureOutput(includeContext=True)


class TestMetadataType:
    def test_supported_value(self):
        assert MetadataType.get_from_str(None) == MetadataType.ALL
        assert MetadataType.get_from_str("frontmatter") == MetadataType.FRONTMATTER
        assert MetadataType.get_from_str("inline") == MetadataType.INLINE
        assert MetadataType.get_from_str("notemeta") == MetadataType.ALL
        assert MetadataType.get_from_str("default") == MetadataType.DEFAULT

    def test_unsupported_value(self):
        with pytest.raises(ValueError):
            assert MetadataType.get_from_str("not_supported")


class DummyMetadata(Metadata):
    """Concrete subclass of Metadata for testing purposes."""

    def to_string(self) -> str:
        if not self.metadata:
            return ""
        lines = []
        for k, v in self.metadata.items():
            lines.append(f"{k}: {', '.join(v)}")
        return "\n".join(lines)

    def _update_content(self, note_content: str) -> str:
        return note_content

    @classmethod
    def _parse(cls, note_content: str, parse_fn=None) -> MetaDict:
        if note_content == "INVALID":
            raise InvalidFrontmatterError("Invalid frontmatter")
        if not note_content.strip():
            return {}

        # Simple mock parser: "key: val1, val2" or "key:"
        result: MetaDict = {}
        for line in note_content.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                result[k] = (
                    [val.strip() for val in v.split(",") if val.strip()] if v else []
                )
        return result

    @classmethod
    def _erase(cls, note_content: str) -> str:
        return ""


class TestMetadata:

    class Test_remove_duplicate_values:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("")
            self.meta.metadata = {
                "k1": ["a", "b", "a", "c", "b"],
                "k2": ["x", "x", "y"],
            }

        def test_key_has_duplicates_values(self):
            self.meta.remove_duplicate_values("k1")
            assert self.meta.get("k1") == ["a", "b", "c"]
            assert self.meta.get("k2") == ["x", "x", "y"]

        def test_multiple_keys_have_duplicates_values(self):
            self.meta.remove_duplicate_values(["k1", "k2"])
            assert self.meta.get("k1") == ["a", "b", "c"]
            assert self.meta.get("k2") == ["x", "y"]

        def test_remove_all_duplicates(self):
            self.meta.remove_duplicate_values()
            assert self.meta.get("k1") == ["a", "b", "c"]
            assert self.meta.get("k2") == ["x", "y"]

        def test_key_not_in_metadata(self):
            self.meta.remove_duplicate_values(["k3"])
            assert self.meta.get("k1") == ["a", "b", "a", "c", "b"]
            assert self.meta.get("k2") == ["x", "x", "y"]

        def test_invalid_key(self):
            with pytest.raises(ArgTypeError):
                self.meta.remove_duplicate_values(123)  # type: ignore

