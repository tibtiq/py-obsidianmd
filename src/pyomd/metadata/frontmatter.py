from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from pathlib import Path

import frontmatter

from pyomd.exceptions import InvalidFrontmatterError
from pyomd.metadata.base import Metadata, MetadataType

MetaValues = list[str] | None
MetaDict = dict[str, MetaValues]
ParseFunction = Callable[[str], tuple[MetaDict, str]]
Number = int | float
Span = tuple[int, int]


class Frontmatter(Metadata):
    """A note's frontmatter.

    Attributes:
        self.metadata MetaDict:
            metadata dictionary
    """

    REGEX = "(?s)(^---\n).*?(\n---\n)"

    def to_string(self) -> str:
        """Render metadata as a string.

        Returns:
            String representation of the metadata
        """
        if len(self.metadata) == 0:
            return ""
        metadata_repr = ""
        for k, v in self.metadata.items():
            if v is None:
                continue

            if len(v) == 1:
                metadata_repr += f"{k}: {v[0]}\n"
            else:
                metadata_repr += f"{k}: [ {', '.join(v)} ]\n"
        out = "---\n" + metadata_repr + "---\n"
        return out

    def _update_content(self, note_content: str) -> str:
        """Returns the note content with the updated metadata.

        Args:
            note_content:
                The note content
        """
        content_no_meta = self._erase(note_content)
        res = self.to_string() + content_no_meta
        return res

    @staticmethod
    def is_frontmatter_valid(path: Path) -> bool:
        """Checks if the file frontmatter is valid."""
        is_valid = True
        try:
            with open(path, "r") as f:
                frontmatter.load(f)
        except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as e:
            print(f"File operations failed due to a system error: {e}")
            is_valid = False

        return is_valid

    @classmethod
    def _parse(
        cls, note_content: str, parse_fn: ParseFunction | None = None
    ) -> MetaDict:
        """Parse note content to extract metadata dictionary."""
        if parse_fn is None:
            parse_fn = cls._parse_1
        return parse_fn(note_content)

    @classmethod
    def _parse_1(cls, note_content: str) -> MetaDict:
        """Parse note content to extract metadata dictionary.
        Uses the python-frontmatter library."""
        try:
            fm = frontmatter.loads(note_content)
        except Exception as e:
            raise InvalidFrontmatterError(exception=e) from e

        meta_dict: MetaDict = fm.metadata

        for k in meta_dict:
            if meta_dict[k] is None:
                meta_dict[k] = []

        # make all elements into list of strings
        for k, v in meta_dict.items():
            # print(f'K = "{k}"\nV = "{v}"\ntype(V) = "{type(v)}"')
            if isinstance(v, str):
                meta_dict[k] = [v]
            elif isinstance(v, list):
                meta_dict[k] = [str(x) for x in v]
            elif isinstance(v, (Number, datetime.date)):
                meta_dict[k] = [str(v)]

        meta_dict = cls._parse_special_fields(
            metadata=meta_dict, meta_type=MetadataType.FRONTMATTER
        )
        return meta_dict

    @classmethod
    def _parse_2(cls, note_content: str) -> MetaDict:
        """Parse frontmatter metadata using regex"""
        mtc = re.search(cls.REGEX, note_content)
        if mtc is None:
            ext_str = []
        fm_str = mtc.group()
        ext_str = [fm_str]

        # convert extracted string to dictionary
        metadata: MetaDict = {}
        if len(ext_str) == 0:
            return {}
        ms = ext_str[0]
        elements = ms.split("\n")
        for e in elements:
            if ":" not in e:
                continue
            k, v = e.split(":", maxsplit=1)
            c = [v.strip()] if "," not in v else [x.strip() for x in v.split(",")]
            metadata[k.strip()] = c
        if "tags" in metadata:
            mtags = " ".join(metadata["tags"])
            metadata["tags"] = [t.strip() for t in mtags.split(" ") if t.strip() != ""]

        return metadata

    @classmethod
    def _erase(cls, note_content: str) -> str:
        r: str = frontmatter.loads(note_content).content
        return r
