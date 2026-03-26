import { create } from 'zustand';
import type { Project, ProductSpec, BomItem, CostBreakdown, CertificationItem, TimelineEvent, CircuitBlock } from '../types/project';
import type { Stats, Activity } from '../types/common';
import { projectsApi } from '../api/projects';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  circuitBlocks: CircuitBlock[];
  bomItems: BomItem[];
  costBreakdown: CostBreakdown | null;
  certifications: CertificationItem[];
  timeline: TimelineEvent[];
  stats: Stats;
  recentActivity: Activity[];
  loading: boolean;
  error: string | null;

  fetchProjects: () => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  createProject: (data: { name: string; description: string; spec: ProductSpec }) => Promise<Project>;
  updateProject: (id: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  fetchCircuitBlocks: (id: string) => Promise<void>;
  fetchBom: (id: string) => Promise<void>;
  updateBomItem: (projectId: string, itemId: string, updates: Partial<BomItem>) => Promise<void>;
  fetchCostBreakdown: (id: string) => Promise<void>;
  fetchCertifications: (id: string) => Promise<void>;
  updateCertification: (projectId: string, itemId: string, updates: Partial<CertificationItem>) => Promise<void>;
  fetchTimeline: (id: string) => Promise<void>;
  setStats: (stats: Stats) => void;
  setRecentActivity: (activity: Activity[]) => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  circuitBlocks: [],
  bomItems: [],
  costBreakdown: null,
  certifications: [],
  timeline: [],
  stats: { total_projects: 0, total_components: 0, boms_generated: 0, analyses_run: 0 },
  recentActivity: [],
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const res = await projectsApi.list();
      set({ projects: res.items, loading: false });
    } catch (e: unknown) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  fetchProject: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const project = await projectsApi.get(id);
      set({ currentProject: project, loading: false });
    } catch (e: unknown) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  createProject: async (data) => {
    set({ loading: true, error: null });
    try {
      const project = await projectsApi.create(data);
      set((s) => ({ projects: [project, ...s.projects], loading: false }));
      return project;
    } catch (e: unknown) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  updateProject: async (id, updates) => {
    try {
      const project = await projectsApi.update(id, updates);
      set((s) => ({
        projects: s.projects.map((p) => (p.id === id ? project : p)),
        currentProject: s.currentProject?.id === id ? project : s.currentProject,
      }));
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  deleteProject: async (id) => {
    try {
      await projectsApi.delete(id);
      set((s) => ({
        projects: s.projects.filter((p) => p.id !== id),
        currentProject: s.currentProject?.id === id ? null : s.currentProject,
      }));
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  fetchCircuitBlocks: async (id) => {
    try {
      const blocks = await projectsApi.getCircuitBlocks(id);
      set({ circuitBlocks: blocks });
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  fetchBom: async (id) => {
    try {
      const items = await projectsApi.getBom(id);
      set({ bomItems: items });
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  updateBomItem: async (projectId, itemId, updates) => {
    try {
      const item = await projectsApi.updateBomItem(projectId, itemId, updates);
      set((s) => ({ bomItems: s.bomItems.map((i) => (i.id === itemId ? item : i)) }));
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  fetchCostBreakdown: async (id) => {
    try {
      const cost = await projectsApi.getCostBreakdown(id);
      set({ costBreakdown: cost });
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  fetchCertifications: async (id) => {
    try {
      const certs = await projectsApi.getCertifications(id);
      set({ certifications: certs });
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  updateCertification: async (projectId, itemId, updates) => {
    try {
      const item = await projectsApi.updateCertification(projectId, itemId, updates);
      set((s) => ({ certifications: s.certifications.map((c) => (c.id === itemId ? item : c)) }));
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  fetchTimeline: async (id) => {
    try {
      const events = await projectsApi.getTimeline(id);
      set({ timeline: events });
    } catch (e: unknown) {
      set({ error: (e as Error).message });
    }
  },

  setStats: (stats) => set({ stats }),
  setRecentActivity: (activity) => set({ recentActivity: activity }),
}));
