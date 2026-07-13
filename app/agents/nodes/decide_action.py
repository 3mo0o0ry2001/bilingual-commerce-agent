"""
decide_action.py

Third node in the graph. Decides whether to route to the mutation path
(buy/return -> validate stock -> execute transaction) or straight to
read-only response formatting (search, or unsupported/invalid cases).
"""

import logging

from app.agents.state import AgentState

log = logging.getLogger("decide_action")


def decide_action_node(state: AgentState) -> dict:
    intent = state.get("intent")

    if intent == "search":
        return {"action": "read"}

    if intent == "unsupported":
        return {
            "action": "read",
            "status": "unsupported_intent",
        }

    if intent in ("buy", "return"):
        order_items = state.get("order_items", [])
        requested_items = state.get("requested_items", [])

        if not order_items:
            log.info("No matching products found for requested items")
            return {
                "action": "read",
                "status": "no_match",
            }

        if len(order_items) < len(requested_items):
            log.info("Some requested items had no product match")

        return {"action": "mutate"}

    log.warning(f"Unhandled intent in decide_action: {intent}")
    return {"action": "read", "status": "invalid_request"}