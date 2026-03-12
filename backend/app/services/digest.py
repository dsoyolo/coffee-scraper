"""Builds the daily digest summary from stored products."""
from datetime import datetime, timezone

from app.models import DigestSummary, Product
from app.services.dynamo import ProductStore


def build_digest(store: ProductStore | None = None) -> DigestSummary:
    if store is None:
        store = ProductStore()

    products = store.get_all_products()

    available = [p for p in products if p.available]
    unavailable = [p for p in products if not p.available]
    on_sale = [p for p in products if p.on_sale]
    price_drops = [p for p in products if p.price_drop]

    # "Back in stock" = available now but previously had no stock
    # We approximate this by checking price_drop=False and available=True with a previous_price
    back_in_stock = [
        p for p in products
        if p.available and p.previous_price is not None and not p.price_drop
    ]
    out_of_stock = [p for p in products if not p.available and p.previous_price is not None]

    return DigestSummary(
        generated_at=datetime.now(timezone.utc),
        total_products=len(products),
        available_count=len(available),
        unavailable_count=len(unavailable),
        on_sale_count=len(on_sale),
        price_drops=_sort_by_drop(price_drops),
        new_sales=on_sale,
        back_in_stock=back_in_stock,
        out_of_stock=out_of_stock,
        all_products=products,
    )


def _sort_by_drop(products: list[Product]) -> list[Product]:
    return sorted(products, key=lambda p: p.price_drop_pct or 0, reverse=True)
