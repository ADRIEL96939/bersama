#!/usr/bin/env python3
"""
Bersama evaluation harness.

Run:  python eval.py           # English benchmark (data/benchmark.json)
      python eval.py id        # Bahasa Indonesia benchmark (data/benchmark_id.json)

Loads the labelled benchmark for the chosen language and reports metrics you can
quote as verification evidence in the application:

  1. Retrieval accuracy    - does the top passage belong to the expected topic?
  2. Grounded-answer check  - does the answer contain the expected key fact?
  3. No-answer guard        - are clearly out-of-scope questions declined?

It also prints a per-topic breakdown and names the active retriever, and shows a
separate "known-hard" out-of-scope set (questions that share common words like
"Taiwan" with the corpus) so the numbers stay honest.

This runs offline (no API key needed): for a language whose passages are in the
knowledge base (English, Indonesian), questions are retrieved and answered
directly in that language, so the score reflects the real offline experience.
"""

import json
import os
import sys
from collections import defaultdict

from src.pipeline import Bersama
from src import config


def benchmark_path(lang: str) -> str:
    name = "benchmark.json" if lang == "en" else f"benchmark_{lang}.json"
    return os.path.join(config.DATA_DIR, name)


def load_benchmark(lang: str):
    path = benchmark_path(lang)
    if not os.path.exists(path):
        raise SystemExit(f"No benchmark file for language '{lang}': {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(lang: str = "en") -> None:
    bot = Bersama()
    data = load_benchmark(lang)
    in_scope = data["in_scope"]

    # The retriever that will actually serve this language (with fallback).
    serve_lang = lang if lang in bot.retrievers else config.KB_LANGUAGE
    retriever = bot.retrievers[serve_lang]

    print(f"Evaluation language: {lang}  (answered in: {serve_lang})")
    print(f"Active retriever: {retriever.name} "
          f"(multilingual={retriever.multilingual}, "
          f"min_relevance={retriever.min_relevance})")
    print(f"Knowledge base: {bot.coverage['total']} passages "
          f"across {bot.languages} | Benchmark: {len(in_scope)} in-scope questions")
    if not retriever.multilingual:
        print("Note: install sentence-transformers + set BERSAMA_RETRIEVER=embedding")
        print("      for semantic retrieval, which improves the harder cases below.")
    print()

    # --- 1 & 2: retrieval accuracy and grounded-answer content check ---------
    topic_total = defaultdict(int)
    topic_correct = defaultdict(int)
    retrieval_correct = 0
    content_correct = 0
    failures = []

    for item in in_scope:
        q = item["question"]
        expected = item["expected_topic"]
        acceptable = set(item.get("acceptable_topics", [expected]))
        result = bot.answer(q, user_lang=lang)
        top = result["retrieval"][0] if result["retrieval"] else None
        got = top["topic"] if top else "none"

        topic_total[expected] += 1
        if got in acceptable:
            retrieval_correct += 1
            topic_correct[expected] += 1
        else:
            failures.append((q, expected, got))

        answer_l = result["answer"].lower()
        if any(kw.lower() in answer_l for kw in item.get("expect_contains", [])):
            content_correct += 1

    n = len(in_scope)
    print("=" * 70)
    print("1. RETRIEVAL ACCURACY (top-1 topic)  and  2. GROUNDED-ANSWER CHECK")
    print("=" * 70)
    for topic in sorted(topic_total):
        c, t = topic_correct[topic], topic_total[topic]
        print(f"  {topic:18} {c}/{t}  ({c/t*100:.0f}%)")
    print(f"\n  Overall retrieval top-1 accuracy: {retrieval_correct}/{n} = {retrieval_correct/n*100:.1f}%")
    print(f"  Grounded-answer key-fact present: {content_correct}/{n} = {content_correct/n*100:.1f}%")
    if failures:
        print("\n  Misrouted questions:")
        for q, exp, got in failures:
            print(f"    - {q}  (expected {exp}, got {got})")

    # --- 3: no-answer guard --------------------------------------------------
    def decline_rate(questions):
        declined = 0
        misses = []
        for q in questions:
            r = bot.answer(q, user_lang=lang)
            if not r["grounded"]:
                declined += 1
            else:
                misses.append(q)
        return declined, len(questions), misses

    clear_d, clear_n, clear_miss = decline_rate(data["out_of_scope_clear"])
    hard_d, hard_n, hard_miss = decline_rate(data["out_of_scope_hard"])

    print()
    print("=" * 70)
    print("3. NO-ANSWER GUARD")
    print("=" * 70)
    print(f"  Clearly unrelated declined: {clear_d}/{clear_n} = {clear_d/clear_n*100:.0f}%")
    for q in clear_miss:
        print(f"    - answered unexpectedly: {q}")
    print(f"  Known-hard (shared words) declined: {hard_d}/{hard_n} = {hard_d/hard_n*100:.0f}%")
    print("    (shared-vocabulary cases; embeddings handle these better than keywords)")

    # --- citable summary -----------------------------------------------------
    print()
    print("=" * 70)
    print("SUMMARY (citable)")
    print("=" * 70)
    print(f"  Language:                  {lang}")
    print(f"  Retriever:                 {retriever.name}")
    print(f"  In-scope questions:        {n}")
    print(f"  Retrieval top-1 accuracy:  {retrieval_correct/n*100:.1f}%")
    print(f"  Grounded key-fact present: {content_correct/n*100:.1f}%")
    print(f"  Out-of-scope declined:     {clear_d}/{clear_n} clear, {hard_d}/{hard_n} hard")


if __name__ == "__main__":
    language = sys.argv[1] if len(sys.argv) > 1 else "en"
    run(language)
