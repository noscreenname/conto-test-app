"""
Policy rules for discounts and promotions.

INTENTIONALLY UNDER-TESTED: This module contains multiple branches.
Tests only cover:
  - free tier + EU weekday
  - pro tier + US weekday

NOT covered (for Conto testing):
  - APAC region branch
  - weekend logic (weekday >= 5)
  - invalid coupon branch
  - enterprise tier
"""

from typing import Optional

from app.core.utils import calculate_percentage, normalize_coupon, round_money

# Valid coupon codes and their discount percentages
VALID_COUPONS = {
    "SAVE10": 10.0,
    "SAVE20": 20.0,
    "WELCOME": 15.0,
    "VIP50": 50.0,
}

# Tier-based discount percentages
TIER_DISCOUNTS = {
    "free": 0.0,
    "pro": 5.0,
    "enterprise": 15.0,
}

# Regional adjustments (multipliers)
REGION_MULTIPLIERS = {
    "EU": 1.0,
    "US": 1.0,
    "APAC": 1.2,  # APAC gets boosted discounts
}


def compute_discount(
    tier: str,
    region: str,
    subtotal: float,
    coupon: Optional[str],
    weekday: int,
) -> float:
    """
    Compute the total discount for an order.

    Args:
        tier: Customer tier (free, pro, enterprise)
        region: Customer region (EU, US, APAC)
        subtotal: Order subtotal before discounts
        coupon: Optional coupon code
        weekday: Day of week (0=Monday, 6=Sunday)

    Returns:
        Total discount amount
    """
    if subtotal <= 0:
        return 0.0

    discount = 0.0

    # Tier-based discount
    tier_discount_pct = TIER_DISCOUNTS.get(tier.lower(), 0.0)
    discount += calculate_percentage(subtotal, tier_discount_pct)

    # Coupon discount (UNCOVERED: invalid coupon branch)
    normalized_coupon = normalize_coupon(coupon)
    if normalized_coupon is not None:
        if normalized_coupon in VALID_COUPONS:
            coupon_pct = VALID_COUPONS[normalized_coupon]
            discount += calculate_percentage(subtotal, coupon_pct)
        else:
            # Invalid coupon - no additional discount
            # This branch is intentionally not tested
            pass

    # Weekend bonus (UNCOVERED: weekend branch)
    if weekday >= 5:
        # Weekend: extra 5% off
        weekend_bonus = calculate_percentage(subtotal, 5.0)
        discount += weekend_bonus

    # Regional adjustment (UNCOVERED: APAC branch)
    if region == "APAC":
        # APAC customers get boosted discounts
        multiplier = REGION_MULTIPLIERS["APAC"]
        discount = round_money(discount * multiplier)
    elif region == "EU":
        # EU standard
        pass
    elif region == "US":
        # US standard
        pass

    # Cap discount at 60% of subtotal
    max_discount = round_money(subtotal * 0.6)
    if discount > max_discount:
        discount = max_discount

    return round_money(discount)


def is_eligible_for_promotion(tier: str, region: str, order_count: int) -> bool:
    """
    Check if customer is eligible for special promotions.

    UNCOVERED: enterprise tier branch
    """
    if tier == "enterprise":
        # Enterprise always eligible
        return True
    elif tier == "pro":
        # Pro needs at least 3 orders
        return order_count >= 3
    else:
        # Free tier needs at least 10 orders
        return order_count >= 10
