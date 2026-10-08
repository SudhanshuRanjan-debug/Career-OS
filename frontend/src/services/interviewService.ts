/**
 * Interview & Interview Preparation API Service.
 * Stage 7: Interviews & Interview Preparation.
 */

import { apiClient } from "@/lib/axios";
import type {
  Interview,
  InterviewCreateInput,
  InterviewListResponse,
  InterviewPreparation,
  InterviewPreparationUpdateInput,
  InterviewType,
  InterviewUpdateInput,
} from "@/types/interview.types";

export interface InterviewFilterParams {
  search?: string;
  status?: string;
  interview_type?: InterviewType;
  application_id?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export const interviewService = {
  // -------------------------------------------------------------------------
  // Interviews CRUD
  // -------------------------------------------------------------------------

  async listInterviews(params?: InterviewFilterParams): Promise<InterviewListResponse> {
    const res = await apiClient.get<InterviewListResponse>("/interviews", { params });
    return res.data;
  },

  async createInterview(data: InterviewCreateInput): Promise<Interview> {
    const res = await apiClient.post<Interview>("/interviews", data);
    return res.data;
  },

  async getInterview(id: string): Promise<Interview> {
    const res = await apiClient.get<Interview>(`/interviews/${id}`);
    return res.data;
  },

  async updateInterview(id: string, data: InterviewUpdateInput): Promise<Interview> {
    const res = await apiClient.put<Interview>(`/interviews/${id}`, data);
    return res.data;
  },

  async deleteInterview(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.delete<{ success: boolean; message: string }>(`/interviews/${id}`);
    return res.data;
  },

  // -------------------------------------------------------------------------
  // Interview Preparation
  // -------------------------------------------------------------------------

  async getPreparation(interviewId: string): Promise<InterviewPreparation> {
    const res = await apiClient.get<InterviewPreparation>(`/interviews/${interviewId}/preparation`);
    return res.data;
  },

  async updatePreparation(
    interviewId: string,
    data: InterviewPreparationUpdateInput
  ): Promise<InterviewPreparation> {
    const res = await apiClient.put<InterviewPreparation>(
      `/interviews/${interviewId}/preparation`,
      data
    );
    return res.data;
  },

  // -------------------------------------------------------------------------
  // Application Interviews Sub-Resource
  // -------------------------------------------------------------------------

  async listApplicationInterviews(applicationId: string): Promise<Interview[]> {
    const res = await apiClient.get<Interview[]>(`/applications/${applicationId}/interviews`);
    return res.data;
  },
};
