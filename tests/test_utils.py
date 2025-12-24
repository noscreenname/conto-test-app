"""Tests for utility functions - thoroughly tested module."""

import pytest

from app.core.utils import (
    calculate_percentage,
    clamp,
    normalize_coupon,
    round_money,
    safe_float,
)


class TestRoundMoney:
    def test_rounds_to_two_decimals_by_default(self):
        assert round_money(10.555) == 10.56
        assert round_money(10.554) == 10.55

    def test_rounds_to_specified_decimals(self):
        assert round_money(10.5555, decimals=3) == 10.556
        assert round_money(10.5, decimals=0) == 11.0

    def test_handles_zero(self):
        assert round_money(0.0) == 0.0

    def test_handles_negative(self):
        assert round_money(-10.555) == -10.56  # ROUND_HALF_UP rounds away from zero


class TestNormalizeCoupon:
    def test_normalizes_to_uppercase(self):
        assert normalize_coupon("save10") == "SAVE10"
        assert normalize_coupon("Save20") == "SAVE20"

    def test_strips_whitespace(self):
        assert normalize_coupon("  SAVE10  ") == "SAVE10"
        assert normalize_coupon("\tWELCOME\n") == "WELCOME"

    def test_returns_none_for_none(self):
        assert normalize_coupon(None) is None

    def test_returns_none_for_empty_string(self):
        assert normalize_coupon("") is None
        assert normalize_coupon("   ") is None


class TestSafeFloat:
    def test_converts_valid_numbers(self):
        assert safe_float(10) == 10.0
        assert safe_float("10.5") == 10.5
        assert safe_float(0) == 0.0

    def test_returns_default_for_none(self):
        assert safe_float(None) == 0.0
        assert safe_float(None, default=5.0) == 5.0

    def test_returns_default_for_invalid(self):
        assert safe_float("abc") == 0.0
        assert safe_float("abc", default=1.0) == 1.0

    def test_returns_default_for_negative(self):
        assert safe_float(-5) == 0.0
        assert safe_float(-5, default=1.0) == 1.0


class TestClamp:
    def test_returns_value_when_in_range(self):
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_clamps_to_min(self):
        assert clamp(-5.0, 0.0, 10.0) == 0.0

    def test_clamps_to_max(self):
        assert clamp(15.0, 0.0, 10.0) == 10.0

    def test_handles_boundary_values(self):
        assert clamp(0.0, 0.0, 10.0) == 0.0
        assert clamp(10.0, 0.0, 10.0) == 10.0


class TestCalculatePercentage:
    def test_calculates_percentage(self):
        assert calculate_percentage(100.0, 10.0) == 10.0
        assert calculate_percentage(200.0, 15.0) == 30.0

    def test_handles_zero(self):
        assert calculate_percentage(0.0, 10.0) == 0.0
        assert calculate_percentage(100.0, 0.0) == 0.0

    def test_rounds_result(self):
        assert calculate_percentage(33.33, 33.33) == 11.11
