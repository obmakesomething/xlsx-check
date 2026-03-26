"""Embedding functions for the RAG pipeline.

Provides a ChromaDB-compatible embedding function using the default
all-MiniLM-L6-v2 model.  Falls back to a lightweight TF-IDF based
embedding if ``sentence-transformers`` is not available.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


def get_embedding_function() -> Any:
    """Return a ChromaDB-compatible embedding function.

    Tries the following strategies in order:

    1. ``chromadb.utils.embedding_functions.DefaultEmbeddingFunction``
       (uses all-MiniLM-L6-v2 via ``sentence-transformers``).
    2. :class:`TFIDFFallbackEmbeddingFunction` -- a deterministic,
       dependency-free fallback that produces fixed-size vectors from a
       simple bag-of-words hash.

    Returns:
        An object implementing ``__call__(texts: list[str]) -> list[list[float]]``.
    """
    # Strategy 1 -- sentence-transformers via ChromaDB default
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        ef = DefaultEmbeddingFunction()
        # Quick smoke test to surface import errors early
        ef(["test"])
        logger.info("Using DefaultEmbeddingFunction (all-MiniLM-L6-v2)")
        return ef
    except Exception as exc:
        logger.warning(
            "Could not load DefaultEmbeddingFunction (%s). "
            "Falling back to TF-IDF hash embedding.",
            exc,
        )

    # Strategy 2 -- lightweight deterministic fallback
    logger.info("Using TFIDFFallbackEmbeddingFunction")
    return TFIDFFallbackEmbeddingFunction()


class TFIDFFallbackEmbeddingFunction:
    """Minimal, dependency-free embedding function.

    Produces a fixed-dimension vector (default 384 to match MiniLM) by
    hashing token unigrams and bigrams into buckets and weighting them
    with a simple TF scheme.  The vectors are L2-normalised so that
    cosine distance is meaningful.

    This is **not** a substitute for a real embedding model -- it is only
    intended as a development/testing fallback when ``sentence-transformers``
    cannot be installed.
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    # ChromaDB expects the embedding function to be callable
    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        """Produce a deterministic embedding vector for *text*."""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dim

        vec = [0.0] * self.dim
        tf = Counter(tokens)

        for token, count in tf.items():
            # Hash the token to a bucket index
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
            weight = 1.0 + math.log(count)
            vec[idx] += sign * weight

        # Add bigrams for a bit more expressiveness
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i + 1]}"
            h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
            vec[idx] += sign * 0.5

        # L2-normalise
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + punctuation tokenizer."""
        text = text.lower()
        tokens = re.findall(r"[a-z0-9\uac00-\ud7a3]+", text)
        return tokens
