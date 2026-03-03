import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Если токена нет, скрипт упадет с понятной ошибкой
if not TOKEN:
    raise ValueError("Нет токена! Укажи переменную окружения TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    # ВАЖНО: Замени URL на адрес твоего приложения на Render
    web_app_url = "https://my-route-api.onrender.com" 
    
    builder.button(text="🚀 Создать маршрут", web_app=WebAppInfo(url=web_app_url))
    
    await message.answer(
        "Привет! Я помогу спланировать путешествие.\nНажми кнопку ниже, чтобы начать.",
        reply_markup=builder.as_markup()
    )

# --- ГЛАВНОЕ: Хэндлер, который ловит данные из Web App ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    # Получаем данные (наш текст маршрута)
    data = message.web_app_data.data
    
    try:
        # Телеграм не дает отправлять сообщения длиннее 4096 символов.
        # Если маршрут длинный, разбиваем его на части.
        if len(data) > 4096:
            for x in range(0, len(data), 4096):
                await message.answer(data[x:x+4096], parse_mode=ParseMode.HTML)
        else:
            await message.answer(data, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        # Если HTML кривой, отправляем как простой текст
        print(f"Ошибка отправки HTML: {e}")
        await message.answer(data)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
