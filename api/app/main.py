import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class RouteRequest(BaseModel):
    language: str
    destination: str
    days: int
    budget: str
    pace: str
    companions: str
    interests: list[str] = []
    notes: str = ""

# ПРОМПТ: ПИШЕМ КНИГУ/СТАТЬЮ
SYSTEM_PROMPT = """
You are an Editor for Apple News Travel.
You write immersive, high-quality travel essays.

**RULES:**
1. **NO LISTS.** Do not use bullet points. Write fluid, narrative text.
2. **FORMAT:** Output valid HTML.
   - Use `<h3>` for chapter titles (e.g. "Day 1: The Arrival").
   - Use `<p>` for paragraphs.
   - Use `<b>` to highlight key locations or prices within the text.
3. **DEPTH:** Each section must be detailed (history, atmosphere, logistics).

**OUTPUT JSON:**
{
  "summary": "One sentence intro.",
  "book_content": "<h3>Chapter 1</h3><p>...</p>"
}
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key: raise HTTPException(status_code=500, detail="No API Key")

    user_content = f"Write a travel essay about {req.destination} ({req.days} days). Lang: {req.language}. Notes: {req.notes}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
