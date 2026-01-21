export type ScopePolicy = 'IN_SCOPE' | 'OUT_OF_SCOPE';

export interface AssetBase {
  id: string;
  external_id: string;
  created_at: string;
  updated_at: string;
  created_by?: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
}

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
  metadata: Record<string, unknown>;
}

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
  metadata?: Record<string, unknown>;
}

export interface IPCreatePayload {
  external_id?: string;
  address: string;
  version?: 4 | 6;
  is_cloud?: boolean;
  is_internal?: boolean;
  is_cdn?: boolean;
  country_code?: string | null;
  asn_number?: string | null;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface DomainAsset extends AssetBase {
  name: string;
  root_domain?: string | null;
  tier: number;
  is_resolved: boolean;
  is_wildcard: boolean;
  is_internal: boolean;
  has_waf: boolean;
  scope_policy: ScopePolicy;
  metadata: Record<string, unknown>;
}

export interface DomainCreatePayload {
  external_id?: string;
  name: string;
  root_domain?: string | null;
  tier?: number;
  is_resolved?: boolean;
  is_wildcard?: boolean;
  is_internal?: boolean;
  has_waf?: boolean;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface DomainUpdatePayload {
  name?: string;
  root_domain?: string | null;
  tier?: number;
  is_resolved?: boolean;
  is_wildcard?: boolean;
  is_internal?: boolean;
  has_waf?: boolean;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}

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
  metadata: Record<string, unknown>;
}

export interface ServiceCreatePayload {
  external_id?: string;
  service_name?: string | null;
  port: number;
  protocol?: 'TCP' | 'UDP';
  product?: string | null;
  version?: string | null;
  banner?: string | null;
  is_http?: boolean;
  risk_score?: number;
  asset_category?: string | null;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface ServiceUpdatePayload {
  service_name?: string | null;
  port?: number;
  protocol?: 'TCP' | 'UDP';
  product?: string | null;
  version?: string | null;
  banner?: string | null;
  is_http?: boolean;
  risk_score?: number;
  asset_category?: string | null;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}

export interface OrganizationAsset extends AssetBase {
  name: string;
  full_name?: string | null;
  credit_code?: string | null;
  is_primary: boolean;
  tier: number;
  asset_count: number;
  risk_score: number;
  scope_policy: ScopePolicy;
  metadata: Record<string, unknown>;
}

export interface OrganizationCreatePayload {
  external_id?: string;
  name: string;
  full_name?: string | null;
  credit_code?: string | null;
  is_primary?: boolean;
  tier?: number;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface OrganizationUpdatePayload {
  name?: string;
  full_name?: string | null;
  credit_code?: string | null;
  is_primary?: boolean;
  tier?: number;
  asset_count?: number;
  risk_score?: number;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}

export interface NetblockAsset extends AssetBase {
  cidr: string;
  asn_number?: string | null;
  capacity?: number | null;
  live_count: number;
  risk_score: number;
  is_internal: boolean;
  scope_policy: ScopePolicy;
  metadata: Record<string, unknown>;
}

export interface NetblockCreatePayload {
  external_id?: string;
  cidr: string;
  asn_number?: string | null;
  live_count?: number;
  risk_score?: number;
  is_internal?: boolean;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface NetblockUpdatePayload {
  asn_number?: string | null;
  live_count?: number;
  risk_score?: number;
  is_internal?: boolean;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}

export interface CertificateAsset extends AssetBase {
  subject_cn?: string | null;
  issuer_cn?: string | null;
  issuer_org?: string | null;
  valid_from?: number | null;
  valid_to?: number | null;
  days_to_expire?: number | null;
  is_expired: boolean;
  is_self_signed: boolean;
  is_revoked: boolean;
  san_count: number;
  scope_policy: ScopePolicy;
  metadata: Record<string, unknown>;
}

export interface CertificateCreatePayload {
  external_id?: string;
  subject_cn?: string | null;
  issuer_cn?: string | null;
  issuer_org?: string | null;
  valid_from?: number | null;
  valid_to?: number | null;
  days_to_expire?: number | null;
  is_expired?: boolean;
  is_self_signed?: boolean;
  is_revoked?: boolean;
  san_count?: number;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface CertificateUpdatePayload {
  subject_cn?: string | null;
  issuer_cn?: string | null;
  issuer_org?: string | null;
  valid_from?: number | null;
  valid_to?: number | null;
  days_to_expire?: number | null;
  is_expired?: boolean;
  is_self_signed?: boolean;
  is_revoked?: boolean;
  san_count?: number;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}

export interface ClientApplicationAsset extends AssetBase {
  app_name: string;
  package_name: string;
  version?: string | null;
  platform: string;
  bundle_id?: string | null;
  risk_score: number;
  scope_policy: ScopePolicy;
  metadata: Record<string, unknown>;
}

export interface ClientApplicationCreatePayload {
  external_id?: string;
  app_name: string;
  package_name: string;
  version?: string | null;
  platform: string;
  bundle_id?: string | null;
  risk_score?: number;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface ClientApplicationUpdatePayload {
  app_name?: string;
  package_name?: string;
  version?: string | null;
  platform?: string;
  bundle_id?: string | null;
  risk_score?: number;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}

export interface CredentialAsset extends AssetBase {
  cred_type: string;
  provider?: string | null;
  username?: string | null;
  email?: string | null;
  phone?: string | null;
  leaked_count: number;
  content: Record<string, unknown>;
  validation_result?: string | null;
  scope_policy: ScopePolicy;
  metadata: Record<string, unknown>;
}

export interface CredentialCreatePayload {
  external_id?: string;
  cred_type: string;
  provider?: string | null;
  username?: string | null;
  email?: string | null;
  phone?: string | null;
  leaked_count?: number;
  content?: Record<string, unknown>;
  validation_result?: string | null;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
  created_by?: string | null;
}

export interface CredentialUpdatePayload {
  cred_type?: string;
  provider?: string | null;
  username?: string | null;
  email?: string | null;
  phone?: string | null;
  leaked_count?: number;
  content?: Record<string, unknown>;
  validation_result?: string | null;
  scope_policy?: ScopePolicy;
  metadata?: Record<string, unknown>;
}
