"""Integration tests for the FastAPI endpoints using mocked DynamoDB."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Product

client = TestClient(app)

_PRODUCT = Product(
    product_id="supplier#espresso",
    supplier="Test Supplier",
    name="Espresso",
    url="https://example.com/espresso",
    current_price=Decimal("12.00"),
    currency="GBP",
    available=True,
    on_sale=False,
)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("app.api.products.ProductStore")
def test_list_products(mock_store_cls):
    mock_store_cls.return_value.get_all_products.return_value = [_PRODUCT]
    resp = client.get("/api/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Espresso"


@patch("app.api.products.ProductStore")
def test_get_product_not_found(mock_store_cls):
    mock_store_cls.return_value.get_product.return_value = None
    resp = client.get("/api/products/nonexistent#product")
    assert resp.status_code == 404
