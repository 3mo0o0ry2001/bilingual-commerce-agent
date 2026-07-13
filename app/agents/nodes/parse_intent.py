"""
parse_intent.py

First node in the graph. Uses the LLM to understand the customer's request
(Arabic, English, or mixed) and extract structured intent + filters/items.
Does NOT touch the database — pure understanding step.
"""

import json
import logging
import os

from openai import OpenAI
from app.agents.state import AgentState

log = logging.getLogger("parse_intent")
client = OpenAI()

SYSTEM_PROMPT = """You are an intent parser for a bilingual (Arabic/English) perfume store
customer service agent in the UAE. Customers may write in English, Modern Standard Arabic,
Gulf/Egyptian dialect, or a mix (Arabizi included).

Classify the request into exactly one intent:
- "search": asking about availability, price, or details of perfume(s) — no purchase/return intent
- "buy": wants to purchase one or more perfumes
- "return": wants to return a previously purchased perfume
- "unsupported": anything outside these (e.g. repairs, complaints unrelated to orders, general chit-chat)

Also extract:
- "filters": for search intent — e.g. {"max_price": 100, "min_price": null, "keywords": ["woody", "oud"],
  "gender": "men"|"women"|"unisex"|null}. Use null/empty when not mentioned. Do NOT invent values.
- "requested_items": for buy/return intent — a list of
  {"name_hint": "<perfume name or brand as mentioned by the customer>", "quantity": <int, default 1 if unspecified>}

Be conservative: if intent is ambiguous, prefer "search" (read-only) over "buy".

Return ONLY a JSON object, no extra text, no markdown fences:
{"intent": "...", "filters": {...}, "requested_items": [...]}"""


def parse_intent_node(state: AgentState) -> dict:
    user_request = state["user_request"]
    model = os.getenv("INTENT_MODEL", "gpt-4.1-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_request},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)

        return {
            "intent": parsed.get("intent", "unsupported"),
            "filters": parsed.get("filters", {}) or {},
            "requested_items": parsed.get("requested_items", []) or [],
        }

    except Exception as e:
        log.error(f"parse_intent failed: {e}")
        return {
            "intent": "unsupported",
            "filters": {},
            "requested_items": [],
            "error": f"Intent parsing failed: {e}",
        }