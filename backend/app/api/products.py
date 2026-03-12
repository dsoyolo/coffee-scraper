from fastapi import APIRouter, HTTPException

from app.models import DigestSummary, PriceRecord, Product
from app.services import ProductStore, build_digest

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[Product])
def list_products():
    store = ProductStore()
    return store.get_all_products()


@router.get("/digest", response_model=DigestSummary)
def get_digest():
    store = ProductStore()
    return build_digest(store)


@router.get("/{product_id:path}", response_model=Product)
def get_product(product_id: str):
    store = ProductStore()
    product = store.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id:path}/history", response_model=list[PriceRecord])
def get_price_history(product_id: str, limit: int = 30):
    store = ProductStore()
    return store.get_price_history(product_id, limit=limit)
