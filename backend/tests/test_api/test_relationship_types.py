import pytest


@pytest.mark.asyncio
async def test_all_relationship_types(async_client, test_prefix):
    async def create_asset(path: str, payload: dict) -> dict:
        resp = await async_client.post(path, json=payload)
        assert resp.status_code == 201
        return resp.json()

    org_main = await create_asset(
        "/api/v1/organizations",
        {"external_id": f"{test_prefix}:org-main", "name": "Org Main"},
    )
    org_child = await create_asset(
        "/api/v1/organizations",
        {"external_id": f"{test_prefix}:org-child", "name": "Org Child"},
    )
    domain_root = await create_asset(
        "/api/v1/domains",
        {
            "external_id": f"{test_prefix}:domain-root",
            "name": f"{test_prefix}.example.org",
            "root_domain": "example.org",
        },
    )
    domain_child = await create_asset(
        "/api/v1/domains",
        {
            "external_id": f"{test_prefix}:domain-child",
            "name": f"sub.{test_prefix}.example.org",
            "root_domain": f"{test_prefix}.example.org",
        },
    )
    ip = await create_asset(
        "/api/v1/ips",
        {
            "external_id": f"{test_prefix}:ip",
            "address": "10.20.30.40",
        },
    )
    netblock = await create_asset(
        "/api/v1/netblocks",
        {
            "external_id": f"{test_prefix}:netblock",
            "cidr": "10.20.30.0/24",
        },
    )
    certificate = await create_asset(
        "/api/v1/certificates",
        {
            "external_id": f"{test_prefix}:cert",
            "subject_cn": f"{test_prefix}.example.org",
            "issuer_cn": "Example CA",
        },
    )
    service_a = await create_asset(
        "/api/v1/services",
        {
            "external_id": f"{test_prefix}:svc-a",
            "service_name": "http",
            "port": 8080,
            "protocol": "TCP",
        },
    )
    service_b = await create_asset(
        "/api/v1/services",
        {
            "external_id": f"{test_prefix}:svc-b",
            "service_name": "http",
            "port": 8081,
            "protocol": "TCP",
        },
    )
    client_app = await create_asset(
        "/api/v1/client-applications",
        {
            "external_id": f"{test_prefix}:app",
            "app_name": "Test App",
            "package_name": f"com.example.{test_prefix}",
            "platform": "Android",
        },
    )

    relationship_payloads = [
        ("SUBSIDIARY", org_main, "Organization", org_child, "Organization"),
        ("OWNS_NETBLOCK", org_main, "Organization", netblock, "Netblock"),
        ("OWNS_ASSET", org_main, "Organization", ip, "IP"),
        ("OWNS_DOMAIN", org_main, "Organization", domain_root, "Domain"),
        ("CONTAINS", netblock, "Netblock", ip, "IP"),
        ("SUBDOMAIN", domain_root, "Domain", domain_child, "Domain"),
        ("RESOLVES_TO", domain_root, "Domain", ip, "IP"),
        ("HISTORY_RESOLVES_TO", ip, "IP", domain_child, "Domain"),
        ("ISSUED_TO", certificate, "Certificate", domain_root, "Domain"),
        ("HOSTS_SERVICE", ip, "IP", service_a, "Service"),
        ("ROUTES_TO", domain_root, "Domain", service_a, "Service"),
        ("UPSTREAM", service_a, "Service", service_b, "Service"),
        ("COMMUNICATES", client_app, "ClientApplication", service_a, "Service"),
    ]

    created_ids: dict[str, str] = {}
    for rel_type, source, source_type, target, target_type in relationship_payloads:
        payload = {
            "source_external_id": source["external_id"],
            "source_type": source_type,
            "target_external_id": target["external_id"],
            "target_type": target_type,
            "relation_type": rel_type,
        }
        resp = await async_client.post("/api/v1/relationships", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["relation_type"] == rel_type
        assert data["edge_key"] == "default"
        created_ids[rel_type] = data["id"]

    for rel_type, _, _, _, _ in relationship_payloads:
        list_resp = await async_client.get(
            "/api/v1/relationships",
            params={"page": 1, "page_size": 20, "relation_type": rel_type},
        )
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert any(item["id"] == created_ids[rel_type] for item in items)
