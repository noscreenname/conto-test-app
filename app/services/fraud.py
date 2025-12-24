"""
Fraud detection service.

Contains risk assessment logic with intentionally uncovered branches
for testing Conto's coverage attention gap signal.
"""

import hashlib

from app.core.utils import clamp, round_money

# Risk thresholds
HIGH_RISK_THRESHOLD = 0.7
MEDIUM_RISK_THRESHOLD = 0.4

# Amount thresholds by payment method
AMOUNT_THRESHOLDS = {
    "card": 5000.0,
    "invoice": 10000.0,
}


def _hash_user_id(user_id: str) -> float:
    """Generate a deterministic 'risk factor' from user_id for demo purposes."""
    h = hashlib.md5(user_id.encode()).hexdigest()
    return (int(h[:8], 16) % 100) / 100.0


def assess_risk(
    user_id: str,
    amount: float,
    region: str,
    payment_method: str,
) -> dict:
    """
    Assess fraud risk for a transaction.

    Args:
        user_id: Customer identifier
        amount: Transaction amount
        region: Customer region (EU, US, APAC)
        payment_method: Payment method (card, invoice)

    Returns:
        Dict with risk_score, is_high_risk, and flags
    """
    base_risk = _hash_user_id(user_id)
    flags = []

    # Amount-based risk
    threshold = AMOUNT_THRESHOLDS.get(payment_method, 5000.0)
    if amount > threshold:
        base_risk += 0.2
        flags.append("high_amount")

    # Region-based adjustments (UNCOVERED: APAC + invoice branch)
    if region == "APAC" and payment_method == "invoice":
        # Special handling for APAC invoices - higher scrutiny
        base_risk += 0.25
        flags.append("apac_invoice_review")
    elif region == "APAC":
        base_risk += 0.1
        flags.append("apac_region")
    elif region == "EU":
        # EU has strong fraud protection
        base_risk -= 0.05

    # Payment method adjustments
    if payment_method == "invoice":
        # Invoice payments have delayed risk
        base_risk += 0.15
        flags.append("invoice_payment")

    # Clamp final risk score
    risk_score = round_money(clamp(base_risk, 0.0, 1.0))

    return {
        "risk_score": risk_score,
        "is_high_risk": risk_score >= HIGH_RISK_THRESHOLD,
        "is_medium_risk": risk_score >= MEDIUM_RISK_THRESHOLD,
        "flags": flags,
    }


def should_require_verification(risk_result: dict, amount: float) -> bool:
    """
    Determine if additional verification is required.

    UNCOVERED: high amount + medium risk branch
    """
    if risk_result["is_high_risk"]:
        return True
    if risk_result["is_medium_risk"] and amount > 2000.0:
        # Medium risk + high amount needs verification
        return True
    return False


def get_risk_reason(risk_result: dict) -> str:
    """Generate a human-readable risk reason."""
    if risk_result["is_high_risk"]:
        return "Transaction flagged for high risk"
    elif risk_result["is_medium_risk"]:
        return "Transaction flagged for review"
    return "Transaction approved"
