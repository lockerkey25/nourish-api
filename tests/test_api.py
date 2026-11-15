import io

from PIL import Image


def _jpeg(color: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, format="JPEG")
    return buf.getvalue()


def _first_meal(client) -> dict:
    resident = client.get("/api/residents").json()[0]
    meals = client.get(f"/api/residents/{resident['id']}/meals").json()
    assert meals, "seed data should create today's meals"
    return meals[0]


def test_health_reports_mock_mode(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["mode"] == "mock"


def test_residents_seeded(client):
    r = client.get("/api/residents")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_unknown_resident_is_404(client):
    assert client.get("/api/residents/999999/meals").status_code == 404


def test_menu_items_have_safety_for_resident(client):
    resident = client.get("/api/residents").json()[0]
    items = client.get("/api/menu-items", params={"resident_id": resident["id"]}).json()
    assert items
    assert all(it["safety"] in {"safe", "warning", "block"} for it in items)


def test_weight_out_of_range_rejected(client):
    resident = client.get("/api/residents").json()[0]
    r = client.post(f"/api/residents/{resident['id']}/weight", json={"weight_kg": 5})
    assert r.status_code == 422


def test_analyze_and_confirm_meal_in_mock_mode(client):
    meal = _first_meal(client)
    files = {
        "before": ("before.jpg", _jpeg("white"), "image/jpeg"),
        "after": ("after.jpg", _jpeg("gray"), "image/jpeg"),
    }
    r = client.post(f"/api/meals/{meal['id']}/analyze", files=files)
    assert r.status_code == 200, r.text
    analysis = r.json()

    items = [{"menu_item_id": it["id"], "percent_eaten": 50} for it in meal["items"]]
    r = client.post(
        f"/api/meals/{meal['id']}/confirm",
        json={"analysis_id": analysis["analysis_id"], "items": items},
    )
    assert r.status_code == 200, r.text
    assert 0 <= r.json()["overall_percent_eaten"] <= 100


def test_invalid_image_rejected(client):
    meal = _first_meal(client)
    files = {"before": ("x.jpg", b"not an image", "image/jpeg")}
    assert client.post(f"/api/meals/{meal['id']}/check-before", files=files).status_code == 400
