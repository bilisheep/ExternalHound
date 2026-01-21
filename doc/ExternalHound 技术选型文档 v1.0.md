# ExternalHound 技术选型文档 v1.0

**文档信息**
- 版本：v1.0
- 日期：2026-01-16
- 系统定位：渗透测试数据管理与可视化平台（不执行扫描）
- 状态：正式版

---

## 1. 系统定位

ExternalHound 是一个**纯数据管理和可视化平台**，专注于：
- 接收外部扫描工具的结果数据
- 解析、归一化和存储数据
- 提供强大的查询和可视化能力

**明确不做的事情**：
- ❌ 不执行任何主动扫描
- ❌ 不进行渗透测试或攻击
- ❌ 不包含复杂的任务调度系统
- ❌ 暂不考虑复杂的权限和用户管理

---

## 2. 技术架构总览

### 2.1 架构图（文字描述）

```
┌─────────────────────────────────────────────────────────┐
│                      前端层                              │
│  React + Ant Design + 图谱组件 (AntV G6/Cytoscape.js)   │
└─────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│                      API 层                              │
│              FastAPI (REST API)                          │
│  - 数据导入接口                                          │
│  - 查询接口                                              │
│  - 图谱数据接口                                          │
│  - 报表导出接口                                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────┬──────────────────────────────────┐
│    数据存储层        │        文件存储层                 │
│                      │                                   │
│  PostgreSQL          │      MinIO/S3                     │
│  - 资产元数据        │      - 原始导入文件               │
│  - 导入记录          │      - 截图                       │
│  - 全文检索          │      - 附件                       │
│                      │                                   │
│  Neo4j               │      Redis (可选)                 │
│  - 资产关系图谱      │      - 查询缓存                   │
│  - 路径分析          │      - 简单限流                   │
└──────────────────────┴──────────────────────────────────┘
```

### 2.2 核心特点

- **轻量化**：去除了复杂的任务队列、调度系统
- **专注数据**：核心是数据的导入、存储、查询、展示
- **易部署**：组件少，依赖简单
- **易扩展**：支持多种数据格式，易于添加新的解析器

---

## 3. 核心技术选型

### 3.1 后端框架：FastAPI

**选型理由**
- 轻量级，易于部署和维护
- 原生支持异步 I/O，性能优异
- 自动生成 OpenAPI 文档，便于前端对接
- Pydantic 提供强类型校验

**技术优势**
- 依赖注入系统便于管理数据库连接池
- 可选集成 slowapi 实现简单限流
- 丰富的中间件生态
- 学习曲线平缓

**应用场景**
- 数据导入接口（文件上传、解析、验证）
- 查询接口（资产查询、模糊搜索、高级过滤）
- 图谱数据接口（节点、边数据）
- 报表导出接口（CSV、JSON、PDF）

**替代方案对比**
- **Flask**：更轻量但需手工补齐类型系统和文档生成
- **Django**：功能完整但过重，不适合纯 API 服务

**推荐配置**
```python
# 核心依赖
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy[asyncio]==2.0.23
neo4j==5.14.0
```

---

### 3.2 关系数据库：PostgreSQL + JSONB

**选型理由**
- 同时支持结构化和半结构化数据（JSONB）
- 强大的全文检索能力（GIN 索引 + pg_trgm）
- 成熟的事务和并发控制
- 丰富的扩展生态

**技术优势**
- JSONB 类型适合存储灵活的元数据
- GIN/GiST 索引支持高效的模糊搜索
- 支持分区表，便于数据归档
- 可靠的备份和恢复机制

**应用场景**
- 资产元数据存储（Organization、Netblock、Domain、IP、Service 等）
- 导入记录和日志
- 去重和归一化结果
- 全文检索索引

**数据模型设计**
```sql
-- 示例：IP 资产表
CREATE TABLE assets_ip (
    id UUID PRIMARY KEY,
    address INET NOT NULL UNIQUE,
    version INT NOT NULL,
    metadata JSONB,  -- 灵活的元数据字段
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 全文检索索引
CREATE INDEX idx_ip_metadata_gin ON assets_ip USING GIN (metadata);

-- 导入记录表
CREATE TABLE import_logs (
    id UUID PRIMARY KEY,
    filename TEXT,
    format TEXT,
    status TEXT,
    error_message TEXT,
    records_count INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**替代方案对比**
- **MySQL**：JSON 能力较弱，全文检索不如 PG
- **MongoDB**：灵活但缺少关系约束，不适合结构化资产数据

---

### 3.3 图数据库：Neo4j

**选型理由**
- 专为关系查询优化，路径分析性能优异
- Cypher 查询语言语义清晰，易于表达复杂图查询
- 成熟的索引和约束机制
- 丰富的图算法库

**技术优势**
- 低延迟的多跳路径查询
- 支持复杂的图遍历和模式匹配
- 内置可视化工具（Neo4j Browser）
- ACID 事务保证

**应用场景**
- 资产关系图谱（归属、拓扑、解析、服务链路）
- 攻击路径分析（从外网入口到内网服务）
- 邻居查询（某资产的上下游关系）
- 社区发现（资产聚类）

**关系模型示例**
```cypher
// 创建节点
CREATE (org:Organization {id: 'org:123', name: 'Target Corp'})
CREATE (ip:IP {id: 'ip:1.2.3.4', address: '1.2.3.4'})
CREATE (svc:Service {id: 'svc:1.2.3.4:443', port: 443})

// 创建关系
CREATE (org)-[:OWNS_ASSET]->(ip)
CREATE (ip)-[:HOSTS_SERVICE]->(svc)

// 查询路径
MATCH path = (org:Organization)-[*]-(svc:Service)
WHERE org.id = 'org:123' AND svc.port = 443
RETURN path
```

**替代方案对比**
- **Memgraph**：性能优异但生态较小
- **JanusGraph**：分布式能力强但部署复杂
- **关系数据库**：可以存储关系但查询性能差

---

### 3.4 前端框架：React + Ant Design + 图谱组件

**选型理由**
- Ant Design 是成熟的中后台 UI 解决方案
- 图谱组件（AntV G6/Cytoscape.js）提供强大的可视化能力
- React 生态丰富，组件复用性强

**技术优势**
- 开箱即用的表格、表单、筛选组件
- 图谱渲染性能优异（支持千级节点）
- 支持主题定制
- 丰富的图表库（AntV、ECharts）

**应用场景**
- 资产列表和详情展示
- 关系图谱可视化
- 数据导入界面
- 报表和统计面板

**推荐技术栈**
```json
{
  "react": "^18.2.0",
  "antd": "^5.11.0",
  "@antv/g6": "^4.8.0",
  "cytoscape": "^3.26.0",
  "axios": "^1.6.0",
  "react-router-dom": "^6.20.0"
}
```

**替代方案对比**
- **Vue + Element Plus**：功能等价，可根据团队技术栈选择
- **原生 D3.js**：灵活但开发成本高

---

### 3.5 对象存储：MinIO / S3

**选型理由**
- S3 协议兼容，易于本地和云端部署
- 支持分片上传和版本化
- 权限策略灵活

**应用场景**
- 原始导入文件存档（Nmap XML、Masscan JSON 等）
- 网页截图
- SSL 证书 PEM 文件
- 其他附件

**推荐配置**
```python
# MinIO 客户端
from minio import Minio

client = Minio(
    "minio.example.com:9000",
    access_key="ACCESS_KEY",
    secret_key="SECRET_KEY",
    secure=True
)

# 上传文件
client.fput_object(
    "imports",
    "nmap_scan_20260116.xml",
    "/tmp/scan.xml"
)
```

**替代方案对比**
- **本地文件系统**：简单但缺少权限管理和版本化
- **Ceph RGW**：功能强大但部署运维复杂

---

### 3.6 缓存（可选）：Redis

**选型理由**
- 高性能内存数据库
- 支持多种数据结构
- 简单的限流和防抖实现

**应用场景**
- 热点查询缓存（常用资产列表、统计数据）
- 简单限流（防止 API 滥用）
- 会话存储（如果需要用户登录）

**是否必需**
- 初期可不启用，直接查询数据库
- 当查询压力增大时再引入

**推荐配置**
```python
# Redis 缓存示例
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

### 3.7 监控（可选）：Prometheus + Grafana

**选型理由**
- 云原生标准组合
- 易于集成和部署
- 丰富的可视化面板

**应用场景**
- API 性能监控（延迟、吞吐量）
- 错误率统计
- 数据库连接池监控
- 导入任务统计

**是否必需**
- 初期可使用结构化日志
- 生产环境建议启用

---

## 4. 数据导入与处理流程

### 4.1 支持的数据格式

| 格式 | 工具 | 优先级 |
|------|------|--------|
| Nmap XML | Nmap | P0 |
| Masscan JSON | Masscan | P0 |
| Nuclei JSON | Nuclei | P0 |
| 通用 JSON | 自定义 | P0 |
| CSV | 通用 | P1 |
| XML | 通用 | P1 |

### 4.2 导入流程

```
┌─────────────┐
│ 1. 文件上传 │
│   或 URL    │
└──────┬──────┘
       ↓
┌─────────────┐
│ 2. 格式识别 │
│   与校验    │
└──────┬──────┘
       ↓
┌─────────────┐
│ 3. 解析数据 │
│   映射字段  │
└──────┬──────┘
       ↓
┌─────────────┐
│ 4. 数据验证 │
│   与归一化  │
└──────┬──────┘
       ↓
┌─────────────┐
│ 5. 去重合并 │
└──────┬──────┘
       ↓
┌─────────────┐
│ 6. 写入 PG  │
└──────┬──────┘
       ↓
┌─────────────┐
│ 7. 写入 Neo4j│
│   (批量)    │
└──────┬──────┘
       ↓
┌─────────────┐
│ 8. 记录日志 │
└─────────────┘
```

### 4.3 解析器设计

**统一接口**
```python
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict]:
        """解析文件，返回标准化的资产列表"""
        pass

    @abstractmethod
    def validate(self, data: Dict) -> bool:
        """验证数据完整性"""
        pass

class NmapParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict]:
        # 解析 Nmap XML
        pass

    def validate(self, data: Dict) -> bool:
        # 验证必填字段
        pass
```

### 4.4 去重与合并策略

**去重规则**
- **IP**：按 `address` 去重
- **Domain**：按 `name` 去重
- **Service**：按 `(ip, port, protocol)` 去重
- **Certificate**：按 `sha256` 指纹去重

**合并策略**
- 优先保留高置信度数据
- 保留最新时间戳的数据
- 合并多个来源的标签和属性
- 记录所有来源和导入时间

**示例代码**
```python
def merge_assets(existing: Dict, new: Dict) -> Dict:
    """合并资产数据"""
    merged = existing.copy()

    # 更新时间戳
    if new['updated_at'] > existing['updated_at']:
        merged['updated_at'] = new['updated_at']

    # 合并标签
    merged['tags'] = list(set(existing['tags'] + new['tags']))

    # 合并来源
    merged['sources'] = existing['sources'] + [new['source']]

    # 保留高置信度数据
    if new.get('confidence', 0) > existing.get('confidence', 0):
        merged.update(new)

    return merged
```

---

## 5. PG ↔ Neo4j 数据同步

> 约定：Neo4j 节点 `id` 使用 PostgreSQL 的 `external_id`，保证两库强关联。

### 5.1 同步策略（简化版）

由于不需要实时任务队列，采用**应用层批量同步**策略：

1. **导入时同步**：数据导入完成后，由 API 服务层批量写入 Neo4j
2. **幂等写入**：使用 Neo4j 的 MERGE 语句保证幂等性
3. **定期对账**（可选）：定期任务检查 PG 和 Neo4j 的数据一致性

### 5.2 批量写入示例

```python
from neo4j import GraphDatabase

class Neo4jSync:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def sync_assets(self, assets: List[Dict]):
        """批量同步资产到 Neo4j"""
        with self.driver.session() as session:
            # 批量创建节点
            session.execute_write(self._create_nodes, assets)
            # 批量创建关系
            session.execute_write(self._create_relationships, assets)

    @staticmethod
    def _create_nodes(tx, assets):
        query = """
        UNWIND $assets AS asset
        MERGE (n:IP {id: asset.external_id})
        SET n.address = asset.address,
            n.updated_at = asset.updated_at
        """
        tx.run(query, assets=assets)

    @staticmethod
    def _create_relationships(tx, assets):
        query = """
        UNWIND $assets AS asset
        MATCH (org:Organization {id: asset.org_external_id})
        MATCH (ip:IP {id: asset.external_id})
        MERGE (org)-[:OWNS_ASSET]->(ip)
        """
        tx.run(query, assets=assets)
```

### 5.3 一致性保证

- **事务性**：PG 写入成功后再写入 Neo4j
- **失败重试**：Neo4j 写入失败时记录日志，支持手动重试
- **对账任务**：定期比对 PG 和 Neo4j 的节点数量和关系数量

---

## 6. 技术风险与应对

### 6.1 数据格式多样性

**风险**
- 不同工具的输出格式差异大
- 字段命名不统一
- 数据质量参差不齐

**应对措施**
- 设计健壮的解析器，支持多种格式
- 提供字段映射配置功能
- 保留原始文件，便于追溯和重新解析
- 详细的错误日志和报告

### 6.2 去重与合并冲突

**风险**
- 不同来源的数据可能冲突
- 去重规则可能不完善
- 合并策略可能丢失信息

**应对措施**
- 可配置的去重规则和优先级
- 记录所有来源和时间戳
- 提供手动合并和拆分功能
- 保留决策日志

### 6.3 Neo4j 批量写入性能

**风险**
- 大批量数据写入可能导致性能问题
- 事务过大可能失败

**应对措施**
- 控制批次大小（建议 1000-5000 条/批）
- 使用 MERGE 语句保证幂等性
- 分段写入，避免大事务
- 监控写入性能，及时调整

### 6.4 单一 API 压力

**风险**
- 大量查询请求可能导致 API 响应慢
- 数据库连接池耗尽

**应对措施**
- 引入 Redis 缓存热点查询
- 使用连接池管理数据库连接
- 可选添加只读副本分担查询压力
- 实施简单的限流策略

---

## 7. 部署建议

### 7.1 最小化部署

**适用场景**：开发测试、小规模使用

**组件清单**
- FastAPI（单实例）
- PostgreSQL（单实例）
- Neo4j（单实例）
- MinIO（单实例）
- 前端静态文件（Nginx）

**资源需求**
- CPU：4 核
- 内存：16GB
- 磁盘：500GB SSD

### 7.2 生产部署

**适用场景**：生产环境、大规模使用

**组件清单**
- FastAPI（多实例 + 负载均衡）
- PostgreSQL（主从复制）
- Neo4j（HA 集群）
- MinIO（分布式部署）
- Redis（主从复制）
- Prometheus + Grafana（监控）

**资源需求**
- CPU：16 核+
- 内存：64GB+
- 磁盘：2TB+ SSD

### 7.3 Docker Compose 示例

```yaml
version: '3.8'

services:
  api:
    image: externalhound-api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/externalhound
      - NEO4J_URI=bolt://neo4j:7687
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
      - neo4j
      - minio

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=externalhound
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

  neo4j:
    image: neo4j:5.14
    volumes:
      - neo4j_data:/data
    environment:
      - NEO4J_AUTH=neo4j/password

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=password

  frontend:
    image: externalhound-frontend:latest
    ports:
      - "80:80"
    depends_on:
      - api

volumes:
  postgres_data:
  neo4j_data:
  minio_data:
```

---

## 8. 总结

ExternalHound v1.0 的技术选型充分考虑了系统的定位和需求：

**核心原则**
1. **简单优先**：去除不必要的复杂组件
2. **专注数据**：聚焦数据管理和可视化
3. **易于部署**：最小化依赖，降低运维成本
4. **易于扩展**：模块化设计，便于添加新功能

**技术栈总结**
- **后端**：FastAPI（轻量、高性能）
- **数据库**：PostgreSQL（元数据）+ Neo4j（关系图谱）
- **存储**：MinIO/S3（文件存储）
- **前端**：React + Ant Design + 图谱组件
- **可选**：Redis（缓存）、Prometheus（监控）

该技术栈能够满足渗透测试数据管理的核心需求，同时保持系统的简洁性和可维护性。
