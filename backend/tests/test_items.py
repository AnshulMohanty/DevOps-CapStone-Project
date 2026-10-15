import re

import pytest


def metric_value(client, name, labels=""):
    """Read one sample from /metrics, e.g. metric_value(c, "foundit_items_resolved_total")."""
    pattern = rf"^{re.escape(name)}{re.escape(labels)} ([0-9.e+]+)$"
    match = re.search(pattern, client.get("/metrics").text, re.MULTILINE)
    return float(match.group(1)) if match else 0.0


def test_create_item(client):
    response = client.post("/api/items", json={
        "title": "Student ID card", "type": "FOUND", "category": "ID_CARD",
        "location": "Canteen", "reported_by": "Riya", "contact": "riya@campus.edu",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["status"] == "OPEN"
    assert body["resolved_at"] is None


@pytest.mark.parametrize("payload", [
    {"title": "", "type": "LOST", "location": "Lab", "reported_by": "A"},          # empty title
    {"title": "Pen", "type": "STOLEN", "location": "Lab", "reported_by": "A"},     # unknown type
    {"title": "Pen", "type": "LOST", "category": "PETS", "location": "Lab", "reported_by": "A"},
    {"title": "Pen", "type": "LOST", "reported_by": "A"},                          # no location
])
def test_create_item_rejects_bad_input(client, payload):
    assert client.post("/api/items", json=payload).status_code == 422


def test_list_is_newest_first(client, make_item):
    make_item()
    make_item()
    ids = [item["id"] for item in client.get("/api/items").json()]
    assert ids == sorted(ids, reverse=True)


def test_filter_by_type_and_category(client, make_item):
    make_item(type="FOUND", category="ELECTRONICS", title="Phone charger")
    found = client.get("/api/items", params={"type": "FOUND", "category": "ELECTRONICS"}).json()
    assert found and all(i["type"] == "FOUND" and i["category"] == "ELECTRONICS" for i in found)


def test_filter_by_status(client, make_item):
    item = make_item()
    client.post(f"/api/items/{item['id']}/resolve")
    returned = client.get("/api/items", params={"status": "RETURNED"}).json()
    assert item["id"] in [i["id"] for i in returned]
    assert all(i["status"] == "RETURNED" for i in returned)


def test_search_matches_title_and_location_case_insensitively(client, make_item):
    by_title = make_item(title="Calculus TEXTBOOK", category="BOOKS")
    by_place = make_item(title="Keys", location="Hostel Block C")
    assert [i["id"] for i in client.get("/api/items", params={"q": "textbook"}).json()] == [by_title["id"]]
    assert by_place["id"] in [i["id"] for i in client.get("/api/items", params={"q": "block c"}).json()]


def test_invalid_filter_value_is_rejected(client):
    assert client.get("/api/items", params={"type": "MISSING"}).status_code == 422


def test_get_item(client, make_item):
    item = make_item()
    assert client.get(f"/api/items/{item['id']}").json()["title"] == item["title"]


def test_get_missing_item_returns_404(client):
    assert client.get("/api/items/999999").status_code == 404


def test_update_item(client, make_item):
    item = make_item()
    response = client.put(f"/api/items/{item['id']}", json={"location": "Library desk", "status": "CLAIMED"})
    assert response.status_code == 200
    assert response.json()["location"] == "Library desk"
    assert response.json()["status"] == "CLAIMED"
    assert response.json()["title"] == item["title"]  # untouched fields stay


def test_update_to_returned_sets_resolved_at_and_reopen_clears_it(client, make_item):
    item = make_item()
    returned = client.put(f"/api/items/{item['id']}", json={"status": "RETURNED"}).json()
    assert returned["resolved_at"] is not None
    reopened = client.put(f"/api/items/{item['id']}", json={"status": "OPEN"}).json()
    assert reopened["resolved_at"] is None


def test_resolve_marks_returned_once(client, make_item):
    item = make_item()
    response = client.post(f"/api/items/{item['id']}/resolve")
    assert response.status_code == 200
    assert response.json()["status"] == "RETURNED"
    assert response.json()["resolved_at"] is not None
    assert client.post(f"/api/items/{item['id']}/resolve").status_code == 409


def test_delete_item(client, make_item):
    item = make_item()
    assert client.delete(f"/api/items/{item['id']}").status_code == 204
    assert client.get(f"/api/items/{item['id']}").status_code == 404
    assert client.delete(f"/api/items/{item['id']}").status_code == 404


def test_stats_count_by_type_status_and_category(client, make_item):
    before = client.get("/api/items/stats").json()
    make_item(type="LOST", category="BOTTLE")
    make_item(type="FOUND", category="BOTTLE")
    resolved = make_item(type="FOUND", category="BOTTLE")
    client.post(f"/api/items/{resolved['id']}/resolve")
    after = client.get("/api/items/stats").json()
    assert after["total"] == before["total"] + 3
    assert after["open_lost"] == before["open_lost"] + 1
    assert after["open_found"] == before["open_found"] + 1
    assert after["returned"] == before["returned"] + 1
    assert after["by_category"]["BOTTLE"] == before["by_category"].get("BOTTLE", 0) + 3


def test_business_metrics_count_reports_and_resolutions(client, make_item):
    reported = metric_value(client, "foundit_items_reported_total", '{type="FOUND"}')
    resolved = metric_value(client, "foundit_items_resolved_total")
    item = make_item(type="FOUND")
    client.post(f"/api/items/{item['id']}/resolve")
    assert metric_value(client, "foundit_items_reported_total", '{type="FOUND"}') == reported + 1
    assert metric_value(client, "foundit_items_resolved_total") == resolved + 1
