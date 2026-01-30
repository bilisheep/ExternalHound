import axios from 'axios';
import { message } from 'antd';
import { getCurrentProjectId } from '@/utils/projects';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;

    if (!status) {
      message.error('Network error');
      return Promise.reject(error);
    }

    switch (status) {
      case 400:
        message.error('Bad request');
        break;
      case 401:
        message.error('Unauthorized');
        break;
      case 403:
        message.error('Forbidden');
        break;
      case 404:
        message.error('Not found');
        break;
      case 500:
        message.error('Server error');
        break;
      default:
        message.error('Request failed');
    }

    return Promise.reject(error);
  }
);

apiClient.interceptors.request.use((config) => {
  const projectId = getCurrentProjectId();
  if (!projectId) {
    return config;
  }

  config.headers = {
    ...config.headers,
    'X-Project-Id': projectId,
  };

  if (config.params instanceof URLSearchParams) {
    if (!config.params.has('project_id')) {
      config.params.append('project_id', projectId);
    }
    return config;
  }

  if (!config.params || typeof config.params !== 'object') {
    config.params = { project_id: projectId };
    return config;
  }

  if (!('project_id' in config.params)) {
    config.params = { ...config.params, project_id: projectId };
  }

  return config;
});
