# api/app/ai.py
import json
import os
from typing import Any, Dict, List, Tuple

from openai import OpenAI

from app.geocode import geocode_many
from app.schemas import MapPoint, RouteRequest, RouteResponse


def _env_float(name: str, default: float) -> float:
    val = (os.getenv(name) or "").strip()
    if not val:
        return default
    try:
        return float(val)
    except Exception:
        return default


def _env_int(name: str, default: int) -> int:
    val = (os.getenv(name) or "").strip()
    if not val:
        return default
    try:
        return int(val)
    except Exception:
        return default


def _normalize_query(q: str, destination: str) -> str:
    q = (q or "").strip()
    if not q:
        return q
    # Если GPT не добавил город — добавим.
    low = q.lower()
    dest_low = (destination or "").strip().lower()
    if dest_low and dest_low not in low:
        q = f"{q}, {destination}"
    # Чуть повышаем шанс нахождения в Nominatim
    if "russia" not in low and "россия" not in low:
        q = f"{q}, Russia"
    return q


def _extract_json(text: str) -> str:
    """
    На случай если модель всё же прислала лишний текст.
    Вырежем первый JSON-объект.
    """
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    temperature = _env_float("OPENAI_TEMPERATURE", 0.4)
    geocode_delay = _env_float("GEOCODE_DELAY_SEC", 1.0)
    min_points = _env_int("MAP_POINTS_MIN", 10)
    max_points = _env_int("MAP_POINTS_MAX", 14)

    client = OpenAI(api_key=api_key, timeout=45.0, max_retries=2)

    schema_hint = {
        "summary": "string",
        "daily_plan": [{"day": 1, "morning": ["string"], "afternoon": ["string"], "evening": ["string"]}],
        "food": [{"name": "string", "type": "string"}],
        "tips": ["string"],
        "budget_notes": "string",
        "checklist": ["string"],
        "map_points": [{"name": "string", "query": "string", "day": 1, "category": "museum|coffee|architecture|park|food|other"}],
    }

    language = getattr(req, "language", None) or "ru"
    destination = (req.destination or "").strip()

    system = (
        "You are a travel itinerary planner.\n"
        "Return ONLY valid JSON (no markdown, no comments, no extra text).\n"
        "The JSON must match this structure exactly:\n"
        f"{json.dumps(schema_hint, ensure_ascii=False)}\n"
        "Rules:\n"
        f"- daily_plan must have exactly {req.days} entries (day 1..days)\n"
        "- morning/afternoon/evening are arrays of short bullet strings\n"
        f"- map_points MUST be a NON-EMPTY array of {min_points}..{max_points} items\n"
        "- Every map_points item must have: name, query, day, category\n"
        f"- IMPORTANT: map_points.query MUST be geocodable and MUST include city name '{destination}' and country 'Russia'\n"
        "- Use the user's requested language.\n"
    )

    user_payload = {
        "language": language,
        "destination": destination,
        "days": req.days,
        "nights": req.nights,
        "budget": req.budget,
        "interests": req.interests,
        "pace": req.pace,
        "companions": req.companions,
        "notes": req.notes,
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    )

    raw_text = (resp.choices[0].message.content or "").strip()
    json_text = _extract_json(raw_text)

    try:
        data = json.loads(json_text)
    except Exception as e:
        raise RuntimeError(f"Model did not return valid JSON: {e}. Raw: {raw_text[:500]}")

    # --- Диагностика (видно в Render Logs) ---
    raw_points = data.get("map_points") or []
    print("AI raw map_points count:", len(raw_points))

    # Валидируем основу (без lat/lng)
    data["map_points"] = []
    base = RouteResponse.model_validate(data)

    # Готовим вход для геокодинга
    points_in: List[Dict[str, Any]] = []
    for p in raw_points:
        if not isinstance(p, dict):
            continue
        name = (p.get("name") or "").strip()
        query = (p.get("query") or "").strip()
        if not name or not query:
            continue
        p2 = dict(p)
        p2["query"] = _normalize_query(query, destination)
        points_in.append(p2)

    # Уберём дубликаты query, сохраняя порядок
    seen: set[str] = set()
    uniq_queries: List[str] = []
    for p in points_in:
        q = p["query"]
        if q in seen:
            continue
        seen.add(q)
        uniq_queries.append(q)

    print("AI points_in for geocode:", len(points_in), "uniq_queries:", len(uniq_queries))

    geo = geocode_many(uniq_queries, delay_sec=geocode_delay)

    # Соберём точки
    out_points: List[MapPoint] = []
    for p in points_in:
        g = geo.get(p["query"])
        if not g:
            continue
        out_points.append(
            MapPoint(
                name=str(p.get("name")),
                query=str(p.get("query")),
                lat=float(g["lat"]),
                lng=float(g["lng"]),
                day=p.get("day"),
                category=p.get("category"),
            )
        )

    print("Geocoded out_points:", len(out_points))

    # Если ничего не нашли — вернём хотя бы пустой массив (фронт не упадёт)
    base.map_points = out_points or []
    return base
