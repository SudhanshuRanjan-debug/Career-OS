/**
 * Analytics API Client Service.
 * Stage 9: Analytics & Settings.
 */

import { apiClient } from "@/lib/axios";
import type {
  AnalyticsOverviewResponse,
  ApplicationTrendsResponse,
  PipelineAnalyticsResponse,
  CompanyAnalyticsResponse,
  OutcomeAnalyticsResponse,
  TimeAnalyticsResponse,
  DashboardSummaryResponse,
} from "@/types/analytics.types";

export const analyticsService = {
  async getOverview(): Promise<AnalyticsOverviewResponse> {
    const res = await apiClient.get<AnalyticsOverviewResponse>("/analytics/overview");
    return res.data;
  },

  async getTrends(range: string = "30d"): Promise<ApplicationTrendsResponse> {
    const res = await apiClient.get<ApplicationTrendsResponse>("/analytics/trends", {
      params: { range },
    });
    return res.data;
  },

  async getPipeline(): Promise<PipelineAnalyticsResponse> {
    const res = await apiClient.get<PipelineAnalyticsResponse>("/analytics/pipeline");
    return res.data;
  },

  async getCompanies(): Promise<CompanyAnalyticsResponse> {
    const res = await apiClient.get<CompanyAnalyticsResponse>("/analytics/companies");
    return res.data;
  },

  async getOutcomes(): Promise<OutcomeAnalyticsResponse> {
    const res = await apiClient.get<OutcomeAnalyticsResponse>("/analytics/outcomes");
    return res.data;
  },

  async getTime(): Promise<TimeAnalyticsResponse> {
    const res = await apiClient.get<TimeAnalyticsResponse>("/analytics/time");
    return res.data;
  },

  async getDashboardSummary(): Promise<DashboardSummaryResponse> {
    const res = await apiClient.get<DashboardSummaryResponse>("/dashboard/summary");
    return res.data;
  },
};
