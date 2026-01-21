-- Align existing PostgreSQL schema with ExternalHound database design v1.0

BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Add external_id to core asset tables (UUID PK tables)
-- ============================================

ALTER TABLE assets_organization ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
UPDATE assets_organization SET external_id = id::text WHERE external_id IS NULL;
ALTER TABLE assets_organization ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_organization_external_id_key'
    ) THEN
        ALTER TABLE assets_organization
            ADD CONSTRAINT assets_organization_external_id_key UNIQUE (external_id);
    END IF;
END $$;

ALTER TABLE assets_netblock ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
UPDATE assets_netblock SET external_id = id::text WHERE external_id IS NULL;
ALTER TABLE assets_netblock ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_netblock_external_id_key'
    ) THEN
        ALTER TABLE assets_netblock
            ADD CONSTRAINT assets_netblock_external_id_key UNIQUE (external_id);
    END IF;
END $$;

ALTER TABLE assets_domain ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
UPDATE assets_domain SET external_id = id::text WHERE external_id IS NULL;
ALTER TABLE assets_domain ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_domain_external_id_key'
    ) THEN
        ALTER TABLE assets_domain
            ADD CONSTRAINT assets_domain_external_id_key UNIQUE (external_id);
    END IF;
END $$;

ALTER TABLE assets_ip ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
UPDATE assets_ip SET external_id = id::text WHERE external_id IS NULL;
ALTER TABLE assets_ip ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_ip_external_id_key'
    ) THEN
        ALTER TABLE assets_ip
            ADD CONSTRAINT assets_ip_external_id_key UNIQUE (external_id);
    END IF;
END $$;

-- ============================================
-- Certificate: move current id to external_id, introduce UUID id
-- ============================================

ALTER TABLE assets_certificate DROP CONSTRAINT IF EXISTS assets_certificate_pkey;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets_certificate' AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets_certificate' AND column_name = 'external_id'
    ) THEN
        ALTER TABLE assets_certificate RENAME COLUMN id TO external_id;
    END IF;
END $$;

ALTER TABLE assets_certificate ALTER COLUMN external_id TYPE VARCHAR(255);
ALTER TABLE assets_certificate ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_certificate_external_id_key'
    ) THEN
        ALTER TABLE assets_certificate
            ADD CONSTRAINT assets_certificate_external_id_key UNIQUE (external_id);
    END IF;
END $$;

ALTER TABLE assets_certificate ADD COLUMN IF NOT EXISTS id UUID;
UPDATE assets_certificate SET id = uuid_generate_v4() WHERE id IS NULL;
ALTER TABLE assets_certificate ALTER COLUMN id SET NOT NULL;
ALTER TABLE assets_certificate ALTER COLUMN id SET DEFAULT uuid_generate_v4();
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_certificate_pkey'
    ) THEN
        ALTER TABLE assets_certificate
            ADD CONSTRAINT assets_certificate_pkey PRIMARY KEY (id);
    END IF;
END $$;

-- ============================================
-- Service: move current id to external_id, introduce UUID id
-- ============================================

ALTER TABLE assets_service DROP CONSTRAINT IF EXISTS assets_service_pkey;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets_service' AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets_service' AND column_name = 'external_id'
    ) THEN
        ALTER TABLE assets_service RENAME COLUMN id TO external_id;
    END IF;
END $$;

ALTER TABLE assets_service ALTER COLUMN external_id TYPE VARCHAR(255);
ALTER TABLE assets_service ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_service_external_id_key'
    ) THEN
        ALTER TABLE assets_service
            ADD CONSTRAINT assets_service_external_id_key UNIQUE (external_id);
    END IF;
END $$;

ALTER TABLE assets_service ADD COLUMN IF NOT EXISTS id UUID;
UPDATE assets_service SET id = uuid_generate_v4() WHERE id IS NULL;
ALTER TABLE assets_service ALTER COLUMN id SET NOT NULL;
ALTER TABLE assets_service ALTER COLUMN id SET DEFAULT uuid_generate_v4();
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_service_pkey'
    ) THEN
        ALTER TABLE assets_service
            ADD CONSTRAINT assets_service_pkey PRIMARY KEY (id);
    END IF;
END $$;

ALTER TABLE assets_service DROP COLUMN IF EXISTS dir_scan_status;
ALTER TABLE assets_service DROP COLUMN IF EXISTS vuln_scan_status;

-- ============================================
-- ClientApplication: move current id to external_id, introduce UUID id
-- ============================================

ALTER TABLE assets_client_application DROP CONSTRAINT IF EXISTS assets_client_application_pkey;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets_client_application' AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets_client_application' AND column_name = 'external_id'
    ) THEN
        ALTER TABLE assets_client_application RENAME COLUMN id TO external_id;
    END IF;
END $$;

ALTER TABLE assets_client_application ALTER COLUMN external_id TYPE VARCHAR(255);
ALTER TABLE assets_client_application ALTER COLUMN external_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_client_application_external_id_key'
    ) THEN
        ALTER TABLE assets_client_application
            ADD CONSTRAINT assets_client_application_external_id_key UNIQUE (external_id);
    END IF;
END $$;

ALTER TABLE assets_client_application ADD COLUMN IF NOT EXISTS id UUID;
UPDATE assets_client_application SET id = uuid_generate_v4() WHERE id IS NULL;
ALTER TABLE assets_client_application ALTER COLUMN id SET NOT NULL;
ALTER TABLE assets_client_application ALTER COLUMN id SET DEFAULT uuid_generate_v4();
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'assets_client_application_pkey'
    ) THEN
        ALTER TABLE assets_client_application
            ADD CONSTRAINT assets_client_application_pkey PRIMARY KEY (id);
    END IF;
END $$;

ALTER TABLE assets_client_application DROP COLUMN IF EXISTS analysis_status;

-- ============================================
-- Credential table (missing in current schema)
-- ============================================

CREATE TABLE IF NOT EXISTS assets_credential (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    cred_type VARCHAR(50) NOT NULL,
    provider VARCHAR(50),
    is_valid BOOLEAN DEFAULT FALSE,
    leaked_count INTEGER DEFAULT 0,
    content JSONB DEFAULT '{}'::jsonb,
    source_context TEXT,
    validation_result JSONB DEFAULT '{}'::jsonb,
    discovered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_cred_type ON assets_credential(cred_type);
CREATE INDEX IF NOT EXISTS idx_cred_provider ON assets_credential(provider);
CREATE INDEX IF NOT EXISTS idx_cred_is_valid ON assets_credential(is_valid);
CREATE INDEX IF NOT EXISTS idx_cred_metadata_gin ON assets_credential USING GIN (content);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_credential_updated_at'
    ) THEN
        CREATE TRIGGER trg_credential_updated_at
            BEFORE UPDATE ON assets_credential
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

COMMIT;
