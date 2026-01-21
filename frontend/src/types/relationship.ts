export type NodeType =
  | 'Organization'
  | 'Domain'
  | 'IP'
  | 'Netblock'
  | 'Service'
  | 'Certificate'
  | 'ClientApplication'
  | 'Credential';

export type RelationshipType =
  | 'SUBSIDIARY'
  | 'OWNS_NETBLOCK'
  | 'OWNS_ASSET'
  | 'OWNS_DOMAIN'
  | 'CONTAINS'
  | 'SUBDOMAIN'
  | 'RESOLVES_TO'
  | 'HISTORY_RESOLVES_TO'
  | 'ISSUED_TO'
  | 'HOSTS_SERVICE'
  | 'ROUTES_TO'
  | 'UPSTREAM'
  | 'COMMUNICATES';

export interface RelationshipCreatePayload {
  source_external_id: string;
  source_type: NodeType;
  target_external_id: string;
  target_type: NodeType;
  relation_type: RelationshipType;
  edge_key?: string;
  properties?: Record<string, unknown>;
  created_by?: string | null;
}

export interface RelationshipUpdatePayload {
  properties?: Record<string, unknown>;
}

export interface RelationshipRecord {
  id: string;
  source_external_id: string;
  source_type: NodeType;
  target_external_id: string;
  target_type: NodeType;
  relation_type: RelationshipType;
  edge_key: string;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  created_by?: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
}
