from __future__ import annotations

import re
from collections.abc import Callable
from string import Template

from pyomd.metadata.base import Metadata, MetadataType

MetaValues = list[str] | None
MetaDict = dict[str, MetaValues]
ParseFunction = Callable[[str], tuple[MetaDict, str]]
Span = tuple[int, int]
SpanList = list[Span]


class InlineMetadata(Metadata):
    """A note's inline metadata (dataview style).

    Attributes:
        self.metadata MetaDict:
            metadata dictionary
    """

    TMP_REGEX = Template(r"(?P<beg>.*?)(?P<key>$key)::(?P<values>.*)")
    TMP_REGEX_ENCLOSED = Template(
        r"(?P<beg>.*?)(?P<open>[(\[])(?P<key>$key)::(?P<values>.*?)(?P<close>[)\]])(?P<end>.*)"
    )
    REGEX = re.compile(TMP_REGEX.substitute(key="[A-z][A-z0-9_ -]*"))
    REGEX_ENCLOSED = re.compile(TMP_REGEX_ENCLOSED.substitute(key=".*?"))

    def to_string(
        self,
        ignore_k: str | list[str] | None = None,
        tml: str | Callable = "standard",
    ) -> str:
        """Render metadata as a string.

        Args:
            ignore_k:
                metadata keys to ignore.
            tml:
                Template function to use to display inline metadata.

        Returns:
            String representation of the metadata
        """
        if tml == "standard":
            tml = self._tml_standard
        elif tml == "callout":
            tml = self._tml_callout

        if ignore_k is None:
            ignore_k = []
        if isinstance(ignore_k, str):
            ignore_k = [ignore_k]
        meta_dict = {k: v for (k, v) in self.metadata.items() if k not in ignore_k}
        if len(meta_dict) == 0:
            return ""
        out = tml(meta_dict)
        return out

    def _update_content(
        self,
        note_content: str,
        position: str = "bottom",
        inplace: bool = True,
        tml: str | Callable = "standard",
    ) -> str:
        """
        position:
            - bottom
            - top
        inplace:
            - replace inline metadata inplace (for existing fields in the note)
        """
        if inplace:
            nc, ignore_k = self._update_content_inplace(note_content=note_content)
        else:
            nc, ignore_k = self._erase(note_content), None
        sep = self._get_sep_newlines(nc, position=position)
        if position == "top":
            new_nc = self.to_string(ignore_k=ignore_k, tml=tml) + sep + nc
        elif position == "bottom":
            new_nc = nc + sep + self.to_string(ignore_k=ignore_k, tml=tml)
        else:
            raise NotImplementedError
        new_nc = new_nc.strip()
        return new_nc

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

        Uses the python-frontmatter library.
        """

        matches: list[re.Match] = {}
        for l in note_content.split("\n"):
            m = cls.REGEX.search(l)
            b = m is not None
            b_enc = cls.REGEX_ENCLOSED.search(l) is not None
            if b and not b_enc:
                matches.append(m)

        tmp: dict[str, list[str]] = {}
        for m in matches:
            k = m.group("key").strip()
            v = m.group("values")
            tmp[k] = tmp.get(k, "") + ", " + v
        metadata: MetaDict = {
            k: [x.strip() for x in v.split(",") if len(x.strip()) > 0]
            for (k, v) in tmp.items()
        }

        metadata = cls._parse_special_fields(
            metadata=metadata, meta_type=MetadataType.INLINE
        )
        return metadata

    @classmethod
    def _erase(cls, note_content: str) -> str:

        keep: list[str] = []
        for l in note_content.split("\n"):
            b_match = re.search(cls.REGEX, l) is not None
            b_match_enclosed = re.search(cls.REGEX_ENCLOSED, l) is not None
            if b_match and not b_match_enclosed:
                continue
            keep.append(l)
        content_no_meta = "\n".join(keep)

        ## artefacts to erase
        artefacts = [re.escape("> [!info]- metadata") + "(\n\n|$)"]
        for a in artefacts:
            content_no_meta = re.sub(a, "", content_no_meta)
        return content_no_meta

    @staticmethod
    def _get_sep_newlines(content_no_meta: str, position: str = "bottom") -> str:
        if position == "top":
            if len(content_no_meta) >= 1 and content_no_meta[0] != "\n":
                sep = "\n\n"
            elif len(content_no_meta) >= 1 and content_no_meta[0:2] != "\n\n":
                sep = "\n"
            else:
                sep = ""
        elif position == "bottom":
            if len(content_no_meta) >= 1 and content_no_meta[-1] != "\n":
                sep = "\n\n"
            elif len(content_no_meta) >= 2 and content_no_meta[-2:] != "\n\n":
                sep = "\n"
            else:
                sep = ""
        else:
            sep = ""
        return sep

    @staticmethod
    def _get_spans_to_delete(
        s: str,
        r: re.Pattern,
        r_enc: re.Pattern,
        meta_dict: dict,
        debug: bool = False,
    ) -> SpanList:
        sp_del: SpanList = []
        for m in r.finditer(s):
            if r_enc.match(m.group()):
                continue
            k = m.group(2).strip()
            if k not in meta_dict:
                sp_del.append(m.span())
        return sp_del

    @staticmethod
    def _delete_span(s: str, span: Span) -> str:
        s = s[: span[0]] + s[span[1] :]
        return s

    @staticmethod
    def _delete_spans(s: str, spans: SpanList):
        offset = 0
        for span in spans:
            p1, p2 = span
            span_offset = (p1 - offset, p2 - offset)
            s = InlineMetadata._delete_span(s, span_offset)
            len_span = p2 - p1
            offset += len_span
        return s

    @staticmethod
    def _get_span_redundant_keys(
        s: str, r: re.Pattern, r_enc: re.Pattern, debug: bool = False
    ) -> SpanList:
        """Returns spans for inline metadata which keys appear earlier in the file content."""
        found_keys: set[str] = set()
        spans_del: SpanList = []
        for m in r.finditer(s):
            if r_enc.match(m.group()):
                continue
            k = m.group(2).strip()
            if debug:
                print(f'"{k}"')
            if k in found_keys:
                spans_del.append(m.span())
                if debug:
                    print(f'to delete: "{m.group()}"')
            else:
                found_keys.add(k)
                if debug:
                    print(f"keep: {m.group()}")
        return spans_del

    def _update_content_inplace(self, note_content: str) -> tuple[str, set[str]]:
        """
        Updates inline metadata in place.

        Returns a tuple:
            - updated note_content
            - list of updated fields.
        """

        rgx = re.compile(self.REGEX.pattern + "\n?")

        # remove fields that aren't in the metadata dictionary anymore
        spans: SpanList = self._get_spans_to_delete(
            s=note_content, r=rgx, r_enc=self.REGEX_ENCLOSED, meta_dict=self.metadata
        )
        note_content = self._delete_spans(note_content, spans)

        # remove redundant inline metadata
        spans_redundant = self._get_span_redundant_keys(
            s=note_content, r=rgx, r_enc=self.REGEX_ENCLOSED
        )
        note_content = self._delete_spans(note_content, spans_redundant)

        # update fields still in metadata dictionary
        updated_fields: set[str] = set()
        for key in self.metadata:
            # print(f'this is key: "{key}"')
            new_v = ", ".join(self.metadata[key])
            regex_field = re.compile(self.TMP_REGEX.substitute(key=f"{key} *"))
            for m in regex_field.finditer(note_content):
                updated_fields.add(key)
                beg = m.group("beg")
                k = m.group("key")
                rep = f"{beg}{k.strip()} :: {new_v}"
                note_content = regex_field.sub(rep, note_content)

        return (note_content, updated_fields)

    @staticmethod
    def _tml_standard(meta_dict: dict | None = None) -> str:
        """
        Args:
            - meta_dict: dictionary containing inline metadata (k,v pairs)
        """
        if meta_dict is None:
            meta_dict = {}
        tmp = [f"{k}:: {', '.join(v)}" for k, v in meta_dict.items()]
        out = "\n".join(tmp)
        return out

    @staticmethod
    def _tml_callout(meta_dict: dict | None = None) -> str:
        """
        Args:
            - meta_dict: dictionary containing inline metadata (k,v pairs)
        """
        if meta_dict is None:
            meta_dict = {}
        tmp = ["> [!info]- metadata"]
        tmp += [f"> {k} :: {', '.join(v)}" for k, v in meta_dict.items()]
        out = "\n".join(tmp)
        return out
