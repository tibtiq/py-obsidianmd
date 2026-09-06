import pytest
from icecream import ic

ic.configureOutput(includeContext=True)

from pyomd.note import Note, Notes


class TestNote:
    def test_init(self, tmp_path):
        temp_file = tmp_path / "note1.md"
        temp_file.write_text("")

        Note(temp_file)


class TestNotes:
    def test_init_single(self, tmp_path):
        temp_file = tmp_path / "note1.md"
        temp_file.write_text("")

        Note(temp_file)

    def test_init_dir(self, tmp_path):
        temp_file = tmp_path / "note1.md"
        temp_file.write_text("")

        notes = Notes(tmp_path)
        assert len(notes) == 1

        temp_file = tmp_path / "note2.md"
        temp_file.write_text("")

        notes = Notes(tmp_path)
        assert len(notes) == 2
