# api/app/main.py
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.ai import generate_route_with_gpt
from app.payments import create_stars_invoice_link
from app.schemas import RouteRequest, RouteResponse

# 1) .env полезен локально. На Render переменные задаются в Environment.
load_dotenv()

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="My Route API", version="0.2.0")


def _get_cors_origins() -> List[str]:
    """
    Для Telegram WebApp чаще всего origin будет 'https://web.telegram.org'
    и/или домен, на котором хостится твой фронт (например GitHub Pages/Render Static).
    Поэтому CORS_ORIGINS лучше задавать через переменную окружения на Render.
    """
    env_val = (os.getenv("CORS_ORIGINS") or "").strip()
    if env_val:
        return [x.strip() for x in env_val.split(",") if x.strip()]

    # дефолты для локальной разработки
    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        # можно временно добавить Telegram origin, чтобы не ловить CORS (лучше через env)
        "https://web.telegram.org",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def _startup_logs() -> None:
    logger.info("ENV CORS_ORIGINS=%s", os.getenv("CORS_ORIGINS"))
    logger.info("ENV OPENAI_API_KEY set=%s", bool((os.getenv("OPENAI_API_KEY") or "").strip()))
    logger.info("ENV OPENAI_MODEL=%s", os.getenv("OPENAI_MODEL"))


def _require_env(name: str) -> str:
    val = (os.getenv(name) or "").strip()
    if not val:
        raise HTTPException(500, f"{name} is not set")
    return val


def _generate_route(req: RouteRequest) -> RouteResponse:
    # 2) Явно проверяем ключ (чтобы 500 было понятным)
    _require_env("OPENAI_API_KEY")

    route = generate_route_with_gpt(req)

    # 3) Гарантия, что map_points всегда есть (даже если геокодинг ничего не нашёл)
    # Это важно для фронта: он ожидает data.map_points.
    if getattr(route, "map_points", None) is None:
        route.map_points = []

    return route


@app.post("/route/generate", response_model=RouteResponse)
def generate_route(req: RouteRequest):
    return _generate_route(req)


# ----- Payments (как у тебя, но без лишних вещей) -----

# In-memory storages (потеряются при рестарте/деплое)
PAID: Dict[str, Dict[str, Any]] = {}
ORDERS: Dict[str, Dict[str, Any]] = {}
PAID_ORDERS: Dict[str, Dict[str, Any]] = {}
USED_ORDERS: Dict[str, bool] = {}


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

    order_id = uuid.uuid4().hex
    telegram_payload = f"order:{order_id}"

    ORDERS[order_id] = {
        "type": "route_generation",
        "stars_amount": body.stars_amount,
        "lang": body.lang,
        "route_request": body.route_request.model_dump(),
    }
    USED_ORDERS.pop(order_id, None)

    invoice_link = create_stars_invoice_link(
        title=title,
        description=description,
        stars_amount=body.stars_amount,
        payload=telegram_payload,
    )
    return CreateInvoiceResponse(invoice_link=invoice_link, order_id=order_id)


@app.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    update = await req.json()

    # pre_checkout_query
    if "pre_checkout_query" in update:
        pcq = update["pre_checkout_query"]
        token = _require_env("BOT_TOKEN")

        url = f"https://api.telegram.org/bot{token}/answerPreCheckoutQuery"
        r = requests.post(url, json={"pre_checkout_query_id": pcq["id"], "ok": True}, timeout=20)
        r.raise_for_status()
        return {"ok": True}

    # successful_payment
    msg = update.get("message") or update.get("edited_message")
    if msg and msg.get("successful_payment"):
        sp = msg["successful_payment"]
        payment_id = sp.get("telegram_payment_charge_id")
        invoice_payload = sp.get("invoice_payload")

        order_id: Optional[str] = None
        if isinstance(invoice_payload, str) and invoice_payload.startswith("order:"):
            order_id = invoice_payload.split("order:", 1)[1]

        decoded: Dict[str, Any] = {}
        if order_id:
            decoded = {"order_id": order_id, "order": ORDERS.get(order_id)}
        elif invoice_payload:
            try:
                decoded = json.loads(invoice_payload)
            except Exception:
                decoded = {"raw_payload": invoice_payload}

        if payment_id:
            PAID[payment_id] = decoded
        if order_id:
            PAID_ORDERS[order_id] = {"payment_id": payment_id, "order": ORDERS.get(order_id)}

        return {"ok": True}

    return {"ok": True}


class PayStatusResponse(BaseModel):
    paid: bool
    data: Optional[Dict[str, Any]] = None


@app.get("/pay/status/{payment_id}", response_model=PayStatusResponse)
def pay_status(payment_id: str):
    data = PAID.get(payment_id)
    return PayStatusResponse(paid=bool(data), data=data)


class PayOrderStatusResponse(BaseModel):
    order_id: str
    paid: bool
    payment_id: Optional[str] = None
    order: Optional[Dict[str, Any]] = None
    used: Optional[bool] = None


@app.get("/pay/status-by-order/{order_id}", response_model=PayOrderStatusResponse)
def pay_status_by_order(order_id: str):
    rec = PAID_ORDERS.get(order_id)
    used = bool(USED_ORDERS.get(order_id))

    if not rec:
        return PayOrderStatusResponse(
            order_id=order_id,
            paid=False,
            payment_id=None,
            order=ORDERS.get(order_id),
            used=used,
        )

    return PayOrderStatusResponse(
        order_id=order_id,
        paid=True,
        payment_id=rec.get("payment_id"),
        order=rec.get("order"),
        used=used,
    )


class GenerateByOrderResponse(BaseModel):
    order_id: str
    payment_id: str
    route: RouteResponse


@app.post("/route/generate-by-order/{order_id}", response_model=GenerateByOrderResponse)
def generate_route_by_order(order_id: str):
    paid_rec = PAID_ORDERS.get(order_id)
    if not paid_rec:
        raise HTTPException(402, "not paid")
    if USED_ORDERS.get(order_id):
        raise HTTPException(409, "order already used")

    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(404, "order not found (server restarted or order expired)")

    rr = order.get("route_request")
    if not isinstance(rr, dict):
        raise HTTPException(500, "order.route_request missing")

    req_model = RouteRequest.model_validate(rr)
    route = _generate_route(req_model)

    USED_ORDERS[order_id] = True

    return GenerateByOrderResponse(
        order_id=order_id,
        payment_id=paid_rec.get("payment_id") or "",
        route=route,
    )


@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(status_code=200)
