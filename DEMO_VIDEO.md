# Bersama - 2-Minute Demo Video Script and Recording Guide

This is a turnkey script for the required demo video. It shows one full flow end
to end: a worker asks in a migrant language, Bersama retrieves an official source,
answers in plain language in that language, declines honestly when it has no
source, and drafts a real form. Total target length: about 2 minutes.

The video feeds two scoring areas: maturity (Feasibility) and the finals system
demo. Record the flow exactly as scripted so it stays under two minutes.

---

## Before you record

1. Open a terminal with a large, readable font (18pt or more, high contrast).
2. Start the demo:

   ```bash
   pip install -r requirements.txt
   python bersama_cli.py
   ```

   The web page (`python app.py`) is an equally good choice if you prefer a
   visual UI; the beats below map to either. The CLI is easier to screen-record
   cleanly.

3. Optional but recommended: enable the language model for fluent answers
   (`export ANTHROPIC_API_KEY=...` and `export BERSAMA_LLM=1`). The offline mode
   also demos well and needs no key; either is fine.

Type slowly. Pause on each answer so viewers can read the cited source.

---

## The script (narration + on-screen actions)

### 0:00 to 0:15 - The problem

**On screen:** the Bersama title screen in the CLI (the banner and status line
showing "Languages: en, id, vi").

**Narration:**
"There are more than 800,000 migrant workers in Taiwan. When they have a
question about their wages, their health insurance, or changing employers, the
answers are scattered across government websites, mostly in Chinese. Bersama
answers those questions in the worker's own language, grounded in official
sources."

### 0:15 to 0:28 - Switch to the worker's language

**On screen:** type
```
lang id
```
The prompt changes to `[id] ask>`.

**Narration:**
"A worker from Indonesia switches to Bahasa Indonesia and just asks a question in
plain words."

### 0:28 to 1:05 - Ask, retrieve, grounded answer with a source

**On screen:** type
```
Bagaimana cara pindah ke majikan baru?
```
(English: "How do I change to a new employer?")

Let the answer appear. It is in Indonesian, and it ends with a cited source line
and the top-match label.

**Narration:**
"Bersama finds the relevant official rule, answers in Indonesian in plain
language, and cites the source it used. It is not making this up. Every answer is
grounded in a passage from an official source, so it can be checked."

Point the cursor at the "Sumber:" (Sources) line and the source URL.

### 1:05 to 1:25 - The honesty guard

**On screen:** type an out-of-scope question, for example
```
Bahasa apa saja yang bisa dilayani hotline 1955?
```
then type something clearly unrelated:
```
Apa gunung tertinggi di Taiwan?
```
(English: "What is the tallest mountain in Taiwan?")

Bersama declines and points to the 1955 hotline instead of guessing.

**Narration:**
"Just as important is what it does not do. When Bersama has no verified source,
it says so and points to the free 1955 government hotline, instead of inventing
an answer. For legal and administrative questions, that restraint is the whole
point."

### 1:25 to 1:52 - Draft a real form

**On screen:** type
```
form
```
Answer the short prompts (name, nationality, ARC number, employer, reason,
phone). A completed DRAFT employer-transfer request prints out.

**Narration:**
"Finally, Bersama can turn a short conversation into a real application. Here it
drafts an employer-transfer request. Notice it says DRAFT. It never submits
anything on the worker's behalf. A person, the worker or an NGO caseworker,
reviews it and submits it."

### 1:52 to 2:05 - Impact and close

**On screen:** run `status` to show the coverage line (156 passages, three
languages), or show the web page with the language pills.

**Narration:**
"Bersama works today in English, Bahasa Indonesia, and Vietnamese, across
employer transfer, wages, health insurance, and visas, fully offline. It brings
public services closer to the people who need them most. That is digital
inclusion in the AI era."

---

## A second short take to keep in reserve (optional, 15 seconds)

Repeat the 0:28 beat in Vietnamese to prove it is not a single-language demo:
```
lang vi
Lương tối thiểu ở Đài Loan là bao nhiêu?
```
(English: "What is the minimum wage in Taiwan?")

Use this only if you are under time; the main script already stands on its own.

---

## Recording checklist

- Large font, high contrast, no personal data on screen.
- One clean take of the full flow; type slowly and pause on each answer.
- Keep total length at or under 2 minutes.
- Add short on-screen captions for each beat (Problem, Ask, Grounded answer,
  Honesty guard, Draft form, Impact) so it reads without sound.
- Export at 1080p. Upload unlisted to YouTube or Vimeo and put the link in the
  README and the application form.
- If you narrate in English for the judges, consider adding Indonesian or
  Vietnamese subtitles to reinforce the multilingual point.

## Exact inputs, for copy-paste while recording

```
lang id
Bagaimana cara pindah ke majikan baru?
Apa gunung tertinggi di Taiwan?
form
lang vi
Lương tối thiểu ở Đài Loan là bao nhiêu?
```
