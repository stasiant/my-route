import os
import json

from openai import OpenAI

from app.schemas import RouteRequest, RouteResponse


def _env_float(name: str, default: float) -> float:
    val = os.getenv(name)
    if not val:
        return default
    try:
        return float(val)
    except Exception:
        return default


def generate_route_with_gpt(req: RouteRequest) -> RouteResponse:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = _env_float("OPENAI_TEMPERATURE", 0.7)

    # timeout + retries, чтобы не висело бесконечно
    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)

    schema_hint = {
        "summary": "string",
        "daily_plan": [
            {
                "day": 1,
                "morning": ["string"],
                "afternoon": ["string"],
                "evening": ["string"],
            }
        ],
        "food": [{"name": "string", "type": "string"}],
        "tips": ["string"],
        "budget_notes": "string",
        "checklist": ["string"],
    }

    language = getattr(req, "language", None) or "ru"

    system = (
        "You are a travel itinerary planner.\n"
        "Return ONLY valid JSON (no markdown, no comments, no extra text).\n"
        "The JSON must match this structure exactly:\n"
        f"{json.dumps(schema_hint, ensure_ascii=False)}\n"
        "Rules:\n"
        "- daily_plan must have exactly req.days entries (day 1..days)\n"
        "- morning/afternoon/evening are arrays of short bullet strings\n"
        "- tips/checklist arrays should be concise\n"
        "- Use the user's requested language.\n"
    )

    user_payload = {
        "language": language,
        "destination": req.destination,
        "days": req.days,
        "nights": req.nights,
        "budget": req.budget,
        "interests": req.interests,
        "pace": req.pace,
        "companions": req.companions,
        "notes": req.notes,
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    )

    text = (resp.choices[0].message.content or "").strip()

    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Model did not return valid JSON: {e}. Raw: {text[:500]}")

    return RouteResponse.model_validate(data)
