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
    # Твоя ссылка на фронтенд
    web_app_url = "https://my-route-webapp.onrender.com" 
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )
    
    # Красивое приветственное сообщение
    welcome_text = (
        "Привет! 🌍 Я твой персональный ИИ-редактор путешествий.\n\n"
        "Я создам для тебя идеальную историю поездки, учитывая твой бюджет, темп и компанию.\n\n"
        "<b>Что я умею:</b>\n"
        "🗺 Писать подробные маршруты по дням\n"
        "🏛 Рассказывать историю и атмосферу мест\n"
        "💰 Подсказывать цены на билеты и еду\n"
        "🚇 Строить удобную логистику (как добраться)\n\n"
        "Жми на серую кнопку внизу экрана 👇"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=markup,
        parse_mode=ParseMode.HTML
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
    print("Бот с красивым приветствием запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
