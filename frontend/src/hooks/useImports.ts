import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { importsApi } from '@/services/api/imports';
import { useProject } from '@/contexts/ProjectContext';

const useProjectKey = () => {
  const { currentProjectId } = useProject();
  return ['project', currentProjectId] as const;
};

export const usePluginList = () => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'plugins'],
    queryFn: () => importsApi.listPlugins(),
    staleTime: 5 * 60 * 1000,
  });
};

export const useImportList = (params?: { limit?: number; offset?: number }) => {
  const projectKey = useProjectKey();
  return useQuery({
    queryKey: [...projectKey, 'imports', params],
    queryFn: () => importsApi.listImports(params),
    staleTime: 10 * 1000,
  });
};

export const useUploadImport = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { file: File; parserName?: string; createdBy?: string }) =>
      importsApi.uploadImport(payload),
    onSuccess: () => {
      message.success('Import completed');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'imports'] });
    },
    onError: () => {
      message.error('Import failed');
    },
  });
};

export const useDeleteImportFile = () => {
  const projectKey = useProjectKey();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => importsApi.deleteImportFile(id),
    onSuccess: () => {
      message.success('File deleted');
      queryClient.invalidateQueries({ queryKey: [...projectKey, 'imports'] });
    },
    onError: () => {
      message.error('File delete failed');
    },
  });
};
