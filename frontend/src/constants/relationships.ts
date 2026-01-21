import type { NodeType, RelationshipType } from '@/types/relationship';

export const nodeTypeOptions: NodeType[] = [
  'Organization',
  'Domain',
  'IP',
  'Netblock',
  'Service',
  'Certificate',
  'ClientApplication',
  'Credential',
];

export const relationshipTypeOptions: RelationshipType[] = [
  'SUBSIDIARY',
  'OWNS_NETBLOCK',
  'OWNS_ASSET',
  'OWNS_DOMAIN',
  'CONTAINS',
  'SUBDOMAIN',
  'RESOLVES_TO',
  'HISTORY_RESOLVES_TO',
  'ISSUED_TO',
  'HOSTS_SERVICE',
  'ROUTES_TO',
  'UPSTREAM',
  'COMMUNICATES',
];

export const relationshipRules: Record<
  RelationshipType,
  {
    source: NodeType;
    target: NodeType;
  }
> = {
  SUBSIDIARY: { source: 'Organization', target: 'Organization' },
  OWNS_NETBLOCK: { source: 'Organization', target: 'Netblock' },
  OWNS_ASSET: { source: 'Organization', target: 'IP' },
  OWNS_DOMAIN: { source: 'Organization', target: 'Domain' },
  CONTAINS: { source: 'Netblock', target: 'IP' },
  SUBDOMAIN: { source: 'Domain', target: 'Domain' },
  RESOLVES_TO: { source: 'Domain', target: 'IP' },
  HISTORY_RESOLVES_TO: { source: 'IP', target: 'Domain' },
  ISSUED_TO: { source: 'Certificate', target: 'Domain' },
  HOSTS_SERVICE: { source: 'IP', target: 'Service' },
  ROUTES_TO: { source: 'Domain', target: 'Service' },
  UPSTREAM: { source: 'Service', target: 'Service' },
  COMMUNICATES: { source: 'ClientApplication', target: 'Service' },
};
