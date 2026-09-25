import unittest

import css_gen


class SanitizeTests(unittest.TestCase):
    def test_extracts_fenced_css(self):
        reply = "Here you go:\n```css\nbody { color: red; }\n```\nEnjoy"
        self.assertEqual(css_gen.sanitize_css(reply), "body { color: red; }")

    def test_keeps_the_word_css(self):
        # The old code removed every occurrence of "css", corrupting output.
        self.assertIn("css-grid", css_gen.sanitize_css(".css-grid { display: grid; }"))

    def test_cannot_break_out_of_style(self):
        out = css_gen.sanitize_css("a{}</style><script>alert(1)</script>")
        self.assertNotIn("</style", out.lower())
        self.assertNotIn("<script", out.lower())

    def test_strips_remote_imports(self):
        self.assertNotIn("@import", css_gen.sanitize_css("@import url(http://evil/x.css); a{}"))


class AddStylesTests(unittest.TestCase):
    def test_default_css_without_key(self):
        css_gen.GEMINI_API_KEY = ""
        html, source = css_gen.add_styles("<html><head><!-- STYLES --></head><body></body></html>")
        self.assertEqual(source, "default")
        self.assertIn("<style>", html)
        self.assertNotIn("<!-- STYLES -->", html)


if __name__ == "__main__":
    unittest.main()
