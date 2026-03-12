"""Manual trigger endpoint for scraping (also used by the scheduled Lambda)."""
import logging

from fastapi import APIRouter, BackgroundTasks

from app.scrapers import run_all_scrapers
from app.services import ProductStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/", status_code=202)
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Kick off a scrape in the background and return immediately."""
    background_tasks.add_task(_do_scrape)
    return {"status": "scraping started"}


@router.post("/sync", status_code=200)
async def trigger_scrape_sync():
    """Run scrape synchronously — useful for the scheduled Lambda."""
    result = await _do_scrape()
    return result


async def _do_scrape() -> dict:
    store = ProductStore()
    products = await run_all_scrapers()
    updated = [store.upsert_product(p) for p in products]
    logger.info("Scrape complete: %d products processed", len(updated))
    return {"products_processed": len(updated)}
