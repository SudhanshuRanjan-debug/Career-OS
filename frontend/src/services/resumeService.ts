/**
 * Resumes API Service.
 */

import { apiClient } from "@/lib/axios";
import type { ResumeItem, ResumeListResponse } from "@/types/resume.types";

export const resumeService = {
  async listResumes(): Promise<ResumeListResponse> {
    const res = await apiClient.get<ResumeListResponse>("/resumes");
    return res.data;
  },

  async uploadResume(file: File, name?: string): Promise<ResumeItem> {
    const formData = new FormData();
    formData.append("file", file);
    if (name) {
      formData.append("name", name);
    }
    const res = await apiClient.post<ResumeItem>("/resumes/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return res.data;
  },

  async renameResume(id: string, name: string): Promise<ResumeItem> {
    const res = await apiClient.put<ResumeItem>(`/resumes/${id}`, { name });
    return res.data;
  },

  async setDefaultResume(id: string): Promise<ResumeItem> {
    const res = await apiClient.post<ResumeItem>(`/resumes/${id}/set-default`);
    return res.data;
  },

  async downloadResume(id: string, filename: string): Promise<void> {
    const res = await apiClient.get(`/resumes/${id}/download`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async deleteResume(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/resumes/${id}`);
    return res.data;
  },
};
