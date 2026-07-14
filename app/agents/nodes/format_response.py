"""
format_response.py

Final node. Converts the accumulated state (search results, transaction
outcome, or error status) into a single natural Arabic customer-facing
message (answer_text). This is the only user-visible output.
"""

import json
import logging
import os

from openai import OpenAI
from app.agents.state import AgentState

log = logging.getLogger("format_response")
client = OpenAI()

SYSTEM_PROMPT = """You are a warm, concise customer service agent for a UAE perfume store,
replying on WhatsApp in natural Gulf/MSA Arabic. Write a short reply (1-2 sentences).

You will receive a JSON "context" describing the outcome. Craft the reply based on "status":
- "success" (search): present the found perfumes naturally with prices in AED. If many, mention 2-3 best.
- "success" (buy): confirm the purchase, mention item(s) and total.
- "success" (return): confirm the return was processed.
- "no_match": politely say the item wasn't found; if alternatives exist, suggest one.
- "insufficient_stock": state available quantity and offer what you can fulfill.
- "invalid_request": ask briefly for the missing info (e.g. quantity).
- "unsupported_intent": politely explain it's outside what you can help with, offer a supported alternative.

Always use the Arabic word "عطر" (singular) or "عطور" (plural) when referring to perfumes.
Never use "عرق" or any other word — "عطر"/"عطور" only.

Keep it natural and friendly. Prices are in AED (درهم). Return ONLY the Arabic reply text,
no JSON, no quotes, no extra formatting."""


def _build_context(state: AgentState) -> dict:
    return {
        "intent": state.get("intent"),
        "status": state.get("status"),
        "matched_products": [
            {"name_ar": p.get("name_ar"), "name_en": p.get("name_en"),
             "price_aed": p.get("price_aed")}
            for p in state.get("matched_products", [])[:5]
        ],
        "order_items": [
            {"name_en": i.get("name_en"), "quantity": i.get("quantity"),
             "unit_price_aed": i.get("unit_price_aed")}
            for i in state.get("order_items", [])
        ],
        "insufficient_items": state.get("insufficient_items", []),
        "transaction_count": len(state.get("transaction_ids", [])),
    }


def format_response_node(state: AgentState) -> dict:
    context = _build_context(state)
    model = os.getenv("RESPONSE_MODEL", "gpt-4.1-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        answer = (resp.choices[0].message.content or "").strip()
        return {"answer_text": answer}

    except Exception as e:
        log.error(f"format_response failed: {e}")
        return {
            "answer_text": "عذراً، حصل خطأ مؤقت. ممكن تعيد طلبك؟",
            "error": f"Response formatting failed: {e}",
        }