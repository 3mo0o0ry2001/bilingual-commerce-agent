"""
SQLAlchemy ORM models for the bilingual commerce agent.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    item_id = Column(String, primary_key=True)
    brand = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    name_ar = Column(String)
    gender = Column(String)

    main_accords = Column(JSON)
    notes = Column(JSON)

    description_en = Column(Text)
    description_ar = Column(Text)

    category = Column(String)
    price_aed = Column(Float, nullable=False)
    quantity_in_stock = Column(Integer, nullable=False, default=0)

    rating = Column(Float)
    reviews_count = Column(Integer, default=0)
    source_url = Column(String)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    transactions = relationship("Transaction", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, unique=True, nullable=False)
    name = Column(String)
    preferred_language = Column(String, default="ar")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    transactions = relationship("Transaction", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True)
    item_id = Column(String, ForeignKey("products.item_id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    unit_price_aed = Column(Float, nullable=False)
    line_total_aed = Column(Float, nullable=False)
    balance_after_aed = Column(Float, nullable=False)

    status = Column(String, nullable=False)  # success, return, insufficient_stock, etc.
    timestamp = Column(DateTime(timezone=True), default=utcnow)

    customer = relationship("Customer", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True)

    channel = Column(String, default="whatsapp")
    role = Column(String, nullable=False)  # "user" or "assistant"
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    customer = relationship("Customer", back_populates="conversations")