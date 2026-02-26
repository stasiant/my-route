from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging
import uuid
import json
import os
import requests

from app.schemas import RouteRequest, RouteResponse
from app.payments import create_stars_invoice_link

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="My Route API", version="0.1.0")

# Allow WebApp to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for MVP; later restrict to your domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP: store paid invoice payloads in memory (lost on restart)
# Key: telegram_payment_charge_id, Value: decoded invoice payload dict
PAID: Dict[str, Dict[str, Any]] = {}

# Optional: keep mapping order_id -> route_request (lost on restart)
ORDERS: Dict[str, Dict[str, Any]] = {}


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
    order_id: str


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

    # Create short valid payload for Telegram
    order_id = uuid.uuid4().hex
    telegram_payload = f"order:{order_id}"

    # Store order data in memory (MVP)
    ORDERS[order_id] = {
        "type": "route_generation",
        "stars_amount": body.stars_amount,
        "lang": body.lang,
        "route_request": body.route_request.model_dump(),
    }

    logger.info(
        "pay_create_invoice: order_id=%s stars_amount=%s lang=%s route_request=%s",
        order_id,
        body.stars_amount,
        body.lang,
        body.route_request,
    )

    invoice_link = create_stars_invoice_link(
        title=title,
        description=description,
        stars_amount=body.stars_amount,
        payload=telegram_payload,  # IMPORTANT: short string payload
    )
    return CreateInvoiceResponse(invoice_link=invoice_link, order_id=order_id)


@app.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    update = await req.json()

    # 1) Pre-checkout query must be answered, иначе оплата не пройдет
    if "pre_checkout_query" in update:
        pcq = update["pre_checkout_query"]

        token = os.getenv("BOT_TOKEN", "")
        if not token:
            raise HTTPException(500, "BOT_TOKEN missing")

        url = f"https://api.telegram.org/bot{token}/answerPreCheckoutQuery"
        r = requests.post(
            url,
            json={"pre_checkout_query_id": pcq["id"], "ok": True},
            timeout=20,
        )
        r.raise_for_status()
        return {"ok": True}

    # 2) Successful payment arrives in message.successful_payment
    msg = update.get("message") or update.get("edited_message")
    if msg and msg.get("successful_payment"):
        sp = msg["successful_payment"]
        payment_id = sp.get("telegram_payment_charge_id")
        invoice_payload = sp.get("invoice_payload")  # string payload we set in createInvoiceLink

        decoded: Dict[str, Any] = {}
        if invoice_payload:
            # Our payload is like "order:<id>"
            if isinstance(invoice_payload, str) and invoice_payload.startswith("order:"):
                order_id = invoice_payload.split("order:", 1)[1]
                decoded = {"order_id": order_id, "order": ORDERS.get(order_id)}
            else:
                # fallback: try json (if you ever send json payloads)
                try:
                    decoded = json.loads(invoice_payload)
                except Exception:
                    decoded = {"raw_payload": invoice_payload}

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


@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(status_code=200)
