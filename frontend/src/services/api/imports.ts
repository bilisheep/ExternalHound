import { apiClient } from '@/services/api/client';
import type { ImportListResponse, ImportLog, PluginInfo } from '@/types/import';

export const importsApi = {
  listPlugins: async (): Promise<PluginInfo[]> => {
    const response = await apiClient.get<PluginInfo[]>('/imports/plugins');
    return response.data;
  },
  listImports: async (params?: { limit?: number; offset?: number }): Promise<ImportListResponse> => {
    const response = await apiClient.get<ImportListResponse>('/imports', { params });
    return response.data;
  },
  uploadImport: async (payload: {
    file: File;
    parserName?: string;
    createdBy?: string;
  }): Promise<ImportLog> => {
    const formData = new FormData();
    formData.append('file', payload.file);
    if (payload.parserName) {
      formData.append('parser_name', payload.parserName);
    }
    if (payload.createdBy) {
      formData.append('created_by', payload.createdBy);
    }
    const response = await apiClient.post<ImportLog>('/imports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  deleteImportFile: async (id: string): Promise<void> => {
    await apiClient.delete(`/imports/${id}`);
  },
};
