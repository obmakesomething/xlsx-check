export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export type Status = 'draft' | 'in_progress' | 'review' | 'completed' | 'archived';

export interface SelectOption {
  value: string;
  label: string;
}

export interface FileUploadResult {
  filename: string;
  file_type: string;
  parsed_data: Record<string, unknown>;
  warnings: string[];
}

export interface Activity {
  id: string;
  type: 'project_created' | 'bom_generated' | 'analysis_completed' | 'component_added' | 'file_uploaded';
  description: string;
  project_id?: string;
  project_name?: string;
  timestamp: string;
}

export interface Stats {
  total_projects: number;
  total_components: number;
  boms_generated: number;
  analyses_run: number;
}
