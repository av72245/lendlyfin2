"""
Rates API (V2 - Google Sheets powered)
- GET  /api/rates          — public, returns all active rates
- POST /api/rates/refresh  — admin, forces cache refresh
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User, Rate
from app.services.google_sheets_service import get_sheets_service, init_sheets_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/rates", tags=["rates"])


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


def _ensure_sheets_service():
    """Ensure Google Sheets service is initialized"""
    service = get_sheets_service()
    if service is None:
        settings = get_settings()
        if not settings.GOOGLE_SHEETS_CREDENTIALS_JSON or not settings.GOOGLE_SHEETS_RATES_ID:
            return None
        init_sheets_service(
            settings.GOOGLE_SHEETS_CREDENTIALS_JSON,
            settings.GOOGLE_SHEETS_RATES_ID
        )
        service = get_sheets_service()
    return service


@router.get("")
def get_rates(db: Session = Depends(get_db)):
    """
    Public endpoint — returns all active rates.
    Tries Google Sheets first (live data), falls back to database (seeded data).
    Cached for 1 hour to avoid API rate limits.
    """
    service = _ensure_sheets_service()

    if service is not None:
        try:
            rates = service.get_rates()
            return rates
        except Exception:
            pass  # Fall through to database

    # Database fallback — map to same shape as Google Sheets response
    db_rates = db.query(Rate).filter(Rate.is_active == True).all()
    if not db_rates:
        raise HTTPException(status_code=503, detail="No rates available")

    return [
        {
            "id": r.id,
            "bank_id": r.bank_id,
            "name": r.name,
            "abbr": r.abbr,
            "color": r.color,
            "text_color": r.text_color,
            "bank_type": r.bank_type,
            "loan_type": r.loan_type.value if hasattr(r.loan_type, "value") else str(r.loan_type),
            "min_rate": r.min_rate,
            "max_rate": r.max_rate,
            "comp_rate": r.comp_rate,
            "has_offset": r.has_offset,
            "has_redraw": r.has_redraw,
            "annual_fees": r.annual_fees,
            "is_active": r.is_active,
        }
        for r in db_rates
    ]


@router.post("/refresh", response_model=MessageResponse)
def refresh_rates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin/Broker: Force cache refresh from Google Sheets.
    """
    if not current_user or not hasattr(current_user, 'is_admin'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = _ensure_sheets_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Google Sheets service not configured")

    try:
        service.invalidate_cache()
        rates = service.get_rates()
        return MessageResponse(message=f"Cache refreshed. {len(rates)} active rates loaded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing rates: {str(e)}")
