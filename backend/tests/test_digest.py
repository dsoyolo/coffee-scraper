"""Tests for the digest service."""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from app.models import Product
from app.services.digest import build_digest


def _make_product(**kwargs) -> Product:
    defaults = {
        "product_id": "supplier#test-coffee",
        "supplier": "Supplier",
        "name": "Test Coffee",
        "url": "https://example.com/coffee",
        "current_price": Decimal("12.00"),
        "currency": "GBP",
        "available": True,
        "on_sale": False,
        "price_drop": False,
    }
    defaults.update(kwargs)
    return Product(**defaults)


def test_digest_counts():
    products = [
        _make_product(product_id="s#a", name="A", available=True, on_sale=False, price_drop=False),
        _make_product(product_id="s#b", name="B", available=True, on_sale=True, price_drop=True, price_drop_pct=10.0, previous_price=Decimal("13.00")),
        _make_product(product_id="s#c", name="C", available=False, on_sale=False, price_drop=False),
    ]
    store = MagicMock()
    store.get_all_products.return_value = products

    digest = build_digest(store)

    assert digest.total_products == 3
    assert digest.available_count == 2
    assert digest.unavailable_count == 1
    assert digest.on_sale_count == 1
    assert len(digest.price_drops) == 1
    assert digest.price_drops[0].name == "B"


def test_digest_price_drops_sorted_by_pct():
    products = [
        _make_product(product_id="s#a", name="A", price_drop=True, price_drop_pct=5.0, previous_price=Decimal("11.00")),
        _make_product(product_id="s#b", name="B", price_drop=True, price_drop_pct=20.0, previous_price=Decimal("15.00")),
        _make_product(product_id="s#c", name="C", price_drop=True, price_drop_pct=12.0, previous_price=Decimal("13.00")),
    ]
    store = MagicMock()
    store.get_all_products.return_value = products

    digest = build_digest(store)
    drops = digest.price_drops
    assert drops[0].name == "B"
    assert drops[1].name == "C"
    assert drops[2].name == "A"
