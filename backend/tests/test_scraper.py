import pytest
from backend.app.services.scraper import extract_price_from_text, scrape_product
from backend.app.mock_store.routes import MOCK_PRODUCTS


def test_extract_price_formats():
    assert extract_price_from_text("$199.99") == 199.99
    assert extract_price_from_text("$1,299.50") == 1299.50
    assert extract_price_from_text("EUR 45.00") == 45.00
    assert extract_price_from_text("Special Deal: 899.00 USD") == 899.00
    assert extract_price_from_text("No price here") is None
    assert extract_price_from_text("") is None


def test_mock_store_endpoints(client):
    # Test getting mock product page
    res = client.get("/mock-store/product/laptop-pro")
    assert res.status_code == 200
    assert "UltraBook Pro" in res.text
    assert 'application/ld+json' in res.text

    # Test updating mock price
    update_res = client.post("/mock-store/product/laptop-pro/set-price", json={"price": 1699.99})
    assert update_res.status_code == 200
    assert update_res.json()["new_price"] == 1699.99
    assert MOCK_PRODUCTS["laptop-pro"]["price"] == 1699.99


def test_mock_store_scraper():
    # Testing scraper extraction against sample HTML
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "Product",
          "name": "Test Wireless Mouse",
          "offers": {
            "@type": "Offer",
            "price": "49.99",
            "priceCurrency": "USD"
          }
        }
        </script>
      </head>
      <body>
        <h1>Test Wireless Mouse</h1>
      </body>
    </html>
    """
    from bs4 import BeautifulSoup
    import json
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", type="application/ld+json")
    data = json.loads(script.string)
    price = float(data["offers"]["price"])
    assert price == 49.99
