"""Scraper for Shopify stores using the /products.json API.

Shopify exposes a stable JSON endpoint on every store:
  {base_url}/collections/{collection}/products.json?limit=250

This is far more reliable than HTML scraping — no CSS selectors, no
theme changes, no bot-detection on the HTML page.
"""
import re
from decimal import Decimal
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.models import Product

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _collection_from_url(products_url: str) -> str:
    """Extract the collection handle from a URL like /collections/direct-trade-coffee."""
    path = urlparse(products_url).path
    parts = [p for p in path.split("/") if p]
    try:
        idx = parts.index("collections")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return ""


class ShopifyJsonScraper:
    """Fetches products from the Shopify JSON API — no HTML parsing needed."""

    def __init__(self, config: dict):
        self.name: str = config["name"]
        self.base_url: str = config["base_url"].rstrip("/")
        self.products_url: str = config["products_url"]
        self.currency: str = config.get("currency", "GBP")
        self._collection = config.get("collection") or _collection_from_url(self.products_url)

    @property
    def _api_url(self) -> str:
        return f"{self.base_url}/collections/{self._collection}/products.json?limit=250"

    async def _fetch_json(self) -> dict:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
            response = await client.get(self._api_url)
            response.raise_for_status()
            return response.json()

    def _make_product_id(self, handle: str) -> str:
        return f"{_slug(self.name)}#{handle}"

    def _parse_product(self, raw: dict) -> Optional[Product]:
        variants = raw.get("variants", [])
        if not variants:
            return None

        variant = variants[0]
        try:
            price = Decimal(str(variant["price"]))
        except Exception:
            return None

        compare_at = variant.get("compare_at_price")
        on_sale = bool(compare_at and Decimal(str(compare_at)) > price)

        # A product is available if any variant is available
        available = any(v.get("available", False) for v in variants)

        images = raw.get("images", [])
        image_url = images[0]["src"] if images else None

        handle = raw.get("handle", _slug(raw.get("title", "")))

        return Product(
            product_id=self._make_product_id(handle),
            supplier=self.name,
            name=raw["title"],
            url=f"{self.base_url}/products/{handle}",
            image_url=image_url,
            current_price=price,
            currency=self.currency,
            available=available,
            on_sale=on_sale,
        )

    async def scrape(self) -> list[Product]:
        data = await self._fetch_json()
        products = []
        for raw in data.get("products", []):
            product = self._parse_product(raw)
            if product:
                products.append(product)
        return products
