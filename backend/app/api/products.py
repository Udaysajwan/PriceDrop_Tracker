from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.repositories.product_repo import product_repo
from backend.app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductSummary
)
from backend.app.schemas.price_history import PriceHistoryResponse
from backend.app.api.deps import get_current_user
from backend.app.services.scraper import scrape_product, ScraperError
from backend.app.services.notifier import send_price_drop_alert

router = APIRouter(prefix="/products", tags=["Products"])


def _format_product_response(product: Dict[str, Any]) -> ProductResponse:
    target_price = float(product.get("target_price", 0.0))
    current_price = float(product.get("current_price")) if product.get("current_price") is not None else None
    
    price_dropped = False
    pct_from_target = None
    if current_price is not None:
        price_dropped = current_price <= target_price
        if target_price > 0:
            pct_from_target = round(
                ((current_price - target_price) / target_price) * 100,
                2
            )

    return ProductResponse(
        id=str(product.get("id")),
        user_id=str(product.get("user_id")),
        title=product.get("title", "Tracked Product"),
        url=product.get("url", ""),
        target_price=target_price,
        current_price=current_price,
        currency=product.get("currency", "INR"),
        image_url=product.get("image_url"),
        in_stock=product.get("in_stock", True),
        last_scraped_at=product.get("last_scraped_at"),
        created_at=product.get("created_at"),
        updated_at=product.get("updated_at"),
        price_dropped=price_dropped,
        percent_change_from_target=pct_from_target
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Track a new product in Firestore. Immediately scrapes product page,
    creates document, and seeds initial history subcollection document.
    """
    try:
        scraped = await scrape_product(str(product_in.url))
    except ScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not scrape product: {str(e)}"
        )

    title = product_in.title or scraped["title"]
    product = product_repo.create(
        user_id=current_user["id"],
        title=title,
        url=str(product_in.url),
        target_price=product_in.target_price,
        current_price=scraped["price"],
        currency=scraped.get("currency", "INR"),
        image_url=scraped.get("image_url"),
        in_stock=scraped.get("in_stock", True)
    )

    # Check alert trigger
    if product["current_price"] <= product["target_price"]:
        product_repo.create_alert(
            product_id=product["id"],
            user_id=current_user["id"],
            product_title=product["title"],
            product_url=product["url"],
            target_price=product["target_price"],
            current_price=product["current_price"],
            currency=product.get("currency", "INR"),
        )
        send_price_drop_alert(
            user_email=current_user.get("email", ""),
            product_title=product["title"],
            product_url=product["url"],
            target_price=product["target_price"],
            current_price=product["current_price"],
            currency=product.get("currency", "INR")
        )

    return _format_product_response(product)


@router.get("", response_model=List[ProductResponse])
def list_products(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all tracked products for the current authenticated user from Firestore."""
    products = product_repo.list_by_user(current_user["id"])
    return [_format_product_response(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve details for a single tracked product."""
    product = product_repo.get_by_id(product_id, user_id=current_user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _format_product_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update target price or title for a product in Firestore."""
    product = product_repo.get_by_id(product_id, user_id=current_user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = {}
    if product_in.target_price is not None:
        updates["target_price"] = product_in.target_price
    if product_in.title is not None:
        updates["title"] = product_in.title

    updated = product_repo.update(product_id, updates)
    return _format_product_response(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a tracked product and its history subcollection."""
    product = product_repo.get_by_id(product_id, user_id=current_user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_repo.delete(product_id)
    return None


@router.get("/{product_id}/history", response_model=List[PriceHistoryResponse])
def get_product_price_history(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the chronological price history points from subcollection for Chart.js rendering."""
    product = product_repo.get_by_id(product_id, user_id=current_user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    history = product_repo.get_price_history(product_id)
    return history


@router.get("/{product_id}/summary", response_model=ProductSummary)
def get_product_summary(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get aggregated price statistics (min, max, average, overall change percentage)
    for a given product.
    """
    product = product_repo.get_by_id(product_id, user_id=current_user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    summary = product_repo.get_summary(product_id)
    return summary


@router.post("/{product_id}/check", response_model=ProductResponse)
async def manual_price_check(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually trigger an immediate price scrape and update for a product."""
    product = product_repo.get_by_id(product_id, user_id=current_user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        scraped = await scrape_product(product["url"])
    except ScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Live scrape failed: {str(e)}"
        )

    new_price = scraped["price"]
    product_repo.add_price_history(product_id, new_price)
    updated_product = product_repo.get_by_id(product_id)

    # Check for price drop alert
    target_price = float(product.get("target_price", 0.0))
    if new_price <= target_price:
        product_repo.create_alert(
            product_id=product_id,
            user_id=current_user["id"],
            product_title=product["title"],
            product_url=product["url"],
            target_price=target_price,
            current_price=new_price,
            currency=product.get("currency", "INR")
        )
        send_price_drop_alert(
            user_email=current_user.get("email", ""),
            product_title=product["title"],
            product_url=product["url"],
            target_price=target_price,
            current_price=new_price,
            currency=product.get("currency", "INR")
        )
    else:
        product_repo.resolve_active_alert(product_id, user_id=current_user["id"], current_price=new_price)

    return _format_product_response(updated_product)
