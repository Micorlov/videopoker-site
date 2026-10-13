"""The HTML walker must find every visible string and nothing else, and must
put a page back together byte for byte when nothing is translated."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from i18n import segments  # noqa: E402

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Blog &mdash; Orlov Games</title>
<meta name="description" content="Notes on how the games work.">
<meta property="og:title" content="Orlov Games blog">
<meta property="og:url" content="https://michaelorlov.com/blog/">
<meta name="theme-color" content="#07170F">
<script>var t = "do not translate me";</script>
<script type="application/ld+json">
{"@type": "Blog", "name": "Orlov Games blog", "url": "https://michaelorlov.com/blog/",
 "description": "How the games work."}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<h1>Bankroll &amp; session length</h1>
<p>Each coin staked costs 0.0046 coins.</p>
<p>The package is <code>com.micorlov.videopoker</code> on Play.</p>
<img src="/img/a.jpg" alt="Video Poker screenshot" width="4" height="4">
<p>Michael Orlov</p>
<p>  spaced  </p>
<p>99.54%</p>
</body>
</html>"""


class TestExtract(unittest.TestCase):
    def setUp(self):
        self.found = segments.extract(PAGE)

    def test_finds_visible_text(self):
        # Arrange / Act in setUp
        for wanted in ["Blog — Orlov Games", "Skip to content", "Bankroll & session length",
                       "Each coin staked costs 0.0046 coins.", "spaced"]:
            self.assertIn(wanted, self.found)

    def test_finds_translatable_attributes(self):
        self.assertIn("Notes on how the games work.", self.found)
        self.assertIn("Orlov Games blog", self.found)
        self.assertIn("Video Poker screenshot", self.found)

    def test_finds_json_ld_prose(self):
        self.assertIn("How the games work.", self.found)

    def test_skips_script_style_and_code(self):
        self.assertNotIn("do not translate me", self.found)
        self.assertNotIn("com.micorlov.videopoker", self.found)

    def test_skips_urls_machine_values_and_numbers(self):
        for unwanted in ["https://michaelorlov.com/blog/", "#07170F", "99.54%", "#main", "/img/a.jpg"]:
            self.assertNotIn(unwanted, self.found)

    def test_skips_protected_brand_names(self):
        self.assertNotIn("Michael Orlov", self.found)
        self.assertNotIn("Orlov Games", self.found)

    def test_text_split_by_inline_tags_is_one_segment_per_run(self):
        html = "<p>The <a href='/x/'>house edge</a> is small.</p>"
        self.assertEqual(segments.extract(html), ["The", "house edge", "is small."])


class TestRender(unittest.TestCase):
    def test_identity_when_nothing_is_translated(self):
        self.assertEqual(segments.render(PAGE, lambda s: None), PAGE)

    def test_replaces_text_and_escapes_the_result(self):
        out = segments.render("<p>Blog</p>", lambda s: "Caf<é> & more" if s == "Blog" else None)
        self.assertEqual(out, "<p>Caf&lt;é&gt; &amp; more</p>")

    def test_preserves_surrounding_whitespace(self):
        out = segments.render("<p>\n  Blog\n</p>", lambda s: "Blogue" if s == "Blog" else None)
        self.assertEqual(out, "<p>\n  Blogue\n</p>")

    def test_replaces_attributes_and_quotes_the_result(self):
        out = segments.render('<img src="/a.jpg" alt="A shot" width="1" height="1">',
                              lambda s: 'A "shot"' if s == "A shot" else None)
        self.assertIn('alt="A &quot;shot&quot;"', out)
        self.assertIn('src="/a.jpg"', out)

    def test_rewrites_json_ld_prose_but_not_urls(self):
        out = segments.render(PAGE, lambda s: "COMO FUNCIONAN" if s == "How the games work." else None)
        self.assertIn("COMO FUNCIONAN", out)
        self.assertIn("https://michaelorlov.com/blog/", out)

    def test_leaves_a_page_valid_when_only_some_segments_exist(self):
        out = segments.render(PAGE, lambda s: "X" if s == "Skip to content" else None)
        self.assertIn(">X<", out)
        self.assertIn("Bankroll &amp; session length", out)


if __name__ == "__main__":
    unittest.main()
