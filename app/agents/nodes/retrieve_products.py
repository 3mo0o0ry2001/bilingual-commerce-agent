"""
retrieve_products.py

Second node in the graph. Queries the products table based on the parsed
intent (search filters, or requested item name hints for buy/return).
"""

import logging

from sqlalchemy import or_, func, cast, String

from app.agents.state import AgentState
from app.db.database import SessionLocal
from app.db.models import Product
from app.search.semantic_search import semantic_search

log = logging.getLogger("retrieve_products")


def _search_by_filters(db, filters: dict) -> list[Product]:
    query = db.query(Product)

    if filters.get("max_price"):
        query = query.filter(Product.price_aed <= filters["max_price"])
    if filters.get("min_price"):
        query = query.filter(Product.price_aed >= filters["min_price"])
    if filters.get("gender"):
        query = query.filter(
            or_(Product.gender == filters["gender"], Product.gender == "unisex")
        )
    if filters.get("keywords"):
        keyword_conditions = []
        for kw in filters["keywords"]:
            pattern = f"%{kw}%"
            keyword_conditions.append(
                or_(
                    func.lower(Product.name_en).like(func.lower(pattern)),
                    func.lower(Product.description_en).like(func.lower(pattern)),
                    cast(Product.main_accords, String).ilike(pattern),
                )
            )
        query = query.filter(or_(*keyword_conditions))

    return query.filter(Product.quantity_in_stock > 0).limit(10).all()


def _search_by_name_hints(db, requested_items: list[dict]) -> list[tuple]:
    matched = []
    for item in requested_items:
        hint = item.get("name_hint", "")
        if not hint:
            continue

        product = None

        sem_results = semantic_search(hint, top_k=1)
        if sem_results:
            best_id = sem_results[0]["item_id"]
            product = db.query(Product).filter(Product.item_id == best_id).first()

        if not product:
            pattern = f"%{hint}%"
            product = (
                db.query(Product)
                .filter(
                    or_(
                        func.lower(Product.name_en).like(func.lower(pattern)),
                        func.lower(Product.brand).like(func.lower(pattern)),
                        Product.name_ar.like(pattern),
                    )
                )
                .first()
            )

        if product:
            matched.append((item, product))

    return matched


def retrieve_products_node(state: AgentState) -> dict:
    intent = state.get("intent")

    with SessionLocal() as db:
        if intent == "search":
            user_request = state.get("user_request", "")

            semantic_matches = semantic_search(user_request, top_k=5, max_distance=0.85)

            filters = state.get("filters", {})

            if semantic_matches:
                matched_ids = [m["item_id"] for m in semantic_matches]
                query = db.query(Product).filter(Product.item_id.in_(matched_ids))
                query = query.filter(Product.quantity_in_stock > 0)
                if filters.get("max_price"):
                    query = query.filter(Product.price_aed <= filters["max_price"])
                if filters.get("min_price"):
                    query = query.filter(Product.price_aed >= filters["min_price"])
                if filters.get("gender"):
                    query = query.filter(
                        or_(Product.gender == filters["gender"], Product.gender == "unisex")
                    )
                products = query.all()
            else:
                products = []

            if not products or any(filters.get(k) for k in ("max_price", "min_price", "gender", "keywords")):
                filtered = _search_by_filters(db, filters)
                existing_ids = {p.item_id for p in products}
                products += [p for p in filtered if p.item_id not in existing_ids]

            return {
                "matched_products": [
                    {
                        "item_id": p.item_id,
                        "brand": p.brand,
                        "name_en": p.name_en,
                        "name_ar": p.name_ar,
                        "description_ar": p.description_ar,
                        "price_aed": p.price_aed,
                        "quantity_in_stock": p.quantity_in_stock,
                    }
                    for p in products
                ]
            }

        elif intent in ("buy", "return"):
            matches = _search_by_name_hints(db, state.get("requested_items", []))
            order_items = []
            for requested, product in matches:
                order_items.append({
                    "item_id": product.item_id,
                    "name_en": product.name_en,
                    "quantity": requested.get("quantity", 1),
                    "unit_price_aed": product.price_aed,
                    "available_stock": product.quantity_in_stock,
                })
            return {"order_items": order_items}

        else:
            log.info(f"retrieve_products skipped for intent={intent}")
            return {"matched_products": [], "order_items": []}