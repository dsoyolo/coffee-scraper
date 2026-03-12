from fastapi import APIRouter

from .products import router as products_router
from .scrape import router as scrape_router

api_router = APIRouter()
api_router.include_router(products_router)
api_router.include_router(scrape_router)

__all__ = ["api_router"]
