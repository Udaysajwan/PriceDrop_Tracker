import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.config import settings
from backend.app.repositories.product_repo import product_repo
from backend.app.repositories.user_repo import user_repo
from backend.app.services.scraper import scrape_product
from backend.app.services.notifier import send_price_drop_alert

logger = logging.getLogger("price_tracker.scheduler")

scheduler = BackgroundScheduler()


def check_product_price(product_id: str):
    """Checks and updates the price for a single product in Firestore."""
    try:
        product = product_repo.get_by_id(str(product_id))
        if not product:
            return

        # Scrape product details
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraped_data = loop.run_until_complete(scrape_product(product["url"]))
            loop.close()
        except Exception as e:
            logger.error(f"Error scraping product {product_id} ({product['url']}): {e}")
            return

        new_price = scraped_data["price"]
        product_repo.add_price_history(product_id, new_price)
        logger.info(f"Updated product {product_id} ('{product['title']}') price to {new_price}")

        # Check for price drop alert
        target_price = float(product.get("target_price", 0.0))
        if new_price <= target_price:
            user = user_repo.get_by_id(product.get("user_id", ""))
            user_email = user.get("email") if user else "unknown@user"
            product_repo.create_alert(
                product_id=product_id,
                user_id=product.get("user_id", ""),
                product_title=product.get("title", "Product"),
                product_url=product.get("url", ""),
                target_price=target_price,
                current_price=new_price,
                currency=product.get("currency", "INR")
            )
            send_price_drop_alert(
                user_email=user_email,
                product_title=product.get("title", "Product"),
                product_url=product.get("url", ""),
                target_price=target_price,
                current_price=new_price,
                currency=product.get("currency", "INR")
            )
        else:
            product_repo.resolve_active_alert(product_id, user_id=product.get("user_id", ""), current_price=new_price)
    except Exception as exc:
        logger.error(f"Unexpected error checking product {product_id}: {exc}")


def check_all_products():
    """Runs a price check job across all registered Firestore products."""
    logger.info("Executing scheduled check for all tracked products...")
    try:
        products = product_repo.get_all_active_products()
        for p in products:
            check_product_price(p["id"])
    except Exception as e:
        logger.error(f"Error in scheduled check_all_products: {e}")


def start_scheduler():
    """Starts the background scheduler if enabled."""
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled in configuration.")
        return

    if not scheduler.running:
        interval = settings.DEFAULT_SCRAPE_INTERVAL_MINUTES
        scheduler.add_job(
            check_all_products,
            trigger=IntervalTrigger(minutes=interval),
            id="periodic_product_check",
            name="Periodic Product Price Scrape",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"APScheduler started. Product price check interval: {interval} minutes.")


def stop_scheduler():
    """Stops the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
