import json
import os
from openai import OpenAI
from app.schemas import RouteRequest, RouteResponse

def _extract_json(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"): return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start: return text[start : end + 1]
    return text

def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key, timeout=60.0)

    # Структура ответа
    schema_hint = {
        "summary": "Short intro string",
        "html_content": "<h3>Day 1...</h3><p>...</p>",
        "map_points": [] 
    }

    # Логика формирования контекста
    budget_desc = {
        "economy": "Strict Economy (Free spots, street food, walking)",
        "medium": "Balanced (Good value restaurants, standard tickets)",
        "high": "Comfort (Taxi, nice restaurants, guided tours)",
        "premium": "Luxury (Best hotels, fine dining, private drivers, exclusive access)"
    }.get(req.budget, "Medium")

    companion_desc = {
        "solo": "Solo Traveler (Focus on safety, social spots, or solitude)",
        "couple": "Romantic Couple (Atmospheric spots, nice dinners)",
        "family": "Family with Kids (Playgrounds, kid-friendly food, not too much walking)",
        "group": "Group of Friends (Bars, fun activities, active pace)"
    }.get(req.companions, "Couple")

    system = (
        "You are a Premium Travel Editor.\n"
        "Write a detailed HTML travel essay.\n"
        f"CONTEXT: Budget: {budget_desc}. Group: {companion_desc}.\n"
        "RULES:\n"
        "1. html_content: Use <h3> and <p>. NO LISTS.\n"
        "2. Tailor recommendations to the Budget and Group type.\n"
        f"JSON Format: {json.dumps(schema_hint)}\n"
    )

    user_payload = {
        "destination": req.destination,
        "days": req.days,
        "notes": req.notes,
        "lang": req.language
    }

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"}
    )

    data = json.loads(_extract_json(resp.choices[0].message.content))
    # Для упрощения пока возвращаем пустые точки карты, фокус на тексте
    return RouteResponse(
        summary=data.get("summary", ""),
        html_content=data.get("html_content"),
        daily_plan=[],
        map_points=[]
    )
