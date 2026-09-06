import pathlib

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

    def test_is_md_file(self, make_markdown_file):
        note_path = make_markdown_file("", filename="note.md")
        assert Note._is_md_file(note_path)

        assert not Note._is_md_file("not_note.md")

        note_path = make_markdown_file("", filename="not_note.txt")
        assert not Note._is_md_file(note_path)


class TestNotes:
    class TestsInit:
        def test_single(self, make_markdown_file):
            temp_file = make_markdown_file(content="")

            Note(temp_file)

        def test_dir(self, tmp_path, make_markdown_file):
            make_markdown_file("", filename="note1.md")
            notes = Notes(tmp_path)

            assert len(notes) == 1

            make_markdown_file("", filename="note2.md")
            notes = Notes(tmp_path)

            assert len(notes) == 2

    class TestAdd:
        def test_add_file(self, tmp_path, make_markdown_file):
            make_markdown_file("", filename="note1.md")
            notes = Notes(tmp_path)
            assert len(notes) == 1

            note_path = make_markdown_file("", filename="note2.md")
            notes.add(note_path)
            assert len(notes) == 2

        def test_add_dir_recursive(self, tmp_path, make_markdown_file):
            notes = Notes(tmp_path)
            assert len(notes) == 0

            make_markdown_file("", filename="note1.md")
            make_markdown_file("", filename="note2.md")
            notes.add(tmp_path, True)
            assert len(notes) == 2

        def test_add_dir_not_recursive(self, tmp_path, make_markdown_file):
            notes = Notes(tmp_path)
            assert len(notes) == 0

            make_markdown_file("", filename="note1.md")
            make_markdown_file("", filename="note2.md")
            file_path = tmp_path / "nested_dir" / "note3.md"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("", encoding="utf-8")

            notes = Notes(tmp_path, False)
            assert len(notes) == 2

    class TestAppend:
        def test_append(self, tmp_path, make_markdown_file):
            make_markdown_file("", filename="note1.md")
            make_markdown_file("", filename="note2.md")
            notes = Notes(tmp_path)

            new_content = "new_content"
            notes.append(new_content, False)

            for note in notes.notes:
                assert note.content == f"\n{new_content}"

        def test_allow_repeat(self, tmp_path, make_markdown_file):
            file_content = "file_content"
            make_markdown_file(file_content, filename="note1.md")
            make_markdown_file(file_content, filename="note2.md")
            notes = Notes(tmp_path)

            new_content = "file_content"
            notes.append(new_content, True)

            for note in notes.notes:
                assert note.content == f"{file_content}\n{file_content}"

    class TestFilter:
        def test_starts_with(self, tmp_path, make_markdown_file):
            make_markdown_file("", filename="note1.md")
            flagged_note_path = make_markdown_file("", filename="flagged_note2.md")
            notes = Notes(tmp_path)
            assert len(notes) == 2

            notes.filter(starts_with="flagged")
            assert len(notes) == 1
            assert notes.notes[0].path == flagged_note_path

        def test_ends_with(self, tmp_path, make_markdown_file):
            make_markdown_file("", filename="note1.md")
            flagged_note_path = make_markdown_file("", filename="note2_flagged.md")
            notes = Notes(tmp_path)
            assert len(notes) == 2

            notes.filter(ends_with="flagged.md")
            assert len(notes) == 1
            assert notes.notes[0].path == flagged_note_path

        def test_pattern(self, tmp_path, make_markdown_file):
            make_markdown_file("", filename="note1.md")
            flagged_note_path = make_markdown_file("", filename="note2_flagged.md")
            notes = Notes(tmp_path)
            assert len(notes) == 2

            notes.filter(pattern=r"(.*)_(.*)")
            assert len(notes) == 1
            assert notes.notes[0].path == flagged_note_path

        # def test_has_meta(self, tmp_path, make_markdown_file):
        #     pass

    def test_write(self, tmp_path, make_markdown_file):
        make_markdown_file("", filename="note1.md")
        make_markdown_file("", filename="note2.md")
        notes = Notes(tmp_path)

        new_content = "file_content"
        notes.append(new_content, True)

        notes.write()

        for note in notes.notes:
            with open(note.path) as file:
                file_content = file.read()

            assert f"\n{new_content}" == f"{file_content}"
