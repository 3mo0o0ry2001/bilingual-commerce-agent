"""
semantic_search.py

Queries the ChromaDB perfume collection using semantic (vector) similarity.
Handles cross-language, transliteration, and fuzzy matching that exact
SQL LIKE cannot.
"""

import logging

import chromadb

from app.search.embeddings import embed_text

log = logging.getLogger("semantic_search")

CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "perfumes"

_client = None
_collection = None


def _get_collection():
    """Lazy singleton: load the collection once and reuse it."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def semantic_search(query: str, top_k: int = 3, max_distance: float = 0.78) -> list[dict]:
    """
    Returns up to top_k matching item_ids ranked by semantic similarity.
    Results with cosine distance above max_distance are filtered out
    (too dissimilar to be a real match).
    """
    if not query.strip():
        return []

    collection = _get_collection()
    query_embedding = embed_text(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    matches = []
    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    for item_id, distance, meta in zip(ids, distances, metadatas):
        if distance <= max_distance:
            matches.append({
                "item_id": item_id,
                "distance": distance,
                "name_en": meta.get("name_en"),
                "name_ar": meta.get("name_ar"),
            })

    return matches