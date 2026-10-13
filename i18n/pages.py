"""One finished English page -> the same page in one language.

Four things change and nothing else: the words, the internal links, the
language metadata, and the list of languages the page is available in. The
markup, the layout, the images and the Analytics tag are untouched, so a
translated page cannot drift from the English one it came from.

A page is only ever produced for a language whose translation memory covers
every segment on it. A half-translated page would be a worse page than no page,
and seventy copies of untranslated English would be seventy duplicates of the
same site competing with it in search.
"""
import html
import re

from i18n import segments

# Entities that are the same thing in every language and keep one @id across
# the whole site, so search engines read them as a single organisation and
# person rather than seventy of each.
GLOBAL_IDS = ("/#organization", "/#michael")

# A path that is a page gets the language prefix. Images, fonts, the
# stylesheet and the icons are shared by every language and stay at the root.
PAGE_PATH = re.compile(r"^/(?:[\w./-]*/|[\w./-]+\.html|feed\.xml)?$")

URL_ATTRS = frozenset({"href", "src", "action", "content"})

ALTERNATES = "<!-- @alternates -->"
PICKER = "<!-- @langs -->"


def is_page_path(path):
    return bool(PAGE_PATH.match(path)) and not path.startswith(("/img/", "/fonts/"))


def localize_path(path, locale):
    """A site path as it is addressed in one language."""
    return locale.path(path) if is_page_path(path) else path


def _localize_url(url, locale, site):
    """Rewrite one href/src, absolute or relative, leaving anything external alone."""
    if url.startswith(site):
        rest = url[len(site):]
        if any(rest.startswith(gid) for gid in GLOBAL_IDS):
            return url
        base, sep, frag = rest.partition("#")
        return site + localize_path(base, locale) + sep + frag if is_page_path(base) else url
    if not url.startswith("/"):
        return url
    base, sep, frag = url.partition("#")
    return localize_path(base, locale) + sep + frag


def relink(page, locale, site):
    """Every internal link on the page, moved into this language's tree."""
    out = []
    for token in segments.TAG.split(page):
        if token.startswith("<") and token.endswith(">") and not token.startswith("<!"):
            token = segments.ATTR.sub(
                lambda m: (f'{m.group(1)}="{html.escape(_localize_url(html.unescape(m.group(2)), locale, site), quote=True)}"'
                           if m.group(1).lower() in URL_ATTRS else m.group(0)),
                token,
            )
        elif token.strip().startswith("{") and site in token:
            # A JSON-LD block: its urls move too, but its @id values do not.
            token = re.sub(
                re.escape(site) + r'[^"]*',
                lambda m: _localize_url(m.group(0), locale, site),
                token,
            )
        out.append(token)
    return "".join(out)


def _language_meta(page, locale):
    page, swapped = re.subn(
        r'<html lang="en">',
        f'<html lang="{locale.code}" dir="{locale.dir}">',
        page, count=1,
    )
    if not swapped:
        raise SystemExit('a page did not carry <html lang="en"> to replace')
    return page.replace('content="en_GB"', f'content="{locale.og_locale}"', 1)


def alternates_block(path, languages, default, site):
    """<link rel="alternate" hreflang> for every language this page exists in.

    Google reads these as a set, so every page in the set lists every other one
    and itself. x-default points at English, which is also where a Play locale
    with no tree of its own is sent.
    """
    links = []
    for loc in [default] + list(languages):
        href = site + localize_path(path, loc)
        for tag in loc.hreflang:
            links.append(f'<link rel="alternate" hreflang="{tag}" href="{href}">')
    links.append(f'<link rel="alternate" hreflang="x-default" href="{site}{path}">')
    return "\n".join(links)


def picker_block(path, languages, default, current, label="Language"):
    """The footer language menu: plain links, no JavaScript, crawlable."""
    items = []
    for loc in [default] + list(languages):
        href = localize_path(path, loc)
        here = ' aria-current="true"' if loc.code == current.code else ""
        items.append(f'<li><a href="{href}" lang="{loc.code}" hreflang="{loc.code}" '
                     f'dir="{loc.dir}"{here}>{html.escape(loc.name)}</a></li>')
    if len(items) == 1:
        return ""
    return (f'<details class="langpicker">\n'
            f'  <summary aria-label="{html.escape(label, quote=True)}">'
            f'<span lang="{current.code}">{html.escape(current.name)}</span></summary>\n'
            f'  <ul>{"".join(items)}</ul>\n'
            f'</details>')


def finish(page, path, locale, languages, default, site, label="Language"):
    """Fill the alternates and the language menu on a page that is otherwise done."""
    return (page
            .replace(ALTERNATES, alternates_block(path, languages, default, site))
            .replace(PICKER, picker_block(path, languages, default, locale, label)))


def translate(page, memory, texts=None):
    """The page in one language, or None when its text is not all there yet.

    texts is the page's segments when the caller already has them: at seventy
    languages they would otherwise be extracted seventy times per page.
    """
    if not memory.covers(segments.extract(page) if texts is None else texts):
        return None
    return segments.render(page, memory.get)


def localize(page, path, locale, memory, site, texts=None):
    """An English page -> the same page in one language, or None if not ready."""
    done = translate(page, memory, texts)
    if done is None:
        return None
    return _language_meta(relink(done, locale, site), locale)
