import asyncio
import os
import logging
import json
import urllib.request
import re
import ssl  # ДОБАВИЛИ ИМПОРТ ДЛЯ SSL

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Нет токена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Фоновая функция для запроса к твоему API (С ИГНОРИРОВАНИЕМ SSL)
def fetch_route_sync(payload):
    url = "https://my-route-api.onrender.com/route/generate"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(payload).encode("utf-8")
    
    # === ВОТ ЭТОТ КОД РЕШАЕТ ОШИБКУ НА MAC ===
    context = ssl._create_unverified_context()
    
    with urllib.request.urlopen(req, data=data, timeout=120, context=context) as response:
        return json.loads(response.read().decode("utf-8"))

# Функция для конвертации HTML с сервера в красивый текст для Телеграма
def format_for_telegram(html: str) -> str:
    text = re.sub(r'<h2>(.*?)</h2>', r'\n\n<b>===== \1 =====</b>\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<h3>(.*?)</h3>', r'\n\n<b>🗓 \1</b>\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<b>(.*?)</b>', r'<b>\1</b>', text, flags=re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r'<i>\1</i>', text, flags=re.IGNORECASE)
    text = re.sub(r'<p>', r'', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', r'\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br/?>', r'\n', text, flags=re.IGNORECASE)
    return text.strip()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    web_app_url = "https://my-route-webapp.onrender.com" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    
    welcome_text = (
        "Привет! 🌍 Я твой персональный ИИ-редактор путешествий.\n\n"
        "Я создам для тебя идеальную историю поездки, учитывая твой бюджет, темп и компанию.\n\n"
        "Жми на кнопку внизу экрана 👇"
    )
    
    await message.answer(welcome_text, reply_markup=markup, parse_mode=ParseMode.HTML)

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
                f"Это займет около 30-40 секунд. Можешь свернуть бота или заблокировать телефон, я пришлю гид автоматически! 🚀",
                parse_mode=ParseMode.HTML
            )
            
            try:
                response_data = await asyncio.to_thread(fetch_route_sync, api_params)
                route_html = response_data.get("html_content", "")
                
                if not route_html:
                    await message.answer("❌ Извините, не удалось сгенерировать маршрут. Попробуйте еще раз.")
                    return
                
                route_text = f"<b>Маршрут: {dest} ({days} дн.)</b>\n\n" + format_for_telegram(route_html)
                
                if len(route_text) > 4000:
                    for x in range(0, len(route_text), 4000):
                        await message.answer(route_text[x:x+4000], parse_mode=ParseMode.HTML)
                else:
                    await message.answer(route_text, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"Ошибка API: {e}")
                await message.answer("❌ Произошла ошибка при составлении маршрута. Сервер не ответил вовремя.")
            return

    except json.JSONDecodeError:
        pass

async def main():
    print("Бот запущен. Проверка SSL отключена!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
