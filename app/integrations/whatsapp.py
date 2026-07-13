"""
whatsapp.py

Thin client for sending messages via Meta's WhatsApp Cloud API.
"""

import logging
import os

import httpx

log = logging.getLogger("whatsapp")

WHATSAPP_API_VERSION = "v25.0"
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"


def send_whatsapp_message(to: str, text: str) -> bool:
    """Sends a plain text WhatsApp message. Returns True on success."""
    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        log.error("WhatsApp credentials missing in environment")
        return False

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = httpx.post(BASE_URL, headers=headers, json=payload, timeout=10.0)
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        log.error(f"WhatsApp send failed: {e.response.status_code} {e.response.text}")
        return False
    except Exception as e:
        log.error(f"WhatsApp send error: {e}")
        return False