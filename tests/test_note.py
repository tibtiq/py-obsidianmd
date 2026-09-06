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
            note1 = Note(make_markdown_file(content=""))
            note2 = Note(make_markdown_file(content=""))

            assert note1 == note2

        def test_not_same_instance(self, make_markdown_file):
            temp_file = make_markdown_file(content="")
            note = Note(temp_file)

            assert note != 1

    class TestAppend:
        def test_append(self, make_markdown_file):
            note = Note(make_markdown_file(content=""))

            new_content = "new_content"
            note.append(new_content, False)
            assert note.content == f"\n{new_content}"

            note.append(new_content, False)
            assert note.content == f"\n{new_content}"

        def test_allow_repeat(self, make_markdown_file):
            file_content = "file_content"
            note = Note(make_markdown_file(content=file_content))

            note.append("file_content", True)
            assert note.content == f"{file_content}\n{file_content}"

    def test_print(self, capsys, make_markdown_file):
        file_content = "file_content"
        note = Note(make_markdown_file(content=file_content))

        note.print()
        captured = capsys.readouterr()

        assert captured.out == f"{file_content}\n"

    class TestSub:
        def test_regular(self, make_markdown_file):
            file_content = "file_content"
            note = Note(make_markdown_file(content=file_content))

            note.sub(file_content, "new_content")
            assert note.content == "new_content"

        def test_regex(self, make_markdown_file):
            file_content = "file_content"
            note = Note(make_markdown_file(content=file_content))
            ic(note.content)
            note.sub(r"(.*)_", "new_", True)
            assert note.content == "new_content"

    def test_write(self, make_markdown_file):
        note_path = make_markdown_file(content="")
        note = Note(note_path)
        new_content = "file_content"
        note.append(new_content, True)

        note.write()

        with open(note_path) as file:
            file_content = file.read()

        assert f"\n{new_content}" == f"{file_content}"


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
