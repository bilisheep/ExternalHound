export interface PluginInfo {
  name: string;
  version: string;
  entrypoint: string;
  supported_formats: string[];
  priority: number;
  description?: string | null;
  vendor?: string | null;
}

export interface ImportLog {
  id: string;
  filename: string;
  file_size?: number | null;
  file_hash?: string | null;
  file_path?: string | null;
  format: string;
  parser_version?: string | null;
  status: string;
  progress: number;
  records_total: number;
  records_success: number;
  records_failed: number;
  error_message?: string | null;
  error_details?: Record<string, unknown> | null;
  assets_created: Record<string, number>;
  created_at: string;
  updated_at: string;
  created_by?: string | null;
  duration_seconds?: number | null;
}

export interface ImportListResponse {
  items: ImportLog[];
  total: number;
}
