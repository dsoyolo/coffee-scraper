import re
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.models import Product


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _parse_price(raw: str) -> Optional[Decimal]:
    """Extract a decimal price from a string like '£12.50' or '12.50'."""
    match = re.search(r"[\d]+[\.,][\d]{2}", raw.replace(",", "."))
    if not match:
        # try integer price e.g. "£12"
        match = re.search(r"[\d]+", raw)
    if match:
        try:
            return Decimal(match.group().replace(",", "."))
        except InvalidOperation:
            pass
    return None


class BaseScraper(ABC):
    """Base class that all supplier scrapers inherit from."""

    def __init__(self, config: dict):
        self.name: str = config["name"]
        self.base_url: str = config["base_url"].rstrip("/")
        self.products_url: str = config["products_url"]
        self.currency: str = config.get("currency", "GBP")
        self.selectors: dict = config["selectors"]
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_html(self, url: str) -> str:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _abs_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return urljoin(self.base_url, path)

    def _make_product_id(self, product_name: str) -> str:
        supplier_slug = _slug(self.name)
        product_slug = _slug(product_name)
        return f"{supplier_slug}#{product_slug}"

    def _parse_product(self, element: Tag) -> Optional[Product]:
        sel = self.selectors

        name_el = element.select_one(sel["name"])
        price_el = element.select_one(sel["price"])
        if not name_el or not price_el:
            return None

        name = name_el.get_text(strip=True)
        raw_price = price_el.get_text(strip=True)
        price = _parse_price(raw_price)
        if not price:
            return None

        # Availability: treat absence of a sold-out badge as available
        avail_sel = sel.get("availability")
        if avail_sel:
            sold_out_el = element.select_one(avail_sel)
            available = sold_out_el is None
        else:
            available = True

        # Sale badge
        sale_sel = sel.get("sale_badge")
        on_sale = bool(sale_sel and element.select_one(sale_sel))

        # URL
        link_el = element.select_one("a[href]")
        url = self._abs_url(link_el["href"]) if link_el else self.products_url

        # Image
        image_url: Optional[str] = None
        img_sel = sel.get("image")
        if img_sel:
            img_el = element.select_one(img_sel)
            if img_el:
                src = img_el.get("data-src") or img_el.get("src") or img_el.get("data-lazy-src")
                if src:
                    image_url = self._abs_url(str(src))

        return Product(
            product_id=self._make_product_id(name),
            supplier=self.name,
            name=name,
            url=url,
            image_url=image_url,
            current_price=price,
            currency=self.currency,
            available=available,
            on_sale=on_sale,
        )

    async def scrape(self) -> list[Product]:
        html = await self._get_html(self.products_url)
        soup = BeautifulSoup(html, "lxml")
        products = []
        for el in soup.select(self.selectors["product_list"]):
            product = self._parse_product(el)
            if product:
                products.append(product)
        return products
