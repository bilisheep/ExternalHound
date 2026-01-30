# ExternalHound 开发指南

本文档介绍如何在本地开发环境中进行 ExternalHound 的开发工作。

## 目录

- [环境准备](#环境准备)
- [后端开发](#后端开发)
- [前端开发](#前端开发)
- [数据库操作](#数据库操作)
- [开发规范](#开发规范)
- [测试](#测试)
- [调试技巧](#调试技巧)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

## 环境准备

### 前置要求

- Docker 20.10+ 和 Docker Compose 2.0+
- Node.js 18+ (前端开发)
- Python 3.11+ (后端开发)
- Git 2.30+
- 至少 4GB 可用内存

### 快速启动开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/bilisheep/ExternalHound.git
cd ExternalHound

# 2. 初始化项目（首次运行）
./scripts/bootstrap.sh

# 3. 启动开发环境
./scripts/dev.sh
```

`dev.sh` 会自动：
- 检查 Docker 服务状态
- 安装后端和前端依赖
- 运行数据库迁移
- 启动后端服务（http://localhost:8000）
- 启动前端服务（http://localhost:5173）

## 后端开发

### 项目结构

```
backend/
├── app/
│   ├── api/v1/          # REST API 路由
│   ├── models/          # SQLAlchemy 模型
│   ├── schemas/         # Pydantic 请求/响应模式
│   ├── services/        # 业务逻辑层
│   ├── repositories/    # 数据访问层
│   ├── parsers/         # 数据解析器插件
│   ├── db/              # 数据库连接管理
│   ├── core/            # 核心功能（异常、中间件）
│   └── utils/           # 工具函数
├── alembic/             # 数据库迁移
├── tests/               # 测试代码
├── config.toml          # 配置文件
└── requirements.txt     # Python 依赖
```

### 启动后端服务

#### 方式 1: 使用 dev.sh（推荐）

```bash
./scripts/dev.sh
```

#### 方式 2: 手动启动

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API 文档

启动后端服务后，访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 添加新的 API 端点

1. **定义 Pydantic Schema** (`app/schemas/`)

```python
# app/schemas/assets/example.py
from pydantic import BaseModel, Field
from uuid import UUID

class ExampleCreate(BaseModel):
    name: str = Field(..., description="名称")
    description: str | None = None

class ExampleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None

    class Config:
        from_attributes = True
```

2. **创建数据库模型** (`app/models/postgres/`)

```python
# app/models/postgres/example.py
from sqlalchemy import Column, String, Text
from app.models.postgres.base import BaseModel

class Example(BaseModel):
    __tablename__ = "examples"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
```

3. **创建 Repository** (`app/repositories/`)

```python
# app/repositories/example.py
from app.repositories.base import BaseRepository
from app.models.postgres.example import Example

class ExampleRepository(BaseRepository[Example]):
    pass
```

4. **创建 Service** (`app/services/`)

```python
# app/services/example.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.example import ExampleRepository
from app.schemas.assets.example import ExampleCreate

class ExampleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ExampleRepository(db)

    async def create(self, data: ExampleCreate):
        return await self.repo.create(data.model_dump())
```

5. **创建 API Router** (`app/api/v1/`)

```python
# app/api/v1/example.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db
from app.services.example import ExampleService
from app.schemas.assets.example import ExampleCreate, ExampleResponse

router = APIRouter(prefix="/examples", tags=["examples"])

@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(
    data: ExampleCreate,
    db: AsyncSession = Depends(get_db)
):
    service = ExampleService(db)
    return await service.create(data)
```

6. **注册 Router** (`app/api/v1/__init__.py`)

```python
from app.api.v1.example import router as example_router

api_router.include_router(example_router)
```

## 前端开发

### 项目结构

```
frontend/
├── src/
│   ├── pages/           # 页面组件
│   ├── components/      # 可复用组件
│   ├── hooks/           # 自定义 React Hooks
│   ├── services/api/    # API 客户端
│   ├── contexts/        # React Context
│   ├── stores/          # Zustand 状态管理
│   ├── types/           # TypeScript 类型定义
│   ├── utils/           # 工具函数
│   ├── i18n/            # 国际化
│   └── router/          # 路由配置
├── public/              # 静态资源
├── index.html           # HTML 入口
├── vite.config.ts       # Vite 配置
└── package.json         # Node.js 依赖
```

### 启动前端服务

#### 方式 1: 使用 dev.sh（推荐）

```bash
./scripts/dev.sh
```

#### 方式 2: 手动启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（热重载）
npm run dev

# 访问 http://localhost:5173
```

### 构建生产版本

```bash
cd frontend

# 构建
npm run build

# 预览构建结果
npm run preview
```

### 添加新页面

1. **创建页面组件** (`src/pages/`)

```typescript
// src/pages/Example/ExamplePage.tsx
import { Typography } from 'antd';

const ExamplePage: React.FC = () => {
  return (
    <div>
      <Typography.Title>Example Page</Typography.Title>
    </div>
  );
};

export default ExamplePage;
```

2. **添加路由** (`src/router/AppRouter.tsx`)

```typescript
import ExamplePage from '@/pages/Example/ExamplePage';

const routes = [
  // ... 其他路由
  {
    path: '/example',
    element: <ExamplePage />,
  },
];
```

3. **添加导航菜单项**（如需要）

### 使用 API

1. **定义类型** (`src/types/`)

```typescript
// src/types/example.ts
export interface Example {
  id: string;
  name: string;
  description?: string;
}

export interface ExampleCreatePayload {
  name: string;
  description?: string;
}
```

2. **创建 API 客户端** (`src/services/api/`)

```typescript
// src/services/api/example.ts
import { apiClient } from './client';
import type { Example, ExampleCreatePayload } from '@/types/example';

export const exampleApi = {
  getAll: () => apiClient.get<Example[]>('/examples'),
  create: (data: ExampleCreatePayload) =>
    apiClient.post<Example>('/examples', data),
};
```

3. **创建 React Hook** (`src/hooks/`)

```typescript
// src/hooks/useExample.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { exampleApi } from '@/services/api/example';

export const useExamples = () => {
  return useQuery({
    queryKey: ['examples'],
    queryFn: () => exampleApi.getAll(),
  });
};

export const useCreateExample = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: exampleApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examples'] });
    },
  });
};
```

4. **在组件中使用**

```typescript
import { useExamples, useCreateExample } from '@/hooks/useExample';

const ExampleList: React.FC = () => {
  const { data: examples, isLoading } = useExamples();
  const createMutation = useCreateExample();

  const handleCreate = async (values: ExampleCreatePayload) => {
    await createMutation.mutateAsync(values);
  };

  // ...
};
```

## 数据库操作

### PostgreSQL 迁移

```bash
cd backend

# 创建新迁移（自动生成）
alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
alembic upgrade head

# 回滚到上一个版本
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 手动创建迁移

```bash
# 创建空迁移文件
alembic revision -m "add_custom_index"
```

编辑生成的迁移文件：

```python
def upgrade() -> None:
    op.create_index(
        'idx_assets_external_id',
        'assets_organization',
        ['external_id']
    )

def downgrade() -> None:
    op.drop_index('idx_assets_external_id', 'assets_organization')
```

### 直接操作数据库

```bash
# PostgreSQL
docker exec -it externalhound-postgres psql -U postgres -d externalhound

# 常用 SQL 命令
\dt                    # 列出所有表
\d table_name          # 查看表结构
\di                    # 列出所有索引
SELECT * FROM tags;    # 查询数据
\q                     # 退出
```

```bash
# Neo4j
docker exec -it externalhound-neo4j cypher-shell -u neo4j -p externalhound_neo4j_pass

# 常用 Cypher 命令
SHOW CONSTRAINTS;                      // 查看约束
SHOW INDEXES;                          // 查看索引
MATCH (n:Organization) RETURN n;       // 查询节点
MATCH (n)-[r]-(m) RETURN n, r, m;     // 查询关系
:exit                                  // 退出
```

## 开发规范

### 代码风格

#### Python (后端)

使用 Black + Ruff + MyPy:

```bash
cd backend

# 格式化代码
black app/

# Lint 检查
ruff check app/

# 类型检查
mypy app/
```

**风格要点**:
- 使用 Black 默认配置（行长 88）
- 类型注解必须完整
- 遵循 PEP 8 命名规范
- Docstring 使用 Google 风格

#### TypeScript (前端)

使用 ESLint + Prettier:

```bash
cd frontend

# Lint 检查
npm run lint

# 自动修复
npm run lint:fix

# 类型检查
npm run type-check
```

**风格要点**:
- 使用函数组件和 Hooks
- 使用 TypeScript 严格模式
- Props 必须有类型定义
- 使用 CSS Modules 或 styled-components

### Git 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建/工具变更

**示例**:
```
feat(api): 添加域名批量导入功能

- 实现 CSV 文件解析
- 添加批量创建 API
- 更新文档

Closes #123
```

### 分支管理

- `main`: 主分支，稳定版本
- `develop`: 开发分支（可选）
- `feature/*`: 功能分支
- `fix/*`: 修复分支
- `refactor/*`: 重构分支

**工作流程**:
```bash
# 1. 创建功能分支
git checkout -b feature/add-domain-import

# 2. 开发并提交
git add .
git commit -m "feat: 添加域名导入功能"

# 3. 推送并创建 PR
git push origin feature/add-domain-import
```

## 测试

### 后端测试

使用 pytest:

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_assets.py

# 运行特定测试函数
pytest tests/test_assets.py::test_create_organization

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

**编写测试**:

```python
# tests/test_example.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_example():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/examples",
            json={"name": "Test", "description": "Test example"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Test"
```

### 前端测试

使用 Vitest + React Testing Library:

```bash
cd frontend

# 运行测试
npm test

# 监听模式
npm test -- --watch

# 生成覆盖率
npm run test:coverage
```

**编写测试**:

```typescript
// src/components/Example.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Example from './Example';

describe('Example', () => {
  it('renders correctly', () => {
    render(<Example name="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

## 调试技巧

### 后端调试

#### 使用 Python Debugger

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb (更友好)
import ipdb; ipdb.set_trace()
```

#### 使用 VS Code 调试

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### 日志调试

```python
import logging

logger = logging.getLogger(__name__)

# 使用日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告")
logger.error("错误")
```

### 前端调试

#### 使用 React DevTools

安装浏览器扩展：
- [React Developer Tools](https://react.dev/learn/react-developer-tools)

#### 使用 Console

```typescript
console.log('Debug:', data);
console.table(arrayData);
console.trace('Trace point');
```

#### 使用 VS Code 调试

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

## 性能优化

### 后端性能优化

#### 数据库优化

```python
# 使用 select_in_load 避免 N+1 查询
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(Organization)
    .options(selectinload(Organization.domains))
)

# 使用批量操作
await session.execute(
    insert(Domain),
    [{"name": "example1.com"}, {"name": "example2.com"}]
)
```

#### 使用缓存

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/organizations")
@cache(expire=300)  # 缓存 5 分钟
async def get_organizations():
    # ...
```

#### 异步处理

```python
import asyncio

# 并发执行多个查询
results = await asyncio.gather(
    get_organizations(),
    get_domains(),
    get_ips()
)
```

### 前端性能优化

#### React 优化

```typescript
// 使用 memo 避免不必要的重渲染
const MemoizedComponent = React.memo(Component);

// 使用 useMemo 缓存计算结果
const expensiveValue = useMemo(
  () => computeExpensiveValue(data),
  [data]
);

// 使用 useCallback 缓存回调函数
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

#### 代码分割

```typescript
// 路由级别代码分割
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Graph = lazy(() => import('@/pages/Graph'));

// 使用 Suspense
<Suspense fallback={<Loading />}>
  <Dashboard />
</Suspense>
```

#### 虚拟滚动

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={1000}
  itemSize={50}
>
  {Row}
</FixedSizeList>
```

## 故障排查

### 后端常见问题

#### 数据库连接失败

```bash
# 检查 PostgreSQL
docker-compose logs postgres

# 检查连接
docker exec -it externalhound-postgres pg_isready

# 检查配置
cat backend/config.toml | grep POSTGRES
```

#### 导入数据失败

```bash
# 查看导入日志
curl http://localhost:8000/api/v1/imports/{import_id}

# 检查文件格式
xmllint --noout scan.xml
```

#### Neo4j 内存不足

```yaml
# docker-compose.yml
environment:
  NEO4J_dbms_memory_heap_max__size: 4G
  NEO4J_dbms_memory_pagecache_size: 2G
```

### 前端常见问题

#### API 请求失败

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查浏览器控制台
# Network 标签查看请求详情
```

#### 构建失败

```bash
# 清理缓存
rm -rf node_modules .vite
npm install

# 检查 TypeScript 错误
npm run type-check
```

#### 样式不生效

```bash
# 清理缓存
rm -rf frontend/dist frontend/.vite

# 重启开发服务器
npm run dev
```

## 相关文档

- [插件开发指南](./PLUGIN_DEVELOPMENT.md)
- [API 使用示例](./API.md)
- [配置说明](../backend/CONFIG.md)
- [部署指南](../DEPLOYMENT.md)

## 获取帮助

- 查看 [GitHub Issues](https://github.com/bilisheep/ExternalHound/issues)
- 参与 [Discussions](https://github.com/bilisheep/ExternalHound/discussions)
- 阅读现有代码和测试用例
