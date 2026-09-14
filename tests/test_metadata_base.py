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
    def test_metadata_repr(self):
        meta = DummyMetadata("tags: python, pytest")

        repr_str = repr(meta)

        assert "DummyMetadata" in repr_str
        assert "python, pytest" in repr_str

    class Test_has:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("tags: python, pytest\nempty_key:")

        def test_keys(self):
            assert self.meta.has("tags")
            assert not self.meta.has("missing")

        def test_keys_and_values(self):
            assert self.meta.has("tags", "python")
            assert self.meta.has("tags", ["python", "pytest"])
            assert not self.meta.has("tags", ["python", "missing"])

        def test_key_with_no_values(self):
            assert self.meta.has("empty_key", [])
            assert not self.meta.has("tags", [])

    class Test_add:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("tags: python")

        def test_single_element(self):
            assert len(self.meta.metadata) == 1

            self.meta.add("tags", "pytest")

            assert len(self.meta.metadata) == 1
            assert self.meta.get("tags") == ["python", "pytest"]

        def test_duplicate_value(self):
            assert len(self.meta.metadata) == 1

            self.meta.add("tags", "pytest", allow_duplicates=False)

            assert len(self.meta.metadata) == 1
            assert self.meta.get("tags") == ["python", "pytest"]

            self.meta.add("tags", "pytest", allow_duplicates=True)

            assert len(self.meta.metadata) == 1
            assert self.meta.get("tags") == ["python", "pytest", "pytest"]

        def test_overwrite(self):
            self.meta.add("tags", ["java", "c++"], overwrite=True)

            assert len(self.meta.metadata) == 1
            assert self.meta.get("tags") == ["java", "c++"]

        def test_numerical_value(self):
            self.meta.add("count", 42)
            self.meta.add("ratio", 3.14)

            assert len(self.meta.metadata) == 3
            assert self.meta.get("count") == ["42"]
            assert self.meta.get("ratio") == ["3.14"]

        def test_empty_key(self):
            self.meta.add("empty", None)

            assert self.meta.get("empty") == []

    class Test_remove:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("tags: python, pytest, java")

        def test_nonexisting_key(self):
            self.meta.remove("missing")

            assert self.meta.has("tags", ["python", "pytest", "java"])

        def test_single_item(self):
            self.meta.remove("tags", "pytest")

            assert self.meta.get("tags") == ["python", "java"]

        def test_list_of_values(self):
            self.meta.remove("tags", ["python", "java"])

            assert self.meta.has("tags", ["pytest"])

        def test_remove_key(self):
            self.meta.remove("tags")

            assert not self.meta.has("tags")

    def test_metadata_remove_empty(self):
        meta = DummyMetadata("tags: python\nempty1:\nempty2:")
        assert len(meta.metadata) == 3

        meta.remove_empty()

        assert len(meta.metadata) == 1
        assert "tags" in meta.metadata
        assert "empty1" not in meta.metadata
        assert "empty2" not in meta.metadata

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

    class Test_order_values:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("")
            self.meta.metadata = {
                "letters": ["b", "c", "a"],
                "more_letters": ["f", "e", "g"],
            }

        def test_multiple_keys(self):
            self.meta.order_values(None, how=Order.ASC)

            assert self.meta.get("letters") == ["a", "b", "c"]
            assert self.meta.get("more_letters") == ["e", "f", "g"]

        def test_ascending(self):
            self.meta.order_values("letters", how=Order.ASC)

            assert self.meta.get("letters") == ["a", "b", "c"]

        def test_decending(self):
            self.meta.order_values("letters", how=Order.DESC)

            assert self.meta.get("letters") == ["c", "b", "a"]

        def test_invalid_how(self):
            with pytest.raises(ArgTypeError):
                self.meta.order_values("letters", how="invalid")  # type: ignore

    class Test_order_keys:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("")
            self.meta.metadata = {"z": ["1"], "a": ["2"], "m": ["3"]}

        def test_no_keys(self):
            self.meta.metadata = {}
            assert len(self.meta.metadata) == 0

            self.meta.order_keys(how=Order.ASC)

            assert len(self.meta.metadata) == 0

        def test_ascending(self):
            self.meta.order_keys(how=Order.ASC)

            assert list(self.meta.metadata.keys()) == ["a", "m", "z"]
            assert self.meta.has("a", ["2"])
            assert self.meta.has("m", ["3"])
            assert self.meta.has("z", ["1"])

        def test_descending(self):
            self.meta.order_keys(how=Order.DESC)

            assert list(self.meta.metadata.keys()) == ["z", "m", "a"]
            assert self.meta.has("a", ["2"])
            assert self.meta.has("m", ["3"])
            assert self.meta.has("z", ["1"])

    class Test_order:
        @pytest.fixture(autouse=True)
        def setup_method(self):
            self.meta = DummyMetadata("")
            self.meta.metadata = {"z": ["b", "a"], "a": ["y", "x"]}

        def test_nones(self):
            self.meta.order(o_keys=None, o_values=None)

            assert list(self.meta.metadata.keys()) == ["z", "a"]
            assert self.meta.get("a") == ["y", "x"]
            assert self.meta.get("z") == ["b", "a"]

        def test_ascending(self):
            self.meta.order(o_keys=Order.ASC, o_values=None)
            assert list(self.meta.metadata.keys()) == ["a", "z"]
            assert self.meta.get("a") == ["y", "x"]
            assert self.meta.get("z") == ["b", "a"]

            self.meta.order(o_keys=None, o_values=Order.ASC)
            assert list(self.meta.metadata.keys()) == ["a", "z"]
            assert self.meta.get("a") == ["x", "y"]
            assert self.meta.get("z") == ["a", "b"]

    def test_metadata_print(self, capsys):
        meta = DummyMetadata("tags: python, pytest")

        meta.print()
        captured = capsys.readouterr()

        assert "tags: python, pytest\n" in captured.out
