from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any

Budget = Literal["low", "medium", "high", "premium"]
Pace = Literal["slow", "normal", "fast"]
Companions = Literal["solo", "couple", "family", "group"]

class RouteRequest(BaseModel):
    language: Literal["ru", "en"] = "ru"
    destination: str
    days: int
    nights: Optional[int] = None
    budget: Budget = "medium"
    interests: List[str] = []
    pace: Pace = "normal"
    companions: Companions = "solo"
    notes: Optional[str] = None

class RouteResponse(BaseModel):
    summary: str
    daily_plan: List[Dict[str, Any]]
    food: List[Dict[str, Any]]
    tips: List[str]
    budget_notes: str
    checklist: List[str]
