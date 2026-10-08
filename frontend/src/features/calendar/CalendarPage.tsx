import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { calendarService } from "@/services/calendarService";
import type { CalendarEvent, CalendarEventType } from "@/types/calendar.types";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Video,
  Clock,
  CheckSquare,
  Plus,
  ExternalLink,
  Briefcase,
  AlertCircle,
  Flag,
} from "lucide-react";

export const CalendarPage: React.FC = () => {
  // Calendar date navigation state
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [selectedDateStr, setSelectedDateStr] = useState<string>(() => {
    return new Date().toISOString().split("T")[0];
  });
  const [typeFilter, setTypeFilter] = useState<string>("");

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); // 0-indexed

  // Calculate start and end dates for the month view grid (including padding days)
  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  const startDayOfWeek = firstDayOfMonth.getDay(); // 0 (Sun) to 6 (Sat)
  const daysInMonth = lastDayOfMonth.getDate();

  // Grid start (Sunday before or on 1st)
  const gridStartDate = new Date(year, month, 1 - startDayOfWeek);
  // Grid end (Saturday after or on last day)
  const endDayOfWeek = lastDayOfMonth.getDay();
  const gridEndDate = new Date(year, month + 1, 6 - endDayOfWeek);

  const formatDateISO = (d: Date) => d.toISOString().split("T")[0];

  const startDateStr = formatDateISO(gridStartDate);
  const endDateStr = formatDateISO(gridEndDate);

  // Query events
  const { data: scheduleData, isLoading } = useQuery({
    queryKey: ["calendar", startDateStr, endDateStr, typeFilter],
    queryFn: () =>
      calendarService.getSchedule({
        start_date: startDateStr,
        end_date: endDateStr,
        event_types: typeFilter ? [typeFilter as CalendarEventType] : undefined,
      }),
  });

  const events = scheduleData?.events || [];

  // Month navigation handlers
  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const handleToday = () => {
    const now = new Date();
    setCurrentDate(now);
    setSelectedDateStr(formatDateISO(now));
  };

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Generate grid days
  const gridDays: { dateStr: string; dayNumber: number; isCurrentMonth: boolean; isToday: boolean }[] = [];
  const cur = new Date(gridStartDate);
  const todayStr = formatDateISO(new Date());

  while (cur <= gridEndDate) {
    const curStr = formatDateISO(cur);
    gridDays.push({
      dateStr: curStr,
      dayNumber: cur.getDate(),
      isCurrentMonth: cur.getMonth() === month,
      isToday: curStr === todayStr,
    });
    cur.setDate(cur.getDate() + 1);
  }

  // Selected date events
  const selectedDayEvents = events.filter((e) => e.date === selectedDateStr);

  const getEventBadgeClass = (color?: string | null) => {
    switch (color) {
      case "blue":
        return "bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200";
      case "amber":
        return "bg-amber-100 text-amber-800 border-amber-200 hover:bg-amber-200";
      case "emerald":
        return "bg-emerald-100 text-emerald-800 border-emerald-200 hover:bg-emerald-200";
      case "purple":
        return "bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200 hover:bg-slate-200";
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Career Calendar"
        subtitle="Unified schedule aggregating upcoming interviews, task deadlines, follow-ups, and recruiter calls."
        actions={
          <div className="flex items-center gap-3">
            <Link to="/tasks">
              <Button variant="primary">
                <Plus className="w-4 h-4 mr-1.5" /> Add Task
              </Button>
            </Link>
          </div>
        }
      />

      {/* Legend & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-3 rounded-xl border border-slate-200 text-xs">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="font-semibold text-slate-600">Event Key:</span>
          <span className="flex items-center gap-1.5 text-blue-700 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Interviews
          </span>
          <span className="flex items-center gap-1.5 text-amber-700 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Tasks
          </span>
          <span className="flex items-center gap-1.5 text-emerald-700 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Follow-ups
          </span>
          <span className="flex items-center gap-1.5 text-purple-700 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Deadlines
          </span>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2.5 py-1 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
          >
            <option value="">All Event Types</option>
            <option value="INTERVIEW">Interviews Only</option>
            <option value="TASK">Tasks Only</option>
            <option value="FOLLOW_UP">Follow-ups Only</option>
            <option value="DEADLINE">Deadlines Only</option>
          </select>

          <Button variant="outline" size="sm" onClick={handleToday}>
            Today
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Grid View */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-4">
            {/* Calendar Controls */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-slate-900">
                {monthNames[month]} {year}
              </h3>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrevMonth}
                  aria-label="Previous month"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNextMonth}
                  aria-label="Next month"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Days of week header */}
            <div className="grid grid-cols-7 gap-1 text-center font-semibold text-xs text-slate-500 mb-2">
              {daysOfWeek.map((d) => (
                <div key={d} className="py-1">
                  {d}
                </div>
              ))}
            </div>

            {/* Calendar Cells Grid */}
            <div className="grid grid-cols-7 gap-1">
              {gridDays.map((cell) => {
                const dayEvents = events.filter((e) => e.date === cell.dateStr);
                const isSelected = cell.dateStr === selectedDateStr;

                return (
                  <div
                    key={cell.dateStr}
                    onClick={() => setSelectedDateStr(cell.dateStr)}
                    className={`min-h-[88px] p-1.5 rounded-lg border text-left cursor-pointer transition-all ${
                      isSelected
                        ? "border-blue-600 bg-blue-50/40 shadow-sm"
                        : cell.isToday
                        ? "border-blue-300 bg-blue-50/15"
                        : cell.isCurrentMonth
                        ? "border-slate-100 bg-white hover:bg-slate-50"
                        : "border-slate-50 bg-slate-50/40 text-slate-300"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span
                        className={`text-xs font-semibold ${
                          cell.isToday
                            ? "w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold"
                            : cell.isCurrentMonth
                            ? "text-slate-700"
                            : "text-slate-400"
                        }`}
                      >
                        {cell.dayNumber}
                      </span>
                      {dayEvents.length > 0 && (
                        <span className="text-[10px] text-slate-400 font-medium">
                          {dayEvents.length}
                        </span>
                      )}
                    </div>

                    <div className="space-y-1">
                      {dayEvents.slice(0, 3).map((ev) => (
                        <div
                          key={ev.id}
                          className={`text-[10px] px-1.5 py-0.5 rounded font-medium truncate border ${getEventBadgeClass(
                            ev.color
                          )}`}
                          title={ev.title}
                        >
                          {ev.title}
                        </div>
                      ))}
                      {dayEvents.length > 3 && (
                        <div className="text-[9px] text-slate-500 font-semibold pl-1">
                          +{dayEvents.length - 3} more
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Selected Day Agenda Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-sm flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4 text-blue-600" />
                  Agenda: {selectedDateStr}
                </span>
                <span className="text-xs text-slate-500 font-normal">
                  {selectedDayEvents.length} event{selectedDayEvents.length !== 1 ? "s" : ""}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {isLoading ? (
                <div className="text-center py-8 text-xs text-slate-500">
                  Loading schedule...
                </div>
              ) : selectedDayEvents.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">
                  No events scheduled for this day.
                </div>
              ) : (
                selectedDayEvents.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2 hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              ev.color === "blue"
                                ? "bg-blue-500"
                                : ev.color === "amber"
                                ? "bg-amber-500"
                                : ev.color === "emerald"
                                ? "bg-emerald-500"
                                : "bg-purple-500"
                            }`}
                          />
                          <span className="text-xs font-semibold text-slate-900">
                            {ev.title}
                          </span>
                        </div>
                        {ev.description && (
                          <p className="text-xs text-slate-600 line-clamp-2">
                            {ev.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 text-xs text-slate-500">
                      <span>{ev.status || ev.event_type}</span>
                      <div className="flex items-center gap-2">
                        {ev.meeting_link && (
                          <a
                            href={ev.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-blue-600 hover:underline font-medium"
                          >
                            <Video className="w-3.5 h-3.5" /> Join
                          </a>
                        )}

                        {ev.event_type === "INTERVIEW" && ev.related_id && (
                          <Link
                            to={`/interviews/${ev.related_id}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <ExternalLink className="w-3.5 h-3.5" /> Details
                          </Link>
                        )}

                        {(ev.event_type === "DEADLINE" || ev.event_type === "FOLLOW_UP") && ev.related_id && (
                          <Link
                            to={`/applications/${ev.related_id}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <ExternalLink className="w-3.5 h-3.5" /> Application
                          </Link>
                        )}

                        {ev.event_type === "TASK" && (
                          <Link
                            to="/tasks"
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <CheckSquare className="w-3.5 h-3.5" /> View Tasks
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
