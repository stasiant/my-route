from typing import List, Optional, Any
from pydantic import BaseModel

class MapPoint(BaseModel):
    name: str
    query: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    day: Optional[int] = None
    category: Optional[str] = None

class RouteRequest(BaseModel):
    language: str = "ru"
    destination: str
    days: int
    nights: Optional[int] = None
    budget: str = "medium"
    pace: str = "medium"
    companions: str = "couple"
    interests: List[str] = []
    notes: str = ""

class RouteResponse(BaseModel):
    summary: str
    # Делаем план необязательным, так как теперь у нас html_content
    daily_plan: Optional[List[Any]] = None 
    map_points: List[MapPoint] = []
    # НОВОЕ ПОЛЕ ДЛЯ КНИГИ/СТАТЬИ
    html_content: Optional[str] = None
