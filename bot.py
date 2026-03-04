import asyncio
import os
import logging
import json
import urllib.request
import urllib.parse
import re
import ssl  # <--- ИМПОРТИРУЕМ SSL
from openai import OpenAI

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")

if not TOKEN:
    raise ValueError("Нет токена Telegram!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ФУНКЦИЯ ЯНДЕКСА (С ФИКСОМ ДЛЯ MAC) ---
def get_yandex_coords(query: str, api_key: str) -> str:
    if not api_key: return "📍 <i>[Нет ключа Яндекса]</i>"
    try:
        url = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(url)
        
        # ОТКЛЮЧАЕМ ПРОВЕРКУ SSL ДЛЯ МУКА
        context = ssl._create_unverified_context()
        
        with urllib.request.urlopen(req, timeout=5, context=context) as response:
            res = json.loads(response.read().decode('utf-8'))
            features = res.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
            if not features: return "📍 <i>[Место не найдено]</i>"
            pos = features[0]["GeoObject"]["Point"]["pos"]
            lon, lat = pos.split(" ")
            return f"📍 <b>({round(float(lat), 5)}, {round(float(lon), 5)})</b>"
    except Exception as e:
        print(f"Yandex Error for '{query}': {e}")
        return "📍 <i>[Ошибка связи с Яндексом]</i>"

def extract_json(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```json"): text = text.replace("```json", "").replace("```", "").strip()
    if text.startswith("{") and text.endswith("}"): return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start: return text[start : end + 1]
    return text

def generate_route_local(payload: dict) -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY, timeout=300.0)
    
    days = payload.get("days", 3)
    system = (
        f"Ты — профессиональный гид. Твоя задача — составить маршрут РОВНО НА {days} ДНЕЙ. "
        f"ЗАПРЕЩЕНО обрывать маршрут раньше времени. Опиши каждый день от 1 до {days}.\n\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. Минимум 3 ДОСТОПРИМЕЧАТЕЛЬНОСТИ в день.\n"
        "2. КООРДИНАТЫ: Рядом с названием КАЖДОГО места ставь тег {GEO: Название места, Город}.\n"
        "3. ЛОГИСТИКА: Если идти менее 30 минут, ПРЕДЛАГАЙ ТОЛЬКО ПЕШУЮ ПРОГУЛКУ.\n"
        "4. Формат вывода — строго HTML.\n\n"
        "ШАБЛОН ДНЯ:\n"
        "<h3>День X: [Название дня]</h3>\n"
        "<p><b>1. [Место]</b> {GEO: Место, Город}. [Описание].</p>\n"
        "<p><i>👣 Как добраться...</i></p>\n"
        "Верни JSON с полем 'html_content'."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.6, max_tokens=10000,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        response_format={"type": "json_object"}
    )

    data = json.loads(extract_json(resp.choices[0].message.content))
    html = data.get("html_content", "")

    if html:
        def replacer(match):
            query = match.group(1).strip()
            return get_yandex_coords(query, YANDEX_API_KEY)
        html = re.sub(r'\{GEO:(.*?)\}', replacer, html)
        data["html_content"] = html

    return data

def format_for_telegram(html: str) -> str:
    text = re.sub(r'<h2>(.*?)</h2>', r'\n\n<b>===== \1 =====</b>\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<h3>(.*?)</h3>', r'\n\n<b>🗓 \1</b>\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<b>(.*?)</b>', r'<b>\1</b>', text, flags=re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r'<i>\1</i>', text, flags=re.IGNORECASE)
    text = re.sub(r'<p>', r'', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', r'\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br/?>', r'\n', text, flags=re.IGNORECASE)
    return text.strip()

def smart_split(text: str, max_len: int = 4000) -> list:
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 <= max_len:
            current_chunk += ("\n\n" + p) if current_chunk else p
        else:
            if current_chunk: chunks.append(current_chunk)
            current_chunk = p
    if current_chunk: chunks.append(current_chunk)
    return chunks

@dp.message(CommandStart())
async def cmd_start(message: Message):
    web_app_url = "https://my-route-webapp.onrender.com" 
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! 🌍 Я твой персональный ИИ-редактор путешествий.\nЖми на кнопку внизу экрана 👇",
        reply_markup=markup
    )

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = message.web_app_data.data
    try:
        payload = json.loads(data)
        if payload.get("action") == "generate_route":
            api_params = payload.get("params", {})
            dest = api_params.get("destination", "Город")
            days = api_params.get("days", "?")
            
            await message.answer(
                f"⏳ <b>Принято!</b>\nНачинаю составлять маршрут: <b>{dest} на {days} дней</b>.\n\n"
                f"Я работаю автономно! ИИ пишет текст, это займет 1-3 минуты. Я пришлю всё автоматически. 🚀",
                parse_mode=ParseMode.HTML
            )
            
            try:
                response_data = await asyncio.to_thread(generate_route_local, api_params)
                route_html = response_data.get("html_content", "")
                
                if not route_html:
                    await message.answer("❌ Извините, не удалось сгенерировать маршрут.")
                    return
                
                route_text = f"<b>МАРШРУТ: {dest} ({days} дн.)</b>\n\n" + format_for_telegram(route_html)
                
                chunks = smart_split(route_text)
                for i, chunk in enumerate(chunks):
                    prefix = f"<i>(Часть {i+1}/{len(chunks)})</i>\n\n" if len(chunks) > 1 else ""
                    try:
                        await message.answer(prefix + chunk, parse_mode=ParseMode.HTML)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Ошибка отправки куска {i+1}: {e}")
                        await message.answer(prefix + chunk)

            except Exception as e:
                print(f"Ошибка AI: {e}")
                await message.answer("❌ Произошла ошибка при составлении маршрута.")
            return

    except json.JSONDecodeError:
        pass

async def main():
    print("Бот запущен. НОВАЯ ЛОГИКА: AI + YANDEX С ОТКЛЮЧЕННЫМ SSL!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
