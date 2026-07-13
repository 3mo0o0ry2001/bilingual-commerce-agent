"""
Integration test for semantic_search — requires a live ChromaDB index
built from build_vector_index.py. Skipped automatically if the index
doesn't exist yet.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.search.semantic_search import semantic_search

CHROMA_PATH = Path("data/chroma")


@pytest.mark.skipif(
    not CHROMA_PATH.exists(),
    reason="ChromaDB index not built yet; run scripts/build_vector_index.py first",
)
def test_semantic_search_returns_results_for_known_query():
    results = semantic_search("mercedes benz", top_k=3, max_distance=1.0)
    assert len(results) > 0


@pytest.mark.skipif(
    not CHROMA_PATH.exists(),
    reason="ChromaDB index not built yet; run scripts/build_vector_index.py first",
)
def test_semantic_search_empty_query_returns_empty_list():
    results = semantic_search("", top_k=3)
    assert results == []