"""API route definitions."""

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.billing import charge, create_quote

router = APIRouter()


# Request/Response models


class OrderItem(BaseModel):
    sku: str
    qty: int = Field(gt=0)
    unit_price: float = Field(gt=0)


class QuoteRequest(BaseModel):
    user_id: str
    tier: Literal["free", "pro", "enterprise"]
    region: Literal["EU", "US", "APAC"]
    items: List[OrderItem]
    coupon: Optional[str] = None


class QuoteResponse(BaseModel):
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str = "USD"


class ChargeRequest(BaseModel):
    user_id: str
    amount: float = Field(gt=0)
    currency: Literal["USD"] = "USD"
    payment_method: Literal["card", "invoice"]
    region: Literal["EU", "US", "APAC"]


class ChargeResponse(BaseModel):
    approved: bool
    reason: str
    risk_score: float


# Endpoints


@router.post("/quote", response_model=QuoteResponse)
def post_quote(request: QuoteRequest) -> QuoteResponse:
    """
    Generate a price quote for an order.

    Takes customer tier, region, items, and optional coupon code.
    Returns subtotal, discount, tax, and total.
    """
    if not request.items:
        raise HTTPException(status_code=400, detail="Items list cannot be empty")

    items = [item.model_dump() for item in request.items]

    result = create_quote(
        user_id=request.user_id,
        tier=request.tier,
        region=request.region,
        items=items,
        coupon=request.coupon,
    )

    return QuoteResponse(**result)


@router.post("/charge", response_model=ChargeResponse)
def post_charge(request: ChargeRequest) -> ChargeResponse:
    """
    Process a charge request.

    Performs fraud risk assessment and returns approval status.
    """
    result = charge(
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        payment_method=request.payment_method,
        region=request.region,
    )

    return ChargeResponse(**result)
