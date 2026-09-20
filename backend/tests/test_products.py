from unittest.mock import patch, AsyncMock

from backend.app.repositories.product_repo import product_repo


@patch("backend.app.api.products.scrape_product", new_callable=AsyncMock)
def test_create_and_list_product(mock_scrape, client, auth_headers):
    mock_scrape.return_value = {
        "title": "Test Gaming Monitor 27-inch",
        "price": 349.99,
        "currency": "USD",
        "image_url": "https://example.com/monitor.jpg",
        "in_stock": True
    }

    # 1. Create tracked product
    response = client.post(
        "/products",
        json={"url": "https://example.com/monitor", "target_price": 300.00},
        headers=auth_headers
    )
    assert response.status_code == 201
    prod = response.json()
    assert prod["title"] == "Test Gaming Monitor 27-inch"
    assert prod["current_price"] == 349.99
    assert prod["target_price"] == 300.00
    assert prod["price_dropped"] is False
    product_id = prod["id"]

    # 2. List products
    list_res = client.get("/products", headers=auth_headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == product_id

    # 3. Get product history
    hist_res = client.get(f"/products/{product_id}/history", headers=auth_headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 1
    assert history[0]["price"] == 349.99

    # 4. Get product summary
    sum_res = client.get(f"/products/{product_id}/summary", headers=auth_headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["lowest_price"] == 349.99
    assert summary["highest_price"] == 349.99
    assert summary["total_checks"] == 1


@patch("backend.app.api.products.scrape_product", new_callable=AsyncMock)
def test_price_drop_detection(mock_scrape, client, auth_headers):
    mock_scrape.return_value = {
        "title": "Smart Speaker",
        "price": 79.99,
        "currency": "USD",
        "image_url": "https://example.com/speaker.jpg",
        "in_stock": True
    }

    # Create product with target higher than current price (price already dropped)
    res = client.post(
        "/products",
        json={"url": "https://example.com/speaker", "target_price": 99.00},
        headers=auth_headers
    )
    assert res.status_code == 201
    prod = res.json()
    assert prod["price_dropped"] is True

    # Check summary calculates savings
    sum_res = client.get(f"/products/{prod['id']}/summary", headers=auth_headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["price_dropped"] is True
    assert summary["savings_amount"] == 19.01


@patch("backend.app.api.products.scrape_product", new_callable=AsyncMock)
def test_manual_check_and_delete(mock_scrape, client, auth_headers):
    mock_scrape.return_value = {
        "title": "Coffee Maker",
        "price": 120.00,
        "currency": "USD",
        "image_url": None,
        "in_stock": True
    }

    create_res = client.post(
        "/products",
        json={"url": "https://example.com/coffee", "target_price": 100.00},
        headers=auth_headers
    )
    product_id = create_res.json()["id"]

    # Now mock a price drop to $95 on manual check
    mock_scrape.return_value = {
        "title": "Coffee Maker",
        "price": 95.00,
        "currency": "USD",
        "image_url": None,
        "in_stock": True
    }
    check_res = client.post(f"/products/{product_id}/check", headers=auth_headers)
    assert check_res.status_code == 200
    updated_prod = check_res.json()
    assert updated_prod["current_price"] == 95.00
    assert updated_prod["price_dropped"] is True

    # Verify history now has 2 entries
    hist_res = client.get(f"/products/{product_id}/history", headers=auth_headers)
    assert len(hist_res.json()) == 2

    # Delete product
    del_res = client.delete(f"/products/{product_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/products/{product_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_alert_lifecycle_deduplicates_target_hits():
    product = product_repo.create(
        user_id="user-123",
        title="Alert Test Lamp",
        url="https://example.com/lamp",
        target_price=150.00,
        current_price=120.00,
        currency="INR",
        image_url="https://example.com/lamp.jpg",
        in_stock=True,
    )

    first_alert = product_repo.create_alert(
        product_id=product["id"],
        user_id="user-123",
        product_title="Alert Test Lamp",
        product_url="https://example.com/lamp",
        target_price=150.00,
        current_price=120.00,
        currency="INR",
    )
    second_alert = product_repo.create_alert(
        product_id=product["id"],
        user_id="user-123",
        product_title="Alert Test Lamp",
        product_url="https://example.com/lamp",
        target_price=150.00,
        current_price=120.00,
        currency="INR",
    )

    assert first_alert["id"] == second_alert["id"]
    assert len(product_repo.list_alerts_for_product(product["id"])) == 1
    assert product_repo.get_active_alert_for_product(product["id"])["status"] == "active"

    resolved = product_repo.resolve_active_alert(product["id"], current_price=140.00)
    assert resolved["status"] == "resolved"
    assert product_repo.get_active_alert_for_product(product["id"]) is None


def test_alert_lifecycle_works_with_price_recovery():
    product = product_repo.create(
        user_id="user-456",
        title="Recovery Watch",
        url="https://example.com/recovery-watch",
        target_price=200.00,
        current_price=180.00,
        currency="INR",
        image_url=None,
        in_stock=True,
    )

    first_alert = product_repo.create_alert(
        product_id=product["id"],
        user_id="user-456",
        product_title="Recovery Watch",
        product_url="https://example.com/recovery-watch",
        target_price=200.00,
        current_price=180.00,
        currency="INR",
    )
    assert first_alert["status"] == "active"

    product_repo.resolve_active_alert(product["id"], current_price=210.00)
    product_repo.add_price_history(product["id"], 180.00)

    reopened = product_repo.create_alert(
        product_id=product["id"],
        user_id="user-456",
        product_title="Recovery Watch",
        product_url="https://example.com/recovery-watch",
        target_price=200.00,
        current_price=180.00,
        currency="INR",
    )

    assert reopened["status"] == "active"
    assert product_repo.get_active_alert_for_product(product["id"])["id"] == reopened["id"]


def test_alerts_endpoints_list_and_dismiss(client, auth_headers, test_user):
    product = product_repo.create(
        user_id=test_user["id"],
        title="Alert Center Lamp",
        url="https://example.com/lamp",
        target_price=150.00,
        current_price=120.00,
        currency="INR",
        image_url="https://example.com/lamp.jpg",
        in_stock=True,
    )

    alert = product_repo.create_alert(
        product_id=product["id"],
        user_id=test_user["id"],
        product_title="Alert Center Lamp",
        product_url="https://example.com/lamp",
        target_price=150.00,
        current_price=120.00,
        currency="INR",
    )

    list_res = client.get("/alerts", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(item["id"] == alert["id"] for item in list_res.json())

    active_res = client.get("/alerts/active", headers=auth_headers)
    assert active_res.status_code == 200
    assert any(item["id"] == alert["id"] for item in active_res.json())

    dismiss_res = client.patch(f"/alerts/{alert['id']}", json={"status": "dismissed"}, headers=auth_headers)
    assert dismiss_res.status_code == 200
    assert dismiss_res.json()["status"] == "dismissed"
