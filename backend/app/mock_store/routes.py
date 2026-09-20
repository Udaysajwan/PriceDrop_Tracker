from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict

router = APIRouter(prefix="/mock-store", tags=["Mock Store"])

# In-memory store state for demo products (in INR ₹)
MOCK_PRODUCTS: Dict[str, Dict] = {
    "laptop-pro": {
        "title": "UltraBook Pro 16-inch M3 Chip (1TB SSD, 32GB RAM)",
        "price": 89999.00,
        "currency": "INR",
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop",
        "description": "High-performance laptop with 16-inch Liquid Retina display and 22-hour battery life."
    },
    "sony-headphones": {
        "title": "AcousticNoise Pro Wireless ANC Headphones",
        "price": 19999.00,
        "currency": "INR",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop",
        "description": "Industry-leading noise canceling with dual noise sensor technology."
    },
    "mechanical-keyboard": {
        "title": "Custom RGB Mechanical Gaming Keyboard (Hot-swappable)",
        "price": 6499.00,
        "currency": "INR",
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop",
        "description": "Gasket-mounted mechanical keyboard with lubed linear switches."
    },
    "smart-watch": {
        "title": "Apex Pulse Smart Health & GPS Watch",
        "price": 12999.00,
        "currency": "INR",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop",
        "description": "Advanced health sensors, heart rate tracking, and 7-day battery life."
    }
}


class UpdatePriceRequest(BaseModel):
    price: float


@router.get("/product/{sku}", response_class=HTMLResponse)
def get_mock_product_page(sku: str):
    """
    Renders an HTML product page with standard Schema.org JSON-LD and OpenGraph tags,
    allowing the scraper to parse it realistically.
    """
    product = MOCK_PRODUCTS.get(sku)
    if not product:
        raise HTTPException(status_code=404, detail=f"Mock product '{sku}' not found")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{product['title']} - MockStore</title>
    <meta property="og:title" content="{product['title']}">
    <meta property="og:price:amount" content="{product['price']}">
    <meta property="og:price:currency" content="{product['currency']}">
    <meta property="og:image" content="{product['image_url']}">
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "{product['title']}",
      "image": ["{product['image_url']}"],
      "description": "{product['description']}",
      "sku": "{sku}",
      "offers": {{
        "@type": "Offer",
        "price": "{product['price']}",
        "priceCurrency": "{product['currency']}",
        "availability": "https://schema.org/InStock"
      }}
    }}
    </script>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #f8fafc; color: #1e293b; padding: 2rem; display: flex; justify-content: center; }}
        .card {{ background: white; border-radius: 12px; padding: 2rem; max-width: 500px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        img {{ width: 100%; height: 260px; object-fit: cover; border-radius: 8px; }}
        .price-tag {{ font-size: 2rem; font-weight: bold; color: #16a34a; margin: 1rem 0; }}
        .badge {{ background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Official Demo Mock Store</span>
        <h1 id="productTitle">{product['title']}</h1>
        <img src="{product['image_url']}" alt="{product['title']}">
        <p>{product['description']}</p>
        <div class="price-tag" id="priceblock_ourprice">₹{product['price']:,.2f}</div>
        <p style="color: #64748b; font-size: 0.9rem;">SKU: {sku} | Availability: In Stock</p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/list")
def list_mock_products():
    """List available mock products for easy testing."""
    return MOCK_PRODUCTS


@router.post("/product/{sku}/set-price")
def set_mock_price(sku: str, body: UpdatePriceRequest):
    """
    Manually update a mock product's price.
    Use this endpoint during testing or demos to simulate a price drop!
    """
    if sku not in MOCK_PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Mock product '{sku}' not found")
    
    old_price = MOCK_PRODUCTS[sku]["price"]
    MOCK_PRODUCTS[sku]["price"] = round(body.price, 2)
    return {
        "sku": sku,
        "old_price": old_price,
        "new_price": MOCK_PRODUCTS[sku]["price"],
        "message": f"Price updated from ${old_price} to ${body.price}"
    }
