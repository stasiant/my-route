from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any, List

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _user_agent() -> str:
    # Важно: Nominatim требует валидный User-Agent с идентификацией приложения.
    # Задай в env: NOMINATIM_USER_AGENT="my-route-app/0.1 (contact: your@email.com)"
    ua = os.getenv("NOMINATIM_USER_AGENT", "").strip()
    if ua:
        return ua
    return "my-route-app/0.1 (local dev)"


def geocode_nominatim(query: str, *, timeout: int = 20) -> Optional[Dict[str, Any]]:
    headers = {
        "User-Agent": _user_agent(),
        "Accept-Language": "ru,en;q=0.8",
    }
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }

    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=timeout)
    except requests.RequestException:
        return None

    # Если Nominatim режет (403/429) — не валим весь маршрут
    if r.status_code in (403, 429):
        return None

    r.raise_for_status()

    data = r.json()
    if not data:
        return None

    item = data[0]
    return {
        "lat": float(item["lat"]),
        "lng": float(item["lon"]),
        "display_name": item.get("display_name"),
    }


def geocode_many(queries: List[str], *, delay_sec: float = 1.0) -> Dict[str, Optional[Dict[str, Any]]]:
    out: Dict[str, Optional[Dict[str, Any]]] = {}
    for q in queries:
        if q in out:
            continue
        out[q] = geocode_nominatim(q)
        time.sleep(delay_sec)
    return out
