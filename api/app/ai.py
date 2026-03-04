import json
import os
from openai import OpenAI
from app.schemas import RouteRequest, RouteResponse

def _extract_json(text: str) -> str:
    text = (text or "").strip()
    # Защита на случай, если ИИ обернет JSON в маркдаун
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    if text.startswith("{") and text.endswith("}"): return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start: return text[start : end + 1]
    return text

def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key, timeout=60.0)

    # --- ЖЕСТКИЙ ПЛАН: КООРДИНАТЫ + ЛОГИСТИКА (<30 МИН ПЕШКОМ) ---
    system = (
        "Ты — профессиональный гид-логист.\n"
        "Твоя задача — составить ИДЕАЛЬНЫЙ маршрут путешествия.\n\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. МИНИМУМ 3 ГЛАВНЫЕ ДОСТОПРИМЕЧАТЕЛЬНОСТИ на каждый день.\n"
        "2. КООРДИНАТЫ: Рядом с названием КАЖДОГО места обязательно пиши его реальные GPS-координаты (широта, долгота) в скобках.\n"
        "   Пример: <b>Красная площадь (55.7539, 37.6208)</b>.\n"
        "3. ЛОГИСТИКА: Между локациями обязательно пиши, как добраться.\n"
        "   ПРАВИЛО ПЕШЕХОДА: Если расстояние между точками занимает менее 30 минут пешком, ПРЕДЛАГАЙ ТОЛЬКО ПЕШУЮ ПРОГУЛКУ. ЗАПРЕЩЕНО предлагать такси или транспорт для коротких расстояний.\n"
        "4. Формат вывода — строго HTML.\n\n"
        "ШАБЛОН ДНЯ (Используй именно этот формат):\n"
        "<h3>День X: [Название дня]</h3>\n"
        "<p><b>1. [Название места] ([Координаты])</b>. [Подробное описание 3-4 предложения: история, цены, билеты].</p>\n"
        "<p><i>👣 Как добраться: [Четкая инструкция. Если <30 мин - пиши 'Пешком X минут'].</i></p>\n"
        "<p><b>2. [Название места] ([Координаты])</b>. [Описание...]</p>\n"
        "<p><i>🚇 Как добраться: [Инструкция...]</i></p>\n"
        "<p><b>3. [Название места] ([Координаты])</b>. [Описание...]</p>\n"
        "<p><b>🍽 Обед/Ужин ([Координаты]):</b> [Рекомендация ресторана рядом].</p>\n\n"
        "В конце добавь блок <h2>Полезные советы</h2> (Транспорт, Жилье, Бюджет).\n"
        "Верни JSON с полем 'html_content'."
    )

    # Интерпретация бюджета для ИИ
    budget_desc = {
        "economy": "Эконом (строго общественный транспорт и пешком)",
        "medium": "Средний (такси только для длинных поездок)",
        "high": "Комфорт (такси, если идти больше 20 мин)",
        "premium": "Премиум (удобные трансферы)"
    }.get(req.budget, "Средний")

    user_payload = {
        "destination": req.destination,
        "days": req.days,
        "notes": f"{req.notes}. Бюджет: {budget_desc}. Компания: {req.companions}",
        "lang": req.language
    }

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6, 
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
