"""
execute_transaction.py

Mutation-path node. Performs the actual DB changes:
- one transaction row PER item (never aggregated)
- sequential running-balance updates
- inventory decrement (buy) or increment (return)
All within a single DB transaction: any failure rolls back everything.
"""

import logging
import uuid
from datetime import datetime, timezone

from app.agents.state import AgentState
from app.db.database import SessionLocal
from app.db.models import Product, Transaction, Customer

log = logging.getLogger("execute_transaction")


def _get_current_balance(db) -> float:
    last = db.query(Transaction).order_by(Transaction.timestamp.desc()).first()
    return last.balance_after_aed if last else 0.0


def _resolve_customer(db, phone: str | None) -> int | None:
    if not phone:
        return None
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if not customer:
        customer = Customer(phone=phone, preferred_language="ar")
        db.add(customer)
        db.flush()  # assign customer_id without full commit
    return customer.customer_id


def execute_transaction_node(state: AgentState) -> dict:
    intent = state.get("intent")
    order_items = state.get("order_items", [])
    phone = state.get("customer_phone")

    transaction_ids = []

    try:
        with SessionLocal() as db:
            customer_id = _resolve_customer(db, phone)
            balance = _get_current_balance(db)

            for item in order_items:
                product = db.query(Product).filter(
                    Product.item_id == item["item_id"]
                ).with_for_update().first()

                if not product:
                    raise ValueError(f"Product {item['item_id']} disappeared mid-transaction")

                qty = item.get("quantity", 1)
                unit_price = product.price_aed

                if intent == "buy":
                    if product.quantity_in_stock < qty:
                        raise ValueError(f"Stock changed for {product.name_en}")
                    product.quantity_in_stock -= qty
                    line_total = unit_price * qty
                    balance += line_total
                    status = "success"
                elif intent == "return":
                    product.quantity_in_stock += qty
                    line_total = -(unit_price * qty)
                    balance += line_total
                    status = "return"
                else:
                    raise ValueError(f"execute_transaction called with invalid intent: {intent}")

                txn = Transaction(
                    transaction_id="TXN" + uuid.uuid4().hex[:10].upper(),
                    customer_id=customer_id,
                    item_id=product.item_id,
                    quantity=qty,
                    unit_price_aed=unit_price,
                    line_total_aed=line_total,
                    balance_after_aed=balance,
                    status=status,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(txn)
                transaction_ids.append(txn.transaction_id)

            db.commit()  # commit all rows atomically

        log.info(f"Executed {len(transaction_ids)} transaction(s), intent={intent}")
        return {
            "status": "success",
            "transaction_ids": transaction_ids,
        }

    except Exception as e:
        log.error(f"execute_transaction failed, rolled back: {e}")
        return {
            "status": "invalid_request",
            "transaction_ids": [],
            "error": f"Transaction failed: {e}",
        }