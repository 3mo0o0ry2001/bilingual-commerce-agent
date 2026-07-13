"""
Unit tests for decide_action_node — pure routing logic, no external calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.nodes.decide_action import decide_action_node


def test_search_intent_routes_to_read():
    state = {"intent": "search"}
    result = decide_action_node(state)
    assert result["action"] == "read"


def test_unsupported_intent_routes_to_read_with_status():
    state = {"intent": "unsupported"}
    result = decide_action_node(state)
    assert result["action"] == "read"
    assert result["status"] == "unsupported_intent"


def test_buy_intent_with_matched_items_routes_to_mutate():
    state = {
        "intent": "buy",
        "order_items": [{"item_id": "PF123", "quantity": 1}],
        "requested_items": [{"name_hint": "euphoria", "quantity": 1}],
    }
    result = decide_action_node(state)
    assert result["action"] == "mutate"


def test_buy_intent_with_no_matches_routes_to_read_no_match():
    state = {
        "intent": "buy",
        "order_items": [],
        "requested_items": [{"name_hint": "nonexistent perfume", "quantity": 1}],
    }
    result = decide_action_node(state)
    assert result["action"] == "read"
    assert result["status"] == "no_match"


def test_return_intent_with_matched_items_routes_to_mutate():
    state = {
        "intent": "return",
        "order_items": [{"item_id": "PF456", "quantity": 1}],
        "requested_items": [{"name_hint": "la nuit", "quantity": 1}],
    }
    result = decide_action_node(state)
    assert result["action"] == "mutate"