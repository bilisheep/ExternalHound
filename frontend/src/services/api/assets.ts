import { apiClient } from './client';
import type {
  IPAsset,
  DomainAsset,
  ServiceAsset,
  IPUpdatePayload,
  IPCreatePayload,
  DomainCreatePayload,
  DomainUpdatePayload,
  ServiceCreatePayload,
  ServiceUpdatePayload,
  OrganizationAsset,
  OrganizationCreatePayload,
  OrganizationUpdatePayload,
  NetblockAsset,
  NetblockCreatePayload,
  NetblockUpdatePayload,
  CertificateAsset,
  CertificateCreatePayload,
  CertificateUpdatePayload,
  ClientApplicationAsset,
  ClientApplicationCreatePayload,
  ClientApplicationUpdatePayload,
  CredentialAsset,
  CredentialCreatePayload,
  CredentialUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import type { PaginatedResponse } from '@/types/api';

const fetchAllPages = async <T>(
  path: string,
  params: Record<string, unknown> = {}
): Promise<T[]> => {
  const pageSize = 100;
  let page = 1;
  let totalPages = 1;
  const items: T[] = [];

  do {
    const { data } = await apiClient.get<PaginatedResponse<T>>(path, {
      params: {
        ...params,
        page,
        page_size: pageSize,
      },
    });
    items.push(...data.items);
    totalPages = data.total_pages;
    page += 1;
  } while (page <= totalPages);

  return items;
};

export const assetsApi = {
  getIPs: async (params: {
    page?: number;
    page_size?: number;
    version?: 4 | 6;
    is_cloud?: boolean;
    is_internal?: boolean;
    is_cdn?: boolean;
    country_code?: string;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<IPAsset>> => {
    const { data } = await apiClient.get('/ips', { params });
    return data;
  },

  getIPDetail: async (address: string): Promise<IPAsset> => {
    const { data } = await apiClient.get(`/ips/address/${encodeURIComponent(address)}`);
    return data;
  },

  createIP: async (payload: IPCreatePayload): Promise<IPAsset> => {
    const { data } = await apiClient.post('/ips', payload);
    return data;
  },

  updateIP: async (id: string, payload: IPUpdatePayload): Promise<IPAsset> => {
    const { data } = await apiClient.put(`/ips/${id}`, payload);
    return data;
  },

  deleteIP: async (id: string): Promise<void> => {
    await apiClient.delete(`/ips/${id}`);
  },

  getDomains: async (params: {
    page?: number;
    page_size?: number;
    root_domain?: string;
    tier?: number;
    is_resolved?: boolean;
    is_wildcard?: boolean;
    has_waf?: boolean;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<DomainAsset>> => {
    const { data } = await apiClient.get('/domains', { params });
    return data;
  },

  getAllDomains: async (): Promise<DomainAsset[]> => {
    return fetchAllPages<DomainAsset>('/domains');
  },

  getDomainDetail: async (name: string): Promise<DomainAsset> => {
    const { data } = await apiClient.get(`/domains/name/${encodeURIComponent(name)}`);
    return data;
  },

  getDomainByNameOptional: async (name: string): Promise<DomainAsset | null> => {
    const response = await apiClient.get(`/domains/name/${encodeURIComponent(name)}`, {
      validateStatus: (status) => status === 200 || status === 404,
    });
    if (response.status === 404) {
      return null;
    }
    return response.data;
  },

  getDomainSubdomains: async (
    rootDomain: string,
    params?: { skip?: number; limit?: number }
  ): Promise<DomainAsset[]> => {
    const { data } = await apiClient.get(
      `/domains/root/${encodeURIComponent(rootDomain)}/subdomains`,
      { params }
    );
    return data;
  },

  createDomain: async (payload: DomainCreatePayload): Promise<DomainAsset> => {
    const { data } = await apiClient.post('/domains', payload);
    return data;
  },

  updateDomain: async (id: string, payload: DomainUpdatePayload): Promise<DomainAsset> => {
    const { data } = await apiClient.put(`/domains/${id}`, payload);
    return data;
  },

  deleteDomain: async (id: string): Promise<void> => {
    await apiClient.delete(`/domains/${id}`);
  },

  getServices: async (params: {
    page?: number;
    page_size?: number;
    port?: number;
    protocol?: 'TCP' | 'UDP';
    is_http?: boolean;
    asset_category?: string;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<ServiceAsset>> => {
    const { data } = await apiClient.get('/services', { params });
    return data;
  },

  getServiceDetail: async (id: string): Promise<ServiceAsset> => {
    const { data } = await apiClient.get(`/services/${id}`);
    return data;
  },

  createService: async (payload: ServiceCreatePayload): Promise<ServiceAsset> => {
    const { data } = await apiClient.post('/services', payload);
    return data;
  },

  updateService: async (id: string, payload: ServiceUpdatePayload): Promise<ServiceAsset> => {
    const { data } = await apiClient.put(`/services/${id}`, payload);
    return data;
  },

  deleteService: async (id: string): Promise<void> => {
    await apiClient.delete(`/services/${id}`);
  },

  getOrganizations: async (params: {
    page?: number;
    page_size?: number;
    is_primary?: boolean;
    tier?: number;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<OrganizationAsset>> => {
    const { data } = await apiClient.get('/organizations', { params });
    return data;
  },

  createOrganization: async (
    payload: OrganizationCreatePayload
  ): Promise<OrganizationAsset> => {
    const { data } = await apiClient.post('/organizations', payload);
    return data;
  },

  updateOrganization: async (
    id: string,
    payload: OrganizationUpdatePayload
  ): Promise<OrganizationAsset> => {
    const { data } = await apiClient.put(`/organizations/${id}`, payload);
    return data;
  },

  deleteOrganization: async (id: string): Promise<void> => {
    await apiClient.delete(`/organizations/${id}`);
  },

  getNetblocks: async (params: {
    page?: number;
    page_size?: number;
    asn_number?: string;
    is_internal?: boolean;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<NetblockAsset>> => {
    const { data } = await apiClient.get('/netblocks', { params });
    return data;
  },

  createNetblock: async (payload: NetblockCreatePayload): Promise<NetblockAsset> => {
    const { data } = await apiClient.post('/netblocks', payload);
    return data;
  },

  updateNetblock: async (id: string, payload: NetblockUpdatePayload): Promise<NetblockAsset> => {
    const { data } = await apiClient.put(`/netblocks/${id}`, payload);
    return data;
  },

  deleteNetblock: async (id: string): Promise<void> => {
    await apiClient.delete(`/netblocks/${id}`);
  },

  getCertificates: async (params: {
    page?: number;
    page_size?: number;
    is_expired?: boolean;
    is_self_signed?: boolean;
    is_revoked?: boolean;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<CertificateAsset>> => {
    const { data } = await apiClient.get('/certificates', { params });
    return data;
  },

  createCertificate: async (
    payload: CertificateCreatePayload
  ): Promise<CertificateAsset> => {
    const { data } = await apiClient.post('/certificates', payload);
    return data;
  },

  updateCertificate: async (
    id: string,
    payload: CertificateUpdatePayload
  ): Promise<CertificateAsset> => {
    const { data } = await apiClient.put(`/certificates/${id}`, payload);
    return data;
  },

  deleteCertificate: async (id: string): Promise<void> => {
    await apiClient.delete(`/certificates/${id}`);
  },

  getClientApplications: async (params: {
    page?: number;
    page_size?: number;
    platform?: string;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<ClientApplicationAsset>> => {
    const { data } = await apiClient.get('/client-applications', { params });
    return data;
  },

  createClientApplication: async (
    payload: ClientApplicationCreatePayload
  ): Promise<ClientApplicationAsset> => {
    const { data } = await apiClient.post('/client-applications', payload);
    return data;
  },

  updateClientApplication: async (
    id: string,
    payload: ClientApplicationUpdatePayload
  ): Promise<ClientApplicationAsset> => {
    const { data } = await apiClient.put(`/client-applications/${id}`, payload);
    return data;
  },

  deleteClientApplication: async (id: string): Promise<void> => {
    await apiClient.delete(`/client-applications/${id}`);
  },

  getCredentials: async (params: {
    page?: number;
    page_size?: number;
    cred_type?: string;
    provider?: string;
    validation_result?: string;
    scope_policy?: ScopePolicy;
  }): Promise<PaginatedResponse<CredentialAsset>> => {
    const { data } = await apiClient.get('/credentials', { params });
    return data;
  },

  createCredential: async (payload: CredentialCreatePayload): Promise<CredentialAsset> => {
    const { data } = await apiClient.post('/credentials', payload);
    return data;
  },

  updateCredential: async (
    id: string,
    payload: CredentialUpdatePayload
  ): Promise<CredentialAsset> => {
    const { data } = await apiClient.put(`/credentials/${id}`, payload);
    return data;
  },

  deleteCredential: async (id: string): Promise<void> => {
    await apiClient.delete(`/credentials/${id}`);
  },

  getAllAssets: async (): Promise<{
    organizations: OrganizationAsset[];
    domains: DomainAsset[];
    ips: IPAsset[];
    netblocks: NetblockAsset[];
    services: ServiceAsset[];
    certificates: CertificateAsset[];
    clientApplications: ClientApplicationAsset[];
    credentials: CredentialAsset[];
  }> => {
    const [
      organizations,
      domains,
      ips,
      netblocks,
      services,
      certificates,
      clientApplications,
      credentials,
    ] = await Promise.all([
      fetchAllPages<OrganizationAsset>('/organizations'),
      fetchAllPages<DomainAsset>('/domains'),
      fetchAllPages<IPAsset>('/ips'),
      fetchAllPages<NetblockAsset>('/netblocks'),
      fetchAllPages<ServiceAsset>('/services'),
      fetchAllPages<CertificateAsset>('/certificates'),
      fetchAllPages<ClientApplicationAsset>('/client-applications'),
      fetchAllPages<CredentialAsset>('/credentials'),
    ]);

    return {
      organizations,
      domains,
      ips,
      netblocks,
      services,
      certificates,
      clientApplications,
      credentials,
    };
  },
};
