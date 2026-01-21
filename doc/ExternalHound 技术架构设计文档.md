# ExternalHound 技术架构设计文档

## 1. 核心数据模型总览

本模型采用**“实体归属 + 网络拓扑 + 服务指纹”**的三维结构。

- **归属层**：通过 Organization 锁定资产范围。
- **网络层**：通过 Netblock, IP, Domain, Certificate 构建资产的物理和逻辑连接。
- **服务层**：通过 Service 节点（融合 L4/L7）和 ClientApplication 描述具体的攻击面。

------

## 2. 节点数据结构详解 (Node Schema)

以下定义了所有 8 类核心节点的 JSON 结构、字段含义及数据类型。

**约定**：Neo4j 节点的 `id` 为业务唯一标识，与 PostgreSQL 的 `external_id` 保持一致；PostgreSQL 仍保留 UUID 主键用于内部关联。

### 2.1 商业与归属节点

#### Node: `Organization` (组织/公司)

**描述**：资产图谱的根节点，代表商业实体。所有的资产最终都应追溯到某个 Organization。

Neo4j

```
// Neo4j Node: Organization
{
  "id": "org:91110000XXXXXX",       // [PK] 关联键，必须与 PG external_id 一致
  "label": "Organization",
  
  // === 核心展示属性 ===
  "name": "某某科技集团",           // 节点显示的简短名称 (Short Name)
  
  // === 拓扑查询属性 (Cypher用于过滤) ===
  "is_primary": true,               // 是否为一级目标/根目标 (用于快速高亮核心资产)
  "tier": 0,                        // 层级：0=总部, 1=一级子公司, 2=孙公司... (用于控制递归深度)
  "asset_count": 15420,             // 聚合属性：该组织下的资产总数 (用于地图上节点大小的渲染)
  "risk_score": 9.5,                // 聚合属性：风险评分 (0-10)，用于热力图染色
  
  // === 权限与范围控制 ===
  "scope_policy": "IN_SCOPE"        // 范围策略：IN_SCOPE(纳入分析), OUT_OF_SCOPE(红线资产)
}
```

PostgreSQL

```json
// PostgreSQL metadata column
{
  // === 基础信息 (OSINT/工商) ===
  "full_name": "某某科技集团有限公司", // 完整的注册名称
  "english_name": "MoMo Tech Group Co., Ltd.",
  "credit_code": "91110000XXXXXX",    // 统一社会信用代码
  "description": "一家主要从事互联网金融与人工智能的高科技企业...",
  "industries": ["Internet", "Finance", "AI"], // 行业标签
  "headquarters": "Beijing, China",
  "stock_symbol": "HK:09988",         // 股票代码 (用于关联金融数据)
  
  // === 联系人/应急响应 ===
  "contacts": [
    {"role": "CISO", "email": "security@momo.com"},
    {"role": "Admin", "email": "admin@momo.com"}
  ],

  // === 审计与元数据 ===
  "source": "Tianyancha",             // 数据来源 (天眼查/企查查/人工录入)
  "tags": ["Nasdaq", "China-Top500"], // 业务标签
  "created_by": "user_admin",
  "notes": "该目标将于 Q4 进行红队演练，注意避开双11高峰期。",
  
  "update_time":"更新时间",
  "create_time":"创建时间"
}
```



#### Node: `Netblock` (网段)

**描述**：代表 IP 地址段（CIDR），用于聚合管理分散的 IP 资产。

Neo4j

```
// Neo4j Node: Netblock
{
  "id": "cidr:47.100.0.0/16",       // [PK] 唯一标识
  "label": "Netblock",

  // === 核心展示与拓扑属性 ===
  "cidr": "47.100.0.0/16",          // 网段地址 (用于显示)
  "asn_number": "AS37963",          // AS号 (用于在图中按 ISP/ASN 快速聚类)
  
  // === 统计属性 (决定节点大小/颜色) ===
  "capacity": 65536,                // 网段容量 (2^n)
  "live_count": 128,                // 存活 IP 数量 (定期从 PG 同步，用于计算使用率)
  "risk_score": 7.5,                // 该网段内聚合的风险值
  
  // === 权限与范围控制 (关键) ===
  "scope_policy": "IN_SCOPE",       // IN_SCOPE, OUT_OF_SCOPE (黑名单网段), CAUTION (敏感网段)
  "is_internal": false              // 是否为内网段 (RFC1918) 或 VPN 网段
}
```

PostgreSQL

```json
// PostgreSQL metadata column
{
  // === Whois 与 归属信息 (OSINT) ===
  "net_name": "ALIBABA-CN-NET",     // 网络名称 (Whois)
  "description": "Alibaba (China) Technology Co., Ltd.", // 详细描述
  "org_handle": "ORG-ALIBABA-1",    // 注册机构句柄
  "maintainer": "MAINT-ALI-CN",     // 维护者 ID
  "abuse_contact": "abuse@aliyun.com", // 滥用举报邮箱 (红队用来判定被发现的风险)
  
  // === 地理位置 (Geolocation) ===
  "location": {
    "country": "CN",
    "region": "Zhejiang",
    "city": "Hangzhou",
    "latitude": 30.29,
    "longitude": 120.16
  },

  // === 来源与元数据 ===
  "source": "BGP_View",             // 数据来源：Whois, BGP, 或 Manual (手工添加)
  "tags": ["Cloud", "Production"],  // 业务标签
  "discovered_at": "2023-10-01T12:00:00Z",
  "last_whois_update": "2023-10-29T12:00:00Z"
  
  "update_time":"更新时间",
  "create_time":"创建时间"
}
```



### 2.2 网络与基础节点

#### Node: `Domain` (域名)

**描述**：DNS 体系中的节点。**注意：本架构不区分 Domain 和 Subdomain，所有层级域名均为 Domain 节点**。

Neo4j

```
// Neo4j Node: Domain
{
  "id": "domain:api.target.com",      // [PK] 唯一标识
  "label": "Domain",

  // === 核心拓扑索引 ===
  "name": "api.target.com",           // 完整域名
  "root_domain": "target.com",        // 根域名 (超级高频的聚合字段，必须在 Neo4j 建索引)
  "tier": 2,                          // 层级深度：target.com(1) -> api.target.com(2)
  
  // === 攻击面状态 (快速过滤用) ===
  "is_resolved": true,                // 是否能解析出 IP (用于隐藏 NXDOMAIN/死域名)
  "is_wildcard": false,               // 是否为泛解析域名 (*.target.com) - 避免爆破死循环
  "is_internal": false,               // 是否解析到内网 IP (Intranet) - 关键风险标识
  "has_waf": true,                    // 是否有 WAF 防护 (红队更喜欢找 false 的节点)
  
  // === 范围控制 ===
  "scope_policy": "IN_SCOPE"          // 继承或覆盖的范围标记
}
```

PostgreSQL

```json
// PostgreSQL metadata column
{
  // === DNS 详情 (重文本) ===
  "records": {
    "A": ["1.2.3.4", "1.2.3.5"],      // 当前解析记录
    "CNAME": ["aliyun-waf.com"],      // 别名 (用于判断 CDN/WAF 厂商)
    "MX": ["mxbiz1.qq.com"],          // 邮件服务器
    "TXT": ["v=spf1 include:spf..."], // SPF 记录 (反垃圾邮件/资产归属验证)
    "NS": ["ns1.alidns.com"]          // 域名服务器
  },

  // === 合规与注册信息 (OSINT) ===
  "icp_license": "京ICP备xxxxx号-1",  // ICP 备案号 (中国特有，非常重要)
  "registrar": "Godaddy",             // 注册商
  "registrant_email": "admin@target.com", // 注册人邮箱 (用于反查)
  "creation_date": "2015-01-01",
  "expiration_date": "2025-01-01",

  // === 技术栈探测 (非拓扑类) ===
  "tech_stack": {
    "cdn_provider": "Cloudflare",     // CDN 厂商
    "waf_product": "Aliyun WAF",      // 具体 WAF 型号
    "server": "Nginx"                 // HTTP Server 头
  },

  // === 来源与取证 ===
  "sources": ["Subfinder", "Certificate Transparency", "BruteForce"], // 发现渠道
  "screenshot_path": "s3://bucket/snapshots/hash.jpg", // 网页截图路径
  "page_title": "用户登录中心 - Target", // 网页标题 (用于文本搜索)
  "http_status_code": 200,             // 最近一次访问状态码
  
  "update_time":"更新时间",
  "create_time":"创建时间"
}
```



#### Node: `IP` (主机)

**描述**：网络空间的物理锚点。**它是外部扫描结果的状态载体**。

Neo4j

```json
// Neo4j Node: IP
{
  "id": "ip:47.100.1.15",           // [PK] 唯一标识
  "label": "IP",

  // === 核心拓扑属性 ===
  "address": "47.100.1.15",         // IP 地址字符串
  "version": 4,                     // 4 或 6
  "is_cloud": true,                 // 是否为云主机 (重要战术属性)
  "is_internal": false,             // 是否为内网 IP (10.x, 192.168.x)
  "is_cdn": false,                  // 是否为 CDN 节点 (Cloudflare/Akamai) - 避免无效攻击
  
  // === 聚合统计 (加速渲染) ===
  "open_ports_count": 12,           // 开放端口总数 (用于过滤 "大门大开" 的机器)
  "risk_score": 8.5,                // 聚合风险值
  "vuln_critical_count": 1,         // 包含的严重漏洞数量 (用于红队优先打击)

  // === 地理/归属索引 ===
  "country_code": "CN",             // 国家代码 (用于按国家过滤)
  "asn_number": "AS37963",          // AS 号 (用于关联同一运营商的资产)

  // === 范围控制 ===
  "scope_policy": "IN_SCOPE"
}
```

PostgreSQL

```json
// PostgreSQL metadata column
{
  // === 操作系统指纹 (OSINT/Active) ===
  "os_info": {
    "name": "Ubuntu",
    "flavor": "Focal Fossa",
    "version": "20.04 LTS",
    "kernel": "Linux 5.4.0",
    "cpe": "cpe:/o:canonical:ubuntu_linux:20.04", // CPE 标准标识
    "confidence": 95,                 // 指纹置信度
    "fingerprint_source": "Nmap OSDetection"
  },

  // === 精确地理与网络位置 ===
  "geo_location": {
    "city": "Hangzhou",
    "region": "Zhejiang",
    "latitude": 30.2936,
    "longitude": 120.1614,
    "timezone": "Asia/Shanghai",      // 用于按时区展示与分组
    "isp": "Aliyun Computing Co., LTD"
  },

  // === 云元数据 (如果是云主机) ===
  "cloud_metadata": {
    "provider": "Aliyun",
    "region_id": "cn-hangzhou",
    "instance_type": "ecs.t5-lc1m1.small", // 实例规格
    "tags": ["Production", "K8s-Node"]    // 云控制台读取的标签
  },

  "update_time":"更新时间",
  "create_time":"创建时间"


}
```



#### Node: `Certificate` (证书)

**描述**：SSL/TLS 证书实体。它是连接“孤立 IP”和“隐蔽域名”的关键桥梁。

Neo4j

```json
// Neo4j Node: Certificate
{
  "id": "cert:a1b2c3d4e5...",       // [PK] 格式：cert:SHA256指纹
  "label": "Certificate",

  // === 核心拓扑索引 ===
  "subject_cn": "api.target.com",   // 主题通用名称 (CN)
  "issuer_cn": "DigiCert Inc",      // 颁发者通用名称 (用于聚合：是否都是大厂签发？)
  "issuer_org": "DigiCert Global",  // 颁发者组织 (O)
  
  // === 风险与时间属性 (用于过滤) ===
  "valid_from": 1672531200,         // 生效时间戳
  "valid_to": 1704067200,           // 过期时间戳 (用于 Range Query: 查即将过期的)
  "days_to_expire": 30,             // 剩余天数 (每日计算更新，用于热力图染色：红色=即将过期)
  
  "is_expired": false,              // 是否已过期 (高频过滤器)
  "is_self_signed": false,          // 是否自签名 (高风险：通常意味着测试环境或影子资产)
  "is_revoked": false,              // 是否被吊销 (CRL/OCSP 检查结果)
  
  // === 统计属性 ===
  "san_count": 15,                  // SAN 包含的域名数量 (数量巨大通常意味着这是个核心负载均衡器)
  "scope_policy": "IN_SCOPE"        // 通常跟随发现它的 IP
}
```

PostgreSQL

```json
// PostgreSQL metadata column
{
  // === 完整身份信息 ===
  "subject": {
    "C": "CN", "ST": "Beijing", "L": "Beijing",
    "O": "Target Corp", "OU": "IT Dept",
    "CN": "api.target.com"
  },
  "issuer": {
    "C": "US", "O": "DigiCert Inc", "CN": "DigiCert Global CA"
  },
  
  // === SANs (情报核心) ===
  // 这里可能包含上百个域名，Neo4j 存不下，也不方便检索
  "subject_alt_names": [
    "api.target.com",
    "dev-internal.target.com", // 这种隐蔽域名在 DNS 爆破中很难发现
    "legacy-payment.target.com"
  ],

  // === 加密技术细节 (用于合规审计) ===
  "public_key": {
    "algorithm": "RSA",
    "bits": 2048,           // <2048 为高风险
    "exponent": 65537
  },
  "signature_algorithm": "SHA256withRSA", // 检查是否使用 SHA1 (弱哈希)
  "serial_number": "543216789...",
  "fingerprints": {
    "sha1": "...",
    "sha256": "...",
    "md5": "..."
  },

  // === 证书链与验证 ===
  "chain_validation": {
    "is_trusted": true,     // 根证书是否受操作系统信任
    "chain_depth": 2,
    "root_ca": "DigiCert Global Root CA"
  },

  // === 监控与告警配置 (Monitor Config) ===
  // 证书不需要主动扫描，状态可由外部系统导入
  "monitor_config": {
    "alert_before_days": 14,      // 过期前14天告警
    "track_transparency": true,   // 是否追踪 CT (Certificate Transparency) 日志
    "allow_wildcard": false       // 如果发现变成泛域名证书，是否告警
  },

  // === 原始数据引用 ===
  "raw_pem_path": "s3://certs/a1b2c3...pem", // 原始 PEM 文件存储路径
  
	"update_time":"更新时间",
  "create_time":"创建时间"
}
```



### 2.3 服务与应用节点

#### Node: `Service` (全能服务)

**描述**：**最小资产单元**。它聚合了 L4（传输层端口）和 L7（应用层 Web 指纹）的所有信息。

Neo4j

```json
// Neo4j Node: Service
{
  "id": "svc:47.100.1.15:8080",     // [PK] 格式：svc:IP:Port (即使是UDP也建议加上协议后缀防冲突，如 svc:IP:Port:UDP)
  "label": "Service",

  // === 核心拓扑与识别 ===
  "port": 8080,                     // 端口号 (Int)
  "protocol": "TCP",                // TCP / UDP
  "service_name": "http-alt",       // Nmap 识别出的服务名 (http, ssh, mysql, rdp)
  "product": "Nginx",               // 核心软件名称 (用于聚类：所有 Nginx 节点)
  "version": "1.18.0",              // 核心版本号 (存 Neo4j 方便一眼看出是否老旧)
  
  // === 战术属性 (红队视角) ===
  "is_http": true,                  // 是否为 Web 服务 (用于识别 Web 资产)
  "is_admin": false,                // 是否为管理后台 (SSH, RDP, Telnet, WebConsole)
  
  // === 风险聚合 ===
  "has_exploit": true,              // 是否存在已知 EXP (攻击者最爱)
  
  // === 范围控制 ===
  "scope_policy": "IN_SCOPE"
}
```

PostgreSQL

```json
{
  // === 1. 基础索引与端口信息 (Port Info) ===
  "id": "svc:47.100.1.15:8443",        // [PK] 唯一标识
  "ip_address": "47.100.1.15",         // IP地址 (用于快速检索)
  "port": 8443,                        // 端口号
  "protocol": "TCP",                   // 协议类型

  // === 2. 核心指纹信息 (Fingerprints) ===
  "service_name": "https-alt",         // Nmap/Masscan 识别的服务名
  "product": "Sangfor SSL VPN",        // 核心组件/产品名称
  "version": "M7.6.1",                 // 版本号
  "http_title": "Sangfor VPN Login - Welcome", // 网页标题 (HTTP特有，非常关键)

  // === 3. 项目定位/资产属性 (Asset Category) ===
  // [关键字段] 用于快速分类高价值资产
  // 常见值: "VPN", "Gateway", "S3", "OA", "Mail", "Monitor", "General"
  "asset_category": "VPN",             

  // === 5. 原始数据 (Raw Data) ===
  // 用于人工复核或正则匹配
  "banner": "HTTP/1.1 200 OK\r\nServer: Sangfor Http Server\r\n...", 
  "response_headers": "Content-Type: text/html\nSet-Cookie: SF_SESSION=...",

  // === 6. 杂项与扩展信息 (JSONB - extra_info) ===
  // 存放那些“如果不存有点可惜，存了又不常搜”的数据
  "extra_info": {
    "screenshot_url": "s3://scan-results/screenshots/svc_47_100_1_15_8443.jpg", // 截图链接
    "tech_stacks": [                   // Wappalyzer 详细组件列表
      {"name": "jQuery", "version": "1.12.4"},
      {"name": "Vue.js", "version": "2.6.10"}
    ],
    "final_redirect": "https://47.100.1.15:8443/portal/login", // 最终跳转地址
    "is_honeypot": false               // 是否疑似蜜罐
  },

	"update_time":"更新时间",
  "create_time":"创建时间"
}
```



#### Node: `ClientApplication` (客户端)

**描述**：移动端 App、PC 客户端或微信小程序。

Neo4j

```
// Neo4j Node: ClientApplication
{
  "id": "app:com.target.mobile",       // [PK] 唯一标识
  "label": "ClientApplication",

  // === 核心拓扑索引 ===
  "name": "Target Admin",              // 应用名
  "bundle_id": "com.target.mobile",    // 包名
  "platform": "Android",               // Android, iOS, Windows
  
  // === 战术属性 (用于图谱过滤) ===
  "app_category": "Enterprise",        // "Enterprise"(内部版-高价值), "Consumer"(C端)
  "is_hardened": true,                 // 是否加固 (未加固的 App 是逆向首选)
  
  // === 范围控制 ===
  "scope_policy": "IN_SCOPE"
}
```

PostgreSQL

```json
// PostgreSQL Row Data
{
  // === 1. 基础身份 ===
  "id": "app:com.target.mobile",       // [PK]
  "name": "Target Admin",
  "bundle_id": "com.target.mobile",
  "platform": "Android",
  "version": "2.1.0",

  // === 2. 项目定位 (Asset Category) ===
  // [关键] 类似于 Service 的分类，红队优先看 "Enterprise" 或 "Legacy"
  "app_category": "Enterprise",

  // === 4. 资源与防护 ===
  "download_url": "https://oss-cn.../admin-v2.apk", // 安装包地址
  "hardening_vendor": "Qihoo 360",     // 加固厂商 (决定脱壳策略)

  // === 5. 扩展信息 (JSONB) ===
  "extra_info": {
    "permissions": ["CAMERA", "READ_CONTACTS"], // 敏感权限
    "signature": "a1b2c3d4...",        // 签名指纹
    "file_size": 45000000,             // 字节
    "compile_time": "2023-01-01"
  },
	"update_time":"更新时间",
  "create_time":"创建时间"
}
```



#### Node: `Credential` (凭证 - 攻击路径用)

Neo4j

```
// Neo4j Node: Credential
{
  "id": "cred:ak-xxxx",                // [PK] 唯一标识 (通常是 Hash 或 KeyID)
  "label": "Credential",

  // === 核心属性 ===
  "type": "AccessKey",                 // AccessKey, PrivateKey, DB_Password
  "is_valid": true,                    // 是否验证有效 (红队最关心的属性)
  "provider": "AWS",                   // 云厂商/服务商 (AWS, Aliyun, SSH)
  
  // === 统计 ===
  "leaked_count": 3                    // 该凭证在多少个地方被泄露了 (复用程度)
}
```

PostgreSQL

```json
// PostgreSQL Row Data
{
  // === 1. 凭证核心 ===
  "id": "cred:ak-xxxx",                // [PK]
  "type": "AccessKey",                 // 类型
  
  // [敏感] 实际的密钥内容。如果担心安全，可存加密后的密文。
  "content": {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  },

  // === 2. 来源上下文 ===
  // 记录是在哪里发现的 (文件路径、代码行数)
  "source_context": "config.js line 15, variable 'aws_key'", 

  // === 3. 验证结果 ===
  "validation_result": {
    "status": "VALID",                 // VALID, INVALID, UNKNOWN
    "permissions": ["s3:ListBuckets"], // 验证后获取的权限列表
    "remark": "Connected successfully"
  },

  "discovered_at": "2023-10-29T12:00:00Z"
}
```



## 3. 边关系详解 (Edge Schema)

共有 **13 种** 边类型，涵盖了归属、包含、解析、历史、承载、路由、通信等七大维度。

### 3.1 归属类 (Ownership)

#### Edge: `SUBSIDIARY` (子公司)

- **Source:** `Organization` (父公司)
- **Target:** `Organization` (子公司)
- **Properties:**
  - `percent`: `100` (持股比例，Float)
  - `type`: `"WhollyOwned"` (关系类型：全资/控股/参股)
- **含义**：表示商业上的股权控制关系，用于扩展攻击面范围。

#### Edge: `OWNS_NETBLOCK` (拥有网段)

- **Source:** `Organization`
- **Target:** `Netblock`
- **Properties:**
  - `source`: `"Whois"` (数据来源)
  - `confidence`: `0.9` (置信度)
- **含义**：确认该 CIDR 网段在法律上归属于该组织。

#### Edge: `OWNS_ASSET` (拥有独立资产)

- **Source:** `Organization`
- **Target:** `IP`
- **Properties:**
  - `source`: `"Whois"`
- **含义**：当一个 IP 不属于任何已知的 Netblock，但 Whois 显示属于该组织时使用。

#### Edge: `OWNS_DOMAIN` (拥有域名)

- **Source:** `Organization`
- **Target:** `Domain`
- **Properties:**
  - `source`: `"ICP"` (ICP备案) 或 `"Whois"`
- **含义**：通过 ICP 备案或注册人邮箱确认域名的法律归属。

### 3.2 拓扑类 (Topology)

#### Edge: `CONTAINS` (包含)

- **Source:** `Netblock`
- **Target:** `IP`
- **含义**：物理网络层级关系，表示 IP 位于该 CIDR 范围内。

#### Edge: `SUBDOMAIN` (子域名层级)

- **Source:** `Domain` (父，如 target.com)
- **Target:** `Domain` (子，如 api.target.com)
- **Properties:**
  - `is_direct`: `true` (是否为直接下级)
- **含义**：构建域名的树状层级结构，方便进行资产聚合展示。

### 3.3 解析类 (Resolution)

#### Edge: `RESOLVES_TO` (当前解析)

- **Source:** `Domain`
- **Target:** `IP`
- **Properties:**
  - `record_type`: `"A"` (记录类型)
  - `last_seen`: `"2023-10-29"`
- **含义**：DNS A 记录指向。代表了当前的流量流向。

#### Edge: `HISTORY_RESOLVES_TO` (历史解析 / PDNS)

- **Source:** `IP`
- **Target:** `Domain`
- **Properties:**
  - `first_seen`: `"2021-01-01"`
  - `last_seen`: `"2022-05-01"`
- **含义**：**被动 DNS (PDNS)** 数据。表示该 IP 曾经托管过该域名。
  - *注意方向：* 图中定义为 IP -> Domain，意为“此 IP 的历史租户包括该域名”。

#### Edge: `ISSUED_TO` (证书签发)

- **Source:** `Certificate`
- **Target:** `Domain`
- **Properties:**
  - `source_field`: `"SAN"` (来源字段：SAN 或 CN)
- **含义**：证书的“使用者备用名称”或“主题”中包含了该域名。这是发现隐蔽子域名的核心路径。

### 3.4 服务与路由类 (Service & Routing)

#### Edge: `HOSTS_SERVICE` (物理承载)

- **Source:** `IP`
- **Target:** `Service`
- **Properties:**
  - `discovery`: `"Masscan"`
  - `first_seen`: `"2023-10-29"`
- **含义**：**L4 层物理关系**。表示外部扫描结果显示该 IP 上的开放端口。

#### Edge: `ROUTES_TO` (逻辑路由)

- **Source:** `Domain`
- **Target:** `Service`
- **Properties:**
  - `url_context`: `"/"`
  - `http_status`: `200`
- **含义**：**L7 层逻辑关系**。表示访问该域名（Host Header）最终由该 Service 处理。
  - *解决了 Virtual Hosting 问题*：多个 Domain 可以 `ROUTES_TO` 同一个 Service。

#### Edge: `UPSTREAM` (上游代理)

- **Source:** `Service` (网关/代理，如 Nginx)
- **Target:** `Service` (后端/应用，如 Tomcat)
- **Properties:**
  - `type`: `"ReverseProxy"`
  - `conf_file`: `"nginx.conf"`
- **含义**：**逻辑后置关系**。表示流量从一个前置服务转发到了内部或后端的另一个服务。通常通过配置文件分析或 SSRF 探测发现。

#### Edge: `COMMUNICATES` (客户端通信)

- **Source:** `ClientApplication`
- **Target:** `Service`
- **Properties:**
  - `method`: `"StaticAnalysis"` (静态分析逆向发现)
- **含义**：App 内部硬编码了连接该服务的 API 地址。这是发现未公开 API 的重要路径。

------

## 4. 关键数据流场景演示

### 场景一：全流程资产发现与指纹识别

1. **输入**：`Organization(Target Corp)`.
2. **归属发现**：系统自动关联出 `Netblock(47.x.x.x/24)`.
3. **主机发现**：导入外部扫描结果，发现存活 `IP(47.x.x.5)`. 建立 `Netblock` -> `CONTAINS` -> `IP`.
4. **端口结果**：导入 Masscan 结果，发现 80 端口。建立 `IP` -> `HOSTS_SERVICE` -> `Service(80)`.
5. **指纹导入**：
   - 导入外部指纹结果（HTTP Banner、Title 等）。
   - 更新 `Service` 节点属性：`product="Nginx"`, `web_title="GitLab"`, `fingerprint_status="COMPLETED"`.

### 场景二：基于证书的隐蔽资产关联

1. **输入**：导入 `IP(1.2.3.4)` 的 443 端口扫描结果。
2. **证书导入**：导入 SSL 证书信息，SHA256 为 `abc...`。
3. **SAN 分析**：证书的 SAN 字段包含 `admin-dev.target.com`.
4. **图谱构建**：
   - 创建 `Certificate(abc...)`.
   - 创建 `Domain(admin-dev.target.com)`.
   - 建立边 `Certificate` -> `ISSUED_TO` -> `Domain`.
   - 即使 DNS 无法解析 `admin-dev.target.com`，我们也通过证书知道了这个隐蔽域名的存在，且知道它部署在 `1.2.3.4` 上。

### 场景三：逻辑后置服务发现

1. **现状**：已知 `Domain(api.com)` -> `ROUTES_TO` -> `Service(Nginx)`.
2. **发现**：外部结果显示 Nginx 配置中存在 `upstream` 信息。
3. **发现**：配置显示 `proxy_pass http://10.0.0.5:8080;`.
4. **图谱更新**：
   - 创建内网 `Service(10.0.0.5:8080)`.
   - 建立边 `Service(Nginx)` -> `UPSTREAM` -> `Service(Internal)`.
   - 这揭示了深层攻击路径。
