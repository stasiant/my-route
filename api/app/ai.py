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

    schema_hint = {
        "summary": "Short intro string",
        "html_content": "Full HTML formatted article",
        "map_points": [] 
    }

    budget_desc = {
        "economy": "Эконом (бесплатные места, недорогие кафе, пешком)",
        "medium": "Средний (кафе, платные музеи, такси)",
        "high": "Комфорт (хорошие рестораны, экскурсии)",
        "premium": "Премиум (лучшие рестораны, индивидуальные туры)"
    }.get(req.budget, "Средний")

    companion_desc = {
        "solo": "Один",
        "couple": "Пара",
        "family": "Семья с детьми",
        "group": "Компания друзей"
    }.get(req.companions, "Пара")

    # --- ЖЕСТКИЙ ШАБЛОН ДЛЯ ИИ ---
    system = (
        "Ты профессиональный трэвел-журналист и гид.\n"
        "Твоя задача — составить маршрут СТРОГО по указанному HTML-шаблону.\n"
        f"УЧИТЫВАЙ: Бюджет - {budget_desc}, Компания - {companion_desc}.\n\n"
        "ОБЯЗАТЕЛЬНЫЙ ШАБЛОН ОТВЕТА (используй ровно эти теги):\n"
        "<p>[Вступительный абзац о городе и поездке]</p>\n\n"
        "<h2>Маршрут по [Город] на [Кол-во] дней</h2>\n\n"
        "<h3>День 1: [Название дня, например: Сердце столицы]</h3>\n"
        "<p>[Короткое описание логики первого дня]</p>\n"
        "<p><b>[Название локации 1]</b>. [Подробное описание, что посмотреть, сколько заложить времени, цены]</p>\n"
        "<p><b>[Название локации 2]</b>. [Подробное описание...]</p>\n"
        "<p><b>[Обед/Ужин]</b>. [Рекомендация заведения]</p>\n\n"
        "...(Повторить для каждого дня)...\n\n"
        "<h2>Полезные советы для поездки</h2>\n"
        "<p><b>Транспорт:</b> [Как перемещаться, какие карты купить]</p>\n"
        "<p><b>Проживание:</b> [В каком районе лучше жить]</p>\n"
        "<p><b>Бюджет:</b> [Примерные цены на еду и билеты]</p>\n"
        "<p><b>Совет:</b> [Лайфхак или важная особенность]</p>\n\n"
        "Верни ответ в формате JSON:\n"
        f"{json.dumps(schema_hint)}"
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
    return RouteResponse(
        summary=data.get("summary", ""),
        html_content=data.get("html_content"),
        daily_plan=[],
        map_points=[]
    )
