-- ExternalHound PostgreSQL 初始化脚本
-- 版本：v1.0
-- 日期：2026-01-16

-- ============================================
-- 1. 创建扩展
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 模糊搜索
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN 索引增强
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- GiST 索引增强
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- 加密功能

-- ============================================
-- 2. 创建触发器函数
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 3. 创建核心资产表
-- ============================================

-- 3.1 Organization（组织表）
CREATE TABLE assets_organization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500),
    credit_code VARCHAR(100) UNIQUE,
    is_primary BOOLEAN DEFAULT FALSE,
    tier INTEGER DEFAULT 0,
    asset_count INTEGER DEFAULT 0,
    risk_score DECIMAL(3,1) DEFAULT 0.0,
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_org_risk_score CHECK (risk_score >= 0 AND risk_score <= 10),
    CONSTRAINT chk_org_tier CHECK (tier >= 0),
    CONSTRAINT chk_org_asset_count CHECK (asset_count >= 0)
);

CREATE INDEX idx_org_name ON assets_organization(name);
CREATE INDEX idx_org_credit_code ON assets_organization(credit_code);
CREATE INDEX idx_org_is_primary ON assets_organization(is_primary);
CREATE INDEX idx_org_scope_policy ON assets_organization(scope_policy);
CREATE INDEX idx_org_is_deleted ON assets_organization(is_deleted);
CREATE INDEX idx_org_metadata_gin ON assets_organization USING GIN (metadata);
CREATE INDEX idx_org_created_at ON assets_organization(created_at);
CREATE INDEX idx_org_name_trgm ON assets_organization USING GIN (name gin_trgm_ops);
CREATE INDEX idx_org_full_name_trgm ON assets_organization USING GIN (full_name gin_trgm_ops);

CREATE TRIGGER trg_org_updated_at
    BEFORE UPDATE ON assets_organization
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.2 Netblock（网段表）
CREATE TABLE assets_netblock (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    cidr CIDR NOT NULL UNIQUE,
    asn_number VARCHAR(20),
    capacity BIGINT,
    live_count INTEGER DEFAULT 0,
    risk_score DECIMAL(3,1) DEFAULT 0.0,
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    is_internal BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_netblock_risk_score CHECK (risk_score >= 0 AND risk_score <= 10),
    CONSTRAINT chk_netblock_live_count CHECK (live_count >= 0),
    CONSTRAINT chk_netblock_capacity CHECK (capacity IS NULL OR capacity >= 0),
    CONSTRAINT chk_netblock_live_count_capacity CHECK (
        capacity IS NULL OR live_count <= capacity
    )
);

CREATE INDEX idx_netblock_cidr ON assets_netblock USING GIST (cidr inet_ops);
CREATE INDEX idx_netblock_asn ON assets_netblock(asn_number);
CREATE INDEX idx_netblock_scope_policy ON assets_netblock(scope_policy);
CREATE INDEX idx_netblock_is_internal ON assets_netblock(is_internal);
CREATE INDEX idx_netblock_is_deleted ON assets_netblock(is_deleted);
CREATE INDEX idx_netblock_metadata_gin ON assets_netblock USING GIN (metadata);

CREATE TRIGGER trg_netblock_updated_at
    BEFORE UPDATE ON assets_netblock
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.3 Domain（域名表）
CREATE TABLE assets_domain (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    root_domain VARCHAR(255),
    tier INTEGER DEFAULT 1,
    is_resolved BOOLEAN DEFAULT FALSE,
    is_wildcard BOOLEAN DEFAULT FALSE,
    is_internal BOOLEAN DEFAULT FALSE,
    has_waf BOOLEAN DEFAULT FALSE,
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_domain_tier CHECK (tier >= 1)
);

CREATE INDEX idx_domain_name ON assets_domain(name);
CREATE INDEX idx_domain_root_domain ON assets_domain(root_domain);
CREATE INDEX idx_domain_is_resolved ON assets_domain(is_resolved);
CREATE INDEX idx_domain_scope_policy ON assets_domain(scope_policy);
CREATE INDEX idx_domain_is_deleted ON assets_domain(is_deleted);
CREATE INDEX idx_domain_metadata_gin ON assets_domain USING GIN (metadata);
CREATE INDEX idx_domain_name_trgm ON assets_domain USING GIN (name gin_trgm_ops);

CREATE TRIGGER trg_domain_updated_at
    BEFORE UPDATE ON assets_domain
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.4 IP（主机表）
CREATE TABLE assets_ip (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    address INET NOT NULL UNIQUE,
    version INTEGER NOT NULL,
    is_cloud BOOLEAN DEFAULT FALSE,
    is_internal BOOLEAN DEFAULT FALSE,
    is_cdn BOOLEAN DEFAULT FALSE,
    open_ports_count INTEGER DEFAULT 0,
    risk_score DECIMAL(3,1) DEFAULT 0.0,
    vuln_critical_count INTEGER DEFAULT 0,
    country_code VARCHAR(2),
    asn_number VARCHAR(20),
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_ip_version CHECK (version IN (4, 6)),
    CONSTRAINT chk_ip_risk_score CHECK (risk_score >= 0 AND risk_score <= 10),
    CONSTRAINT chk_ip_open_ports_count CHECK (open_ports_count >= 0),
    CONSTRAINT chk_ip_vuln_critical_count CHECK (vuln_critical_count >= 0)
);

CREATE INDEX idx_ip_address ON assets_ip USING GIST (address inet_ops);
CREATE INDEX idx_ip_version ON assets_ip(version);
CREATE INDEX idx_ip_country_code ON assets_ip(country_code);
CREATE INDEX idx_ip_asn_number ON assets_ip(asn_number);
CREATE INDEX idx_ip_scope_policy ON assets_ip(scope_policy);
CREATE INDEX idx_ip_is_cloud ON assets_ip(is_cloud);
CREATE INDEX idx_ip_is_deleted ON assets_ip(is_deleted);
CREATE INDEX idx_ip_metadata_gin ON assets_ip USING GIN (metadata);

CREATE TRIGGER trg_ip_updated_at
    BEFORE UPDATE ON assets_ip
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.5 Certificate（证书表）
CREATE TABLE assets_certificate (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    subject_cn VARCHAR(255),
    issuer_cn VARCHAR(255),
    issuer_org VARCHAR(255),
    valid_from BIGINT,
    valid_to BIGINT,
    days_to_expire INTEGER,
    is_expired BOOLEAN DEFAULT FALSE,
    is_self_signed BOOLEAN DEFAULT FALSE,
    is_revoked BOOLEAN DEFAULT FALSE,
    san_count INTEGER DEFAULT 0,
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_cert_san_count CHECK (san_count >= 0),
    CONSTRAINT chk_cert_valid_range CHECK (
        valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to
    )
);

CREATE INDEX idx_cert_subject_cn ON assets_certificate(subject_cn);
CREATE INDEX idx_cert_issuer_cn ON assets_certificate(issuer_cn);
CREATE INDEX idx_cert_valid_to ON assets_certificate(valid_to);
CREATE INDEX idx_cert_is_expired ON assets_certificate(is_expired);
CREATE INDEX idx_cert_is_self_signed ON assets_certificate(is_self_signed);
CREATE INDEX idx_cert_is_revoked ON assets_certificate(is_revoked);
CREATE INDEX idx_cert_scope_policy ON assets_certificate(scope_policy);
CREATE INDEX idx_cert_is_deleted ON assets_certificate(is_deleted);
CREATE INDEX idx_cert_metadata_gin ON assets_certificate USING GIN (metadata);
CREATE INDEX idx_cert_subject_cn_trgm ON assets_certificate USING GIN (subject_cn gin_trgm_ops);

CREATE TRIGGER trg_cert_updated_at
    BEFORE UPDATE ON assets_certificate
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.6 Service（服务表）
CREATE TABLE assets_service (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    service_name VARCHAR(100),
    port INTEGER NOT NULL,
    protocol VARCHAR(10) NOT NULL DEFAULT 'TCP',
    product VARCHAR(255),
    version VARCHAR(100),
    banner TEXT,
    is_http BOOLEAN DEFAULT FALSE,
    risk_score DOUBLE PRECISION DEFAULT 0.0,
    asset_category VARCHAR(50),
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_service_port CHECK (port >= 1 AND port <= 65535),
    CONSTRAINT chk_service_risk_score CHECK (risk_score >= 0 AND risk_score <= 10),
    CONSTRAINT chk_service_protocol CHECK (protocol IN ('TCP', 'UDP'))
);

CREATE INDEX idx_service_service_name ON assets_service(service_name);
CREATE INDEX idx_service_port ON assets_service(port);
CREATE INDEX idx_service_protocol ON assets_service(protocol);
CREATE INDEX idx_service_product ON assets_service(product);
CREATE INDEX idx_service_is_http ON assets_service(is_http);
CREATE INDEX idx_service_asset_category ON assets_service(asset_category);
CREATE INDEX idx_service_scope_policy ON assets_service(scope_policy);
CREATE INDEX idx_service_is_deleted ON assets_service(is_deleted);
CREATE INDEX idx_service_metadata_gin ON assets_service USING GIN (metadata);
CREATE INDEX idx_service_banner_trgm ON assets_service USING GIN (banner gin_trgm_ops);
CREATE INDEX idx_service_product_trgm ON assets_service USING GIN (product gin_trgm_ops);

CREATE TRIGGER trg_service_updated_at
    BEFORE UPDATE ON assets_service
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.7 ClientApplication（客户端应用表）
CREATE TABLE assets_client_application (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    app_name VARCHAR(255) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    version VARCHAR(100),
    platform VARCHAR(50) NOT NULL,
    bundle_id VARCHAR(255),
    risk_score DOUBLE PRECISION DEFAULT 0.0,
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_app_risk_score CHECK (risk_score >= 0 AND risk_score <= 10),
    CONSTRAINT chk_app_platform CHECK (platform IN ('Android', 'iOS', 'Windows', 'macOS', 'Linux'))
);

CREATE INDEX idx_app_name ON assets_client_application(app_name);
CREATE INDEX idx_app_package_name ON assets_client_application(package_name);
CREATE INDEX idx_app_platform ON assets_client_application(platform);
CREATE INDEX idx_app_scope_policy ON assets_client_application(scope_policy);
CREATE INDEX idx_app_is_deleted ON assets_client_application(is_deleted);
CREATE INDEX idx_app_metadata_gin ON assets_client_application USING GIN (metadata);
CREATE INDEX idx_app_name_trgm ON assets_client_application USING GIN (app_name gin_trgm_ops);

CREATE TRIGGER trg_app_updated_at
    BEFORE UPDATE ON assets_client_application
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.8 Credential（凭证表）
CREATE TABLE assets_credential (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    cred_type VARCHAR(50) NOT NULL,
    provider VARCHAR(255),
    username VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    leaked_count INTEGER DEFAULT 0,
    content JSONB DEFAULT '{}'::jsonb,
    validation_result VARCHAR(50),
    scope_policy VARCHAR(50) DEFAULT 'IN_SCOPE',
    metadata JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_cred_leaked_count CHECK (leaked_count >= 0),
    CONSTRAINT chk_cred_validation_result CHECK (
        validation_result IS NULL
        OR validation_result IN ('VALID', 'INVALID', 'UNKNOWN')
    )
);

CREATE INDEX idx_cred_type ON assets_credential(cred_type);
CREATE INDEX idx_cred_provider ON assets_credential(provider);
CREATE INDEX idx_cred_username ON assets_credential(username);
CREATE INDEX idx_cred_email ON assets_credential(email);
CREATE INDEX idx_cred_validation_result ON assets_credential(validation_result);
CREATE INDEX idx_cred_scope_policy ON assets_credential(scope_policy);
CREATE INDEX idx_cred_is_deleted ON assets_credential(is_deleted);
CREATE INDEX idx_cred_content_gin ON assets_credential USING GIN (content);
CREATE INDEX idx_cred_metadata_gin ON assets_credential USING GIN (metadata);

CREATE TRIGGER trg_credential_updated_at
    BEFORE UPDATE ON assets_credential
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3.9 Relationship（关系表）
CREATE TABLE assets_relationship (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_external_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    target_external_id VARCHAR(255) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    edge_key VARCHAR(255) DEFAULT 'default' NOT NULL,
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT uq_assets_relationship_key UNIQUE (
        source_external_id,
        source_type,
        target_external_id,
        target_type,
        relation_type,
        edge_key
    )
);

CREATE INDEX idx_relationship_source_external_id ON assets_relationship(source_external_id);
CREATE INDEX idx_relationship_source_type ON assets_relationship(source_type);
CREATE INDEX idx_relationship_target_external_id ON assets_relationship(target_external_id);
CREATE INDEX idx_relationship_target_type ON assets_relationship(target_type);
CREATE INDEX idx_relationship_relation_type ON assets_relationship(relation_type);
CREATE INDEX idx_relationship_edge_key ON assets_relationship(edge_key);
CREATE INDEX idx_relationship_is_deleted ON assets_relationship(is_deleted);
CREATE INDEX idx_relationship_created_at ON assets_relationship(created_at);

CREATE TRIGGER trg_relationship_updated_at
    BEFORE UPDATE ON assets_relationship
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. 创建辅助表
-- ============================================

-- 4.1 导入记录表
CREATE TABLE import_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    file_path TEXT,
    format VARCHAR(50) NOT NULL,
    parser_version VARCHAR(20),
    status VARCHAR(20) NOT NULL,
    progress INTEGER DEFAULT 0,
    records_total INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    assets_created JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    duration_seconds INTEGER
);

CREATE INDEX idx_import_status ON import_logs(status);
CREATE INDEX idx_import_format ON import_logs(format);
CREATE INDEX idx_import_created_at ON import_logs(created_at);
CREATE INDEX idx_import_created_by ON import_logs(created_by);

CREATE TRIGGER trg_import_updated_at
    BEFORE UPDATE ON import_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 4.2 操作日志表
CREATE TABLE operation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255),
    operation_detail JSONB,
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_oplog_operation_type ON operation_logs(operation_type);
CREATE INDEX idx_oplog_entity_type ON operation_logs(entity_type);
CREATE INDEX idx_oplog_entity_id ON operation_logs(entity_id);
CREATE INDEX idx_oplog_created_at ON operation_logs(created_at);
CREATE INDEX idx_oplog_created_by ON operation_logs(created_by);

-- 4.3 标签表
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    color VARCHAR(20),
    description TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

CREATE INDEX idx_tag_name ON tags(name);
CREATE INDEX idx_tag_category ON tags(category);

CREATE TRIGGER trg_tag_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 4.4 资产标签关联表
CREATE TABLE asset_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_type VARCHAR(50) NOT NULL,
    asset_id VARCHAR(255) NOT NULL,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT uq_asset_tag UNIQUE (asset_type, asset_id, tag_id)
);

CREATE INDEX idx_asset_tag_asset ON asset_tags(asset_type, asset_id);
CREATE INDEX idx_asset_tag_tag_id ON asset_tags(tag_id);
CREATE INDEX idx_asset_tag_created_at ON asset_tags(created_at);

-- ============================================
-- 5. 插入初始数据
-- ============================================

-- 插入默认标签
INSERT INTO tags (name, category, color, description) VALUES
    ('High Risk', 'Risk', '#FF0000', '高风险资产'),
    ('Medium Risk', 'Risk', '#FFA500', '中风险资产'),
    ('Low Risk', 'Risk', '#00FF00', '低风险资产'),
    ('Production', 'Business', '#0000FF', '生产环境'),
    ('Development', 'Business', '#808080', '开发环境'),
    ('Testing', 'Business', '#FFFF00', '测试环境'),
    ('Cloud', 'Technical', '#00FFFF', '云服务'),
    ('On-Premise', 'Technical', '#800080', '本地部署');

-- ============================================
-- 6. 完成提示
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'ExternalHound PostgreSQL 初始化完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库名称: externalhound';
    RAISE NOTICE '核心资产表: 8 个';
    RAISE NOTICE '关系表: 1 个';
    RAISE NOTICE '辅助表: 4 个';
    RAISE NOTICE '默认标签: 8 个';
    RAISE NOTICE '========================================';
END $$;
