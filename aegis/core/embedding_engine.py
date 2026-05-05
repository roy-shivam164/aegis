"""
Embedding Engine — generates vector embeddings for AEGIS.

Primary model  : OpenAI ``text-embedding-3-small`` (1536-dim)
Secondary model: ``sentence-transformers/all-MiniLM-L6-v2`` (384-dim)
                 used for sentiment vectors and as an offline fallback.

Both models are loaded lazily on first use.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from aegis.config import settings

if TYPE_CHECKING:
    from openai import OpenAI
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ── Internal singletons (lazy) ────────────────────────────────────────────────

_openai_client: "OpenAI | None" = None
_st_model: "SentenceTransformer | None" = None


def _get_openai_client() -> "OpenAI":
    """Return (or create) the OpenAI client singleton."""
    global _openai_client  # noqa: PLW0603
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
        logger.debug("OpenAI client initialised")
    return _openai_client


def _get_st_model() -> "SentenceTransformer":
    """Return (or load) the sentence-transformers model singleton."""
    global _st_model  # noqa: PLW0603
    if _st_model is None:
        from sentence_transformers import SentenceTransformer

        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.debug("SentenceTransformer 'all-MiniLM-L6-v2' loaded")
    return _st_model


# ── Public API ────────────────────────────────────────────────────────────────


def embed_text(text: str) -> list[float]:
    """Embed *text* with OpenAI text-embedding-3-small (1536-dim).

    Falls back to sentence-transformers if the OpenAI API key is not set,
    padding/truncating the output to 1536 dimensions.

    Parameters
    ----------
    text:
        The raw text to embed.

    Returns
    -------
    list[float]
        A 1536-dimensional embedding vector.
    """
    if not settings.openai_api_key:
        logger.warning("No OPENAI_API_KEY — using sentence-transformers fallback (384→1536 pad)")
        return _st_embed_padded(text, target_dim=settings.dim_large)

    client = _get_openai_client()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    return response.data[0].embedding


def embed_sentiment(text: str) -> list[float]:
    """Embed *text* with sentence-transformers all-MiniLM-L6-v2 (384-dim).

    Used for the ``sentiment`` named vector in ``user_life_log`` and the
    ``communication_style`` named vector in ``person_profiles``.

    Parameters
    ----------
    text:
        The raw text to embed.

    Returns
    -------
    list[float]
        A 384-dimensional embedding vector.
    """
    model = _get_st_model()
    return model.encode(text, convert_to_numpy=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in one OpenAI API call (more efficient).

    Parameters
    ----------
    texts:
        List of strings to embed.

    Returns
    -------
    list[list[float]]
        A list of 1536-dimensional embedding vectors, one per input text.
    """
    if not settings.openai_api_key:
        return [_st_embed_padded(t, target_dim=settings.dim_large) for t in texts]

    client = _get_openai_client()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    # Results are returned in the same order as the input
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


# ── Internal helpers ──────────────────────────────────────────────────────────


@lru_cache(maxsize=256)
def _st_embed_padded(text: str, target_dim: int = 1536) -> list[float]:
    """Embed with sentence-transformers and pad / truncate to *target_dim*."""
    model = _get_st_model()
    vec: list[float] = model.encode(text, convert_to_numpy=True).tolist()
    if len(vec) < target_dim:
        vec = vec + [0.0] * (target_dim - len(vec))
    return vec[:target_dim]
