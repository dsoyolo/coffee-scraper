"""Unit tests for ShopifyJsonScraper using a mocked HTTP response."""
import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.shopify import ShopifyJsonScraper

SUPPLIER_CONFIG = {
    "name": "Detour Coffee",
    "type": "shopify",
    "base_url": "https://detourcoffee.com",
    "products_url": "https://detourcoffee.com/collections/direct-trade-coffee",
    "currency": "CAD",
}

SAMPLE_PRODUCTS_JSON = {
    "products": [
        {
            "title": "Ethiopia Guji Natural",
            "handle": "ethiopia-guji-natural",
            "variants": [
                {"price": "22.00", "compare_at_price": None, "available": True}
            ],
            "images": [{"src": "https://cdn.shopify.com/ethiopia.jpg"}],
        },
        {
            "title": "Colombia Huila Washed",
            "handle": "colombia-huila-washed",
            "variants": [
                {"price": "19.00", "compare_at_price": "24.00", "available": True}
            ],
            "images": [{"src": "https://cdn.shopify.com/colombia.jpg"}],
        },
        {
            "title": "Sold Out Blend",
            "handle": "sold-out-blend",
            "variants": [
                {"price": "18.00", "compare_at_price": None, "available": False}
            ],
            "images": [],
        },
        {
            # Malformed — no variants, should be skipped
            "title": "Bad Product",
            "handle": "bad-product",
            "variants": [],
            "images": [],
        },
    ]
}


@pytest.fixture
def scraper():
    return ShopifyJsonScraper(SUPPLIER_CONFIG)


def test_collection_derived_from_url(scraper):
    assert scraper._collection == "direct-trade-coffee"


def test_api_url_is_correct(scraper):
    assert scraper._api_url == (
        "https://detourcoffee.com/collections/direct-trade-coffee/products.json?limit=250"
    )


@pytest.mark.asyncio
async def test_scrape_parses_products(scraper):
    with patch.object(scraper, "_fetch_json", new=AsyncMock(return_value=SAMPLE_PRODUCTS_JSON)):
        products = await scraper.scrape()

    assert len(products) == 3  # bad product skipped


@pytest.mark.asyncio
async def test_scrape_regular_product(scraper):
    with patch.object(scraper, "_fetch_json", new=AsyncMock(return_value=SAMPLE_PRODUCTS_JSON)):
        products = await scraper.scrape()

    ethiopia = products[0]
    assert ethiopia.name == "Ethiopia Guji Natural"
    assert ethiopia.current_price == Decimal("22.00")
    assert ethiopia.available is True
    assert ethiopia.on_sale is False
    assert ethiopia.currency == "CAD"
    assert ethiopia.product_id == "detour-coffee#ethiopia-guji-natural"
    assert ethiopia.url == "https://detourcoffee.com/products/ethiopia-guji-natural"
    assert ethiopia.image_url == "https://cdn.shopify.com/ethiopia.jpg"


@pytest.mark.asyncio
async def test_scrape_detects_sale(scraper):
    with patch.object(scraper, "_fetch_json", new=AsyncMock(return_value=SAMPLE_PRODUCTS_JSON)):
        products = await scraper.scrape()

    colombia = products[1]
    assert colombia.on_sale is True
    assert colombia.current_price == Decimal("19.00")


@pytest.mark.asyncio
async def test_scrape_detects_sold_out(scraper):
    with patch.object(scraper, "_fetch_json", new=AsyncMock(return_value=SAMPLE_PRODUCTS_JSON)):
        products = await scraper.scrape()

    sold_out = products[2]
    assert sold_out.available is False
    assert sold_out.image_url is None


@pytest.mark.asyncio
async def test_scrape_skips_no_variants(scraper):
    with patch.object(scraper, "_fetch_json", new=AsyncMock(return_value=SAMPLE_PRODUCTS_JSON)):
        products = await scraper.scrape()

    names = [p.name for p in products]
    assert "Bad Product" not in names


@pytest.mark.asyncio
async def test_scrape_empty_collection(scraper):
    with patch.object(scraper, "_fetch_json", new=AsyncMock(return_value={"products": []})):
        products = await scraper.scrape()
    assert products == []


def test_explicit_collection_overrides_url():
    config = {**SUPPLIER_CONFIG, "collection": "all-coffee"}
    scraper = ShopifyJsonScraper(config)
    assert scraper._collection == "all-coffee"
    assert "/all-coffee/" in scraper._api_url
