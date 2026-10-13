"""The translation memory: the only source of translated text a build reads.

A build never calls a translation API. It reads what tools/translate.py has
already written here and committed, so CI is offline, deterministic, and free,
and a page is published in a language only once its text is actually there.

    content/i18n/sources.json   hash -> the English text  (written once)
    content/i18n/<code>.json    hash -> that text in one language

The English source lives in one shared file instead of beside every
translation: at seventy languages, repeating it would be seventy copies of the
whole site in git for nothing.
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "content" / "i18n"
SOURCES = STORE / "sources.json"


def key(text):
    """The stable id of an English segment. Short, but far past collision risk here."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def _write(path, table):
    path.parent.mkdir(parents=True, exist_ok=True)
    # One key per line and sorted, so a day's new posts are a small, readable
    # diff rather than a rewritten file.
    path.write_text(json.dumps(table, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def load_sources():
    return _read(SOURCES)


def save_sources(table):
    _write(SOURCES, table)


def path_for(code):
    return STORE / f"{code}.json"


def load(code):
    return _read(path_for(code))


def save(code, table):
    _write(path_for(code), table)


def translated_languages(locales):
    """The languages that have a memory file at all, in registry order."""
    return [loc for loc in locales if path_for(loc.code).exists()]


class Memory:
    """Lookup for one language, with a tally of what was missing."""

    def __init__(self, code, table=None):
        self.code = code
        self._table = load(code) if table is None else dict(table)
        self.missing = set()

    def get(self, text):
        """The translation, or None when it has not been made yet."""
        hit = self._table.get(key(text))
        if hit is None:
            self.missing.add(text)
        return hit

    def covers(self, texts):
        """True when every segment of a page is translated."""
        return all(key(t) in self._table for t in texts)

    def __len__(self):
        return len(self._table)
