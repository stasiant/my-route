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

# --- СТРОЖАЙШИЙ ЗАПРЕТ НА СПИСКИ ---
SYSTEM_PROMPT = """
You are a Travel Novelist. 
You DO NOT write guides. You write **immersive travel stories**.

**ABSOLUTE RULES:**
1. **FORBIDDEN:** Do not use JSON keys like "morning", "afternoon", "evening".
2. **FORBIDDEN:** Do not use bullet points or lists.
3. **REQUIRED:** Write valid HTML. Use `<h3>` for chapter titles (e.g., "Day 1: Arrival") and `<p>` for text.
4. **LENGTH:** Each paragraph MUST be at least 80 words long. Detail the history, the smells, the prices, the logistics.

**OUTPUT FORMAT:**
Return a JSON object with a single key "travel_book_chapter":
{
  "summary": "Intro...",
  "travel_book_chapter": "<h3>Chapter 1</h3><p>As you step onto the pavement...</p>"
}
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key: raise HTTPException(status_code=500, detail="No API Key")

    user_content = f"""
    Write a story about {req.destination} ({req.days} days).
    Language: {req.language}.
    User notes: {req.notes}.
    
    IMPORTANT: Return JSON with key 'travel_book_chapter'. HTML format. Long paragraphs only.
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
