import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

# Инициализация
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# --- НОВАЯ СИСТЕМА: ТОЛЬКО HTML, НИКАКИХ СПИСКОВ ---
SYSTEM_PROMPT = """
You are a Travel Book Author. 
Your goal is to write a continuous, immersive travel story (longread).

**RULES:**
1. **NO LISTS/BULLET POINTS.** Do not use markdown lists like "- ...".
2. **FORMAT:** You must output valid HTML.
   - Use `<h3>` for creative titles (e.g., "<h3>Day 1: The Red Heart of Moscow</h3>").
   - Use `<p>` for long, descriptive paragraphs (minimum 60 words per paragraph).
   - Use `<b>` for highlighting prices and key details inside the text.
3. **CONTENT:** For every location, weave in history, prices, and opening hours into the narrative.

**JSON OUTPUT FORMAT:**
Return a single JSON object:
{
  "summary": "Short intro (1 sentence)",
  "html_content": "<h3>Chapter 1...</h3><p>Long text...</p>..."
}
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API Key not set")

    user_content = f"""
    Write a Travel Story about {req.destination} for {req.days} days.
    Language: {req.language}.
    Wishes: {req.notes}.
    
    IMPORTANT: Output HTML. NO LISTS. Write paragraphs!
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=4000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
