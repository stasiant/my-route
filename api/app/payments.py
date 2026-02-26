import os
import json
import requests
from typing import Any, Dict


def _bot_api(method: str, data: Dict[str, Any]) -> Any:
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    r = requests.post(url, json=data, timeout=20)

    # ВАЖНО: покажем реальную причину 400/401 и т.п.
    if not r.ok:
        raise RuntimeError(f"Telegram API error {r.status_code}: {r.text}")

    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")

    return payload["result"]


def create_stars_invoice_link(
    *,
    title: str,
    description: str,
    stars_amount: int,
    payload: Any,  # может быть dict или str
) -> str:
    # Telegram требует payload строкой
    payload_str = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)

    result = _bot_api(
        "createInvoiceLink",
        {
            "title": title,
            "description": description,
            "payload": payload_str,
            "currency": "XTR",
            "prices": [{"label": title, "amount": int(stars_amount)}],
        },
    )
    return result
