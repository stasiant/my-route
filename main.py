import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

# Проверяем ключ API
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

app = FastAPI()

# Разрешаем запросы с любого сайта (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель данных, которую мы ждем от фронтенда
class RouteRequest(BaseModel):
    language: str
    destination: str
    days: int
    budget: str
    pace: str
    companions: str
    interests: list[str] = []
    notes: str = ""

# --- НОВЫЙ МОЩНЫЙ СИСТЕМНЫЙ ПРОМПТ ---
SYSTEM_PROMPT = """
You are a professional Travel Journalist for National Geographic.
Your task is to write a HIGHLY DETAILED, IMMERSIVE travel guide.

RULES FOR CONTENT:
1.  **NO SHORT LISTS.** Write like a book or a blog article.
2.  **DETAILS ARE MANDATORY.** For every single location/activity, you MUST include:
    *   **History & Atmosphere:** What makes it special? (2-3 sentences)
    *   **Logistics:** How to get there? (Metro station, walking distance)
    *   **Cost:** Approximate ticket price or average check in local currency.
    *   **Hours:** Opening hours or best time to visit.
3.  **FORMAT:** Start every item with the location name wrapped in <b> tag.
    Example: "<b>The Louvre Museum.</b> This iconic palace..."
4.  **STRUCTURE:** Do NOT label items as "Morning" or "Evening" inside the text. Just provide the rich content.

Your output must be a valid JSON object with this exact structure:
{
  "summary": "A captivating intro about the trip (max 30 words).",
  "daily_plan": [
    {
      "day": 1,
      "morning": ["<b>Location 1</b>. Long description with prices...", "<b>Location 2</b>. Long description..."],
      "afternoon": ["<b>Location 3</b>. Long description...", "<b>Location 4</b>. Long description..."],
      "evening": ["<b>Dinner Place</b>. Description of food and prices..."]
    }
  ],
  "map_points": [{"name": "Location 1"}, {"name": "Location 2"}]
}
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API Key not set on server")

    # Формируем запрос пользователя
    user_content = f"""
    Destination: {req.destination}
    Duration: {req.days} days
    Travelers: {req.companions}
    Budget: {req.budget}
    Pace: {req.pace}
    Interests: {', '.join(req.interests)}
    Specific Wishes: {req.notes}
    Language: {req.language} (The Output MUST be in {req.language}!)
    
    REMEMBER: Write LONG descriptions with PRICES and OPENING HOURS for every point.
    """

    try:
        # Запрос к OpenAI (GPT-4o-mini или GPT-3.5-turbo для скорости)
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # или "gpt-3.5-turbo", если 4o недоступна
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7, # Чуть выше креативность
            max_tokens=4000  # <--- УВЕЛИЧИЛИ ЛИМИТ ТОКЕНОВ, чтобы текст не обрезался
        )

        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        return data

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Запуск сервера (для локального теста)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
