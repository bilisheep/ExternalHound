"""
Nmap XML parser plugin.
"""

from __future__ import annotations

import ipaddress
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from app.parsers.base import BaseParser, ParseResult
from app.utils.external_id import (
    generate_ip_external_id,
    generate_netblock_external_id,
    generate_service_external_id,
)


class NmapParser(BaseParser):
    """Parse Nmap XML output into normalized assets and relationships."""

    @classmethod
    def probe(cls, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".xml":
            return False
        try:
            with file_path.open("rb") as handle:
                chunk = handle.read(4096)
            return b"<nmaprun" in chunk
        except OSError:
            return False

    def parse(self) -> ParseResult:
        result = ParseResult()
        ip_addresses: list[str] = []
        try:
            tree = ET.parse(self.file_path)
        except Exception as exc:
            result.add_error("file", f"Failed to parse XML: {exc}", self._parser_name())
            return result

        root = tree.getroot()
        for host in root.findall("host"):
            status = host.find("status")
            if status is None or status.get("state") != "up":
                continue
            result.total_records += 1
            ip_address: str | None = None
            try:
                ip_address, ip_version = self._extract_address(host)
                if not ip_address:
                    raise ValueError("Missing host address")
                ip_data = self._build_ip(host, ip_address, ip_version)
                result.ips.append(ip_data)
                ip_addresses.append(ip_address)
                for service_data, relationship in self._parse_services(host, ip_address):
                    result.services.append(service_data)
                    result.relationships.append(relationship)
                result.success_count += 1
            except Exception as exc:
                record_id = ip_address or "unknown"
                result.failed_count += 1
                result.add_error(record_id, str(exc), self._parser_name())

        self._append_netblocks(result, root, ip_addresses)
        return result

    def _extract_address(self, host: ET.Element) -> tuple[str | None, int | None]:
        for addrtype, version in (("ipv4", 4), ("ipv6", 6)):
            addr = host.find(f'address[@addrtype="{addrtype}"]')
            if addr is not None:
                value = addr.get("addr")
                if value:
                    return value, version
        return None, None

    def _build_ip(
        self,
        host: ET.Element,
        ip_address: str,
        ip_version: int | None,
    ) -> dict[str, object]:
        metadata: dict[str, object] = {
            "hostnames": self._extract_hostnames(host),
            "os": self._extract_os(host),
            "scan_time": host.get("starttime"),
        }
        if self.context.import_id:
            metadata["import_id"] = self.context.import_id
        if self.context.source:
            metadata["source"] = self.context.source

        version = ip_version or ipaddress.ip_address(ip_address).version
        ip_data: dict[str, object] = {
            "external_id": generate_ip_external_id(ip_address),
            "address": ip_address,
            "version": version,
            "is_internal": ipaddress.ip_address(ip_address).is_private,
            "metadata": metadata,
        }
        if self.context.created_by:
            ip_data["created_by"] = self.context.created_by
        return ip_data

    def _parse_services(
        self,
        host: ET.Element,
        ip_address: str,
    ) -> list[tuple[dict[str, object], dict[str, object]]]:
        services: list[tuple[dict[str, object], dict[str, object]]] = []
        ports = host.find("ports")
        if ports is None:
            return services
        for port in ports.findall("port"):
            state_elem = port.find("state")
            state = state_elem.get("state") if state_elem is not None else None
            if state not in {"open", "open|filtered"}:
                continue

            portid = port.get("portid")
            if not portid:
                continue
            port_number = int(portid)
            protocol = (port.get("protocol") or "tcp").upper()

            service_elem = port.find("service")
            service_name = service_elem.get("name") if service_elem is not None else None
            product = service_elem.get("product") if service_elem is not None else None
            version = service_elem.get("version") if service_elem is not None else None
            extrainfo = service_elem.get("extrainfo") if service_elem is not None else None
            tunnel = service_elem.get("tunnel") if service_elem is not None else None
            banner = " ".join(part for part in [product, version, extrainfo] if part)
            if not banner:
                banner = None

            cpes = []
            if service_elem is not None:
                for cpe in service_elem.findall("cpe"):
                    if cpe.text:
                        cpes.append(cpe.text.strip())

            scripts = {}
            for script in port.findall("script"):
                script_id = script.get("id")
                output = script.get("output")
                if script_id:
                    scripts[script_id] = output or ""

            metadata: dict[str, object] = {
                "ip": ip_address,
                "state": state,
                "cpe": cpes,
                "scripts": scripts,
            }
            if tunnel:
                metadata["tunnel"] = tunnel
            if self.context.import_id:
                metadata["import_id"] = self.context.import_id
            if self.context.source:
                metadata["source"] = self.context.source

            is_http = service_name in {"http", "https"}
            service_external_id = generate_service_external_id(
                port=port_number,
                protocol=protocol,
                service_name=service_name,
                product=product,
                metadata=metadata,
            )
            service_data: dict[str, object] = {
                "external_id": service_external_id,
                "service_name": service_name,
                "port": port_number,
                "protocol": protocol,
                "product": product,
                "version": version,
                "banner": banner,
                "is_http": is_http,
                "metadata": metadata,
            }
            if self.context.created_by:
                service_data["created_by"] = self.context.created_by

            relationship = {
                "source_external_id": generate_ip_external_id(ip_address),
                "source_type": "IP",
                "target_external_id": service_external_id,
                "target_type": "Service",
                "relation_type": "HOSTS_SERVICE",
                "edge_key": f"{ip_address}:{port_number}:{protocol}",
                "properties": {
                    "state": state,
                    "protocol": protocol,
                    "port": port_number,
                },
            }
            if self.context.created_by:
                relationship["created_by"] = self.context.created_by
            services.append((service_data, relationship))
        return services

    def _extract_hostnames(self, host: ET.Element) -> list[str]:
        hostnames = []
        for hostname in host.findall("hostnames/hostname"):
            name = hostname.get("name")
            if name:
                hostnames.append(name)
        return hostnames

    def _extract_os(self, host: ET.Element) -> dict[str, object]:
        os_match = host.find("os/osmatch")
        if os_match is None:
            return {}
        os_info: dict[str, object] = {
            "name": os_match.get("name"),
            "accuracy": os_match.get("accuracy"),
        }
        classes = []
        for os_class in os_match.findall("osclass"):
            classes.append(
                {
                    "type": os_class.get("type"),
                    "vendor": os_class.get("vendor"),
                    "family": os_class.get("osfamily"),
                    "gen": os_class.get("osgen"),
                    "accuracy": os_class.get("accuracy"),
                }
            )
        if classes:
            os_info["classes"] = classes
        return os_info

    def _append_netblocks(
        self,
        result: ParseResult,
        root: ET.Element,
        ip_addresses: list[str],
    ) -> None:
        if not ip_addresses:
            return
        networks, source = self._resolve_networks(root, ip_addresses)
        if not networks:
            return
        for network in networks:
            netblock_data = self._build_netblock(network, ip_addresses, source)
            result.netblocks.append(netblock_data)
            for ip in ip_addresses:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj in network:
                    relationship = {
                        "source_external_id": netblock_data["external_id"],
                        "source_type": "Netblock",
                        "target_external_id": generate_ip_external_id(ip),
                        "target_type": "IP",
                        "relation_type": "CONTAINS",
                        "edge_key": f"{network.compressed}:{ip}",
                        "properties": {"source": source},
                    }
                    if self.context.created_by:
                        relationship["created_by"] = self.context.created_by
                    result.relationships.append(relationship)

    def _resolve_networks(
        self,
        root: ET.Element,
        ip_addresses: list[str],
    ) -> tuple[list[ipaddress._BaseNetwork], str]:
        networks = self._extract_networks_from_args(root)
        if networks:
            return networks, "nmap_args"
        return self._infer_networks_from_ips(ip_addresses), "inferred"

    def _extract_networks_from_args(
        self,
        root: ET.Element,
    ) -> list[ipaddress._BaseNetwork]:
        args = root.get("args") or ""
        if not args:
            return []
        matches = re.findall(r"(?:\\d{1,3}\\.){3}\\d{1,3}/\\d{1,2}", args)
        networks: list[ipaddress._BaseNetwork] = []
        for match in matches:
            try:
                networks.append(ipaddress.ip_network(match, strict=False))
            except ValueError:
                continue
        return networks

    def _infer_networks_from_ips(
        self,
        ip_addresses: list[str],
    ) -> list[ipaddress._BaseNetwork]:
        networks: dict[str, ipaddress._BaseNetwork] = {}
        for ip in ip_addresses:
            ip_obj = ipaddress.ip_address(ip)
            prefix = 24 if ip_obj.version == 4 else 64
            network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
            networks[network.compressed] = network
        return list(networks.values())

    def _build_netblock(
        self,
        network: ipaddress._BaseNetwork,
        ip_addresses: list[str],
        source: str,
    ) -> dict[str, object]:
        live_count = sum(
            1 for ip in ip_addresses if ipaddress.ip_address(ip) in network
        )
        metadata: dict[str, object] = {
            "source": source,
        }
        if self.context.import_id:
            metadata["import_id"] = self.context.import_id
        if self.context.source:
            metadata["scan_source"] = self.context.source
        netblock_data: dict[str, object] = {
            "external_id": generate_netblock_external_id(network.compressed),
            "cidr": network.compressed,
            "live_count": live_count,
            "is_internal": network.is_private,
            "metadata": metadata,
        }
        if self.context.created_by:
            netblock_data["created_by"] = self.context.created_by
        return netblock_data

    def _parser_name(self) -> str:
        return self.manifest.name if self.manifest else self.__class__.__name__
