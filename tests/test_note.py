import pytest
from icecream import ic

ic.configureOutput(includeContext=True)

from pyomd.note import Note


class TestNote:
    def test_init(self, tmp_path):
        temp_file = tmp_path / "note1.md"
        temp_file.write_text("")

        Note(temp_file)
