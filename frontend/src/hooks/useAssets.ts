import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { assetsApi } from '@/services/api/assets';
import { useProject } from '@/contexts/ProjectContext';
import type {
  ScopePolicy,
  IPCreatePayload,
  IPUpdatePayload,
  DomainCreatePayload,
  DomainUpdatePayload,
  ServiceCreatePayload,
  ServiceUpdatePayload,
  OrganizationCreatePayload,
  OrganizationUpdatePayload,
  NetblockCreatePayload,
  NetblockUpdatePayload,
  CertificateCreatePayload,
  CertificateUpdatePayload,
  ClientApplicationCreatePayload,
  ClientApplicationUpdatePayload,
  CredentialCreatePayload,
  CredentialUpdatePayload,
} from '@/types/asset';

const useProjectKey = () => {
  const { currentProjectId } = useProject();
  return ['project', currentProjectId] as const;
};

export const useAllAssets = () => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'assets', 'all'],
    queryFn: () => assetsApi.getAllAssets(),
    staleTime: 5 * 60 * 1000,
  });
};

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
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'ips', params],
    queryFn: () => assetsApi.getIPs(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useIPDetail = (address: string) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'ip', address],
    queryFn: () => assetsApi.getIPDetail(address),
    enabled: !!address,
  });
};

export const useCreateIP = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: IPCreatePayload) => assetsApi.createIP(payload),
    onSuccess: () => {
      message.success('IP created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'ips'] });
    },
    onError: () => {
      message.error('IP create failed');
    },
  });
};

export const useUpdateIP = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: IPUpdatePayload }) =>
      assetsApi.updateIP(id, payload),
    onSuccess: () => {
      message.success('IP updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'ip'] });
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'ips'] });
    },
    onError: () => {
      message.error('IP update failed');
    },
  });
};

export const useUpdateIPScope = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, scopePolicy }: { id: string; scopePolicy: ScopePolicy }) =>
      assetsApi.updateIP(id, { scope_policy: scopePolicy }),
    onSuccess: () => {
      message.success('Scope policy updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'ip'] });
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'ips'] });
    },
    onError: () => {
      message.error('Scope policy update failed');
    },
  });
};

export const useDeleteIP = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteIP(id),
    onSuccess: () => {
      message.success('IP deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'ips'] });
    },
    onError: () => {
      message.error('IP delete failed');
    },
  });
};

export const useDomainList = (params: {
  page?: number;
  page_size?: number;
  root_domain?: string;
  tier?: number;
  is_resolved?: boolean;
  is_wildcard?: boolean;
  has_waf?: boolean;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'domains', params],
    queryFn: () => assetsApi.getDomains(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useAllDomains = () => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'domains', 'all'],
    queryFn: () => assetsApi.getAllDomains(),
    staleTime: 5 * 60 * 1000,
  });
};

export const useDomainDetail = (name: string) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'domain', name],
    queryFn: () => assetsApi.getDomainDetail(name),
    enabled: !!name,
  });
};

export const useCreateDomain = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: DomainCreatePayload) => assetsApi.createDomain(payload),
    onSuccess: () => {
      message.success('Domain created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'domains'] });
    },
    onError: () => {
      message.error('Domain create failed');
    },
  });
};

export const useUpdateDomain = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DomainUpdatePayload }) =>
      assetsApi.updateDomain(id, payload),
    onSuccess: () => {
      message.success('Domain updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'domain'] });
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'domains'] });
    },
    onError: () => {
      message.error('Domain update failed');
    },
  });
};

export const useDeleteDomain = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteDomain(id),
    onSuccess: () => {
      message.success('Domain deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'domains'] });
    },
    onError: () => {
      message.error('Domain delete failed');
    },
  });
};

export const useServiceList = (params: {
  page?: number;
  page_size?: number;
  port?: number;
  protocol?: 'TCP' | 'UDP';
  is_http?: boolean;
  asset_category?: string;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'services', params],
    queryFn: () => assetsApi.getServices(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useServiceDetail = (id: string) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'service', id],
    queryFn: () => assetsApi.getServiceDetail(id),
    enabled: !!id,
  });
};

export const useCreateService = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ServiceCreatePayload) => assetsApi.createService(payload),
    onSuccess: () => {
      message.success('Service created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'services'] });
    },
    onError: () => {
      message.error('Service create failed');
    },
  });
};

export const useUpdateService = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ServiceUpdatePayload }) =>
      assetsApi.updateService(id, payload),
    onSuccess: () => {
      message.success('Service updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'service'] });
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'services'] });
    },
    onError: () => {
      message.error('Service update failed');
    },
  });
};

export const useDeleteService = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteService(id),
    onSuccess: () => {
      message.success('Service deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'services'] });
    },
    onError: () => {
      message.error('Service delete failed');
    },
  });
};

export const useOrganizationList = (params: {
  page?: number;
  page_size?: number;
  is_primary?: boolean;
  tier?: number;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'organizations', params],
    queryFn: () => assetsApi.getOrganizations(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateOrganization = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: OrganizationCreatePayload) => assetsApi.createOrganization(payload),
    onSuccess: () => {
      message.success('Organization created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'organizations'] });
    },
    onError: () => {
      message.error('Organization create failed');
    },
  });
};

export const useUpdateOrganization = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: OrganizationUpdatePayload;
    }) => assetsApi.updateOrganization(id, payload),
    onSuccess: () => {
      message.success('Organization updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'organizations'] });
    },
    onError: () => {
      message.error('Organization update failed');
    },
  });
};

export const useDeleteOrganization = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteOrganization(id),
    onSuccess: () => {
      message.success('Organization deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'organizations'] });
    },
    onError: () => {
      message.error('Organization delete failed');
    },
  });
};

export const useNetblockList = (params: {
  page?: number;
  page_size?: number;
  asn_number?: string;
  is_internal?: boolean;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'netblocks', params],
    queryFn: () => assetsApi.getNetblocks(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateNetblock = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: NetblockCreatePayload) => assetsApi.createNetblock(payload),
    onSuccess: () => {
      message.success('Netblock created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'netblocks'] });
    },
    onError: () => {
      message.error('Netblock create failed');
    },
  });
};

export const useUpdateNetblock = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: NetblockUpdatePayload }) =>
      assetsApi.updateNetblock(id, payload),
    onSuccess: () => {
      message.success('Netblock updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'netblocks'] });
    },
    onError: () => {
      message.error('Netblock update failed');
    },
  });
};

export const useDeleteNetblock = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteNetblock(id),
    onSuccess: () => {
      message.success('Netblock deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'netblocks'] });
    },
    onError: () => {
      message.error('Netblock delete failed');
    },
  });
};

export const useCertificateList = (params: {
  page?: number;
  page_size?: number;
  is_expired?: boolean;
  is_self_signed?: boolean;
  is_revoked?: boolean;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'certificates', params],
    queryFn: () => assetsApi.getCertificates(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateCertificate = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CertificateCreatePayload) => assetsApi.createCertificate(payload),
    onSuccess: () => {
      message.success('Certificate created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'certificates'] });
    },
    onError: () => {
      message.error('Certificate create failed');
    },
  });
};

export const useUpdateCertificate = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: CertificateUpdatePayload;
    }) => assetsApi.updateCertificate(id, payload),
    onSuccess: () => {
      message.success('Certificate updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'certificates'] });
    },
    onError: () => {
      message.error('Certificate update failed');
    },
  });
};

export const useDeleteCertificate = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteCertificate(id),
    onSuccess: () => {
      message.success('Certificate deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'certificates'] });
    },
    onError: () => {
      message.error('Certificate delete failed');
    },
  });
};

export const useClientApplicationList = (params: {
  page?: number;
  page_size?: number;
  platform?: string;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'client-applications', params],
    queryFn: () => assetsApi.getClientApplications(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateClientApplication = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ClientApplicationCreatePayload) =>
      assetsApi.createClientApplication(payload),
    onSuccess: () => {
      message.success('Client application created');
      queryClient.invalidateQueries({
        queryKey: [...projectKey, 'client-applications'],
      });
    },
    onError: () => {
      message.error('Client application create failed');
    },
  });
};

export const useUpdateClientApplication = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: ClientApplicationUpdatePayload;
    }) => assetsApi.updateClientApplication(id, payload),
    onSuccess: () => {
      message.success('Client application updated');
      queryClient.invalidateQueries({
        queryKey: [...projectKey, 'client-applications'],
      });
    },
    onError: () => {
      message.error('Client application update failed');
    },
  });
};

export const useDeleteClientApplication = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteClientApplication(id),
    onSuccess: () => {
      message.success('Client application deleted');
      queryClient.invalidateQueries({
        queryKey: [...projectKey, 'client-applications'],
      });
    },
    onError: () => {
      message.error('Client application delete failed');
    },
  });
};

export const useCredentialList = (params: {
  page?: number;
  page_size?: number;
  cred_type?: string;
  provider?: string;
  validation_result?: string;
  scope_policy?: ScopePolicy;
}) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'credentials', params],
    queryFn: () => assetsApi.getCredentials(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateCredential = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CredentialCreatePayload) => assetsApi.createCredential(payload),
    onSuccess: () => {
      message.success('Credential created');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'credentials'] });
    },
    onError: () => {
      message.error('Credential create failed');
    },
  });
};

export const useUpdateCredential = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CredentialUpdatePayload }) =>
      assetsApi.updateCredential(id, payload),
    onSuccess: () => {
      message.success('Credential updated');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'credentials'] });
    },
    onError: () => {
      message.error('Credential update failed');
    },
  });
};

export const useDeleteCredential = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => assetsApi.deleteCredential(id),
    onSuccess: () => {
      message.success('Credential deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'credentials'] });
    },
    onError: () => {
      message.error('Credential delete failed');
    },
  });
};
