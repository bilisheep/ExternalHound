# ExternalHound 数据库设计方案 v1.0

**文档信息**
- 版本：v1.0
- 日期：2026-01-16
- 系统定位：渗透测试数据管理与可视化平台
- 状态：设计方案

---

## 目录

1. [设计概述](#1-设计概述)
2. [PostgreSQL 数据库设计](#2-postgresql-数据库设计)
3. [Neo4j 图数据库设计](#3-neo4j-图数据库设计)
4. [数据同步策略](#4-数据同步策略)
5. [索引与性能优化](#5-索引与性能优化)
6. [数据迁移与备份](#6-数据迁移与备份)
7. [安全与权限控制](#7-安全与权限控制)

---

## 1. 设计概述

### 1.1 架构原则

ExternalHound 采用 **PostgreSQL + Neo4j 双数据库架构**：

- **PostgreSQL**：存储资产的详细元数据、导入记录、操作日志等结构化和半结构化数据
- **Neo4j**：存储资产间的关系图谱，支持高效的路径查询和关系分析
- **MinIO/S3**：存储原始文件、截图等二进制数据

### 1.2 设计原则

1. **职责分离**：PostgreSQL 负责详细数据，Neo4j 负责关系查询
2. **数据一致性**：PostgreSQL 为主数据源，Neo4j 为关系视图
3. **灵活扩展**：使用 JSONB 存储可变元数据
4. **性能优先**：合理设计索引，支持高频查询场景
5. **可追溯性**：记录数据来源、创建时间、更新时间

**标识策略**：各资产表使用 UUID 作为主键，并新增 `external_id` 作为业务唯一标识，用于与 Neo4j 节点 `id` 对齐以保证强关联。

### 1.3 核心实体

基于需求文档，系统包含以下 8 类核心资产实体：

1. **Organization**（组织）- 资产归属的根节点
2. **Netblock**（网段）- IP 地址段
3. **Domain**（域名）- DNS 实体
4. **IP**（主机）- 网络节点
5. **Certificate**（证书）- SSL/TLS 证书
6. **Service**（服务）- 端口服务（L4+L7）
7. **ClientApplication**（客户端应用）- 移动端/PC 客户端
8. **Credential**（凭证）- 外部泄露/分析得到的凭证

### 1.4 关系类型

系统定义 13 种边关系，分为以下几类：

**归属类**：
- SUBSIDIARY（子公司）
- OWNS_NETBLOCK（拥有网段）
- OWNS_ASSET（拥有资产）
- OWNS_DOMAIN（拥有域名）

**拓扑类**：
- CONTAINS（包含）
- SUBDOMAIN（子域名）

**解析类**：
- RESOLVES_TO（当前解析）
- HISTORY_RESOLVES_TO（历史解析）
- ISSUED_TO（证书签发）

**服务与路由类**：
- HOSTS_SERVICE（物理承载）
- ROUTES_TO（逻辑路由）
- UPSTREAM（上游代理）
- COMMUNICATES（客户端通信）

---

## 2. PostgreSQL 数据库设计

### 2.1 数据库配置

```sql
-- 创建数据库
CREATE DATABASE externalhound
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 模糊搜索
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN 索引增强
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- GiST 索引增强
```

### 2.2 核心资产表

#### 2.2.1 Organization（组织表）

```sql
CREATE TABLE assets_organization (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（与 Neo4j 节点 id 对齐）

    -- 核心字段（用于 Neo4j 同步）
    name VARCHAR(255) NOT NULL,                    -- 简短名称
    full_name VARCHAR(500),                        -- 完整注册名称
    credit_code VARCHAR(100) UNIQUE,               -- 统一社会信用代码

    -- 拓扑属性
    is_primary BOOLEAN DEFAULT FALSE,              -- 是否为一级目标
    tier INTEGER DEFAULT 0,                        -- 层级：0=总部, 1=子公司
    asset_count INTEGER DEFAULT 0,                 -- 资产总数（聚合字段）
    risk_score DECIMAL(3,1) DEFAULT 0.0,          -- 风险评分 0-10

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',  -- IN_SCOPE, OUT_OF_SCOPE

    -- 元数据（JSONB 灵活字段）
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "english_name": "MoMo Tech Group Co., Ltd.",
        "description": "企业描述",
        "industries": ["Internet", "Finance"],
        "headquarters": "Beijing, China",
        "stock_symbol": "HK:09988",
        "contacts": [
            {"role": "CISO", "email": "security@example.com"}
        ],
        "source": "Tianyancha",
        "tags": ["Nasdaq", "China-Top500"],
        "notes": "备注信息"
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    -- 索引
    CONSTRAINT chk_risk_score CHECK (risk_score >= 0 AND risk_score <= 10),
    CONSTRAINT chk_tier CHECK (tier >= 0)
);

-- 索引
CREATE INDEX idx_org_name ON assets_organization(name);
CREATE INDEX idx_org_credit_code ON assets_organization(credit_code);
CREATE INDEX idx_org_is_primary ON assets_organization(is_primary);
CREATE INDEX idx_org_scope_policy ON assets_organization(scope_policy);
CREATE INDEX idx_org_metadata_gin ON assets_organization USING GIN (metadata);
CREATE INDEX idx_org_created_at ON assets_organization(created_at);

-- 全文搜索索引
CREATE INDEX idx_org_name_trgm ON assets_organization USING GIN (name gin_trgm_ops);
CREATE INDEX idx_org_full_name_trgm ON assets_organization USING GIN (full_name gin_trgm_ops);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_org_updated_at
    BEFORE UPDATE ON assets_organization
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.2 Netblock（网段表）

```sql
CREATE TABLE assets_netblock (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（与 Neo4j 节点 id 对齐）

    -- 核心字段
    cidr CIDR NOT NULL UNIQUE,                     -- 网段地址
    asn_number VARCHAR(20),                        -- AS 号

    -- 拓扑属性
    capacity BIGINT,                               -- 网段容量
    live_count INTEGER DEFAULT 0,                  -- 存活 IP 数量
    risk_score DECIMAL(3,1) DEFAULT 0.0,

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    is_internal BOOLEAN DEFAULT FALSE,             -- 是否为内网段

    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "net_name": "ALIBABA-CN-NET",
        "description": "Alibaba (China) Technology Co., Ltd.",
        "org_handle": "ORG-ALIBABA-1",
        "maintainer": "MAINT-ALI-CN",
        "abuse_contact": "abuse@aliyun.com",
        "location": {
            "country": "CN",
            "region": "Zhejiang",
            "city": "Hangzhou",
            "latitude": 30.29,
            "longitude": 120.16
        },
        "source": "BGP_View",
        "tags": ["Cloud", "Production"],
        "discovered_at": "2023-10-01T12:00:00Z"
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT chk_netblock_risk_score CHECK (risk_score >= 0 AND risk_score <= 10)
);

-- 索引
CREATE INDEX idx_netblock_cidr ON assets_netblock USING GIST (cidr inet_ops);
CREATE INDEX idx_netblock_asn ON assets_netblock(asn_number);
CREATE INDEX idx_netblock_scope_policy ON assets_netblock(scope_policy);
CREATE INDEX idx_netblock_metadata_gin ON assets_netblock USING GIN (metadata);

-- 触发器
CREATE TRIGGER trg_netblock_updated_at
    BEFORE UPDATE ON assets_netblock
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.3 Domain（域名表）

```sql
CREATE TABLE assets_domain (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（与 Neo4j 节点 id 对齐）

    -- 核心字段
    name VARCHAR(255) NOT NULL UNIQUE,             -- 完整域名
    root_domain VARCHAR(255),                      -- 根域名
    tier INTEGER DEFAULT 1,                        -- 层级深度

    -- 攻击面状态
    is_resolved BOOLEAN DEFAULT FALSE,             -- 是否能解析
    is_wildcard BOOLEAN DEFAULT FALSE,             -- 是否为泛解析
    is_internal BOOLEAN DEFAULT FALSE,             -- 是否解析到内网
    has_waf BOOLEAN DEFAULT FALSE,                 -- 是否有 WAF

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',

    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "records": {
            "A": ["1.2.3.4"],
            "CNAME": ["aliyun-waf.com"],
            "MX": ["mxbiz1.qq.com"],
            "TXT": ["v=spf1 include:spf..."],
            "NS": ["ns1.alidns.com"]
        },
        "icp_license": "京ICP备xxxxx号-1",
        "registrar": "Godaddy",
        "registrant_email": "admin@target.com",
        "creation_date": "2015-01-01",
        "expiration_date": "2025-01-01",
        "tech_stack": {
            "cdn_provider": "Cloudflare",
            "waf_product": "Aliyun WAF",
            "server": "Nginx"
        },
        "sources": ["Subfinder", "Certificate Transparency"],
        "screenshot_path": "s3://bucket/snapshots/hash.jpg",
        "page_title": "用户登录中心",
        "http_status_code": 200
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT chk_domain_tier CHECK (tier >= 1)
);

-- 索引
CREATE INDEX idx_domain_name ON assets_domain(name);
CREATE INDEX idx_domain_root_domain ON assets_domain(root_domain);
CREATE INDEX idx_domain_is_resolved ON assets_domain(is_resolved);
CREATE INDEX idx_domain_scope_policy ON assets_domain(scope_policy);
CREATE INDEX idx_domain_metadata_gin ON assets_domain USING GIN (metadata);

-- 全文搜索索引
CREATE INDEX idx_domain_name_trgm ON assets_domain USING GIN (name gin_trgm_ops);

-- 触发器
CREATE TRIGGER trg_domain_updated_at
    BEFORE UPDATE ON assets_domain
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.4 IP（主机表）

```sql
CREATE TABLE assets_ip (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（与 Neo4j 节点 id 对齐）

    -- 核心字段
    address INET NOT NULL UNIQUE,                  -- IP 地址
    version INTEGER NOT NULL,                      -- 4 或 6

    -- 拓扑属性
    is_cloud BOOLEAN DEFAULT FALSE,                -- 是否为云主机
    is_internal BOOLEAN DEFAULT FALSE,             -- 是否为内网
    is_cdn BOOLEAN DEFAULT FALSE,                  -- 是否为 CDN 节点

    -- 聚合统计
    open_ports_count INTEGER DEFAULT 0,            -- 开放端口数
    risk_score DECIMAL(3,1) DEFAULT 0.0,
    vuln_critical_count INTEGER DEFAULT 0,         -- 严重漏洞数

    -- 地理/归属
    country_code VARCHAR(2),                       -- 国家代码
    asn_number VARCHAR(20),                        -- AS 号

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',

    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "os_info": {
            "name": "Ubuntu",
            "flavor": "Focal Fossa",
            "version": "20.04 LTS",
            "kernel": "Linux 5.4.0",
            "cpe": "cpe:/o:canonical:ubuntu_linux:20.04",
            "confidence": 95,
            "fingerprint_source": "Nmap OSDetection"
        },
        "geo_location": {
            "city": "Hangzhou",
            "region": "Zhejiang",
            "latitude": 30.2936,
            "longitude": 120.1614,
            "timezone": "Asia/Shanghai",
            "isp": "Aliyun Computing Co., LTD"
        },
        "cloud_metadata": {
            "provider": "Aliyun",
            "region_id": "cn-hangzhou",
            "instance_type": "ecs.t5-lc1m1.small",
            "tags": ["Production", "K8s-Node"]
        }
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT chk_ip_version CHECK (version IN (4, 6)),
    CONSTRAINT chk_ip_risk_score CHECK (risk_score >= 0 AND risk_score <= 10)
);

-- 索引
CREATE INDEX idx_ip_address ON assets_ip USING GIST (address inet_ops);
CREATE INDEX idx_ip_version ON assets_ip(version);
CREATE INDEX idx_ip_country_code ON assets_ip(country_code);
CREATE INDEX idx_ip_asn_number ON assets_ip(asn_number);
CREATE INDEX idx_ip_scope_policy ON assets_ip(scope_policy);
CREATE INDEX idx_ip_is_cloud ON assets_ip(is_cloud);
CREATE INDEX idx_ip_metadata_gin ON assets_ip USING GIN (metadata);

-- 触发器
CREATE TRIGGER trg_ip_updated_at
    BEFORE UPDATE ON assets_ip
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.5 Certificate（证书表）

```sql
CREATE TABLE assets_certificate (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（建议使用 cert:SHA256）

    -- 核心字段
    subject_cn VARCHAR(255),                       -- 主题通用名称
    issuer_cn VARCHAR(255),                        -- 颁发者通用名称
    issuer_org VARCHAR(255),                       -- 颁发者组织

    -- 时间属性
    valid_from BIGINT,                             -- 生效时间戳
    valid_to BIGINT,                               -- 过期时间戳
    days_to_expire INTEGER,                        -- 剩余天数

    -- 风险属性
    is_expired BOOLEAN DEFAULT FALSE,
    is_self_signed BOOLEAN DEFAULT FALSE,
    is_revoked BOOLEAN DEFAULT FALSE,

    -- 统计属性
    san_count INTEGER DEFAULT 0,                   -- SAN 域名数量

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',

    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "subject": {
            "C": "CN", "ST": "Beijing", "L": "Beijing",
            "O": "Target Corp", "OU": "IT Dept",
            "CN": "api.target.com"
        },
        "issuer": {
            "C": "US", "O": "DigiCert Inc", "CN": "DigiCert Global CA"
        },
        "subject_alt_names": [
            "api.target.com",
            "dev-internal.target.com"
        ],
        "public_key": {
            "algorithm": "RSA",
            "bits": 2048,
            "exponent": 65537
        },
        "signature_algorithm": "SHA256withRSA",
        "serial_number": "543216789...",
        "fingerprints": {
            "sha1": "...",
            "sha256": "...",
            "md5": "..."
        },
        "chain_validation": {
            "is_trusted": true,
            "chain_depth": 2,
            "root_ca": "DigiCert Global Root CA"
        },
        "monitor_config": {
            "alert_before_days": 14,
            "track_transparency": true,
            "allow_wildcard": false
        },
        "raw_pem_path": "s3://certs/a1b2c3...pem"
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 索引
CREATE INDEX idx_cert_subject_cn ON assets_certificate(subject_cn);
CREATE INDEX idx_cert_issuer_cn ON assets_certificate(issuer_cn);
CREATE INDEX idx_cert_valid_to ON assets_certificate(valid_to);
CREATE INDEX idx_cert_is_expired ON assets_certificate(is_expired);
CREATE INDEX idx_cert_is_self_signed ON assets_certificate(is_self_signed);
CREATE INDEX idx_cert_metadata_gin ON assets_certificate USING GIN (metadata);

-- 全文搜索索引
CREATE INDEX idx_cert_subject_cn_trgm ON assets_certificate USING GIN (subject_cn gin_trgm_ops);

-- 触发器
CREATE TRIGGER trg_cert_updated_at
    BEFORE UPDATE ON assets_certificate
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.6 Service（服务表）

```sql
CREATE TABLE assets_service (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（如 svc:IP:Port 或 svc:IP:Port:UDP）

    -- 核心字段
    ip_address INET NOT NULL,                      -- IP 地址
    port INTEGER NOT NULL,                         -- 端口号
    protocol VARCHAR(10) NOT NULL DEFAULT 'TCP',   -- TCP/UDP

    -- 指纹信息
    service_name VARCHAR(100),                     -- 服务名
    product VARCHAR(255),                          -- 产品名称
    version VARCHAR(100),                          -- 版本号

    -- 战术属性
    is_http BOOLEAN DEFAULT FALSE,                 -- 是否为 Web 服务
    is_admin BOOLEAN DEFAULT FALSE,                -- 是否为管理后台

    -- 风险属性
    has_exploit BOOLEAN DEFAULT FALSE,             -- 是否有已知 EXP

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',

    -- 项目定位
    asset_category VARCHAR(50),                    -- VPN, Gateway, S3, OA, Mail, Monitor, General

    -- 原始数据
    banner TEXT,
    response_headers TEXT,

    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "http_title": "Sangfor VPN Login - Welcome",
        "screenshot_url": "s3://scan-results/screenshots/svc_47_100_1_15_8443.jpg",
        "tech_stacks": [
            {"name": "jQuery", "version": "1.12.4"},
            {"name": "Vue.js", "version": "2.6.10"}
        ],
        "final_redirect": "https://47.100.1.15:8443/portal/login",
        "is_honeypot": false
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT chk_service_port CHECK (port >= 1 AND port <= 65535),
    CONSTRAINT chk_service_protocol CHECK (protocol IN ('TCP', 'UDP'))
);

-- 索引
CREATE INDEX idx_service_ip_address ON assets_service USING GIST (ip_address inet_ops);
CREATE INDEX idx_service_port ON assets_service(port);
CREATE INDEX idx_service_protocol ON assets_service(protocol);
CREATE INDEX idx_service_product ON assets_service(product);
CREATE INDEX idx_service_is_http ON assets_service(is_http);
CREATE INDEX idx_service_asset_category ON assets_service(asset_category);
CREATE INDEX idx_service_metadata_gin ON assets_service USING GIN (metadata);

-- 全文搜索索引
CREATE INDEX idx_service_banner_trgm ON assets_service USING GIN (banner gin_trgm_ops);
CREATE INDEX idx_service_product_trgm ON assets_service USING GIN (product gin_trgm_ops);

-- 触发器
CREATE TRIGGER trg_service_updated_at
    BEFORE UPDATE ON assets_service
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.7 ClientApplication（客户端应用表）

```sql
CREATE TABLE assets_client_application (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（如 app:bundle_id）

    -- 核心字段
    name VARCHAR(255) NOT NULL,                    -- 应用名
    bundle_id VARCHAR(255) NOT NULL UNIQUE,        -- 包名
    platform VARCHAR(50) NOT NULL,                 -- Android, iOS, Windows
    version VARCHAR(100),                          -- 版本号

    -- 战术属性
    app_category VARCHAR(50),                      -- Enterprise, Consumer, Legacy
    is_hardened BOOLEAN DEFAULT FALSE,             -- 是否加固

    -- 范围控制
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',

    -- 资源
    download_url TEXT,
    hardening_vendor VARCHAR(100),                 -- 加固厂商

    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    metadata 结构示例：
    {
        "permissions": ["CAMERA", "READ_CONTACTS"],
        "signature": "a1b2c3d4...",
        "file_size": 45000000,
        "compile_time": "2023-01-01"
    }
    */

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT chk_app_platform CHECK (platform IN ('Android', 'iOS', 'Windows', 'macOS', 'Linux'))
);

-- 索引
CREATE INDEX idx_app_name ON assets_client_application(name);
CREATE INDEX idx_app_bundle_id ON assets_client_application(bundle_id);
CREATE INDEX idx_app_platform ON assets_client_application(platform);
CREATE INDEX idx_app_category ON assets_client_application(app_category);
CREATE INDEX idx_app_metadata_gin ON assets_client_application USING GIN (metadata);

-- 全文搜索索引
CREATE INDEX idx_app_name_trgm ON assets_client_application USING GIN (name gin_trgm_ops);

-- 触发器
CREATE TRIGGER trg_app_updated_at
    BEFORE UPDATE ON assets_client_application
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2.8 Credential（凭证表）

```sql
CREATE TABLE assets_credential (
    -- 主键与标识
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,      -- 业务唯一标识（如 cred:hash 或 cred:key_id）

    -- 核心字段
    cred_type VARCHAR(50) NOT NULL,                -- AccessKey, PrivateKey, DB_Password 等
    provider VARCHAR(50),                          -- AWS, Aliyun, SSH 等
    is_valid BOOLEAN DEFAULT FALSE,                -- 是否验证有效
    leaked_count INTEGER DEFAULT 0,                -- 泄露次数

    -- 敏感内容与上下文（建议加密存储）
    content JSONB DEFAULT '{}'::jsonb,             -- 密钥内容/凭证明细
    source_context TEXT,                           -- 来源上下文（文件/代码位置）
    validation_result JSONB DEFAULT '{}'::jsonb,   -- 验证结果与权限

    -- 审计字段
    discovered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 索引
CREATE INDEX idx_cred_type ON assets_credential(cred_type);
CREATE INDEX idx_cred_provider ON assets_credential(provider);
CREATE INDEX idx_cred_is_valid ON assets_credential(is_valid);
CREATE INDEX idx_cred_metadata_gin ON assets_credential USING GIN (content);

-- 触发器
CREATE TRIGGER trg_credential_updated_at
    BEFORE UPDATE ON assets_credential
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 2.3 辅助表

#### 2.3.1 导入记录表

```sql
CREATE TABLE import_logs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 文件信息
    filename VARCHAR(500) NOT NULL,
    file_size BIGINT,                              -- 文件大小（字节）
    file_hash VARCHAR(64),                         -- SHA256 哈希
    file_path TEXT,                                -- MinIO 存储路径

    -- 导入信息
    format VARCHAR(50) NOT NULL,                   -- Nmap, Masscan, Nuclei, JSON, CSV
    parser_version VARCHAR(20),                    -- 解析器版本

    -- 状态
    status VARCHAR(20) NOT NULL,                   -- PENDING, PROCESSING, SUCCESS, FAILED, PARTIAL
    progress INTEGER DEFAULT 0,                    -- 进度百分比

    -- 统计
    records_total INTEGER DEFAULT 0,               -- 总记录数
    records_success INTEGER DEFAULT 0,             -- 成功记录数
    records_failed INTEGER DEFAULT 0,              -- 失败记录数

    -- 结果
    error_message TEXT,                            -- 错误信息
    error_details JSONB,                           -- 详细错误日志

    -- 资产统计
    assets_created JSONB DEFAULT '{}'::jsonb,      -- 创建的资产统计
    /*
    {
        "organization": 1,
        "ip": 150,
        "domain": 50,
        "service": 300
    }
    */

    -- 审计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    duration_seconds INTEGER                       -- 导入耗时（秒）
);

-- 索引
CREATE INDEX idx_import_status ON import_logs(status);
CREATE INDEX idx_import_format ON import_logs(format);
CREATE INDEX idx_import_created_at ON import_logs(created_at);
CREATE INDEX idx_import_created_by ON import_logs(created_by);

-- 触发器
CREATE TRIGGER trg_import_updated_at
    BEFORE UPDATE ON import_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.3.2 操作日志表

```sql
CREATE TABLE operation_logs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 操作信息
    operation_type VARCHAR(50) NOT NULL,           -- CREATE, UPDATE, DELETE, MERGE, EXPORT
    entity_type VARCHAR(50) NOT NULL,              -- Organization, IP, Domain, Service, etc.
    entity_id VARCHAR(255),                        -- 实体 ID

    -- 操作详情
    operation_detail JSONB,                        -- 操作详细信息
    /*
    {
        "action": "merge_assets",
        "source_ids": ["uuid1", "uuid2"],
        "target_id": "uuid3",
        "merge_strategy": "keep_latest"
    }
    */

    -- 变更记录
    old_value JSONB,                               -- 变更前的值
    new_value JSONB,                               -- 变更后的值

    -- 审计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    ip_address INET,                               -- 操作来源 IP
    user_agent TEXT                                -- User Agent
);

-- 索引
CREATE INDEX idx_oplog_operation_type ON operation_logs(operation_type);
CREATE INDEX idx_oplog_entity_type ON operation_logs(entity_type);
CREATE INDEX idx_oplog_entity_id ON operation_logs(entity_id);
CREATE INDEX idx_oplog_created_at ON operation_logs(created_at);
CREATE INDEX idx_oplog_created_by ON operation_logs(created_by);

-- 分区表（按月分区）
-- 可选：如果操作日志量大，建议使用分区表
```

#### 2.3.3 标签表

```sql
CREATE TABLE tags (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 标签信息
    name VARCHAR(100) NOT NULL UNIQUE,             -- 标签名称
    category VARCHAR(50),                          -- 标签分类：Risk, Business, Technical
    color VARCHAR(20),                             -- 显示颜色
    description TEXT,                              -- 标签描述

    -- 统计
    usage_count INTEGER DEFAULT 0,                 -- 使用次数

    -- 审计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 索引
CREATE INDEX idx_tag_name ON tags(name);
CREATE INDEX idx_tag_category ON tags(category);

-- 触发器
CREATE TRIGGER trg_tag_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2.3.4 资产标签关联表

```sql
CREATE TABLE asset_tags (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息
    asset_type VARCHAR(50) NOT NULL,               -- Organization, IP, Domain, Service, etc.
    asset_id VARCHAR(255) NOT NULL,                -- 资产 ID
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

    -- 审计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    -- 唯一约束
    CONSTRAINT uq_asset_tag UNIQUE (asset_type, asset_id, tag_id)
);

-- 索引
CREATE INDEX idx_asset_tag_asset ON asset_tags(asset_type, asset_id);
CREATE INDEX idx_asset_tag_tag_id ON asset_tags(tag_id);
CREATE INDEX idx_asset_tag_created_at ON asset_tags(created_at);
```

---

## 3. Neo4j 图数据库设计

### 3.1 节点设计

Neo4j 中的节点与 PostgreSQL 中的资产表对应，但只存储用于图谱查询和可视化的核心属性。

#### 3.1.1 节点标签与属性

```cypher
// 1. Organization 节点
CREATE (org:Organization {
    id: "org:uuid",                    // [必需] 与 PG 一致的 ID
    name: "某某科技集团",               // [必需] 显示名称
    is_primary: true,                  // 是否为一级目标
    tier: 0,                           // 层级
    asset_count: 15420,                // 资产总数
    risk_score: 9.5,                   // 风险评分
    scope_policy: "IN_SCOPE"           // 范围策略
})

// 2. Netblock 节点
CREATE (nb:Netblock {
    id: "cidr:47.100.0.0/16",
    cidr: "47.100.0.0/16",
    asn_number: "AS37963",
    capacity: 65536,
    live_count: 128,
    risk_score: 7.5,
    scope_policy: "IN_SCOPE",
    is_internal: false
})

// 3. Domain 节点
CREATE (d:Domain {
    id: "domain:api.target.com",
    name: "api.target.com",
    root_domain: "target.com",
    tier: 2,
    is_resolved: true,
    is_wildcard: false,
    is_internal: false,
    has_waf: true,
    scope_policy: "IN_SCOPE"
})

// 4. IP 节点
CREATE (ip:IP {
    id: "ip:47.100.1.15",
    address: "47.100.1.15",
    version: 4,
    is_cloud: true,
    is_internal: false,
    is_cdn: false,
    open_ports_count: 12,
    risk_score: 8.5,
    vuln_critical_count: 1,
    country_code: "CN",
    asn_number: "AS37963",
    scope_policy: "IN_SCOPE"
})

// 5. Certificate 节点
CREATE (cert:Certificate {
    id: "cert:a1b2c3d4e5...",
    subject_cn: "api.target.com",
    issuer_cn: "DigiCert Inc",
    issuer_org: "DigiCert Global",
    valid_from: 1672531200,
    valid_to: 1704067200,
    days_to_expire: 30,
    is_expired: false,
    is_self_signed: false,
    is_revoked: false,
    san_count: 15,
    scope_policy: "IN_SCOPE"
})

// 6. Service 节点
CREATE (svc:Service {
    id: "svc:47.100.1.15:8080",
    port: 8080,
    protocol: "TCP",
    service_name: "http-alt",
    product: "Nginx",
    version: "1.18.0",
    is_http: true,
    is_admin: false,
    has_exploit: true,
    scope_policy: "IN_SCOPE"
})

// 7. ClientApplication 节点
CREATE (app:ClientApplication {
    id: "app:com.target.mobile",
    name: "Target Admin",
    bundle_id: "com.target.mobile",
    platform: "Android",
    app_category: "Enterprise",
    is_hardened: true,
    scope_policy: "IN_SCOPE"
})

// 8. Credential 节点
CREATE (cred:Credential {
    id: "cred:ak-xxxx",
    type: "AccessKey",
    provider: "AWS",
    is_valid: true,
    leaked_count: 3
})
```

#### 3.1.2 节点约束与索引

```cypher
// 唯一约束（自动创建索引）
CREATE CONSTRAINT org_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT netblock_id_unique IF NOT EXISTS FOR (n:Netblock) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT domain_id_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT ip_id_unique IF NOT EXISTS FOR (i:IP) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT cert_id_unique IF NOT EXISTS FOR (c:Certificate) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT service_id_unique IF NOT EXISTS FOR (s:Service) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT app_id_unique IF NOT EXISTS FOR (a:ClientApplication) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT cred_id_unique IF NOT EXISTS FOR (c:Credential) REQUIRE c.id IS UNIQUE;

// 常用属性索引
CREATE INDEX org_name_idx IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX org_is_primary_idx IF NOT EXISTS FOR (o:Organization) ON (o.is_primary);

CREATE INDEX netblock_asn_idx IF NOT EXISTS FOR (n:Netblock) ON (n.asn_number);
CREATE INDEX netblock_scope_idx IF NOT EXISTS FOR (n:Netblock) ON (n.scope_policy);

CREATE INDEX domain_name_idx IF NOT EXISTS FOR (d:Domain) ON (d.name);
CREATE INDEX domain_root_idx IF NOT EXISTS FOR (d:Domain) ON (d.root_domain);
CREATE INDEX domain_resolved_idx IF NOT EXISTS FOR (d:Domain) ON (d.is_resolved);

CREATE INDEX ip_address_idx IF NOT EXISTS FOR (i:IP) ON (i.address);
CREATE INDEX ip_country_idx IF NOT EXISTS FOR (i:IP) ON (i.country_code);
CREATE INDEX ip_asn_idx IF NOT EXISTS FOR (i:IP) ON (i.asn_number);

CREATE INDEX cert_subject_cn_idx IF NOT EXISTS FOR (c:Certificate) ON (c.subject_cn);
CREATE INDEX cert_expired_idx IF NOT EXISTS FOR (c:Certificate) ON (c.is_expired);

CREATE INDEX service_port_idx IF NOT EXISTS FOR (s:Service) ON (s.port);
CREATE INDEX service_product_idx IF NOT EXISTS FOR (s:Service) ON (s.product);
CREATE INDEX service_is_http_idx IF NOT EXISTS FOR (s:Service) ON (s.is_http);

CREATE INDEX app_platform_idx IF NOT EXISTS FOR (a:ClientApplication) ON (a.platform);
CREATE INDEX app_category_idx IF NOT EXISTS FOR (a:ClientApplication) ON (a.app_category);

CREATE INDEX cred_type_idx IF NOT EXISTS FOR (c:Credential) ON (c.type);
CREATE INDEX cred_provider_idx IF NOT EXISTS FOR (c:Credential) ON (c.provider);
CREATE INDEX cred_is_valid_idx IF NOT EXISTS FOR (c:Credential) ON (c.is_valid);
```

### 3.2 关系设计

#### 3.2.1 归属类关系

```cypher
// 1. SUBSIDIARY（子公司）
CREATE (parent:Organization)-[:SUBSIDIARY {
    percent: 100.0,                    // 持股比例
    type: "WhollyOwned",               // 关系类型
    source: "Tianyancha",              // 数据来源
    created_at: datetime()
}]->(child:Organization)

// 2. OWNS_NETBLOCK（拥有网段）
CREATE (org:Organization)-[:OWNS_NETBLOCK {
    source: "Whois",
    confidence: 0.9,
    created_at: datetime()
}]->(nb:Netblock)

// 3. OWNS_ASSET（拥有独立资产）
CREATE (org:Organization)-[:OWNS_ASSET {
    source: "Whois",
    created_at: datetime()
}]->(ip:IP)

// 4. OWNS_DOMAIN（拥有域名）
CREATE (org:Organization)-[:OWNS_DOMAIN {
    source: "ICP",                     // ICP 或 Whois
    created_at: datetime()
}]->(d:Domain)
```

#### 3.2.2 拓扑类关系

```cypher
// 5. CONTAINS（包含）
CREATE (nb:Netblock)-[:CONTAINS {
    created_at: datetime()
}]->(ip:IP)

// 6. SUBDOMAIN（子域名）
CREATE (parent:Domain)-[:SUBDOMAIN {
    is_direct: true,                   // 是否为直接下级
    created_at: datetime()
}]->(child:Domain)
```

#### 3.2.3 解析类关系

```cypher
// 7. RESOLVES_TO（当前解析）
CREATE (d:Domain)-[:RESOLVES_TO {
    record_type: "A",                  // A, AAAA, CNAME
    last_seen: "2023-10-29",
    created_at: datetime()
}]->(ip:IP)

// 8. HISTORY_RESOLVES_TO（历史解析）
CREATE (ip:IP)-[:HISTORY_RESOLVES_TO {
    first_seen: "2021-01-01",
    last_seen: "2022-05-01",
    source: "PassiveDNS",
    created_at: datetime()
}]->(d:Domain)

// 9. ISSUED_TO（证书签发）
CREATE (cert:Certificate)-[:ISSUED_TO {
    source_field: "SAN",               // SAN 或 CN
    created_at: datetime()
}]->(d:Domain)
```

#### 3.2.4 服务与路由类关系

```cypher
// 10. HOSTS_SERVICE（物理承载）
CREATE (ip:IP)-[:HOSTS_SERVICE {
    discovery: "Masscan",
    first_seen: "2023-10-29",
    created_at: datetime()
}]->(svc:Service)

// 11. ROUTES_TO（逻辑路由）
CREATE (d:Domain)-[:ROUTES_TO {
    url_context: "/",
    http_status: 200,
    created_at: datetime()
}]->(svc:Service)

// 12. UPSTREAM（上游代理）
CREATE (frontend:Service)-[:UPSTREAM {
    type: "ReverseProxy",
    conf_file: "nginx.conf",
    created_at: datetime()
}]->(backend:Service)

// 13. COMMUNICATES（客户端通信）
CREATE (app:ClientApplication)-[:COMMUNICATES {
    method: "StaticAnalysis",
    api_endpoint: "/api/v1/login",
    created_at: datetime()
}]->(svc:Service)
```

### 3.3 常用查询模式

#### 3.3.1 基础查询

```cypher
// 查询某组织的所有资产
MATCH (org:Organization {id: 'org:123'})-[*1..3]->(asset)
RETURN org, asset
LIMIT 500

// 查询某 IP 的所有服务
MATCH (ip:IP {address: '1.2.3.4'})-[:HOSTS_SERVICE]->(svc:Service)
RETURN ip, svc

// 查询某域名的解析记录
MATCH (d:Domain {name: 'api.target.com'})-[:RESOLVES_TO]->(ip:IP)
RETURN d, ip
```

#### 3.3.2 路径查询

```cypher
// 查询从组织到服务的完整路径
MATCH path = (org:Organization)-[*]->(svc:Service)
WHERE org.id = 'org:123' AND svc.port = 443
RETURN path
LIMIT 10

// 查询两个节点之间的最短路径
MATCH path = shortestPath(
    (start:IP {address: '1.2.3.4'})-[*]-(end:Service {port: 8080})
)
RETURN path
```

#### 3.3.3 聚合查询

```cypher
// 统计某组织下各类资产数量
MATCH (org:Organization {id: 'org:123'})-[*1..3]->(asset)
RETURN labels(asset)[0] AS asset_type, count(asset) AS count
ORDER BY count DESC

// 查询高风险服务
MATCH (svc:Service)
WHERE svc.has_exploit = true AND svc.scope_policy = 'IN_SCOPE'
RETURN svc
ORDER BY svc.risk_score DESC
LIMIT 100
```

#### 3.3.4 关系分析

```cypher
// 查询某证书关联的所有域名
MATCH (cert:Certificate {id: 'cert:abc...'})-[:ISSUED_TO]->(d:Domain)
RETURN cert, d

// 查询某域名的上下游关系（2 跳）
MATCH (d:Domain {name: 'api.target.com'})-[*1..2]-(related)
RETURN d, related
LIMIT 100

// 查询内网服务的暴露路径
MATCH path = (external:IP {is_internal: false})-[*]-(internal:Service)
WHERE internal.scope_policy = 'IN_SCOPE'
RETURN path
LIMIT 50
```

---

## 4. 数据同步策略

### 4.1 同步原则

1. **PostgreSQL 为主数据源**：所有数据首先写入 PostgreSQL
2. **Neo4j 为关系视图**：从 PostgreSQL 同步核心属性和关系到 Neo4j
3. **应用层同步**：由 FastAPI 服务层负责同步逻辑
4. **幂等性保证**：使用 MERGE 语句确保重复同步不会产生副作用
5. **强关联主键**：同步时使用 PostgreSQL 的 `external_id` 作为 Neo4j 节点 `id`

### 4.2 同步时机

#### 4.2.1 实时同步（推荐）

在数据导入完成后，立即同步到 Neo4j：

```python
# 伪代码示例
async def import_assets(file_path: str):
    # 1. 解析文件
    assets = parse_file(file_path)

    # 2. 写入 PostgreSQL
    pg_ids = await write_to_postgres(assets)

    # 3. 同步到 Neo4j
    await sync_to_neo4j(pg_ids)

    # 4. 记录导入日志
    await log_import(file_path, pg_ids)
```

#### 4.2.2 批量同步（可选）

对于大批量数据，可以采用批量同步策略：

```python
async def batch_sync_to_neo4j(batch_size=1000):
    # 查询未同步的资产
    unsync_assets = await get_unsync_assets(limit=batch_size)

    # 批量同步
    await neo4j_batch_write(unsync_assets)

    # 标记为已同步
    await mark_as_synced(unsync_assets)
```

### 4.3 同步实现

#### 4.3.1 节点同步

```python
from neo4j import GraphDatabase

class Neo4jSync:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    async def sync_organization(self, org_data: dict):
        """同步组织节点"""
        with self.driver.session() as session:
            query = """
            MERGE (o:Organization {id: $id})
            SET o.name = $name,
                o.is_primary = $is_primary,
                o.tier = $tier,
                o.asset_count = $asset_count,
                o.risk_score = $risk_score,
                o.scope_policy = $scope_policy
            """
            session.run(query, **org_data)

    async def sync_ip(self, ip_data: dict):
        """同步 IP 节点"""
        with self.driver.session() as session:
            query = """
            MERGE (i:IP {id: $id})
            SET i.address = $address,
                i.version = $version,
                i.is_cloud = $is_cloud,
                i.is_internal = $is_internal,
                i.is_cdn = $is_cdn,
                i.open_ports_count = $open_ports_count,
                i.risk_score = $risk_score,
                i.vuln_critical_count = $vuln_critical_count,
                i.country_code = $country_code,
                i.asn_number = $asn_number,
                i.scope_policy = $scope_policy
            """
            session.run(query, **ip_data)

    async def batch_sync_nodes(self, nodes: list, node_type: str):
        """批量同步节点"""
        with self.driver.session() as session:
            # 根据节点类型选择对应的 MERGE 语句
            query = self._get_merge_query(node_type)
            session.execute_write(lambda tx: tx.run(query, nodes=nodes))
```

#### 4.3.2 关系同步

```python
async def sync_relationship(self, rel_data: dict):
    """同步关系"""
    with self.driver.session() as session:
        query = """
        MATCH (source {id: $source_id})
        MATCH (target {id: $target_id})
        MERGE (source)-[r:$rel_type]->(target)
        SET r += $properties
        """
        session.run(
            query,
            source_id=rel_data['source_id'],
            target_id=rel_data['target_id'],
            rel_type=rel_data['type'],
            properties=rel_data['properties']
        )

async def batch_sync_relationships(self, relationships: list):
    """批量同步关系"""
    with self.driver.session() as session:
        query = """
        UNWIND $rels AS rel
        MATCH (source {id: rel.source_id})
        MATCH (target {id: rel.target_id})
        CALL apoc.merge.relationship(
            source, rel.type, {}, rel.properties, target
        ) YIELD rel AS r
        RETURN count(r)
        """
        session.run(query, rels=relationships)
```

### 4.4 一致性保证

#### 4.4.1 事务性

```python
async def import_with_transaction(assets: list):
    """使用事务保证一致性"""
    async with pg_transaction() as tx:
        try:
            # 1. 写入 PostgreSQL
            pg_ids = await tx.write_assets(assets)

            # 2. 同步到 Neo4j
            await sync_to_neo4j(pg_ids)

            # 3. 提交事务
            await tx.commit()
        except Exception as e:
            # 回滚 PostgreSQL
            await tx.rollback()
            # 清理 Neo4j（如果已写入）
            await cleanup_neo4j(pg_ids)
            raise e
```

#### 4.4.2 对账机制

```python
async def reconcile_data():
    """对账：检查 PG 和 Neo4j 的数据一致性"""
    # 1. 统计 PG 中的资产数量
    pg_counts = await count_pg_assets()

    # 2. 统计 Neo4j 中的节点数量
    neo4j_counts = await count_neo4j_nodes()

    # 3. 比对差异
    diff = compare_counts(pg_counts, neo4j_counts)

    # 4. 如果有差异，记录日志并触发重新同步
    if diff:
        logger.warning(f"Data inconsistency detected: {diff}")
        await resync_missing_data(diff)
```

---

## 5. 索引与性能优化

### 5.1 PostgreSQL 索引策略

#### 5.1.1 核心索引

已在表结构中定义的索引：

- **唯一索引**：主键、唯一字段（如 IP address、Domain name）
- **B-Tree 索引**：常用查询字段（如 scope_policy、is_resolved）
- **GIN 索引**：JSONB 字段、全文搜索
- **GiST 索引**：INET/CIDR 字段（IP 地址范围查询）
- **Trigram 索引**：模糊搜索字段（如 name、banner）

#### 5.1.2 复合索引

针对高频组合查询创建复合索引：

```sql
-- 域名 + 解析状态
CREATE INDEX idx_domain_root_resolved ON assets_domain(root_domain, is_resolved);

-- IP + 范围策略
CREATE INDEX idx_ip_scope_cloud ON assets_ip(scope_policy, is_cloud);

-- 服务 + 端口 + HTTP
CREATE INDEX idx_service_port_http ON assets_service(port, is_http);

-- 证书 + 过期状态
CREATE INDEX idx_cert_expired_days ON assets_certificate(is_expired, days_to_expire);
```

#### 5.1.3 部分索引

针对特定条件的查询创建部分索引：

```sql
-- 只索引范围内的资产
CREATE INDEX idx_ip_in_scope ON assets_ip(address) WHERE scope_policy = 'IN_SCOPE';

-- 只索引已解析的域名
CREATE INDEX idx_domain_resolved ON assets_domain(name) WHERE is_resolved = true;

-- 只索引高风险服务
CREATE INDEX idx_service_high_risk ON assets_service(port, product)
WHERE has_exploit = true;
```

### 5.2 Neo4j 性能优化

#### 5.2.1 索引优化

```cypher
// 复合索引（Neo4j 5.x+）
CREATE INDEX org_primary_tier IF NOT EXISTS
FOR (o:Organization) ON (o.is_primary, o.tier);

CREATE INDEX ip_scope_cloud IF NOT EXISTS
FOR (i:IP) ON (i.scope_policy, is_cloud);

CREATE INDEX service_port_http IF NOT EXISTS
FOR (s:Service) ON (s.port, s.is_http);
```

#### 5.2.2 查询优化

```cypher
// 使用 LIMIT 限制结果集
MATCH (org:Organization)-[*1..3]->(asset)
WHERE org.id = 'org:123'
RETURN asset
LIMIT 500

// 使用 WITH 子句分段查询
MATCH (org:Organization {id: 'org:123'})
WITH org
MATCH (org)-[:OWNS_NETBLOCK]->(nb:Netblock)
WITH org, collect(nb) AS netblocks
MATCH (nb)-[:CONTAINS]->(ip:IP)
RETURN org, netblocks, collect(ip) AS ips

// 避免笛卡尔积
// 不推荐
MATCH (d:Domain), (ip:IP)
WHERE d.name CONTAINS 'target' AND ip.is_cloud = true
RETURN d, ip

// 推荐
MATCH (d:Domain)-[:RESOLVES_TO]->(ip:IP)
WHERE d.name CONTAINS 'target' AND ip.is_cloud = true
RETURN d, ip
```

#### 5.2.3 批量操作优化

```cypher
// 使用 UNWIND 批量创建节点
UNWIND $nodes AS node
MERGE (n:IP {id: node.id})
SET n += node.properties

// 使用 CALL {} IN TRANSACTIONS 分批处理（Neo4j 4.4+）
CALL {
    UNWIND $nodes AS node
    MERGE (n:IP {id: node.id})
    SET n += node.properties
} IN TRANSACTIONS OF 1000 ROWS
```

### 5.3 查询缓存策略

#### 5.3.1 Redis 缓存

```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_query(ttl=300):
    """查询结果缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行查询
            result = await func(*args, **kwargs)

            # 写入缓存
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# 使用示例
@cache_query(ttl=600)
async def get_organization_assets(org_id: str):
    """查询组织的所有资产（缓存 10 分钟）"""
    return await db.query(...)
```

#### 5.3.2 缓存失效策略

```python
async def invalidate_cache(entity_type: str, entity_id: str):
    """使缓存失效"""
    # 删除相关的缓存键
    pattern = f"*{entity_type}*{entity_id}*"
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

# 在数据更新时调用
async def update_asset(asset_id: str, data: dict):
    # 更新数据库
    await db.update(asset_id, data)

    # 使缓存失效
    await invalidate_cache("asset", asset_id)
```

---

## 6. 数据迁移与备份

### 6.1 PostgreSQL 备份

#### 6.1.1 逻辑备份

```bash
# 全库备份
pg_dump -h localhost -U postgres -d externalhound \
    -F c -b -v -f externalhound_backup_$(date +%Y%m%d).dump

# 仅备份数据（不含结构）
pg_dump -h localhost -U postgres -d externalhound \
    --data-only -F c -f externalhound_data_$(date +%Y%m%d).dump

# 仅备份特定表
pg_dump -h localhost -U postgres -d externalhound \
    -t assets_ip -t assets_domain \
    -F c -f externalhound_assets_$(date +%Y%m%d).dump
```

#### 6.1.2 物理备份

```bash
# 使用 pg_basebackup
pg_basebackup -h localhost -U postgres -D /backup/pg_base \
    -F tar -z -P -v

# 使用 WAL 归档实现 PITR（时间点恢复）
# 在 postgresql.conf 中配置
archive_mode = on
archive_command = 'cp %p /backup/pg_wal/%f'
```

#### 6.1.3 恢复

```bash
# 恢复全库
pg_restore -h localhost -U postgres -d externalhound \
    -v externalhound_backup_20260116.dump

# 恢复特定表
pg_restore -h localhost -U postgres -d externalhound \
    -t assets_ip externalhound_backup_20260116.dump
```

### 6.2 Neo4j 备份

#### 6.2.1 在线备份

```bash
# 使用 neo4j-admin dump（需要停止数据库）
neo4j-admin database dump neo4j \
    --to=/backup/neo4j_dump_$(date +%Y%m%d).dump

# 使用 APOC 导出（在线）
CALL apoc.export.cypher.all("/backup/neo4j_export_$(date +%Y%m%d).cypher", {
    format: "cypher-shell",
    useOptimizations: {type: "UNWIND_BATCH", unwindBatchSize: 20}
})
```

#### 6.2.2 增量备份

```bash
# 使用 neo4j-admin backup（企业版功能）
neo4j-admin backup --backup-dir=/backup/neo4j_incremental \
    --database=neo4j --verbose
```

#### 6.2.3 恢复

```bash
# 从 dump 恢复
neo4j-admin database load neo4j \
    --from-path=/backup/neo4j_dump_20260116.dump \
    --overwrite-destination=true

# 从 Cypher 脚本恢复
cat /backup/neo4j_export_20260116.cypher | cypher-shell -u neo4j -p password
```

### 6.3 MinIO 备份

```bash
# 使用 mc（MinIO Client）镜像备份
mc mirror minio/externalhound /backup/minio_mirror

# 定期备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d)
mc mirror minio/externalhound /backup/minio_$DATE
```

### 6.4 自动化备份脚本

```bash
#!/bin/bash
# backup_all.sh - 全量备份脚本

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/$DATE"

mkdir -p $BACKUP_DIR

# 1. 备份 PostgreSQL
echo "Backing up PostgreSQL..."
pg_dump -h localhost -U postgres -d externalhound \
    -F c -f $BACKUP_DIR/postgres.dump

# 2. 备份 Neo4j
echo "Backing up Neo4j..."
neo4j-admin database dump neo4j \
    --to=$BACKUP_DIR/neo4j.dump

# 3. 备份 MinIO
echo "Backing up MinIO..."
mc mirror minio/externalhound $BACKUP_DIR/minio

# 4. 压缩备份
echo "Compressing backup..."
tar -czf /backup/externalhound_$DATE.tar.gz $BACKUP_DIR

# 5. 清理旧备份（保留 30 天）
find /backup -name "externalhound_*.tar.gz" -mtime +30 -delete

echo "Backup completed: /backup/externalhound_$DATE.tar.gz"
```

---

## 7. 安全与权限控制

> 说明：v1.0 不包含用户与权限控制，本节作为后续版本参考。

### 7.1 PostgreSQL 安全

#### 7.1.1 用户与角色

```sql
-- 创建只读用户
CREATE ROLE readonly_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE externalhound TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- 创建应用用户（读写权限）
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE externalhound TO app_user;
GRANT USAGE, CREATE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- 创建管理员用户
CREATE ROLE admin_user WITH LOGIN PASSWORD 'secure_password' SUPERUSER;
```

#### 7.1.2 行级安全（RLS）

```sql
-- 启用行级安全
ALTER TABLE assets_organization ENABLE ROW LEVEL SECURITY;

-- 创建策略：用户只能看到自己创建的资产
CREATE POLICY org_isolation ON assets_organization
    FOR SELECT
    USING (created_by = current_user);

-- 创建策略：管理员可以看到所有资产
CREATE POLICY org_admin_access ON assets_organization
    FOR ALL
    TO admin_user
    USING (true);
```

#### 7.1.3 数据加密

```sql
-- 使用 pgcrypto 扩展加密敏感字段
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 加密存储
INSERT INTO assets_organization (name, metadata)
VALUES ('Target Corp', pgp_sym_encrypt('{"secret": "data"}', 'encryption_key'));

-- 解密查询
SELECT name, pgp_sym_decrypt(metadata::bytea, 'encryption_key') AS metadata
FROM assets_organization;
```

### 7.2 Neo4j 安全

#### 7.2.1 用户与角色

```cypher
// 创建只读用户
CREATE USER readonly SET PASSWORD 'secure_password' CHANGE NOT REQUIRED;
GRANT ROLE reader TO readonly;

// 创建应用用户
CREATE USER appuser SET PASSWORD 'secure_password' CHANGE NOT REQUIRED;
GRANT ROLE editor TO appuser;

// 创建管理员
CREATE USER admin SET PASSWORD 'secure_password' CHANGE NOT REQUIRED;
GRANT ROLE admin TO admin;
```

#### 7.2.2 访问控制

```cypher
// 限制用户只能访问特定标签
DENY MATCH {*} ON GRAPH neo4j NODES Organization TO readonly;
GRANT MATCH {*} ON GRAPH neo4j NODES IP, Domain, Service TO readonly;

// 限制用户只能执行特定操作
GRANT TRAVERSE ON GRAPH neo4j TO appuser;
GRANT READ {*} ON GRAPH neo4j TO appuser;
DENY WRITE ON GRAPH neo4j TO appuser;
```

### 7.3 应用层安全

#### 7.3.1 连接字符串加密

```python
# 使用环境变量存储敏感信息
import os
from cryptography.fernet import Fernet

# 加密连接字符串
def encrypt_connection_string(conn_str: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(conn_str.encode()).decode()

# 解密连接字符串
def decrypt_connection_string(encrypted: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()

# 使用
encryption_key = os.getenv('ENCRYPTION_KEY')
pg_conn = decrypt_connection_string(os.getenv('PG_CONN_ENCRYPTED'), encryption_key)
```

#### 7.3.2 SQL 注入防护

```python
# 使用参数化查询
async def get_ip_by_address(address: str):
    # 安全：使用参数化查询
    query = "SELECT * FROM assets_ip WHERE address = $1"
    result = await db.fetch(query, address)

    # 不安全：字符串拼接（禁止使用）
    # query = f"SELECT * FROM assets_ip WHERE address = '{address}'"
```

---

## 8. 总结

### 8.1 设计亮点

1. **双数据库架构**：PostgreSQL 存储详细元数据，Neo4j 存储关系图谱，各司其职
2. **JSONB 灵活性**：使用 JSONB 存储可变元数据，适应多样化的扫描工具输出
3. **完善的索引**：B-Tree、GIN、GiST、Trigram 多种索引类型，支持各类查询场景
4. **数据一致性**：明确的同步策略和对账机制，保证双库数据一致
5. **性能优化**：缓存策略、批量操作、查询优化，满足高性能需求
6. **安全可靠**：完善的备份恢复机制、权限控制、数据加密

### 8.2 实施建议

1. **分阶段实施**：
   - 第一阶段：实现核心资产表和基础关系
   - 第二阶段：完善辅助表和高级查询
   - 第三阶段：优化性能和安全加固

2. **监控与调优**：
   - 使用 Prometheus + Grafana 监控数据库性能
   - 定期分析慢查询并优化索引
   - 监控数据库连接池和缓存命中率

3. **数据治理**：
   - 定期清理过期数据
   - 归档历史数据
   - 维护数据质量

### 8.3 扩展性考虑

1. **水平扩展**：
   - PostgreSQL：使用 Citus 或分片策略
   - Neo4j：使用 Fabric 或 Causal Cluster

2. **垂直扩展**：
   - 增加数据库服务器资源
   - 使用 SSD 提升 I/O 性能

3. **读写分离**：
   - PostgreSQL：主从复制，读请求分发到从库
   - Neo4j：使用 Read Replica

---

**文档版本**：v1.0
**最后更新**：2026-01-16
**维护者**：ExternalHound 开发团队
