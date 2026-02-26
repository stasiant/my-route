from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.schemas import RouteRequest, RouteResponse
from app.payments import create_stars_invoice_link

app = FastAPI(title="My Route API", version="0.1.0")

# Allow WebApp to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for MVP; later restrict to your domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP: store paid invoice payloads in memory (lost on restart)
# Key: telegram_payment_charge_id, Value: decoded invoice payload dict
PAID: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/route/generate", response_model=RouteResponse)
def generate_route(req: RouteRequest):
    # Demo implementation (stub). Later you replace with real generation.
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
        tips=["Buy a transport card", "Book popular museums in advance"],
        budget_notes=f"Budget level: {req.budget}",
        checklist=["Passport", "Insurance", "Power adapter"],
    )


# ----- Payments -----

class CreateInvoiceRequest(BaseModel):
    lang: str = "en"
    route_request: RouteRequest
    stars_amount: int = 50


class CreateInvoiceResponse(BaseModel):
    invoice_link: str


@app.post("/pay/create-invoice", response_model=CreateInvoiceResponse)
def pay_create_invoice(body: CreateInvoiceRequest):
    if body.stars_amount <= 0:
        raise HTTPException(400, "stars_amount must be > 0")

    if body.lang == "ru":
        title = "My Route: 1 маршрут"
        description = "Оплата генерации 1 маршрута"
    else:
        title = "My Route: 1 itinerary"
        description = "Payment for generating 1 itinerary"

    invoice_link = create_stars_invoice_link(
        title=title,
        description=description,
        stars_amount=body.stars_amount,
        payload={
            "type": "route_generation",
            "route_request": body.route_request.model_dump(),
        },
    )
    return CreateInvoiceResponse(invoice_link=invoice_link)


@app.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    update = await req.json()

    # 1) Pre-checkout query must be answered, иначе оплата не пройдет
    if "pre_checkout_query" in update:
        pcq = update["pre_checkout_query"]

        import os
        import requests

        token = os.getenv("BOT_TOKEN", "")
        if not token:
            raise HTTPException(500, "BOT_TOKEN missing")

        url = f"https://api.telegram.org/bot{token}/answerPreCheckoutQuery"
        r = requests.post(url, json={"pre_checkout_query_id": pcq["id"], "ok": True}, timeout=20)
        r.raise_for_status()
        return {"ok": True}

    # 2) Successful payment arrives in message.successful_payment
    msg = update.get("message") or update.get("edited_message")
    if msg and msg.get("successful_payment"):
        sp = msg["successful_payment"]
        payment_id = sp.get("telegram_payment_charge_id")
        invoice_payload = sp.get("invoice_payload")  # stringified JSON that we set in createInvoiceLink

        decoded: Dict[str, Any] = {}
        if invoice_payload:
            import json
            try:
                decoded = json.loads(invoice_payload)
            except Exception:
                decoded = {}

        if payment_id:
            PAID[payment_id] = decoded

        return {"ok": True}

    return {"ok": True}


class PayStatusResponse(BaseModel):
    paid: bool
    data: Optional[Dict[str, Any]] = None


@app.get("/pay/status/{payment_id}", response_model=PayStatusResponse)
def pay_status(payment_id: str):
    data = PAID.get(payment_id)
    return PayStatusResponse(paid=bool(data), data=data)
