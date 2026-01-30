# ExternalHound

<div align="center">

**现代化渗透测试数据管理平台**

一个基于 FastAPI + React 的企业级资产管理和关系图谱可视化平台
专为渗透测试团队、安全研究人员和红队打造

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-TBD-yellow.svg)](LICENSE)

[功能特性](#核心功能) • [快速开始](#快速开始) • [文档](doc/) • [部署指南](DEPLOYMENT.md) • [贡献指南](#贡献指南)

</div>

---

## 项目简介

ExternalHound 是一个专为渗透测试和安全评估设计的资产管理平台，提供强大的数据聚合、关系分析和可视化能力。

### 主要特点

- 🎯 **统一资产管理** - 支持 8 种资产类型，涵盖渗透测试全流程
- 📊 **关系图谱可视化** - 基于 Sigma.js 的高性能图谱渲染引擎
- 🔌 **插件化架构** - 支持自定义数据解析器，轻松集成主流扫描工具
- 🏢 **多项目隔离** - 每个项目独立数据空间，适合团队协作
- 📁 **批量导入** - 支持 Nmap、Masscan 等工具输出的批量导入
- 🔍 **高级搜索** - 标签系统 + 全文搜索 + 复杂过滤器
- ⚡ **高性能** - PostgreSQL + Neo4j 双数据库架构，异步 I/O
- 🔒 **企业级安全** - JWT 认证、RBAC 权限控制（开发中）

## 快速开始

### 前置要求

- Docker 20.10+ 和 Docker Compose 2.0+
- Node.js 18+ (用于前端开发)
- Python 3.11+ (用于后端开发)
- 至少 4GB 可用内存

### 一键启动（推荐）

使用自动化脚本快速启动完整开发环境：

```bash
# 1. 初始化项目（首次运行）
./scripts/bootstrap.sh

# 2. 启动开发环境
./scripts/dev.sh
```

`bootstrap.sh` 会自动：
- 复制配置模板文件
- 启动 Docker 服务（PostgreSQL, Neo4j, MinIO, Redis）
- 等待服务健康检查
- 验证数据库初始化
- 创建 MinIO bucket

`dev.sh` 会自动：
- 检查 Docker 服务状态
- 安装后端和前端依赖
- 运行数据库迁移
- 启动后端服务（http://localhost:8000）
- 启动前端服务（http://localhost:5173）

### 手动启动

如果需要单独启动各个服务：

```bash
# 1. 启动基础设施 (PostgreSQL, Neo4j, MinIO, Redis)
docker-compose up -d

# 2. 启动后端服务 (http://localhost:8000)
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. 启动前端服务 (http://localhost:5173)
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用系统。

### 配置说明

**配置优先级**: 环境变量 > .env 文件 > config.toml 默认值

详细配置文档请参考 [backend/CONFIG.md](backend/CONFIG.md)

**后端配置**:
- 复制 `backend/config.example.toml` 为 `backend/config.toml`
- 或复制 `backend/.env.example` 为 `backend/.env` (可选)
- 根目录 `.env` 可配置共享配置（docker-compose 和后端都会读取）

**前端配置**:
- 复制 `frontend/.env.example` 为 `frontend/.env`
- 配置 `VITE_API_BASE_URL` (默认: http://localhost:8000/api/v1)

**开发环境默认密码**:
- PostgreSQL: `postgres / externalhound_pg_pass`
- Neo4j: `neo4j / externalhound_neo4j_pass`
- MinIO: `admin / externalhound_minio_pass`
- Redis: `externalhound_redis_pass`

⚠️ **生产环境请务必修改所有默认密码！**

## 技术架构

### 后端技术栈
- **框架**: FastAPI 0.109 + Uvicorn
- **数据库**: PostgreSQL 16 (资产数据) + Neo4j 5.x (关系图谱)
- **缓存**: Redis 7.2
- **存储**: 本地文件系统 (开发) / MinIO (生产)
- **ORM**: SQLAlchemy 2.0 (异步)
- **迁移**: Alembic
- **验证**: Pydantic 2.5

### 前端技术栈
- **框架**: React 18.3 + TypeScript
- **构建**: Vite 5.2
- **UI 库**: Ant Design 5.19
- **图可视化**: Sigma.js 2.4 + Graphology
- **状态管理**: Zustand 4.5
- **数据获取**: TanStack React Query 5.45
- **路由**: React Router 6.23
- **HTTP**: Axios 1.7

### 核心功能

#### 资产类型
- **组织 (Organization)** - 目标组织信息
- **域名 (Domain)** - 域名资产及 DNS 信息
- **IP 地址 (IP)** - 主机 IP 及端口信息
- **网段 (Netblock)** - IP 段管理
- **证书 (Certificate)** - SSL/TLS 证书信息
- **服务 (Service)** - 网络服务及版本信息
- **客户端应用 (Client Application)** - 客户端软件及漏洞
- **凭证 (Credential)** - 账号密码等敏感信息

#### 数据导入
- 自动解析 Nmap XML 输出
- 支持自定义解析器插件
- 批量导入与去重
- 导入历史记录与回滚

#### 关系图谱
- 交互式图谱可视化
- 自动发现资产关系
- 多层级关系展开
- 自定义布局算法

#### 项目管理
- 多项目数据隔离
- 独立 Neo4j 图谱实例
- 项目级配置管理

## 项目结构

```
ExternalHound/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/      # REST API 路由
│   │   ├── models/      # SQLAlchemy 模型
│   │   ├── schemas/     # Pydantic 模式
│   │   ├── services/    # 业务逻辑层
│   │   ├── repositories/# 数据访问层
│   │   ├── parsers/     # 解析器插件
│   │   └── db/          # 数据库连接
│   ├── alembic/         # 数据库迁移
│   ├── config.toml      # 配置文件（从 config.example.toml 复制）
│   ├── config.example.toml  # 配置模板
│   ├── CONFIG.md        # 配置说明文档
│   └── requirements.txt
├── frontend/            # React 前端
│   ├── src/
│   │   ├── pages/       # 页面组件
│   │   ├── components/  # 可复用组件
│   │   ├── hooks/       # 自定义 Hooks
│   │   ├── services/    # API 客户端
│   │   ├── contexts/    # React Contexts
│   │   └── types/       # TypeScript 类型
│   ├── vite.config.ts
│   └── package.json
├── db/                  # 数据库相关
│   └── init/            # 数据库初始化脚本
│       ├── postgres/    # PostgreSQL 初始化
│       └── neo4j/       # Neo4j 初始化
├── scripts/             # 开发运维脚本
│   ├── bootstrap.sh     # 项目初始化脚本
│   └── dev.sh           # 开发环境启动脚本
├── doc/                 # 详细技术文档 (中文)
├── docker-compose.yml   # 完整环境编排
├── DEPLOYMENT.md        # 部署指南
├── .env.example         # 环境变量模板
└── README.md            # 本文件
```

## 开发指南

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest
```

**API 文档**: http://localhost:8000/docs (Swagger UI)

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (热重载)
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

### 数据库操作

```bash
# 创建新迁移
cd backend
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 添加新的解析器插件

1. 在 `backend/app/parsers/` 创建新解析器类
2. 实现 `BaseParser` 接口
3. 在 `plugin.toml` 注册插件
4. 重启后端服务自动加载

## 部署

详细的生产部署指南请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)，包含：
- 完整的服务配置说明
- 数据库初始化与验证
- 备份与恢复流程
- 性能调优建议
- 安全加固指南
- 故障排查方案

### 快速部署清单

- [ ] 修改所有默认密码
- [ ] 配置生产环境变量
- [ ] 启用 HTTPS/TLS
- [ ] 配置防火墙规则
- [ ] 设置数据备份计划
- [ ] 配置日志收集
- [ ] 启用监控告警

## 文档

详细技术文档位于 `doc/` 目录 (中文):
- [技术架构设计](doc/ExternalHound 技术架构设计文档.md)
- [技术选型说明](doc/ExternalHound 技术选型文档 v1.0.md)
- [数据库设计方案](doc/ExternalHound 数据库设计方案 v1.0.md)
- [前端层设计](doc/ExternalHound 前端层设计 v1.0.md)
- [后端API层设计](doc/ExternalHound 后端API层设计 v1.0.md)
- [数据导入与解析层设计](doc/ExternalHound 数据导入与解析层设计 v1.0.md)

## 常见问题

### 环境问题

**Q: 后端启动失败，提示数据库连接错误？**
A: 确保 Docker Compose 服务已启动且健康:
```bash
docker-compose ps
# 所有服务应显示 healthy 状态

# 查看服务日志
docker-compose logs postgres
docker-compose logs neo4j
```

**Q: 前端无法连接后端 API？**
A: 检查前端配置和网络连接:
```bash
# 1. 检查后端是否启动
curl http://localhost:8000/health

# 2. 检查前端配置
cat frontend/.env | grep VITE_API_BASE_URL

# 3. 检查浏览器控制台网络请求
```

**Q: Docker 容器启动失败？**
A: 检查端口占用和资源限制:
```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :7474  # Neo4j HTTP
lsof -i :7687  # Neo4j Bolt
lsof -i :9000  # MinIO API
lsof -i :6379  # Redis

# 检查 Docker 资源
docker system df
docker stats
```

### 数据库问题

**Q: Neo4j 内存不足？**
A: 调整 `docker-compose.yml` 中的 Neo4j 内存配置:
```yaml
environment:
  NEO4J_dbms_memory_heap_initial__size: 1G    # 初始堆内存
  NEO4J_dbms_memory_heap_max__size: 4G        # 最大堆内存
  NEO4J_dbms_memory_pagecache_size: 2G        # 页面缓存
```

**Q: PostgreSQL 性能慢？**
A: 检查索引和配置:
```bash
# 连接数据库
docker exec -it externalhound-postgres psql -U postgres -d externalhound

# 检查慢查询
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

# 检查索引使用情况
SELECT * FROM pg_stat_user_indexes;
```

**Q: 数据库迁移失败？**
A: 回滚并重新执行:
```bash
cd backend
alembic downgrade -1  # 回滚一个版本
alembic upgrade head  # 重新应用迁移

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

### 配置问题

**Q: 如何支持多个项目隔离？**
A: 在 `backend/config.toml` 中配置独立的 Neo4j 实例:
```toml
# 默认项目使用默认 Neo4j
NEO4J_URI = "bolt://localhost:7687"

# 项目 A 使用独立实例
[NEO4J_PROJECTS.project_a]
uri = "bolt://localhost:7688"
user = "neo4j"
password = "project_a_password"

# 项目 B 使用独立实例
[NEO4J_PROJECTS.project_b]
uri = "bolt://localhost:7689"
user = "neo4j"
password = "project_b_password"
```

**Q: 如何修改上传文件大小限制？**
A: 修改 `backend/config.toml`:
```toml
MAX_UPLOAD_SIZE = 209715200  # 200MB (字节)
```

**Q: 上传文件存储在哪里？**
A:
- **开发环境**: `/tmp/externalhound/uploads` (临时)
- **生产环境**: 建议配置 MinIO 对象存储
- 详见 [backend/CONFIG.md](backend/CONFIG.md)

### 导入问题

**Q: Nmap 导入失败？**
A: 检查 XML 格式和日志:
```bash
# 1. 验证 XML 文件格式
xmllint --noout your_scan.xml

# 2. 查看导入日志
# 通过 API 获取导入记录详情
curl http://localhost:8000/api/v1/imports/{import_id}

# 3. 确保 Nmap 输出包含必要信息
nmap -sV -oX scan.xml target.com
```

**Q: 如何添加自定义解析器？**
A: 参考 [数据导入与解析层设计](doc/ExternalHound 数据导入与解析层设计 v1.0.md)

## API 使用示例

### 认证（开发中）

```bash
# 获取访问令牌
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 使用令牌访问 API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/organizations
```

### 资产管理

```bash
# 创建组织
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Corp",
    "description": "Target organization",
    "tags": ["high-risk"]
  }'

# 查询组织列表
curl http://localhost:8000/api/v1/organizations?page=1&page_size=20

# 查询组织详情
curl http://localhost:8000/api/v1/organizations/{org_id}

# 更新组织
curl -X PUT http://localhost:8000/api/v1/organizations/{org_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# 删除组织（软删除）
curl -X DELETE http://localhost:8000/api/v1/organizations/{org_id}
```

### 域名管理

```bash
# 创建域名
curl -X POST http://localhost:8000/api/v1/domains \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example.com",
    "organization_id": "org-uuid",
    "dns_records": {"A": ["1.2.3.4"], "MX": ["mail.example.com"]},
    "tags": ["production"]
  }'

# 查询域名（带过滤）
curl "http://localhost:8000/api/v1/domains?organization_id=org-uuid&tags=production"
```

### 关系管理

```bash
# 创建资产关系
curl -X POST http://localhost:8000/api/v1/relationships \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "domain-uuid",
    "source_type": "Domain",
    "target_id": "ip-uuid",
    "target_type": "IP",
    "relationship_type": "RESOLVES_TO",
    "properties": {"discovered_at": "2024-01-20"}
  }'

# 查询资产关系
curl "http://localhost:8000/api/v1/relationships?source_id=domain-uuid"
```

### 文件导入

```bash
# 上传并导入 Nmap 扫描结果
curl -X POST http://localhost:8000/api/v1/imports \
  -F "file=@scan.xml" \
  -F "organization_id=org-uuid" \
  -F "parser=nmap"

# 查看导入记录
curl http://localhost:8000/api/v1/imports

# 查看导入详情
curl http://localhost:8000/api/v1/imports/{import_id}

# 删除导入记录和关联数据
curl -X DELETE http://localhost:8000/api/v1/imports/{import_id}
```

## 性能优化

### 数据库优化

**PostgreSQL**:
```bash
# 调整连接池大小（backend/config.toml）
# 根据并发需求调整

# 定期清理和分析
docker exec -it externalhound-postgres psql -U postgres -d externalhound
VACUUM ANALYZE;

# 重建索引
REINDEX DATABASE externalhound;
```

**Neo4j**:
```bash
# 调整内存（docker-compose.yml）
# heap: 推荐为服务器内存的 1/4 到 1/2
# pagecache: 推荐为剩余内存的大部分

# 定期维护（Neo4j Browser）
CALL db.stats.stop();
CALL db.stats.start();
```

### 应用优化

**后端**:
- 启用 Redis 缓存
- 使用连接池
- 异步 I/O 处理
- 批量操作 API

**前端**:
- 使用 React Query 缓存
- 虚拟滚动大列表
- 按需加载路由
- 图谱分页渲染

## 开发规范

### 代码风格

**Python (后端)**:
```bash
# 使用 Black 格式化
black backend/app

# 使用 Ruff 检查
ruff check backend/app

# 类型检查
mypy backend/app
```

**TypeScript (前端)**:
```bash
# ESLint 检查
npm run lint

# 格式化
npm run format

# 类型检查
npm run type-check
```

### Git 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式:

```
feat: 添加域名批量导入功能
fix: 修复图谱渲染性能问题
docs: 更新 API 文档
style: 格式化代码
refactor: 重构解析器插件系统
test: 添加资产管理单元测试
chore: 更新依赖版本
```

### 测试要求

**后端测试**:
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_assets.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

**前端测试**:
```bash
# 运行测试
npm test

# 生成覆盖率
npm run test:coverage
```

## 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 本仓库**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'feat: Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建 Pull Request**

### 贡献类型

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- ✨ 实现新功能
- 🎨 改进 UI/UX
- ⚡ 性能优化

### 开发流程

1. 查看 [Issues](https://github.com/your-org/externalhound/issues) 了解待办事项
2. 在 Issue 中评论表明你想要处理
3. 遵循开发规范编写代码
4. 确保所有测试通过
5. 提交 PR 并等待 Review

### Code Review

- 所有 PR 需要至少一名维护者审核
- CI 检查必须通过
- 遵循代码风格规范
- 包含必要的测试
- 更新相关文档

## 安全

### 漏洞报告

如果发现安全漏洞，请**不要**公开提 Issue，而是通过以下方式报告：

- 邮件：security@example.com
- 私有仓库安全通道

我们会在 48 小时内回复，并在修复后公开致谢。

### 安全最佳实践

- 定期更新依赖
- 使用强密码
- 启用 HTTPS/TLS
- 限制网络访问
- 定期备份数据
- 监控异常行为

## 路线图

### v1.0 (当前)
- [x] 基础资产管理
- [x] 关系图谱可视化
- [x] Nmap 数据导入
- [x] 多项目支持
- [x] 标签系统

### v1.1 (规划中)
- [ ] 用户认证与授权
- [ ] RBAC 权限控制
- [ ] 更多解析器插件（Masscan, Nuclei）
- [ ] MinIO 存储集成
- [ ] 数据导出功能

### v2.0 (未来)
- [ ] 漏洞管理模块
- [ ] 报告生成系统
- [ ] 时间线分析
- [ ] 协作功能
- [ ] 移动端适配

## 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [React](https://reactjs.org/) - UI 框架
- [Ant Design](https://ant.design/) - 企业级 UI 组件库
- [Sigma.js](https://www.sigmajs.org/) - 图可视化库
- [PostgreSQL](https://www.postgresql.org/) - 关系数据库
- [Neo4j](https://neo4j.com/) - 图数据库

## 许可证

(待定)

## 联系方式

- **项目主页**: https://github.com/your-org/externalhound
- **文档**: https://docs.externalhound.com
- **问题反馈**: https://github.com/your-org/externalhound/issues
- **讨论区**: https://github.com/your-org/externalhound/discussions

---

<div align="center">

**[⬆ 回到顶部](#externalhound)**

Made with ❤️ by the ExternalHound Team

</div>