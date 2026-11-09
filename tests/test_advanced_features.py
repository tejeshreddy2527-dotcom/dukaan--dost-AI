import io
import pytest
import database.db as db
from config import Config

@pytest.fixture()
def test_client(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_advanced.db")
    monkeypatch.setenv("DATABASE_PATH", test_db)
    Config.DATABASE_PATH = test_db

    db.init_db()
    from app import app as flask_app
    flask_app.config.update(TESTING=True)
    return flask_app.test_client()

def test_all_pages_load_200(test_client):
    pages = ["/", "/dashboard", "/inventory", "/sales", "/assistant", "/upload"]
    for page in pages:
        res = test_client.get(page)
        assert res.status_code == 200, f"Page {page} failed to load with 200"

def test_greeting_endpoint_multilingual(test_client):
    # Telugu greeting
    res_te = test_client.get("/api/greeting?language=te-IN")
    assert res_te.status_code == 200
    assert "నమస్కారం" in res_te.json["greeting_text"]

    # English greeting
    res_en = test_client.get("/api/greeting?language=en-IN")
    assert res_en.status_code == 200
    assert "Hello" in res_en.json["greeting_text"]

    # Hindi greeting
    res_hi = test_client.get("/api/greeting?language=hi-IN")
    assert res_hi.status_code == 200
    assert "नमस्ते" in res_hi.json["greeting_text"]

def test_telugu_voice_queries(test_client):
    # Telugu sales question: ఈరోజు మొత్తం ఎంత అమ్మకాలు జరిగాయి?
    res_sales = test_client.post("/api/command", json={"text": "ఈరోజు మొత్తం ఎంత అమ్మకాలు జరిగాయి?"})
    assert res_sales.status_code == 200
    assert "ఈరోజు" in res_sales.json["reply"]
    assert "₹" in res_sales.json["reply"]

    # Telugu stock query: బియ్యం ఎంత ఉంది?
    res_stock = test_client.post("/api/command", json={"text": "బియ్యం ఎంత ఉంది?"})
    assert res_stock.status_code == 200
    assert "Rice" in res_stock.json["reply"] or "బియ్యం" in res_stock.json["reply"]

    # Telugu low stock query: స్టాక్ తక్కువగా ఉన్న వస్తువులు ఏవి?
    res_low = test_client.post("/api/command", json={"text": "స్టాక్ తక్కువగా ఉన్న వస్తువులు ఏవి?"})
    assert res_low.status_code == 200

def test_english_voice_queries(test_client):
    # Today's sales query
    res_sales = test_client.post("/api/command", json={"text": "What is today's revenue?"})
    assert res_sales.status_code == 200
    assert "Today's sales" in res_sales.json["reply"]
    assert "₹" in res_sales.json["reply"]

    # How much rice is left?
    res_rice = test_client.post("/api/command", json={"text": "How much rice is left?"})
    assert res_rice.status_code == 200
    assert "Rice" in res_rice.json["reply"]

    # Low stock
    res_low = test_client.post("/api/command", json={"text": "Show low-stock products"})
    assert res_low.status_code == 200

def test_accurate_dashboard_analytics(test_client):
    res = test_client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json

    stats = data["stats"]
    assert "revenue" in stats
    assert "transactions" in stats
    assert "profit" in stats
    assert "units_sold" in stats
    assert "weekly_revenue" in stats
    assert "monthly_revenue" in stats

    # Distinction between sales revenue and gross profit
    assert stats["revenue"] >= stats["profit"], "Revenue must be distinct and >= profit"

    # Charts and lists
    assert "daily_trend" in data
    assert len(data["daily_trend"]) > 0
    assert "category_dist" in data
    assert "best_sellers" in data

def test_csv_upload_and_confirmation_flow(test_client):
    # 1. Upload CSV to preview endpoint
    csv_content = """Product Name,Category,Quantity,Unit,Selling Price,Cost Price,Low Stock Alert
Sona Masoori Super,Staples,50,kg,62.0,52.0,10
Sunflower Fresh Oil,Oils & Ghee,15,L,160.0,140.0,4
"""
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))

    upload_res = test_client.post(
        "/api/upload",
        data={"file": (file_bytes, "supplier_invoice.csv")},
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json
    assert upload_data["success"] is True
    assert upload_data["item_count"] == 2
    assert upload_data["items"][0]["name"] == "Sona Masoori Super"

    # Verify that products are NOT automatically inserted before confirmation
    check_before = test_client.get("/api/products").json["products"]
    names_before = [p["name"] for p in check_before]
    assert "Sona Masoori Super" not in names_before

    # 2. Confirm and save to database
    confirm_res = test_client.post(
        "/api/upload/confirm",
        json={"items": upload_data["items"]}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json["saved_count"] == 2

    # Verify that products ARE now in the database
    check_after = test_client.get("/api/products").json["products"]
    names_after = [p["name"] for p in check_after]
    assert "Sona Masoori Super" in names_after

def test_product_crud_lifecycle(test_client):
    # Create product
    new_prod = {
        "name": "Tata Salt Pro",
        "category": "Staples",
        "quantity": 30,
        "unit": "pkt",
        "price": 28.0,
        "cost_price": 22.0,
        "low_stock_threshold": 5
    }
    create_res = test_client.post("/api/products", json=new_prod)
    assert create_res.status_code == 200
    prod_id = create_res.json["product"]["id"]

    # Update product
    update_res = test_client.put(f"/api/products/{prod_id}", json={
        "name": "Tata Salt Pro (Iodized)",
        "category": "Staples",
        "quantity": 35,
        "unit": "pkt",
        "price": 30.0,
        "cost_price": 23.0,
        "low_stock_threshold": 6
    })
    assert update_res.status_code == 200
    assert update_res.json["product"]["name"] == "Tata Salt Pro (Iodized)"
    assert update_res.json["product"]["price"] == 30.0

    # Delete product
    del_res = test_client.delete(f"/api/products/{prod_id}")
    assert del_res.status_code == 200
