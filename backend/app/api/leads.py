"""
Leads API (V2 - Google Forms powered)
- POST /api/leads/google-form  — webhook for Google Forms submissions
- POST /api/leads          — public, creates a lead + sends emails
- GET  /api/leads          — broker/admin, list all leads
- GET  /api/leads/{id}     — broker/admin, single lead with notes
- PATCH /api/leads/{id}    — broker/admin, update status/assignment
- POST /api/leads/{id}/notes — broker/admin, add a note
- GET  /api/leads/stats    — broker/admin, dashboard stats
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, get_admin_user
from app.core.config import get_settings
from app.models.user import User, Lead, LeadNote, LeadStatus, CalculatorSession
from app.schemas.schemas import (
    LeadCreate, LeadOut, LeadListItem, LeadUpdate,
    NoteCreate, NoteOut, DashboardStats, MessageResponse
)
from app.services.email_service import (
    send_new_lead_notification,
    send_lead_confirmation,
    send_status_update_email,
)
from app.services.google_forms_service import GoogleFormsService

router = APIRouter(prefix="/api/leads", tags=["leads"])


# ── GOOGLE FORMS WEBHOOK ──────────────────────────────────────

@router.post("/google-form", response_model=dict, status_code=201)
async def receive_google_form_submission(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for Google Forms submissions.
    Google Form → (auto Google Sheet) → We poll/parse it
    OR Google Form → (via Zapier/Make) → POST to this endpoint

    This endpoint:
    1. Receives form data from Google Forms webhook
    2. Parses it into a Lead
    3. Stores in database
    4. Sends notification email
    """
    settings = get_settings()
    form_service = GoogleFormsService(settings.GOOGLE_FORMS_WEBHOOK_SECRET)

    try:
        # Parse request body
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        # Parse form data into standardized lead format
        lead_data = form_service.parse_google_form_submission(body)

        # Create Lead record
        loan_purpose = lead_data.get('loan_purpose', 'General Enquiry')
        lead = Lead(
            first_name=lead_data.get('first_name', ''),
            last_name=lead_data.get('last_name', ''),
            email=lead_data.get('email', ''),
            phone=lead_data.get('phone', ''),
            enquiry_type=loan_purpose,  # satisfy NOT NULL constraint
            loan_purpose=loan_purpose,
            budget=float(lead_data.get('loan_amount', 0) or 0),
            message=lead_data.get('additional_notes', ''),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500],
            # Store additional form data as JSON
            interests=json.dumps({
                'property_type': lead_data.get('property_type'),
                'credit_score': lead_data.get('credit_score'),
                'employment_status': lead_data.get('employment_status'),
            })
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        # Send notification email
        try:
            send_new_lead_notification(lead)
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            # Don't block response on email failure

        return {
            "success": True,
            "message": f"Lead received from {lead.first_name}",
            "lead_id": lead.id,
            "reference": f"#{lead.id:04d}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing form: {str(e)}")


# ── PUBLIC: SUBMIT LEAD ───────────────────────────────────────

@router.post("", response_model=dict, status_code=201)
async def create_lead(
    body: LeadCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Public endpoint — called when a visitor submits the contact form.
    1. Saves lead to DB
    2. Sends confirmation email to the visitor
    3. Sends notification email to broker
    """
    # Convert interests list to JSON string for storage
    interests_json = json.dumps(body.interests) if body.interests else "[]"

    lead = Lead(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone=body.phone,
        enquiry_type=body.enquiry_type,
        budget=body.budget,
        interests=interests_json,
        preferred_time=body.preferred_time,
        message=body.message,
        annual_income=body.annual_income,
        overtime=body.overtime,
        bonus=body.bonus,
        partner_income=body.partner_income,
        deposit=body.deposit,
        relationship=body.relationship,
        monthly_expenses=body.monthly_expenses,
        existing_debts=body.existing_debts,
        credit_card_limit=body.credit_card_limit,
        dependants=body.dependants,
        employment_type=body.employment_type,
        loan_purpose=body.loan_purpose,
        estimated_bp=body.estimated_bp,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Fire emails (non-blocking — failures don't break the response)
    try:
        send_lead_confirmation(lead)
        send_new_lead_notification(lead)
    except Exception:
        pass  # Email failure should never block lead creation

    return {
        "success": True,
        "message": f"Thanks {lead.first_name}, we'll be in touch within one business day.",
        "lead_id": lead.id,
        "reference": f"#{lead.id:04d}",
    }


# ── PROTECTED: LIST LEADS ─────────────────────────────────────

@router.get("", response_model=List[LeadListItem])
def list_leads(
    status:   Optional[str] = Query(None),
    priority: Optional[int] = Query(None),
    search:   Optional[str] = Query(None),
    limit:    int = Query(50, le=200),
    offset:   int = Query(0),
    db:       Session = Depends(get_db),
    _:        User = Depends(get_current_user),
):
    """Broker/admin: list leads with optional filtering."""
    q = db.query(Lead)

    if status:
        try:
            q = q.filter(Lead.status == LeadStatus(status))
        except ValueError:
            pass

    if priority is not None:
        q = q.filter(Lead.priority == priority)

    if search:
        term = f"%{search}%"
        q = q.filter(
            Lead.first_name.ilike(term) |
            Lead.last_name.ilike(term)  |
            Lead.email.ilike(term)      |
            Lead.phone.ilike(term)
        )

    return q.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()


# ── PROTECTED: DASHBOARD STATS ────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Dashboard statistics for the broker CRM."""
    now   = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week  = today - timedelta(days=7)
    month = today - timedelta(days=30)

    total     = db.query(func.count(Lead.id)).scalar()
    new       = db.query(func.count(Lead.id)).filter(Lead.status == LeadStatus.new).scalar()
    contacted = db.query(func.count(Lead.id)).filter(Lead.status == LeadStatus.contacted).scalar()
    converted = db.query(func.count(Lead.id)).filter(Lead.status == LeadStatus.won).scalar()
    t_day     = db.query(func.count(Lead.id)).filter(Lead.created_at >= today).scalar()
    t_week    = db.query(func.count(Lead.id)).filter(Lead.created_at >= week).scalar()
    t_month   = db.query(func.count(Lead.id)).filter(Lead.created_at >= month).scalar()

    rate = round((converted / total * 100), 1) if total > 0 else 0.0

    return DashboardStats(
        total_leads=total,
        new_leads=new,
        contacted_leads=contacted,
        converted_leads=converted,
        conversion_rate=rate,
        leads_today=t_day,
        leads_this_week=t_week,
        leads_this_month=t_month,
    )


# ── PROTECTED: SINGLE LEAD ────────────────────────────────────

@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
    lead_id: int,
    db:      Session = Depends(get_db),
    _:       User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# ── PROTECTED: UPDATE LEAD ────────────────────────────────────

@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    body:    LeadUpdate,
    db:      Session = Depends(get_db),
    _:       User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    old_status = lead.status

    if body.status is not None:
        lead.status = body.status
        # Auto-set timestamps
        if body.status == LeadStatus.contacted and not lead.contacted_at:
            lead.contacted_at = datetime.utcnow()
        if body.status == LeadStatus.won and not lead.converted_at:
            lead.converted_at = datetime.utcnow()

    if body.priority is not None:
        lead.priority = body.priority
    if body.assigned_to_id is not None:
        lead.assigned_to_id = body.assigned_to_id

    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)

    # Send email if status changed to a notifiable state
    if body.status and body.status != old_status:
        try:
            send_status_update_email(lead, body.status.value)
        except Exception:
            pass

    return lead


# ── PROTECTED: ADD NOTE ───────────────────────────────────────

@router.post("/{lead_id}/notes", response_model=NoteOut, status_code=201)
def add_note(
    lead_id:      int,
    body:         NoteCreate,
    db:           Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    note = LeadNote(
        lead_id=lead_id,
        author_id=current_user.id,
        content=body.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ── PROTECTED: DELETE LEAD ────────────────────────────────────

@router.delete("/{lead_id}", response_model=MessageResponse)
def delete_lead(
    lead_id: int,
    db:      Session = Depends(get_db),
    _:       User = Depends(get_admin_user),
):
    """Admin only: permanently delete a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return MessageResponse(message=f"Lead #{lead_id} deleted")
