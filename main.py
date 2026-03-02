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

# --- НОВАЯ ЛОГИКА: МЫ ПРОСИМ HTML, А НЕ СПИСКИ ---
SYSTEM_PROMPT = """
You are an expert Travel Writer and Historian.
Your goal is to write a Deep, Immersive, and Highly Practical Travel Guide.

**CRITICAL INSTRUCTION:**
Do NOT output lists or bullet points. You must write **Long, Rich Paragraphs** formatted in HTML.

For EACH location in the itinerary, you MUST cover:
1.  **Atmosphere & History:** 3-4 sentences description.
2.  **Practical Info:** Opening hours and Ticket prices (approximate).
3.  **Logistics:** How to get there from the previous point.

**JSON STRUCTURE:**
You must return a valid JSON object with this exact structure:
{
  "summary": "Short intro string...",
  "daily_plan": [
    {
      "day": 1,
      "content": "HTML STRING HERE" 
    }
  ],
  "map_points": [{"name": "Location 1"}, {"name": "Location 2"}]
}

**HTML FORMATTING RULES for 'content':**
- Use `<h3>` for Location Names.
- Use `<p>` for the text description.
- Use `<b>` for key details like **Price:** or **Hours:**.
- Combine multiple locations into one fluid narrative for the day.

Example of 'content':
"<h3>The Red Square</h3><p>The heart of Moscow... History... <b>Price:</b> Free entry. <b>Open:</b> 24/7.</p><h3>The Kremlin</h3><p>Next, walk 5 minutes to... Description... <b>Price:</b> 1000 RUB.</p>"
"""

@app.post("/route/generate")
async def generate_route(req: RouteRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="No API Key")

    user_content = f"""
    Destination: {req.destination}
    Duration: {req.days} days
    Language: {req.language} (Output MUST be in {req.language})
    Budget: {req.budget}
    Wishes: {req.notes}
    
    WRITE A LONGREAD. NO SHORT LISTS. INCLUDE PRICES AND LOGISTICS FOR EVERY STOP.
    """

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
