"""
Step 1: Knowledge base.

Loads the seed passages, checks each one has the fields the rest of the system
needs, and exposes simple helpers. The quality of everything downstream depends
on the quality of these passages, so we validate strictly and fail loudly.
"""

import glob
import json
import os
from collections import defaultdict
from dataclasses import dataclass

from . import config

REQUIRED_FIELDS = ["id", "topic", "language", "source_title", "source_url", "text"]
VALID_TOPICS = {"employer_transfer", "wage_complaint", "nhi_healthcare", "visa_residency"}


@dataclass
class Passage:
    id: str
    topic: str
    language: str
    source_title: str
    source_url: str
    text: str
    verified: bool = False


def _kb_files() -> list[str]:
    """Every knowledge_base*.json in the data dir. This lets each language live in
    its own file (knowledge_base.json for English, knowledge_base_id.json for
    Bahasa Indonesia, and so on) while still loading as one combined set."""
    pattern = os.path.join(config.DATA_DIR, "knowledge_base*.json")
    return sorted(glob.glob(pattern))


def load_passages(path: str = None) -> list[Passage]:
    """Read the knowledge base file(s) and return validated Passage objects.
    If `path` is given, only that file is read; otherwise all language files are
    merged."""
    files = [path] if path else _kb_files()
    if not files:
        raise ValueError(f"No knowledge base files found in {config.DATA_DIR}")

    passages: list[Passage] = []
    seen_ids: set[str] = set()
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = raw.get("passages", [])
        for i, item in enumerate(items):
            missing = [field for field in REQUIRED_FIELDS if not item.get(field)]
            if missing:
                raise ValueError(f"{os.path.basename(fpath)} passage #{i} missing fields: {missing}")
            if item["topic"] not in VALID_TOPICS:
                raise ValueError(
                    f"Passage {item['id']} has unknown topic '{item['topic']}'. "
                    f"Valid topics: {sorted(VALID_TOPICS)}"
                )
            if item["id"] in seen_ids:
                raise ValueError(f"Duplicate passage id: {item['id']} (in {os.path.basename(fpath)})")
            seen_ids.add(item["id"])
            passages.append(
                Passage(
                    id=item["id"],
                    topic=item["topic"],
                    language=item["language"],
                    source_title=item["source_title"],
                    source_url=item["source_url"],
                    text=item["text"],
                    verified=bool(item.get("verified", False)),
                )
            )
    return passages


def group_by_language(passages: list[Passage]) -> dict[str, list[Passage]]:
    """Split passages into one list per language code."""
    groups: dict[str, list[Passage]] = defaultdict(list)
    for p in passages:
        groups[p.language].append(p)
    return dict(groups)


def coverage_summary(passages: list[Passage]) -> dict:
    """Count passages per topic and how many are human-verified. Useful for
    tracking progress toward the 40-60 passage target and knowing how much of
    the base still needs checking."""
    by_topic: dict[str, int] = {t: 0 for t in VALID_TOPICS}
    verified = 0
    for p in passages:
        by_topic[p.topic] += 1
        if p.verified:
            verified += 1
    return {
        "total": len(passages),
        "verified": verified,
        "unverified": len(passages) - verified,
        "by_topic": by_topic,
    }
