<p align="center">
  <img src="bersama-banner.gif" alt="Bersama - public services for migrant workers in Taiwan, in your language" width="100%">
</p>

# Bersama

An AI public-service companion for migrant workers in Taiwan. A worker asks a
question in their own language, and Bersama explains the relevant rule or service
in plain language, **grounded in official sources**, then can draft a real form
for them.

This is a working **prototype** that implements the full flow end to end. It runs
with zero setup in an offline demo mode, and turns into a fluent multilingual
assistant when you plug in a language model.

## Submission deliverables

- **Working demo:** this repository (https://adriel96939.github.io/bersama/) . See [Quickstart](#quickstart) to run the
  full flow in about a minute in your own computer.
- **Development plan and task breakdown:** [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md)
  - what is built, what remains, time estimates, timeline, and future roadmap.
---

## Quickstart

Requires Python 3.10+.

```bash
pip install -r requirements.txt

# Option A: command-line demo (quickest, good for screen-recording)
python bersama_cli.py

# Option B: web chat page
python app.py         # then open http://127.0.0.1:5000

# Check retrieval quality
python eval.py        # English benchmark
python eval.py id     # Bahasa Indonesia benchmark
python eval.py vi     # Vietnamese benchmark
```

In the CLI: type a question, type `form` to try the form co-pilot, `lang id` to
switch language, `status` to see coverage, `quit` to exit.

---

## Languages: English, Bahasa Indonesia, and Vietnamese work fully offline

The knowledge base ships in three languages: English
(`data/knowledge_base.json`), Bahasa Indonesia (`data/knowledge_base_id.json`),
and Vietnamese (`data/knowledge_base_vi.json`) - the three largest migrant-worker
groups in Taiwan. Retrieval is language-aware: a question in Indonesian or
Vietnamese is matched against that language's passages and answered in the same
language, with **no translation step and no API key**. Type `lang id` or
`lang vi` in the CLI (or use the language pills in the web page) to try it. Each
language gets its own retriever with its own stopword list, which is what keeps
the no-answer guard working across languages.

> The Indonesian and Vietnamese passages are translations of the English ones and
> are marked `verified: false`. They should be reviewed by a native speaker
> before real deployment. The facts come from the same official sources as the
> English set.

Adding another language later is just dropping in a `knowledge_base_<code>.json`
file (and, ideally, a stopword list for it); the loader picks it up
automatically.

## Turning on the language model (fluency + more languages)

Offline mode answers with a plain grounded template in English or Indonesian. For
fluent prose, and for languages the knowledge base does not yet cover (Vietnamese,
Thai, Filipino, handled by translation), enable the language model:

```bash
export ANTHROPIC_API_KEY=your-key-here
export BERSAMA_LLM=1
# optional: export BERSAMA_MODEL=claude-sonnet-5   (check docs.claude.com for current model ids)

python bersama_cli.py     # or python app.py
```

With the model on, a worker can ask in any supported language and read the answer
in the same language. The same grounding rule still applies: the model may only
answer from the retrieved official sources, and is told to decline otherwise.

---

## How the six build steps map to the code

The project follows the agreed build order, one concern per file:

| Step | What it does | File |
|------|--------------|------|
| 1 | Knowledge base: load and validate official-source passages | `data/knowledge_base.json`, `src/knowledge_base.py` |
| 2 | Retrieval: return the most relevant passages for a question | `src/retrieval.py` |
| 3 | Grounded answer generation, with a no-source guard | `src/generation.py` |
| 4 | Language handling: translate question in, answer out | `src/translation.py` |
| 5 | Form co-pilot: draft an employer-transfer request | `src/form_copilot.py` |
| 6 | Interfaces: command line and web chat page | `bersama_cli.py`, `app.py`, `templates/index.html` |
|  | The full flow wired together | `src/pipeline.py` |
|  | Optional language-model client | `src/llm.py` |
|  | Configuration (LLM toggle, thresholds, languages) | `src/config.py` |
|  | Evaluation harness | `eval.py` |

---

## Extending the knowledge base (to be done)

Each passage is a small, self-contained chunk with a source. Add entries to the
`passages` array in `data/knowledge_base.json`:

```json
{
  "id": "wage-005",
  "topic": "wage_complaint",
  "language": "en",
  "source_title": "Ministry of Labor - overtime pay rules",
  "source_url": "https://english.mol.gov.tw/...",
  "verified": true,
  "text": "Plain-language explanation of one specific thing, in a few sentences."
}
```

Guidelines that keep quality high:
- One idea per passage, a few sentences each. Small chunks retrieve better.
- Topic must be one of: `employer_transfer`, `wage_complaint`, `nhi_healthcare`,
  `visa_residency`.
- Always include a real `source_url`. It is shown to the worker as the citation.
- Set `verified` to `true` only after a human checks the text against the source.
- Use the words workers actually search (for example "unpaid wages", "change
  employer"), so keyword retrieval finds the passage.

`python eval.py` shows coverage and retrieval accuracy as you grow the set.

---

## Two retrievers: keyword (default) and semantic (recommended)

Bersama ships with two retrievers and picks automatically:

**TF-IDF (keyword)** is the default. It needs no downloads and runs instantly, so
the project works out of the box. Its weakness is that unrelated questions that
share common words with the corpus (for example "tallest **mountain** in
**Taiwan**", or "what is an **ARC**?" landing on a passage that just mentions ARC
a lot) can produce a wrong match. As the knowledge base grows and passages share
more vocabulary, this gets noticeable. `eval.py` keeps a couple of these
"known-hard" cases visible on purpose.

**Semantic embeddings (recommended)** to be fixed. Install the optional dependency:

```bash
pip install sentence-transformers
```

With it installed, Bersama automatically switches to a multilingual
sentence-embedding retriever (set `BERSAMA_RETRIEVER=embedding` to force it, or
`=tfidf` to force keyword). Embeddings score on meaning, not shared words, which
resolves the false matches, and because the model is multilingual a question in
Bahasa Indonesia or Vietnamese matches the English passages **directly, with no
translation step needed for retrieval**. A ~500MB model downloads once on first
run, so the first startup needs internet and is slower.

Run `python eval.py` to see which retriever is active and how it scores; the line
at the top of the output names it.

A note on testing: the embedding retriever's ranking logic is unit-tested with an
injected encoder, but the semantic quality depends on the downloaded model, which
was not fetched in the build environment. Confirm it on your machine with
`python eval.py` after installing sentence-transformers.

You can also enable the **language model** (above), which adds a second safety
check on top of either retriever: it is instructed to decline when the retrieved
sources do not actually fit the question.

---

## Important boundaries

- **The form drafts only. It never submits anything** to any government system.
  A person (worker, NGO caseworker, or labor bureau) reviews and submits.
- **All legal and administrative content are to be verified.** This is a prototype; treat its
  answers as a starting point that points to official sources, not as legal advice.
- Do not commit an API key. The code reads it from the environment only.

---
