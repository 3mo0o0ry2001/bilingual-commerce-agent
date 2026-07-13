"""
embeddings.py

Thin wrapper around OpenAI's embedding API. Centralizes the model choice
and batching so the rest of the code doesn't depend on OpenAI directly.
"""

import logging
import os

from openai import OpenAI

log = logging.getLogger("embeddings")
client = OpenAI()

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input, same order."""
    if not texts:
        return []
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def embed_text(text: str) -> list[float]:
    """Embed a single text. Returns one vector."""
    return embed_texts([text])[0]