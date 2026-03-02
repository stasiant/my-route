import os
import json
import asyncio
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

# --- НОВАЯ ИНСТРУКЦИЯ: ИИ САМ СТРУКТУРИРУЕТ ТЕКСТ ---
SYSTEM_PROMPT = """
You are a Travel Book Author. 
Your task is to write a **continuous, engaging travel story** (longread).

**RULES:**
1.  **NO "Day 1" HEADERS:** Do not strictly separate days unless it fits the story flow.
2.  **NO LISTS:** Do not use bullet points. Write full paragraphs.
3.  **USE HTML:** You control the formatting.
    - Use `<h3>` for your own creative titles (e.g., "<h3>Arrival and the Red Square</h3>").
    - Use `<p>` for text.
    - Use `<b>` for highlighting places/prices.
4.  **CONTENT:** Include history, prices, and logistics naturally in the text.

**JSON STRUCTURE:**
Return a JSON with a single "content" field containing the entire HTML article.
{
  "summary": "Short intro...",
  "full_article_html": "<h3>Chapter 1: The Heart of the City</h3><p>Start your journey at...</p><h3>Next Morning</h3><p>..."
}
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key: raise HTTPException(status_code=500, detail="No API Key")

    user_content = f"""
    Write a travel story about {req.destination} for {req.days} days.
    Travelers: {req.companions}. Budget: {req.budget}.
    Language: {req.language}.
    Wishes: {req.notes}.
    
    IMPORTANT: Return valid JSON with 'full_article_html'. Do not use bullet points. Write a story.
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.8, # Больше креатива
            max_tokens=4000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
