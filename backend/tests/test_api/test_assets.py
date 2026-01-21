import pytest


@pytest.mark.asyncio
async def test_domain_and_ip_endpoints(async_client, test_prefix):
    domain_payload = {
        "external_id": f"{test_prefix}:domain",
        "name": f"{test_prefix}.example.com",
        "root_domain": "example.com",
        "tier": 2,
        "is_resolved": True,
        "has_waf": False,
        "metadata": {"env": "test"},
    }

    domain_resp = await async_client.post("/api/v1/domains", json=domain_payload)
    assert domain_resp.status_code == 201
    domain = domain_resp.json()
    domain_id = domain["id"]
    assert domain["external_id"] == domain_payload["external_id"]
    assert domain["is_resolved"] is True

    by_name = await async_client.get(
        f"/api/v1/domains/name/{domain_payload['name']}"
    )
    assert by_name.status_code == 200
    assert by_name.json()["id"] == domain_id

    resolved_list = await async_client.get(
        "/api/v1/domains",
        params={"page": 1, "page_size": 10, "is_resolved": True},
    )
    assert resolved_list.status_code == 200
    items = resolved_list.json()["items"]
    assert any(item["id"] == domain_id for item in items)

    ip_payload = {
        "external_id": f"{test_prefix}:ip",
        "address": "10.10.10.10",
        "is_cloud": True,
        "metadata": {"owner": "pytest"},
    }

    ip_resp = await async_client.post("/api/v1/ips", json=ip_payload)
    assert ip_resp.status_code == 201
    ip = ip_resp.json()
    assert ip["external_id"] == ip_payload["external_id"]
    assert ip["version"] == 4

    by_external = await async_client.get(
        f"/api/v1/ips/external/{ip_payload['external_id']}"
    )
    assert by_external.status_code == 200
    assert by_external.json()["address"] == ip_payload["address"]

    cloud_list = await async_client.get(
        "/api/v1/ips",
        params={"page": 1, "page_size": 10, "is_cloud": True},
    )
    assert cloud_list.status_code == 200
    cloud_items = cloud_list.json()["items"]
    assert any(item["external_id"] == ip_payload["external_id"] for item in cloud_items)
