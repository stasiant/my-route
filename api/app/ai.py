import json
import os
from typing import Any, Dict, List
from openai import OpenAI
from app.geocode import geocode_many
from app.schemas import MapPoint, RouteRequest, RouteResponse

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name) or default)
    except:
        return default

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name) or default)
    except:
        return default

def _normalize_query(q: str, destination: str) -> str:
    q = (q or "").strip()
    if not q: return q
    low = q.lower()
    dest_low = (destination or "").strip().lower()
    if dest_low and dest_low not in low:
        q = f"{q}, {destination}"
    return q

def _extract_json(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"): return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start: return text[start : end + 1]
    return text

def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    client = OpenAI(api_key=api_key, timeout=60.0)

    # --- НОВАЯ СХЕМА: ТРЕБУЕМ HTML_CONTENT ---
    schema_hint = {
        "summary": "Short intro string",
        "html_content": "<h3>Day 1: Title</h3><p>Long paragraph...</p>",
        "map_points": [{"name": "Place Name", "query": "Place Name, City", "day": 1, "category": "museum"}]
    }

    destination = (req.destination or "").strip()

    # --- НОВЫЙ ПРОМПТ: APPLE NEWS STYLE ---
    system = (
        "You are a Travel Editor for Apple News.\n"
        "Your goal is to write a PREMIUM TRAVEL GUIDE (Longread).\n"
        "Return ONLY valid JSON matching the structure below.\n"
        f"{json.dumps(schema_hint, ensure_ascii=False)}\n\n"
        "RULES:\n"
        "1. **html_content**: This is the main field. Write a full HTML article here.\n"
        "   - Use `<h3>` for Day/Location titles.\n"
        "   - Use `<p>` for LONG, detailed paragraphs (history, prices, atmosphere).\n"
        "   - Use `<b>` for emphasis.\n"
        "   - NO LISTS (<ul>/<li>). Write narrative text.\n"
        "2. **map_points**: Generate 5-10 key locations for the map.\n"
        f"3. Language: {req.language or 'ru'}.\n"
    )

    user_payload = {
        "destination": destination,
        "days": req.days,
        "notes": req.notes,
        "budget": req.budget
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    )

    raw_text = resp.choices[0].message.content
    data = json.loads(_extract_json(raw_text))

    # Валидация и Геокодинг (оставляем твою логику, она хорошая)
    raw_points = data.get("map_points") or []
    base = RouteResponse.model_validate(data) # Теперь это сработает, т.к. мы обновили schemas.py
    
    # Подготовка точек
    uniq_queries = []
    points_in = []
    seen = set()
    
    for p in raw_points:
        if not isinstance(p, dict): continue
        q = _normalize_query(p.get("query"), destination)
        if q not in seen:
            seen.add(q)
            uniq_queries.append(q)
        # Копия точки с нормализованным запросом
        p_copy = p.copy()
        p_copy["query"] = q
        points_in.append(p_copy)

    # Геокодинг
    if uniq_queries:
        geo = geocode_many(uniq_queries, delay_sec=1.0)
        out_points = []
        for p in points_in:
            g = geo.get(p["query"])
            if g:
                out_points.append(MapPoint(
                    name=str(p.get("name")),
                    query=str(p.get("query")),
                    lat=float(g["lat"]),
                    lng=float(g["lng"]),
                    day=p.get("day"),
                    category=p.get("category")
                ))
        base.map_points = out_points

    return base
