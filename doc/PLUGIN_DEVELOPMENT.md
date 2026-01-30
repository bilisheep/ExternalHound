# ExternalHound 插件开发指南

本文档介绍如何为 ExternalHound 开发自定义数据解析器插件，以支持更多扫描工具的输出格式。

## 目录

- [插件系统概述](#插件系统概述)
- [插件架构](#插件架构)
- [开发第一个插件](#开发第一个插件)
- [插件 API 参考](#插件-api-参考)
- [最佳实践](#最佳实践)
- [示例插件](#示例插件)
- [测试插件](#测试插件)
- [发布插件](#发布插件)

## 插件系统概述

### 什么是解析器插件

解析器插件用于将各种扫描工具的输出文件解析为 ExternalHound 的标准资产格式。

### 支持的扫描工具

目前内置支持：
- **Nmap** - 网络扫描和端口探测
- 更多插件开发中...

### 为什么需要插件

- 支持不同扫描工具的输出格式
- 保持核心代码简洁
- 社区可以贡献插件
- 易于维护和扩展

## 插件架构

### 组件结构

```
backend/app/parsers/
├── __init__.py              # 插件注册中心
├── base.py                  # 基础解析器类
├── registry.py              # 插件注册表
├── nmap/                    # Nmap 插件示例
│   ├── __init__.py
│   ├── parser.py            # 解析器实现
│   └── plugin.toml          # 插件元数据
└── your_plugin/             # 你的插件
    ├── __init__.py
    ├── parser.py
    └── plugin.toml
```

### 工作流程

```
上传文件 → 识别格式 → 调用对应插件 → 解析数据 → 存储到数据库
```

### 数据流

```
扫描文件 (XML/JSON/TXT)
    ↓
插件解析器
    ↓
标准化数据格式 (ParsedData)
    ↓
服务层处理
    ↓
PostgreSQL + Neo4j 存储
```

## 开发第一个插件

### 1. 创建插件目录

```bash
cd backend/app/parsers
mkdir my_scanner
cd my_scanner
```

### 2. 创建 plugin.toml

插件元数据文件：

```toml
# plugin.toml
[plugin]
name = "my_scanner"
display_name = "My Scanner"
version = "1.0.0"
author = "Your Name"
description = "My Scanner output parser"

[plugin.supported_formats]
file_extensions = [".xml", ".json"]
mime_types = ["application/xml", "application/json"]

[plugin.requirements]
python_version = ">=3.11"
dependencies = []
```

### 3. 创建解析器类

```python
# parser.py
from typing import BinaryIO
from app.parsers.base import BaseParser, ParsedData
from app.schemas.assets.domain import DomainCreate
from app.schemas.assets.ip import IPCreate

class MyScannerParser(BaseParser):
    """My Scanner 输出解析器"""

    def parse(self, file: BinaryIO) -> ParsedData:
        """
        解析扫描文件

        Args:
            file: 文件对象

        Returns:
            ParsedData: 解析后的数据

        Raises:
            ValueError: 文件格式错误
        """
        content = file.read()

        # 解析文件内容
        # 这里实现你的解析逻辑
        data = self._parse_content(content)

        # 返回标准化数据
        return ParsedData(
            domains=[
                DomainCreate(
                    name="example.com",
                    organization_id=self.organization_id
                )
            ],
            ips=[
                IPCreate(
                    address="1.2.3.4",
                    organization_id=self.organization_id
                )
            ],
            # ... 其他资产
        )

    def _parse_content(self, content: bytes) -> dict:
        """解析文件内容的具体实现"""
        # 实现你的解析逻辑
        pass

    def validate(self, file: BinaryIO) -> bool:
        """
        验证文件格式是否正确

        Args:
            file: 文件对象

        Returns:
            bool: 是否为有效的扫描文件
        """
        try:
            content = file.read()
            # 验证文件格式
            # 例如检查 XML 根元素、JSON 结构等
            return True
        except Exception:
            return False
        finally:
            file.seek(0)  # 重置文件指针
```

### 4. 注册插件

```python
# __init__.py
from app.parsers.registry import register_parser
from .parser import MyScannerParser

# 注册解析器
register_parser("my_scanner", MyScannerParser)

__all__ = ["MyScannerParser"]
```

### 5. 使用插件

```bash
# 重启后端服务，插件会自动加载
uvicorn app.main:app --reload
```

通过 API 使用：

```bash
curl -X POST http://localhost:8000/api/v1/imports \
  -F "file=@scan.xml" \
  -F "organization_id=<org-uuid>" \
  -F "parser=my_scanner"
```

## 插件 API 参考

### BaseParser 基类

所有解析器必须继承自 `BaseParser`：

```python
from abc import ABC, abstractmethod
from typing import BinaryIO
from uuid import UUID

class BaseParser(ABC):
    """解析器基类"""

    def __init__(self, organization_id: UUID):
        """
        初始化解析器

        Args:
            organization_id: 组织 UUID
        """
        self.organization_id = organization_id

    @abstractmethod
    def parse(self, file: BinaryIO) -> ParsedData:
        """
        解析文件

        Args:
            file: 文件对象

        Returns:
            ParsedData: 解析后的数据
        """
        pass

    @abstractmethod
    def validate(self, file: BinaryIO) -> bool:
        """
        验证文件格式

        Args:
            file: 文件对象

        Returns:
            bool: 文件是否有效
        """
        pass
```

### ParsedData 数据结构

解析器必须返回 `ParsedData` 对象：

```python
from pydantic import BaseModel
from app.schemas.assets.domain import DomainCreate
from app.schemas.assets.ip import IPCreate
from app.schemas.assets.service import ServiceCreate
from app.schemas.assets.certificate import CertificateCreate

class ParsedData(BaseModel):
    """解析后的数据"""

    domains: list[DomainCreate] = []
    ips: list[IPCreate] = []
    services: list[ServiceCreate] = []
    certificates: list[CertificateCreate] = []
    # 可添加更多资产类型
```

### 资产 Schema 参考

#### DomainCreate

```python
class DomainCreate(BaseModel):
    name: str                           # 域名（必填）
    organization_id: UUID               # 组织 ID（必填）
    description: str | None = None      # 描述
    dns_records: dict | None = None     # DNS 记录
    tags: list[str] = []                # 标签
```

#### IPCreate

```python
class IPCreate(BaseModel):
    address: str                        # IP 地址（必填）
    organization_id: UUID               # 组织 ID（必填）
    hostname: str | None = None         # 主机名
    ports: list[int] = []               # 开放端口
    os_name: str | None = None          # 操作系统
    country_code: str | None = None     # 国家代码
    tags: list[str] = []                # 标签
```

#### ServiceCreate

```python
class ServiceCreate(BaseModel):
    name: str                           # 服务名称（必填）
    port: int                           # 端口号（必填）
    protocol: str                       # 协议（必填）
    organization_id: UUID               # 组织 ID（必填）
    ip_address: str | None = None       # IP 地址
    version: str | None = None          # 版本
    product: str | None = None          # 产品名称
    tags: list[str] = []                # 标签
```

#### CertificateCreate

```python
class CertificateCreate(BaseModel):
    subject: str                        # 证书主题（必填）
    issuer: str                         # 颁发者（必填）
    organization_id: UUID               # 组织 ID（必填）
    serial_number: str | None = None    # 序列号
    not_before: datetime | None = None  # 生效时间
    not_after: datetime | None = None   # 过期时间
    tags: list[str] = []                # 标签
```

## 最佳实践

### 1. 错误处理

```python
from app.core.exceptions import AppError

class MyScannerParser(BaseParser):
    def parse(self, file: BinaryIO) -> ParsedData:
        try:
            content = file.read()
            if not content:
                raise ValueError("文件为空")

            # 解析逻辑
            data = self._parse_content(content)
            return data

        except Exception as e:
            raise AppError(
                message=f"解析失败: {str(e)}",
                code="PARSE_ERROR"
            )
```

### 2. 数据验证

```python
def _validate_ip(self, ip: str) -> bool:
    """验证 IP 地址格式"""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def parse(self, file: BinaryIO) -> ParsedData:
    # ...
    if self._validate_ip(ip_address):
        ips.append(IPCreate(address=ip_address, ...))
```

### 3. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

class MyScannerParser(BaseParser):
    def parse(self, file: BinaryIO) -> ParsedData:
        logger.info(f"开始解析 My Scanner 文件")

        # 解析逻辑
        domains = self._parse_domains(content)
        logger.debug(f"解析到 {len(domains)} 个域名")

        return ParsedData(domains=domains)
```

### 4. 性能优化

```python
def parse(self, file: BinaryIO) -> ParsedData:
    # 使用流式解析处理大文件
    import xml.etree.ElementTree as ET

    domains = []
    for event, elem in ET.iterparse(file, events=('end',)):
        if elem.tag == 'domain':
            domains.append(DomainCreate(
                name=elem.get('name'),
                organization_id=self.organization_id
            ))
            elem.clear()  # 释放内存

    return ParsedData(domains=domains)
```

### 5. 去重处理

```python
def parse(self, file: BinaryIO) -> ParsedData:
    # 使用集合去重
    unique_ips = set()
    ips = []

    for ip_address in parsed_ips:
        if ip_address not in unique_ips:
            unique_ips.add(ip_address)
            ips.append(IPCreate(
                address=ip_address,
                organization_id=self.organization_id
            ))

    return ParsedData(ips=ips)
```

## 示例插件

### Masscan 插件示例

```python
# parsers/masscan/parser.py
import json
from typing import BinaryIO
from app.parsers.base import BaseParser, ParsedData
from app.schemas.assets.ip import IPCreate
from app.schemas.assets.service import ServiceCreate

class MasscanParser(BaseParser):
    """Masscan JSON 输出解析器"""

    def parse(self, file: BinaryIO) -> ParsedData:
        content = file.read()
        data = json.loads(content)

        ips = []
        services = []

        for entry in data:
            ip_address = entry.get('ip')
            if not ip_address:
                continue

            # 解析 IP
            ips.append(IPCreate(
                address=ip_address,
                organization_id=self.organization_id
            ))

            # 解析服务
            for port_info in entry.get('ports', []):
                services.append(ServiceCreate(
                    name=port_info.get('service', 'unknown'),
                    port=port_info.get('port'),
                    protocol=port_info.get('proto', 'tcp'),
                    ip_address=ip_address,
                    organization_id=self.organization_id
                ))

        return ParsedData(ips=ips, services=services)

    def validate(self, file: BinaryIO) -> bool:
        try:
            content = file.read()
            data = json.loads(content)
            # 检查是否为 Masscan 输出格式
            return isinstance(data, list) and all(
                'ip' in item for item in data
            )
        except json.JSONDecodeError:
            return False
        finally:
            file.seek(0)
```

### Nuclei 插件示例

```python
# parsers/nuclei/parser.py
import json
from typing import BinaryIO
from app.parsers.base import BaseParser, ParsedData
from app.schemas.assets.domain import DomainCreate

class NucleiParser(BaseParser):
    """Nuclei JSON 输出解析器"""

    def parse(self, file: BinaryIO) -> ParsedData:
        domains = []

        for line in file:
            try:
                entry = json.loads(line)
                host = entry.get('host')

                if host and not host.startswith('http'):
                    domains.append(DomainCreate(
                        name=host,
                        organization_id=self.organization_id,
                        description=f"发现漏洞: {entry.get('info', {}).get('name')}"
                    ))
            except json.JSONDecodeError:
                continue

        return ParsedData(domains=domains)

    def validate(self, file: BinaryIO) -> bool:
        try:
            first_line = file.readline()
            data = json.loads(first_line)
            return 'template-id' in data or 'info' in data
        except (json.JSONDecodeError, StopIteration):
            return False
        finally:
            file.seek(0)
```

## 测试插件

### 单元测试

```python
# tests/parsers/test_my_scanner.py
import pytest
from io import BytesIO
from uuid import uuid4
from app.parsers.my_scanner import MyScannerParser

def test_parse_valid_file():
    """测试解析有效文件"""
    parser = MyScannerParser(organization_id=uuid4())

    # 准备测试数据
    test_data = b'<?xml version="1.0"?><scan>...</scan>'
    file = BytesIO(test_data)

    # 执行解析
    result = parser.parse(file)

    # 验证结果
    assert len(result.domains) > 0
    assert result.domains[0].name == "example.com"

def test_validate_format():
    """测试格式验证"""
    parser = MyScannerParser(organization_id=uuid4())

    valid_file = BytesIO(b'<?xml version="1.0"?><scan>...</scan>')
    assert parser.validate(valid_file) is True

    invalid_file = BytesIO(b'invalid content')
    assert parser.validate(invalid_file) is False
```

### 集成测试

```python
# tests/api/test_import_my_scanner.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_import_my_scanner_file():
    """测试通过 API 导入文件"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 准备测试文件
        files = {"file": ("scan.xml", b"...", "application/xml")}
        data = {
            "organization_id": str(uuid4()),
            "parser": "my_scanner"
        }

        # 发送请求
        response = await client.post(
            "/api/v1/imports",
            files=files,
            data=data
        )

        # 验证响应
        assert response.status_code == 201
        assert response.json()["status"] == "SUCCESS"
```

### 手动测试

```bash
# 1. 准备测试文件
cp ~/test_scan.xml /tmp/

# 2. 通过 API 导入
curl -X POST http://localhost:8000/api/v1/imports \
  -F "file=@/tmp/test_scan.xml" \
  -F "organization_id=$(uuidgen)" \
  -F "parser=my_scanner"

# 3. 查看导入结果
curl http://localhost:8000/api/v1/imports/{import_id}
```

## 发布插件

### 1. 完善文档

在插件目录创建 `README.md`：

```markdown
# My Scanner Parser Plugin

## 描述
解析 My Scanner 工具的 XML 输出文件。

## 支持的格式
- XML (.xml)
- JSON (.json)

## 使用示例
\`\`\`bash
curl -X POST http://localhost:8000/api/v1/imports \
  -F "file=@scan.xml" \
  -F "parser=my_scanner"
\`\`\`

## 作者
Your Name <your@email.com>

## 许可证
MIT
```

### 2. 添加示例文件

提供示例输入文件：

```
parsers/my_scanner/
├── examples/
│   ├── sample_scan.xml
│   └── expected_output.json
└── README.md
```

### 3. 提交 Pull Request

```bash
git checkout -b feature/add-my-scanner-parser
git add backend/app/parsers/my_scanner/
git commit -m "feat(parser): 添加 My Scanner 解析器插件"
git push origin feature/add-my-scanner-parser
```

### 4. 插件清单

确保包含：
- [ ] parser.py 实现
- [ ] plugin.toml 元数据
- [ ] \_\_init\_\_.py 注册
- [ ] README.md 文档
- [ ] 单元测试
- [ ] 示例文件
- [ ] 更新主 README

## 常见问题

### Q: 如何处理大文件？

使用流式解析：

```python
import xml.etree.ElementTree as ET

def parse(self, file: BinaryIO) -> ParsedData:
    # 流式解析，不一次性加载整个文件
    for event, elem in ET.iterparse(file, events=('end',)):
        if elem.tag == 'host':
            # 处理单个元素
            process_element(elem)
            elem.clear()  # 释放内存
```

### Q: 如何处理编码问题？

```python
def parse(self, file: BinaryIO) -> ParsedData:
    # 尝试多种编码
    for encoding in ['utf-8', 'latin-1', 'gbk']:
        try:
            content = file.read().decode(encoding)
            break
        except UnicodeDecodeError:
            file.seek(0)
            continue
```

### Q: 如何添加自定义配置？

在 plugin.toml 中添加：

```toml
[plugin.config]
max_domains = 1000
timeout = 30
```

在解析器中读取：

```python
from app.parsers.registry import get_plugin_config

config = get_plugin_config("my_scanner")
max_domains = config.get("max_domains", 1000)
```

## 相关资源

- [开发指南](./DEVELOPMENT.md)
- [API 文档](./API.md)
- [Nmap 插件源码](../backend/app/parsers/nmap/)
- [GitHub Issues](https://github.com/bilisheep/ExternalHound/issues)

## 获取帮助

- 提交 [Issue](https://github.com/bilisheep/ExternalHound/issues/new)
- 参与 [Discussions](https://github.com/bilisheep/ExternalHound/discussions)
- 查看现有插件实现
