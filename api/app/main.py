from fastapi import FastAPI
from .schemas import RouteRequest, RouteResponse

app = FastAPI(title="My Route API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/route/generate", response_model=RouteResponse)
def generate_route(req: RouteRequest):
    # TODO: здесь позже подключим оплату/проверку заказа и GPT API
    return RouteResponse(
        summary=f"Demo route for: {req.destination} ({req.days} days)",
        daily_plan=[
            {
                "day": 1,
                "morning": ["City walk", "Main square"],
                "afternoon": ["Museum", "Park"],
                "evening": ["Dinner area", "Sunset viewpoint"],
            }
        ],
        food=[{"name": "Local cafe", "type": "budget-friendly"}],
        tips=["Buy a transport card", "Book popular музеї заранее"],
        budget_notes=f"Budget level: {req.budget}",
        checklist=["Passport", "Insurance", "Power adapter"],
    )
