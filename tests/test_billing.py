"""
Tests for billing service.

NOTE: These tests intentionally do NOT cover all branches in policy.py and fraud.py.
Uncovered branches:
  - policy.py: APAC region, weekend logic, invalid coupon
  - fraud.py: APAC + invoice combination
"""

from unittest.mock import patch

import pytest

from app.services.billing import charge, create_quote


class TestCreateQuote:
    """Tests for create_quote - covers basic paths only."""

    @patch("app.services.billing.datetime")
    def test_quote_free_tier_eu_weekday(self, mock_datetime):
        """Test quote for free tier EU customer on weekday (covered)."""
        mock_datetime.now.return_value.weekday.return_value = 2  # Wednesday

        result = create_quote(
            user_id="user-123",
            tier="free",
            region="EU",
            items=[
                {"sku": "ITEM-1", "qty": 2, "unit_price": 50.0},
                {"sku": "ITEM-2", "qty": 1, "unit_price": 100.0},
            ],
            coupon=None,
        )

        assert result["subtotal"] == 200.0
        assert result["discount"] == 0.0  # free tier, no coupon
        assert result["tax"] == 40.0  # 20% EU VAT
        assert result["total"] == 240.0
        assert result["currency"] == "USD"

    @patch("app.services.billing.datetime")
    def test_quote_pro_tier_us_weekday_with_coupon(self, mock_datetime):
        """Test quote for pro tier US customer with valid coupon (covered)."""
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday

        result = create_quote(
            user_id="user-456",
            tier="pro",
            region="US",
            items=[
                {"sku": "ITEM-1", "qty": 10, "unit_price": 10.0},
            ],
            coupon="SAVE10",
        )

        # subtotal = 100.0
        # pro discount = 5% = 5.0
        # coupon = 10% = 10.0
        # total discount = 15.0
        # taxable = 85.0
        # tax = 8% = 6.8
        # total = 91.8
        assert result["subtotal"] == 100.0
        assert result["discount"] == 15.0
        assert result["tax"] == 6.8
        assert result["total"] == 91.8

    @patch("app.services.billing.datetime")
    def test_quote_empty_items(self, mock_datetime):
        """Test quote with no items."""
        mock_datetime.now.return_value.weekday.return_value = 0

        result = create_quote(
            user_id="user-789",
            tier="free",
            region="EU",
            items=[],
            coupon=None,
        )

        assert result["subtotal"] == 0.0
        assert result["total"] == 0.0


class TestCharge:
    """Tests for charge - covers EU and US card payments only."""

    def test_charge_card_eu_low_amount(self):
        """Test card payment in EU with low amount (covered)."""
        result = charge(
            user_id="lowrisk",
            amount=100.0,
            currency="USD",
            payment_method="card",
            region="EU",
        )

        # EU region gives -0.05 risk adjustment
        # Low amount doesn't add risk
        assert 0.0 <= result["risk_score"] <= 1.0
        assert "approved" in result or "reason" in result

    def test_charge_card_us_medium_amount(self):
        """Test card payment in US with medium amount (covered)."""
        result = charge(
            user_id="normal-user-456",
            amount=1000.0,
            currency="USD",
            payment_method="card",
            region="US",
        )

        # Result depends on user_id hash, but should complete
        assert "approved" in result
        assert "reason" in result
        assert "risk_score" in result

    def test_charge_high_amount_may_be_declined(self):
        """Test that high amounts increase risk."""
        result = charge(
            user_id="risky-user-789",
            amount=10000.0,
            currency="USD",
            payment_method="card",
            region="US",
        )

        # High amount should increase risk score
        assert result["risk_score"] > 0.0
