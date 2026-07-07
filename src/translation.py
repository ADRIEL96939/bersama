"""
Step 4: Language handling.

One knowledge base (in English) can serve many languages if we translate the
question into the base language before retrieval, and translate the answer back
into the worker's language afterwards.

- Offline (no LLM): translation is a passthrough. The demo runs in English so
  you can verify the mechanics with zero setup.
- With the LLM enabled: the model does the translation, so a worker can ask in
  Bahasa Indonesia or Vietnamese and read the answer in the same language.

Keeping translation at the edges means the retrieval and grounding logic never
has to think about language.
"""

from . import config
from . import llm


def to_kb_language(text: str, source_lang: str) -> str:
    """Translate the worker's question into the knowledge-base language."""
    if source_lang == config.KB_LANGUAGE:
        return text
    if not llm.is_available():
        # Offline fallback: assume the question is already usable as-is.
        return text
    target = config.SUPPORTED_LANGUAGES.get(config.KB_LANGUAGE, "English")
    system = (
        "You are a translator. Translate the user's message into "
        f"{target}. Reply with only the translation, no notes, no quotes."
    )
    try:
        return llm.complete(system=system, user=text, max_tokens=400)
    except RuntimeError:
        return text


def from_kb_language(text: str, target_lang: str) -> str:
    """Translate the assistant's answer into the worker's language."""
    if target_lang == config.KB_LANGUAGE:
        return text
    if not llm.is_available():
        return text
    target = config.SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    system = (
        "You are a translator for public-service information aimed at migrant "
        f"workers. Translate the message into {target} using simple, everyday "
        "words. Keep any phone numbers, document names, and website links "
        "exactly as written. Reply with only the translation."
    )
    try:
        return llm.complete(system=system, user=text, max_tokens=800)
    except RuntimeError:
        return text
