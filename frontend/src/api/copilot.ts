import client from './client';
import type { CopilotResponse, TaskType } from '../types/copilot';

export const copilotApi = {
  chat: async (params: {
    message: string;
    task_type?: TaskType;
    project_id?: string;
    context?: Record<string, unknown>;
  }): Promise<CopilotResponse> => {
    const { data } = await client.post('/copilot/chat', params);
    return data;
  },

  chatWithFiles: async (params: {
    message: string;
    task_type?: TaskType;
    project_id?: string;
    files: File[];
  }): Promise<CopilotResponse> => {
    const formData = new FormData();
    formData.append('message', params.message);
    if (params.task_type) formData.append('task_type', params.task_type);
    if (params.project_id) formData.append('project_id', params.project_id);
    params.files.forEach((file) => formData.append('files', file));
    const { data } = await client.post('/copilot/chat', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },

  getHistory: async (projectId?: string): Promise<CopilotResponse[]> => {
    const { data } = await client.get('/copilot/history', {
      params: projectId ? { project_id: projectId } : {},
    });
    return data;
  },

  analyzeDesign: async (projectId: string): Promise<CopilotResponse> => {
    const { data } = await client.post('/copilot/analyze/design', { project_id: projectId });
    return data;
  },

  analyzeBom: async (projectId: string): Promise<CopilotResponse> => {
    const { data } = await client.post('/copilot/analyze/bom', { project_id: projectId });
    return data;
  },

  analyzeReview: async (projectId: string): Promise<CopilotResponse> => {
    const { data } = await client.post('/copilot/analyze/review', { project_id: projectId });
    return data;
  },
};
