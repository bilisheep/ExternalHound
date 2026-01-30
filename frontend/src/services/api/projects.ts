import { apiClient } from '@/services/api/client';

export type PostgresConfig = {
  host: string;
  port: number;
  user: string;
  database: string;
  sslmode?: string | null;
  schema?: string | null;
  has_password?: boolean;
};

export type Neo4jConfig = {
  uri: string;
  user: string;
  has_password?: boolean;
};

export type ProjectConfig = {
  project_id: string;
  postgres?: PostgresConfig | null;
  neo4j?: Neo4jConfig | null;
};

export type PostgresConfigUpdate = {
  host?: string;
  port?: number;
  user?: string;
  password?: string;
  database?: string;
  sslmode?: string;
  schema?: string;
};

export type Neo4jConfigUpdate = {
  uri?: string;
  user?: string;
  password?: string;
};

export type ProjectConfigUpdatePayload = {
  postgres?: PostgresConfigUpdate;
  neo4j?: Neo4jConfigUpdate;
  reset_postgres?: boolean;
  reset_neo4j?: boolean;
};

export const projectsApi = {
  getConfig: async (projectId: string): Promise<ProjectConfig> => {
    const { data } = await apiClient.get<ProjectConfig>(`/projects/${projectId}/config`);
    return data;
  },
  updateConfig: async (
    projectId: string,
    payload: ProjectConfigUpdatePayload
  ): Promise<ProjectConfig> => {
    const { data } = await apiClient.put<ProjectConfig>(
      `/projects/${projectId}/config`,
      payload
    );
    return data;
  },
  deleteConfig: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/projects/${projectId}/config`);
  },
};
