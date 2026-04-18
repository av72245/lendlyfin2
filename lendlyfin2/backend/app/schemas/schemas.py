"""
Pydantic v2 schemas — request bodies and API responses.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole, LeadStatus, LeadSource, EnquiryType, LoanType


# ── AUTH ───────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── USER ───────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: UserRole = UserRole.broker


# ── LEAD — CREATE (from public contact form) ───────────────────

class LeadCreate(BaseModel):
    # Contact
    first_name: str     = Field(min_length=1, max_length=100)
    last_name:  str     = Field(min_length=1, max_length=100)
    email:      EmailStr
    phone:      Optional[str] = None

    # Enquiry
    enquiry_type:   EnquiryType
    budget:         Optional[str] = None
    interests:      Optional[List[str]] = []
    preferred_time: Optional[str] = None
    message:        str = Field(min_length=5, max_length=2000)

    # Financial snapshot (optional — filled if user used the calculator)
    annual_income:     Optional[float] = None
    overtime:          Optional[float] = None
    bonus:             Optional[float] = None
    partner_income:    Optional[float] = None
    deposit:           Optional[float] = None
    relationship:      Optional[str]   = None  # 'single' or 'couple'
    monthly_expenses:  Optional[float] = None
    existing_debts:    Optional[float] = None
    credit_card_limit: Optional[float] = None
    dependants:        Optional[int]   = None
    employment_type:   Optional[str]   = None
    loan_purpose:      Optional[str]   = None
    estimated_bp:      Optional[float] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v:
            cleaned = v.replace(" ", "").replace("-", "")
            if not cleaned.startswith(("04", "+614", "61")):
                # Allow empty — phone is optional
                pass
        return v


class LeadOut(BaseModel):
    id:            int
    first_name:    str
    last_name:     str
    email:         str
    phone:         Optional[str]
    enquiry_type:  EnquiryType
    budget:        Optional[str]
    interests:     Optional[str]  # stored as JSON string
    preferred_time:Optional[str]
    message:       str
    annual_income: Optional[float]
    deposit:       Optional[float]
    estimated_bp:  Optional[float]
    status:        LeadStatus
    source:        LeadSource
    priority:      int
    created_at:    datetime
    updated_at:    datetime
    contacted_at:  Optional[datetime]
    converted_at:  Optional[datetime]
    assigned_to:   Optional[UserOut]
    notes:         List["NoteOut"] = []

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    status:         Optional[LeadStatus] = None
    priority:       Optional[int]        = None
    assigned_to_id: Optional[int]        = None
    contacted_at:   Optional[datetime]   = None
    converted_at:   Optional[datetime]   = None


class LeadListItem(BaseModel):
    id:           int
    first_name:   str
    last_name:    str
    email:        str
    phone:        Optional[str]
    enquiry_type: EnquiryType
    budget:       Optional[str]
    estimated_bp: Optional[float]
    status:       LeadStatus
    priority:     int
    created_at:   datetime
    assigned_to:  Optional[UserOut]

    model_config = {"from_attributes": True}


# ── NOTES ─────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class NoteOut(BaseModel):
    id:         int
    content:    str
    created_at: datetime
    author:     UserOut

    model_config = {"from_attributes": True}


# ── RATES ─────────────────────────────────────────────────────

class RateOut(BaseModel):
    id:         int
    bank_id:    str
    name:       str
    abbr:       str
    color:      str
    text_color: str
    bank_type:  str
    loan_type:  LoanType
    min_rate:   float
    max_rate:   float
    comp_rate:  float
    has_offset: bool
    has_redraw: bool
    annual_fees:float
    is_active:  bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class RateUpdate(BaseModel):
    min_rate:    Optional[float] = None
    max_rate:    Optional[float] = None
    comp_rate:   Optional[float] = None
    annual_fees: Optional[float] = None
    is_active:   Optional[bool]  = None


class BulkRateUpdate(BaseModel):
    rates: List[dict]  # [{bank_id, min_rate, max_rate, comp_rate, annual_fees}]


# ── CALCULATOR ────────────────────────────────────────────────

class BorrowingInput(BaseModel):
    annual_income:     float = Field(gt=0)
    overtime:          float = 0        # annual avg — shaded at 80%
    bonus:             float = 0        # annual avg — shaded at 80%
    partner_income:    float = 0
    monthly_expenses:  float = Field(ge=0)
    dependants:        int   = Field(ge=0, le=10)
    relationship:      str   = "single"  # 'single' or 'couple' — for HEM
    existing_debts:    float = 0
    credit_card_limit: float = 0        # 3% of limit counted as monthly liability
    deposit:           float = Field(ge=0)
    employment_type:   float = 1.0      # income shade multiplier
    loan_purpose:      float = 1.0      # purpose multiplier


class BorrowingResult(BaseModel):
    borrowing_power:   float
    max_property:      float
    lvr:               float
    monthly_repayment: float
    net_annual:        float
    net_monthly:       float
    gross_assessable:  float
    monthly_surplus:   float
    max_repayment:     float
    hem_applied:       bool  = False
    hem_value:         float = 0
    dti_applied:       bool  = False
    dti_cap:           float = 0
    best_rate:         float = 6.14


# ── DASHBOARD STATS ───────────────────────────────────────────

class DashboardStats(BaseModel):
    total_leads:      int
    new_leads:        int
    contacted_leads:  int
    converted_leads:  int
    conversion_rate:  float
    leads_today:      int
    leads_this_week:  int
    leads_this_month: int


# ── GENERIC ───────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# Resolve forward references (Pydantic v2 requirement)
TokenResponse.model_rebuild()
LeadOut.model_rebuild()
