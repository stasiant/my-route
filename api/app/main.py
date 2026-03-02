import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.ai import generate_route_with_gpt
from app.schemas import RouteRequest, RouteResponse

app = FastAPI()

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ВАЖНО: ЭТОТ БЛОК НУЖЕН ДЛЯ RENDER ---
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "running"}
# -----------------------------------------

@app.post("/route/generate", response_model=RouteResponse)
async def generate_route(req: RouteRequest):
    try:
        # Вызываем логику из ai.py (который мы исправили в прошлом шаге)
        return generate_route_with_gpt(req)
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
