import asyncio
import os
import logging
import json
import urllib.request
import urllib.parse
import re
import ssl
from openai import OpenAI

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery
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

# --- ПАМЯТЬ ДЛЯ ЗАКАЗОВ ---
# Мы сохраняем параметры маршрута сюда, пока пользователь оплачивает счет
pending_routes = {}

def get_yandex_coords(query: str, api_key: str) -> str:
    if not api_key: return "📍 <i>[Нет ключа]</i>"
    try:
        url = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(url)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=5, context=context) as response:
            res = json.loads(response.read().decode('utf-8'))
            features = res.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
            if not features: return "📍 <i>[Место не найдено]</i>"
            pos = features[0]["GeoObject"]["Point"]["pos"]
            lon, lat = pos.split(" ")
            return f"📍 <b>({round(float(lat), 5)}, {round(float(lon), 5)})</b>"
    except Exception as e:
        return "📍 <i>[Ошибка гео]</i>"

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
        "Привет! 🌍 Я твой ИИ-гид.\nСоздание идеального маршрута стоит <b>15 ⭐️ (Звезд Telegram)</b>. \nЕсли что-то пойдет не так, звезды вернутся автоматически!\n\nЖми на кнопку 👇",
        reply_markup=markup, parse_mode=ParseMode.HTML
    )

# 1. ПОЛУЧАЕМ ДАННЫЕ ИЗ WEB APP И ВЫСТАВЛЯЕМ СЧЕТ
@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = message.web_app_data.data
    try:
        payload = json.loads(data)
        if payload.get("action") == "generate_route":
            api_params = payload.get("params", {})
            dest = api_params.get("destination", "Город")
            days = api_params.get("days", "?")
            
            # Сохраняем параметры в память для этого пользователя
            user_id = message.from_user.id
            pending_routes[user_id] = api_params
            
            # Создаем цену (15 XTR - это Telegram Звезды)
            prices = [LabeledPrice(label=f"Маршрут в {dest} ({days} дн.)", amount=15)]
            
            await bot.send_invoice(
                chat_id=message.chat.id,
                title=f"Создание маршрута: {dest}",
                description=f"Персональный ИИ-гид напишет для вас подробный план на {days} дней с координатами и логистикой.",
                payload="route_payment_payload",
                provider_token="", # Обязательно пусто для Звезд!
                currency="XTR",
                prices=prices
            )
    except Exception as e:
        print(f"Ошибка парсинга WebApp: {e}")

# 2. ПОДТВЕРЖДЕНИЕ ПЛАТЕЖА ПЕРЕД СПИСАНИЕМ
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# 3. ПЛАТЕЖ ПРОШЕЛ УСПЕШНО -> ГЕНЕРИРУЕМ МАРШРУТ
@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    # Получаем уникальный ID платежа для возможного возврата
    charge_id = message.successful_payment.telegram_payment_charge_id 
    
    api_params = pending_routes.get(user_id)
    if not api_params:
        # Если почему-то нет параметров, возвращаем деньги сразу
        await bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
        await message.answer("❌ Ошибка: данные маршрута потерялись. Звезды возвращены!")
        return

    dest = api_params.get("destination", "Город")
    days = api_params.get("days", "?")
    
    await message.answer(f"⭐️ <b>Оплата получена!</b>\nНачинаю составлять маршрут: <b>{dest} на {days} дней</b>.\nПожалуйста, подождите 1-3 минуты 🚀", parse_mode=ParseMode.HTML)
    
    try:
        # Пытаемся сгенерировать
        response_data = await asyncio.to_thread(generate_route_local, api_params)
        route_html = response_data.get("html_content", "")
        
        if not route_html:
            raise ValueError("Пустой HTML от ИИ")
            
        route_text = f"<b>МАРШРУТ: {dest} ({days} дн.)</b>\n\n" + format_for_telegram(route_html)
        chunks = smart_split(route_text)
        
        for i, chunk in enumerate(chunks):
            prefix = f"<i>(Часть {i+1}/{len(chunks)})</i>\n\n" if len(chunks) > 1 else ""
            await message.answer(prefix + chunk, parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.5)
            
        # Удаляем из памяти после успеха
        del pending_routes[user_id]

    except Exception as e:
        print(f"Ошибка при генерации маршрута: {e}")
        # ==== ВОЗВРАТ ЗВЕЗД ПРИ ОШИБКЕ ====
        try:
            await bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
            await message.answer("❌ <b>Произошла ошибка при составлении маршрута (сбой ИИ).</b>\n\n✅ <b>Не переживайте, 15 ⭐️ были автоматически возвращены на ваш счет!</b> Попробуйте еще раз.", parse_mode=ParseMode.HTML)
        except Exception as refund_error:
            print(f"Ошибка возврата звезд: {refund_error}")
            await message.answer("❌ Произошла критическая ошибка. Напишите в поддержку.")

async def main():
    print("Бот запущен. ПОДКЛЮЧЕНЫ ТЕЛЕГРАМ ЗВЕЗДЫ (15 XTR) И АВТОВОЗВРАТ!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
