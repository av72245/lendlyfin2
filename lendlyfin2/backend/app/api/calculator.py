"""
Calculator API — server-side borrowing power calculation.
Mirrors the frontend calcLocal() logic exactly so results are consistent.
Uses industry-standard methodology: HEM floor, income shading, APRA stress test, DTI cap.
"""
from fastapi import APIRouter
from app.schemas.schemas import BorrowingInput, BorrowingResult

router = APIRouter(prefix="/api/calc", tags=["calculator"])

BASE_RATE = 6.14   # indicative market rate (p.a.)
STRESS    = (BASE_RATE + 3) / 100 / 12   # APRA buffer: +3%
MONTHS    = 360    # 30-year term


def get_hem(relationship: str, dependants: int) -> float:
    """
    Return the HEM (Household Expenditure Measure) monthly benchmark.
    Based on Melbourne Institute figures used by major Australian lenders.
    Banks use the HIGHER of declared expenses vs HEM — never lower.
    """
    base      = 2900.0 if relationship == "couple" else 2000.0
    dep_extra = [0, 600, 1200, 1700, 2200, 2600][min(dependants, 5)]
    return base + dep_extra


def annuity_pv(monthly_payment: float, rate: float, months: int) -> float:
    """Present value of annuity — what loan amount does this repayment support?"""
    if monthly_payment <= 0 or rate <= 0:
        return 0.0
    return monthly_payment * (pow(1 + rate, months) - 1) / (rate * pow(1 + rate, months))


@router.post("/borrowing-power", response_model=BorrowingResult)
def calculate_borrowing_power(body: BorrowingInput):
    """
    Calculate borrowing power using APRA stress-test rules with:
    - Income shading by type (overtime/bonus at 80%)
    - HEM floor (max of declared vs benchmark)
    - Credit card liability (3% of limit/month)
    - DTI cap (6× gross annual income)
    """

    # ── Step 1: Income shading ────────────────────────────────────
    # Base salary uses employment type multiplier (self-employed / casual haircut)
    # Overtime and bonus: 80% per lender standard (variable income)
    # Partner income: 100% (assumed PAYG)
    base_shaded      = body.annual_income * body.employment_type
    overtime_shaded  = body.overtime * 0.80
    bonus_shaded     = body.bonus    * 0.80
    total_assessable = (base_shaded + overtime_shaded + bonus_shaded + body.partner_income) * body.loan_purpose

    # ── Step 2: Tax (2025-26 brackets + LITO) ─────────────────────
    gross = total_assessable
    tax   = 0.0
    if   gross > 180000: tax = 51667 + (gross - 180000) * 0.45
    elif gross > 120000: tax = 29467 + (gross - 120000) * 0.37
    elif gross >  45000: tax = 5092  + (gross -  45000) * 0.325
    elif gross >  18200: tax =          (gross -  18200) * 0.19
    if gross < 66667:
        tax = max(0.0, tax - 700)   # Low Income Tax Offset

    net_annual  = gross - tax
    net_monthly = net_annual / 12

    # ── Step 3: HEM floor ─────────────────────────────────────────
    hem               = get_hem(body.relationship, body.dependants)
    effective_expenses = max(body.monthly_expenses, hem)
    hem_applied       = effective_expenses > body.monthly_expenses

    # ── Step 4: Credit card liability ────────────────────────────
    # Banks count 3% of the credit card LIMIT as monthly debt, regardless of balance
    cc_liability = body.credit_card_limit * 0.03

    # ── Step 5: Surplus and max repayment ────────────────────────
    total_deductions = effective_expenses + body.existing_debts + cc_liability
    surplus   = net_monthly - total_deductions
    max_repay = surplus * 0.85   # banks keep a 15% buffer

    # ── Step 6: Borrowing capacity (APRA stress rate) ────────────
    borrowing = annuity_pv(max_repay, STRESS, MONTHS) if surplus > 0 else 0.0

    # ── Step 7: DTI cap (6× total gross income) ──────────────────
    gross_annual = body.annual_income + body.overtime + body.bonus + body.partner_income
    dti_cap      = gross_annual * 6
    dti_applied  = borrowing > dti_cap and dti_cap > 0
    if dti_applied:
        borrowing = dti_cap

    max_prop = borrowing + body.deposit
    lvr      = (borrowing / max_prop * 100) if max_prop > 0 else 0.0

    # Monthly repayment at actual market rate (for display)
    r = BASE_RATE / 100 / 12
    monthly_repay = (
        borrowing * r * pow(1 + r, MONTHS) / (pow(1 + r, MONTHS) - 1)
        if borrowing > 0 else 0.0
    )

    return BorrowingResult(
        borrowing_power=round(borrowing, 2),
        max_property=round(max_prop, 2),
        lvr=round(lvr, 2),
        monthly_repayment=round(monthly_repay, 2),
        gross_assessable=round(gross, 2),
        net_annual=round(net_annual, 2),
        net_monthly=round(net_monthly, 2),
        monthly_surplus=round(surplus, 2),
        max_repayment=round(max_repay, 2),
        hem_applied=hem_applied,
        hem_value=round(hem, 2),
        dti_applied=dti_applied,
        dti_cap=round(dti_cap, 2),
        best_rate=BASE_RATE,
    )
