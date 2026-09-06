from icecream import ic

ic.configureOutput(includeContext=True)

from pyomd.note import Note, Notes


class TestNote:
    def test_init(self, make_markdown_file):
        temp_file = make_markdown_file(content="")

        Note(temp_file)

    def test_repr(self, make_markdown_file):
        temp_file = make_markdown_file(content="")
        temp_file.write_text("")

        note = Note(temp_file)
        assert note == eval(repr(note))

    class TestEQ:
        def test_eq(self, make_markdown_file):
            temp_file = make_markdown_file(content="")
            note1 = Note(temp_file)

            temp_file = make_markdown_file(content="")
            note2 = Note(temp_file)

            assert note1 == note2

        def test_not_same_instance(self, make_markdown_file):
            temp_file = make_markdown_file(content="")
            note = Note(temp_file)

            assert note != 1

    class TestAppend:
        def test_append(self, make_markdown_file):
            temp_file = make_markdown_file(content="")
            note = Note(temp_file)

            new_content = "new_content"

            note.append(new_content, False)
            assert note.content == f"\n{new_content}"

            note.append(new_content, False)
            assert note.content == f"\n{new_content}"

        def test_allow_repeat(self, make_markdown_file):
            temp_file = make_markdown_file(content="new_content")
            note = Note(temp_file)

            new_content = "new_content"

            note.append(new_content, True)
            assert note.content == "new_content\nnew_content"


class TestNotes:
    def test_init_single(self, make_markdown_file):
        temp_file = make_markdown_file(content="")

        Note(temp_file)

    def test_init_dir(self, tmp_path, make_markdown_file):
        make_markdown_file("", filename="note1.md")
        notes = Notes(tmp_path)

        assert len(notes) == 1

        make_markdown_file("", filename="note2.md")
        notes = Notes(tmp_path)

        assert len(notes) == 2
