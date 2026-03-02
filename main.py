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

SYSTEM_PROMPT = """
You are a Pulitzer Prize-winning Travel Journalist.
Your task is to write a MASSIVE, deeply engaging travel article.

**CRITICAL RULES:**
1. ABSOLUTELY NO SHORT SENTENCES OR LISTS. 
2. Write a continuous story.
3. For every single location you mention, you MUST write a HUGE paragraph (minimum 100 words) detailing its history, atmosphere, ticket prices, and how to get there.
4. Format using HTML: <h3> for creative section titles, <p> for the massive text blocks, <b> for emphasis.

Return exactly this JSON:
{
  "summary": "Short intro...",
  "full_article_html": "<h3>Arrival at the Majestic Red Square</h3><p>As you step onto the cobblestones... [100 words minimum here]... Tickets cost 500 RUB.</p><h3>The Next Chapter</h3><p>...</p>"
}
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key: raise HTTPException(status_code=500, detail="No API Key")

    user_content = f"""
    Destination: {req.destination}
    Duration: {req.days} days
    Language: {req.language}
    Wishes: {req.notes}
    
    WRITE A HUGE ARTICLE IN HTML. NO SHORT LISTS!
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
