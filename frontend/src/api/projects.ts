import client from './client';
import type { Project, ProductSpec, BomItem, CostBreakdown, CertificationItem, TimelineEvent, CircuitBlock } from '../types/project';
import type { PaginatedResponse } from '../types/common';

export const projectsApi = {
  list: async (page = 1, pageSize = 20): Promise<PaginatedResponse<Project>> => {
    const { data } = await client.get('/projects', { params: { page, page_size: pageSize } });
    return data;
  },

  get: async (id: string): Promise<Project> => {
    const { data } = await client.get(`/projects/${id}`);
    return data;
  },

  create: async (project: { name: string; description: string; spec: ProductSpec }): Promise<Project> => {
    const { data } = await client.post('/projects', project);
    return data;
  },

  update: async (id: string, updates: Partial<Project>): Promise<Project> => {
    const { data } = await client.patch(`/projects/${id}`, updates);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await client.delete(`/projects/${id}`);
  },

  getCircuitBlocks: async (id: string): Promise<CircuitBlock[]> => {
    const { data } = await client.get(`/projects/${id}/circuit-blocks`);
    return data;
  },

  getBom: async (id: string): Promise<BomItem[]> => {
    const { data } = await client.get(`/projects/${id}/bom`);
    return data;
  },

  updateBomItem: async (projectId: string, itemId: string, updates: Partial<BomItem>): Promise<BomItem> => {
    const { data } = await client.patch(`/projects/${projectId}/bom/${itemId}`, updates);
    return data;
  },

  getCostBreakdown: async (id: string): Promise<CostBreakdown> => {
    const { data } = await client.get(`/projects/${id}/cost`);
    return data;
  },

  getCertifications: async (id: string): Promise<CertificationItem[]> => {
    const { data } = await client.get(`/projects/${id}/certifications`);
    return data;
  },

  updateCertification: async (projectId: string, itemId: string, updates: Partial<CertificationItem>): Promise<CertificationItem> => {
    const { data } = await client.patch(`/projects/${projectId}/certifications/${itemId}`, updates);
    return data;
  },

  getTimeline: async (id: string): Promise<TimelineEvent[]> => {
    const { data } = await client.get(`/projects/${id}/timeline`);
    return data;
  },
};
