# ExternalHound 后端配置说明

本文档说明 ExternalHound 后端配置的来源、优先级与使用规范。

## 一、配置来源与优先级（从高到低）

1. **环境变量** - 最高优先级，可覆盖任何配置
2. **`.env` 文件**
   - 根目录 `.env` (同时影响 docker-compose 和后端)
   - `backend/.env` (覆盖 root `.env` 中的同名项)
3. **TOML 配置文件** - 最低优先级
   - 默认路径: `backend/config.toml`
   - 可通过环境变量 `EXTERNALHOUND_CONFIG` 指定自定义路径

> **实现说明**: 配置加载逻辑见 `backend/app/config.py:134-140`

## 二、推荐的配置使用方式

### 开发环境（推荐方式）

**方式 1: 使用 TOML 配置文件**
```bash
# 1. 复制配置模板
cp backend/config.example.toml backend/config.toml

# 2. 根据需要修改 backend/config.toml
# 3. 启动应用即可
```

**方式 2: 使用 .env 文件**
```bash
# 1. 复制根目录配置模板（可选）
cp .env.example .env

# 2. 复制后端配置模板（可选）
cp backend/.env.example backend/.env

# 3. 根据需要修改配置
# 注意: backend/.env 会覆盖 root/.env 中的同名配置项
```

**方式 3: 混合使用**
```bash
# 1. 使用 TOML 作为基础配置
cp backend/config.example.toml backend/config.toml

# 2. 使用 .env 覆盖个别配置项（如数据库密码）
echo "POSTGRES_PASSWORD=my_secure_password" >> backend/.env
```

### 生产环境（推荐方式）

**推荐**: 通过环境变量或外部密钥管理系统注入所有配置

```bash
# 示例: 通过环境变量启动
export POSTGRES_PASSWORD="production_secure_password"
export NEO4J_PASSWORD="production_neo4j_password"
export SECRET_KEY="production_secret_key_change_this"
export DEBUG=false

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

或使用外部配置文件:
```bash
# 指定自定义 TOML 配置路径
export EXTERNALHOUND_CONFIG=/etc/externalhound/config.toml
uvicorn app.main:app
```

**⚠️ 安全提示**:
- 严禁在生产环境使用示例配置中的默认密码
- 不要将包含敏感信息的配置文件提交到版本控制
- 建议使用 Secret 管理服务（如 AWS Secrets Manager、HashiCorp Vault）

## 三、配置文件职责说明

| 文件 | 用途 | 是否提交版本库 | 优先级 |
|------|------|----------------|--------|
| `backend/config.example.toml` | 配置模板，包含所有可用配置项 | ✅ 提交 | - |
| `backend/config.toml` | 本地实际配置 | ❌ 不提交 | 最低 |
| `backend/.env.example` | 环境变量模板 | ✅ 提交 | - |
| `backend/.env` | 本地环境变量 | ❌ 不提交 | 中 |
| `.env.example` | 根目录环境变量模板 | ✅ 提交 | - |
| `.env` | 根目录环境变量（docker-compose 也会读取） | ❌ 不提交 | 中 |
| 环境变量 | 系统或容器环境变量 | - | 最高 |

## 四、核心配置项说明

### 应用配置
```toml
APP_NAME = "ExternalHound API"    # 应用名称
APP_VERSION = "1.0.0"              # 应用版本
DEBUG = false                       # 调试模式（生产环境必须为 false）
API_V1_PREFIX = "/api/v1"          # API 路径前缀
```

### PostgreSQL 配置
```toml
POSTGRES_HOST = "localhost"        # 数据库主机
POSTGRES_PORT = 5432               # 数据库端口
POSTGRES_USER = "postgres"         # 数据库用户
POSTGRES_PASSWORD = "***"          # 数据库密码（生产环境必须修改）
POSTGRES_DB = "externalhound"      # 数据库名称
POSTGRES_SSLMODE = "disable"       # SSL 模式: disable/require/verify-ca/verify-full
```

### Neo4j 配置
```toml
NEO4J_URI = "bolt://localhost:7687"    # Neo4j 连接 URI
NEO4J_USER = "neo4j"                   # Neo4j 用户名
NEO4J_PASSWORD = "***"                 # Neo4j 密码（生产环境必须修改）

# 多项目支持（可选）
[NEO4J_PROJECTS.project_name]
uri = "bolt://localhost:7688"
user = "neo4j"
password = "***"
```

### Redis 配置
```toml
REDIS_HOST = "localhost"           # Redis 主机
REDIS_PORT = 6379                  # Redis 端口
REDIS_PASSWORD = "***"             # Redis 密码（生产环境必须修改）
REDIS_DB = 0                       # Redis 数据库编号
```

### JWT 配置（未来认证功能）
```toml
SECRET_KEY = "***"                          # JWT 密钥（生产环境必须修改）
ALGORITHM = "HS256"                         # JWT 算法
ACCESS_TOKEN_EXPIRE_MINUTES = 30            # 访问令牌过期时间（分钟）
REFRESH_TOKEN_EXPIRE_DAYS = 7               # 刷新令牌过期时间（天）
```

### 文件上传配置
```toml
UPLOAD_DIR = "/tmp/externalhound/uploads"   # 上传文件存储目录
MAX_UPLOAD_SIZE = 104857600                 # 最大上传大小（字节，默认 100MB）
```

**存储策略说明**:
- **开发环境**: 默认使用本地文件系统 (`/tmp/externalhound/uploads`)
- **生产环境**: 建议集成 MinIO 或 S3 对象存储（见第六节）

### CORS 配置
```toml
CORS_ORIGINS = [
  "http://localhost:3000",
  "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = true
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]
```

## 五、配置示例场景

### 场景 1: 开发环境 - 使用本地数据库

```toml
# backend/config.toml
DEBUG = true
POSTGRES_HOST = "localhost"
NEO4J_URI = "bolt://localhost:7687"
REDIS_HOST = "localhost"
```

### 场景 2: 生产环境 - 使用远程数据库

```bash
# 通过环境变量配置
export DEBUG=false
export POSTGRES_HOST=prod-db.example.com
export POSTGRES_PASSWORD=secure_production_password
export NEO4J_URI=bolt://prod-neo4j.example.com:7687
export NEO4J_PASSWORD=secure_neo4j_password
export REDIS_HOST=prod-redis.example.com
export SECRET_KEY=very_long_random_secret_key_for_production
```

### 场景 3: 多项目隔离

```toml
# backend/config.toml
# 默认项目使用默认 Neo4j 实例
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "default_password"

# 项目 A 使用独立 Neo4j 实例
[NEO4J_PROJECTS.project_a]
uri = "bolt://localhost:7688"
user = "neo4j"
password = "project_a_password"

# 项目 B 使用独立 Neo4j 实例
[NEO4J_PROJECTS.project_b]
uri = "bolt://localhost:7689"
user = "neo4j"
password = "project_b_password"
```

## 六、常见问题

### Q1: 为什么修改了配置没有生效？

**可能原因**:
1. 配置被更高优先级的来源覆盖（环境变量 > .env > config.toml）
2. `backend/.env` 覆盖了 root `.env` 中的配置
3. 未重启应用（配置仅在启动时加载）

**解决方法**:
1. 检查是否设置了对应的环境变量: `env | grep POSTGRES`
2. 检查 `backend/.env` 是否覆盖了配置
3. 重启应用: `uvicorn app.main:app --reload`

### Q2: 忘记复制 config.toml 怎么办？

```bash
# 从模板复制
cp backend/config.example.toml backend/config.toml

# 或者使用 .env 文件替代
cp backend/.env.example backend/.env
```

### Q3: 可以只使用环境变量吗？

可以。环境变量优先级最高，可以完全不使用 `.env` 和 `config.toml`。

```bash
# 导出所有必需的环境变量
export APP_NAME="ExternalHound API"
export POSTGRES_HOST="localhost"
export POSTGRES_PASSWORD="your_password"
# ... 其他配置

# 启动应用
uvicorn app.main:app
```

### Q4: 如何使用自定义配置文件路径？

```bash
# 通过 EXTERNALHOUND_CONFIG 环境变量指定
export EXTERNALHOUND_CONFIG=/path/to/custom/config.toml
uvicorn app.main:app
```

### Q5: root `.env` 和 `backend/.env` 有什么区别？

- **root `.env`**: 同时被 docker-compose 和后端读取，适合共享配置
- **`backend/.env`**: 仅被后端读取，且会覆盖 root `.env` 中的同名配置

**建议**:
- 数据库连接等公共配置放在 root `.env`
- 后端特定配置放在 `backend/.env`

### Q6: 生产环境应该使用哪种配置方式？

**推荐**: 使用环境变量或外部密钥管理服务

**不推荐**: 使用配置文件（容易泄露敏感信息）

```bash
# Kubernetes 示例
apiVersion: v1
kind: Secret
metadata:
  name: externalhound-secrets
type: Opaque
stringData:
  POSTGRES_PASSWORD: "production_password"
  NEO4J_PASSWORD: "neo4j_password"
  SECRET_KEY: "jwt_secret_key"
```

### Q7: 如何快速查看当前生效的配置？

```python
# 在 Python 中查看
from app.config import settings
print(settings.POSTGRES_HOST)
print(settings.DEBUG)
```

或添加调试输出（仅开发环境）:
```bash
# 在启动时打印配置（注意不要打印密码）
python -c "from app.config import settings; print(f'DB: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}')"
```

## 七、配置检查清单

### 开发环境
- [ ] 复制 `backend/config.example.toml` 到 `backend/config.toml`
- [ ] 或复制 `.env.example` 和 `backend/.env.example` 到对应的 `.env`
- [ ] 确认 Docker Compose 服务已启动 (`docker-compose ps`)
- [ ] 启动后端和前端应用

### 生产环境
- [ ] 通过环境变量或密钥管理服务注入所有配置
- [ ] 修改所有默认密码（POSTGRES, Neo4j, Redis, SECRET_KEY）
- [ ] 设置 `DEBUG=false`
- [ ] 配置正确的 CORS 源
- [ ] 配置 HTTPS/TLS
- [ ] 启用生产级日志和监控
- [ ] 配置数据备份策略

## 八、相关文档

- [项目 README](../README.md) - 快速开始指南
- [部署指南](../DEPLOYMENT.md) - 生产环境部署
- [配置源码](app/config.py) - 配置加载实现

## 九、联系与支持

如有配置相关问题，请提交 Issue 或查阅项目文档。
