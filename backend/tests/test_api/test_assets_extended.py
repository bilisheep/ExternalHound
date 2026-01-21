import time

import pytest


@pytest.mark.asyncio
async def test_netblock_crud(async_client, test_prefix):
    cidr = "10.0.10.0/24"
    payload = {
        "external_id": f"{test_prefix}:netblock",
        "cidr": cidr,
        "asn_number": "as65000",
        "live_count": 5,
        "metadata": {"source": "pytest"},
    }

    create_resp = await async_client.post("/api/v1/netblocks", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["external_id"] == payload["external_id"]
    assert created["cidr"] == cidr
    assert created["capacity"] == 256
    assert created["is_internal"] is True
    netblock_id = created["id"]

    by_external = await async_client.get(
        f"/api/v1/netblocks/external/{payload['external_id']}"
    )
    assert by_external.status_code == 200
    assert by_external.json()["id"] == netblock_id

    by_cidr = await async_client.get(f"/api/v1/netblocks/cidr/{cidr}")
    assert by_cidr.status_code == 200
    assert by_cidr.json()["id"] == netblock_id

    list_resp = await async_client.get(
        "/api/v1/netblocks",
        params={"page": 1, "page_size": 10, "asn_number": "as65000"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["id"] == netblock_id for item in items)

    internal_list = await async_client.get(
        "/api/v1/netblocks/internal/list",
        params={"limit": 50},
    )
    assert internal_list.status_code == 200
    assert any(item["id"] == netblock_id for item in internal_list.json())

    update_resp = await async_client.put(
        f"/api/v1/netblocks/{netblock_id}",
        json={"risk_score": 5.5, "live_count": 12},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert float(updated["risk_score"]) == 5.5
    assert updated["live_count"] == 12

    delete_resp = await async_client.delete(f"/api/v1/netblocks/{netblock_id}")
    assert delete_resp.status_code == 200

    missing_resp = await async_client.get(f"/api/v1/netblocks/{netblock_id}")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_certificate_crud(async_client, test_prefix):
    now = int(time.time())
    payload = {
        "external_id": f"{test_prefix}:cert",
        "subject_cn": f"{test_prefix}.example.com",
        "issuer_cn": "Example CA",
        "valid_from": now - 3600,
        "valid_to": now + 172800,
        "metadata": {"subject_alt_names": ["a.example.com", "b.example.com"]},
    }

    create_resp = await async_client.post("/api/v1/certificates", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    cert_id = created["id"]
    assert created["external_id"] == payload["external_id"]
    assert created["san_count"] == 2
    assert created["is_expired"] is False
    assert created["days_to_expire"] >= 1

    by_external = await async_client.get(
        f"/api/v1/certificates/external/{payload['external_id']}"
    )
    assert by_external.status_code == 200
    assert by_external.json()["id"] == cert_id

    subject_list = await async_client.get(
        f"/api/v1/certificates/subject/{payload['subject_cn']}/list"
    )
    assert subject_list.status_code == 200
    assert any(item["id"] == cert_id for item in subject_list.json())

    list_resp = await async_client.get(
        "/api/v1/certificates",
        params={"page": 1, "page_size": 10, "is_expired": False},
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == cert_id for item in list_resp.json()["items"])

    update_resp = await async_client.put(
        f"/api/v1/certificates/{cert_id}",
        json={"is_revoked": True},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_revoked"] is True

    delete_resp = await async_client.delete(f"/api/v1/certificates/{cert_id}")
    assert delete_resp.status_code == 200

    missing_resp = await async_client.get(f"/api/v1/certificates/{cert_id}")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_service_crud(async_client, test_prefix):
    payload = {
        "external_id": f"{test_prefix}:service",
        "service_name": "http",
        "port": 80,
        "protocol": "TCP",
        "metadata": {"env": "test"},
    }

    create_resp = await async_client.post("/api/v1/services", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    service_id = created["id"]
    assert created["is_http"] is True
    assert created["asset_category"] == "WEB"

    by_external = await async_client.get(
        f"/api/v1/services/external/{payload['external_id']}"
    )
    assert by_external.status_code == 200
    assert by_external.json()["id"] == service_id

    list_resp = await async_client.get(
        "/api/v1/services",
        params={"page": 1, "page_size": 10, "port": 80, "protocol": "TCP"},
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == service_id for item in list_resp.json()["items"])

    name_list = await async_client.get(
        "/api/v1/services/name/http/list",
        params={"limit": 50},
    )
    assert name_list.status_code == 200
    assert any(item["id"] == service_id for item in name_list.json())

    update_resp = await async_client.put(
        f"/api/v1/services/{service_id}",
        json={"product": "Nginx", "version": "1.21", "risk_score": 4.4},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["product"] == "Nginx"
    assert updated["version"] == "1.21"
    assert updated["risk_score"] == 4.4

    delete_resp = await async_client.delete(f"/api/v1/services/{service_id}")
    assert delete_resp.status_code == 200

    missing_resp = await async_client.get(f"/api/v1/services/{service_id}")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_client_application_crud(async_client, test_prefix):
    payload = {
        "external_id": f"{test_prefix}:app",
        "app_name": "Test App",
        "package_name": f"com.example.{test_prefix}",
        "version": "1.0.0",
        "platform": "android",
        "metadata": {"permissions": ["android.permission.INTERNET"]},
    }

    create_resp = await async_client.post(
        "/api/v1/client-applications",
        json=payload,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    app_id = created["id"]
    assert created["platform"] == "Android"

    by_external = await async_client.get(
        f"/api/v1/client-applications/external/{payload['external_id']}"
    )
    assert by_external.status_code == 200
    assert by_external.json()["id"] == app_id

    list_resp = await async_client.get(
        "/api/v1/client-applications",
        params={"page": 1, "page_size": 10, "platform": "Android"},
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == app_id for item in list_resp.json()["items"])

    package_list = await async_client.get(
        f"/api/v1/client-applications/package/{payload['package_name']}/list",
        params={"limit": 50},
    )
    assert package_list.status_code == 200
    assert any(item["id"] == app_id for item in package_list.json())

    update_resp = await async_client.put(
        f"/api/v1/client-applications/{app_id}",
        json={"version": "1.0.1"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["version"] == "1.0.1"

    delete_resp = await async_client.delete(
        f"/api/v1/client-applications/{app_id}"
    )
    assert delete_resp.status_code == 200

    missing_resp = await async_client.get(
        f"/api/v1/client-applications/{app_id}"
    )
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_credential_crud(async_client, test_prefix):
    payload = {
        "external_id": f"{test_prefix}:cred",
        "cred_type": "password",
        "provider": "GitHub",
        "username": "user@example.com",
        "leaked_count": 2,
        "content": {"password_hash": "sha256:abc"},
        "validation_result": "valid",
        "metadata": {"source": "pytest"},
    }

    create_resp = await async_client.post("/api/v1/credentials", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    cred_id = created["id"]
    assert created["cred_type"] == "PASSWORD"
    assert created["validation_result"] == "VALID"

    by_external = await async_client.get(
        f"/api/v1/credentials/external/{payload['external_id']}"
    )
    assert by_external.status_code == 200
    assert by_external.json()["id"] == cred_id

    list_resp = await async_client.get(
        "/api/v1/credentials",
        params={"page": 1, "page_size": 10, "cred_type": "PASSWORD"},
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == cred_id for item in list_resp.json()["items"])

    type_list = await async_client.get(
        "/api/v1/credentials/type/PASSWORD/list",
        params={"limit": 50},
    )
    assert type_list.status_code == 200
    assert any(item["id"] == cred_id for item in type_list.json())

    leaked_list = await async_client.get(
        "/api/v1/credentials/leaked/list",
        params={"min_leaked_count": 1, "limit": 50},
    )
    assert leaked_list.status_code == 200
    assert any(item["id"] == cred_id for item in leaked_list.json())

    update_resp = await async_client.put(
        f"/api/v1/credentials/{cred_id}",
        json={"validation_result": "INVALID"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["validation_result"] == "INVALID"

    delete_resp = await async_client.delete(f"/api/v1/credentials/{cred_id}")
    assert delete_resp.status_code == 200

    missing_resp = await async_client.get(f"/api/v1/credentials/{cred_id}")
    assert missing_resp.status_code == 404
