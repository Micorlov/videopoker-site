"""Moving a finished page into one language: links, metadata, alternates."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from i18n import locales, pages  # noqa: E402

SITE = "https://michaelorlov.com"


class Base(unittest.TestCase):
    def setUp(self):
        self.en, others = locales.load()
        self.es = next(l for l in others if l.code == "es")
        self.ar = next(l for l in others if l.code == "ar")


class TestPaths(Base):
    def test_pages_move_into_the_language_tree(self):
        for path in ["/", "/blog/", "/VideoPoker/", "/blog/a-post.html", "/feed.xml"]:
            self.assertEqual(pages.localize_path(path, self.es), "/es" + path)

    def test_shared_assets_stay_at_the_root(self):
        for path in ["/img/apps/VideoPoker/icon.jpg", "/style.css", "/fonts/a.woff2", "/sitemap.xml"]:
            self.assertEqual(pages.localize_path(path, self.es), path)

    def test_english_is_the_root_and_moves_nothing(self):
        self.assertEqual(pages.localize_path("/blog/", self.en), "/blog/")


class TestLinks(Base):
    def test_internal_links_are_rewritten(self):
        out = pages.relink('<a href="/VideoPoker/">x</a>', self.es, SITE)
        self.assertEqual(out, '<a href="/es/VideoPoker/">x</a>')

    def test_fragments_and_queries_survive(self):
        out = pages.relink('<a href="/#apps">x</a>', self.es, SITE)
        self.assertEqual(out, '<a href="/es/#apps">x</a>')

    def test_external_links_are_left_alone(self):
        html = '<a href="https://play.google.com/store/apps/details?id=x">x</a>'
        self.assertEqual(pages.relink(html, self.es, SITE), html)

    def test_absolute_site_urls_are_rewritten(self):
        out = pages.relink(f'<link rel="canonical" href="{SITE}/blog/">', self.es, SITE)
        self.assertIn(f'href="{SITE}/es/blog/"', out)

    def test_the_studio_and_the_author_keep_one_id_across_languages(self):
        block = '{"@id": "https://michaelorlov.com/#organization", "url": "https://michaelorlov.com/blog/"}'
        out = pages.relink(block, self.es, SITE)
        self.assertIn('"https://michaelorlov.com/#organization"', out)
        self.assertIn('"https://michaelorlov.com/es/blog/"', out)


class TestAlternates(Base):
    def test_every_language_lists_every_other_and_itself(self):
        block = pages.alternates_block("/blog/", [self.es, self.ar], self.en, SITE)
        self.assertIn('hreflang="es" href="https://michaelorlov.com/es/blog/"', block)
        self.assertIn('hreflang="ar" href="https://michaelorlov.com/ar/blog/"', block)
        self.assertIn('hreflang="en" href="https://michaelorlov.com/blog/"', block)

    def test_play_regional_locales_point_at_their_language(self):
        block = pages.alternates_block("/", [self.es], self.en, SITE)
        self.assertIn('hreflang="es-419" href="https://michaelorlov.com/es/"', block)
        self.assertIn('hreflang="en-IN" href="https://michaelorlov.com/"', block)

    def test_x_default_is_english(self):
        block = pages.alternates_block("/blog/", [self.es], self.en, SITE)
        self.assertIn('hreflang="x-default" href="https://michaelorlov.com/blog/"', block)

    def test_no_hebrew_alternate_is_ever_emitted(self):
        _, others = locales.load()
        block = pages.alternates_block("/", others, self.en, SITE)
        self.assertNotIn('hreflang="he', block)
        self.assertNotIn('hreflang="iw', block)


class TestPicker(Base):
    def test_marks_the_language_being_read(self):
        out = pages.picker_block("/blog/", [self.es], self.en, self.es)
        self.assertIn('href="/es/blog/" lang="es" hreflang="es" dir="ltr" aria-current="true"', out)

    def test_offers_english_from_every_language(self):
        out = pages.picker_block("/blog/", [self.es], self.en, self.es)
        self.assertIn('href="/blog/" lang="en"', out)

    def test_is_absent_when_english_is_the_only_language(self):
        self.assertEqual(pages.picker_block("/", [], self.en, self.en), "")


class TestLanguageMetadata(Base):
    PAGE = ('<html lang="en">\n<meta property="og:locale" content="en_GB">\n'
            '<a href="/blog/">x</a>\n</html>')

    def test_declares_the_language_and_its_direction(self):
        out = pages.localize(self.PAGE, "/", self.ar, FullMemory(), SITE)
        self.assertIn('<html lang="ar" dir="rtl">', out)
        self.assertIn('content="ar_AR"', out)

    def test_a_page_is_not_published_until_its_text_is_there(self):
        self.assertIsNone(pages.localize(self.PAGE, "/", self.es, EmptyMemory(), SITE))


class FullMemory:
    def covers(self, texts):
        return True

    def get(self, text):
        return text.upper()


class EmptyMemory:
    def covers(self, texts):
        return False

    def get(self, text):
        return None
