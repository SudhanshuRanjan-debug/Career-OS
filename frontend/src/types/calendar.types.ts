export type CalendarEventType = "INTERVIEW" | "TASK" | "FOLLOW_UP" | "DEADLINE";

export interface CalendarEvent {
  id: string;
  entity_id: string;
  event_type: CalendarEventType;
  title: string;
  description?: string | null;
  date: string;
  start_time?: string | null;
  end_time?: string | null;
  all_day: boolean;
  status?: string | null;
  priority?: string | null;
  color?: string | null;
  meeting_link?: string | null;
  related_type?: string | null;
  related_id?: string | null;
  company_name?: string | null;
  job_title?: string | null;
}

export interface CalendarScheduleResponse {
  events: CalendarEvent[];
  total_events: number;
  start_date?: string | null;
  end_date?: string | null;
}
