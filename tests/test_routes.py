"""
Tests for API routes.

These tests cover the happy paths for /quote and /charge endpoints.
They do NOT cover all underlying business logic branches.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestQuoteEndpoint:
    """Tests for POST /quote endpoint."""

    @patch("app.services.billing.datetime")
    def test_quote_success(self, mock_datetime):
        """Test successful quote generation."""
        mock_datetime.now.return_value.weekday.return_value = 2  # Wednesday

        response = client.post(
            "/quote",
            json={
                "user_id": "user-123",
                "tier": "free",
                "region": "EU",
                "items": [
                    {"sku": "SKU-001", "qty": 2, "unit_price": 25.0},
                ],
                "coupon": None,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subtotal"] == 50.0
        assert data["currency"] == "USD"
        assert "discount" in data
        assert "tax" in data
        assert "total" in data

    @patch("app.services.billing.datetime")
    def test_quote_with_coupon(self, mock_datetime):
        """Test quote with valid coupon code."""
        mock_datetime.now.return_value.weekday.return_value = 1

        response = client.post(
            "/quote",
            json={
                "user_id": "user-456",
                "tier": "pro",
                "region": "US",
                "items": [
                    {"sku": "SKU-002", "qty": 1, "unit_price": 100.0},
                ],
                "coupon": "SAVE10",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["discount"] > 0  # Should have discount from tier + coupon

    def test_quote_empty_items_rejected(self):
        """Test that empty items list is rejected."""
        response = client.post(
            "/quote",
            json={
                "user_id": "user-789",
                "tier": "free",
                "region": "EU",
                "items": [],
                "coupon": None,
            },
        )

        assert response.status_code == 400

    def test_quote_invalid_tier_rejected(self):
        """Test that invalid tier is rejected by Pydantic."""
        response = client.post(
            "/quote",
            json={
                "user_id": "user-000",
                "tier": "invalid",
                "region": "EU",
                "items": [{"sku": "X", "qty": 1, "unit_price": 10.0}],
            },
        )

        assert response.status_code == 422


class TestChargeEndpoint:
    """Tests for POST /charge endpoint."""

    def test_charge_card_success(self):
        """Test successful card charge."""
        response = client.post(
            "/charge",
            json={
                "user_id": "safe-customer",
                "amount": 50.0,
                "currency": "USD",
                "payment_method": "card",
                "region": "EU",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "approved" in data
        assert "reason" in data
        assert "risk_score" in data
        assert isinstance(data["approved"], bool)
        assert isinstance(data["risk_score"], float)

    def test_charge_us_region(self):
        """Test charge in US region."""
        response = client.post(
            "/charge",
            json={
                "user_id": "us-customer",
                "amount": 100.0,
                "currency": "USD",
                "payment_method": "card",
                "region": "US",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["risk_score"] <= 1.0

    def test_charge_invalid_payment_method_rejected(self):
        """Test that invalid payment method is rejected."""
        response = client.post(
            "/charge",
            json={
                "user_id": "customer",
                "amount": 50.0,
                "currency": "USD",
                "payment_method": "crypto",
                "region": "US",
            },
        )

        assert response.status_code == 422

    def test_charge_negative_amount_rejected(self):
        """Test that negative amount is rejected."""
        response = client.post(
            "/charge",
            json={
                "user_id": "customer",
                "amount": -10.0,
                "currency": "USD",
                "payment_method": "card",
                "region": "US",
            },
        )

        assert response.status_code == 422
