from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum

from pyomd.config import CONFIG
from pyomd.exceptions import ArgTypeError, InvalidFrontmatterError
from pyomd.misc import Order

UserInput = str | int | float
MetaValues = list[str] | None
MetaDict = dict[str, MetaValues]
ParseFunction = Callable[[str], tuple[MetaDict, str]]
Number = int | float
Span = tuple[int, int]
SpanList = list[Span]


class MetadataType(Enum):
    """Type of metadata.

    Possible values:
        FRONTMATTER: note frontmatter
        INLINE: inline metadata (dataview style)
        ALL: note metadata, wherever it is located (inline, or frontmatter)
        DEFAULT: default location where to define new metadata
    """

    FRONTMATTER = "frontmatter"
    INLINE = "inline"
    ALL = "notemeta"
    DEFAULT = "default"

    @staticmethod
    def get_from_str(s: str | None) -> MetadataType:
        """Returns Enum value from string.

        Args:
            s:
                string value.
        """
        if s is None:
            return MetadataType.ALL
        for k in MetadataType:
            if s == k.value:
                return k
        raise ValueError(f'Metadatatype not defined: "{s}"')


class Metadata(ABC):
    """Common attributes and methods for all types of metadata."""

    def __init__(self, note_content: str):
        self.metadata: MetaDict = self._parse(note_content)

    def __repr__(self):
        rpr = f"{type(self)}:\n"
        if self.to_string() is None:
            rpr += " None"
        else:
            for k, v in self.metadata.items():
                if isinstance(v, list):
                    rpr += "".join([f"- {k}: {', '.join(v)}\n"])
        return rpr

    @abstractmethod
    def to_string(self) -> str: ...

    def get(self, k: str) -> list[str] | None:
        """Gets metadata field.

        Args:
            k:
                metadata key
        Returns:
            Values of the metadata field. Returns None if k is not in the metadata keys
        """
        return self.metadata.get(k, None)

    def has(self, k: str, l: list[str] | None | str = None) -> bool:
        """Checks if metadata contains field k and values l.

        Args:
            k:
                metadata key.
            l:
                values of the metadata field. If set to None, no values are checked.
                To check if metadata[k] is empty, set l to an empty list.
        Returns:
            Boolean
        """
        b_has = k in self.metadata
        if l is None:
            return b_has
        if isinstance(l, str):
            l = [l]
        if b_has and len(l) == 0:
            b_has = self.metadata[k] == []
        if b_has and len(l) > 0:
            b_has = False

            metadata = self.metadata[k]
            if isinstance(metadata, list):
                b_has = all(val in metadata for val in l)

        return b_has

    def add(
        self,
        k: str,
        l: UserInput | list[UserInput] | None,
        overwrite: bool = False,
        allow_duplicates: bool = False,
    ) -> None:
        """Adds a metadata key and/or new values.

        Args:
            k:
                metadata key
            l:
                metadata values
            overwrite:
                Overwrite the existing values or not.
            allow_duplicates:
                Allow for duplicate values for a given metadata key.
        """
        if l is None:
            nl = []
        elif isinstance(l, UserInput):
            nl = [str(l)]
        else:
            nl = [str(x) for x in l]

        if overwrite:
            self.metadata[k] = nl
        else:
            if k in self.metadata:
                if allow_duplicates:
                    self.metadata[k] += nl
                else:
                    self.metadata[k] += [x for x in nl if x not in self.metadata[k]]
            else:
                self.metadata[k] = nl

    def remove(self, k: str, l: UserInput | list[UserInput] | None = None) -> None:
        """Removes a metadata key or particular values.

        See `NoteMetadata.remove` for argument description
        """
        if k not in self.metadata:
            return
        if l is None:
            del self.metadata[k]
            return
        nl = [str(l)] if isinstance(l, UserInput) else [str(x) for x in l]
        self.metadata[k] = [e for e in self.metadata[k] if e not in nl]

    def remove_empty(self) -> None:
        """removes empty metadata fields.

        See `NoteMetadata.remove_rempty` for argument description
        """
        empty: list[str] = []
        for k in self.metadata:
            if len(self.metadata[k]) == 0:
                empty.append(k)

        for k in empty:
            del self.metadata[k]

    def remove_duplicate_values(self, k: str | list[str] | None = None) -> None:
        """Removes duplicate values of a metadata key.

        See `NoteMetadata.remove_duplicate_values` for argument description
        """

        if k is None:
            list_keys = list(self.metadata.keys())
        elif isinstance(k, str):
            list_keys = [k]
        elif isinstance(k, list):
            list_keys = k
        else:
            raise ArgTypeError(
                var_name="k",
                type_given=type(k),
                type_expected=str(str | list[str] | None),
            )

        for k2 in list_keys:
            if k2 not in self.metadata:
                continue
            self.metadata[k2] = list(dict.fromkeys(self.metadata[k2]))

    def order_values(
        self, k: str | list[str] | None = None, how: Order = Order.ASC
    ) -> None:
        """Orders metadata values.

        See `NoteMetadata.order_values` for argument description
        """
        if not isinstance(how, Order):
            raise ArgTypeError(
                var_name="how", type_given=type(how), type_expected=Order
            )

        if k is None:
            k = list(self.metadata.keys())
        if isinstance(k, str):
            k = [k]
        for e in k:
            reverse = how != Order.ASC
            self.metadata[e] = sorted(self.metadata[e], reverse=reverse)

    def order_keys(self, how: Order = Order.ASC) -> None:
        """Orders metadata keys.

        Uses the property that for python>=3.6, python dict remember insert order.

        See `NoteMetadata.order_keys` for argument description
        """
        reverse = how == Order.DESC
        list_keys = sorted(self.metadata.keys(), reverse=reverse)
        self.metadata = {k: self.metadata.pop(k) for k in list_keys}

    def order(
        self,
        k: str | list[str] | None = None,
        o_keys: Order | None = Order.ASC,
        o_values: Order | None = Order.ASC,
    ):
        """Orders metadata keys and values.

        See `NoteMetadata.order` for argument description
        """
        if o_keys is not None:
            self.order_keys(how=o_keys)
        if o_values is not None:
            self.order_values(k=k, how=o_values)

    def print(self):
        """Prints metadata information."""
        print(self.to_string())

    @abstractmethod
    def _update_content(self, note_content: str) -> str: ...

    @classmethod
    @abstractmethod
    def _parse(
        cls, note_content: str, parse_fn: ParseFunction | None = None
    ) -> MetaDict:
        pass

    @staticmethod
    def _parse_special_fields(metadata: MetaDict, meta_type: MetadataType) -> MetaDict:
        """Parse special fields."""
        sep_field_name = f"{meta_type.value}_separators"
        for k in metadata:
            b1 = k in CONFIG.cfg["fields"]
            b2 = sep_field_name in CONFIG.cfg["fields"].get(k, {})
            if b1 and b2:
                for sep in CONFIG.cfg["fields"][k][sep_field_name]:
                    tmp = sep.join(metadata[k])
                    metadata[k] = [t.strip() for t in tmp.split(sep) if t.strip() != ""]
        return metadata

    @classmethod
    @abstractmethod
    def _erase(cls, note_content: str) -> str:
        pass

    @classmethod
    def _exists(cls, note_content: str) -> bool:
        """Checks if the metadata type is present in the note"""
        try:
            meta_dict = cls._parse(note_content)
        except InvalidFrontmatterError:
            meta_dict = {}
        return len(meta_dict) > 0
