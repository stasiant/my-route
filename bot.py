import asyncio
import os
import logging
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

# --- РИСУЕМ ПРАВИЛЬНУЮ СЕРУЮ КНОПКУ ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    web_app_url = "https://my-route-api.onrender.com/webapp/index.html" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    
    await message.answer(
        "Привет! Нажми СЕРУЮ кнопку внизу экрана 👇\n\n(Не нажимай синюю кнопку Menu слева, она не умеет сохранять маршруты!)",
        reply_markup=markup
    )

# --- ЛОВИМ МАРШРУТ И ОТПРАВЛЯЕМ В ЧАТ ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = message.web_app_data.data
    
    print(f"\n[УСПЕХ] Получен маршрут! Длина: {len(data)} символов.")
    
    try:
        # Если маршрут огромный (лонгрид от ИИ), режем его на куски, иначе Телеграм выдаст ошибку
        if len(data) > 4000:
            for x in range(0, len(data), 4000):
                await message.answer(data[x:x+4000], parse_mode=ParseMode.HTML)
        else:
            await message.answer(data, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"[ОШИБКА HTML] {e}")
        # Если ИИ прислал кривой тег, отправляем как простой текст
        await message.answer(data)

async def main():
    print("Бот запущен. Переходи в Телеграм и жми /start")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
