
from typing import TypedDict, Literal, Optional


class OrderItem(TypedDict):
    item_id: str
    name_en: str
    quantity: int
    unit_price_aed: float


class AgentState(TypedDict):
    # input
    user_request: str
    customer_phone: Optional[str]

    # parsed intent
    intent: Optional[Literal["search", "buy", "return", "unsupported"]]
    filters: dict          # e.g. {"max_price": 100, "keywords": ["woody"]}
    requested_items: list  # e.g. [{"name_hint": "aviator", "quantity": 2}]

    # retrieval
    matched_products: list  # list of product dicts from DB

    # decision
    action: Optional[Literal["read", "mutate"]]
    order_items: list[OrderItem]
    
    # validation
    insufficient_items: list

    # execution result
    status: Optional[str]   # success, no_match, insufficient_stock, invalid_request, unsupported_intent
    transaction_ids: list[str]

    # output
    answer_text: Optional[str]
    error: Optional[str]

