import json
import os
import re
import urllib.request
import urllib.parse
from openai import OpenAI
from app.schemas import RouteRequest, RouteResponse

def _extract_json(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    if text.startswith("{") and text.endswith("}"): return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start: return text[start : end + 1]
    return text

def get_yandex_coords(query: str, api_key: str) -> str:
    if not api_key: return "📍 <i>[Нет ключа Яндекса]</i>"
    try:
        url = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            features = res.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
            if not features: return "📍 <i>[Место не найдено]</i>"
            pos = features[0]["GeoObject"]["Point"]["pos"]
            lon, lat = pos.split(" ")
            return f"📍 <b>({round(float(lat), 5)}, {round(float(lon), 5)})</b>"
    except Exception as e:
        print(f"Yandex Error for '{query}': {e}")
        return "📍 <i>[Ошибка связи с Яндексом]</i>"

def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    yandex_key = os.getenv("YANDEX_API_KEY")
    
    client = OpenAI(api_key=api_key, timeout=120.0)

    # --- СТРОГОЕ УКАЗАНИЕ ИИ СДЕЛАТЬ ВСЕ ДНИ ---
    system = (
        f"Ты — профессиональный гид. Твоя задача — составить маршрут РОВНО НА {req.days} ДНЕЙ. "
        "ЗАПРЕЩЕНО обрывать маршрут раньше времени. Опиши каждый день от 1 до {req.days}.\n\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. Минимум 3 ДОСТОПРИМЕЧАТЕЛЬНОСТИ в день.\n"
        "2. КООРДИНАТЫ: Рядом с названием КАЖДОГО места ставь тег {GEO: Название места, Город}. Используй ФИГУРНЫЕ скобки!\n"
        "3. ЛОГИСТИКА: Если идти менее 30 минут, ПРЕДЛАГАЙ ТОЛЬКО ПЕШУЮ ПРОГУЛКУ.\n"
        "4. Формат вывода — строго HTML.\n\n"
        "ШАБЛОН ДНЯ:\n"
        "<h3>День X: [Название дня]</h3>\n"
        "<p><b>1. [Место]</b> {GEO: Место, Город}. [Описание].</p>\n"
        "<p><i>👣 Как добраться...</i></p>\n"
        "Верни JSON с полем 'html_content'."
    )

    budget_desc = {"economy": "Эконом", "medium": "Средний", "high": "Комфорт", "premium": "Премиум"}.get(req.budget, "Средний")

    user_payload = {
        "destination": req.destination, "days": req.days,
        "notes": f"{req.notes}. Бюджет: {budget_desc}. Компания: {req.companions}",
        "lang": req.language
    }

    # Увеличиваем max_tokens до 10000, чтобы вместить 14 дней!
    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.6, max_tokens=10000,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
        response_format={"type": "json_object"}
    )

    data = json.loads(_extract_json(resp.choices[0].message.content))
    html = data.get("html_content", "")

    if html:
        def replacer(match):
            query = match.group(1).strip()
            return get_yandex_coords(query, yandex_key)
        html = re.sub(r'\{GEO:(.*?)\}', replacer, html)
        data["html_content"] = html

    return RouteResponse(
        summary=data.get("summary", ""),
        html_content=data.get("html_content"),
        daily_plan=[], map_points=[]
    )
