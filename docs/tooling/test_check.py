import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("check", Path(__file__).with_name("check.py"))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class SafetyTests(unittest.TestCase):
    def test_markdown_and_diagram(self):
        soup = check.inspect_html("# Title\n\nA **clear** statement.\n\n![figure](https://adpsagent.com/images/a.svg)")
        self.assertEqual(soup.h1.text, "Title")

    def test_script(self):
        with self.assertRaises(ValueError):
            check.inspect_html('<script>alert(1)</script>')

    def test_event(self):
        with self.assertRaises(ValueError):
            check.inspect_html('<img src="x" onerror="alert(1)">')

    def test_url(self):
        with self.assertRaises(ValueError):
            check.inspect_html('<a href="java&#10;script:alert(1)">x</a>')

    def test_svg_data(self):
        with self.assertRaises(ValueError):
            check.inspect_html('<img src="data:image/svg+xml;base64,abcd">')

    def test_private_path_escape(self):
        with self.assertRaises(ValueError):
            check.local("../outside.md")


if __name__ == "__main__":
    unittest.main()
