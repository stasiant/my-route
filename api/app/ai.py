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

    # --- ЖЕСТКИЙ ПЛАН: 3 МЕСТА + ЛОГИСТИКА ---
    system = (
        "Ты — профессиональный гид-логист.\n"
        "Твоя задача — составить ИДЕАЛЬНЫЙ маршрут с учетом логистики перемещений.\n\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. Минимум 3 ГЛАВНЫЕ ДОСТОПРИМЕЧАТЕЛЬНОСТИ на каждый день.\n"
        "2. МЕЖДУ локациями обязательно пиши, как добраться (пешком, метро, такси).\n"
        "3. Формат вывода — HTML (без Markdown).\n\n"
        "ШАБЛОН ДНЯ (Используй именно этот формат):\n"
        "<h3>День X: [Название дня]</h3>\n"
        "<p><b>1. [Название места 1]</b>. [Описание 2-3 предложения: что смотреть, цены].</p>\n"
        "<p><i>👣 Как добраться: [Четкая инструкция: 10 мин пешком по ул. Ленина / Метро до станции...]</i></p>\n"
        "<p><b>2. [Название места 2]</b>. [Описание...]</p>\n"
        "<p><i>🚕 Как добраться: [Инструкция...]</i></p>\n"
        "<p><b>3. [Название места 3]</b>. [Описание...]</p>\n"
        "<p><b>🍽 Ужин:</b> [Рекомендация ресторана рядом].</p>\n\n"
        "В конце добавь блок <h2>Полезные советы</h2> (Транспорт, Жилье, Бюджет).\n"
        "Верни JSON с полем 'html_content'."
    )

    budget_desc = {
        "economy": "Эконом (пешком, метро)",
        "medium": "Средний (такси иногда)",
        "premium": "Премиум (VIP такси)"
    }.get(req.budget, "Средний")

    user_payload = {
        "destination": req.destination,
        "days": req.days,
        "notes": f"{req.notes}. Бюджет: {budget_desc}. Компания: {req.companions}",
        "lang": req.language
    }

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6, # Чуть строже, чтобы соблюдал структуру
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"}
    )

    data = json.loads(_extract_json(resp.choices[0].message.content))
    return RouteResponse(
        summary=data.get("summary", ""),
        html_content=data.get("html_content"),
        daily_plan=[],
        map_points=[]
    )
