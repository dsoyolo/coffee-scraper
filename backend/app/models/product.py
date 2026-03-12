from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class Currency(str, Enum):
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"


class PriceRecord(BaseModel):
    """A single price snapshot stored in history."""
    price: Decimal
    currency: Currency
    available: bool
    on_sale: bool
    scraped_at: datetime

    model_config = {"use_enum_values": True}


class Product(BaseModel):
    """A coffee product from a supplier."""
    product_id: str           # supplier_slug#product_slug
    supplier: str
    name: str
    url: str
    image_url: Optional[str] = None
    current_price: Decimal
    previous_price: Optional[Decimal] = None
    currency: Currency = Currency.GBP
    available: bool = True
    on_sale: bool = False
    price_drop: bool = False
    price_drop_pct: Optional[float] = None
    last_updated: datetime = datetime.utcnow()

    model_config = {"use_enum_values": True}

    @field_validator("current_price", "previous_price", mode="before")
    @classmethod
    def parse_price(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            cleaned = v.replace("£", "").replace("$", "").replace("€", "").replace(",", "").strip()
            return Decimal(cleaned)
        return Decimal(str(v))


class DigestSummary(BaseModel):
    """Daily digest highlighting availability, sales and price drops."""
    generated_at: datetime
    total_products: int
    available_count: int
    unavailable_count: int
    on_sale_count: int
    price_drops: list[Product]
    new_sales: list[Product]
    back_in_stock: list[Product]
    out_of_stock: list[Product]
    all_products: list[Product]
