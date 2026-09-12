import pytest

from pyomd.metadata import MetadataType


class TestMetadataType:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (None, MetadataType.ALL),
            ("frontmatter", MetadataType.FRONTMATTER),
            ("inline", MetadataType.INLINE),
            ("notemeta", MetadataType.ALL),
            ("default", MetadataType.DEFAULT),
        ],
    )
    def test_supported_value(self, value, expected):
        assert MetadataType.get_from_str(value) == expected

    def test_unsupported_value(self):
        with pytest.raises(ValueError):
            assert MetadataType.get_from_str("not_supported")
