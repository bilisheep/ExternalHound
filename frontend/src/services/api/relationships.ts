import { apiClient } from './client';
import type { PaginatedResponse } from '@/types/api';
import type {
  RelationshipCreatePayload,
  RelationshipRecord,
  RelationshipType,
  RelationshipUpdatePayload,
  NodeType,
} from '@/types/relationship';

export const relationshipsApi = {
  getRelationship: async (id: string): Promise<RelationshipRecord> => {
    const { data } = await apiClient.get(`/relationships/${id}`);
    return data;
  },

  getRelationships: async (params: {
    page?: number;
    page_size?: number;
    source_external_id?: string;
    source_type?: NodeType;
    target_external_id?: string;
    target_type?: NodeType;
    relation_type?: RelationshipType;
    edge_key?: string;
    include_deleted?: boolean;
  }): Promise<PaginatedResponse<RelationshipRecord>> => {
    const { data } = await apiClient.get('/relationships', { params });
    return data;
  },
  getAllRelationships: async (params: {
    source_external_id?: string;
    source_type?: NodeType;
    target_external_id?: string;
    target_type?: NodeType;
    relation_type?: RelationshipType;
    edge_key?: string;
    include_deleted?: boolean;
  }): Promise<RelationshipRecord[]> => {
    const pageSize = 100;
    let page = 1;
    let totalPages = 1;
    const items: RelationshipRecord[] = [];

    do {
      const { data } = await apiClient.get<PaginatedResponse<RelationshipRecord>>(
        '/relationships',
        {
          params: {
            ...params,
            page,
            page_size: pageSize,
          },
        }
      );
      items.push(...data.items);
      totalPages = data.total_pages;
      page += 1;
    } while (page <= totalPages);

    return items;
  },

  createRelationship: async (
    payload: RelationshipCreatePayload
  ): Promise<RelationshipRecord> => {
    const { data } = await apiClient.post('/relationships', payload);
    return data;
  },

  createRelationshipIfMissing: async (
    payload: RelationshipCreatePayload
  ): Promise<RelationshipRecord | null> => {
    const response = await apiClient.post('/relationships', payload, {
      validateStatus: (status) => status === 201 || status === 409,
    });
    if (response.status === 409) {
      return null;
    }
    return response.data;
  },

  updateRelationship: async (
    id: string,
    payload: RelationshipUpdatePayload
  ): Promise<RelationshipRecord> => {
    const { data } = await apiClient.put(`/relationships/${id}`, payload);
    return data;
  },

  deleteRelationship: async (id: string): Promise<void> => {
    await apiClient.delete(`/relationships/${id}`);
  },
};
