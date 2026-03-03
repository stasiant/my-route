import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    # Ссылка на твой фронтенд
    web_app_url = "https://my-route-api.onrender.com/webapp/index.html" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    await message.answer("Нажми кнопку внизу 👇", reply_markup=markup)

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = message.web_app_data.data
    
    try:
        # Разбиваем на части, если маршрут очень длинный
        if len(data) > 4000:
            for x in range(0, len(data), 4000):
                await message.answer(data[x:x+4000], parse_mode=ParseMode.HTML)
        else:
            await message.answer(data, parse_mode=ParseMode.HTML)
    except Exception as e:
        # Если HTML невалидный, шлем как текст
        await message.answer(data)

async def main():
    print("Бот готов к работе!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
