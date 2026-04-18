"""
All SQLAlchemy ORM models for Lendlyfin.
Tables: users, leads, lead_notes, rates, calculator_sessions
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship as orm_relationship
from app.core.database import Base
import enum


# ── ENUMS ──────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin  = "admin"
    broker = "broker"


class LeadStatus(str, enum.Enum):
    new        = "new"
    contacted  = "contacted"
    qualified  = "qualified"
    converting = "converting"
    won        = "won"
    lost       = "lost"
    archived   = "archived"


class LeadSource(str, enum.Enum):
    contact_form   = "contact_form"
    borrowing_tool = "borrowing_tool"
    eligibility    = "eligibility"
    organic        = "organic"


class EnquiryType(str, enum.Enum):
    first_home  = "first-home"
    upgrade     = "upgrade"
    invest      = "invest"
    refinance   = "refinance"
    construction= "construction"
    general     = "general"
    other       = "other"


class LoanType(str, enum.Enum):
    variable = "variable"
    fixed    = "fixed"


# ── USER ───────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String(255), unique=True, index=True, nullable=False)
    full_name  = Column(String(255), nullable=False)
    hashed_pw  = Column(String(255), nullable=False)
    role       = Column(Enum(UserRole), default=UserRole.broker, nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notes      = orm_relationship("LeadNote", back_populates="author")
    leads      = orm_relationship("Lead", back_populates="assigned_to")


# ── LEAD ───────────────────────────────────────────────────────

class Lead(Base):
    __tablename__ = "leads"

    id             = Column(Integer, primary_key=True, index=True)

    # Contact info
    first_name     = Column(String(100), nullable=False)
    last_name      = Column(String(100), nullable=False)
    email          = Column(String(255), nullable=False, index=True)
    phone          = Column(String(30), nullable=True)

    # Enquiry details
    enquiry_type   = Column(Enum(EnquiryType), nullable=False)
    budget         = Column(String(50), nullable=True)
    interests      = Column(Text, nullable=True)        # JSON array stored as text
    preferred_time = Column(String(50), nullable=True)
    message        = Column(Text, nullable=False)

    # Financial snapshot (from borrowing tool if used)
    annual_income     = Column(Float,   nullable=True)
    overtime          = Column(Float,   nullable=True)
    bonus             = Column(Float,   nullable=True)
    partner_income    = Column(Float,   nullable=True)
    deposit           = Column(Float,   nullable=True)
    relationship      = Column(String(20), nullable=True)  # 'single' or 'couple'
    monthly_expenses  = Column(Float,   nullable=True)
    existing_debts    = Column(Float,   nullable=True)
    credit_card_limit = Column(Float,   nullable=True)
    dependants        = Column(Integer, nullable=True)
    employment_type   = Column(String(50), nullable=True)
    loan_purpose      = Column(String(50), nullable=True)
    estimated_bp      = Column(Float,   nullable=True)  # Calculated borrowing power

    # CRM fields
    status         = Column(Enum(LeadStatus), default=LeadStatus.new, nullable=False)
    source         = Column(Enum(LeadSource), default=LeadSource.contact_form)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    priority       = Column(Integer, default=0)  # 0=normal, 1=high, 2=urgent

    # Metadata
    ip_address     = Column(String(50), nullable=True)
    user_agent     = Column(String(500), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contacted_at   = Column(DateTime, nullable=True)
    converted_at   = Column(DateTime, nullable=True)

    # Relationships
    notes          = orm_relationship("LeadNote", back_populates="lead", cascade="all, delete-orphan")
    assigned_to    = orm_relationship("User", back_populates="leads")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ── LEAD NOTE ─────────────────────────────────────────────────

class LeadNote(Base):
    __tablename__ = "lead_notes"

    id         = Column(Integer, primary_key=True, index=True)
    lead_id    = Column(Integer, ForeignKey("leads.id"), nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead   = orm_relationship("Lead", back_populates="notes")
    author = orm_relationship("User", back_populates="notes")


# ── RATE ──────────────────────────────────────────────────────

class Rate(Base):
    __tablename__ = "rates"

    id          = Column(Integer, primary_key=True, index=True)
    bank_id     = Column(String(20), unique=True, nullable=False)   # e.g. "anz"
    name        = Column(String(100), nullable=False)
    abbr        = Column(String(10), nullable=False)
    color       = Column(String(10), nullable=False)
    text_color  = Column(String(10), nullable=False, default="#fff")
    bank_type   = Column(String(50), nullable=False)                # "Major Bank" etc.
    loan_type   = Column(Enum(LoanType), default=LoanType.variable)
    min_rate    = Column(Float, nullable=False)
    max_rate    = Column(Float, nullable=False)
    comp_rate   = Column(Float, nullable=False)
    has_offset  = Column(Boolean, default=False)
    has_redraw  = Column(Boolean, default=True)
    annual_fees = Column(Float, default=0)
    is_active   = Column(Boolean, default=True)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by  = Column(Integer, ForeignKey("users.id"), nullable=True)


# ── CALCULATOR SESSION ────────────────────────────────────────

class CalculatorSession(Base):
    """Tracks anonymous calculator usage for analytics."""
    __tablename__ = "calculator_sessions"

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(String(64), index=True)
    calculator_type = Column(String(30))   # "borrowing", "repayment", "eligibility"
    inputs          = Column(Text)          # JSON snapshot of inputs
    result          = Column(Text)          # JSON snapshot of result
    converted_lead  = Column(Boolean, default=False)
    ip_address      = Column(String(50), nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
