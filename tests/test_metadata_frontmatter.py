from pyomd.metadata import Frontmatter


class TestFrontmatter:
    class Test_to_string:
        def test_empty(self):
            meta = Frontmatter("")

            assert meta.to_string() == ""
