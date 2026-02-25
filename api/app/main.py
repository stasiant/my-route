from fastapi import FastAPI

app = FastAPI(title="My Route API")

@app.get("/health")
def health():
    return {"status": "ok"}
