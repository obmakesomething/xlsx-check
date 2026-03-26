import client from './client';
import type { Component, ComponentSearchParams, LCSCComponent, SubstitutePart } from '../types/component';
import type { PaginatedResponse } from '../types/common';

export const componentsApi = {
  search: async (params: ComponentSearchParams): Promise<PaginatedResponse<Component>> => {
    const { data } = await client.get('/components', { params });
    return data;
  },

  get: async (id: string): Promise<Component> => {
    const { data } = await client.get(`/components/${id}`);
    return data;
  },

  getSubstitutes: async (id: string): Promise<SubstitutePart[]> => {
    const { data } = await client.get(`/components/${id}/substitutes`);
    return data;
  },

  searchLCSC: async (query: string, page = 1): Promise<PaginatedResponse<LCSCComponent>> => {
    const { data } = await client.get('/components/lcsc/search', {
      params: { query, page },
    });
    return data;
  },

  getUsageHistory: async (id: string): Promise<{ project_id: string; project_name: string; quantity: number; date: string }[]> => {
    const { data } = await client.get(`/components/${id}/usage`);
    return data;
  },

  create: async (component: Omit<Component, 'id' | 'usage_count' | 'last_used' | 'substitutes'>): Promise<Component> => {
    const { data } = await client.post('/components', component);
    return data;
  },

  update: async (id: string, updates: Partial<Component>): Promise<Component> => {
    const { data } = await client.patch(`/components/${id}`, updates);
    return data;
  },
};
