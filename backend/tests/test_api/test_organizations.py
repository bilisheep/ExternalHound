import pytest


@pytest.mark.asyncio
async def test_organization_crud(async_client, test_prefix):
    payload = {
        "external_id": f"{test_prefix}:org",
        "name": "Test Org",
        "full_name": "Test Organization LLC",
        "credit_code": f"{test_prefix}-credit",
        "is_primary": True,
        "tier": 0,
        "scope_policy": "IN_SCOPE",
        "metadata": {"source": "pytest"},
        "created_by": "pytest",
    }

    create_resp = await async_client.post("/api/v1/organizations", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["external_id"] == payload["external_id"]
    assert created["name"] == payload["name"]
    org_id = created["id"]

    get_resp = await async_client.get(f"/api/v1/organizations/{org_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == org_id

    update_resp = await async_client.put(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Updated Org", "tier": 1},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "Updated Org"
    assert updated["tier"] == 1

    list_resp = await async_client.get(
        "/api/v1/organizations",
        params={"page": 1, "page_size": 10, "is_primary": True},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["external_id"] == payload["external_id"] for item in items)

    delete_resp = await async_client.delete(f"/api/v1/organizations/{org_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    missing_resp = await async_client.get(f"/api/v1/organizations/{org_id}")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_organization_conflict(async_client, test_prefix):
    payload = {
        "external_id": f"{test_prefix}:org",
        "name": "Conflict Org",
    }

    first = await async_client.post("/api/v1/organizations", json=payload)
    assert first.status_code == 201

    second = await async_client.post("/api/v1/organizations", json=payload)
    assert second.status_code == 409
    data = second.json()
    assert data["error"] == "ConflictError"
