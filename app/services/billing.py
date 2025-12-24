"""Billing service - orchestrates pricing and fraud checks."""

from datetime import datetime
from typing import List, Optional

from app.core.pricing import calculate_total
from app.core.utils import round_money
from app.services.fraud import assess_risk, get_risk_reason


def create_quote(
    user_id: str,
    tier: str,
    region: str,
    items: List[dict],
    coupon: Optional[str] = None,
) -> dict:
    """
    Create a price quote for an order.

    Args:
        user_id: Customer identifier
        tier: Customer tier (free, pro, enterprise)
        region: Customer region (EU, US, APAC)
        items: List of order items
        coupon: Optional coupon code

    Returns:
        Quote with subtotal, discount, tax, and total
    """
    # Use current weekday for discount calculation
    weekday = datetime.now().weekday()

    pricing = calculate_total(
        items=items,
        tier=tier,
        region=region,
        coupon=coupon,
        weekday=weekday,
    )

    return pricing


def charge(
    user_id: str,
    amount: float,
    currency: str,
    payment_method: str,
    region: str,
) -> dict:
    """
    Process a charge request.

    Args:
        user_id: Customer identifier
        amount: Charge amount
        currency: Currency code (USD)
        payment_method: Payment method (card, invoice)
        region: Customer region

    Returns:
        Charge result with approved status, reason, and risk score
    """
    # Assess fraud risk
    risk_result = assess_risk(
        user_id=user_id,
        amount=amount,
        region=region,
        payment_method=payment_method,
    )

    # Determine approval
    approved = not risk_result["is_high_risk"]
    reason = get_risk_reason(risk_result)

    return {
        "approved": approved,
        "reason": reason,
        "risk_score": round_money(risk_result["risk_score"]),
    }
