"""
validate_stock.py

Mutation-path node. Verifies every requested item has sufficient stock
BEFORE any database mutation. Enforces all-or-nothing: if any single item
is short, the whole order is rejected (no partial fulfillment).
Return intent skips stock validation (returns add stock back).
"""

import logging

from app.agents.state import AgentState

log = logging.getLogger("validate_stock")


def validate_stock_node(state: AgentState) -> dict:
    intent = state.get("intent")
    order_items = state.get("order_items", [])

    # Returns don't need stock validation (they add stock back, not remove)
    if intent == "return":
        return {"status": "validated"}

    insufficient = []
    for item in order_items:
        requested_qty = item.get("quantity", 1)
        available = item.get("available_stock", 0)
        if requested_qty > available:
            insufficient.append({
                "name_en": item["name_en"],
                "requested": requested_qty,
                "available": available,
            })

    if insufficient:
        log.info(f"Insufficient stock for {len(insufficient)} item(s)")
        return {
            "status": "insufficient_stock",
            "action": "read",  # reroute away from execution
            "insufficient_items": insufficient,
        }

    return {"status": "validated"}