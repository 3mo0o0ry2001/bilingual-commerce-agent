"""
schemas.py

Request/response contracts for the API layer.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Customer's message, Arabic or English")
    customer_phone: str | None = Field(None, description="WhatsApp-style phone identifier")


class ChatResponse(BaseModel):
    answer_text: str
    intent: str | None = None
    status: str | None = None
    transaction_ids: list[str] = []


class HealthResponse(BaseModel):
    status: str
    database: str