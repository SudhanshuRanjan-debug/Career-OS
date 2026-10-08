/**
 * Calendar API Client Service.
 * Stage 8: Tasks, Calendar & Notifications.
 */

import { apiClient } from "@/lib/axios";
import type { CalendarEventType, CalendarScheduleResponse } from "@/types/calendar.types";

export interface CalendarFilterParams {
  start_date?: string;
  end_date?: string;
  event_types?: CalendarEventType[];
}

export const calendarService = {
  async getSchedule(params?: CalendarFilterParams): Promise<CalendarScheduleResponse> {
    const res = await apiClient.get<CalendarScheduleResponse>("/calendar", { params });
    return res.data;
  },
};
