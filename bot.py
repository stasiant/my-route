import asyncio
import os
import logging
import json
import urllib.request
import re
import ssl

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

def fetch_route_sync(payload):
    url = "https://my-route-api.onrender.com/route/generate"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(payload).encode("utf-8")
    
    context = ssl._create_unverified_context()
    
    # Ждем до 3-х минут (14 дней генерируются долго!)
    with urllib.request.urlopen(req, data=data, timeout=180, context=context) as response:
        return json.loads(response.read().decode("utf-8"))

def format_for_telegram(html: str) -> str:
    text = re.sub(r'<h2>(.*?)</h2>', r'\n\n<b>===== \1 =====</b>\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<h3>(.*?)</h3>', r'\n\n<b>🗓 \1</b>\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<b>(.*?)</b>', r'<b>\1</b>', text, flags=re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r'<i>\1</i>', text, flags=re.IGNORECASE)
    text = re.sub(r'<p>', r'', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', r'\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br/?>', r'\n', text, flags=re.IGNORECASE)
    return text.strip()

# --- УМНАЯ НАРЕЗКА СООБЩЕНИЙ ---
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
            
    if current_chunk:
        chunks.append(current_chunk)
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
                f"Так как дней много, это займет около 1-2 минут. Можешь свернуть бота, я пришлю гид автоматически! 🚀",
                parse_mode=ParseMode.HTML
            )
            
            try:
                response_data = await asyncio.to_thread(fetch_route_sync, api_params)
                route_html = response_data.get("html_content", "")
                
                if not route_html:
                    await message.answer("❌ Извините, не удалось сгенерировать маршрут.")
                    return
                
                route_text = f"<b>МАРШРУТ: {dest} ({days} дн.)</b>\n\n" + format_for_telegram(route_html)
                
                # Отправляем умными кусками
                chunks = smart_split(route_text)
                for i, chunk in enumerate(chunks):
                    # Если кусков больше одного, добавляем нумерацию
                    prefix = f"<i>(Часть {i+1}/{len(chunks)})</i>\n\n" if len(chunks) > 1 else ""
                    try:
                        await message.answer(prefix + chunk, parse_mode=ParseMode.HTML)
                        await asyncio.sleep(0.5) # Пауза, чтобы Телеграм не ругался на спам
                    except Exception as e:
                        print(f"Ошибка отправки куска {i+1}: {e}")
                        # Фоллбэк: если HTML все-таки сломался, шлем без форматирования
                        await message.answer(prefix + chunk)

            except Exception as e:
                print(f"Ошибка API: {e}")
                await message.answer("❌ Произошла ошибка при составлении маршрута.")
            return

    except json.JSONDecodeError:
        pass

async def main():
    print("Бот запущен. Умная нарезка включена!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
