"""The languages the site is published in.

Hebrew is excluded by request. That is enforced here rather than left to the
absence of an entry: EXCLUDED is checked against the registry on load and
against every language code the build is asked for, so a Hebrew tree cannot
reappear through an edit to content/locales.json or a --locales argument.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "content" / "locales.json"

# Hebrew, under every tag it travels by: the modern code, the deprecated one
# Google Play still uses (iw-IL), and both with a region.
EXCLUDED = frozenset({"he", "iw", "he-il", "iw-il"})


class Locale:
    """One published language: a URL prefix, a direction and its hreflang codes."""

    def __init__(self, code, name, english_name, direction, og_locale, hreflang):
        self.code = code
        self.name = name
        self.english_name = english_name
        self.dir = direction
        self.og_locale = og_locale
        self.hreflang = tuple(hreflang)

    @property
    def is_default(self):
        return self.code == "en"

    @property
    def prefix(self):
        """What goes in front of every internal path. Empty for English."""
        return "" if self.is_default else "/" + self.code

    def path(self, url):
        """An English site path -> the same path in this language."""
        return url if self.is_default else self.prefix + url

    def __repr__(self):
        return f"<Locale {self.code}>"


def _excluded(code):
    return code.lower() in EXCLUDED or code.lower().split("-")[0] in EXCLUDED


def _build(entry):
    return Locale(entry["code"], entry["name"], entry["english_name"],
                  entry["dir"], entry["og_locale"], entry["hreflang"])


def load(path=REGISTRY):
    """(default_locale, [other locales]) from the registry, Hebrew refused."""
    doc = json.loads(pathlib.Path(path).read_text())
    default = _build(doc["default"])
    others = [_build(e) for e in doc["languages"]]

    seen = set()
    for loc in [default] + others:
        for code in (loc.code,) + loc.hreflang:
            if _excluded(code):
                raise SystemExit(
                    f"{path}: {loc.code} carries the excluded language tag {code!r}. "
                    "The site does not publish Hebrew."
                )
        if loc.code in seen:
            raise SystemExit(f"{path}: duplicate language {loc.code!r}")
        seen.add(loc.code)
    if default.code != "en":
        raise SystemExit(f"{path}: the default language must be en, not {default.code!r}")
    return default, others


def select(requested, available):
    """Resolve a --locales argument against the languages that have translations.

    "all" is every available language; otherwise a comma-separated list, each
    of which must be both known and not excluded.
    """
    by_code = {loc.code: loc for loc in available}
    if requested in (None, "", "all"):
        return list(available)
    chosen = []
    for code in (c.strip() for c in requested.split(",")):
        if not code:
            continue
        if _excluded(code):
            raise SystemExit(f"--locales {code}: the site does not publish Hebrew.")
        if code not in by_code:
            raise SystemExit(f"--locales {code}: no such language, or it has no translations yet.")
        chosen.append(by_code[code])
    return chosen
