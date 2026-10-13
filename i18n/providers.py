"""The translation backends that fill the memory. Never imported by a build.

Only one backend is implemented — Claude, through the official Anthropic SDK —
because it is the one that covers all seventy languages and handles editorial
prose rather than UI strings. `translate_batch` is the whole interface a second
backend would have to satisfy: a list of English strings in, the same number of
strings out, in order.
"""
import json
import re

MODEL = "claude-opus-5-5"

SYSTEM = """You are translating a website for Orlov Games, a one-person Android game \
studio. The pages are editorial prose about card and casino games: paytables, odds, \
probability, strategy and the mathematics behind the machines, plus the studio's app \
listings and legal pages.

You will be given a JSON array of English strings. Reply with a JSON array of exactly \
the same length, in the same order, each string translated into {language} ({code}).

Rules:
- Reply with the JSON array and nothing else. No preamble, no code fence, no commentary.
- Translate every element, even a single word or a fragment. A fragment is part of a \
sentence that continues in the next element; translate it as a fragment.
- Keep every number, percentage, odds ratio, paytable value and currency exactly as it \
is. "9/6 Jacks or Better" keeps "9/6". Do not convert units or reformat numbers.
- Leave these names in English: {glossary}.
- Keep the register of the original: plain, precise, unhurried. Explain the game terms \
the way a player of that language's games would say them, not by transliterating the \
English.
- Keep the length close to the English. Several of these strings are page titles and \
search-result descriptions that are cut off when they run long.
- If a string is a proper noun, a package name or has nothing to translate, return it \
unchanged."""


class TranslationError(RuntimeError):
    pass


def client():
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depends on the machine
        raise SystemExit(
            "tools/translate.py needs the Anthropic SDK: pip install anthropic"
        ) from exc
    return anthropic.Anthropic()


def _parse(reply, expected):
    """The model's reply -> the list of translations, or an error worth retrying."""
    text = reply.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        out = json.loads(text)
    except ValueError as exc:
        raise TranslationError(f"reply was not JSON: {exc}") from exc
    if not isinstance(out, list) or len(out) != expected:
        raise TranslationError(f"expected {expected} strings, got {len(out) if isinstance(out, list) else type(out).__name__}")
    if not all(isinstance(s, str) and s.strip() for s in out):
        raise TranslationError("reply contained a non-string or empty translation")
    return out


def translate_batch(api, texts, locale, glossary, model=MODEL):
    """One request: len(texts) English strings -> the same number in one language."""
    response = api.messages.create(
        model=model,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=[{
            "type": "text",
            "text": SYSTEM.format(language=locale.english_name, code=locale.code,
                                  glossary=", ".join(sorted(glossary))),
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": json.dumps(texts, ensure_ascii=False)}],
    )
    if response.stop_reason == "refusal":
        raise TranslationError(f"refused: {getattr(response.stop_details, 'category', None)}")
    if response.stop_reason == "max_tokens":
        raise TranslationError("ran out of output tokens — send a smaller batch")
    body = "".join(b.text for b in response.content if b.type == "text")
    return _parse(body, len(texts)), response.usage


def count_tokens(api, texts, locale, glossary, model=MODEL):
    """What one batch would cost to send, without sending it."""
    return api.messages.count_tokens(
        model=model,
        system=SYSTEM.format(language=locale.english_name, code=locale.code,
                             glossary=", ".join(sorted(glossary))),
        messages=[{"role": "user", "content": json.dumps(texts, ensure_ascii=False)}],
    ).input_tokens
