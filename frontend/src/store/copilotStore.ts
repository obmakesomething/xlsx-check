import { create } from 'zustand';
import type { ChatMessage, TaskType, CopilotResponse } from '../types/copilot';
import { copilotApi } from '../api/copilot';

interface CopilotState {
  messages: ChatMessage[];
  isLoading: boolean;
  currentTaskType: TaskType | undefined;
  currentAgent: string | null;
  error: string | null;

  sendMessage: (params: {
    message: string;
    taskType?: TaskType;
    projectId?: string;
    files?: File[];
  }) => Promise<CopilotResponse | null>;
  setTaskType: (type: TaskType | undefined) => void;
  clearMessages: () => void;
  addSystemMessage: (content: string) => void;
}

let msgCounter = 0;
function nextId() {
  return `msg-${Date.now()}-${++msgCounter}`;
}

export const useCopilotStore = create<CopilotState>((set, get) => ({
  messages: [],
  isLoading: false,
  currentTaskType: undefined,
  currentAgent: null,
  error: null,

  sendMessage: async ({ message, taskType, projectId, files }) => {
    const userMsg: ChatMessage = {
      id: nextId(),
      role: 'user',
      content: message,
      task_type: taskType,
      files: files?.map((f) => ({ name: f.name, type: f.type })),
      timestamp: new Date().toISOString(),
    };
    set((s) => ({ messages: [...s.messages, userMsg], isLoading: true, error: null }));

    try {
      let response: CopilotResponse;
      if (files && files.length > 0) {
        response = await copilotApi.chatWithFiles({ message, task_type: taskType, project_id: projectId, files });
      } else {
        response = await copilotApi.chat({ message, task_type: taskType, project_id: projectId });
      }

      const assistantMsg: ChatMessage = {
        id: nextId(),
        role: 'assistant',
        content: response.message,
        task_type: response.task_type,
        agent: response.agent,
        analysis: response,
        timestamp: response.timestamp,
      };

      set((s) => ({
        messages: [...s.messages, assistantMsg],
        isLoading: false,
        currentAgent: response.agent,
      }));
      return response;
    } catch (e: unknown) {
      const errMsg = (e as Error).message || '오류가 발생했습니다';
      set((s) => ({
        messages: [
          ...s.messages,
          { id: nextId(), role: 'system', content: `오류: ${errMsg}`, timestamp: new Date().toISOString() },
        ],
        isLoading: false,
        error: errMsg,
      }));
      return null;
    }
  },

  setTaskType: (type) => set({ currentTaskType: type }),
  clearMessages: () => set({ messages: [], currentAgent: null, error: null }),
  addSystemMessage: (content) =>
    set((s) => ({
      messages: [...s.messages, { id: nextId(), role: 'system', content, timestamp: new Date().toISOString() }],
    })),
}));
