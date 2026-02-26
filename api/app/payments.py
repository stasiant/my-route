import os
import json
import requests
from typing import Any, Dict

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

def _bot_api(method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    r = requests.post(url, json=data, timeout=20)
    r.raise_for_status()

    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")

    return payload["result"]

def create_stars_invoice_link(title: str, description: str, stars_amount: int, payload: Dict[str, Any]) -> str:
    # currency for Telegram Stars is XTR, amount is in STARS (integer)
    invoice_payload = json.dumps(payload, ensure_ascii=False)

    result = _bot_api("createInvoiceLink", {
        "title": title,
        "description": description,
        "payload": invoice_payload,
        "currency": "XTR",
        "prices": [{"label": title, "amount": int(stars_amount)}],
    })

    # createInvoiceLink returns the link string
    return result
