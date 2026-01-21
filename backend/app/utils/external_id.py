from __future__ import annotations

import ipaddress
import json
from hashlib import sha256
from typing import Any, Mapping
from uuid import uuid4

MAX_EXTERNAL_ID_LEN = 255


def _hash_value(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _build_external_id(prefix: str, *parts: str) -> str:
    cleaned_parts: list[str] = [prefix]
    for part in parts:
        if part is None:
            continue
        part_value = str(part).strip()
        if part_value:
            cleaned_parts.append(part_value)
    candidate = ":".join(cleaned_parts)
    if len(candidate) <= MAX_EXTERNAL_ID_LEN:
        return candidate
    return f"{prefix}:sha256:{_hash_value(candidate)}"


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return _hash_value(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _normalize_ip(address: str) -> str:
    return str(ipaddress.ip_address(address.strip()))


def _normalize_cidr(cidr: str) -> str:
    return str(ipaddress.ip_network(cidr.strip(), strict=False))


def _extract_ip_from_metadata(metadata: Mapping[str, Any] | None) -> str | None:
    if not metadata:
        return None
    for key in ("ip", "ip_address", "address", "host"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def generate_organization_external_id(name: str | None, credit_code: str | None) -> str:
    if credit_code:
        return _build_external_id("org", credit_code)
    if name:
        return _build_external_id("org", "sha256", _hash_value(name.strip()))
    return _build_external_id("org", "uuid", str(uuid4()))


def generate_domain_external_id(name: str) -> str:
    return _build_external_id("domain", name.strip().lower())


def generate_ip_external_id(address: str) -> str:
    return _build_external_id("ip", _normalize_ip(address))


def generate_netblock_external_id(cidr: str) -> str:
    return _build_external_id("cidr", _normalize_cidr(cidr))


def generate_service_external_id(
    port: int,
    protocol: str | None,
    service_name: str | None,
    product: str | None,
    metadata: Mapping[str, Any] | None,
) -> str:
    normalized_protocol = (protocol or "TCP").strip().upper()
    ip_hint = _extract_ip_from_metadata(metadata)
    if ip_hint:
        return _build_external_id("svc", ip_hint, str(port), normalized_protocol)
    fingerprint = _hash_payload(
        {
            "port": port,
            "protocol": normalized_protocol,
            "service_name": service_name or "",
            "product": product or "",
            "metadata": metadata or {},
        }
    )
    return _build_external_id("svc", str(port), normalized_protocol, fingerprint)


def generate_certificate_external_id(
    metadata: Mapping[str, Any] | None,
    subject_cn: str | None,
    issuer_cn: str | None,
    issuer_org: str | None,
    valid_from: int | None,
    valid_to: int | None,
) -> str:
    fingerprints = {}
    if metadata and isinstance(metadata.get("fingerprints"), Mapping):
        fingerprints = metadata.get("fingerprints")  # type: ignore[assignment]
    if isinstance(fingerprints, Mapping):
        for algo in ("sha256", "sha1", "md5"):
            value = fingerprints.get(algo)
            if isinstance(value, str) and value.strip():
                return _build_external_id("cert", algo, value.strip().lower())
    payload = {
        "subject_cn": subject_cn or "",
        "issuer_cn": issuer_cn or "",
        "issuer_org": issuer_org or "",
        "valid_from": valid_from,
        "valid_to": valid_to,
        "metadata": metadata or {},
    }
    if any(value for value in payload.values()):
        return _build_external_id("cert", "sha256", _hash_payload(payload))
    return _build_external_id("cert", "uuid", str(uuid4()))


def generate_client_application_external_id(platform: str, package_name: str) -> str:
    return _build_external_id("app", platform.strip(), package_name.strip())


def generate_credential_external_id(
    cred_type: str,
    provider: str | None,
    username: str | None,
    email: str | None,
    phone: str | None,
    content: Mapping[str, Any] | None,
) -> str:
    payload = {
        "cred_type": cred_type,
        "provider": provider or "",
        "username": username or "",
        "email": email or "",
        "phone": phone or "",
        "content": content or {},
    }
    has_identity = any(
        [
            provider and provider.strip(),
            username and username.strip(),
            email and email.strip(),
            phone and phone.strip(),
            bool(content),
        ]
    )
    if has_identity:
        return _build_external_id("cred", cred_type, _hash_payload(payload))
    return _build_external_id("cred", "uuid", str(uuid4()))
