import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Нет токена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КНОПКА ОТКРЫТИЯ ПРИЛОЖЕНИЯ ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    # ВАЖНО: Добавляем путь к фронтенду! (Убедись, что index.html доступен по этому адресу)
    # Если твой фронтенд хостится на GitHub Pages, сюда нужно вставить ссылку на GitHub Pages.
    # Но пока попробуем так, если сервер раздает статику:
    web_app_url = "https://my-route-api.onrender.com/webapp/index.html" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "Привет! Нажми кнопку внизу экрана, чтобы создать маршрут 👇",
        reply_markup=markup
    )

# --- ЛОВИМ ДАННЫЕ ИЗ ПРИЛОЖЕНИЯ ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = message.web_app_data.data
    
    # Отправляем тестовое сообщение
    await message.answer(f"✅ Данные получены!\n\n{data}")

async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
