"""
Rates API (V2 - Google Sheets powered)
- GET  /api/rates          — public, returns all active rates from Google Sheets
- POST /api/rates/refresh  — admin, forces cache refresh
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.services.google_sheets_service import get_sheets_service, init_sheets_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/rates", tags=["rates"])


class RateResponse(BaseModel):
    """Response model for rates"""
    product_name: str
    min_rate: float
    comp_rate: float
    min_loan: float
    max_loan: float
    lender: str

    class Config:
        from_attributes = True


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


@router.get("", response_model=List[RateResponse])
def get_rates():
    """
    Public endpoint — returns all active rates from Google Sheets.
    Cached for 1 hour to avoid API rate limits.
    """
    service = _ensure_sheets_service()

    if service is None:
        # Fallback: return empty or error response
        raise HTTPException(
            status_code=503,
            detail="Google Sheets service not configured"
        )

    try:
        rates = service.get_rates()
        return rates
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching rates: {str(e)}"
        )


@router.post("/refresh", response_model=MessageResponse)
def refresh_rates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin/Broker: Force cache refresh from Google Sheets.
    Useful if you just updated rates in the sheet.
    """
    # Verify user is admin or broker
    if not current_user or not hasattr(current_user, 'is_admin'):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    service = _ensure_sheets_service()

    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Google Sheets service not configured"
        )

    try:
        service.invalidate_cache()
        rates = service.get_rates()
        return MessageResponse(
            message=f"Cache refreshed. {len(rates)} active rates loaded."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing rates: {str(e)}"
        )


# Removed PUT /api/rates/bulk and PATCH /api/rates/{id}
# Instead, edit rates directly in your Google Sheet!
