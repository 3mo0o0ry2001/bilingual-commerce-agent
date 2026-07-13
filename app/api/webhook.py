"""
webhook.py

Handles Meta's WhatsApp webhook: verification (GET) and incoming
messages (POST). Incoming customer messages are routed through the
LangGraph agent, and the reply is sent back via the WhatsApp API.
"""

import logging
import os

from fastapi import APIRouter, Request, Response

from app.core.limiter import limiter
from app.agents.graph import build_graph
from app.integrations.whatsapp import send_whatsapp_message

log = logging.getLogger("webhook")
router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "dev_verify_token_change_me")

_graph = build_graph()


@router.get("/webhook")
def verify_webhook(request: Request):
    """Meta calls this once when you configure the webhook, to confirm ownership."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        log.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    log.warning("Webhook verification failed")
    return Response(status_code=403)


@router.post("/webhook")
@limiter.limit("30/minute")
async def receive_message(request: Request):
    """Meta calls this for every incoming event (messages, statuses, etc.)."""
    body = await request.json()

    try:
        entry = body["entry"][0]
        change = entry["changes"][0]["value"]

        if "messages" not in change:
            # Status update (delivered/read) or other non-message event; ignore
            return Response(status_code=200)

        message = change["messages"][0]
        from_number = message["from"]
        text = message.get("text", {}).get("body", "")

        if not text:
            log.info("Received non-text message, skipping")
            return Response(status_code=200)

        log.info(f"Incoming WhatsApp message from {from_number}: {text}")

        result = _graph.invoke({
            "user_request": text,
            "customer_phone": from_number,
            "filters": {},
            "requested_items": [],
            "matched_products": [],
            "order_items": [],
        })

        answer = result.get("answer_text", "عذراً، حصل خطأ. حاول تاني.")
        send_whatsapp_message(from_number, answer)

    except (KeyError, IndexError) as e:
        log.warning(f"Unexpected webhook payload shape: {e}")
    except Exception as e:
        log.error(f"Webhook processing failed: {e}")

    return Response(status_code=200)