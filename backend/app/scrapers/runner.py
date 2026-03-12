"""Loads supplier config and runs all scrapers concurrently."""
import asyncio
import logging
from pathlib import Path

import yaml

from app.models import Product
from app.scrapers.base import BaseScraper
from app.scrapers.shopify import ShopifyJsonScraper

logger = logging.getLogger(__name__)

_SUPPLIERS_FILE = Path(__file__).parent.parent.parent / "suppliers.yaml"


def load_supplier_configs(path: Path = _SUPPLIERS_FILE) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("suppliers", [])


def build_scraper(config: dict) -> BaseScraper | ShopifyJsonScraper:
    """Return the right scraper instance based on the supplier's 'type' field."""
    supplier_type = config.get("type", "html")
    if supplier_type == "shopify":
        return ShopifyJsonScraper(config)
    return BaseScraper(config)


async def run_all_scrapers(configs: list[dict] | None = None) -> list[Product]:
    """Scrape all configured suppliers concurrently and return all products."""
    if configs is None:
        configs = load_supplier_configs()

    async def _scrape_one(config: dict) -> list[Product]:
        scraper = build_scraper(config)
        try:
            products = await scraper.scrape()
            logger.info("Scraped %d products from %s", len(products), config["name"])
            return products
        except Exception as exc:
            logger.error("Failed to scrape %s: %s", config["name"], exc)
            return []

    results = await asyncio.gather(*[_scrape_one(c) for c in configs])
    return [p for supplier_products in results for p in supplier_products]
