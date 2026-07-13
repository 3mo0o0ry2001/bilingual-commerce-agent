"""
build_vector_index.py

Builds a persistent ChromaDB collection of perfume embeddings from the
products table. Each perfume is embedded from a combined multilingual text
(Arabic name + English name + brand + accords) so search works across
languages and spellings.

Re-run safe: clears and rebuilds the collection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import logging

import chromadb

from app.db.database import SessionLocal
from app.db.models import Product
from app.search.embeddings import embed_texts

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("build_vector_index")

CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "perfumes"


def build_search_text(product: Product) -> str:
    """Combine multilingual fields so one vector captures all the ways a
    customer might refer to this perfume."""
    accords = ", ".join(product.main_accords or [])
    parts = [
        product.name_en or "",
        product.name_ar or "",
        product.brand or "",
        accords,
    ]
    return " | ".join(p for p in parts if p)


def main():
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Fresh rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
        log.info("Deleted existing collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    with SessionLocal() as db:
        products = db.query(Product).all()

    log.info(f"Embedding {len(products)} products...")

    texts = [build_search_text(p) for p in products]
    ids = [p.item_id for p in products]
    metadatas = [
        {"item_id": p.item_id, "name_en": p.name_en, "name_ar": p.name_ar or ""}
        for p in products
    ]

    # Batch embed (OpenAI handles up to ~2048 inputs per call; 100 is fine in one shot)
    embeddings = embed_texts(texts)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    log.info(f"Indexed {collection.count()} perfumes into ChromaDB at {CHROMA_PATH}")


if __name__ == "__main__":
    main()