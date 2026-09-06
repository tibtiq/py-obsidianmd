import pytest
from icecream import ic

ic.configureOutput(includeContext=True)


@pytest.fixture
def make_markdown_file(tmp_path):
    def _create_file(content: str, filename: str = "markdown_note.txt"):
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create_file
