"""
Step 3: Answer generation, grounded in retrieved sources.

The rule that makes Bersama safe on legal and administrative questions: the
answer may only use the passages we retrieved, and it must cite them. If nothing
relevant was retrieved, we say so rather than guess.

- Offline (no LLM): assemble a plain-language answer from the top passages using
  a deterministic template. Because the passages are already in the worker's
  language, so is the answer. Localized labels below keep the whole reply in that
  language.
- With the LLM enabled: hand the passages to the model with a strict instruction
  to answer only from them, in the same language as the question.
"""

from . import config
from . import llm
from .retrieval import RetrievedPassage

# Localized template labels and no-answer text, keyed by language.
# Fall back to English for any language not listed.
STRINGS = {
    "en": {
        "intro": "Here is what the official sources say:",
        "sources": "Sources:",
        "no_answer": (
            "I do not have verified information about that yet. For help, you can "
            "call the free 1955 hotline (dial 1955), which is open 24 hours and has "
            "staff who speak several languages."
        ),
    },
    "id": {
        "intro": "Berikut yang dikatakan oleh sumber resmi:",
        "sources": "Sumber:",
        "no_answer": (
            "Saya belum memiliki informasi yang terverifikasi tentang itu. Untuk "
            "bantuan, Anda bisa menelepon hotline gratis 1955 (tekan 1955), yang "
            "buka 24 jam dan memiliki staf yang berbicara beberapa bahasa."
        ),
    },
    "vi": {
        "intro": "Đây là những gì các nguồn chính thức cho biết:",
        "sources": "Nguồn:",
        "no_answer": (
            "Tôi chưa có thông tin đã được xác minh về điều đó. Để được giúp đỡ, "
            "bạn có thể gọi đường dây nóng miễn phí 1955 (bấm 1955), mở cửa 24 giờ "
            "và có nhân viên nói được nhiều thứ tiếng."
        ),
    },
}


def _s(lang: str, key: str) -> str:
    return STRINGS.get(lang, STRINGS["en"])[key]


def _sources_block(passages: list[RetrievedPassage]) -> str:
    return "\n".join(
        f"[{i}] {rp.passage.source_title} - {rp.passage.source_url}"
        for i, rp in enumerate(passages, start=1)
    )


def _template_answer(passages: list[RetrievedPassage], lang: str) -> str:
    """Deterministic, fully grounded answer used when the LLM is off."""
    parts = [_s(lang, "intro"), ""]
    for i, rp in enumerate(passages, start=1):
        parts.append(f"- {rp.passage.text} [{i}]")
    parts.append("")
    parts.append(_s(lang, "sources"))
    parts.append(_sources_block(passages))
    return "\n".join(parts)


def _llm_answer(question: str, passages: list[RetrievedPassage], lang: str) -> str:
    """Fluent, grounded answer produced by the language model."""
    numbered = "\n\n".join(
        f"[{i}] (source: {rp.passage.source_title})\n{rp.passage.text}"
        for i, rp in enumerate(passages, start=1)
    )
    system = (
        "You help migrant workers in Taiwan understand public services and their "
        "rights. Answer ONLY using the numbered sources provided. Do not add facts "
        "that are not in the sources. If the sources do not answer the question, "
        "say you do not have that information and suggest calling the free 1955 "
        "hotline. Use short sentences and simple words. Answer in the SAME language "
        "as the question. Cite sources inline like [1] or [2]. End with a short "
        "sources list."
    )
    user = f"Question: {question}\n\nSources:\n{numbered}"
    try:
        answer = llm.complete(system=system, user=user, max_tokens=700)
        if answer:
            return answer
    except RuntimeError:
        pass
    return _template_answer(passages, lang)


def generate_answer(question: str, passages: list[RetrievedPassage],
                    min_relevance: float | None = None, lang: str = None) -> dict:
    """Return a grounded answer plus the sources it rests on.

    min_relevance: score cutoff below which we decline.
    lang: language of the retrieved passages, used for localized labels and the
          no-answer message. Defaults to the knowledge-base default language.
    """
    if min_relevance is None:
        min_relevance = config.MIN_RELEVANCE
    if lang is None:
        lang = config.KB_LANGUAGE

    relevant = [rp for rp in passages if rp.score >= min_relevance]

    if not relevant:
        return {"answer": _s(lang, "no_answer"), "grounded": False, "sources": []}

    if llm.is_available():
        answer = _llm_answer(question, relevant, lang)
    else:
        answer = _template_answer(relevant, lang)

    sources = [
        {"title": rp.passage.source_title, "url": rp.passage.source_url}
        for rp in relevant
    ]
    return {"answer": answer, "grounded": True, "sources": sources}
