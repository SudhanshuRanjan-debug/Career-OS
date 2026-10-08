/**
 * Application Domain API Service.
 * Stage 5 Master Implementation.
 */

import { apiClient } from "@/lib/axios";
import type {
  Application,
  ApplicationActivity,
  ApplicationAnswer,
  ApplicationConvertInput,
  ApplicationCreateInput,
  ApplicationDocument,
  ApplicationFollowup,
  ApplicationFollowupWithApp,
  ApplicationHealth,
  ApplicationListResponse,
  ApplicationNote,
  ApplicationUpdateInput,
  PipelineResponse,
  QAVaultEntry,
  StageHistory,
} from "@/types/application.types";

export interface ApplicationFilterParams {
  search?: string;
  status?: string;
  stage?: string;
  priority?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export const applicationService = {
  // Applications Collection
  async listApplications(params?: ApplicationFilterParams): Promise<ApplicationListResponse> {
    const res = await apiClient.get<ApplicationListResponse>("/applications", { params });
    return res.data;
  },

  async createApplication(data: ApplicationCreateInput): Promise<Application> {
    const res = await apiClient.post<Application>("/applications", data);
    return res.data;
  },

  async getPipeline(): Promise<PipelineResponse> {
    const res = await apiClient.get<PipelineResponse>("/applications/pipeline");
    return res.data;
  },

  async getGlobalFollowups(is_completed?: boolean): Promise<ApplicationFollowupWithApp[]> {
    const params = is_completed !== undefined ? { is_completed } : undefined;
    const res = await apiClient.get<ApplicationFollowupWithApp[]>("/applications/followups", { params });
    return res.data;
  },

  // Single Application
  async getApplication(id: string): Promise<Application> {
    const res = await apiClient.get<Application>(`/applications/${id}`);
    return res.data;
  },

  async updateApplication(id: string, data: ApplicationUpdateInput): Promise<Application> {
    const res = await apiClient.put<Application>(`/applications/${id}`, data);
    return res.data;
  },

  async deleteApplication(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/applications/${id}`);
    return res.data;
  },

  async convertOpportunity(opportunityId: string, data: ApplicationConvertInput): Promise<Application> {
    const res = await apiClient.post<Application>(`/opportunities/${opportunityId}/convert`, data);
    return res.data;
  },

  // Stage Transitions & History
  async transitionStage(id: string, to_stage: string, notes?: string): Promise<Application> {
    const res = await apiClient.post<Application>(`/applications/${id}/stage`, {
      to_stage,
      notes: notes || undefined,
    });
    return res.data;
  },

  async getStageHistory(id: string): Promise<StageHistory[]> {
    const res = await apiClient.get<StageHistory[]>(`/applications/${id}/stage-history`);
    return res.data;
  },

  async getActivity(id: string): Promise<ApplicationActivity[]> {
    const res = await apiClient.get<ApplicationActivity[]>(`/applications/${id}/activity`);
    return res.data;
  },

  async getHealth(id: string): Promise<ApplicationHealth> {
    const res = await apiClient.get<ApplicationHealth>(`/applications/${id}/health`);
    return res.data;
  },

  // Notes
  async getNotes(id: string): Promise<ApplicationNote[]> {
    const res = await apiClient.get<ApplicationNote[]>(`/applications/${id}/notes`);
    return res.data;
  },

  async createNote(id: string, content: string): Promise<ApplicationNote> {
    const res = await apiClient.post<ApplicationNote>(`/applications/${id}/notes`, { content });
    return res.data;
  },

  async updateNote(id: string, noteId: string, content: string): Promise<ApplicationNote> {
    const res = await apiClient.put<ApplicationNote>(`/applications/${id}/notes/${noteId}`, { content });
    return res.data;
  },

  async deleteNote(id: string, noteId: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/applications/${id}/notes/${noteId}`);
    return res.data;
  },

  // Follow-ups
  async getFollowups(id: string): Promise<ApplicationFollowup[]> {
    const res = await apiClient.get<ApplicationFollowup[]>(`/applications/${id}/followups`);
    return res.data;
  },

  async createFollowup(id: string, data: { due_date?: string | null; note?: string | null }): Promise<ApplicationFollowup> {
    const res = await apiClient.post<ApplicationFollowup>(`/applications/${id}/followups`, data);
    return res.data;
  },

  async updateFollowup(
    id: string,
    followupId: string,
    data: { due_date?: string | null; note?: string | null; is_completed?: boolean }
  ): Promise<ApplicationFollowup> {
    const res = await apiClient.put<ApplicationFollowup>(`/applications/${id}/followups/${followupId}`, data);
    return res.data;
  },

  async deleteFollowup(id: string, followupId: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/applications/${id}/followups/${followupId}`);
    return res.data;
  },

  // Supporting Documents
  async getDocuments(id: string): Promise<ApplicationDocument[]> {
    const res = await apiClient.get<ApplicationDocument[]>(`/applications/${id}/documents`);
    return res.data;
  },

  async attachDocument(id: string, document_id: string): Promise<ApplicationDocument> {
    const res = await apiClient.post<ApplicationDocument>(`/applications/${id}/documents`, { document_id });
    return res.data;
  },

  async detachDocument(id: string, documentId: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/applications/${id}/documents/${documentId}`);
    return res.data;
  },

  // Q&A Answers
  async getAnswers(id: string): Promise<ApplicationAnswer[]> {
    const res = await apiClient.get<ApplicationAnswer[]>(`/applications/${id}/answers`);
    return res.data;
  },

  async createAnswer(
    id: string,
    data: { question: string; answer: string; qa_vault_entry_id?: string | null }
  ): Promise<ApplicationAnswer> {
    const res = await apiClient.post<ApplicationAnswer>(`/applications/${id}/answers`, data);
    return res.data;
  },

  async updateAnswer(
    id: string,
    answerId: string,
    data: { question?: string; answer?: string; qa_vault_entry_id?: string | null }
  ): Promise<ApplicationAnswer> {
    const res = await apiClient.put<ApplicationAnswer>(`/applications/${id}/answers/${answerId}`, data);
    return res.data;
  },

  async deleteAnswer(id: string, answerId: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/applications/${id}/answers/${answerId}`);
    return res.data;
  },

  // Q&A Vault
  async getQAVault(category?: string): Promise<{ items: QAVaultEntry[]; total: number }> {
    const params = category ? { category } : undefined;
    const res = await apiClient.get<{ items: QAVaultEntry[]; total: number }>("/qa-vault", { params });
    return res.data;
  },

  async createQAVault(data: {
    question: string;
    answer: string;
    category?: string | null;
    is_template?: boolean;
  }): Promise<QAVaultEntry> {
    const res = await apiClient.post<QAVaultEntry>("/qa-vault", data);
    return res.data;
  },
};
