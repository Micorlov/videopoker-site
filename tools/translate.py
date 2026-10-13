"""Fill content/i18n/ with the site's text in every language but Hebrew.

This is the only thing that calls a translation API, and it never runs in a
build or in CI. It writes after every batch, so it can be stopped at any point
and picked up again: what is already in the memory is never paid for twice.

    python3 tools/translate.py --estimate              what it would cost
    python3 tools/translate.py --locales es,fr         those two languages
    python3 tools/translate.py --locales all           all seventy
    python3 tools/translate.py --locales all --budget 20   stop after $20
    python3 tools/translate.py --audit                 coverage per language
    python3 tools/translate.py --prune                 drop text no page uses

Then run build.py: a language appears on the site as soon as its file covers
every page. Commit content/i18n/ — the build reads it and nothing else.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
from i18n import locales, memory, providers, segments  # noqa: E402

# Small enough that one reply fits comfortably in the output budget, and that a
# failure costs little to retry.
BATCH = 25

# claude-opus-5-5, $ per million tokens. Used for the estimate and the budget
# stop only; the invoice is Anthropic's.
PRICE_IN, PRICE_OUT = 4.00, 20.00


def source_text():
    """Every English string the site publishes, in page order."""
    build.collect()
    found, seen = [], set()
    for text in build.CHROME:
        seen.add(text)
        found.append(text)
    for path, page in build.PAGES.items():
        if not build.translatable(path, page):
            continue
        for s in segments.extract(page):
            if s not in seen:
                seen.add(s)
                found.append(s)
    return found


def batches(items, size=BATCH):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def estimate(api, sources, languages):
    """Tokens and dollars for translating everything that is missing."""
    glossary = segments.PROTECTED
    sample = languages[0]
    tokens_in = sum(providers.count_tokens(api, b, sample, glossary) for b in batches(sources))
    # A translation runs about as long as its source, and output is the larger
    # share of the bill, so this is the number that matters.
    tokens_out = tokens_in
    per_language = tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT
    return tokens_in, per_language


def fill(api, sources, locale, args, spent):
    """Translate what this language is missing. Returns dollars spent."""
    table = memory.load(locale.code)
    missing = [s for s in sources if memory.key(s) not in table]
    if not missing:
        print(f"  {locale.code:8} complete ({len(table)} strings)")
        return 0.0
    done, cost = 0, 0.0
    for batch in batches(missing, args.batch):
        if args.budget and spent + cost >= args.budget:
            print(f"  {locale.code:8} stopped at the budget")
            break
        try:
            out, usage = providers.translate_batch(api, batch, locale, segments.PROTECTED, args.model)
        except providers.TranslationError as exc:
            print(f"  {locale.code:8} batch failed, skipped: {exc}")
            continue
        table.update({memory.key(src): dst for src, dst in zip(batch, out)})
        memory.save(locale.code, table)  # after every batch: this is resumable
        done += len(batch)
        cost += usage.input_tokens / 1e6 * PRICE_IN + usage.output_tokens / 1e6 * PRICE_OUT
        print(f"  {locale.code:8} {done}/{len(missing)}  ${cost:,.2f}", end="\r", flush=True)
    print(f"  {locale.code:8} {done}/{len(missing)} new strings, ${cost:,.2f}        ")
    return cost


def audit(sources, default, languages):
    live = {memory.key(s) for s in sources}
    print(f"{len(sources)} strings on the site, {len(live)} unique\n")
    for loc in languages:
        table = memory.load(loc.code)
        if not table:
            continue
        have = len(live & set(table))
        orphans = len(set(table) - live)
        state = "publishes" if have == len(live) else f"{len(live) - have} missing"
        print(f"  {loc.code:8} {have:5}/{len(live)}  {state}"
              + (f", {orphans} stale" if orphans else ""))


def prune(sources, languages):
    live = {memory.key(s) for s in sources}
    for loc in languages:
        table = memory.load(loc.code)
        kept = {k: v for k, v in table.items() if k in live}
        if len(kept) != len(table):
            memory.save(loc.code, kept)
            print(f"  {loc.code:8} dropped {len(table) - len(kept)} stale strings")
    memory.save_sources({memory.key(s): s for s in sources})
    print(f"  sources   {len(live)} strings")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--locales", help='"all", or a comma-separated list such as es,fr,ja')
    ap.add_argument("--model", default=providers.MODEL,
                    help="the translating model (default %(default)s)")
    ap.add_argument("--batch", type=int, default=BATCH, help="strings per request")
    ap.add_argument("--budget", type=float, help="stop once this many dollars are spent")
    ap.add_argument("--estimate", action="store_true", help="price the job, translate nothing")
    ap.add_argument("--audit", action="store_true", help="what each language has")
    ap.add_argument("--prune", action="store_true", help="forget text no page uses")
    args = ap.parse_args()

    default, languages = locales.load()
    sources = source_text()

    if args.audit:
        return audit(sources, default, languages)
    if args.prune:
        return prune(sources, languages)

    chosen = locales.select(args.locales, languages) if args.locales else languages
    api = providers.client()

    if args.estimate:
        tokens, each = estimate(api, sources, chosen)
        print(f"{len(sources)} strings, {tokens:,} input tokens per language")
        print(f"about ${each:,.2f} a language with {args.model}, "
              f"${each * len(chosen):,.2f} for {len(chosen)}")
        print("a language already in content/i18n/ only pays for what is new")
        return

    if not args.locales:
        ap.error("say which languages: --locales all, or --locales es,fr")

    print(f"{len(sources)} strings, {len(chosen)} languages, {args.model}")
    spent = 0.0
    for loc in chosen:
        spent += fill(api, sources, loc, args, spent)
        if args.budget and spent >= args.budget:
            print(f"budget reached: ${spent:,.2f}")
            break
    memory.save_sources({memory.key(s): s for s in sources})
    print(f"${spent:,.2f} spent. Run python3 build.py to publish what is ready.")


if __name__ == "__main__":
    main()
