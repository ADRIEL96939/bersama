# Bersama - Development Plan and Task Breakdown

*2026 Presidential Hackathon International Track. Theme: Digital Inclusion in the AI Era.*

This document is the development plan and task breakdown for Bersama. It states
what is already built, how long the remaining work takes, and how the project develops after the competition. It is
written to match the Feasibility criterion (maturity of the solution, overview
and development plan, future plans) and the finals Implementation and
Verification criterion (progress, completeness, verification status).

---

## 1. Project snapshot

Bersama ("together" in Bahasa Indonesia and Malay) is an AI public-service
companion for migrant workers in Taiwan. A worker asks a question in their own
language, and Bersama retrieves the relevant official rule, answers in plain
language grounded in that source, cites it, and can draft a real application
form. It runs offline with no external service required, and turns into a fluent
assistant when a language model is connected.

The system covers four high-need topics: employer transfer, wage complaints,
National Health Insurance (NHI), and visa and residency basics. It works today
in three languages (English, Bahasa Indonesia, Vietnamese), which are the three
largest migrant-worker groups in Taiwan.

Current status: a working end-to-end prototype exists and is tested. The core
build is complete. Remaining work before submission is verification, the demo
video, and light polish.

---

## 2. Scope committed for the July 31 submission

The submission proves one full flow, end to end, with no gaps:

1. A worker asks a question in a migrant language (Indonesian or Vietnamese).
2. Bersama retrieves the matching official source from a curated knowledge base.
3. It answers in plain language, in the worker's language, grounded in that
   source, and cites it.
4. It declines honestly when it has no verified source, instead of guessing.
5. It drafts one real application (an employer-transfer request) from a short
   conversation, as a reviewable draft that is never auto-submitted.

This scope is intentionally narrow and fully working, rather than broad and
partly working. That is the right trade-off for a prototype judged on maturity
and verifiability.

---

## 3. Task breakdown

Status legend: Done = built and tested. In progress = partially built.
To do = not started. Estimates are for the remaining work only.

### Workstream A: Knowledge base

| Task | Status | Est. remaining |
|---|---|---|
| Curate English passages from official sources (4 topics) | Done (52 passages) | - |
| Tag each passage with topic, source title, source URL | Done | - |
| Translate knowledge base to Bahasa Indonesia | Done (52 passages) | - |
| Translate knowledge base to Vietnamese | Done (52 passages) | - |
| Native-speaker review of Indonesian and Vietnamese text | To do | 3-4 days (needs a reviewer) |
| Expand English base toward 60 passages for edge cases | In progress | 2-3 days |

### Workstream B: Retrieval and answering (RAG)

| Task | Status | Est. remaining |
|---|---|---|
| Keyword retriever (TF-IDF), offline, zero setup | Done | - |
| Semantic retriever (multilingual embeddings), optional | Done | - |
| Language-aware routing (answer in the worker's language) | Done | - |
| Per-language stopwords so the no-answer guard works | Done | - |
| Grounded answer generation with citations | Done | - |
| No-answer guard (decline when no verified source) | Done | - |
| Optional language-model path for fluent answers | Done | - |

### Workstream C: Form co-pilot

| Task | Status | Est. remaining |
|---|---|---|
| Employer-transfer draft flow (draft only, never submits) | Done | - |
| Confirm exact fields against the current official form | To do | 1 day |
| Add a second form (wage-complaint intake) | To do | 2 days |

### Workstream D: Evaluation

| Task | Status | Est. remaining |
|---|---|---|
| 112-question labelled benchmark (English) | Done | - |
| Parallel benchmark (Indonesian, Vietnamese) | Done | - |
| Harness reporting retrieval, grounding, decline rates | Done | - |
| Re-run with embeddings on for the strongest numbers | To do | 0.5 day |

### Workstream E: Interfaces

| Task | Status | Est. remaining |
|---|---|---|
| Command-line demo (good for screen recording) | Done | - |
| Web chat page (accessible, language pills, sources) | Done | - |
| Language switch in both interfaces | Done | - |

### Workstream F: Submission deliverables

| Task | Status | Est. remaining |
|---|---|---|
| Application form content (Section VIII) | Done (draft) | 0.5 day to finalize |
| Development plan and task breakdown (this document) | Done | - |
| 2-minute demo video | To do | 1 day (script is ready) |
| Public GitHub repository | In progress | 0.5 day |

---

## 4. What is completed

The core product is built and tested. Concretely: a 52-passage curated knowledge
base in three languages (156 passages total), each passage tied to an official
source; a language-aware RAG pipeline that retrieves and answers in the worker's
own language offline; a grounded-answer generator that cites sources and declines
when it has none; a form co-pilot that drafts an employer-transfer request; a
command-line demo and an accessible web page; and a 112-question evaluation
benchmark in each language with a harness that produces citable accuracy numbers.

On the default offline keyword retriever, the benchmark reports retrieval top-1
accuracy and grounded key-fact presence of roughly 82% / 78% (English),
88% / 84% (Indonesian), and 87% / 87% (Vietnamese). These are honest numbers on a
deliberately hard, paraphrase-rich set; the optional semantic retriever raises
the harder cases further.

---

## 6. Timeline aligned to the competition schedule

| Phase | Dates (from handbook) | Bersama focus |
|---|---|---|
| Submission | now to July 31 | Record video, publish repo, finalize form, eligibility check |
| Preliminary review | Aug 6 to Aug 16 | Respond to any clarifications; keep repo stable |
| Results announced | late Aug | If selected, plan the mentorship asks |
| Mentorship | mid-Sep to mid-Oct | Native-speaker verification, field validation with an NGO or service center, second form, embeddings in production |
| Final review | late Oct | Live system demo of the full flow plus verification results |
| Awards | early to mid Dec | - |

The mentorship period is where the verified-content and field-validation work
belongs, because the competition explicitly offers reviewers, technical
consultants, and field-validation support to selected teams. The plan is built to
use that support rather than to require it beforehand.

---

## 7. Verification plan (for the finals Implementation and Verification score)

Verification does not depend on a partner and can be shown at the finals:

- Automated: the 112-question benchmark per language, re-runnable on demand,
  reporting retrieval accuracy, grounded key-fact presence, and out-of-scope
  decline rates. This is the primary, reproducible evidence.
- Content: every passage is traceable to a named official source (Ministry of
  Labor, NHIA, National Immigration Agency, and the 1955 hotline guidance), so
  answers can be checked against the source of record.
- Human review: native speakers confirm the translated passages read correctly;
  an NGO caseworker or the local labor bureau reviews sample answers and the form
  draft for correctness.
- Field validation (if selected): a small supervised pilot with real workers
  through a migrant-service center, captured as usage notes and corrections.

---

## 8. Future development (post-competition roadmap)

- Voice-first interaction, so workers can speak rather than type, which matters
  for accessibility and for lower-literacy users.
- Two more languages (Thai and Filipino), which is now a repeatable recipe: a
  translated knowledge-base file, a stopword list, and a benchmark file, with no
  code changes.
- More forms beyond employer transfer (wage-complaint intake, NHI enrollment
  checks), always draft-only with a human in the loop.
- A lightweight content-update process so passages stay current as wages, fees,
  and rules change each year.
- Partnership with a migrant-service NGO or a local labor bureau for hosting,
  distribution, and ongoing content verification.

---

## 9. Risks and mitigations

- Incorrect or outdated content. Mitigation: strict grounding, source citation
  on every answer, a no-answer guard, and native-speaker plus caseworker review
  before any real use.
- Over-trust in an AI answer. Mitigation: Bersama frames answers as a starting
  point that points to official sources, always surfaces the free 1955 hotline,
  and never submits a form on the worker's behalf.
- Translation quality. Mitigation: translated passages are marked unverified
  until a native speaker signs off; the facts come from the same official
  sources as the English set.
- Scope creep before the deadline. Mitigation: the committed scope is one full
  flow in two languages across four topics, and it is already working.
