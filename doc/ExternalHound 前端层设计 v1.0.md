# ExternalHound 前端层设计 v1.0

**文档信息**
- 版本：v1.0
- 日期：2026-01-16
- 层次定位：前端展示层（Frontend Presentation Layer）
- 状态：设计方案

---

## 目录

1. [设计概述](#1-设计概述)
2. [技术栈选型](#2-技术栈选型)
3. [项目结构](#3-项目结构)
4. [路由与权限](#4-路由与权限)
5. [状态管理](#5-状态管理)
6. [API 集成](#6-api-集成)
7. [核心页面设计](#7-核心页面设计)
8. [图谱可视化](#8-图谱可视化)
9. [实时更新](#9-实时更新)
10. [安全措施](#10-安全措施)
11. [构建与部署](#11-构建与部署)

---

## 1. 设计概述

### 1.1 层次职责

前端层是 ExternalHound 系统的**用户交互层**，负责：

1. **数据可视化**：资产列表、统计图表、关系图谱展示
2. **用户交互**：资产管理、数据导入、查询搜索等操作
3. **权限控制**：后续版本考虑（v1.0 不包含用户与权限）
4. **实时更新**：导入进度、解析状态的实时推送
5. **响应式设计**：适配桌面端和移动端

### 1.2 设计原则

1. **组件化开发**：可复用的 UI 组件库
2. **类型安全**：使用 TypeScript 确保类型安全
3. **性能优先**：虚拟滚动、懒加载、代码分割
4. **用户体验**：流畅的交互、友好的错误提示
5. **安全第一**：XSS 防护、CSP 策略、输入净化

### 1.3 核心功能模块

```
┌─────────────────────────────────────────────────────────┐
│                    React Application                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Dashboard   │  │   Assets     │  │   Import     │ │
│  │   Module     │  │   Module     │  │   Module     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Graph     │  │   Search     │  │   Settings   │ │
│  │   Module     │  │   Module     │  │   Module     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│              State Management (Zustand)                 │
├─────────────────────────────────────────────────────────┤
│              API Client (Axios + React Query)           │
├─────────────────────────────────────────────────────────┤
│                    Backend API (FastAPI)                │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 技术栈选型

### 2.1 核心框架

- **React 18.2+**：主流前端框架
  - 并发渲染（Concurrent Rendering）
  - 自动批处理（Automatic Batching）
  - Suspense 支持
  - Server Components（可选）

### 2.2 开发语言

- **TypeScript 5.0+**：类型安全
  - 严格模式（strict mode）
  - 类型推断
  - 接口定义

### 2.3 构建工具

- **Vite 5.0+**：现代化构建工具
  - 快速的冷启动
  - 即时的模块热更新（HMR）
  - 优化的生产构建

### 2.4 UI 组件库

- **Ant Design 5.x**：企业级 UI 组件库
  - 丰富的组件
  - 完善的文档
  - TypeScript 支持
  - 主题定制

### 2.5 状态管理

- **Zustand**：轻量级状态管理
  - 简单的 API
  - 无需 Provider
  - TypeScript 友好
  - 中间件支持

### 2.6 数据请求

- **Axios**：HTTP 客户端
- **React Query (TanStack Query)**：服务端状态管理
  - 自动缓存
  - 后台重新验证
  - 乐观更新
  - 分页和无限滚动

### 2.7 路由管理

- **React Router 6.x**：声明式路由
  - 嵌套路由
  - 路由守卫
  - 懒加载

### 2.8 图谱可视化

- **G6 (AntV)**：图可视化引擎
  - 丰富的布局算法
  - 交互能力强
  - 性能优秀
  - 支持大规模数据

### 2.9 图表可视化

- **ECharts 5.x**：数据可视化库
  - 丰富的图表类型
  - 交互能力强
  - 主题定制

### 2.10 其他依赖

- **dayjs**：日期处理
- **lodash-es**：工具函数库
- **react-helmet-async**：文档头管理
- **ahooks**：React Hooks 库

---

## 3. 项目结构

```
frontend/
├── public/
│   ├── favicon.ico
│   └── index.html
│
├── src/
│   ├── assets/                    # 静态资源
│   │   ├── images/
│   │   ├── icons/
│   │   └── styles/
│   │       ├── global.css
│   │       ├── variables.css
│   │       └── antd-theme.css
│   │
│   ├── components/                # 通用组件
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── index.tsx
│   │   ├── AssetCard/
│   │   │   ├── IPCard.tsx
│   │   │   ├── DomainCard.tsx
│   │   │   ├── ServiceCard.tsx
│   │   │   └── index.tsx
│   │   ├── DataTable/
│   │   │   ├── DataTable.tsx
│   │   │   ├── TableFilter.tsx
│   │   │   └── index.tsx
│   │   ├── GraphViewer/
│   │   │   ├── GraphCanvas.tsx
│   │   │   ├── GraphToolbar.tsx
│   │   │   ├── GraphLegend.tsx
│   │   │   └── index.tsx
│   │   ├── FileUpload/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── UploadProgress.tsx
│   │   │   └── index.tsx
│   │   └── Common/
│   │       ├── Loading.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── EmptyState.tsx
│   │       └── ConfirmDialog.tsx
│   │
│   ├── pages/                     # 页面组件
│   │   ├── Dashboard/
│   │   │   ├── index.tsx
│   │   │   ├── StatisticsCard.tsx
│   │   │   └── RecentActivity.tsx
│   │   ├── Assets/
│   │   │   ├── IPList.tsx
│   │   │   ├── IPDetail.tsx
│   │   │   ├── DomainList.tsx
│   │   │   ├── DomainDetail.tsx
│   │   │   ├── ServiceList.tsx
│   │   │   ├── ServiceDetail.tsx
│   │   │   └── index.tsx
│   │   ├── Import/
│   │   │   ├── ImportList.tsx
│   │   │   ├── ImportDetail.tsx
│   │   │   ├── FileUploadPage.tsx
│   │   │   └── index.tsx
│   │   ├── Graph/
│   │   │   ├── GraphExplorer.tsx
│   │   │   ├── PathFinder.tsx
│   │   │   └── index.tsx
│   │   ├── Search/
│   │   │   ├── SearchPage.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   └── index.tsx
│   │   ├── Organizations/
│   │   │   ├── OrgList.tsx
│   │   │   ├── OrgDetail.tsx
│   │   │   └── index.tsx
│   │   ├── Auth/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── index.tsx
│   │   └── Settings/
│   │       ├── Profile.tsx
│   │       ├── Security.tsx
│   │       └── index.tsx
│   │
│   ├── hooks/                     # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   ├── useAssets.ts
│   │   ├── useImport.ts
│   │   ├── useGraph.ts
│   │   ├── useSearch.ts
│   │   └── useWebSocket.ts
│   │
│   ├── stores/                    # Zustand 状态管理
│   │   ├── authStore.ts
│   │   ├── assetStore.ts
│   │   ├── importStore.ts
│   │   ├── graphStore.ts
│   │   └── uiStore.ts
│   │
│   ├── services/                  # API 服务
│   │   ├── api/
│   │   │   ├── client.ts         # Axios 实例
│   │   │   ├── auth.ts
│   │   │   ├── assets.ts
│   │   │   ├── imports.ts
│   │   │   ├── queries.ts
│   │   │   └── organizations.ts
│   │   └── websocket/
│   │       ├── client.ts
│   │       └── handlers.ts
│   │
│   ├── types/                     # TypeScript 类型定义
│   │   ├── api.ts
│   │   ├── asset.ts
│   │   ├── import.ts
│   │   ├── graph.ts
│   │   └── user.ts
│   │
│   ├── utils/                     # 工具函数
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   ├── storage.ts
│   │   ├── security.ts
│   │   └── constants.ts
│   │
│   ├── router/                    # 路由配置
│   │   ├── index.tsx
│   │   ├── routes.tsx
│   │   └── guards.tsx
│   │
│   ├── App.tsx                    # 根组件
│   ├── main.tsx                   # 入口文件
│   └── vite-env.d.ts
│
├── .env.development               # 开发环境变量
├── .env.production                # 生产环境变量
├── .eslintrc.js                   # ESLint 配置
├── .prettierrc                    # Prettier 配置
├── tsconfig.json                  # TypeScript 配置
├── vite.config.ts                 # Vite 配置
├── package.json
└── README.md
```

---

## 4. TypeScript 类型定义

### 4.1 API 响应类型

```typescript
// src/types/api.ts

/**
 * 通用分页响应
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * 通用 API 响应
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}
```

### 4.2 资产类型

```typescript
// src/types/asset.ts

/**
 * 范围策略
 */
export type ScopePolicy = 'IN_SCOPE' | 'OUT_OF_SCOPE';

/**
 * 资产基础字段
 */
export interface AssetBase {
  id: string;
  external_id: string;
  created_at: string;
  updated_at: string;
  created_by?: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
}

/**
 * IP 资产
 */
export interface IPAsset extends AssetBase {
  address: string;
  version: 4 | 6;
  is_cloud: boolean;
  is_internal: boolean;
  is_cdn: boolean;
  open_ports_count: number;
  risk_score: number;
  vuln_critical_count: number;
  country_code?: string | null;
  asn_number?: string | null;
  scope_policy: ScopePolicy;
  metadata: Record<string, any>;
}

/**
 * IP 更新字段
 */
export interface IPUpdatePayload {
  is_cloud?: boolean;
  is_internal?: boolean;
  is_cdn?: boolean;
  open_ports_count?: number;
  risk_score?: number;
  vuln_critical_count?: number;
  country_code?: string | null;
  asn_number?: string | null;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, any>;
}

/**
 * 域名资产
 */
export interface DomainAsset extends AssetBase {
  name: string;
  root_domain?: string | null;
  tier: number;
  is_resolved: boolean;
  is_wildcard: boolean;
  is_internal: boolean;
  has_waf: boolean;
  scope_policy: ScopePolicy;
  metadata: Record<string, any>;
}

/**
 * 服务资产
 */
export interface ServiceAsset extends AssetBase {
  service_name?: string | null;
  port: number;
  protocol: 'TCP' | 'UDP';
  product?: string | null;
  version?: string | null;
  banner?: string | null;
  is_http: boolean;
  risk_score: number;
  asset_category?: string | null;
  scope_policy: ScopePolicy;
  metadata: Record<string, any>;
}

/**
 * 资产列表响应
 */
export type AssetListResponse<T> = PaginatedResponse<T>;
```

### 4.3 导入类型

```typescript
// src/types/import.ts

/**
 * 导入状态
 */
export type ImportStatus = 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';

/**
 * 导入记录
 */
export interface ImportLog {
  id: string;
  filename: string;
  file_size: number;
  format: string;
  status: ImportStatus;
  progress: number;
  records_total: number;
  records_success: number;
  records_failed: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
}

/**
 * 导入列表响应
 */
export type ImportListResponse = PaginatedResponse<ImportLog>;
```

### 4.4 统计类型

```typescript
// src/types/statistics.ts

/**
 * 统计概览
 */
export interface StatisticsOverview {
  total_ips: number;
  total_domains: number;
  total_services: number;
  high_risk_count: number;
  in_scope_count: number;
  total_assets: number;
  cloud_count: number;
  ip_trend?: number;
  domain_trend?: number;
  service_trend?: number;
  risk_trend?: number;
}
```

### 4.5 图谱类型

```typescript
// src/types/graph.ts

/**
 * 图节点
 */
export interface GraphNode {
  id: string;
  label: string;
  type: 'IP' | 'Domain' | 'Service' | 'Organization' | 'Certificate' | 'Netblock' | 'ClientApplication' | 'Credential';
  properties: Record<string, any>;
}

/**
 * 图边
 */
export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

/**
 * 图数据
 */
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
```

---

## 5. 路由与认证

> 说明：v1.0 不包含用户与权限控制，下述认证/鉴权相关内容为后续版本预留示例。

### 4.1 路由配置

```typescript
// src/router/routes.tsx
import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';
import { AuthGuard } from './guards';
import Layout from '@/components/Layout';

// 懒加载页面组件
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const IPList = lazy(() => import('@/pages/Assets/IPList'));
const IPDetail = lazy(() => import('@/pages/Assets/IPDetail'));
const DomainList = lazy(() => import('@/pages/Assets/DomainList'));
const DomainDetail = lazy(() => import('@/pages/Assets/DomainDetail'));
const ServiceList = lazy(() => import('@/pages/Assets/ServiceList'));
const ServiceDetail = lazy(() => import('@/pages/Assets/ServiceDetail'));
const ImportList = lazy(() => import('@/pages/Import/ImportList'));
const ImportDetail = lazy(() => import('@/pages/Import/ImportDetail'));
const GraphExplorer = lazy(() => import('@/pages/Graph/GraphExplorer'));
const SearchPage = lazy(() => import('@/pages/Search/SearchPage'));
const OrgList = lazy(() => import('@/pages/Organizations/OrgList'));
const OrgDetail = lazy(() => import('@/pages/Organizations/OrgDetail'));
const Settings = lazy(() => import('@/pages/Settings'));
const Login = lazy(() => import('@/pages/Auth/Login'));
const NotFound = lazy(() => import('@/pages/Errors/NotFound'));
const Forbidden = lazy(() => import('@/pages/Errors/Forbidden'));
const ServerError = lazy(() => import('@/pages/Errors/ServerError'));

export const routes: RouteObject[] = [
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <Layout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'assets',
        children: [
          {
            path: 'ips',
            element: (
              <AuthGuard>
                <IPList />
              </AuthGuard>
            ),
          },
          {
            path: 'ips/:address',
            element: (
              <AuthGuard>
                <IPDetail />
              </AuthGuard>
            ),
          },
          {
            path: 'domains',
            element: (
              <AuthGuard>
                <DomainList />
              </AuthGuard>
            ),
          },
          {
            path: 'domains/:name',
            element: (
              <AuthGuard>
                <DomainDetail />
              </AuthGuard>
            ),
          },
          {
            path: 'services',
            element: (
              <AuthGuard>
                <ServiceList />
              </AuthGuard>
            ),
          },
          {
            path: 'services/:id',
            element: (
              <AuthGuard>
                <ServiceDetail />
              </AuthGuard>
            ),
          },
        ],
      },
      {
        path: 'import',
        children: [
          {
            index: true,
            element: (
              <AuthGuard>
                <ImportList />
              </AuthGuard>
            ),
          },
          {
            path: ':id',
            element: (
              <AuthGuard>
                <ImportDetail />
              </AuthGuard>
            ),
          },
        ],
      },
      {
        path: 'graph',
        element: (
          <AuthGuard>
            <GraphExplorer />
          </AuthGuard>
        ),
      },
      {
        path: 'search',
        element: (
          <AuthGuard>
            <SearchPage />
          </AuthGuard>
        ),
      },
      {
        path: 'organizations',
        children: [
          {
            index: true,
            element: (
              <AuthGuard>
                <OrgList />
              </AuthGuard>
            ),
          },
          {
            path: ':id',
            element: (
              <AuthGuard>
                <OrgDetail />
              </AuthGuard>
            ),
          },
        ],
      },
      {
        path: 'settings',
        element: (
          <AuthGuard>
            <Settings />
          </AuthGuard>
        ),
      },
    ],
  },
  // 错误页面路由
  {
    path: '/403',
    element: <Forbidden />,
  },
  {
    path: '/500',
    element: <ServerError />,
  },
  {
    path: '*',
    element: <NotFound />,
  },
];
```

### 4.2 路由守卫

```typescript
// src/router/guards.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { ReactNode } from 'react';

interface AuthGuardProps {
  children: ReactNode;
}

export const AuthGuard = ({ children }: AuthGuardProps) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  // 未登录，重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
```

---

## 5. 状态管理

### 5.1 认证状态

```typescript
// src/stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  email: string;
  isActive: boolean;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  // Actions
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: (accessToken, refreshToken, user) => {
        set({
          accessToken,
          refreshToken,
          user,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      updateUser: (user) => {
        set({ user });
      },

    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

### 5.2 UI 状态

```typescript
// src/stores/uiStore.ts
import { create } from 'zustand';

interface UIState {
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  loading: boolean;

  // Actions
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  theme: 'light',
  loading: false,

  toggleSidebar: () => set((state) => ({
    sidebarCollapsed: !state.sidebarCollapsed
  })),

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  setTheme: (theme) => set({ theme }),

  setLoading: (loading) => set({ loading }),
}));
```

### 5.3 图谱状态

```typescript
// src/stores/graphStore.ts
import { create } from 'zustand';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  layout: 'force' | 'dagre' | 'circular';

  // Actions
  setGraphData: (nodes: GraphNode[], edges: GraphEdge[]) => void;
  selectNode: (node: GraphNode | null) => void;
  setLayout: (layout: 'force' | 'dagre' | 'circular') => void;
  clearGraph: () => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  layout: 'force',

  setGraphData: (nodes, edges) => set({ nodes, edges }),

  selectNode: (node) => set({ selectedNode: node }),

  setLayout: (layout) => set({ layout }),

  clearGraph: () => set({
    nodes: [],
    edges: [],
    selectedNode: null
  }),
}));
```

---

## 6. API 集成

### 6.1 Axios 客户端配置

```typescript
// src/services/api/client.ts
import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { message } from 'antd';
import { useAuthStore } from '@/stores/authStore';

// 创建 Axios 实例
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token 刷新队列，防止并发刷新
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

// 添加到刷新队列
const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback);
};

// 通知所有等待的请求
const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
};

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证令牌
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const { response, config } = error;

    if (!response) {
      message.error('网络错误，请检查网络连接');
      return Promise.reject(error);
    }

    // 处理不同的错误状态码
    switch (response.status) {
      case 401:
        // 未授权，尝试刷新令牌
        const { refreshToken, logout } = useAuthStore.getState();

        if (!refreshToken) {
          logout();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // 如果正在刷新，将请求加入队列
        if (isRefreshing) {
          return new Promise((resolve) => {
            subscribeTokenRefresh((token: string) => {
              if (config) {
                config.headers!.Authorization = `Bearer ${token}`;
                resolve(apiClient.request(config));
              }
            });
          });
        }

        isRefreshing = true;

        try {
          // 使用 apiClient 刷新令牌，确保使用正确的 baseURL
          const { data } = await apiClient.post('/auth/refresh', {
            refresh_token: refreshToken,
          });

          // 更新令牌
          useAuthStore.getState().login(
            data.access_token,
            data.refresh_token,
            useAuthStore.getState().user!
          );

          // 通知所有等待的请求
          onRefreshed(data.access_token);

          // 重试原请求
          if (config) {
            config.headers!.Authorization = `Bearer ${data.access_token}`;
            return apiClient.request(config);
          }
        } catch (refreshError) {
          // 刷新失败，清理状态并登出
          logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
        break;

      case 403:
        message.error('权限不足');
        break;

      case 404:
        message.error('请求的资源不存在');
        break;

      case 500:
        message.error('服务器错误，请稍后重试');
        break;

      default:
        message.error(response.data?.message || '请求失败');
    }

    return Promise.reject(error);
  }
);
```

### 6.2 API 服务封装

```typescript
// src/services/api/assets.ts
import { apiClient } from './client';
import {
  IPAsset,
  DomainAsset,
  ServiceAsset,
  AssetListResponse,
  IPUpdatePayload,
  ScopePolicy,
} from '@/types/asset';

export const assetsApi = {
  // 获取 IP 列表
  getIPs: async (params: {
    page?: number;
    page_size?: number;
    version?: 4 | 6;
    is_cloud?: boolean;
    is_internal?: boolean;
    is_cdn?: boolean;
    country_code?: string;
    scope_policy?: ScopePolicy;
  }): Promise<AssetListResponse<IPAsset>> => {
    const { data } = await apiClient.get('/ips', { params });
    return data;
  },

  // 获取 IP 详情（通过地址）
  getIPDetail: async (address: string): Promise<IPAsset> => {
    const { data } = await apiClient.get(`/ips/address/${address}`);
    return data;
  },

  // 更新 IP
  updateIP: async (id: string, payload: IPUpdatePayload): Promise<IPAsset> => {
    const { data } = await apiClient.put(`/ips/${id}`, payload);
    return data;
  },

  // 删除 IP
  deleteIP: async (id: string): Promise<void> => {
    await apiClient.delete(`/ips/${id}`);
  },

  // 获取域名列表
  getDomains: async (params: {
    page?: number;
    page_size?: number;
    tier?: number;
    is_resolved?: boolean;
    is_wildcard?: boolean;
    has_waf?: boolean;
    scope_policy?: ScopePolicy;
  }): Promise<AssetListResponse<DomainAsset>> => {
    const { data } = await apiClient.get('/domains', { params });
    return data;
  },

  // 获取域名详情（通过名称）
  getDomainDetail: async (name: string): Promise<DomainAsset> => {
    const { data } = await apiClient.get(`/domains/name/${name}`);
    return data;
  },

  // 获取服务列表
  getServices: async (params: {
    page?: number;
    page_size?: number;
    port?: number;
    protocol?: 'TCP' | 'UDP';
    is_http?: boolean;
    asset_category?: string;
    scope_policy?: ScopePolicy;
  }): Promise<AssetListResponse<ServiceAsset>> => {
    const { data } = await apiClient.get('/services', { params });
    return data;
  },

  // 获取服务详情
  getServiceDetail: async (id: string): Promise<ServiceAsset> => {
    const { data } = await apiClient.get(`/services/${id}`);
    return data;
  },
};
```

### 6.3 React Query 集成

```typescript
// src/hooks/useAssets.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assetsApi } from '@/services/api/assets';
import type { ScopePolicy } from '@/types/asset';
import { message } from 'antd';

// 获取 IP 列表
export const useIPList = (params: {
  page?: number;
  page_size?: number;
  version?: 4 | 6;
  is_cloud?: boolean;
  is_internal?: boolean;
  is_cdn?: boolean;
  country_code?: string;
  scope_policy?: ScopePolicy;
}) => {
  return useQuery({
    queryKey: ['ips', params],
    queryFn: () => assetsApi.getIPs(params),
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 获取 IP 详情
export const useIPDetail = (address: string) => {
  return useQuery({
    queryKey: ['ip', address],
    queryFn: () => assetsApi.getIPDetail(address),
    enabled: !!address,
  });
};

// 更新 IP 范围策略
export const useUpdateIPScope = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, scopePolicy }: { id: string; scopePolicy: ScopePolicy }) =>
      assetsApi.updateIP(id, { scope_policy: scopePolicy }),
    onSuccess: () => {
      message.success('范围策略更新成功');
      queryClient.invalidateQueries({ queryKey: ['ip'] });
      queryClient.invalidateQueries({ queryKey: ['ips'] });
    },
    onError: () => {
      message.error('范围策略更新失败');
    },
  });
};

// 删除 IP
export const useDeleteIP = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteIP(id),
    onSuccess: () => {
      message.success('IP 删除成功');
      queryClient.invalidateQueries({ queryKey: ['ips'] });
    },
    onError: () => {
      message.error('IP 删除失败');
    },
  });
};
```

---

## 7. 核心页面设计

### 7.1 Dashboard 页面

```typescript
// src/pages/Dashboard/index.tsx
import { Row, Col, Card, Statistic, Table, Tag } from 'antd';
import {
  DatabaseOutlined,
  GlobalOutlined,
  ApiOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { assetsApi } from '@/services/api/assets';
import StatisticsCard from './StatisticsCard';
import RecentActivity from './RecentActivity';

const Dashboard = () => {
  // 获取统计数据
  const { data: stats, isLoading } = useQuery({
    queryKey: ['statistics', 'overview'],
    queryFn: () => assetsApi.getStatistics(),
    refetchInterval: 30000, // 30秒刷新一次
  });

  return (
    <div className="dashboard">
      <Row gutter={[16, 16]}>
        {/* 统计卡片 */}
        <Col xs={24} sm={12} lg={6}>
          <StatisticsCard
            title="IP 资产"
            value={stats?.total_ips || 0}
            icon={<DatabaseOutlined />}
            color="#1890ff"
            trend={stats?.ip_trend}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatisticsCard
            title="域名资产"
            value={stats?.total_domains || 0}
            icon={<GlobalOutlined />}
            color="#52c41a"
            trend={stats?.domain_trend}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatisticsCard
            title="服务资产"
            value={stats?.total_services || 0}
            icon={<ApiOutlined />}
            color="#722ed1"
            trend={stats?.service_trend}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatisticsCard
            title="高危资产"
            value={stats?.high_risk_count || 0}
            icon={<WarningOutlined />}
            color="#ff4d4f"
            trend={stats?.risk_trend}
          />
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={16}>
          <Card title="最近导入" bordered={false}>
            <RecentActivity />
          </Card>
        </Col>

        {/* 资产分布 */}
        <Col xs={24} lg={8}>
          <Card title="资产分布" bordered={false}>
            <Statistic
              title="范围内资产"
              value={stats?.in_scope_count || 0}
              suffix={`/ ${stats?.total_assets || 0}`}
            />
            <Statistic
              title="云资产"
              value={stats?.cloud_count || 0}
              suffix={`/ ${stats?.total_ips || 0}`}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
```

### 7.2 IP 资产列表页面

```typescript
// src/pages/Assets/IPList.tsx
import { useState } from 'react';
import { Table, Button, Space, Tag, Input, Select, Popconfirm } from 'antd';
import { SearchOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useIPList, useDeleteIP } from '@/hooks/useAssets';
import type { IPAsset } from '@/types/asset';

const IPList = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    scope_policy: undefined,
    is_cloud: undefined,
    country_code: undefined,
  });

  // 获取 IP 列表
  const { data, isLoading, refetch } = useIPList({
    page,
    page_size: pageSize,
    ...filters,
  });

  // 删除 IP
  const deleteMutation = useDeleteIP();

  const columns = [
    {
      title: 'IP 地址',
      dataIndex: 'address',
      key: 'address',
      render: (address: string) => (
        <a onClick={() => navigate(`/assets/ips/${address}`)}>
          {address}
        </a>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (version: number) => `IPv${version}`,
    },
    {
      title: '范围策略',
      dataIndex: 'scope_policy',
      key: 'scope_policy',
      width: 120,
      render: (policy: string) => {
        const colorMap = {
          IN_SCOPE: 'green',
          OUT_OF_SCOPE: 'red',
        };
        return <Tag color={colorMap[policy]}>{policy}</Tag>;
      },
    },
    {
      title: '类型',
      key: 'type',
      width: 150,
      render: (record: IPAsset) => (
        <Space>
          {record.is_cloud && <Tag color="blue">云资产</Tag>}
          {record.is_cdn && <Tag color="purple">CDN</Tag>}
          {record.is_internal && <Tag>内网</Tag>}
        </Space>
      ),
    },
    {
      title: '国家',
      dataIndex: 'country_code',
      key: 'country_code',
      width: 80,
    },
    {
      title: 'ASN',
      dataIndex: 'asn_number',
      key: 'asn_number',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (record: IPAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/assets/ips/${record.address}`)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定删除此 IP？"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="ip-list">
      {/* 过滤器 */}
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="范围策略"
          style={{ width: 150 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, scope_policy: value })}
        >
          <Select.Option value="IN_SCOPE">IN_SCOPE</Select.Option>
          <Select.Option value="OUT_OF_SCOPE">OUT_OF_SCOPE</Select.Option>
        </Select>

        <Select
          placeholder="资产类型"
          style={{ width: 120 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_cloud: value })}
        >
          <Select.Option value={true}>云资产</Select.Option>
          <Select.Option value={false}>非云资产</Select.Option>
        </Select>

        <Input
          placeholder="国家代码"
          style={{ width: 120 }}
          allowClear
          onChange={(e) => setFilters({ ...filters, country_code: e.target.value })}
        />

        <Button icon={<SearchOutlined />} type="primary">
          搜索
        </Button>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
          刷新
        </Button>
      </Space>

      {/* 表格 */}
      <Table
        columns={columns}
        dataSource={data?.items || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize: pageSize,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => {
            setPage(page);
            setPageSize(pageSize);
          },
        }}
      />
    </div>
  );
};

export default IPList;
```

### 7.3 IP 资产详情页面

```typescript
// src/pages/Assets/IPDetail.tsx
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Tag, Space, Button, Tabs, Table, Empty } from 'antd';
import { EditOutlined, GlobalOutlined } from '@ant-design/icons';
import { useIPDetail } from '@/hooks/useAssets';

const IPDetail = () => {
  const { address } = useParams<{ address: string }>();
  const { data: ipAsset, isLoading } = useIPDetail(address!);

  if (isLoading) {
    return <Card loading />;
  }

  if (!ipAsset) {
    return <Empty description="IP 资产不存在" />;
  }

  return (
    <div className="ip-detail">
      {/* 基本信息 */}
      <Card
        title={`IP 资产详情: ${ipAsset.address}`}
        extra={
          <Button type="primary" icon={<EditOutlined />}>
            编辑
          </Button>
        }
      >
        <Descriptions column={2}>
          <Descriptions.Item label="IP 地址">{ipAsset.address}</Descriptions.Item>
          <Descriptions.Item label="版本">IPv{ipAsset.version}</Descriptions.Item>
          <Descriptions.Item label="范围策略">
            <Tag color={ipAsset.scope_policy === 'IN_SCOPE' ? 'green' : 'red'}>
              {ipAsset.scope_policy}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="资产类型">
            <Space>
              {ipAsset.is_cloud && <Tag color="blue">云资产</Tag>}
              {ipAsset.is_cdn && <Tag color="purple">CDN</Tag>}
              {ipAsset.is_internal && <Tag>内网</Tag>}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="国家">{ipAsset.country_code}</Descriptions.Item>
          <Descriptions.Item label="ASN">{ipAsset.asn_number}</Descriptions.Item>
          <Descriptions.Item label="开放端口">{ipAsset.open_ports_count}</Descriptions.Item>
          <Descriptions.Item label="风险评分">{ipAsset.risk_score}</Descriptions.Item>
          <Descriptions.Item label="严重漏洞">{ipAsset.vuln_critical_count}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{ipAsset.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 详细信息标签页 */}
      <Card style={{ marginTop: 16 }}>
        <Tabs
          items={[
            {
              key: 'services',
              label: '服务列表',
              children: <ServiceTable ipAddress={ipAsset.address} />,
            },
            {
              key: 'domains',
              label: '关联域名',
              children: <DomainTable ipAddress={ipAsset.address} />,
            },
            {
              key: 'metadata',
              label: '元数据',
              children: <pre>{JSON.stringify(ipAsset.metadata, null, 2)}</pre>,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default IPDetail;
```

### 7.4 数据导入页面

```typescript
// src/pages/Import/ImportList.tsx
import { useState } from 'react';
import { Table, Button, Space, Tag, Progress, Modal } from 'antd';
import { UploadOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { importsApi } from '@/services/api/imports';
import FileUploadModal from './FileUploadModal';
import dayjs from 'dayjs';

const ImportList = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);

  // 获取导入记录列表
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['imports', page, pageSize],
    queryFn: () => importsApi.getImportList({ page, page_size: pageSize }),
  });

  // 使用 WebSocket 监听导入进度更新
  useWebSocket('import:progress', (progressData) => {
    // 当收到导入进度更新时，刷新列表
    refetch();
  });

  // 监听导入完成事件
  useWebSocket('import:complete', (completeData) => {
    // 导入完成时刷新列表
    refetch();
  });

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename: string, record: any) => (
        <a onClick={() => navigate(`/import/${record.id}`)}>
          {filename}
        </a>
      ),
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 100,
      render: (format: string) => <Tag>{format.toUpperCase()}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const colorMap = {
          PENDING: 'default',
          PROCESSING: 'processing',
          SUCCESS: 'success',
          FAILED: 'error',
        };
        return <Tag color={colorMap[status]}>{status}</Tag>;
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: any) => {
        if (record.status === 'PROCESSING') {
          return <Progress percent={progress} size="small" />;
        }
        return record.status === 'SUCCESS' ? '100%' : '-';
      },
    },
    {
      title: '成功记录',
      dataIndex: 'records_success',
      key: 'records_success',
      width: 100,
    },
    {
      title: '失败记录',
      dataIndex: 'records_failed',
      key: 'records_failed',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (record: any) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/import/${record.id}`)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div className="import-list">
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => setUploadModalVisible(true)}
        >
          上传文件
        </Button>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
          刷新
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize: pageSize,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => {
            setPage(page);
            setPageSize(pageSize);
          },
        }}
      />

      {/* 文件上传弹窗 */}
      <FileUploadModal
        visible={uploadModalVisible}
        onClose={() => setUploadModalVisible(false)}
        onSuccess={() => {
          setUploadModalVisible(false);
          refetch();
        }}
      />
    </div>
  );
};

export default ImportList;
```

### 7.5 文件上传组件

```typescript
// src/pages/Import/FileUploadModal.tsx
import { useState } from 'react';
import { Modal, Upload, Form, Select, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { importsApi } from '@/services/api/imports';
import type { UploadFile } from 'antd/es/upload/interface';

interface FileUploadModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const FileUploadModal = ({ visible, onClose, onSuccess }: FileUploadModalProps) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // 文件上传 mutation
  const uploadMutation = useMutation({
    mutationFn: (data: FormData) => importsApi.uploadFile(data),
    onSuccess: () => {
      message.success('文件上传成功，开始解析');
      form.resetFields();
      setFileList([]);
      onSuccess();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '文件上传失败');
    },
  });

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (fileList.length === 0) {
        message.error('请选择要上传的文件');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileList[0].originFileObj as Blob);
      if (values.parser_type) {
        formData.append('parser_type', values.parser_type);
      }
      if (values.organization_id) {
        formData.append('organization_id', values.organization_id);
      }

      uploadMutation.mutate(formData);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  return (
    <Modal
      title="上传导入文件"
      open={visible}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={uploadMutation.isPending}
      width={600}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="file"
          label="选择文件"
          rules={[{ required: true, message: '请选择文件' }]}
        >
          <Upload.Dragger
            name="file"
            multiple={false}
            fileList={fileList}
            beforeUpload={(file) => {
              setFileList([file]);
              return false; // 阻止自动上传
            }}
            onRemove={() => {
              setFileList([]);
            }}
            accept=".xml,.json,.jsonl,.txt"
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持格式：Nmap XML、Masscan JSON、Subfinder JSON、Nuclei JSONL
            </p>
          </Upload.Dragger>
        </Form.Item>

        <Form.Item
          name="parser_type"
          label="解析器类型"
          tooltip="留空则自动检测"
        >
          <Select placeholder="自动检测" allowClear>
            <Select.Option value="nmap">Nmap XML</Select.Option>
            <Select.Option value="masscan">Masscan JSON</Select.Option>
            <Select.Option value="subfinder">Subfinder JSON</Select.Option>
            <Select.Option value="nuclei">Nuclei JSONL</Select.Option>
            <Select.Option value="httpx">Httpx JSON</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="organization_id"
          label="关联组织"
          tooltip="可选，将资产关联到指定组织"
        >
          <Select placeholder="选择组织" allowClear>
            {/* 这里应该从 API 获取组织列表 */}
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default FileUploadModal;
```

### 7.6 错误页面组件

```typescript
// src/pages/Errors/NotFound.tsx
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Result
      status="404"
      title="404"
      subTitle="抱歉，您访问的页面不存在"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      }
    />
  );
};

export default NotFound;
```

```typescript
// src/pages/Errors/Forbidden.tsx
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const Forbidden = () => {
  const navigate = useNavigate();

  return (
    <Result
      status="403"
      title="403"
      subTitle="抱歉，您没有权限访问此页面"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      }
    />
  );
};

export default Forbidden;
```

```typescript
// src/pages/Errors/ServerError.tsx
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const ServerError = () => {
  const navigate = useNavigate();

  return (
    <Result
      status="500"
      title="500"
      subTitle="抱歉，服务器出现错误"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      }
    />
  );
};

export default ServerError;
```

---

## 8. 图谱可视化

### 8.1 G6 图谱组件

```typescript
// src/components/GraphViewer/GraphCanvas.tsx
import { useEffect, useRef } from 'react';
import G6, { Graph, GraphData } from '@antv/g6';
import { useGraphStore } from '@/stores/graphStore';

interface GraphCanvasProps {
  data: GraphData;
  onNodeClick?: (node: any) => void;
  layout?: 'force' | 'dagre' | 'circular';
}

// 全局标志，确保自定义节点只注册一次
let customNodesRegistered = false;

const GraphCanvas = ({ data, onNodeClick, layout = 'force' }: GraphCanvasProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const { selectNode } = useGraphStore();

  // 在组件挂载时注册自定义节点（只注册一次）
  useEffect(() => {
    if (!customNodesRegistered) {
      registerCustomNodes();
      customNodesRegistered = true;
    }
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    // 初始化 G6 图实例
    const graph = new G6.Graph({
      container: containerRef.current,
      width: containerRef.current.offsetWidth,
      height: containerRef.current.offsetHeight,
      modes: {
        default: [
          'drag-canvas',
          'zoom-canvas',
          'drag-node',
          'click-select',
        ],
      },
      layout: getLayoutConfig(layout),
      defaultNode: {
        size: 40,
        style: {
          fill: '#5B8FF9',
          stroke: '#5B8FF9',
          lineWidth: 2,
        },
        labelCfg: {
          style: {
            fill: '#000',
            fontSize: 12,
          },
        },
      },
      defaultEdge: {
        style: {
          stroke: '#e2e2e2',
          lineWidth: 2,
          endArrow: {
            path: G6.Arrow.triangle(10, 12, 0),
            fill: '#e2e2e2',
          },
        },
        labelCfg: {
          autoRotate: true,
          style: {
            fill: '#666',
            fontSize: 10,
          },
        },
      },
      nodeStateStyles: {
        selected: {
          stroke: '#1890ff',
          lineWidth: 3,
        },
        hover: {
          stroke: '#40a9ff',
          lineWidth: 2.5,
        },
      },
    });

    // 绑定事件
    graph.on('node:click', (evt) => {
      const { item } = evt;
      const model = item?.getModel();
      if (model) {
        selectNode(model as any);
        onNodeClick?.(model);
      }
    });

    graph.on('node:mouseenter', (evt) => {
      const { item } = evt;
      graph.setItemState(item!, 'hover', true);
    });

    graph.on('node:mouseleave', (evt) => {
      const { item } = evt;
      graph.setItemState(item!, 'hover', false);
    });

    // 加载数据
    graph.data(data);
    graph.render();

    graphRef.current = graph;

    // 自适应画布
    graph.fitView();

    // 清理函数
    return () => {
      graph.destroy();
    };
  }, [data, layout]);

  // 响应式调整画布大小
  useEffect(() => {
    const handleResize = () => {
      if (graphRef.current && containerRef.current) {
        graphRef.current.changeSize(
          containerRef.current.offsetWidth,
          containerRef.current.offsetHeight
        );
        graphRef.current.fitView();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

// 获取布局配置
const getLayoutConfig = (layout: string) => {
  switch (layout) {
    case 'force':
      return {
        type: 'force',
        preventOverlap: true,
        nodeSpacing: 50,
        linkDistance: 150,
      };
    case 'dagre':
      return {
        type: 'dagre',
        rankdir: 'LR',
        nodesep: 50,
        ranksep: 100,
      };
    case 'circular':
      return {
        type: 'circular',
        radius: 300,
        startRadius: 100,
        endRadius: 300,
      };
    default:
      return { type: 'force' };
  }
};

// 注册自定义节点样式
const registerCustomNodes = () => {
  // IP 节点
  G6.registerNode('ip-node', {
    draw(cfg, group) {
      const shape = group!.addShape('circle', {
        attrs: {
          x: 0,
          y: 0,
          r: 25,
          fill: '#5B8FF9',
          stroke: '#5B8FF9',
          lineWidth: 2,
        },
        name: 'ip-circle',
      });

      // 添加图标
      group!.addShape('text', {
        attrs: {
          x: 0,
          y: 0,
          textAlign: 'center',
          textBaseline: 'middle',
          text: '🖥️',
          fontSize: 20,
        },
        name: 'ip-icon',
      });

      // 添加标签
      group!.addShape('text', {
        attrs: {
          x: 0,
          y: 35,
          textAlign: 'center',
          text: cfg!.label,
          fontSize: 12,
          fill: '#000',
        },
        name: 'ip-label',
      });

      return shape;
    },
  });

  // Domain 节点
  G6.registerNode('domain-node', {
    draw(cfg, group) {
      const shape = group!.addShape('circle', {
        attrs: {
          x: 0,
          y: 0,
          r: 25,
          fill: '#52C41A',
          stroke: '#52C41A',
          lineWidth: 2,
        },
        name: 'domain-circle',
      });

      group!.addShape('text', {
        attrs: {
          x: 0,
          y: 0,
          textAlign: 'center',
          textBaseline: 'middle',
          text: '🌐',
          fontSize: 20,
        },
        name: 'domain-icon',
      });

      group!.addShape('text', {
        attrs: {
          x: 0,
          y: 35,
          textAlign: 'center',
          text: cfg!.label,
          fontSize: 12,
          fill: '#000',
        },
        name: 'domain-label',
      });

      return shape;
    },
  });

  // Service 节点
  G6.registerNode('service-node', {
    draw(cfg, group) {
      const shape = group!.addShape('rect', {
        attrs: {
          x: -20,
          y: -20,
          width: 40,
          height: 40,
          radius: 5,
          fill: '#722ED1',
          stroke: '#722ED1',
          lineWidth: 2,
        },
        name: 'service-rect',
      });

      group!.addShape('text', {
        attrs: {
          x: 0,
          y: 0,
          textAlign: 'center',
          textBaseline: 'middle',
          text: '⚙️',
          fontSize: 20,
        },
        name: 'service-icon',
      });

      group!.addShape('text', {
        attrs: {
          x: 0,
          y: 35,
          textAlign: 'center',
          text: cfg!.label,
          fontSize: 12,
          fill: '#000',
        },
        name: 'service-label',
      });

      return shape;
    },
  });
};

export default GraphCanvas;
```

### 8.2 图谱工具栏

```typescript
// src/components/GraphViewer/GraphToolbar.tsx
import { Space, Button, Select, Tooltip } from 'antd';
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  FullscreenOutlined,
  ReloadOutlined,
  DownloadOutlined,
} from '@ant-design/icons';

interface GraphToolbarProps {
  layout: string;
  onLayoutChange: (layout: string) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  onRefresh: () => void;
  onExport: () => void;
}

const GraphToolbar = ({
  layout,
  onLayoutChange,
  onZoomIn,
  onZoomOut,
  onFitView,
  onRefresh,
  onExport,
}: GraphToolbarProps) => {
  return (
    <div className="graph-toolbar" style={{ padding: '12px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
      <Space>
        <Select
          value={layout}
          onChange={onLayoutChange}
          style={{ width: 120 }}
        >
          <Select.Option value="force">力导向布局</Select.Option>
          <Select.Option value="dagre">层次布局</Select.Option>
          <Select.Option value="circular">环形布局</Select.Option>
        </Select>

        <Tooltip title="放大">
          <Button icon={<ZoomInOutlined />} onClick={onZoomIn} />
        </Tooltip>

        <Tooltip title="缩小">
          <Button icon={<ZoomOutOutlined />} onClick={onZoomOut} />
        </Tooltip>

        <Tooltip title="适应画布">
          <Button icon={<FullscreenOutlined />} onClick={onFitView} />
        </Tooltip>

        <Tooltip title="刷新">
          <Button icon={<ReloadOutlined />} onClick={onRefresh} />
        </Tooltip>

        <Tooltip title="导出图片">
          <Button icon={<DownloadOutlined />} onClick={onExport} />
        </Tooltip>
      </Space>
    </div>
  );
};

export default GraphToolbar;
```

---

## 9. 实时更新

### 9.1 WebSocket 客户端

```typescript
// src/services/websocket/client.ts
import { useAuthStore } from '@/stores/authStore';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private handlers: Map<string, Set<Function>> = new Map();
  private url: string = '';
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private heartbeatTimeout: NodeJS.Timeout | null = null;
  private readonly HEARTBEAT_INTERVAL = 30000; // 30秒发送一次心跳
  private readonly HEARTBEAT_TIMEOUT = 5000; // 5秒内未收到响应视为超时
  private subscriptions: Set<string> = new Set(); // 记录已订阅的事件，用于重连后恢复

  connect(url: string) {
    this.url = url;
    const { accessToken } = useAuthStore.getState();

    // 建立 WebSocket 连接，携带 token
    this.ws = new WebSocket(`${url}?token=${accessToken}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;

      // 启动心跳机制
      this.startHeartbeat();

      // 恢复订阅
      this.recoverSubscriptions();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        // 处理心跳响应
        if (message.type === 'pong') {
          this.handlePong();
          return;
        }

        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason);

      // 停止心跳
      this.stopHeartbeat();

      // 尝试重连
      this.attemptReconnect();
    };
  }

  private startHeartbeat() {
    // 清除旧的心跳定时器
    this.stopHeartbeat();

    // 定期发送心跳
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping', {});

        // 设置心跳超时检测
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('Heartbeat timeout, reconnecting...');
          this.ws?.close();
        }, this.HEARTBEAT_TIMEOUT);
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  private handlePong() {
    // 收到心跳响应，清除超时定时器
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  private recoverSubscriptions() {
    // 重连后恢复所有订阅
    this.subscriptions.forEach((event) => {
      this.send('subscribe', { event });
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => {
        // 检查 token 是否过期，如果过期则刷新
        this.refreshTokenAndReconnect();
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private async refreshTokenAndReconnect() {
    const { accessToken, refreshToken, isAuthenticated } = useAuthStore.getState();

    if (!isAuthenticated || !refreshToken) {
      console.error('Not authenticated, cannot reconnect');
      return;
    }

    try {
      // 尝试刷新 token
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();

        // 更新 token
        useAuthStore.getState().login(
          data.access_token,
          data.refresh_token,
          useAuthStore.getState().user!
        );

        // 使用新 token 重连
        this.connect(this.url);
      } else {
        // Token 刷新失败，使用旧 token 重连
        this.connect(this.url);
      }
    } catch (error) {
      console.error('Failed to refresh token:', error);
      // 刷新失败，使用旧 token 重连
      this.connect(this.url);
    }
  }

  private handleMessage(message: any) {
    const { type, data } = message;
    const handlers = this.handlers.get(type);

    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  on(event: string, handler: Function) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);

    // 记录订阅，用于重连后恢复
    this.subscriptions.add(event);

    // 向服务器发送订阅请求
    this.send('subscribe', { event });
  }

  off(event: string, handler: Function) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.delete(handler);

      // 如果该事件没有处理器了，取消订阅
      if (handlers.size === 0) {
        this.handlers.delete(event);
        this.subscriptions.delete(event);
        this.send('unsubscribe', { event });
      }
    }
  }

  send(type: string, data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }

  disconnect() {
    this.stopHeartbeat();
    this.subscriptions.clear();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
```

### 9.2 WebSocket Hook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect } from 'react';
import { wsClient } from '@/services/websocket/client';

export const useWebSocket = (event: string, handler: (data: any) => void) => {
  useEffect(() => {
    wsClient.on(event, handler);

    return () => {
      wsClient.off(event, handler);
    };
  }, [event, handler]);
};

// 导入进度更新 Hook
export const useImportProgress = (importId: string, onProgress: (progress: number) => void) => {
  useWebSocket('import:progress', (data) => {
    if (data.import_id === importId) {
      onProgress(data.progress);
    }
  });
};

// 导入完成通知 Hook
export const useImportComplete = (onComplete: (data: any) => void) => {
  useWebSocket('import:complete', onComplete);
};
```

### 9.3 WebSocket 初始化与认证策略

#### 9.3.1 初始化时机

WebSocket 连接应在用户成功登录后立即建立，并在用户登出时断开。这确保了：

1. **安全性**：只有认证用户才能建立 WebSocket 连接
2. **Token 有效性**：连接建立时使用有效的 access token
3. **资源管理**：避免未认证用户占用服务器资源

#### 9.3.2 App.tsx 集成

```typescript
// src/App.tsx
import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { router } from '@/router';
import { useAuthStore } from '@/stores/authStore';
import { wsClient } from '@/services/websocket/client';

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
});

function App() {
  const { isAuthenticated, user } = useAuthStore();

  // WebSocket 连接管理
  useEffect(() => {
    if (isAuthenticated && user) {
      // 用户已登录，建立 WebSocket 连接
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
      wsClient.connect(wsUrl);

      console.log('WebSocket connection established for user:', user.username);

      // 组件卸载或用户登出时断开连接
      return () => {
        wsClient.disconnect();
        console.log('WebSocket connection closed');
      };
    }
  }, [isAuthenticated, user]);

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <RouterProvider router={router} />
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
```

#### 9.3.3 认证流程

```
┌─────────────────────────────────────────────────────────────┐
│                     用户认证与 WebSocket 流程                │
└─────────────────────────────────────────────────────────────┘

1. 用户登录
   ↓
2. 后端验证凭据
   ↓
3. 返回 access_token + refresh_token
   ↓
4. 前端存储 token 到 Zustand store
   ↓
5. App.tsx 检测到 isAuthenticated = true
   ↓
6. 建立 WebSocket 连接（携带 access_token）
   │
   ├─→ 连接成功
   │   ├─→ 启动心跳机制（30秒间隔）
   │   └─→ 恢复之前的订阅
   │
   └─→ 连接失败
       └─→ 自动重连（最多5次）
           ├─→ 检查 token 是否过期
           ├─→ 如过期则刷新 token
           └─→ 使用新 token 重连

7. 用户使用系统
   │
   ├─→ 订阅实时事件（import:progress, import:complete 等）
   ├─→ 接收服务器推送的更新
   └─→ 心跳保活（每30秒发送 ping，5秒内未收到 pong 则重连）

8. Token 即将过期
   ↓
9. HTTP 请求触发 401 错误
   ↓
10. Axios 拦截器自动刷新 token
   ↓
11. WebSocket 在下次重连时使用新 token

12. 用户登出
   ↓
13. 清理 Zustand store
   ↓
14. App.tsx 检测到 isAuthenticated = false
   ↓
15. 断开 WebSocket 连接
   ↓
16. 清理所有订阅和定时器
```

#### 9.3.4 Token 同步机制

WebSocket 和 HTTP 请求使用相同的 token 管理策略：

```typescript
// Token 刷新时的同步流程

1. HTTP 请求收到 401 响应
   ↓
2. Axios 拦截器触发 token 刷新
   ↓
3. 使用 refresh_token 获取新的 access_token
   ↓
4. 更新 Zustand store 中的 token
   ↓
5. 重试失败的 HTTP 请求
   ↓
6. WebSocket 连接继续使用旧 token（直到下次重连）
   │
   └─→ 如果 WebSocket 收到认证错误
       ├─→ 触发重连流程
       ├─→ 从 Zustand store 获取最新 token
       └─→ 使用新 token 建立连接
```

#### 9.3.5 环境变量配置

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws

# .env.production
VITE_API_BASE_URL=https://api.example.com/api/v1
VITE_WS_URL=wss://api.example.com/ws
```

#### 9.3.6 安全注意事项

1. **Token 传输**：
   - 开发环境使用 `ws://`（未加密）
   - 生产环境必须使用 `wss://`（TLS 加密）
   - Token 通过 URL 参数传递：`ws://host/ws?token=xxx`

2. **连接验证**：
   - 后端在 WebSocket 握手时验证 token
   - Token 无效或过期时拒绝连接
   - 前端收到拒绝后触发重新登录流程

3. **心跳机制**：
   - 防止连接被中间代理超时断开
   - 及时检测连接异常
   - 30秒间隔适合大多数场景

4. **重连策略**：
   - 指数退避算法避免服务器压力
   - 最多重连5次后停止
   - 重连前检查用户是否仍然登录

---

## 10. 安全措施

### 10.1 Content Security Policy

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    headers: {
      'Content-Security-Policy': [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self' ws: wss:",
        "frame-ancestors 'none'",
      ].join('; '),
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'X-XSS-Protection': '1; mode=block',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    },
  },
});
```

### 10.2 输入净化

```typescript
// src/utils/security.ts
import DOMPurify from 'dompurify';

/**
 * 净化 HTML 内容，防止 XSS 攻击
 */
export const sanitizeHTML = (html: string): string => {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target'],
  });
};

/**
 * 转义特殊字符
 */
export const escapeHTML = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

/**
 * 验证 URL 是否安全
 */
export const isSafeURL = (url: string): boolean => {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};

/**
 * 防止 CSRF 攻击 - 生成随机 token
 */
export const generateCSRFToken = (): string => {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
};
```

### 10.3 敏感数据处理

```typescript
// src/utils/storage.ts
/**
 * 安全的本地存储封装
 */
class SecureStorage {
  private prefix = 'externalhound_';

  set(key: string, value: any, encrypt = false): void {
    const fullKey = this.prefix + key;
    const data = encrypt ? this.encrypt(JSON.stringify(value)) : JSON.stringify(value);
    localStorage.setItem(fullKey, data);
  }

  get(key: string, decrypt = false): any {
    const fullKey = this.prefix + key;
    const data = localStorage.getItem(fullKey);

    if (!data) return null;

    try {
      const parsed = decrypt ? this.decrypt(data) : data;
      return JSON.parse(parsed);
    } catch {
      return null;
    }
  }

  remove(key: string): void {
    const fullKey = this.prefix + key;
    localStorage.removeItem(fullKey);
  }

  clear(): void {
    Object.keys(localStorage)
      .filter((key) => key.startsWith(this.prefix))
      .forEach((key) => localStorage.removeItem(key));
  }

  private encrypt(data: string): string {
    // 简单的 Base64 编码（生产环境应使用更强的加密）
    return btoa(data);
  }

  private decrypt(data: string): string {
    return atob(data);
  }
}

export const secureStorage = new SecureStorage();
```

---

## 11. 构建与部署

### 11.1 Vite 配置

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
          'query-vendor': ['@tanstack/react-query'],
          'graph-vendor': ['@antv/g6'],
          'chart-vendor': ['echarts'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

### 11.2 Dockerfile

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 11.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_min_length 1000;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # 24小时超时，适配长连接
    }

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 生产环境安全头（完整配置）
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Content Security Policy - 生产环境严格策略
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;

    # Permissions Policy (替代 Feature-Policy)
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # HSTS (仅在 HTTPS 时启用)
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
}
```

---

## 总结

### 设计亮点

1. **现代化技术栈**：React 18 + TypeScript + Vite，充分利用最新特性
2. **轻量级状态管理**：Zustand 替代 Redux，减少样板代码
3. **智能数据缓存**：React Query 自动管理服务端状态
4. **强大的图谱可视化**：G6 支持大规模图数据渲染
5. **实时更新**：WebSocket 实现导入进度实时推送
6. **完善的安全措施**：CSP、XSS 防护、输入净化
7. **优化的构建配置**：代码分割、Gzip 压缩、静态资源缓存

### 实施建议

1. **优先实现核心页面**：Dashboard、资产列表、导入页面
2. **完善类型定义**：为所有 API 响应定义 TypeScript 类型
3. **添加单元测试**：使用 Vitest + React Testing Library
4. **性能监控**：集成 Web Vitals 监控页面性能
5. **国际化支持**：使用 react-i18next 支持多语言

---

**文档版本**：v1.0
**最后更新**：2026-01-16
**维护者**：ExternalHound 开发团队
