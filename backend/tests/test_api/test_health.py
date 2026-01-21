import pytest


@pytest.mark.asyncio
async def test_health_and_root(async_client):
    health = await async_client.get("/health")
    assert health.status_code == 200
    health_data = health.json()
    assert health_data["status"] == "healthy"
    assert health_data["service"] == "ExternalHound API"

    root = await async_client.get("/")
    assert root.status_code == 200
    root_data = root.json()
    assert root_data["message"] == "Welcome to ExternalHound API"
    assert root_data["docs"] == "/docs"
