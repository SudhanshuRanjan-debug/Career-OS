/**
 * Settings Hub Page.
 * Stage 9: Analytics & Settings.
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import {
  User,
  Shield,
  Bell,
  Lock,
  Laptop,
  Database,
  Palette,
  Trash2,
  CheckCircle2,
  Download,
  AlertCircle,
  Clock,
  RefreshCw,
} from "lucide-react";
import { settingsService } from "@/services/settingsService";
import { useAuthStore } from "@/store/authStore";

export const SettingsHubPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const clearAuth = useAuthStore((state) => state.clearAuth);

  const [activeTab, setActiveTab] = useState<
    "general" | "security" | "notifications" | "privacy" | "sessions" | "data" | "appearance" | "delete"
  >("general");

  // Status feedback states
  const [accountSuccess, setAccountSuccess] = useState<string | null>(null);
  const [accountError, setAccountError] = useState<string | null>(null);

  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [notifSuccess, setNotifSuccess] = useState<string | null>(null);
  const [notifError, setNotifError] = useState<string | null>(null);

  const [exportLoading, setExportLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Form states
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Queries
  const { data: account, isLoading: accountLoading } = useQuery({
    queryKey: ["settings-account"],
    queryFn: () => settingsService.getAccount(),
  });

  const { data: notifications, isLoading: notifLoading } = useQuery({
    queryKey: ["settings-notifications"],
    queryFn: () => settingsService.getNotificationSettings(),
  });

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ["settings-sessions"],
    queryFn: () => settingsService.getSessions(),
  });

  // Local notification toggles initialized when query loads
  const [inAppAlerts, setInAppAlerts] = useState(true);
  const [interviewReminders, setInterviewReminders] = useState(true);
  const [deadlineReminders, setDeadlineReminders] = useState(true);
  const [taskReminders, setTaskReminders] = useState(true);

  useEffect(() => {
    if (account) {
      setUsername(account.username || "");
      setEmail(account.email || "");
    }
  }, [account]);

  useEffect(() => {
    if (notifications) {
      setInAppAlerts(notifications.in_app_alerts);
      setInterviewReminders(notifications.interview_reminders);
      setDeadlineReminders(notifications.deadline_reminders);
      setTaskReminders(notifications.task_reminders);
    }
  }, [notifications]);

  // Mutations
  const updateAccountMutation = useMutation({
    mutationFn: () => settingsService.updateAccount({ username, email }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["settings-account"], updated);
      setAccountSuccess("Account details updated successfully.");
      setAccountError(null);
      setTimeout(() => setAccountSuccess(null), 4000);
    },
    onError: (err: any) => {
      setAccountError(err.response?.data?.detail || "Failed to update account details.");
      setAccountSuccess(null);
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: () => settingsService.changePassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      setPasswordSuccess("Password successfully changed.");
      setPasswordError(null);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setPasswordSuccess(null), 4000);
      queryClient.invalidateQueries({ queryKey: ["settings-sessions"] });
    },
    onError: (err: any) => {
      setPasswordError(err.response?.data?.detail || "Failed to change password.");
      setPasswordSuccess(null);
    },
  });

  const updateNotifMutation = useMutation({
    mutationFn: () =>
      settingsService.updateNotificationSettings({
        in_app_alerts: inAppAlerts,
        interview_reminders: interviewReminders,
        deadline_reminders: deadlineReminders,
        task_reminders: taskReminders,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["settings-notifications"], updated);
      setNotifSuccess("Notification preferences saved.");
      setNotifError(null);
      setTimeout(() => setNotifSuccess(null), 4000);
    },
    onError: (err: any) => {
      setNotifError(err.response?.data?.detail || "Failed to save preferences.");
      setNotifSuccess(null);
    },
  });

  const revokeSessionMutation = useMutation({
    mutationFn: (id: string) => settingsService.revokeSession(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings-sessions"] });
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => settingsService.deleteAccount({ password: deletePassword }),
    onSuccess: () => {
      clearAuth();
      navigate("/login");
    },
    onError: (err: any) => {
      setDeleteError(err.response?.data?.detail || "Failed to delete account. Verify your password.");
    },
  });

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New password confirmation does not match.");
      return;
    }
    changePasswordMutation.mutate();
  };

  const handleExportData = async () => {
    try {
      setExportLoading(true);
      const exportBundle = await settingsService.exportData();
      const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
        JSON.stringify(exportBundle, null, 2)
      )}`;
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", jsonString);
      downloadAnchor.setAttribute(
        "download",
        `career_os_export_${new Date().toISOString().slice(0, 10)}.json`
      );
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch {
      alert("Failed to export Career OS data bundle.");
    } finally {
      setExportLoading(false);
    }
  };

  const tabs = [
    { id: "general", label: "General & Account", icon: User },
    { id: "security", label: "Security & Passwords", icon: Shield },
    { id: "notifications", label: "In-App Alerts", icon: Bell },
    { id: "privacy", label: "Privacy & Data Visibility", icon: Lock },
    { id: "sessions", label: "Active Sessions", icon: Laptop },
    { id: "data", label: "Data Export (GDPR)", icon: Database },
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "delete", label: "Delete Account", icon: Trash2, danger: true },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Platform Settings"
        description="Manage your account profile, authentication credentials, active device sessions, and privacy preferences."
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                  isActive
                    ? tab.danger
                      ? "bg-rose-50 text-rose-700 font-semibold"
                      : "bg-blue-50 text-blue-700 font-semibold"
                    : tab.danger
                    ? "text-rose-600 hover:bg-rose-50/60"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    isActive
                      ? tab.danger
                        ? "text-rose-600"
                        : "text-blue-600"
                      : tab.danger
                      ? "text-rose-500"
                      : "text-slate-400"
                  }`}
                />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panel */}
        <div className="md:col-span-3">
          {/* GENERAL & ACCOUNT */}
          {activeTab === "general" && (
            <Card>
              <CardHeader>
                <CardTitle>Account Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {accountSuccess && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>{accountSuccess}</span>
                  </div>
                )}
                {accountError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                    <span>{accountError}</span>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Username
                    </label>
                    <Input
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="e.g. jdoe_engineer"
                    />
                    <span className="text-[11px] text-slate-400">
                      Must be 3-50 characters.
                    </span>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Account Email
                    </label>
                    <Input
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      type="email"
                      placeholder="name@example.com"
                    />
                    <span className="text-[11px] text-slate-400">
                      Used for platform authentication and security notices.
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 space-y-1">
                  <div className="flex items-center justify-between">
                    <span>Account Status:</span>
                    <Badge variant={account?.is_active ? "success" : "neutral"}>
                      {account?.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Created:</span>
                    <span className="font-medium text-slate-800">
                      {account?.created_at ? new Date(account.created_at).toLocaleDateString() : "-"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Last Login:</span>
                    <span className="font-medium text-slate-800">
                      {account?.last_login_at
                        ? new Date(account.last_login_at).toLocaleString()
                        : "Current Session"}
                    </span>
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    variant="primary"
                    onClick={() => updateAccountMutation.mutate()}
                    isLoading={updateAccountMutation.isPending}
                  >
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* SECURITY & PASSWORDS */}
          {activeTab === "security" && (
            <Card>
              <CardHeader>
                <CardTitle>Security & Password Management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {passwordSuccess && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>{passwordSuccess}</span>
                  </div>
                )}
                {passwordError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                    <span>{passwordError}</span>
                  </div>
                )}

                <form onSubmit={handlePasswordSubmit} className="max-w-md space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Current Password
                    </label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      New Password
                    </label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                    />
                    <span className="text-[11px] text-slate-400">
                      Minimum 8 characters with letters, numbers, and symbols.
                    </span>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Confirm New Password
                    </label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="pt-2">
                    <Button
                      type="submit"
                      variant="primary"
                      isLoading={changePasswordMutation.isPending}
                    >
                      Update Password
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* NOTIFICATION PREFERENCES */}
          {activeTab === "notifications" && (
            <Card>
              <CardHeader>
                <CardTitle>In-App Notification Preferences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {notifSuccess && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>{notifSuccess}</span>
                  </div>
                )}
                {notifError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                    <span>{notifError}</span>
                  </div>
                )}

                <div className="space-y-3">
                  <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-50 transition-colors">
                    <div>
                      <span className="font-semibold text-sm text-slate-900 block">
                        Platform In-App Alerts
                      </span>
                      <span className="text-xs text-slate-500">
                        Enable or disable real-time in-app toasts and banner alerts.
                      </span>
                    </div>
                    <input
                      type="checkbox"
                      checked={inAppAlerts}
                      onChange={(e) => setInAppAlerts(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-50 transition-colors">
                    <div>
                      <span className="font-semibold text-sm text-slate-900 block">
                        Interview Schedule Reminders
                      </span>
                      <span className="text-xs text-slate-500">
                        Receive 24-hour and 1-hour notifications before scheduled rounds.
                      </span>
                    </div>
                    <input
                      type="checkbox"
                      checked={interviewReminders}
                      onChange={(e) => setInterviewReminders(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-50 transition-colors">
                    <div>
                      <span className="font-semibold text-sm text-slate-900 block">
                        Application Deadline Reminders
                      </span>
                      <span className="text-xs text-slate-500">
                        Notify when saved opportunity target deadlines are approaching.
                      </span>
                    </div>
                    <input
                      type="checkbox"
                      checked={deadlineReminders}
                      onChange={(e) => setDeadlineReminders(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-50 transition-colors">
                    <div>
                      <span className="font-semibold text-sm text-slate-900 block">
                        Tasks Due Reminders
                      </span>
                      <span className="text-xs text-slate-500">
                        Notify for actionable tasks and interview preparation items due today.
                      </span>
                    </div>
                    <input
                      type="checkbox"
                      checked={taskReminders}
                      onChange={(e) => setTaskReminders(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                  </label>
                </div>

                <div className="pt-2">
                  <Button
                    variant="primary"
                    onClick={() => updateNotifMutation.mutate()}
                    isLoading={updateNotifMutation.isPending}
                  >
                    Save Preferences
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* PRIVACY & DATA VISIBILITY */}
          {activeTab === "privacy" && (
            <Card>
              <CardHeader>
                <CardTitle>Privacy & Data Security</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-slate-700">
                <div className="p-3.5 bg-blue-50/60 rounded-lg border border-blue-100 flex items-start gap-3">
                  <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <h4 className="text-xs font-semibold text-blue-900">Tenant-Scoped Isolation</h4>
                    <p className="text-xs text-blue-800 leading-relaxed">
                      Every database query, document storage upload, and analytics aggregation is strictly filtered by your authenticated user ID. No cross-tenant access is ever permitted.
                    </p>
                  </div>
                </div>

                <div className="space-y-2 text-xs text-slate-600">
                  <p>
                    • <strong>Zero Third-Party Trackers:</strong> Career OS contains no Google Analytics, Mixpanel, Amplitude, Segment, or ad networks.
                  </p>
                  <p>
                    • <strong>Local Processing:</strong> All metrics, conversion funnels, and progression velocity calculations are deterministic relational queries executed on your local database.
                  </p>
                  <p>
                    • <strong>Zero Automated Scraping:</strong> Your candidate data is strictly private and never submitted to unauthorized external aggregators.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ACTIVE SESSIONS */}
          {activeTab === "sessions" && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Active User Sessions</CardTitle>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Devices and browser sessions currently logged into your Career OS account.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ["settings-sessions"] })}
                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                >
                  Refresh
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                {sessionsLoading ? (
                  <div className="p-6 text-center text-xs text-slate-500">Loading sessions...</div>
                ) : !sessions || sessions.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500">No active sessions found.</div>
                ) : (
                  sessions.map((sess) => (
                    <div
                      key={sess.id}
                      className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-sm"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Laptop className="w-4 h-4 text-slate-500" />
                          <span className="font-semibold text-slate-900 text-xs">
                            {sess.user_agent ? sess.user_agent.slice(0, 48) : "Active Device"}
                          </span>
                          {sess.is_current && <Badge variant="success">Current Session</Badge>}
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-3">
                          <span>IP: {sess.ip_address || "127.0.0.1"}</span>
                          <span>Started: {new Date(sess.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      {!sess.is_current && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => revokeSessionMutation.mutate(sess.id)}
                          isLoading={revokeSessionMutation.isPending}
                        >
                          Revoke
                        </Button>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          )}

          {/* DATA EXPORT */}
          {activeTab === "data" && (
            <Card>
              <CardHeader>
                <CardTitle>GDPR Data Export</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-slate-600 leading-relaxed">
                  Under data protection and GDPR guidelines, you can download a complete structured JSON copy of all personal records, job applications, stage history, interviews, notes, contacts, companies, and candidate preferences stored in Career OS.
                </p>
                <div className="pt-2">
                  <Button
                    variant="outline"
                    onClick={handleExportData}
                    isLoading={exportLoading}
                    leftIcon={<Download className="w-4 h-4" />}
                  >
                    Export All Data (.json)
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* APPEARANCE */}
          {activeTab === "appearance" && (
            <Card>
              <CardHeader>
                <CardTitle>Appearance & Theme</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-4">
                  <div className="p-3 border-2 border-blue-600 rounded-xl bg-white text-slate-900 text-xs font-semibold cursor-pointer">
                    Light Theme (Active)
                  </div>
                  <div className="p-3 border border-slate-200 rounded-xl bg-slate-900 text-white text-xs font-semibold opacity-60 cursor-not-allowed">
                    Dark Theme (Future Roadmap)
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* DELETE ACCOUNT */}
          {activeTab === "delete" && (
            <Card className="border-rose-200 bg-rose-50/20">
              <CardHeader>
                <CardTitle className="text-rose-700">Delete Account & Purge Data</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-slate-700 leading-relaxed">
                  Permanently delete your account, authentication tokens, uploaded resumes, private documents, application pipeline, and historical notes. This action is immediate and irreversible.
                </p>
                <Button
                  variant="danger"
                  onClick={() => setDeleteModalOpen(true)}
                  leftIcon={<Trash2 className="w-4 h-4" />}
                >
                  Delete My Account
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setDeletePassword("");
          setDeleteError(null);
        }}
        title="Confirm Account Deletion"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600">
            Please enter your account password to confirm permanent deletion of all Career OS data.
          </p>

          {deleteError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{deleteError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Account Password
            </label>
            <Input
              type="password"
              placeholder="••••••••"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setDeleteModalOpen(false);
                setDeletePassword("");
                setDeleteError(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => deleteAccountMutation.mutate()}
              isLoading={deleteAccountMutation.isPending}
              disabled={!deletePassword}
            >
              Permanently Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
