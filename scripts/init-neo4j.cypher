// ExternalHound Neo4j 初始化脚本
// 版本：v1.0
// 日期：2026-01-16

// ============================================
// 1. 创建唯一约束（自动创建索引）
// ============================================

CREATE CONSTRAINT org_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT netblock_id_unique IF NOT EXISTS FOR (n:Netblock) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT domain_id_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT ip_id_unique IF NOT EXISTS FOR (i:IP) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT cert_id_unique IF NOT EXISTS FOR (c:Certificate) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT service_id_unique IF NOT EXISTS FOR (s:Service) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT app_id_unique IF NOT EXISTS FOR (a:ClientApplication) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT cred_id_unique IF NOT EXISTS FOR (c:Credential) REQUIRE c.id IS UNIQUE;

// ============================================
// 2. 创建常用属性索引
// ============================================

// Organization 索引
CREATE INDEX org_name_idx IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX org_is_primary_idx IF NOT EXISTS FOR (o:Organization) ON (o.is_primary);

// Netblock 索引
CREATE INDEX netblock_asn_idx IF NOT EXISTS FOR (n:Netblock) ON (n.asn_number);
CREATE INDEX netblock_scope_idx IF NOT EXISTS FOR (n:Netblock) ON (n.scope_policy);

// Domain 索引
CREATE INDEX domain_name_idx IF NOT EXISTS FOR (d:Domain) ON (d.name);
CREATE INDEX domain_root_idx IF NOT EXISTS FOR (d:Domain) ON (d.root_domain);
CREATE INDEX domain_resolved_idx IF NOT EXISTS FOR (d:Domain) ON (d.is_resolved);

// IP 索引
CREATE INDEX ip_address_idx IF NOT EXISTS FOR (i:IP) ON (i.address);
CREATE INDEX ip_country_idx IF NOT EXISTS FOR (i:IP) ON (i.country_code);
CREATE INDEX ip_asn_idx IF NOT EXISTS FOR (i:IP) ON (i.asn_number);

// Certificate 索引
CREATE INDEX cert_subject_cn_idx IF NOT EXISTS FOR (c:Certificate) ON (c.subject_cn);
CREATE INDEX cert_expired_idx IF NOT EXISTS FOR (c:Certificate) ON (c.is_expired);

// Service 索引
CREATE INDEX service_port_idx IF NOT EXISTS FOR (s:Service) ON (s.port);
CREATE INDEX service_product_idx IF NOT EXISTS FOR (s:Service) ON (s.product);
CREATE INDEX service_is_http_idx IF NOT EXISTS FOR (s:Service) ON (s.is_http);

// ClientApplication 索引
CREATE INDEX app_platform_idx IF NOT EXISTS FOR (a:ClientApplication) ON (a.platform);
CREATE INDEX app_category_idx IF NOT EXISTS FOR (a:ClientApplication) ON (a.app_category);

// Credential 索引
CREATE INDEX cred_type_idx IF NOT EXISTS FOR (c:Credential) ON (c.type);
CREATE INDEX cred_provider_idx IF NOT EXISTS FOR (c:Credential) ON (c.provider);
CREATE INDEX cred_is_valid_idx IF NOT EXISTS FOR (c:Credential) ON (c.is_valid);

// ============================================
// 3. 创建复合索引（Neo4j 5.x+）
// ============================================

CREATE INDEX org_primary_tier IF NOT EXISTS FOR (o:Organization) ON (o.is_primary, o.tier);
CREATE INDEX ip_scope_cloud IF NOT EXISTS FOR (i:IP) ON (i.scope_policy, i.is_cloud);
CREATE INDEX service_port_http IF NOT EXISTS FOR (s:Service) ON (s.port, s.is_http);

// ============================================
// 4. 完成提示
// ============================================

RETURN '========================================' AS message
UNION ALL
RETURN 'ExternalHound Neo4j 初始化完成！' AS message
UNION ALL
RETURN '========================================' AS message
UNION ALL
RETURN '唯一约束: 8 个' AS message
UNION ALL
RETURN '属性索引: 20 个' AS message
UNION ALL
RETURN '复合索引: 3 个' AS message
UNION ALL
RETURN '========================================' AS message;
