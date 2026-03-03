import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.ai import generate_route_with_gpt
from app.schemas import RouteRequest, RouteResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем папку webapp, чтобы сервер мог отдавать HTML, CSS, JS
# В Render папка webapp находится на уровень выше папки api/app
current_dir = os.path.dirname(os.path.abspath(__file__))
webapp_dir = os.path.join(current_dir, "..", "..", "webapp")

if os.path.exists(webapp_dir):
    app.mount("/webapp", StaticFiles(directory=webapp_dir), name="webapp")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    # Теперь при заходе на корень мы отдаем твой дизайн!
    index_path = os.path.join(webapp_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "running (webapp not found)"}

@app.post("/route/generate", response_model=RouteResponse)
async def generate_route(req: RouteRequest):
    try:
        return generate_route_with_gpt(req)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
