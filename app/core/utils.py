"""Utility functions - well-tested module."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional


def round_money(value: float, decimals: int = 2) -> float:
    """Round a monetary value to specified decimal places using banker's rounding."""
    d = Decimal(str(value))
    rounded = d.quantize(Decimal(10) ** -decimals, rounding=ROUND_HALF_UP)
    return float(rounded)


def normalize_coupon(coupon: Optional[str]) -> Optional[str]:
    """Normalize coupon code: uppercase and strip whitespace."""
    if coupon is None:
        return None
    normalized = coupon.strip().upper()
    if not normalized:
        return None
    return normalized


def safe_float(value: any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    if value is None:
        return default
    try:
        result = float(value)
        if result < 0:
            return default
        return result
    except (ValueError, TypeError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(max_val, value))


def calculate_percentage(amount: float, percentage: float) -> float:
    """Calculate a percentage of an amount."""
    return round_money(amount * (percentage / 100.0))
