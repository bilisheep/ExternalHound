# ExternalHound 数据导入与解析层设计 v1.0

**文档信息**
- 版本：v1.0
- 日期：2026-01-16
- 层次定位：数据导入与解析层（Data Import & Parser Layer）
- 状态：设计方案

---

## 目录

1. [设计概述](#1-设计概述)
2. [支持的数据格式](#2-支持的数据格式)
3. [解析器架构](#3-解析器架构)
4. [核心解析器实现](#4-核心解析器实现)
5. [数据验证与清洗](#5-数据验证与清洗)
6. [导入流程设计](#6-导入流程设计)
7. [错误处理与日志](#7-错误处理与日志)
8. [性能优化](#8-性能优化)

---

## 1. 设计概述

### 1.1 层次职责

数据导入与解析层是 ExternalHound 系统的**数据入口层**，负责：

1. **多格式支持**：解析各种安全扫描工具的输出格式
2. **数据标准化**：将不同格式的数据转换为统一的内部数据模型
3. **数据验证**：确保导入数据的完整性和正确性
4. **增量更新**：支持资产的增量导入和更新
5. **错误处理**：记录解析错误，提供详细的错误报告
6. **无扫描行为**：仅处理外部导入的数据，不执行任何扫描或探测

### 1.2 设计原则

1. **插件化架构**：每种格式对应一个独立的解析器插件
2. **统一接口**：所有解析器实现相同的接口规范
3. **容错性**：单条记录解析失败不影响整体导入
4. **可追溯性**：记录数据来源、导入时间、解析版本
5. **性能优先**：支持大文件流式解析，避免内存溢出

### 1.3 技术栈

- **Python 3.11+**：主要开发语言
- **Pydantic**：数据验证和序列化
- **lxml / xmltodict**：XML 解析（Nmap）
- **ijson**：流式 JSON 解析（大文件）
- **python-magic**：文件类型检测
- **chardet**：字符编码检测

---

## 2. 支持的数据格式

### 2.1 优先级 P0（必须支持）

#### 2.1.1 Nmap XML

**工具**：Nmap
**格式**：XML
**典型命令**：
```bash
nmap -sS -sV -O -oX output.xml target.com
```

**关键信息**：
- Host 信息：IP、状态、OS 指纹
- Port 信息：端口号、协议、服务名、产品、版本
- Script 输出：NSE 脚本结果

**解析目标**：
- 创建/更新 `IP` 节点
- 创建/更新 `Service` 节点
- 建立 `IP` -> `HOSTS_SERVICE` -> `Service` 关系

#### 2.1.2 Masscan JSON

**工具**：Masscan
**格式**：JSON
**典型命令**：
```bash
masscan -p1-65535 --rate=10000 -oJ output.json 1.2.3.0/24
```

**关键信息**：
- IP 地址
- 开放端口列表
- 时间戳

**解析目标**：
- 创建/更新 `IP` 节点
- 创建 `Service` 节点（仅端口信息，无指纹）

#### 2.1.3 Subfinder JSON

**工具**：Subfinder
**格式**：JSON
**典型命令**：
```bash
subfinder -d target.com -o output.json -json
```

**关键信息**：
- 域名列表
- 来源（证书透明度、DNS 爆破等）

**解析目标**：
- 创建/更新 `Domain` 节点
- 建立 `Domain` -> `SUBDOMAIN` -> `Domain` 关系

#### 2.1.4 Nuclei JSONL

**工具**：Nuclei
**格式**：JSONL（每行一个 JSON）
**典型命令**：
```bash
nuclei -l targets.txt -jsonl -o output.jsonl
```

**关键信息**：
- 目标 URL/IP
- 漏洞模板 ID
- 严重程度
- 匹配详情

**解析目标**：
- 更新 `Service` 节点的漏洞信息
- 记录到 `metadata.vulnerabilities` 字段

### 2.2 优先级 P1（重要支持）

#### 2.2.1 Httpx JSON

**工具**：Httpx
**格式**：JSON
**关键信息**：
- URL、状态码、标题
- 技术栈指纹
- 响应头

**解析目标**：
- 更新 `Service` 节点的 HTTP 信息
- 建立 `Domain` -> `ROUTES_TO` -> `Service` 关系

#### 2.2.2 Certificate Transparency (CT) JSON

**来源**：crt.sh API、Censys
**格式**：JSON
**关键信息**：
- 证书指纹
- Subject CN、SAN 列表
- 颁发者、有效期

**解析目标**：
- 创建 `Certificate` 节点
- 创建 `Domain` 节点（从 SAN 提取）
- 建立 `Certificate` -> `ISSUED_TO` -> `Domain` 关系

#### 2.2.3 Whois 文本

**工具**：whois 命令
**格式**：纯文本
**关键信息**：
- 网段归属组织
- 注册人信息
- 联系邮箱

**解析目标**：
- 创建/更新 `Organization` 节点
- 创建 `Netblock` 节点
- 建立 `Organization` -> `OWNS_NETBLOCK` -> `Netblock` 关系

### 2.3 优先级 P2（可选支持）

- **Shodan JSON**：互联网资产搜索引擎
- **Fofa CSV**：网络空间测绘
- **Amass JSON**：子域名枚举
- **Gobuster TXT**：目录爆破结果
- **Wappalyzer JSON**：技术栈识别

---

## 3. 解析器架构

### 3.1 核心接口定义

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from enum import Enum

class ParserType(str, Enum):
    """解析器类型枚举"""
    NMAP = "nmap"
    MASSCAN = "masscan"
    SUBFINDER = "subfinder"
    NUCLEI = "nuclei"
    HTTPX = "httpx"
    CERTIFICATE = "certificate"
    WHOIS = "whois"

class ParseResult(BaseModel):
    """解析结果统一数据结构"""
    # 资产数据
    organizations: List[Dict[str, Any]] = []
    netblocks: List[Dict[str, Any]] = []
    domains: List[Dict[str, Any]] = []
    ips: List[Dict[str, Any]] = []
    certificates: List[Dict[str, Any]] = []
    services: List[Dict[str, Any]] = []
    applications: List[Dict[str, Any]] = []

    # 关系数据
    relationships: List[Dict[str, Any]] = []

    # 统计信息
    total_records: int = 0
    success_count: int = 0
    failed_count: int = 0

    # 错误记录
    errors: List[Dict[str, str]] = []

class BaseParser(ABC):
    """解析器基类"""

    def __init__(self, file_path: str, options: Optional[Dict] = None):
        self.file_path = file_path
        self.options = options or {}
        self.parser_type = self.get_parser_type()
        self.parser_version = "1.0.0"

    @abstractmethod
    def get_parser_type(self) -> ParserType:
        """返回解析器类型"""
        pass

    @abstractmethod
    def validate_format(self) -> bool:
        """验证文件格式是否正确"""
        pass

    @abstractmethod
    def parse(self) -> ParseResult:
        """执行解析，返回标准化结果"""
        pass

    def detect_encoding(self) -> str:
        """检测文件编码"""
        import chardet
        with open(self.file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'

    def log_error(self, record_id: str, error_msg: str, errors_list: List):
        """记录解析错误"""
        errors_list.append({
            "record_id": record_id,
            "error": error_msg,
            "parser": self.parser_type.value
        })
```

### 3.2 解析器工厂

```python
class ParserFactory:
    """解析器工厂类"""

    _parsers = {}

    @classmethod
    def register(cls, parser_type: ParserType, parser_class):
        """注册解析器"""
        cls._parsers[parser_type] = parser_class

    @classmethod
    def create(cls, parser_type: ParserType, file_path: str,
               options: Optional[Dict] = None) -> BaseParser:
        """创建解析器实例"""
        parser_class = cls._parsers.get(parser_type)
        if not parser_class:
            raise ValueError(f"Unsupported parser type: {parser_type}")
        return parser_class(file_path, options)

    @classmethod
    def auto_detect(cls, file_path: str) -> Optional[ParserType]:
        """自动检测文件类型"""
        import magic
        import json
        import xml.etree.ElementTree as ET

        # 检测 MIME 类型
        mime = magic.from_file(file_path, mime=True)

        # XML 文件 - 可能是 Nmap
        if mime == 'application/xml' or mime == 'text/xml':
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                if root.tag == 'nmaprun':
                    return ParserType.NMAP
            except:
                pass

        # JSON 文件 - 需要进一步判断
        elif mime == 'application/json':
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                    # Masscan 特征
                    if isinstance(data, list) and len(data) > 0:
                        if 'ip' in data[0] and 'ports' in data[0]:
                            return ParserType.MASSCAN

                    # Subfinder 特征
                    if 'host' in data and 'source' in data:
                        return ParserType.SUBFINDER
            except:
                pass

        # JSONL 文件 - 可能是 Nuclei
        elif mime == 'text/plain':
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline()
                    data = json.loads(first_line)
                    if 'template-id' in data and 'matcher-name' in data:
                        return ParserType.NUCLEI
            except:
                pass

        return None
```

---

## 4. 核心解析器实现

### 4.1 Nmap XML 解析器

```python
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

class NmapParser(BaseParser):
    """Nmap XML 解析器"""

    def get_parser_type(self) -> ParserType:
        return ParserType.NMAP

    def validate_format(self) -> bool:
        """验证是否为有效的 Nmap XML"""
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            return root.tag == 'nmaprun'
        except:
            return False

    def parse(self) -> ParseResult:
        """解析 Nmap XML 文件"""
        result = ParseResult()

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            # 遍历所有 host
            for host in root.findall('host'):
                try:
                    self._parse_host(host, result)
                    result.success_count += 1
                except Exception as e:
                    result.failed_count += 1
                    addr = host.find('.//address[@addrtype="ipv4"]')
                    ip = addr.get('addr') if addr is not None else 'unknown'
                    self.log_error(ip, str(e), result.errors)

            result.total_records = result.success_count + result.failed_count

        except Exception as e:
            result.errors.append({
                "record_id": "file",
                "error": f"Failed to parse XML: {str(e)}",
                "parser": self.parser_type.value
            })

        return result

    def _parse_host(self, host: ET.Element, result: ParseResult):
        """解析单个 host 节点"""
        # 提取 IP 地址
        addr_elem = host.find('.//address[@addrtype="ipv4"]')
        if addr_elem is None:
            addr_elem = host.find('.//address[@addrtype="ipv6"]')

        if addr_elem is None:
            return

        ip_address = addr_elem.get('addr')
        ip_version = 4 if addr_elem.get('addrtype') == 'ipv4' else 6

        # 检查主机状态
        status = host.find('status')
        if status is None or status.get('state') != 'up':
            return

        # 构建 IP 节点数据
        ip_data = {
            "address": ip_address,
            "version": ip_version,
            "metadata": {
                "scan_time": host.get('starttime'),
                "source": "nmap"
            }
        }

        # 提取 OS 指纹
        os_match = host.find('.//osmatch')
        if os_match is not None:
            ip_data["metadata"]["os_info"] = {
                "name": os_match.get('name'),
                "accuracy": int(os_match.get('accuracy', 0)),
                "fingerprint_source": "Nmap OSDetection"
            }

        # 提取主机名
        hostnames = host.findall('.//hostname')
        if hostnames:
            ip_data["metadata"]["hostnames"] = [
                {"name": hn.get('name'), "type": hn.get('type')}
                for hn in hostnames
            ]

        result.ips.append(ip_data)

        # 解析端口信息
        ports = host.findall('.//port')
        for port in ports:
            self._parse_port(port, ip_address, result)

    def _parse_port(self, port: ET.Element, ip_address: str, result: ParseResult):
        """解析端口信息"""
        port_id = port.get('portid')
        protocol = port.get('protocol', 'tcp').upper()

        # 检查端口状态
        state = port.find('state')
        if state is None or state.get('state') != 'open':
            return

        # 提取服务信息
        service = port.find('service')
        service_name = service.get('name') if service is not None else None
        product = service.get('product') if service is not None else None
        version = service.get('version') if service is not None else None

        # 构建 Service ID
        service_id = f"svc:{ip_address}:{port_id}"
        if protocol == 'UDP':
            service_id += ":UDP"

        # 构建 Service 数据
        service_data = {
            "id": service_id,
            "ip_address": ip_address,
            "port": int(port_id),
            "protocol": protocol,
            "service_name": service_name,
            "product": product,
            "version": version,
            "is_http": service_name in ['http', 'https', 'http-alt', 'https-alt'],
            "metadata": {
                "source": "nmap",
                "confidence": service.get('conf') if service is not None else None
            }
        }

        # 提取 Banner
        banner_script = port.find('.//script[@id="banner"]')
        if banner_script is not None:
            service_data["banner"] = banner_script.get('output')

        # 提取 NSE 脚本输出
        scripts = port.findall('.//script')
        if scripts:
            service_data["metadata"]["nse_scripts"] = {
                script.get('id'): script.get('output')
                for script in scripts
            }

        result.services.append(service_data)

        # 创建关系：IP -> HOSTS_SERVICE -> Service
        result.relationships.append({
            "type": "HOSTS_SERVICE",
            "source_type": "IP",
            "source_id": f"ip:{ip_address}",
            "target_type": "Service",
            "target_id": service_id,
            "properties": {
                "discovery": "Nmap",
                "first_seen": service_data["metadata"]["scan_time"]
            }
        })

# 注册解析器
ParserFactory.register(ParserType.NMAP, NmapParser)
```

### 4.2 Masscan JSON 解析器

```python
import json
from typing import Dict, List, Any

class MasscanParser(BaseParser):
    """Masscan JSON 解析器"""

    def get_parser_type(self) -> ParserType:
        return ParserType.MASSCAN

    def validate_format(self) -> bool:
        """验证是否为有效的 Masscan JSON"""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return False
                if len(data) > 0:
                    return 'ip' in data[0] and 'ports' in data[0]
                return True
        except:
            return False

    def parse(self) -> ParseResult:
        """解析 Masscan JSON 文件"""
        result = ParseResult()

        try:
            with open(self.file_path, 'r', encoding=self.detect_encoding()) as f:
                data = json.load(f)

            for record in data:
                try:
                    self._parse_record(record, result)
                    result.success_count += 1
                except Exception as e:
                    result.failed_count += 1
                    ip = record.get('ip', 'unknown')
                    self.log_error(ip, str(e), result.errors)

            result.total_records = len(data)

        except Exception as e:
            result.errors.append({
                "record_id": "file",
                "error": f"Failed to parse JSON: {str(e)}",
                "parser": self.parser_type.value
            })

        return result

    def _parse_record(self, record: Dict, result: ParseResult):
        """解析单条记录"""
        ip_address = record['ip']

        # 构建 IP 节点（如果不存在）
        ip_data = {
            "address": ip_address,
            "version": 4 if ':' not in ip_address else 6,
            "metadata": {
                "source": "masscan",
                "scan_time": record.get('timestamp')
            }
        }
        result.ips.append(ip_data)

        # 解析端口列表
        for port_info in record.get('ports', []):
            port_num = port_info['port']
            protocol = port_info.get('proto', 'tcp').upper()
            status = port_info.get('status', 'open')

            if status != 'open':
                continue

            # 构建 Service ID
            service_id = f"svc:{ip_address}:{port_num}"
            if protocol == 'UDP':
                service_id += ":UDP"

            # 构建 Service 数据（仅基础信息）
            service_data = {
                "id": service_id,
                "ip_address": ip_address,
                "port": port_num,
                "protocol": protocol,
                "metadata": {
                    "source": "masscan",
                    "scan_time": record.get('timestamp')
                }
            }

            result.services.append(service_data)

            # 创建关系
            result.relationships.append({
                "type": "HOSTS_SERVICE",
                "source_type": "IP",
                "source_id": f"ip:{ip_address}",
                "target_type": "Service",
                "target_id": service_id,
                "properties": {
                    "discovery": "Masscan",
                    "first_seen": record.get('timestamp')
                }
            })

# 注册解析器
ParserFactory.register(ParserType.MASSCAN, MasscanParser)
```

### 4.3 Subfinder JSON 解析器

```python
import json

class SubfinderParser(BaseParser):
    """Subfinder JSON 解析器"""

    def get_parser_type(self) -> ParserType:
        return ParserType.SUBFINDER

    def validate_format(self) -> bool:
        """验证格式"""
        try:
            with open(self.file_path, 'r') as f:
                # Subfinder 输出每行一个 JSON
                first_line = f.readline()
                data = json.loads(first_line)
                return 'host' in data
        except:
            return False

    def parse(self) -> ParseResult:
        """解析 Subfinder JSONL 文件"""
        result = ParseResult()

        try:
            with open(self.file_path, 'r', encoding=self.detect_encoding()) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        self._parse_record(record, result)
                        result.success_count += 1
                    except Exception as e:
                        result.failed_count += 1
                        self.log_error(f"line_{line_num}", str(e), result.errors)

            result.total_records = result.success_count + result.failed_count

        except Exception as e:
            result.errors.append({
                "record_id": "file",
                "error": f"Failed to read file: {str(e)}",
                "parser": self.parser_type.value
            })

        return result

    def _parse_record(self, record: Dict, result: ParseResult):
        """解析单条域名记录"""
        domain_name = record['host']

        # 提取根域名
        parts = domain_name.split('.')
        if len(parts) >= 2:
            root_domain = '.'.join(parts[-2:])
        else:
            root_domain = domain_name

        # 计算层级
        tier = len(parts)

        # 构建 Domain 数据
        domain_data = {
            "name": domain_name,
            "root_domain": root_domain,
            "tier": tier,
            "metadata": {
                "sources": record.get('source', []),
                "discovered_at": record.get('timestamp')
            }
        }

        result.domains.append(domain_data)

        # 如果有父域名，创建 SUBDOMAIN 关系
        if tier > 1:
            parent_domain = '.'.join(parts[1:])
            result.relationships.append({
                "type": "SUBDOMAIN",
                "source_type": "Domain",
                "source_id": f"domain:{parent_domain}",
                "target_type": "Domain",
                "target_id": f"domain:{domain_name}",
                "properties": {
                    "is_direct": True
                }
            })

# 注册解析器
ParserFactory.register(ParserType.SUBFINDER, SubfinderParser)
```

### 4.4 Nuclei JSONL 解析器

```python
import json

class NucleiParser(BaseParser):
    """Nuclei JSONL 解析器"""

    def get_parser_type(self) -> ParserType:
        return ParserType.NUCLEI

    def validate_format(self) -> bool:
        """验证格式"""
        try:
            with open(self.file_path, 'r') as f:
                first_line = f.readline()
                data = json.loads(first_line)
                return 'template-id' in data and 'info' in data
        except:
            return False

    def parse(self) -> ParseResult:
        """解析 Nuclei JSONL 文件"""
        result = ParseResult()

        try:
            with open(self.file_path, 'r', encoding=self.detect_encoding()) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        self._parse_record(record, result)
                        result.success_count += 1
                    except Exception as e:
                        result.failed_count += 1
                        self.log_error(f"line_{line_num}", str(e), result.errors)

            result.total_records = result.success_count + result.failed_count

        except Exception as e:
            result.errors.append({
                "record_id": "file",
                "error": f"Failed to read file: {str(e)}",
                "parser": self.parser_type.value
            })

        return result

    def _parse_record(self, record: Dict, result: ParseResult):
        """解析单条漏洞记录"""
        # 提取目标信息
        host = record.get('host', '')
        matched_at = record.get('matched-at', host)

        # 解析 URL 获取 IP 和端口
        from urllib.parse import urlparse
        parsed = urlparse(matched_at)

        ip_or_domain = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)

        # 构建 Service ID
        service_id = f"svc:{ip_or_domain}:{port}"

        # 提取漏洞信息
        template_id = record.get('template-id')
        info = record.get('info', {})
        severity = info.get('severity', 'unknown')

        # 构建漏洞数据（更新到 Service 的 metadata）
        vuln_data = {
            "template_id": template_id,
            "name": info.get('name'),
            "severity": severity,
            "description": info.get('description'),
            "tags": info.get('tags', []),
            "reference": info.get('reference', []),
            "matched_at": matched_at,
            "matcher_name": record.get('matcher-name'),
            "extracted_results": record.get('extracted-results', []),
            "discovered_at": record.get('timestamp')
        }

        # 注意：这里不直接创建 Service，而是记录需要更新的漏洞信息
        # 实际导入时，会查找对应的 Service 并更新其 metadata
        result.services.append({
            "id": service_id,
            "metadata": {
                "vulnerabilities": [vuln_data]
            }
        })

# 注册解析器
ParserFactory.register(ParserType.NUCLEI, NucleiParser)
```

---

## 5. 数据验证与清洗

### 5.1 Pydantic 数据模型

```python
from pydantic import BaseModel, Field, validator, IPvAnyAddress
from typing import Optional, List, Dict, Any
from datetime import datetime

class IPAsset(BaseModel):
    """IP 资产数据模型"""
    address: IPvAnyAddress
    version: int = Field(..., ge=4, le=6)
    is_cloud: bool = False
    is_internal: bool = False
    is_cdn: bool = False
    country_code: Optional[str] = Field(None, max_length=2)
    asn_number: Optional[str] = None
    scope_policy: str = Field(default="IN_SCOPE")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('version')
    def validate_version(cls, v, values):
        """验证 IP 版本与地址匹配"""
        address = values.get('address')
        if address:
            if v == 4 and ':' in str(address):
                raise ValueError("IPv4 address cannot contain ':'")
            if v == 6 and ':' not in str(address):
                raise ValueError("IPv6 address must contain ':'")
        return v

    @validator('is_internal', always=True)
    def auto_detect_internal(cls, v, values):
        """自动检测是否为内网 IP"""
        address = values.get('address')
        if address:
            import ipaddress
            ip = ipaddress.ip_address(str(address))
            return ip.is_private
        return v

class ServiceAsset(BaseModel):
    """Service 资产数据模型"""
    id: str
    ip_address: IPvAnyAddress
    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(default="TCP")
    service_name: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    is_http: bool = False
    is_admin: bool = False
    scope_policy: str = Field(default="IN_SCOPE")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('protocol')
    def validate_protocol(cls, v):
        """验证协议类型"""
        if v.upper() not in ['TCP', 'UDP']:
            raise ValueError("Protocol must be TCP or UDP")
        return v.upper()

    @validator('is_http', always=True)
    def auto_detect_http(cls, v, values):
        """自动检测是否为 HTTP 服务"""
        service_name = values.get('service_name', '').lower()
        port = values.get('port')

        if service_name in ['http', 'https', 'http-alt', 'https-alt']:
            return True
        if port in [80, 443, 8080, 8443, 8000, 8888]:
            return True
        return v

class DomainAsset(BaseModel):
    """Domain 资产数据模型"""
    name: str = Field(..., max_length=255)
    root_domain: str
    tier: int = Field(default=1, ge=1)
    is_resolved: bool = False
    is_wildcard: bool = False
    is_internal: bool = False
    has_waf: bool = False
    scope_policy: str = Field(default="IN_SCOPE")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('name')
    def validate_domain_name(cls, v):
        """验证域名格式"""
        import re
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid domain name: {v}")
        return v.lower()

    @validator('root_domain', always=True)
    def auto_extract_root(cls, v, values):
        """自动提取根域名"""
        if not v:
            name = values.get('name', '')
            parts = name.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return name
        return v.lower()

    @validator('tier', always=True)
    def auto_calculate_tier(cls, v, values):
        """自动计算层级"""
        name = values.get('name', '')
        return len(name.split('.'))
```

### 5.2 数据清洗规则

```python
class DataCleaner:
    """数据清洗工具类"""

    @staticmethod
    def normalize_ip(ip_str: str) -> str:
        """标准化 IP 地址"""
        import ipaddress
        try:
            ip = ipaddress.ip_address(ip_str)
            return str(ip)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_str}")

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """标准化域名"""
        # 转小写
        domain = domain.lower().strip()

        # 移除协议前缀
        domain = domain.replace('http://', '').replace('https://', '')

        # 移除路径
        domain = domain.split('/')[0]

        # 移除端口
        domain = domain.split(':')[0]

        # 移除前导点
        domain = domain.lstrip('.')

        return domain

    @staticmethod
    def normalize_port(port: Any) -> int:
        """标准化端口号"""
        try:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                raise ValueError(f"Port out of range: {port}")
            return port_int
        except (ValueError, TypeError):
            raise ValueError(f"Invalid port: {port}")

    @staticmethod
    def detect_service_category(service_data: Dict) -> str:
        """检测服务类别"""
        product = (service_data.get('product') or '').lower()
        service_name = (service_data.get('service_name') or '').lower()
        port = service_data.get('port')

        # VPN 检测
        vpn_keywords = ['vpn', 'sangfor', 'fortinet', 'palo alto', 'cisco anyconnect']
        if any(kw in product for kw in vpn_keywords):
            return 'VPN'

        # 网关检测
        gateway_keywords = ['gateway', 'router', 'firewall']
        if any(kw in product for kw in gateway_keywords):
            return 'Gateway'

        # OA 系统检测
        oa_keywords = ['oa', 'office automation', '致远', '泛微', '蓝凌']
        if any(kw in product for kw in oa_keywords):
            return 'OA'

        # 邮件系统
        if 'mail' in service_name or port in [25, 110, 143, 465, 587, 993, 995]:
            return 'Mail'

        # 数据库
        db_ports = [3306, 5432, 1433, 1521, 27017, 6379]
        if port in db_ports:
            return 'Database'

        # 管理后台
        admin_keywords = ['admin', 'console', 'management', 'dashboard']
        if any(kw in product for kw in admin_keywords):
            return 'Admin'

        return 'General'

    @staticmethod
    def merge_metadata(old_meta: Dict, new_meta: Dict) -> Dict:
        """合并元数据（深度合并）"""
        import copy
        result = copy.deepcopy(old_meta)

        for key, value in new_meta.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataCleaner.merge_metadata(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # 列表去重合并
                result[key] = list(set(result[key] + value))
            else:
                result[key] = value

        return result
```

---

## 6. 导入流程设计

### 6.1 导入服务类

```python
from typing import Optional
import uuid
from datetime import datetime

class ImportService:
    """数据导入服务"""

    def __init__(self, db_manager, neo4j_manager):
        self.db = db_manager
        self.neo4j = neo4j_manager

    async def import_file(
        self,
        file_path: str,
        parser_type: Optional[ParserType] = None,
        organization_id: Optional[str] = None,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """
        导入文件

        Args:
            file_path: 文件路径
            parser_type: 解析器类型（None 则自动检测）
            organization_id: 关联的组织 ID
            created_by: 创建人

        Returns:
            导入结果统计
        """
        import_id = str(uuid.uuid4())
        start_time = datetime.now()

        # 创建导入日志记录
        import_log = await self._create_import_log(
            import_id, file_path, parser_type, created_by
        )

        try:
            # 1. 自动检测解析器类型
            if parser_type is None:
                parser_type = ParserFactory.auto_detect(file_path)
                if parser_type is None:
                    raise ValueError("Cannot detect file format")

            # 2. 创建解析器并解析
            parser = ParserFactory.create(parser_type, file_path)

            if not parser.validate_format():
                raise ValueError(f"Invalid {parser_type.value} format")

            parse_result = parser.parse()

            # 3. 数据验证与清洗
            validated_result = await self._validate_and_clean(parse_result)

            # 4. 写入数据库
            import_stats = await self._import_to_database(
                validated_result,
                organization_id,
                created_by
            )

            # 5. 同步到 Neo4j
            await self._sync_to_neo4j(validated_result)

            # 6. 更新导入日志
            duration = (datetime.now() - start_time).total_seconds()
            await self._update_import_log(
                import_id,
                status="SUCCESS",
                stats=import_stats,
                duration=duration
            )

            return {
                "import_id": import_id,
                "status": "SUCCESS",
                "stats": import_stats,
                "duration_seconds": duration
            }

        except Exception as e:
            # 记录失败
            await self._update_import_log(
                import_id,
                status="FAILED",
                error_message=str(e)
            )
            raise

    async def _create_import_log(
        self,
        import_id: str,
        file_path: str,
        parser_type: Optional[ParserType],
        created_by: str
    ) -> Dict:
        """创建导入日志"""
        import os
        import hashlib

        # 计算文件哈希
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        log_data = {
            "id": import_id,
            "filename": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_hash": file_hash,
            "file_path": file_path,
            "format": parser_type.value if parser_type else "unknown",
            "status": "PROCESSING",
            "progress": 0,
            "created_by": created_by
        }

        await self.db.insert("import_logs", log_data)
        return log_data

    async def _validate_and_clean(self, parse_result: ParseResult) -> ParseResult:
        """验证和清洗数据"""
        cleaned_result = ParseResult()

        # 验证 IP 资产
        for ip_data in parse_result.ips:
            try:
                validated = IPAsset(**ip_data)
                cleaned_result.ips.append(validated.dict())
            except Exception as e:
                cleaned_result.errors.append({
                    "record_id": ip_data.get('address', 'unknown'),
                    "error": f"Validation failed: {str(e)}",
                    "type": "IP"
                })

        # 验证 Service 资产
        for svc_data in parse_result.services:
            try:
                validated = ServiceAsset(**svc_data)
                # 自动检测服务类别
                svc_dict = validated.dict()
                svc_dict['asset_category'] = DataCleaner.detect_service_category(svc_dict)
                cleaned_result.services.append(svc_dict)
            except Exception as e:
                cleaned_result.errors.append({
                    "record_id": svc_data.get('id', 'unknown'),
                    "error": f"Validation failed: {str(e)}",
                    "type": "Service"
                })

        # 验证 Domain 资产
        for domain_data in parse_result.domains:
            try:
                validated = DomainAsset(**domain_data)
                cleaned_result.domains.append(validated.dict())
            except Exception as e:
                cleaned_result.errors.append({
                    "record_id": domain_data.get('name', 'unknown'),
                    "error": f"Validation failed: {str(e)}",
                    "type": "Domain"
                })

        # 复制关系数据
        cleaned_result.relationships = parse_result.relationships

        return cleaned_result

    async def _import_to_database(
        self,
        parse_result: ParseResult,
        organization_id: Optional[str],
        created_by: str
    ) -> Dict[str, int]:
        """导入数据到 PostgreSQL"""
        stats = {
            "ips_created": 0,
            "ips_updated": 0,
            "services_created": 0,
            "services_updated": 0,
            "domains_created": 0,
            "domains_updated": 0
        }

        # 导入 IP 资产
        for ip_data in parse_result.ips:
            ip_data['created_by'] = created_by
            result = await self.db.upsert(
                "assets_ip",
                unique_key="address",
                data=ip_data
            )
            if result['action'] == 'insert':
                stats['ips_created'] += 1
            else:
                stats['ips_updated'] += 1

        # 导入 Service 资产
        for svc_data in parse_result.services:
            svc_data['created_by'] = created_by
            result = await self.db.upsert(
                "assets_service",
                unique_key="id",
                data=svc_data
            )
            if result['action'] == 'insert':
                stats['services_created'] += 1
            else:
                stats['services_updated'] += 1

        # 导入 Domain 资产
        for domain_data in parse_result.domains:
            domain_data['created_by'] = created_by
            result = await self.db.upsert(
                "assets_domain",
                unique_key="name",
                data=domain_data
            )
            if result['action'] == 'insert':
                stats['domains_created'] += 1
            else:
                stats['domains_updated'] += 1

        return stats

    async def _sync_to_neo4j(self, parse_result: ParseResult):
        """同步数据到 Neo4j"""
        # 同步节点
        for ip_data in parse_result.ips:
            await self.neo4j.merge_node("IP", ip_data)

        for svc_data in parse_result.services:
            await self.neo4j.merge_node("Service", svc_data)

        for domain_data in parse_result.domains:
            await self.neo4j.merge_node("Domain", domain_data)

        # 同步关系
        for rel in parse_result.relationships:
            await self.neo4j.merge_relationship(
                rel['source_type'],
                rel['source_id'],
                rel['type'],
                rel['target_type'],
                rel['target_id'],
                rel.get('properties', {})
            )

    async def _update_import_log(
        self,
        import_id: str,
        status: str,
        stats: Optional[Dict] = None,
        error_message: Optional[str] = None,
        duration: Optional[float] = None
    ):
        """更新导入日志"""
        update_data = {"status": status}

        if stats:
            update_data['records_success'] = sum(
                v for k, v in stats.items() if 'created' in k or 'updated' in k
            )
            update_data['assets_created'] = stats

        if error_message:
            update_data['error_message'] = error_message

        if duration:
            update_data['duration_seconds'] = int(duration)

        await self.db.update("import_logs", {"id": import_id}, update_data)
```

---

## 7. 错误处理与日志

### 7.1 异常类定义

```python
class ParserException(Exception):
    """解析器基础异常"""
    pass

class FormatValidationError(ParserException):
    """格式验证错误"""
    pass

class DataValidationError(ParserException):
    """数据验证错误"""
    pass

class ImportError(ParserException):
    """导入错误"""
    pass
```

### 7.2 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_parser_logger():
    """配置解析器日志"""
    logger = logging.getLogger('externalhound.parser')
    logger.setLevel(logging.INFO)

    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/parser.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
```

---

## 8. 性能优化

### 8.1 流式解析大文件

```python
import ijson

class LargeFileParser:
    """大文件流式解析器"""

    @staticmethod
    def parse_large_json(file_path: str, batch_size: int = 1000):
        """流式解析大型 JSON 文件"""
        with open(file_path, 'rb') as f:
            parser = ijson.items(f, 'item')
            batch = []

            for item in parser:
                batch.append(item)

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch
```

### 8.2 批量导入优化

```python
class BatchImporter:
    """批量导入优化器"""

    async def batch_upsert(
        self,
        table: str,
        records: List[Dict],
        unique_key: str,
        batch_size: int = 500
    ):
        """批量 upsert 操作"""
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await self.db.bulk_upsert(table, batch, unique_key)
```

---

## 9. 总结

### 9.1 设计亮点

1. **插件化架构**：易于扩展新的解析器
2. **统一接口**：所有解析器遵循相同规范
3. **数据验证**：使用 Pydantic 确保数据质量
4. **容错机制**：单条记录失败不影响整体
5. **性能优化**：支持大文件流式解析

### 9.2 实施建议

1. **优先实现 P0 解析器**：Nmap、Masscan、Subfinder、Nuclei
2. **完善测试用例**：每个解析器需要单元测试
3. **监控导入性能**：记录解析耗时，优化瓶颈
4. **定期更新解析器**：适配工具版本变化

---

**文档版本**：v1.0
**最后更新**：2026-01-16
**维护者**：ExternalHound 开发团队
