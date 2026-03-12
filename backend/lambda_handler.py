"""AWS Lambda entry point.

The API Lambda serves the FastAPI app via Mangum.
The scraper Lambda is triggered by EventBridge on a schedule.
"""
import asyncio
import json
import logging
import os

from mangum import Mangum

from app.main import app
from app.scrapers import run_all_scrapers
from app.services import ProductStore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# FastAPI handler (API Gateway events)
api_handler = Mangum(app, lifespan="off")


def handler(event: dict, context) -> dict:
    """Route Lambda events to the correct handler."""
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    if source == "aws.events" or detail_type == "Scheduled Event":
        return _scraper_handler(event, context)

    return api_handler(event, context)


def _scraper_handler(event: dict, context) -> dict:
    """Run all scrapers and persist results to DynamoDB."""
    logger.info("Scraper Lambda triggered by EventBridge")
    store = ProductStore()

    products = asyncio.get_event_loop().run_until_complete(run_all_scrapers())
    updated = [store.upsert_product(p) for p in products]

    logger.info("Scrape complete: %d products processed", len(updated))
    return {
        "statusCode": 200,
        "body": json.dumps({"products_processed": len(updated)}),
    }
