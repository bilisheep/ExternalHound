# ExternalHound 环境部署指南

## 概述

本文档说明如何使用 Docker Compose 快速搭建 ExternalHound 所需的完整环境。

## 环境组件

- **PostgreSQL 15**：关系数据库，存储资产元数据
- **Neo4j 5.14**：图数据库，存储资产关系图谱
- **MinIO**：对象存储，存储原始文件和截图
- **Redis 7**：缓存服务（可选）

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

## 快速开始

### 1. 启动所有服务

```bash
# 在项目根目录执行
docker-compose up -d
```

### 2. 查看服务状态

```bash
docker-compose ps
```

所有服务应该显示为 `healthy` 状态。

### 3. 访问服务

| 服务 | 地址 | 用户名 | 密码 |
|------|------|--------|------|
| PostgreSQL | localhost:5432 | postgres | externalhound_pg_pass |
| Neo4j Browser | http://localhost:7474 | neo4j | externalhound_neo4j_pass |
| Neo4j Bolt | bolt://localhost:7687 | neo4j | externalhound_neo4j_pass |
| MinIO Console | http://localhost:9001 | admin | externalhound_minio_pass |
| MinIO API | http://localhost:9000 | admin | externalhound_minio_pass |
| Redis | localhost:6379 | - | externalhound_redis_pass |

### 4. 验证数据库初始化

#### 验证 PostgreSQL

```bash
# 连接到 PostgreSQL
docker exec -it externalhound-postgres psql -U postgres -d externalhound

# 查看所有表
\dt

# 查看表结构
\d assets_organization

# 查看默认标签
SELECT * FROM tags;

# 退出
\q
```

#### 验证 Neo4j

```bash
# 方式1：使用 cypher-shell
docker exec -it externalhound-neo4j cypher-shell -u neo4j -p externalhound_neo4j_pass

# 查看约束
SHOW CONSTRAINTS;

# 查看索引
SHOW INDEXES;

# 退出
:exit

# 方式2：访问 Neo4j Browser
# 打开浏览器访问 http://localhost:7474
# 使用用户名 neo4j 和密码 externalhound_neo4j_pass 登录
```

#### 验证 MinIO

```bash
# 访问 MinIO Console
# 打开浏览器访问 http://localhost:9001
# 使用用户名 admin 和密码 externalhound_minio_pass 登录

# 创建存储桶
# 在 Console 中创建名为 "externalhound" 的 bucket
```

## 数据库初始化详情

### PostgreSQL 初始化内容

- ✅ 7 个核心资产表
  - assets_organization（组织）
  - assets_netblock（网段）
  - assets_domain（域名）
  - assets_ip（主机）
  - assets_certificate（证书）
  - assets_service（服务）
  - assets_client_application（客户端应用）

- ✅ 4 个辅助表
  - import_logs（导入记录）
  - operation_logs（操作日志）
  - tags（标签）
  - asset_tags（资产标签关联）

- ✅ 必要的扩展
  - uuid-ossp（UUID 生成）
  - pg_trgm（模糊搜索）
  - btree_gin（GIN 索引增强）
  - btree_gist（GiST 索引增强）
  - pgcrypto（加密功能）

- ✅ 完整的索引
  - B-Tree 索引
  - GIN 索引（JSONB、全文搜索）
  - GiST 索引（IP 地址范围）
  - Trigram 索引（模糊搜索）

- ✅ 8 个默认标签
  - High Risk、Medium Risk、Low Risk
  - Production、Development、Testing
  - Cloud、On-Premise

### Neo4j 初始化内容

- ✅ 7 个节点类型的唯一约束
  - Organization、Netblock、Domain、IP
  - Certificate、Service、ClientApplication

- ✅ 24 个属性索引
  - 覆盖所有高频查询字段

- ✅ 4 个复合索引
  - 优化组合查询性能

## 常用操作

### 停止所有服务

```bash
docker-compose stop
```

### 重启所有服务

```bash
docker-compose restart
```

### 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f neo4j
docker-compose logs -f minio
docker-compose logs -f redis
```

### 删除所有服务和数据

```bash
# 警告：这将删除所有数据！
docker-compose down -v
```

### 仅删除服务（保留数据）

```bash
docker-compose down
```

## 数据持久化

所有数据都存储在 Docker volumes 中：

- `postgres_data`：PostgreSQL 数据
- `neo4j_data`：Neo4j 数据
- `neo4j_logs`：Neo4j 日志
- `minio_data`：MinIO 数据
- `redis_data`：Redis 数据

查看 volumes：

```bash
docker volume ls | grep externalhound
```

## 备份与恢复

### PostgreSQL 备份

```bash
# 备份数据库
docker exec externalhound-postgres pg_dump -U postgres -d externalhound \
    -F c -f /tmp/backup.dump

# 复制备份文件到本地
docker cp externalhound-postgres:/tmp/backup.dump ./backup_$(date +%Y%m%d).dump
```

### PostgreSQL 恢复

```bash
# 复制备份文件到容器
docker cp ./backup_20260116.dump externalhound-postgres:/tmp/backup.dump

# 恢复数据库
docker exec externalhound-postgres pg_restore -U postgres -d externalhound \
    -v /tmp/backup.dump
```

### Neo4j 备份

```bash
# 停止 Neo4j
docker-compose stop neo4j

# 备份数据
docker run --rm \
    -v externalhound_neo4j_data:/data \
    -v $(pwd):/backup \
    neo4j:5.14 \
    neo4j-admin database dump neo4j --to=/backup/neo4j_backup_$(date +%Y%m%d).dump

# 启动 Neo4j
docker-compose start neo4j
```

### Neo4j 恢复

```bash
# 停止 Neo4j
docker-compose stop neo4j

# 恢复数据
docker run --rm \
    -v externalhound_neo4j_data:/data \
    -v $(pwd):/backup \
    neo4j:5.14 \
    neo4j-admin database load neo4j --from-path=/backup/neo4j_backup_20260116.dump \
    --overwrite-destination=true

# 启动 Neo4j
docker-compose start neo4j
```

## 性能调优

### PostgreSQL 性能配置

编辑 `docker-compose.yml`，在 postgres 服务中添加：

```yaml
command:
  - "postgres"
  - "-c"
  - "shared_buffers=256MB"
  - "-c"
  - "effective_cache_size=1GB"
  - "-c"
  - "maintenance_work_mem=64MB"
  - "-c"
  - "max_connections=100"
```

### Neo4j 性能配置

已在 `docker-compose.yml` 中配置：

- `NEO4J_dbms_memory_heap_initial__size=512m`
- `NEO4J_dbms_memory_heap_max__size=2G`
- `NEO4J_dbms_memory_pagecache_size=1G`

根据实际内存情况调整这些值。

## 故障排查

### PostgreSQL 无法启动

```bash
# 查看日志
docker-compose logs postgres

# 检查数据目录权限
docker exec externalhound-postgres ls -la /var/lib/postgresql/data
```

### Neo4j 无法启动

```bash
# 查看日志
docker-compose logs neo4j

# 检查内存配置
docker stats externalhound-neo4j
```

### MinIO 无法访问

```bash
# 检查端口占用
lsof -i :9000
lsof -i :9001

# 重启服务
docker-compose restart minio
```

### 健康检查失败

```bash
# 查看健康检查状态
docker inspect externalhound-postgres | grep -A 10 Health
docker inspect externalhound-neo4j | grep -A 10 Health
docker inspect externalhound-minio | grep -A 10 Health
docker inspect externalhound-redis | grep -A 10 Health
```

## 安全建议

⚠️ **重要**：默认密码仅用于开发环境，生产环境请务必修改！

### 修改密码

编辑 `docker-compose.yml`，修改以下环境变量：

```yaml
# PostgreSQL
POSTGRES_PASSWORD: your_secure_password

# Neo4j
NEO4J_AUTH: neo4j/your_secure_password

# MinIO
MINIO_ROOT_USER: your_username
MINIO_ROOT_PASSWORD: your_secure_password

# Redis
command: redis-server --requirepass your_secure_password
```

### 网络隔离

生产环境建议：

1. 不要暴露数据库端口到公网
2. 使用防火墙限制访问
3. 启用 SSL/TLS 加密连接
4. 定期更新密码

## 下一步

环境搭建完成后，可以：

1. 开发 FastAPI 后端服务
2. 实现数据导入功能
3. 开发前端界面
4. 集成扫描工具

## 参考文档

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [Neo4j 官方文档](https://neo4j.com/docs/)
- [MinIO 官方文档](https://min.io/docs/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
