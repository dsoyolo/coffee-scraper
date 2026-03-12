"""Tests for the base scraper using a mocked HTTP response."""
import pytest
from unittest.mock import AsyncMock, patch

from app.scrapers.base import BaseScraper

SUPPLIER_CONFIG = {
    "name": "Test Supplier",
    "base_url": "https://example.com",
    "products_url": "https://example.com/coffee",
    "currency": "GBP",
    "selectors": {
        "product_list": ".product",
        "name": ".name",
        "price": ".price",
        "availability": ".sold-out",
        "sale_badge": ".sale",
        "image": "img",
    },
}

SAMPLE_HTML = """
<html><body>
  <div class="product">
    <a href="/coffee/espresso-blend"><img src="/img/espresso.jpg" /></a>
    <span class="name">Espresso Blend</span>
    <span class="price">£12.50</span>
  </div>
  <div class="product">
    <a href="/coffee/filter-roast"><img src="/img/filter.jpg" /></a>
    <span class="name">Filter Roast</span>
    <span class="price">£10.00</span>
    <span class="sale">On Sale</span>
    <span class="sold-out">Sold Out</span>
  </div>
  <div class="product">
    <span class="name">No Price</span>
  </div>
</body></html>
"""


@pytest.mark.asyncio
async def test_scraper_parses_products():
    scraper = BaseScraper(SUPPLIER_CONFIG)
    with patch.object(scraper, "_get_html", new=AsyncMock(return_value=SAMPLE_HTML)):
        products = await scraper.scrape()

    assert len(products) == 2

    espresso = products[0]
    assert espresso.name == "Espresso Blend"
    assert float(espresso.current_price) == 12.50
    assert espresso.available is True
    assert espresso.on_sale is False
    assert espresso.supplier == "Test Supplier"
    assert espresso.product_id == "test-supplier#espresso-blend"

    filter_roast = products[1]
    assert filter_roast.name == "Filter Roast"
    assert float(filter_roast.current_price) == 10.00
    assert filter_roast.available is False
    assert filter_roast.on_sale is True


@pytest.mark.asyncio
async def test_scraper_skips_no_price():
    scraper = BaseScraper(SUPPLIER_CONFIG)
    with patch.object(scraper, "_get_html", new=AsyncMock(return_value=SAMPLE_HTML)):
        products = await scraper.scrape()
    names = [p.name for p in products]
    assert "No Price" not in names
