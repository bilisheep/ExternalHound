import pytest


@pytest.mark.asyncio
async def test_relationship_lifecycle(async_client, test_prefix):
    org_external_id = f"{test_prefix}:org"
    domain_external_id = f"{test_prefix}:domain"
    ip_external_id = f"{test_prefix}:ip"

    org_payload = {
        "external_id": org_external_id,
        "name": "Graph Org",
        "is_primary": True,
    }
    domain_payload = {
        "external_id": domain_external_id,
        "name": f"{test_prefix}.example.org",
        "root_domain": "example.org",
        "is_resolved": True,
    }
    ip_payload = {
        "external_id": ip_external_id,
        "address": "10.20.30.40",
    }

    org_resp = await async_client.post("/api/v1/organizations", json=org_payload)
    domain_resp = await async_client.post("/api/v1/domains", json=domain_payload)
    ip_resp = await async_client.post("/api/v1/ips", json=ip_payload)

    assert org_resp.status_code == 201
    assert domain_resp.status_code == 201
    assert ip_resp.status_code == 201

    owns_payload = {
        "source_external_id": org_external_id,
        "source_type": "Organization",
        "target_external_id": domain_external_id,
        "target_type": "Domain",
        "relation_type": "OWNS_DOMAIN",
        "properties": {"source": "pytest"},
    }
    owns_resp = await async_client.post("/api/v1/relationships", json=owns_payload)
    assert owns_resp.status_code == 201
    owns = owns_resp.json()
    owns_id = owns["id"]

    resolves_payload = {
        "source_external_id": domain_external_id,
        "source_type": "Domain",
        "target_external_id": ip_external_id,
        "target_type": "IP",
        "relation_type": "RESOLVES_TO",
        "properties": {"record_type": "A"},
    }
    resolves_resp = await async_client.post(
        "/api/v1/relationships",
        json=resolves_payload,
    )
    assert resolves_resp.status_code == 201

    list_resp = await async_client.get(
        "/api/v1/relationships",
        params={"page": 1, "page_size": 10, "source_external_id": org_external_id},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["id"] == owns_id for item in items)

    update_resp = await async_client.put(
        f"/api/v1/relationships/{owns_id}",
        json={"properties": {"confidence": 0.98}},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["properties"]["source"] == "pytest"
    assert updated["properties"]["confidence"] == 0.98

    path_payload = {
        "source_external_id": org_external_id,
        "target_external_id": ip_external_id,
        "source_type": "Organization",
        "target_type": "IP",
        "relation_types": ["OWNS_DOMAIN", "RESOLVES_TO"],
        "direction": "OUT",
        "min_depth": 1,
        "max_depth": 3,
        "limit": 5,
    }
    path_resp = await async_client.post(
        "/api/v1/relationships/paths",
        json=path_payload,
    )
    assert path_resp.status_code == 200
    paths = path_resp.json()
    assert paths
    assert any(
        node["id"] == org_external_id
        for node in paths[0]["nodes"]
    )
    assert any(
        node["id"] == ip_external_id
        for node in paths[0]["nodes"]
    )

    delete_resp = await async_client.delete(f"/api/v1/relationships/{owns_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    missing_resp = await async_client.get(f"/api/v1/relationships/{owns_id}")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_relationship_type_validation(async_client, test_prefix):
    payload = {
        "source_external_id": f"{test_prefix}:ip",
        "source_type": "IP",
        "target_external_id": f"{test_prefix}:domain",
        "target_type": "Domain",
        "relation_type": "OWNS_DOMAIN",
    }
    resp = await async_client.post("/api/v1/relationships", json=payload)
    assert resp.status_code == 422
