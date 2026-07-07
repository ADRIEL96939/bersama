# Bersama - Development Plan

*2026 Presidential Hackathon International Track. Theme: Digital Inclusion in the AI Era.*

This document describes what Bersama is, what is already built, and where the
project goes next. It maps to the Feasibility criterion (maturity of the solution
and future development plans).

---

## 1. Project snapshot

Bersama ("together" in Bahasa Indonesia and Malay) is an AI public-service
companion for migrant workers in Taiwan. A worker asks a question in their own
language, and Bersama retrieves the relevant official rule, answers in plain
language grounded in that source, cites it, and can draft a real application
form. It runs offline with no external service required, and becomes a fluent
assistant when a language model is connected.

The system covers four high-need topics: employer transfer, wage complaints,
National Health Insurance (NHI), and visa and residency basics. It works today in
three languages (English, Bahasa Indonesia, Vietnamese), the three largest
migrant-worker groups in Taiwan. The core build is complete and tested.

---

## 2. What is built today

Bersama is a working end-to-end prototype, not a mock-up. Concretely:

- A curated knowledge base of 52 passages per language (156 total), each tied to
  a named official source (Ministry of Labor, NHIA, National Immigration Agency,
  and the 1955 hotline guidance), across the four topics.
- A language-aware retrieval pipeline that matches a question against passages in
  the worker's own language and answers in that language, fully offline, with no
  translation step.
- Grounded answer generation: every answer is built from retrieved official
  passages and cites them, with a no-answer guard that declines honestly instead
  of guessing when there is no verified source.
- An optional multilingual semantic retriever and an optional language-model path
  for fluent prose, both behind a flag.
- A form co-pilot that turns a short conversation into a drafted
  employer-transfer request, as a reviewable draft that is never auto-submitted.
- A command-line demo and an accessible web page, both with a language switch.
- A 112-question evaluation benchmark in each language with a harness that
  produces reproducible accuracy numbers.

On the default offline keyword retriever, the benchmark reports retrieval top-1
accuracy and grounded key-fact presence of roughly 82% / 78% (English),
88% / 84% (Indonesian), and 87% / 87% (Vietnamese), on a deliberately hard,
paraphrase-rich set. The optional semantic retriever raises the harder cases
further.

---

## 3. What is next

The roadmap builds outward from a working core:

- **Voice-first interaction.** Let workers speak rather than type, which matters
  for accessibility and for lower-literacy users. This is the single highest-value
  direction for reaching the target audience.
- **Two more languages: Thai and Filipino.** Adding a language is now a repeatable
  recipe (see section 4), so this is breadth without re-engineering.
- **More forms.** Beyond employer transfer, add a wage-complaint intake and an NHI
  enrollment check, always draft-only with a person in the loop.
- **Semantic retrieval in production.** Ship the multilingual embedding retriever
  as the default to improve the hardest, shared-vocabulary queries.
- **Ongoing content freshness.** A lightweight process to keep passages current as
  wages, fees, and rules change each year, with native-speaker review of the
  translated content as a continuous quality step.
- **Institutional partnership.** Work with a migrant-service NGO or a local labor
  bureau for hosting, distribution, and long-term content verification.

---

## 4. How the system scales to new languages

Adding a language is intentionally a small, repeatable change with no code edits:

1. Drop in a `knowledge_base_<code>.json` file with the passages in that language.
2. Add a stopword list for that language so the no-answer guard stays calibrated.
3. Add a `benchmark_<code>.json` file to measure quality the same way.

The loader picks up the new language automatically and answers route to it. This
is what makes the "two more languages" roadmap item low-risk.

---

## 5. How correctness is demonstrated

Bersama is built to be verifiable, and the evidence is reproducible on demand:

- The 112-question benchmark per language reports retrieval accuracy, grounded
  key-fact presence, and out-of-scope decline rates, and can be re-run at any time.
- Every passage is traceable to a named official source, so any answer can be
  checked against the source of record.
- The design fails safe: it declines when it has no verified source, surfaces the
  free 1955 hotline, and never submits a form on the worker's behalf.

---

## 6. Risks and mitigations

- Incorrect or outdated content. Mitigation: strict grounding, a source citation
  on every answer, a no-answer guard, and native-speaker plus caseworker review of
  content over time.
- Over-trust in an AI answer. Mitigation: answers are framed as a starting point
  that points to official sources, the 1955 hotline is always surfaced, and no
  form is ever submitted automatically.
- Translation quality. Mitigation: translated passages carry an unverified flag
  until reviewed; the underlying facts come from the same official sources as the
  English set.
