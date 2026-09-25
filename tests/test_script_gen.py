import unittest

from script_gen import render_page, rows_from_elements


class ScriptGenTests(unittest.TestCase):
    def test_rows_split_on_break(self):
        lines = ["Label,10,5", "TextBox,80,5", "BREAK", "Button,40,60", ""]
        self.assertEqual(rows_from_elements(lines), [["Label", "TextBox"], ["Button"]])

    def test_render_is_valid_html5_shell(self):
        html = render_page([["Label", "TextBox"], ["Button"]])
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn('<input type="text"', html)
        self.assertIn('<button type="button"', html)
        self.assertEqual(html.count('<div class="row">'), 2)
        self.assertIn("<!-- STYLES -->", html)

    def test_unknown_elements_are_skipped(self):
        # The old generator crashed with NameError on unknown labels.
        html = render_page([["Mystery", "Button"]])
        self.assertIn("Button", html)
        self.assertNotIn("Mystery", html)


if __name__ == "__main__":
    unittest.main()
