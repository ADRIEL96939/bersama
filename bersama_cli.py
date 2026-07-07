#!/usr/bin/env python3
"""
Bersama command-line demo.

Run:  python bersama_cli.py

This is the quickest way to see the whole flow, and a clean thing to screen-record
for the 2-minute demo video. Ask a question and get a grounded answer with sources.
Type 'form' to try the employer-transfer form co-pilot. Type 'help' for commands.
"""

import sys

from src import config
from src.pipeline import Bersama
from src.form_copilot import new_employer_transfer_session
from src import llm


BANNER = r"""
  ____                                    
 | __ )  ___ _ __ ___  __ _ _ __ ___   __ _ 
 |  _ \ / _ \ '__/ __|/ _` | '_ ` _ \ / _` |
 | |_) |  __/ |  \__ \ (_| | | | | | | (_| |
 |____/ \___|_|  |___/\__,_|_| |_| |_|\__,_|

 AI public-service companion for migrant workers in Taiwan
"""

HELP = """
Commands:
  <type any question>   Ask about employer transfer, wages, NHI/health, or visa/residency
  form                  Start the employer-transfer form co-pilot
  lang <code>           Set your language: en, id, vi, tl, th   (default: en)
  status                Show knowledge-base coverage and whether the LLM is on
  help                  Show this help
  quit                  Exit
"""


def print_answer(result: dict) -> None:
    print()
    print(result["answer"])
    print()
    if result["grounded"]:
        # Retrieval detail helps during development; comment out for a cleaner demo.
        top = result["retrieval"][0] if result["retrieval"] else None
        if top:
            print(f"   (top match: {top['id']} · topic {top['topic']} · score {top['score']})")
    print("-" * 70)


def run_form(lang: str) -> None:
    """Walk through the employer-transfer form in order, one question at a time."""
    session = new_employer_transfer_session()
    print("\nEmployer-transfer form. Answer each question. Type 'cancel' to stop.")
    print("Optional questions can be left blank (just press Enter).\n")
    for field in session.fields:
        while True:
            label = field.question + ("" if field.required else "  [optional]")
            answer = input(f"  {label}\n  > ").strip()
            if answer.lower() == "cancel":
                print("Form cancelled.\n")
                return
            if not answer and field.required:
                print("  (this one is required, please enter a value)")
                continue
            session.record(field.key, answer)
            break
    print("\n" + "=" * 70)
    print(session.render_draft())
    print("=" * 70 + "\n")


def main() -> None:
    print(BANNER)
    print(f"Language model: {'ON' if llm.is_available() else 'OFF (offline demo mode)'}")
    bot = Bersama()
    print(f"Retriever: {bot.retriever_name}  | Languages: {', '.join(bot.languages)}")
    c = bot.coverage
    print(f"Knowledge base: {c['total']} passages "
          f"({c['verified']} verified, {c['unverified']} to verify)")
    print("Type 'help' for commands, 'quit' to exit.")
    print("-" * 70)

    lang = "en"
    while True:
        try:
            text = input(f"[{lang}] ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if not text:
            continue

        low = text.lower()
        if low in ("quit", "exit"):
            print("Goodbye.")
            return
        if low == "help":
            print(HELP)
            continue
        if low == "status":
            c = bot.coverage
            print(f"\nLLM: {'ON' if llm.is_available() else 'OFF'}  |  model: {config.MODEL}")
            print(f"Retriever: {bot.retriever_name}  | Languages: {', '.join(bot.languages)}")
            print(f"Passages: {c['total']}  verified: {c['verified']}  by topic: {c['by_topic']}\n")
            continue
        if low.startswith("lang"):
            parts = text.split()
            if len(parts) == 2 and parts[1] in config.SUPPORTED_LANGUAGES:
                lang = parts[1]
                print(f"Language set to {config.SUPPORTED_LANGUAGES[lang]}.")
            else:
                opts = ", ".join(config.SUPPORTED_LANGUAGES)
                print(f"Usage: lang <code>. Options: {opts}")
            continue
        if low == "form":
            run_form(lang)
            continue

        result = bot.answer(text, user_lang=lang)
        print_answer(result)


if __name__ == "__main__":
    sys.exit(main())
