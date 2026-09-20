import json
import re
import logging
from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Upgrade-Insecure-Requests": "1",
}


class ScraperError(Exception):
    pass


def extract_price_from_text(text: str) -> Optional[float]:
    """Extract floating point price from messy string (e.g. '₹30,999.00' -> 30999.0)."""
    if not text:
        return None
    cleaned = text.replace(",", "").strip()
    match = re.search(r"(\d+(\.\d{1,2})?)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


async def scrape_product(url: str) -> Dict[str, Any]:
    """
    Scrapes product details from a given URL.
    Supports built-in mock store, Amazon, Flipkart, JSON-LD structured data, OpenGraph tags, and fallback HTML CSS selectors.
    """
    # Check for built-in mock store SKU
    from backend.app.mock_store.routes import MOCK_PRODUCTS
    mock_match = re.search(r"/mock-store/product/([^/?#]+)", url)
    if mock_match:
        sku = mock_match.group(1)
        if sku in MOCK_PRODUCTS:
            item = MOCK_PRODUCTS[sku]
            return {
                "title": item["title"],
                "price": float(item["price"]),
                "currency": item.get("currency", "INR"),
                "image_url": item.get("image_url"),
                "in_stock": True
            }

    try:
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise ScraperError(f"HTTP request returned status {response.status_code}")
            html_content = response.text
    except httpx.RequestError as e:
        logger.error(f"Network error while scraping {url}: {e}")
        raise ScraperError(f"Failed to fetch product page: {str(e)}")

    if "validatecaptcha" in html_content.lower() or "robot check" in html_content.lower():
        raise ScraperError(
            "Amazon temporarily challenged this request with a Bot Check (CAPTCHA). "
            "Please try again in a few seconds."
        )

    soup = BeautifulSoup(html_content, "html.parser")

    title: Optional[str] = None
    price: Optional[float] = None
    currency: str = "INR" if ("amazon.in" in url or "flipkart.com" in url or "₹" in html_content) else "USD"
    image_url: Optional[str] = None
    in_stock: bool = True

    # 1. Check for JSON-LD Structured Data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                candidates = [data]
                if "@graph" in data and isinstance(data["@graph"], list):
                    candidates.extend(data["@graph"])
            else:
                candidates = []

            for item in candidates:
                if not isinstance(item, dict):
                    continue
                type_val = item.get("@type", "")
                if type_val in ["Product", "IndividualProduct"]:
                    if not title and "name" in item:
                        title = item["name"]
                    if not image_url and "image" in item:
                        img = item["image"]
                        image_url = img if isinstance(img, str) else (img[0] if isinstance(img, list) and img else None)
                    
                    offers = item.get("offers")
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    if isinstance(offers, dict):
                        raw_p = offers.get("price")
                        if raw_p is not None:
                            price = extract_price_from_text(str(raw_p))
                        if "priceCurrency" in offers:
                            currency = offers["priceCurrency"]
                        if "availability" in offers:
                            in_stock = "InStock" in str(offers["availability"])
                    break
        except Exception as json_err:
            logger.debug(f"JSON-LD parse error: {json_err}")
            continue

    # 2. Check OpenGraph and Meta tags
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

    if not image_url:
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            image_url = og_img["content"].strip()
        # Amazon image fallback
        if not image_url:
            amz_img = soup.find("img", id="landingImage") or soup.find("img", id="imgBlkFront")
            if amz_img:
                image_url = amz_img.get("src") or amz_img.get("data-old-hires")

    if price is None:
        og_price = (
            soup.find("meta", property="product:price:amount") or
            soup.find("meta", property="og:price:amount") or
            soup.find("meta", attrs={"name": "twitter:data1"})
        )
        if og_price and og_price.get("content"):
            price = extract_price_from_text(og_price["content"])

    # 3. Dedicated Amazon & Flipkart Selectors
    if price is None:
        amz_price_elem = (
            soup.select_one(".a-price .a-offscreen") or
            soup.select_one("span.priceToPay span.a-price-whole") or
            soup.select_one("#corePrice_feature_div .a-offscreen") or
            soup.select_one("#corePriceDisplay_desktop_feature_div .a-offscreen") or
            soup.select_one("#priceblock_ourprice") or
            soup.select_one("#priceblock_dealprice") or
            soup.select_one("div._30jeq3._16Jk6d") or # Flipkart
            soup.select_one("div.Nx9bqj.CxhGGd")     # Flipkart new
        )
        if amz_price_elem:
            price = extract_price_from_text(amz_price_elem.get_text())

    # 4. Fallback CSS Selectors for generic store layouts
    if not title:
        title_elem = (
            soup.find(id="productTitle") or
            soup.find("h1") or
            soup.find(id=re.compile(r"productTitle|product-title|title", re.I)) or
            soup.find(class_=re.compile(r"product-title|product_title|item-name", re.I))
        )
        if title_elem:
            title = title_elem.get_text().strip()

    if price is None:
        price_elem = (
            soup.find(id=re.compile(r"priceblock_ourprice|priceblock_dealprice|price-val|current-price", re.I)) or
            soup.find(class_=re.compile(r"product-price|price-current|offer-price|a-price-whole", re.I)) or
            soup.find(attrs={"data-price": True}) or
            soup.find(itemprop="price")
        )
        if price_elem:
            if price_elem.get("data-price"):
                price = extract_price_from_text(price_elem["data-price"])
            else:
                price = extract_price_from_text(price_elem.get_text())

    # Fallback title if all else fails
    if not title and soup.title:
        title = soup.title.get_text().strip()

    if not title:
        title = "Tracked Product"

    if price is None:
        raise ScraperError(f"Could not extract price from {url}. Ensure the page has standard price tags or JSON-LD.")

    return {
        "title": title,
        "price": price,
        "currency": currency or "INR",
        "image_url": image_url,
        "in_stock": in_stock
    }
