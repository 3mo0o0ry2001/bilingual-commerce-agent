"""
graph.py

Builds the full LangGraph orchestration for the bilingual commerce agent.
"""

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes.parse_intent import parse_intent_node
from app.agents.nodes.retrieve_products import retrieve_products_node
from app.agents.nodes.decide_action import decide_action_node
from app.agents.nodes.validate_stock import validate_stock_node
from app.agents.nodes.execute_transaction import execute_transaction_node
from app.agents.nodes.format_response import format_response_node


def _route_after_decide(state: AgentState) -> str:
    return state.get("action", "read")


def _route_after_validate(state: AgentState) -> str:
    # If stock validation failed, skip execution and go straight to response
    if state.get("status") == "insufficient_stock":
        return "format_response"
    return "execute_transaction"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("retrieve_products", retrieve_products_node)
    graph.add_node("decide_action", decide_action_node)
    graph.add_node("validate_stock", validate_stock_node)
    graph.add_node("execute_transaction", execute_transaction_node)
    graph.add_node("format_response", format_response_node)

    graph.set_entry_point("parse_intent")
    graph.add_edge("parse_intent", "retrieve_products")
    graph.add_edge("retrieve_products", "decide_action")

    # After decide_action: mutate -> validate_stock, read -> format_response
    graph.add_conditional_edges(
        "decide_action",
        _route_after_decide,
        {"mutate": "validate_stock", "read": "format_response"},
    )

    # After validate_stock: ok -> execute, insufficient -> format_response
    graph.add_conditional_edges(
        "validate_stock",
        _route_after_validate,
        {"execute_transaction": "execute_transaction", "format_response": "format_response"},
    )

    graph.add_edge("execute_transaction", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()