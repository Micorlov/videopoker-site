"""The registry publishes seventy languages and refuses one."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from i18n import locales  # noqa: E402


def registry(languages):
    doc = {
        "excluded": ["he", "iw"],
        "default": {"code": "en", "name": "English", "english_name": "English",
                    "dir": "ltr", "og_locale": "en_GB", "hreflang": ["en"]},
        "languages": languages,
    }
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(doc, handle)
    handle.close()
    return handle.name


def language(code, hreflang=None):
    return {"code": code, "name": code, "english_name": code, "dir": "ltr",
            "og_locale": "xx_XX", "hreflang": hreflang or [code]}


class TestShippedRegistry(unittest.TestCase):
    def test_loads_english_plus_the_other_languages(self):
        default, others = locales.load()
        self.assertEqual(default.code, "en")
        self.assertEqual(len(others), 70)

    def test_ships_no_hebrew_anywhere(self):
        default, others = locales.load()
        for loc in [default] + others:
            for tag in (loc.code,) + loc.hreflang:
                self.assertNotIn(tag.lower().split("-")[0], {"he", "iw"})

    def test_covers_the_play_locales_through_hreflang(self):
        _, others = locales.load()
        tags = {t for loc in others for t in loc.hreflang}
        for play_locale in ["pt-BR", "zh-TW", "es-419", "fr-CA", "fa-AF", "nb"]:
            self.assertIn(play_locale, tags)


class TestExclusion(unittest.TestCase):
    def test_refuses_a_hebrew_language(self):
        with self.assertRaises(SystemExit):
            locales.load(registry([language("he")]))

    def test_refuses_the_deprecated_play_tag(self):
        with self.assertRaises(SystemExit):
            locales.load(registry([language("iw-IL")]))

    def test_refuses_hebrew_hidden_in_an_hreflang_list(self):
        with self.assertRaises(SystemExit):
            locales.load(registry([language("es", ["es", "he-IL"])]))

    def test_refuses_hebrew_asked_for_on_the_command_line(self):
        _, others = locales.load()
        with self.assertRaises(SystemExit):
            locales.select("he", others)


class TestSelect(unittest.TestCase):
    def setUp(self):
        _, self.all = locales.load()

    def test_all_means_every_available_language(self):
        self.assertEqual(locales.select("all", self.all), self.all)

    def test_a_list_picks_those_languages_in_order(self):
        self.assertEqual([l.code for l in locales.select("ja,es", self.all)], ["ja", "es"])

    def test_an_unknown_language_is_refused_rather_than_ignored(self):
        with self.assertRaises(SystemExit):
            locales.select("es,klingon", self.all)
