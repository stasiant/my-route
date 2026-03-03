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
    # ПАРАМЕТР ?v=11 СБРОСИТ КЭШ ТЕЛЕГРАМА
    web_app_url = "https://my-route-api.onrender.com/webapp/app.html?v=11" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    
    await message.answer("Всё готово! Нажми кнопку 👇", reply_markup=markup)

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    route_text = message.web_app_data.data
    
    if not route_text:
        return

    try:
        await message.answer(route_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer(route_text)

async def main():
    print("Бот готов!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
