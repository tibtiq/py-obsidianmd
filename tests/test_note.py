import pytest
from icecream import ic

ic.configureOutput(includeContext=True)

from pyomd.note import Note, Notes


class TestNote:
    def test_init(self, tmp_path):
        temp_file = tmp_path / "note1.md"
        temp_file.write_text("")

        Note(temp_file)

    def test_repr(self, tmp_path):
        temp_file = tmp_path / "note1.md"
        temp_file.write_text("")

        note = Note(temp_file)
        assert note == eval(repr(note))

    class TestEQ:
        def test_eq(self, tmp_path):
            temp_file = tmp_path / "note1.md"
            temp_file.write_text("")
            note1 = Note(temp_file)

            temp_file = tmp_path / "note1.md"
            temp_file.write_text("")
            note2 = Note(temp_file)

            assert note1 == note2

        def test_not_same_instance(self, tmp_path):
            temp_file = tmp_path / "note1.md"
            temp_file.write_text("")
            note = Note(temp_file)

            assert note != 1


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
