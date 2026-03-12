"""Tests that suppliers.yaml is valid and each entry produces usable scraper config.

Unit tests run always.
Live scrape tests are opt-in:  uv run pytest -m network
"""
import re
from urllib.parse import urlparse

import pytest
import yaml

from app.scrapers.base import BaseScraper
from app.scrapers.runner import load_supplier_configs

# ── Required shape ────────────────────────────────────────────────────────────

REQUIRED_TOP_KEYS = {"name", "base_url", "products_url", "selectors"}
REQUIRED_SELECTORS = {"product_list", "name", "price"}
VALID_CURRENCIES = {"GBP", "USD", "EUR"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _is_valid_css_selector(selector: str) -> bool:
    """Rough sanity check — non-empty, starts with a recognised token."""
    if not selector or not selector.strip():
        return False
    # Must start with ., #, a tag name, or a combinator/attribute
    return bool(re.match(r"^[.#\[a-zA-Z*>~+]", selector.strip()))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def configs():
    return load_supplier_configs()


# ── YAML loading ──────────────────────────────────────────────────────────────

def test_suppliers_yaml_loads(configs):
    assert isinstance(configs, list), "suppliers.yaml must contain a 'suppliers' list"
    assert len(configs) > 0, "suppliers.yaml must define at least one supplier"


# ── Per-supplier schema tests (parametrised) ──────────────────────────────────

@pytest.fixture(params=lambda: load_supplier_configs(), ids=lambda c: c.get("name", "?"))
def supplier(request, configs):
    # Use the module-scoped configs list for parametrisation
    return request.param


def pytest_generate_tests(metafunc):
    """Parametrise any test that takes a 'supplier' fixture from suppliers.yaml."""
    if "supplier" in metafunc.fixturenames:
        cfgs = load_supplier_configs()
        metafunc.parametrize("supplier", cfgs, ids=[c["name"] for c in cfgs])


def test_supplier_has_required_keys(supplier):
    missing = REQUIRED_TOP_KEYS - supplier.keys()
    assert not missing, f"[{supplier.get('name')}] missing keys: {missing}"


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


def test_supplier_has_required_selectors(supplier):
    selectors = supplier.get("selectors", {})
    missing = REQUIRED_SELECTORS - selectors.keys()
    assert not missing, \
        f"[{supplier['name']}] selectors missing required keys: {missing}"


def test_supplier_required_selectors_are_valid_css(supplier):
    selectors = supplier.get("selectors", {})
    for key in REQUIRED_SELECTORS:
        value = selectors.get(key, "")
        assert _is_valid_css_selector(value), (
            f"[{supplier['name']}] selector '{key}' looks invalid: {value!r}"
        )


def test_supplier_optional_selectors_are_valid_css_when_present(supplier):
    optional = {"availability", "sale_badge", "image"}
    selectors = supplier.get("selectors", {})
    for key in optional & selectors.keys():
        value = selectors[key]
        assert _is_valid_css_selector(value), (
            f"[{supplier['name']}] optional selector '{key}' looks invalid: {value!r}"
        )


def test_supplier_no_unknown_selector_keys(supplier):
    known = REQUIRED_SELECTORS | {"availability", "sale_badge", "image"}
    unknown = supplier.get("selectors", {}).keys() - known
    assert not unknown, \
        f"[{supplier['name']}] unknown selector keys: {unknown}. Add them to the known set if intentional."


# ── Scraper construction ───────────────────────────────────────────────────────

def test_supplier_creates_valid_scraper(supplier):
    """Each config must construct a BaseScraper without raising."""
    scraper = BaseScraper(supplier)
    assert scraper.name == supplier["name"]
    assert scraper.base_url == supplier["base_url"].rstrip("/")
    assert scraper.products_url == supplier["products_url"]
    assert scraper.currency == supplier.get("currency", "GBP")


# ── Live network tests (opt-in with  pytest -m network) ───────────────────────

@pytest.mark.network
@pytest.mark.asyncio
async def test_live_scrape_returns_products(supplier):
    """Actually fetches the supplier page and checks at least one product is returned."""
    scraper = BaseScraper(supplier)
    products = await scraper.scrape()

    assert len(products) > 0, (
        f"[{supplier['name']}] live scrape returned no products — "
        "check products_url and CSS selectors in suppliers.yaml"
    )


@pytest.mark.network
@pytest.mark.asyncio
async def test_live_scrape_products_have_valid_fields(supplier):
    """Each scraped product must have a non-empty name, positive price, and valid product_id."""
    scraper = BaseScraper(supplier)
    products = await scraper.scrape()

    for p in products:
        assert p.name.strip(), f"[{supplier['name']}] product has empty name"
        assert p.current_price > 0, \
            f"[{supplier['name']}] '{p.name}' has non-positive price: {p.current_price}"
        assert "#" in p.product_id, \
            f"[{supplier['name']}] product_id missing '#' separator: {p.product_id!r}"
        assert _is_valid_url(p.url), \
            f"[{supplier['name']}] '{p.name}' has invalid URL: {p.url!r}"
