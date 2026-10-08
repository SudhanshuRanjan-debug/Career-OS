import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { notificationService } from "@/services/notificationService";
import type { Notification, NotificationType } from "@/types/notification.types";
import {
  Bell,
  CheckCheck,
  CalendarCheck,
  Clock,
  Briefcase,
  AlertTriangle,
  User,
  CheckSquare,
  Trash2,
  ExternalLink,
  Calendar,
} from "lucide-react";

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ["notifications", filter],
    queryFn: () =>
      notificationService.listNotifications({
        is_read: filter === "unread" ? false : undefined,
      }),
  });

  const { data: unreadData } = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: () => notificationService.getUnreadCount(),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationService.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => notificationService.deleteNotification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const notifications = notificationsData?.items || [];
  const unreadCount = unreadData?.unread_count ?? 0;

  const getNotificationIcon = (type: NotificationType) => {
    switch (type) {
      case "INTERVIEW_REMINDER":
        return <CalendarCheck className="w-5 h-5 text-blue-600" />;
      case "TASK_DUE":
        return <CheckSquare className="w-5 h-5 text-amber-600" />;
      case "FOLLOW_UP_DUE":
        return <Clock className="w-5 h-5 text-emerald-600" />;
      case "DEADLINE":
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default:
        return <Bell className="w-5 h-5 text-indigo-600" />;
    }
  };

  const getTargetUrl = (notif: Notification) => {
    if (!notif.related_id) {
      if (notif.related_type === "TASK") return "/tasks";
      return null;
    }
    if (notif.related_type === "INTERVIEW") {
      return `/interviews/${notif.related_id}`;
    }
    if (notif.related_type === "APPLICATION") {
      return `/applications/${notif.related_id}`;
    }
    if (notif.related_type === "TASK") {
      return "/tasks";
    }
    return null;
  };

  const formatTimestamp = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications"
        subtitle="Real-time alerts, upcoming interview reminders, follow-up pings, and milestone updates."
        actions={
          <Button
            variant="outline"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || unreadCount === 0}
          >
            <CheckCheck className="w-4 h-4 mr-1.5" /> Mark All as Read
          </Button>
        }
      />

      {/* Filter Tabs */}
      <div className="flex items-center gap-6 border-b border-slate-200">
        <button
          onClick={() => setFilter("all")}
          className={`pb-3 text-sm font-semibold transition-colors border-b-2 ${
            filter === "all"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          All Notifications
        </button>
        <button
          onClick={() => setFilter("unread")}
          className={`pb-3 text-sm font-semibold transition-colors border-b-2 ${
            filter === "unread"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Unread ({unreadCount})
        </button>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12 text-sm text-slate-500">
            Loading notifications...
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 text-slate-500 text-sm">
            <Bell className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-800">No notifications</h3>
            <p className="text-xs text-slate-500 mt-1">
              {filter === "unread"
                ? "You have caught up with all your notifications!"
                : "You don't have any notifications right now."}
            </p>
          </div>
        ) : (
          notifications.map((n) => {
            const targetUrl = getTargetUrl(n);

            return (
              <Card
                key={n.id}
                className={`p-4 transition-all hover:border-slate-300 ${
                  !n.is_read
                    ? "border-blue-200 bg-blue-50/20"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="p-2 rounded-lg bg-white border border-slate-100 shadow-xs flex-shrink-0 mt-0.5">
                      {getNotificationIcon(n.notification_type)}
                    </div>

                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-semibold text-sm text-slate-900">
                          {n.title}
                        </h4>
                        <Badge variant={n.is_read ? "neutral" : "info"}>
                          {n.notification_type.replace(/_/g, " ")}
                        </Badge>
                        {!n.is_read && (
                          <span className="w-2 h-2 rounded-full bg-blue-600 inline-block" />
                        )}
                      </div>

                      {n.body && (
                        <p className="text-sm text-slate-600">{n.body}</p>
                      )}

                      <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
                        <span>{formatTimestamp(n.created_at)}</span>

                        {targetUrl && (
                          <Link
                            to={targetUrl}
                            className="flex items-center gap-1 text-blue-600 hover:underline font-medium"
                          >
                            <ExternalLink className="w-3.5 h-3.5" /> View Resource
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 flex-shrink-0">
                    {!n.is_read && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => markReadMutation.mutate(n.id)}
                        disabled={markReadMutation.isPending}
                        title="Mark as read"
                      >
                        Mark Read
                      </Button>
                    )}
                    <button
                      onClick={() => deleteMutation.mutate(n.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete notification"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
};
