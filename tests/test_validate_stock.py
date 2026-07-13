"""
Unit tests for validate_stock_node — pure validation logic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.nodes.validate_stock import validate_stock_node


def test_sufficient_stock_passes_validation():
    state = {
        "intent": "buy",
        "order_items": [
            {"name_en": "Euphoria", "quantity": 2, "available_stock": 10},
        ],
    }
    result = validate_stock_node(state)
    assert result["status"] == "validated"


def test_insufficient_stock_blocks_and_reroutes():
    state = {
        "intent": "buy",
        "order_items": [
            {"name_en": "Euphoria", "quantity": 5, "available_stock": 2},
        ],
    }
    result = validate_stock_node(state)
    assert result["status"] == "insufficient_stock"
    assert result["action"] == "read"
    assert len(result["insufficient_items"]) == 1


def test_multi_item_order_one_insufficient_blocks_whole_order():
    """Critical policy: if ANY item is short, the WHOLE order is rejected."""
    state = {
        "intent": "buy",
        "order_items": [
            {"name_en": "Euphoria", "quantity": 1, "available_stock": 10},
            {"name_en": "La Nuit", "quantity": 3, "available_stock": 1},
        ],
    }
    result = validate_stock_node(state)
    assert result["status"] == "insufficient_stock"
    assert len(result["insufficient_items"]) == 1
    assert result["insufficient_items"][0]["name_en"] == "La Nuit"


def test_return_intent_skips_stock_validation():
    """Returns add stock back, so they should never be blocked by validation."""
    state = {
        "intent": "return",
        "order_items": [
            {"name_en": "Euphoria", "quantity": 100, "available_stock": 0},
        ],
    }
    result = validate_stock_node(state)
    assert result["status"] == "validated"