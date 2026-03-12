"""DynamoDB service — stores products and price history."""
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

from app.models import Product, PriceRecord

_TABLE_PRODUCTS = os.environ.get("DYNAMO_PRODUCTS_TABLE", "coffee-products")
_TABLE_HISTORY = os.environ.get("DYNAMO_HISTORY_TABLE", "coffee-price-history")
_AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")


def _get_resource():
    endpoint = os.environ.get("DYNAMO_ENDPOINT_URL")  # for local testing
    kwargs = {"region_name": _AWS_REGION}
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return boto3.resource("dynamodb", **kwargs)


def _to_dynamo_item(product: Product) -> dict:
    """Convert a Product to a DynamoDB-safe dict (Decimal-safe)."""
    return {
        "product_id": product.product_id,
        "supplier": product.supplier,
        "name": product.name,
        "url": product.url,
        "image_url": product.image_url or "",
        "current_price": product.current_price,
        "previous_price": product.previous_price or Decimal("0"),
        "currency": product.currency,
        "available": product.available,
        "on_sale": product.on_sale,
        "price_drop": product.price_drop,
        "price_drop_pct": Decimal(str(round(product.price_drop_pct or 0, 2))),
        "last_updated": product.last_updated.isoformat(),
    }


def _from_dynamo_item(item: dict) -> Product:
    return Product(
        product_id=item["product_id"],
        supplier=item["supplier"],
        name=item["name"],
        url=item["url"],
        image_url=item.get("image_url") or None,
        current_price=item["current_price"],
        previous_price=item.get("previous_price") or None,
        currency=item.get("currency", "GBP"),
        available=item.get("available", True),
        on_sale=item.get("on_sale", False),
        price_drop=item.get("price_drop", False),
        price_drop_pct=float(item.get("price_drop_pct", 0)) or None,
        last_updated=datetime.fromisoformat(item["last_updated"]),
    )


class ProductStore:
    def __init__(self):
        db = _get_resource()
        self._products = db.Table(_TABLE_PRODUCTS)
        self._history = db.Table(_TABLE_HISTORY)

    def get_all_products(self) -> list[Product]:
        response = self._products.scan()
        return [_from_dynamo_item(item) for item in response.get("Items", [])]

    def get_product(self, product_id: str) -> Optional[Product]:
        response = self._products.get_item(Key={"product_id": product_id})
        item = response.get("Item")
        return _from_dynamo_item(item) if item else None

    def upsert_product(self, product: Product) -> Product:
        """Store the product, carrying forward previous price for comparison."""
        existing = self.get_product(product.product_id)
        if existing:
            product.previous_price = existing.current_price
            if product.current_price < existing.current_price:
                product.price_drop = True
                drop = float(existing.current_price - product.current_price)
                product.price_drop_pct = round(drop / float(existing.current_price) * 100, 1)

        self._products.put_item(Item=_to_dynamo_item(product))
        self._save_price_record(product)
        return product

    def _save_price_record(self, product: Product) -> None:
        now = datetime.now(timezone.utc)
        self._history.put_item(Item={
            "product_id": product.product_id,
            "scraped_at": now.isoformat(),
            "price": product.current_price,
            "currency": product.currency,
            "available": product.available,
            "on_sale": product.on_sale,
        })

    def get_price_history(self, product_id: str, limit: int = 30) -> list[PriceRecord]:
        response = self._history.query(
            KeyConditionExpression=Key("product_id").eq(product_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        records = []
        for item in response.get("Items", []):
            records.append(PriceRecord(
                price=item["price"],
                currency=item.get("currency", "GBP"),
                available=item.get("available", True),
                on_sale=item.get("on_sale", False),
                scraped_at=datetime.fromisoformat(item["scraped_at"]),
            ))
        return records
