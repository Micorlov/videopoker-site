"""Splitting a finished HTML page into translatable segments, and back again.

The pages this walks are the ones build.py generates: every text node and
attribute value goes through html.escape, so a raw "<" or ">" never appears
inside one. That is what makes splitting on /(<[^>]*>)/ safe here, and it is
why this module belongs to this site rather than to the world.

Two entry points, one walk:

    extract(page)      -> the English strings on the page, in order, deduped
    render(page, fn)   -> the page with each string replaced by fn(string)

fn returning None means "not translated yet", and that segment is left exactly
as it was. A page where nothing is translated comes back byte for byte.
"""
import html
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "content" / "i18n" / "glossary.json"

# Nothing inside these elements is prose: scripts, styling, package names and
# code samples all have to survive a translation untouched.
OPAQUE = frozenset({"script", "style", "code", "pre", "textarea", "svg"})

# Attributes a reader actually sees.
TEXT_ATTRS = frozenset({"alt", "title", "aria-label", "placeholder"})

# <meta content="..."> is prose only for these; og:url, theme-color and the
# rest are machine values.
META_NAMES = frozenset({"description", "twitter:title", "twitter:description"})
META_PROPS = frozenset({"og:title", "og:description"})

# The JSON-LD fields that are written for people. Everything else in a block is
# a URL, an @id, a date, a type or a number, and must not be touched.
SCHEMA_KEYS = frozenset({"name", "description", "headline", "articleSection",
                         "alternateName", "caption", "abstract", "disambiguatingDescription"})

TAG = re.compile(r"(<[^>]*>)")
TAG_NAME = re.compile(r"</?\s*([a-zA-Z][\w:-]*)")
ATTR = re.compile(r'([a-zA-Z_:][-\w:.]*)="([^"]*)"')


def _glossary():
    """Names that stay in English in every language: the studio, the author, the stores."""
    terms = {"Orlov Games", "Michael Orlov", "Google Play", "Google", "Android",
             "Michael Orlov, Israel", "RSS", "Play Store", "Play Console"}
    if GLOSSARY.exists():
        terms |= set(json.loads(GLOSSARY.read_text()))
    return frozenset(terms)


PROTECTED = _glossary()


def is_prose(text):
    """True when a string is something a reader reads, not a machine value."""
    s = text.strip()
    if not s or s in PROTECTED:
        return False
    if re.match(r"^(https?:|mailto:|tel:|data:|/|#|\.)", s):
        return False
    return any(unicodedata.category(ch).startswith("L") for ch in s)


def _attrs(tag):
    return {m.group(1).lower(): m.group(2) for m in ATTR.finditer(tag)}


def _meta_is_prose(attrs):
    return (attrs.get("name", "").lower() in META_NAMES
            or attrs.get("property", "").lower() in META_PROPS)


def _translatable_attrs(name, attrs):
    wanted = set(TEXT_ATTRS)
    if name == "meta" and _meta_is_prose(attrs):
        wanted.add("content")
    return wanted


def _rewrite_tag(tag, fn):
    """Run fn over the human-readable attribute values of one start tag."""
    name = TAG_NAME.match(tag)
    if not name or tag.startswith("</"):
        return tag
    wanted = _translatable_attrs(name.group(1).lower(), _attrs(tag))

    def one(m):
        key, raw = m.group(1).lower(), m.group(2)
        if key not in wanted:
            return m.group(0)
        source = html.unescape(raw)
        if not is_prose(source):
            return m.group(0)
        new = fn(source.strip())
        if new is None:
            return m.group(0)
        return f'{m.group(1)}="{html.escape(new, quote=True)}"'

    return ATTR.sub(one, tag)


def _rewrite_text(chunk, fn):
    """Run fn over one text node, keeping the whitespace around it."""
    source = html.unescape(chunk)
    core = source.strip()
    if not is_prose(core):
        return chunk
    new = fn(core)
    if new is None:
        return chunk
    lead = source[:len(source) - len(source.lstrip())]
    trail = source[len(source.rstrip()):]
    return lead + html.escape(new, quote=False) + trail


def _walk_schema(node, fn):
    """Map fn over the prose fields of a JSON-LD block. Returns (node, changed)."""
    changed = False
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key in SCHEMA_KEYS and isinstance(value, str) and is_prose(value):
                new = fn(value.strip())
                out[key] = value if new is None else new
                changed = changed or new is not None
            else:
                out[key], sub = _walk_schema(value, fn)
                changed = changed or sub
        return out, changed
    if isinstance(node, list):
        pairs = [_walk_schema(v, fn) for v in node]
        return [v for v, _ in pairs], any(c for _, c in pairs)
    return node, False


def _rewrite_schema(chunk, fn):
    try:
        doc = json.loads(chunk)
    except ValueError:
        return chunk
    new, changed = _walk_schema(doc, fn)
    if not changed:
        return chunk
    return "\n" + json.dumps(new, ensure_ascii=False, indent=2) + "\n"


def render(page, fn):
    """The page with every translatable segment passed through fn."""
    out = []
    opaque = 0
    schema = False
    for token in TAG.split(page):
        if not token:
            continue
        if token.startswith("<") and token.endswith(">"):
            if not token.startswith("<!"):
                match = TAG_NAME.match(token)
                name = match.group(1).lower() if match else ""
                if token.startswith("</"):
                    if name in OPAQUE:
                        opaque = max(0, opaque - 1)
                        schema = False
                elif name in OPAQUE:
                    opaque += 1
                    schema = name == "script" and "application/ld+json" in token
                elif not opaque:
                    token = _rewrite_tag(token, fn)
            out.append(token)
        elif schema:
            out.append(_rewrite_schema(token, fn))
        elif opaque:
            out.append(token)
        else:
            out.append(_rewrite_text(token, fn))
    return "".join(out)


def extract(page):
    """Every translatable string on the page, first appearance order, deduped."""
    found, seen = [], set()

    def collect(text):
        if text not in seen:
            seen.add(text)
            found.append(text)
        return None

    render(page, collect)
    return found
