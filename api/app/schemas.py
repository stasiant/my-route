# api/app/schemas.py
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Budget = Literal["low", "medium", "high", "premium"]
Pace = Literal["slow", "normal", "fast"]
Companions = Literal["solo", "couple", "family", "group"]


class RouteRequest(BaseModel):
    language: Literal["ru", "en"] = "ru"
    destination: str
    days: int
    nights: Optional[int] = None
    budget: Budget = "medium"
    interests: List[str] = Field(default_factory=list)
    pace: Pace = "normal"
    companions: Companions = "solo"
    notes: Optional[str] = None


class MapPoint(BaseModel):
    name: str
    query: str  # что именно геокодим
    lat: float
    lng: float
    day: Optional[int] = None
    category: Optional[str] = None


class RouteResponse(BaseModel):
    summary: str
    daily_plan: List[Dict[str, Any]]
    food: List[Dict[str, Any]]
    tips: List[str]
    budget_notes: str
    checklist: List[str]

    # поле для карты: всегда массив
    map_points: List[MapPoint] = Field(default_factory=list)
