"""Metadata-related objects."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from pyomd.config import CONFIG
from pyomd.exceptions import ArgTypeError
from pyomd.metadata import Frontmatter, InlineMetadata, Metadata, MetadataType
from pyomd.misc import Order

UserInput = str | int | float
MetaValues = list[str] | None
MetaDict = dict[str, MetaValues]
ParseFunction = Callable[[str], tuple[MetaDict, str]]
Number = int | float
Span = tuple[int, int]
SpanList = list[Span]


class NoteMetadata:
    """API to the note's metadata (frontmatter + inline).

    Attributes:
        frontmatter:
            frontmatter metadata
        inline:
            inline metadata
    """

    def __init__(self, note_content: str):
        self.frontmatter = Frontmatter(note_content)
        self.inline = InlineMetadata(note_content)

    @classmethod
    def _parse_arg_meta_type(cls, meta_type: MetadataType | None) -> MetadataType:
        if meta_type is None:
            meta_type = MetadataType.ALL
        if not isinstance(meta_type, MetadataType):
            raise ArgTypeError(
                var_name="meta_type",
                type_given=type(meta_type),
                type_expected=str(MetadataType | None),
            )
        return meta_type

    def get_default_metadata(self, k: str | None):
        """Get default metadata, as defined in the library configuration parameters.

        Args:
            k:
                Key for which to check the default metadata.
                If None, returns the global default metadata

        """
        b1 = (k is not None) and (k in CONFIG.cfg["fields"])
        b2 = "default_meta" in CONFIG.cfg["fields"].get(k, {})
        if b1 and b2:
            meta_type = MetadataType.get_from_str(
                CONFIG.cfg["fields"][k]["default_meta"]
            )
        else:
            meta_type = MetadataType.get_from_str(CONFIG.cfg["global"]["default_meta"])
        return meta_type

    def get(self, k: str, meta_type: MetadataType | None = None) -> MetaValues:
        """Returns metadata values for the given key.

        Args:
            k:
                metadata key
            meta_type:
                metadata type to check from. Set to None to check all metadata types

        Returns:
            If meta_type is set to None, returns frontmatter.metadata[k] + inline.metadata[k]
        """
        if meta_type == MetadataType.DEFAULT:
            meta_type = self.get_default_metadata(k)

        get_fm = self.frontmatter.get(k=k)
        get_il = self.inline.get(k=k)
        if meta_type == MetadataType.FRONTMATTER:
            return get_fm
        if meta_type == MetadataType.INLINE:
            return get_il
        if meta_type is None:
            if (get_fm is None) and (get_il is None):
                return None
            if get_fm is None:
                return get_il
            if get_il is None:
                return get_fm
            return get_fm + get_il

    def has(
        self,
        k: str,
        l: list[str] | None | str = None,
        meta_type: MetadataType | None = None,
    ) -> bool:
        """Checks if metadata contains field k and values l in a given meta type.

        Args:
            k:
                metadata key.
            l:
                values of the metadata field. If set to None, no values are checked.
                To check if metadata[k] is empty, set l to an empty list.
            meta_type:
                metadata type. If None, it returns true if it finds the expected values
                in any of the metadata types.

        Returns:
            Boolean
        """
        b_has_fm = self.frontmatter.has(k=k, l=l)
        b_has_il = self.inline.has(k=k, l=l)
        if meta_type is None:
            return b_has_fm or b_has_il
        if meta_type == MetadataType.FRONTMATTER:
            return b_has_fm
        if meta_type == MetadataType.INLINE:
            return b_has_il
        else:
            raise NotImplementedError

    def add(
        self,
        k: str,
        l: UserInput | list[UserInput] | None,
        meta_type: MetadataType = MetadataType.DEFAULT,
        overwrite: bool = False,
        allow_duplicates: bool = False,
    ):
        """Adds a metadata field (k,v)

        Args:
            k:
                metadata key
            l:
                values or list of values for the metadata key
            meta_type:
                The metadata type to add to
            overwrite:
                If precedent values for the metadata key provided should be overwritten.
                If false, new values are appended instead.
            allow_duplicates:
                Allow duplicate values.
        """
        if meta_type == MetadataType.DEFAULT:
            meta_type = self.get_default_metadata(k)
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.add(
                k=k, l=l, overwrite=overwrite, allow_duplicates=allow_duplicates
            )
        if meta_type == MetadataType.INLINE:
            self.inline.add(
                k=k, l=l, overwrite=overwrite, allow_duplicates=allow_duplicates
            )

    def remove(
        self,
        k: str,
        l: UserInput | list[UserInput] | None = None,
        meta_type: MetadataType | None = None,
    ):
        """Removes a metadata key or particular values.

        Args:
            k:
                metadata key
            l:
                metadata values
            meta_type:
                metadata type to modify.
                If None, removes from both the frontmatter and inline metadata
        """
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.remove(k=k, l=l)
        if meta_type == MetadataType.INLINE:
            self.inline.remove(k=k, l=l)
        if meta_type is None:
            self.frontmatter.remove(k=k, l=l)
            self.inline.remove(k=k, l=l)

    def remove_empty(
        self,
        meta_type: MetadataType = MetadataType.ALL,
    ):
        """removes empty metadata fields.

        Args:
            meta_type:
                metadata type. Defaults to MetadataType.ALL:
                All metadata fields with empty values are removed,
                from the frontmatter and inline.
        """
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.remove_empty()
        if meta_type == MetadataType.INLINE:
            self.inline.remove_empty()
        if meta_type is MetadataType.ALL:
            self.frontmatter.remove_empty()
            self.inline.remove_empty()

    def remove_duplicate_values(
        self,
        k: str | list[str] | None = None,
        meta_type: MetadataType | None = None,
    ):
        """Remove duplicate values in the note's metadata

        Args:
            k:
                key or list of keys on which to perform the duplication removal. If None, does it on all keys.
            meta_type:
                metadata type. If None, performs the operation on all metadata types.
        """
        meta_type = self._parse_arg_meta_type(meta_type)
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.remove_duplicate_values(k=k)
        elif meta_type == MetadataType.INLINE:
            self.inline.remove_duplicate_values(k=k)
        elif meta_type == MetadataType.ALL:
            self.frontmatter.remove_duplicate_values(k=k)
            self.inline.remove_duplicate_values(k=k)
        else:
            raise ValueError(f"Unsupported value for argument meta_type: {meta_type}")

    def order_values(
        self,
        k: str | list[str] | None = None,
        how: Order = Order.ASC,
        meta_type: MetadataType | None = None,
    ) -> None:
        """Order the values of a metadata field.

        Args:
            k:
                metadata keys to order. If None, order values of all metadata keys
            how:
                "asc" (ascending) or "desc" (descending)
            meta_type:
                IF None, orders on all type of metadata (frontmatter and inline)
        """
        meta_type = self._parse_arg_meta_type(meta_type)
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.order_values(k=k, how=how)
        elif meta_type == MetadataType.INLINE:
            self.inline.order_values(k=k, how=how)
        elif meta_type == MetadataType.ALL:
            self.frontmatter.order_values(k=k, how=how)
            self.inline.order_values(k=k, how=how)
        else:
            raise ValueError(f"Unsupported value for argument meta_type: {meta_type}")

    def order_keys(
        self, how: Order = Order.DESC, meta_type: MetadataType | None = None
    ) -> None:
        """Order metadata keys.

        Args:
            how:
                "asc" or "desc"
            meta_type:
                If None, orders on all type of metadata (frontmatter and inline)
        """
        meta_type = self._parse_arg_meta_type(meta_type)
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.order_keys(how=how)
        elif meta_type == MetadataType.INLINE:
            self.inline.order_keys(how=how)
        elif meta_type == MetadataType.ALL:
            self.frontmatter.order_keys(how=how)
            self.inline.order_keys(how=how)
        else:
            raise ValueError(f"Unsupported value for argument meta_type: {meta_type}")

    def order(
        self,
        k: str | list[str] | None = None,
        o_keys: Order | None = Order.ASC,
        o_values: Order | None = Order.ASC,
        meta_type: MetadataType | None = None,
    ):
        """Order metadata keys and values.

        Args:
            k:
                key or list of keys to order. If None, order all.
            o_keys:
                How to order keys. "asc" or "desc". If None, don't order them.
            o_values:
                How to order values. "asc" or "desc". If None, don't order them.
            meta_type:
                If None, orders on all type of metadata (frontmatter and inline)
        """
        meta_type = self._parse_arg_meta_type(meta_type)
        if meta_type == MetadataType.FRONTMATTER:
            self.frontmatter.order(k=k, o_keys=o_keys, o_values=o_values)
        elif meta_type == MetadataType.INLINE:
            self.inline.order(k=k, o_keys=o_keys, o_values=o_values)
        elif meta_type == MetadataType.ALL:
            self.frontmatter.order(k=k, o_keys=o_keys, o_values=o_values)
            self.inline.order(k=k, o_keys=o_keys, o_values=o_values)
        else:
            raise ValueError(f"Unsupported value for argument meta_type: {meta_type}")

    def move(
        self,
        k: str | list[str] | None = None,
        fr: MetadataType | None = None,
        to: MetadataType | None = None,
    ):
        """Move a metadata field between frontmatter and inline.

        Args:
            k:
                Key of the metadata field to move. If None, move all fields.
            fr:
                metadata type to move from.
            to:
                metadata type to move to.
        """
        if (k is None) and (fr is None) and (to is None):
            for k2 in CONFIG.cfg["fields"]:
                if "default_meta" in CONFIG.cfg["fields"][k2]:
                    default_meta = MetadataType.get_from_str(
                        CONFIG.cfg["fields"][k2]["default_meta"]
                    )
                    m_to = (
                        self.frontmatter
                        if default_meta == MetadataType.FRONTMATTER
                        else self.inline
                    )
                    m_from = (
                        self.frontmatter
                        if default_meta == MetadataType.INLINE
                        else self.inline
                    )
                    if k2 in m_from.metadata:
                        m_to.add(k=k2, l=m_from.metadata[k2])
                        m_from.remove(k=k2)
            return

        assert (fr is not None) and (to is not None), "args 'fr' and 'to' should be set"
        m_from = self.inline if fr == MetadataType.INLINE else self.frontmatter
        m_to = self.inline if to == MetadataType.INLINE else self.frontmatter

        if k is None:
            k = list(m_from.metadata.keys())
        if isinstance(k, str):
            k = [k]
        for k2 in k:
            if k2 in m_from.metadata:
                m_to.add(k=k2, l=m_from.metadata[k2])
                m_from.remove(k=k2)

    def _update_content(
        self,
        note_content: str,
        inline_position: str = "bottom",
        inline_inplace: bool = True,
        inline_tml: str | Callable = "standard",
    ) -> str:
        """Update the note's metadata (frontmatter and inline)"""
        str_no_fm = self.frontmatter._erase(note_content)
        res = self.inline._update_content(
            str_no_fm, position=inline_position, inplace=inline_inplace, tml=inline_tml
        )
        res = self.frontmatter.to_string() + res
        return res


class NoteMetadataBatch:
    """API to modify in batch metadata from a Notes object."""

    def __init__(self, notes: list[Note]):
        self.notes = notes

    def add(
        self,
        k: str,
        l: UserInput | list[UserInput] | None,
        meta_type: MetadataType = MetadataType.DEFAULT,
        overwrite: bool = False,
        allow_duplicates: bool = False,
    ):
        """Add metadata to the batch of notes.

        See `NoteMetadata.add` for argument description
        """
        for note in self.notes:
            note.metadata.add(
                k=k,
                l=l,
                meta_type=meta_type,
                overwrite=overwrite,
                allow_duplicates=allow_duplicates,
            )

    def remove(
        self,
        k: str,
        l: UserInput | list[UserInput] | None = None,
        meta_type: MetadataType | None = None,
    ):
        """Removes metadata from the batch of notes.

        See `NoteMetadata.remove` for argument description
        """
        for note in self.notes:
            note.metadata.remove(k=k, l=l, meta_type=meta_type)

    def move(
        self,
        k: str | list[str] | None = None,
        fr: MetadataType | None = None,
        to: MetadataType | None = None,
    ):
        """Moves metadata for the batch of notes.

        See `NoteMetadata.move` for argument description
        """
        for note in self.notes:
            note.metadata.move(k=k, fr=fr, to=to)

    def remove_duplicate_values(
        self,
        k: str | list[str] | None = None,
        meta_type: MetadataType | None = None,
    ):
        """Remove duplicate metadata values for the batch of notes.

        See `NoteMetadata.remove_duplicate_values` for argument description
        """
        for note in self.notes:
            note.metadata.remove_duplicate_values(k=k, meta_type=meta_type)

    def order(
        self,
        k: str | list[str] | None = None,
        o_keys: Order | None = Order.ASC,
        o_values: Order | None = Order.ASC,
        meta_type: MetadataType | None = None,
    ):
        """Orders metadata for the batch of notes.

        See `NoteMetadata.order` for argument description
        """
        for note in self.notes:
            note.metadata.order(
                k=k, o_keys=o_keys, o_values=o_values, meta_type=meta_type
            )


def return_metaclass(
    meta_type: MetadataType,
) -> type[Metadata | NoteMetadata] | None:
    if meta_type == MetadataType.FRONTMATTER:
        return Frontmatter
    elif meta_type == MetadataType.INLINE:
        return InlineMetadata
    elif meta_type == MetadataType.ALL:
        return NoteMetadata
    else:
        return None
        # raise NotImplementedError(f'no metadata class implemented of type "{meta_type}"')
