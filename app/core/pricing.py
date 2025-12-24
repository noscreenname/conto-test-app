"""
Pricing calculations - HOTSPOT CANDIDATE.

This module is designed to be touched frequently to build churn history.
After 6-10 small PRs modifying this file, it will trigger Conto's
Hotspot Risk signal.
"""

from typing import List, Optional

from app.core.policy import compute_discount
from app.core.utils import round_money, safe_float

# Tax rates by region
TAX_RATES = {
    "EU": 0.20,   # 20% VAT
    "US": 0.08,   # 8% average sales tax
    "APAC": 0.10, # 10% GST
}

# Minimum order amounts by region
MIN_ORDER_AMOUNTS = {
    "EU": 10.0,
    "US": 5.0,
    "APAC": 15.0,
}


def calculate_subtotal(items: List[dict]) -> float:
    """
    Calculate the subtotal from a list of items.

    Args:
        items: List of dicts with 'qty' and 'unit_price' keys

    Returns:
        Subtotal amount
    """
    total = 0.0
    for item in items:
        qty = safe_float(item.get("qty"), default=0.0)
        unit_price = safe_float(item.get("unit_price"), default=0.0)
        total += qty * unit_price
    return round_money(total)


def calculate_tax(subtotal: float, region: str) -> float:
    """
    Calculate tax based on region.

    Args:
        subtotal: The subtotal amount (after discounts)
        region: Customer region (EU, US, APAC)

    Returns:
        Tax amount
    """
    rate = TAX_RATES.get(region, 0.08)  # Default to US rate
    return round_money(subtotal * rate)


def calculate_total(
    items: List[dict],
    tier: str,
    region: str,
    coupon: Optional[str],
    weekday: int,
) -> dict:
    """
    Calculate complete pricing for an order.

    Args:
        items: List of order items
        tier: Customer tier
        region: Customer region
        coupon: Optional coupon code
        weekday: Day of week (0=Monday)

    Returns:
        Dict with subtotal, discount, tax, and total
    """
    subtotal = calculate_subtotal(items)
    discount = compute_discount(tier, region, subtotal, coupon, weekday)
    taxable_amount = round_money(subtotal - discount)
    tax = calculate_tax(taxable_amount, region)
    total = round_money(taxable_amount + tax)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
        "currency": "USD",
    }


def get_minimum_order(region: str) -> float:
    """Get minimum order amount for a region."""
    return MIN_ORDER_AMOUNTS.get(region, 5.0)


def apply_bulk_discount(subtotal: float, item_count: int) -> float:
    """
    Apply bulk discount for large orders.

    Args:
        subtotal: Order subtotal
        item_count: Total number of items

    Returns:
        Discount amount for bulk orders
    """
    if item_count >= 100:
        return round_money(subtotal * 0.15)
    elif item_count >= 50:
        return round_money(subtotal * 0.10)
    elif item_count >= 20:
        return round_money(subtotal * 0.05)
    return 0.0
# Churn marker: 1766570264
