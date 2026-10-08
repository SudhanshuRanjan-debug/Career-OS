import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { taskService } from "@/services/taskService";
import { applicationService } from "@/services/applicationService";
import { interviewService } from "@/services/interviewService";
import { contactService } from "@/services/contactService";
import type { Company } from "@/types/contact.types";
import type {
  Task,
  TaskCreateInput,
  TaskPriority,
  TaskRelatedType,
  TaskStatus,
  TaskUpdateInput,
} from "@/types/task.types";
import {
  CheckSquare,
  Plus,
  Calendar,
  Clock,
  Briefcase,
  Building2,
  Users,
  CheckCircle2,
  Circle,
  Search,
  Filter,
  Edit2,
  Trash2,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

export const TasksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filterMode, setFilterMode] = useState<"all" | "today" | "upcoming" | "completed">("all");
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [relatedTypeFilter, setRelatedTypeFilter] = useState<string>("");

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deletingTask, setDeletingTask] = useState<Task | null>(null);

  // Form states
  const [formData, setFormData] = useState<TaskCreateInput>({
    title: "",
    description: "",
    due_date: "",
    priority: "MEDIUM",
    status: "PENDING",
    related_type: "GENERAL",
    application_id: "",
    interview_id: "",
    company_id: "",
    contact_id: "",
  });

  // Query tasks
  const { data: taskData, isLoading } = useQuery({
    queryKey: ["tasks", filterMode, search, priorityFilter, relatedTypeFilter],
    queryFn: () =>
      taskService.listTasks({
        filter: filterMode,
        search: search.trim() || undefined,
        priority: (priorityFilter as TaskPriority) || undefined,
        related_type: (relatedTypeFilter as TaskRelatedType) || undefined,
      }),
  });

  // Supporting queries for polymorphic linking
  const { data: applicationsData } = useQuery({
    queryKey: ["applications-options"],
    queryFn: () => applicationService.listApplications({ page_size: 100 }),
    enabled: isAddModalOpen || editingTask !== null,
  });

  const { data: interviewsData } = useQuery({
    queryKey: ["interviews-options"],
    queryFn: () => interviewService.listInterviews({ page_size: 100 }),
    enabled: isAddModalOpen || editingTask !== null,
  });

  const { data: companiesData } = useQuery({
    queryKey: ["companies-options"],
    queryFn: () => contactService.listCompanies({ page_size: 100 }),
    enabled: isAddModalOpen || editingTask !== null,
  });

  const { data: contactsData } = useQuery({
    queryKey: ["contacts-options"],
    queryFn: () => contactService.listContacts({ page_size: 100 }),
    enabled: isAddModalOpen || editingTask !== null,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: TaskCreateInput) => taskService.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setIsAddModalOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdateInput }) =>
      taskService.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setEditingTask(null);
    },
  });

  const completeMutation = useMutation({
    mutationFn: (id: string) => taskService.completeTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => taskService.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setDeletingTask(null);
    },
  });

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      due_date: "",
      priority: "MEDIUM",
      status: "PENDING",
      related_type: "GENERAL",
      application_id: "",
      interview_id: "",
      company_id: "",
      contact_id: "",
    });
  };

  const handleToggleTask = (task: Task) => {
    if (task.is_completed) {
      // Reopen
      updateMutation.mutate({
        id: task.id,
        data: { status: "PENDING", is_completed: false },
      });
    } else {
      // Deterministic complete
      completeMutation.mutate(task.id);
    }
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    const payload: TaskCreateInput = {
      title: formData.title.trim(),
      description: formData.description?.trim() || undefined,
      due_date: formData.due_date || undefined,
      priority: formData.priority,
      status: formData.status,
      related_type: formData.related_type,
    };

    if (formData.related_type === "APPLICATION" && formData.application_id) {
      payload.application_id = formData.application_id;
    } else if (formData.related_type === "INTERVIEW" && formData.interview_id) {
      payload.interview_id = formData.interview_id;
    } else if (formData.related_type === "COMPANY" && formData.company_id) {
      payload.company_id = formData.company_id;
    } else if (formData.related_type === "CONTACT" && formData.contact_id) {
      payload.contact_id = formData.contact_id;
    }

    createMutation.mutate(payload);
  };

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTask || !editingTask.title.trim()) return;

    updateMutation.mutate({
      id: editingTask.id,
      data: {
        title: editingTask.title.trim(),
        description: editingTask.description?.trim() || undefined,
        due_date: editingTask.due_date || undefined,
        priority: editingTask.priority,
        status: editingTask.status,
      },
    });
  };

  const tasks = taskData?.items || [];
  const todayStr = new Date().toISOString().split("T")[0];

  const getPriorityBadgeVariant = (priority: TaskPriority) => {
    switch (priority) {
      case "URGENT":
        return "danger";
      case "HIGH":
        return "warning";
      case "MEDIUM":
        return "info";
      default:
        return "neutral";
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks & Follow-ups"
        subtitle="Manage actionable items across applications, interviews, contacts, and career milestones."
        actions={
          <Button
            variant="primary"
            onClick={() => {
              resetForm();
              setIsAddModalOpen(true);
            }}
          >
            <Plus className="w-4 h-4 mr-1.5" /> Add Task
          </Button>
        }
      />

      {/* Tabs and Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-6">
          <button
            onClick={() => setFilterMode("all")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 -mb-3 ${
              filterMode === "all"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            All Tasks
          </button>
          <button
            onClick={() => setFilterMode("today")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 -mb-3 ${
              filterMode === "today"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Due Today
          </button>
          <button
            onClick={() => setFilterMode("upcoming")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 -mb-3 ${
              filterMode === "upcoming"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Upcoming
          </button>
          <button
            onClick={() => setFilterMode("completed")}
            className={`pb-3 text-sm font-semibold transition-colors border-b-2 -mb-3 ${
              filterMode === "completed"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Completed
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative w-48 sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
          >
            <option value="">All Priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>

          <select
            value={relatedTypeFilter}
            onChange={(e) => setRelatedTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
          >
            <option value="">All Types</option>
            <option value="GENERAL">General</option>
            <option value="APPLICATION">Application</option>
            <option value="INTERVIEW">Interview</option>
            <option value="COMPANY">Company</option>
            <option value="CONTACT">Contact</option>
          </select>
        </div>
      </div>

      {/* Task List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12 text-sm text-slate-500">Loading tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
            <CheckSquare className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-800">No tasks found</h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">
              {search || priorityFilter || relatedTypeFilter
                ? "No tasks match your selected filters."
                : "You don't have any tasks in this view. Keep your momentum going by creating one."}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                resetForm();
                setIsAddModalOpen(true);
              }}
            >
              <Plus className="w-4 h-4 mr-1" /> Add a Task
            </Button>
          </div>
        ) : (
          tasks.map((task) => {
            const isOverdue =
              task.due_date && task.due_date < todayStr && !task.is_completed;

            return (
              <Card
                key={task.id}
                className={`p-4 transition-all hover:border-slate-300 ${
                  task.is_completed ? "bg-slate-50/60 opacity-80" : "bg-white"
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <button
                      onClick={() => handleToggleTask(task)}
                      className="mt-0.5 text-slate-400 hover:text-blue-600 transition-colors flex-shrink-0"
                      aria-label="Toggle completion"
                    >
                      {task.is_completed ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-300 hover:text-blue-500" />
                      )}
                    </button>

                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`text-sm font-semibold ${
                            task.is_completed
                              ? "line-through text-slate-400"
                              : "text-slate-900"
                          }`}
                        >
                          {task.title}
                        </span>
                        <Badge variant={getPriorityBadgeVariant(task.priority)}>
                          {task.priority}
                        </Badge>
                        {task.status !== "PENDING" && task.status !== "COMPLETED" && (
                          <Badge variant="neutral">{task.status}</Badge>
                        )}
                      </div>

                      {task.description && (
                        <p className="text-xs text-slate-600 whitespace-pre-line">
                          {task.description}
                        </p>
                      )}

                      <div className="flex items-center gap-4 text-xs text-slate-500 pt-1 flex-wrap">
                        {task.due_date && (
                          <span
                            className={`flex items-center gap-1 font-medium ${
                              isOverdue ? "text-red-600" : "text-slate-600"
                            }`}
                          >
                            <Calendar className="w-3.5 h-3.5" />
                            {task.due_date}
                            {isOverdue && " (Overdue)"}
                          </span>
                        )}

                        {/* Polymorphic entity links */}
                        {task.application && (
                          <Link
                            to={`/applications/${task.application_id}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <Briefcase className="w-3.5 h-3.5" />
                            {task.application.company_name} • {task.application.job_title}
                          </Link>
                        )}

                        {task.interview && (
                          <Link
                            to={`/interviews/${task.interview_id}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <Calendar className="w-3.5 h-3.5" />
                            Interview: {task.interview.stage || task.interview.interview_type}
                          </Link>
                        )}

                        {task.company && (
                          <Link
                            to={`/companies/${task.company_id}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <Building2 className="w-3.5 h-3.5" />
                            {task.company.name}
                          </Link>
                        )}

                        {task.contact && (
                          <Link
                            to={`/network/${task.contact_id}`}
                            className="flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <Users className="w-3.5 h-3.5" />
                            {task.contact.first_name} {task.contact.last_name || ""}
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={() => setEditingTask(task)}
                      className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                      title="Edit task"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setDeletingTask(task)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete task"
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

      {/* Add Task Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Task"
        description="Create an action item and optionally associate it with an application, interview, company, or contact."
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Follow up with recruiter on technical round"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Description
            </label>
            <textarea
              rows={2}
              placeholder="Add extra context or notes..."
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Due Date
              </label>
              <input
                type="date"
                value={formData.due_date || ""}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as TaskPriority })}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>

          {/* Polymorphic Linking Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Related Category
            </label>
            <select
              value={formData.related_type}
              onChange={(e) => {
                const nextType = e.target.value as TaskRelatedType;
                setFormData({
                  ...formData,
                  related_type: nextType,
                  application_id: "",
                  interview_id: "",
                  company_id: "",
                  contact_id: "",
                });
              }}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="GENERAL">General (No Entity Link)</option>
              <option value="APPLICATION">Job Application</option>
              <option value="INTERVIEW">Interview Round</option>
              <option value="COMPANY">Target Company</option>
              <option value="CONTACT">Contact / Recruiter</option>
            </select>
          </div>

          {formData.related_type === "APPLICATION" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select Application <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.application_id || ""}
                onChange={(e) => setFormData({ ...formData, application_id: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose Application --</option>
                {applicationsData?.items?.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.company_name} • {app.job_title}
                  </option>
                ))}
              </select>
            </div>
          )}

          {formData.related_type === "INTERVIEW" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select Interview <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.interview_id || ""}
                onChange={(e) => setFormData({ ...formData, interview_id: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose Interview Round --</option>
                {interviewsData?.items?.map((int) => (
                  <option key={int.id} value={int.id}>
                    {int.application?.company_name || "Interview"}: {int.round_name || int.interview_type}
                  </option>
                ))}
              </select>
            </div>
          )}

          {formData.related_type === "COMPANY" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select Company <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.company_id || ""}
                onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose Target Company --</option>
                {companiesData?.items?.map((comp: Company) => (
                  <option key={comp.id} value={comp.id}>
                    {comp.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {formData.related_type === "CONTACT" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select Contact <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.contact_id || ""}
                onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose Contact --</option>
                {contactsData?.items?.map((cont) => (
                  <option key={cont.id} value={cont.id}>
                    {cont.first_name} {cont.last_name || ""} ({cont.role || cont.contact_type || "Contact"})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Saving..." : "Create Task"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Task Modal */}
      {editingTask && (
        <Modal
          isOpen={true}
          onClose={() => setEditingTask(null)}
          title="Edit Task"
        >
          <form onSubmit={handleUpdateSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Title
              </label>
              <input
                type="text"
                required
                value={editingTask.title}
                onChange={(e) =>
                  setEditingTask({ ...editingTask, title: e.target.value })
                }
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Description
              </label>
              <textarea
                rows={2}
                value={editingTask.description || ""}
                onChange={(e) =>
                  setEditingTask({ ...editingTask, description: e.target.value })
                }
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  value={editingTask.due_date || ""}
                  onChange={(e) =>
                    setEditingTask({ ...editingTask, due_date: e.target.value })
                  }
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Priority
                </label>
                <select
                  value={editingTask.priority}
                  onChange={(e) =>
                    setEditingTask({
                      ...editingTask,
                      priority: e.target.value as TaskPriority,
                    })
                  }
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Status
              </label>
              <select
                value={editingTask.status}
                onChange={(e) =>
                  setEditingTask({
                    ...editingTask,
                    status: e.target.value as TaskStatus,
                  })
                }
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="PENDING">Pending</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditingTask(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {deletingTask && (
        <Modal
          isOpen={true}
          onClose={() => setDeletingTask(null)}
          title="Delete Task"
        >
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Are you sure you want to delete task{" "}
              <strong className="text-slate-900">"{deletingTask.title}"</strong>?
              This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => setDeletingTask(null)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={() => deleteMutation.mutate(deletingTask.id)}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
