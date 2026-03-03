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

@dp.message(CommandStart())
async def cmd_start(message: Message):
    # ВОТ ОНА - ТВОЯ ПРАВИЛЬНАЯ ССЫЛКА
    web_app_url = "https://my-route-webapp.onrender.com" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    
    await message.answer(
        "Всё готово! Жми на кнопку внизу 👇",
        reply_markup=markup
    )

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    route_text = message.web_app_data.data
    
    try:
        # Режем лонгрид на куски, чтобы Телеграм не ругался на длину
        if len(route_text) > 4000:
            for x in range(0, len(route_text), 4000):
                await message.answer(route_text[x:x+4000], parse_mode=ParseMode.HTML)
        else:
            await message.answer(route_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Ошибка HTML: {e}")
        await message.answer(route_text)

async def main():
    print("Бот запущен с правильной ссылкой! Переходи в Телеграм.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
