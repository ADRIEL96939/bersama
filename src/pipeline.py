"""
The one full flow, wired together, now language-aware.

The knowledge base can hold passages in several languages (English in
knowledge_base.json, Bahasa Indonesia in knowledge_base_id.json, and so on). We
build one retriever per language. When a worker asks in a language we have
passages for, we retrieve and answer directly in that language, with no
translation step at all. If we do not have that language, we fall back to
English: translate the question in (if the LLM is on), retrieve, then translate
the answer back.

  question (lang L)
    -> if we have passages in L:  retrieve in L -> answer in L        (no translation)
    -> else:                      [translate to English] -> retrieve  -> [translate back]

Build the Bersama object once, then call answer() as many times as you like.
"""

from . import config
from . import generation
from . import translation
from .knowledge_base import load_passages, coverage_summary, group_by_language
from .retrieval import build_retriever


class Bersama:
    def __init__(self):
        self.passages = load_passages()
        self.coverage = coverage_summary(self.passages)

        # One retriever per language present in the knowledge base.
        self.by_language = group_by_language(self.passages)
        self.retrievers = {
            lang: build_retriever(subset) for lang, subset in self.by_language.items()
        }
        self.languages = sorted(self.retrievers.keys())
        # A representative retriever name for status display.
        any_lang = config.KB_LANGUAGE if config.KB_LANGUAGE in self.retrievers else self.languages[0]
        self.retriever_name = self.retrievers[any_lang].name

    def _pick_language(self, user_lang: str) -> str:
        """Answer in the worker's own language if we have passages for it,
        otherwise fall back to the knowledge-base default (English)."""
        if user_lang in self.retrievers:
            return user_lang
        if config.KB_LANGUAGE in self.retrievers:
            return config.KB_LANGUAGE
        return self.languages[0]

    def answer(self, question: str, user_lang: str = "en") -> dict:
        """Answer one question, in the worker's language where possible."""
        kb_lang = self._pick_language(user_lang)
        retriever = self.retrievers[kb_lang]
        same_language = (kb_lang == user_lang)

        # Step 4 (in): only translate before retrieval when we are falling back
        # to another language AND the retriever is not multilingual.
        if same_language or retriever.multilingual:
            query = question
        else:
            query = translation.to_kb_language(question, user_lang)

        # Step 2: retrieve.
        retrieved = retriever.retrieve(query, k=config.TOP_K)

        # Step 3: ground an answer (or decline), using this retriever's threshold.
        result = generation.generate_answer(
            question, retrieved, min_relevance=retriever.min_relevance, lang=kb_lang
        )

        # Step 4 (out): if the passages were not in the worker's language, translate
        # the answer back. (Grounded answers built from same-language passages are
        # already in the worker's language.)
        if same_language:
            answer_text = result["answer"]
        else:
            answer_text = translation.from_kb_language(result["answer"], user_lang)

        return {
            "question": question,
            "language": user_lang,
            "answered_in": kb_lang,
            "retriever": retriever.name,
            "answer": answer_text,
            "grounded": result["grounded"],
            "sources": result["sources"],
            "retrieval": [
                {"id": rp.passage.id, "topic": rp.passage.topic, "score": round(rp.score, 4)}
                for rp in retrieved
            ],
        }
