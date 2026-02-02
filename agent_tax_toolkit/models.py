"""Data models for tax compliance."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Contractor(Base):
    """A contractor/customer requiring 1099 filing."""

    __tablename__ = "contractors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    tin_encrypted = Column(LargeBinary, nullable=True)  # Encrypted Tax ID Number
    w9_received = Column(Boolean, default=False)
    w9_received_date = Column(Date, nullable=True)
    w9_pdf_path = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = relationship("Payment", back_populates="contractor")
    forms_1099 = relationship("Form1099", back_populates="contractor")


class Payment(Base):
    """A payment made to a contractor."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    contractor_id = Column(String(36), ForeignKey("contractors.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    stripe_payment_id = Column(String(255), nullable=True, unique=True)
    category = Column(
        String(50), default="contractor_payment"
    )  # contractor_payment, service_fee, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    contractor = relationship("Contractor", back_populates="payments")


class Form1099(Base):
    """A 1099-NEC form for a contractor."""

    __tablename__ = "forms_1099"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    year = Column(String(4), nullable=False)
    contractor_id = Column(String(36), ForeignKey("contractors.id"), nullable=False)
    total_paid = Column(Numeric(10, 2), nullable=False)  # Box 1: Nonemployee compensation
    pdf_path = Column(String(500), nullable=True)
    efiled = Column(Boolean, default=False)
    efile_confirmation = Column(String(255), nullable=True)
    sent_to_contractor = Column(Boolean, default=False)
    sent_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contractor = relationship("Contractor", back_populates="forms_1099")
