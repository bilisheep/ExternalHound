import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { relationshipsApi } from '@/services/api/relationships';
import type {
  RelationshipCreatePayload,
  RelationshipType,
  RelationshipUpdatePayload,
  NodeType,
} from '@/types/relationship';

export const useRelationshipList = (params: {
  page?: number;
  page_size?: number;
  source_external_id?: string;
  source_type?: NodeType;
  target_external_id?: string;
  target_type?: NodeType;
  relation_type?: RelationshipType;
  edge_key?: string;
  include_deleted?: boolean;
}) => {
  return useQuery({
    queryKey: ['relationships', params],
    queryFn: () => relationshipsApi.getRelationships(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useAllRelationships = (params: {
  source_external_id?: string;
  source_type?: NodeType;
  target_external_id?: string;
  target_type?: NodeType;
  relation_type?: RelationshipType;
  edge_key?: string;
  include_deleted?: boolean;
}) => {
  return useQuery({
    queryKey: ['relationships', 'all', params],
    queryFn: () => relationshipsApi.getAllRelationships(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateRelationship = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: RelationshipCreatePayload) =>
      relationshipsApi.createRelationship(payload),
    onSuccess: () => {
      message.success('Relationship created');
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
    },
    onError: () => {
      message.error('Relationship create failed');
    },
  });
};

export const useUpdateRelationship = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: RelationshipUpdatePayload }) =>
      relationshipsApi.updateRelationship(id, payload),
    onSuccess: () => {
      message.success('Relationship updated');
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
    },
    onError: () => {
      message.error('Relationship update failed');
    },
  });
};

export const useDeleteRelationship = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => relationshipsApi.deleteRelationship(id),
    onSuccess: () => {
      message.success('Relationship deleted');
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
    },
    onError: () => {
      message.error('Relationship delete failed');
    },
  });
};
