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
