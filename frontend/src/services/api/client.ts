import axios from 'axios';
import { message } from 'antd';

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
