"""
Central configuration for Bersama.

Everything you might tune lives here. The most important switch is LLM_ENABLED:
- LLM_ENABLED = False (default): the whole flow runs offline with no API key.
  Retrieval + grounded answer assembly + form drafting all work. Answers are
  built from a deterministic template so you can demo the pipeline immediately.
- LLM_ENABLED = True: the same pipeline calls a real language model for fluent,
  plain-language answers and for translating to/from the worker's language.

You enable the LLM by setting the environment variable BERSAMA_LLM=1 and
providing ANTHROPIC_API_KEY. Nothing here ever hard-codes a secret.
"""

import os

# --- Language model (optional) ---------------------------------------------
# Off by default so the project runs with zero setup.
LLM_ENABLED = os.environ.get("BERSAMA_LLM", "0") == "1"

# Read from the environment only. Never commit a real key.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Model id. Configurable so you are not locked to one version.
# Check https://docs.claude.com for the current list of model ids.
MODEL = os.environ.get("BERSAMA_MODEL", "claude-sonnet-5")

# --- Retrieval --------------------------------------------------------------
# Which retriever to use:
#   'auto'      -> semantic embeddings if sentence-transformers is installed, else TF-IDF
#   'embedding' -> force semantic embeddings (falls back to TF-IDF if unavailable)
#   'tfidf'     -> force keyword retrieval (zero setup, no downloads)
RETRIEVER = os.environ.get("BERSAMA_RETRIEVER", "auto")

# Multilingual sentence-embedding model used by the embedding retriever.
# Downloaded once on first run; supports the migrant-worker languages.
EMBEDDING_MODEL = os.environ.get("BERSAMA_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# How many passages to retrieve per question.
TOP_K = 4

# Minimum score below which a match is treated as "no answer" (Bersama declines
# instead of guessing). Keyword and embedding similarity are on different scales,
# so each retriever carries its own threshold.
MIN_RELEVANCE = 0.12            # for TF-IDF (keyword) scores
MIN_RELEVANCE_EMBEDDING = 0.35  # for embedding cosine scores; tune on your data

# --- Languages --------------------------------------------------------------
# Languages the interface offers. The pipeline itself is language-agnostic;
# these are the ones we surface in the demo (start with the two largest
# communities, then add the rest).
SUPPORTED_LANGUAGES = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "vi": "Tieng Viet",
    "tl": "Tagalog",
    "th": "Thai",
}

# The seed knowledge base is written in this language. Questions in other
# languages are translated to this language for retrieval, then answers are
# translated back to the worker's language.
KB_LANGUAGE = "en"

# --- Paths ------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
KB_PATH = os.path.join(DATA_DIR, "knowledge_base.json")
