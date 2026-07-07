#!/usr/bin/env python3
"""
Bersama web app (Flask).

Run:  python app.py
Then open http://127.0.0.1:5000 in a browser.

A thin server over the same pipeline the CLI uses. Two JSON endpoints:
  POST /ask            {question, lang}  -> grounded answer + sources
  POST /draft-transfer {answers: {...}}  -> plain-text employer-transfer draft
The form is kept stateless: the browser collects the answers and posts them all
at once, so the server holds no session.
"""

from flask import Flask, jsonify, render_template, request

from src import config
from src.pipeline import Bersama
from src.form_copilot import new_employer_transfer_session, EMPLOYER_TRANSFER_FIELDS
from src import llm

app = Flask(__name__)
bot = Bersama()  # built once at startup


@app.route("/")
def index():
    fields = [
        {"key": f.key, "question": f.question, "required": f.required}
        for f in EMPLOYER_TRANSFER_FIELDS
    ]
    return render_template(
        "index.html",
        languages=config.SUPPORTED_LANGUAGES,
        llm_on=llm.is_available(),
        retriever=bot.retriever_name,
        languages_available=bot.languages,
        coverage=bot.coverage,
        form_fields=fields,
    )


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    lang = data.get("lang") or "en"
    if not question:
        return jsonify({"error": "empty question"}), 400
    result = bot.answer(question, user_lang=lang)
    return jsonify(result)


@app.route("/draft-transfer", methods=["POST"])
def draft_transfer():
    data = request.get_json(force=True)
    answers = data.get("answers") or {}
    session = new_employer_transfer_session()
    for key, value in answers.items():
        if value:
            session.record(key, str(value))
    return jsonify({"draft": session.render_draft(), "complete": session.is_complete()})


if __name__ == "__main__":
    # Local development server. Keep debug off by default; set BERSAMA_DEBUG=1 to
    # enable the auto-reloader while you are editing.
    import os
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("BERSAMA_DEBUG") == "1")
