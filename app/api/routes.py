"""
routes.py

API endpoints wiring HTTP requests to the LangGraph agent.
"""

import logging

from app.core.limiter import limiter
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from app.agents.graph import build_graph
from app.api.schemas import ChatRequest, ChatResponse, HealthResponse
from app.db.database import engine

log = logging.getLogger("api.routes")
router = APIRouter()

# Build once at import time; the compiled graph is stateless and reusable.
_graph = build_graph()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, body: ChatRequest) -> ChatResponse:
    try:
        result = _graph.invoke({
            "user_request": body.message,
            "customer_phone": body.customer_phone,
            "filters": {},
            "requested_items": [],
            "matched_products": [],
            "order_items": [],
        })
    except Exception as e:
        log.error(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail="Internal agent error")

    return ChatResponse(
        answer_text=result.get("answer_text", "عذراً، حصل خطأ. حاول تاني."),
        intent=result.get("intent"),
        status=result.get("status"),
        transaction_ids=result.get("transaction_ids", []),
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        log.error(f"Health check DB failure: {e}")
        db_status = "unavailable"

    return HealthResponse(status="ok", database=db_status)
