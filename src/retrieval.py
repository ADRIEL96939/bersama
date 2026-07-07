"""
Step 2: Retrieval layer.

Two retrievers with the same tiny interface (retrieve(query, k)):

- TfidfRetriever: keyword overlap. No downloads, instant, zero setup. Good enough
  on a small, single-language corpus, but it degrades as the knowledge base grows
  and passages share common words (a question about "the tallest mountain in
  Taiwan" can brush against passages that merely mention "Taiwan"). It also cannot
  match a Vietnamese question against an English passage.

- EmbeddingRetriever: semantic similarity using multilingual sentence embeddings.
  It scores on meaning rather than shared words, which fixes the keyword
  false-match problem, and because the model is multilingual it can match a
  question in Bahasa Indonesia or Vietnamese directly against the English
  passages, with no translation step needed for retrieval. It requires the
  optional 'sentence-transformers' package and a one-time model download.

build_retriever() picks the embedding retriever when it is available (or when
forced), and falls back to TF-IDF otherwise, so the project always runs.

Each retriever exposes:
  .name           short label for status output
  .multilingual   True if it can match across languages (skip translate-before-retrieve)
  .min_relevance  the score below which a match should be treated as "no answer"
                  (different scale for keyword vs embedding similarity)
"""

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config
from .knowledge_base import Passage

# Common function words to strip so they do not inflate similarity. scikit-learn
# ships an English list; without an equivalent for other languages, ubiquitous
# words like "saya"/"yang"/"apa" make even unrelated questions look relevant,
# which breaks the no-answer guard. One list per supported keyword language.
STOPWORDS = {
    "id": [
        "saya", "aku", "kamu", "anda", "dia", "kita", "kami", "mereka", "ini",
        "itu", "yang", "di", "ke", "dari", "untuk", "pada", "dengan", "dan",
        "atau", "tapi", "tetapi", "karena", "jika", "kalau", "agar", "supaya",
        "apa", "apakah", "bagaimana", "berapa", "siapa", "kapan", "mana",
        "dimana", "mengapa", "kenapa", "adalah", "akan", "sudah", "telah",
        "sedang", "bisa", "bisakah", "dapat", "harus", "boleh", "bolehkah",
        "tidak", "bukan", "ada", "adakah", "jadi", "juga", "saja", "lagi",
        "masih", "sangat", "lebih", "paling", "oleh", "sebagai", "dalam",
        "atas", "bawah", "saat", "ketika", "setelah", "sebelum", "hingga",
        "sampai", "antara", "para", "nya", "pun", "per", "bagi", "tentang",
        "seperti", "yaitu", "maupun", "serta", "hal", "cara", "melakukan",
        "membuat", "yg", "ya", "nya", "akan", "agar", "punya", "banyak",
    ],
    "vi": [
        "tôi", "bạn", "anh", "chị", "em", "họ", "chúng", "ta", "mình", "nó",
        "của", "và", "hoặc", "nhưng", "vì", "nếu", "khi", "để", "cho", "với",
        "từ", "đến", "tại", "trong", "ngoài", "trên", "dưới", "về", "theo",
        "bằng", "là", "có", "không", "được", "sẽ", "đã", "đang", "bị", "phải",
        "cần", "nên", "thì", "mà", "này", "đó", "kia", "các", "những", "một",
        "gì", "ai", "sao", "nào", "đâu", "bao", "nhiêu", "thế", "rất", "quá",
        "hơn", "cũng", "vẫn", "còn", "chỉ", "đều", "ra", "vào", "lên", "xuống",
        "hay", "nhé", "ạ", "ừ", "vâng", "ở", "cùng", "rồi", "lúc", "việc",
        "người", "những", "hãy", "đi",
    ],
}


@dataclass
class RetrievedPassage:
    passage: Passage
    score: float


def _index_text(p: Passage) -> str:
    """What we actually embed/index: the topic plus the passage text, so a query
    like 'change employer' is pulled toward employer_transfer passages."""
    return f"{p.topic.replace('_', ' ')}. {p.text}"


def _stopwords_for(language: str):
    """English uses scikit-learn's built-in list; other languages use ours if we
    have one, else None (no stopword removal)."""
    if language == "en":
        return "english"
    return STOPWORDS.get(language, None)


class TfidfRetriever:
    name = "tfidf"
    multilingual = False

    def __init__(self, passages: list[Passage]):
        if not passages:
            raise ValueError("Cannot build a retriever with no passages.")
        self.passages = passages
        self.language = passages[0].language
        self.min_relevance = config.MIN_RELEVANCE
        corpus = [_index_text(p) for p in passages]
        self.vectorizer = TfidfVectorizer(
            stop_words=_stopwords_for(self.language), ngram_range=(1, 2)
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, k: int = 4) -> list[RetrievedPassage]:
        if not query.strip():
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(zip(self.passages, scores), key=lambda pair: pair[1], reverse=True)
        return [RetrievedPassage(passage=p, score=float(s)) for p, s in ranked[:k]]


class EmbeddingRetriever:
    """Semantic retriever. Pass `model` to inject a custom encoder (used in tests);
    otherwise a multilingual SentenceTransformer is loaded lazily."""

    multilingual = True

    def __init__(self, passages: list[Passage], model=None):
        if not passages:
            raise ValueError("Cannot build a retriever with no passages.")
        self.passages = passages
        self.min_relevance = config.MIN_RELEVANCE_EMBEDDING

        if model is None:
            # Imported here so the package is only required when this path is used.
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(config.EMBEDDING_MODEL)
            self.name = f"embedding:{config.EMBEDDING_MODEL}"
        else:
            self.name = "embedding:injected"

        self.model = model
        vectors = self.model.encode([_index_text(p) for p in passages])
        self.matrix = self._normalize(np.asarray(vectors, dtype=float))

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        """L2-normalize rows so a dot product equals cosine similarity."""
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def retrieve(self, query: str, k: int = 4) -> list[RetrievedPassage]:
        if not query.strip():
            return []
        q = self._normalize(np.asarray(self.model.encode([query]), dtype=float))
        scores = (self.matrix @ q[0])
        order = np.argsort(scores)[::-1][:k]
        return [RetrievedPassage(passage=self.passages[i], score=float(scores[i])) for i in order]


def build_retriever(passages: list[Passage]):
    """Choose a retriever based on config.RETRIEVER and what is installed.

    'auto' (default): use embeddings if sentence-transformers is available, else TF-IDF.
    'embedding': force embeddings (falls back to TF-IDF with a warning if unavailable).
    'tfidf': force keyword retrieval.
    """
    choice = config.RETRIEVER.lower()

    def _embeddings_available() -> bool:
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            return False

    if choice == "tfidf":
        return TfidfRetriever(passages)

    if choice in ("embedding", "auto"):
        if _embeddings_available():
            try:
                return EmbeddingRetriever(passages)
            except Exception as e:  # model download failed, out of memory, etc.
                print(f"[bersama] Embedding retriever unavailable ({e}); using TF-IDF.")
                return TfidfRetriever(passages)
        if choice == "embedding":
            print("[bersama] sentence-transformers not installed; using TF-IDF. "
                  "Install it to enable semantic retrieval.")
        return TfidfRetriever(passages)

    # Unknown value: be safe.
    return TfidfRetriever(passages)
