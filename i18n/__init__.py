"""Publishing the site in every supported language except Hebrew.

The English pages are generated first, exactly as they always were. Each
language is then a pass over that finished HTML: translate the text, rewrite
the internal links under a /<code>/ prefix, and swap the language metadata.
One code path builds every page, so a language can never drift from English.

    locales    the registry of languages, and the Hebrew exclusion
    memory     the on-disk translation memory, the only thing a build reads
    segments   splitting a page into translatable pieces and putting it back
    pages      an English page -> the same page in one language
    providers  the translation APIs that fill the memory (never run in a build)
"""
