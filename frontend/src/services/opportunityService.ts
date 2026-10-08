/**
 * Opportunity & Saved Opportunity API Service.
 */

import { apiClient } from "@/lib/axios";
import type {
  Opportunity,
  OpportunityCreateInput,
  OpportunityFilterParams,
  OpportunityListResponse,
  OpportunityUpdateInput,
  SavedOpportunity,
  SavedOpportunityListResponse,
} from "@/types/opportunity.types";

export const opportunityService = {
  async listOpportunities(params?: OpportunityFilterParams): Promise<OpportunityListResponse> {
    const res = await apiClient.get<OpportunityListResponse>("/opportunities", {
      params,
    });
    return res.data;
  },

  async getOpportunity(id: string): Promise<Opportunity> {
    const res = await apiClient.get<Opportunity>(`/opportunities/${id}`);
    return res.data;
  },

  async createOpportunity(data: OpportunityCreateInput): Promise<Opportunity> {
    const res = await apiClient.post<Opportunity>("/opportunities", data);
    return res.data;
  },

  async updateOpportunity(id: string, data: OpportunityUpdateInput): Promise<Opportunity> {
    const res = await apiClient.put<Opportunity>(`/opportunities/${id}`, data);
    return res.data;
  },

  async deleteOpportunity(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/opportunities/${id}`);
    return res.data;
  },

  async saveOpportunity(id: string, notes?: string): Promise<SavedOpportunity> {
    const res = await apiClient.post<SavedOpportunity>(`/opportunities/${id}/save`, {
      notes: notes || undefined,
    });
    return res.data;
  },

  async unsaveOpportunity(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/opportunities/${id}/save`);
    return res.data;
  },

  async listSavedOpportunities(): Promise<SavedOpportunityListResponse> {
    const res = await apiClient.get<SavedOpportunityListResponse>("/opportunities/saved");
    return res.data;
  },
};
