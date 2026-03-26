import client from './client';
import type { FileUploadResult } from '../types/common';

export const parsersApi = {
  uploadBom: async (file: File): Promise<FileUploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await client.post('/parsers/bom', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },

  uploadSchematic: async (file: File): Promise<FileUploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await client.post('/parsers/schematic', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },

  uploadInterview: async (file: File): Promise<FileUploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await client.post('/parsers/interview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },

  uploadDatasheet: async (file: File): Promise<FileUploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await client.post('/parsers/datasheet', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },
};
