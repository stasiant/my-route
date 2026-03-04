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

# --- ФУНКЦИЯ ЗАПРОСА К ЯНДЕКС КАРТАМ ---
def get_yandex_coords(query: str, api_key: str) -> str:
    if not api_key:
        return "" # Если ключа нет, возвращаем пустоту
    try:
        url = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            # Яндекс возвращает координаты в формате "Долгота Широта"
            pos = res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
            lon, lat = pos.split(" ")
            # Округляем до 5 знаков после запятой
            return f"({round(float(lat), 5)}, {round(float(lon), 5)})"
    except Exception as e:
        print(f"Yandex Geocode Error for '{query}': {e}")
        return ""

def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    yandex_key = os.getenv("YANDEX_API_KEY") # <--- Ключ от Яндекса
    
    client = OpenAI(api_key=api_key, timeout=60.0)

    # --- ИНСТРУКЦИЯ ДЛЯ ИИ ---
    system = (
        "Ты — профессиональный гид-логист.\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. Минимум 3 ГЛАВНЫЕ ДОСТОПРИМЕЧАТЕЛЬНОСТИ на каждый день.\n"
        "2. КООРДИНАТЫ: ЗАПРЕЩЕНО писать координаты цифрами! Рядом с названием КАЖДОГО места ты ОБЯЗАН поставить тег [GEO: Название места, Город].\n"
        "   Пример: <b>Красная Площадь</b> [GEO: Красная Площадь, Москва].\n"
        "3. ЛОГИСТИКА: Между локациями обязательно пиши, как добраться.\n"
        "   ПРАВИЛО ПЕШЕХОДА: Если идти менее 30 минут, ПРЕДЛАГАЙ ТОЛЬКО ПЕШУЮ ПРОГУЛКУ. ЗАПРЕЩЕНО предлагать такси для коротких расстояний.\n"
        "4. Формат вывода — строго HTML.\n\n"
        "ШАБЛОН ДНЯ:\n"
        "<h3>День X: [Название дня]</h3>\n"
        "<p><b>1. [Место]</b> [GEO: Место, Город]. [Подробное описание: история, цены].</p>\n"
        "<p><i>👣 Как добраться: [Инструкция. Если <30 мин - 'Пешком X минут'].</i></p>\n"
        "<p><b>2. [Место]</b> [GEO: Место, Город]. [Описание...]</p>\n\n"
        "В конце добавь блок <h2>Полезные советы</h2>.\n"
        "Верни JSON с полем 'html_content'."
    )

    budget_desc = {"economy": "Эконом", "medium": "Средний", "high": "Комфорт", "premium": "Премиум"}.get(req.budget, "Средний")

    user_payload = {
        "destination": req.destination, "days": req.days,
        "notes": f"{req.notes}. Бюджет: {budget_desc}. Компания: {req.companions}",
        "lang": req.language
    }

    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.6, 
        messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
        response_format={"type": "json_object"}
    )

    data = json.loads(_extract_json(resp.choices[0].message.content))
    html = data.get("html_content", "")

    # --- ЗАМЕНЯЕМ ТЕГИ [GEO: ...] НА РЕАЛЬНЫЕ КООРДИНАТЫ ---
    if html:
        # Находим все теги вида [GEO: Что-то там]
        geo_tags = set(re.findall(r'$$GEO:(.*?)$$', html))
        for tag in geo_tags:
            query = tag.strip()
            # Запрашиваем Яндекс
            coords = get_yandex_coords(query, yandex_key)
            # Заменяем тег в тексте на координаты (или на пустоту, если не нашли)
            html = html.replace(f"[GEO:{tag}]", coords)
            
        data["html_content"] = html

    return RouteResponse(
        summary=data.get("summary", ""),
        html_content=data.get("html_content"),
        daily_plan=[], map_points=[]
    )
