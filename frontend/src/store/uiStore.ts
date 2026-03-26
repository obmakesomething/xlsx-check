import { create } from 'zustand';

interface UIState {
  sidebarCollapsed: boolean;
  copilotOpen: boolean;
  activeModal: string | null;
  modalData: unknown;

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleCopilot: () => void;
  setCopilotOpen: (open: boolean) => void;
  openModal: (modalId: string, data?: unknown) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  copilotOpen: false,
  activeModal: null,
  modalData: null,

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleCopilot: () => set((s) => ({ copilotOpen: !s.copilotOpen })),
  setCopilotOpen: (open) => set({ copilotOpen: open }),
  openModal: (modalId, data) => set({ activeModal: modalId, modalData: data }),
  closeModal: () => set({ activeModal: null, modalData: null }),
}));
