import pytest
from icecream import ic

from pyomd.metadata import MetadataType

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
