"""Tests that suppliers.yaml is valid and each entry produces a usable scraper.

Unit tests run always.
Live scrape tests are opt-in:  uv run pytest -m network
"""
import re
from urllib.parse import urlparse

import pytest

from app.scrapers.base import BaseScraper
from app.scrapers.runner import build_scraper, load_supplier_configs
from app.scrapers.shopify import ShopifyJsonScraper

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_TYPES = {"html", "shopify"}
VALID_CURRENCIES = {"GBP", "USD", "EUR", "CAD", "AUD"}
REQUIRED_TOP_KEYS = {"name", "base_url", "products_url"}   # common to all types
REQUIRED_SELECTORS = {"product_list", "name", "price"}      # html type only
KNOWN_SELECTOR_KEYS = REQUIRED_SELECTORS | {"availability", "sale_badge", "image"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _is_valid_css_selector(selector: str) -> bool:
    """Rough sanity check — non-empty, starts with a recognised CSS token."""
    if not selector or not selector.strip():
        return False
    return bool(re.match(r"^[.#\[a-zA-Z*>~+]", selector.strip()))


def _is_html(supplier: dict) -> bool:
    return supplier.get("type", "html") == "html"


def _is_shopify(supplier: dict) -> bool:
    return supplier.get("type") == "shopify"


# ── Parametrisation ───────────────────────────────────────────────────────────

def pytest_generate_tests(metafunc):
    if "supplier" in metafunc.fixturenames:
        cfgs = load_supplier_configs()
        metafunc.parametrize("supplier", cfgs, ids=[c["name"] for c in cfgs])


# ── YAML loading ──────────────────────────────────────────────────────────────

def test_suppliers_yaml_loads():
    configs = load_supplier_configs()
    assert isinstance(configs, list), "suppliers.yaml must contain a 'suppliers' list"
    assert len(configs) > 0, "suppliers.yaml must define at least one supplier"


# ── Common field tests (all types) ────────────────────────────────────────────

def test_supplier_has_required_keys(supplier):
    missing = REQUIRED_TOP_KEYS - supplier.keys()
    assert not missing, f"[{supplier.get('name')}] missing keys: {missing}"


def test_supplier_type_is_valid(supplier):
    t = supplier.get("type", "html")
    assert t in VALID_TYPES, \
        f"[{supplier['name']}] unknown type {t!r}; expected one of {VALID_TYPES}"


def test_supplier_name_is_non_empty_string(supplier):
    assert isinstance(supplier["name"], str) and supplier["name"].strip(), \
        "name must be a non-empty string"


def test_supplier_base_url_is_valid(supplier):
    assert _is_valid_url(supplier["base_url"]), \
        f"[{supplier['name']}] base_url is not a valid HTTP/HTTPS URL: {supplier['base_url']!r}"


def test_supplier_products_url_is_valid(supplier):
    assert _is_valid_url(supplier["products_url"]), \
        f"[{supplier['name']}] products_url is not a valid HTTP/HTTPS URL: {supplier['products_url']!r}"


def test_supplier_products_url_starts_with_base_url(supplier):
    assert supplier["products_url"].startswith(supplier["base_url"]), (
        f"[{supplier['name']}] products_url should be under base_url\n"
        f"  base_url:     {supplier['base_url']}\n"
        f"  products_url: {supplier['products_url']}"
    )


def test_supplier_currency_is_valid(supplier):
    currency = supplier.get("currency", "GBP")
    assert currency in VALID_CURRENCIES, \
        f"[{supplier['name']}] unknown currency {currency!r}; expected one of {VALID_CURRENCIES}"


# ── HTML-type selector tests ──────────────────────────────────────────────────

def test_html_supplier_has_selectors(supplier):
    if not _is_html(supplier):
        pytest.skip("not an html supplier")
    assert "selectors" in supplier, \
        f"[{supplier['name']}] html suppliers must have a 'selectors' block"


def test_html_supplier_has_required_selectors(supplier):
    if not _is_html(supplier):
        pytest.skip("not an html supplier")
    selectors = supplier.get("selectors", {})
    missing = REQUIRED_SELECTORS - selectors.keys()
    assert not missing, \
        f"[{supplier['name']}] selectors missing required keys: {missing}"


def test_html_supplier_required_selectors_are_valid_css(supplier):
    if not _is_html(supplier):
        pytest.skip("not an html supplier")
    selectors = supplier.get("selectors", {})
    for key in REQUIRED_SELECTORS:
        value = selectors.get(key, "")
        assert _is_valid_css_selector(value), \
            f"[{supplier['name']}] selector '{key}' looks invalid: {value!r}"


def test_html_supplier_optional_selectors_are_valid_css_when_present(supplier):
    if not _is_html(supplier):
        pytest.skip("not an html supplier")
    optional = {"availability", "sale_badge", "image"}
    for key in optional & supplier.get("selectors", {}).keys():
        value = supplier["selectors"][key]
        assert _is_valid_css_selector(value), \
            f"[{supplier['name']}] optional selector '{key}' looks invalid: {value!r}"


def test_html_supplier_no_unknown_selector_keys(supplier):
    if not _is_html(supplier):
        pytest.skip("not an html supplier")
    unknown = supplier.get("selectors", {}).keys() - KNOWN_SELECTOR_KEYS
    assert not unknown, \
        f"[{supplier['name']}] unknown selector keys: {unknown}. Add them to KNOWN_SELECTOR_KEYS if intentional."


# ── Shopify-type tests ────────────────────────────────────────────────────────

def test_shopify_supplier_has_no_selectors(supplier):
    if not _is_shopify(supplier):
        pytest.skip("not a shopify supplier")
    assert "selectors" not in supplier, \
        f"[{supplier['name']}] shopify suppliers should not have a 'selectors' block"


def test_shopify_supplier_collection_is_derivable(supplier):
    if not _is_shopify(supplier):
        pytest.skip("not a shopify supplier")
    scraper = ShopifyJsonScraper(supplier)
    assert scraper._collection, \
        f"[{supplier['name']}] could not derive collection from products_url: {supplier['products_url']!r}"


def test_shopify_supplier_api_url_is_valid(supplier):
    if not _is_shopify(supplier):
        pytest.skip("not a shopify supplier")
    scraper = ShopifyJsonScraper(supplier)
    assert _is_valid_url(scraper._api_url), \
        f"[{supplier['name']}] derived API URL is not valid: {scraper._api_url!r}"


# ── Scraper construction (all types) ─────────────────────────────────────────

def test_build_scraper_returns_correct_type(supplier):
    scraper = build_scraper(supplier)
    if _is_shopify(supplier):
        assert isinstance(scraper, ShopifyJsonScraper), \
            f"[{supplier['name']}] expected ShopifyJsonScraper"
    else:
        assert isinstance(scraper, BaseScraper), \
            f"[{supplier['name']}] expected BaseScraper"


def test_scraper_name_and_urls_match_config(supplier):
    scraper = build_scraper(supplier)
    assert scraper.name == supplier["name"]
    assert scraper.base_url == supplier["base_url"].rstrip("/")
    assert scraper.products_url == supplier["products_url"]
    assert scraper.currency == supplier.get("currency", "GBP")


# ── Live network tests (opt-in: pytest -m network) ────────────────────────────

@pytest.mark.network
@pytest.mark.asyncio
async def test_live_scrape_returns_products(supplier):
    """Fetches the real supplier page/API and asserts at least one product is returned."""
    scraper = build_scraper(supplier)
    products = await scraper.scrape()
    assert len(products) > 0, (
        f"[{supplier['name']}] live scrape returned no products — "
        "check products_url and config in suppliers.yaml"
    )


@pytest.mark.network
@pytest.mark.asyncio
async def test_live_scrape_products_have_valid_fields(supplier):
    """Every scraped product must have a non-empty name, positive price, and valid URL."""
    scraper = build_scraper(supplier)
    products = await scraper.scrape()
    for p in products:
        assert p.name.strip(), \
            f"[{supplier['name']}] product has empty name"
        assert p.current_price > 0, \
            f"[{supplier['name']}] '{p.name}' has non-positive price: {p.current_price}"
        assert "#" in p.product_id, \
            f"[{supplier['name']}] product_id missing '#' separator: {p.product_id!r}"
        assert _is_valid_url(p.url), \
            f"[{supplier['name']}] '{p.name}' has invalid URL: {p.url!r}"
