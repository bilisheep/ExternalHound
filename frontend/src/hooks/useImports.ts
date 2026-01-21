import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { importsApi } from '@/services/api/imports';

export const usePluginList = () => {
  return useQuery({
    queryKey: ['plugins'],
    queryFn: () => importsApi.listPlugins(),
    staleTime: 5 * 60 * 1000,
  });
};

export const useImportList = (params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: ['imports', params],
    queryFn: () => importsApi.listImports(params),
    staleTime: 10 * 1000,
  });
};

export const useUploadImport = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { file: File; parserName?: string; createdBy?: string }) =>
      importsApi.uploadImport(payload),
    onSuccess: () => {
      message.success('Import completed');
      queryClient.invalidateQueries({ queryKey: ['imports'] });
    },
    onError: () => {
      message.error('Import failed');
    },
  });
};

export const useDeleteImportFile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => importsApi.deleteImportFile(id),
    onSuccess: () => {
      message.success('File deleted');
      queryClient.invalidateQueries({ queryKey: ['imports'] });
    },
    onError: () => {
      message.error('File delete failed');
    },
  });
};
