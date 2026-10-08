import React, { useEffect, useState } from "react";
import { Plus, FolderGit2, ExternalLink, Github, Trash2, Edit2, Loader2, Calendar } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { profileService } from "@/services/profileService";
import type { ProjectItem, ProjectPayload } from "@/types/profile.types";

export const ProjectsTab: React.FC = () => {
  const [items, setItems] = useState<ProjectItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ProjectItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [form, setForm] = useState({
    name: "",
    role: "",
    tech_stack_str: "",
    url: "",
    repo_url: "",
    project_type: "SIDE_PROJECT",
    start_date: "",
    end_date: "",
    is_ongoing: false,
    description: "",
    achievements: "",
  });

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await profileService.getProjects();
      setItems(data);
    } catch {
      // Error
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreate = () => {
    setEditingItem(null);
    setForm({
      name: "",
      role: "",
      tech_stack_str: "",
      url: "",
      repo_url: "",
      project_type: "SIDE_PROJECT",
      start_date: "",
      end_date: "",
      is_ongoing: false,
      description: "",
      achievements: "",
    });
    setModalOpen(true);
  };

  const openEdit = (item: ProjectItem) => {
    setEditingItem(item);
    setForm({
      name: item.name,
      role: item.role || "",
      tech_stack_str: item.tech_stack ? item.tech_stack.join(", ") : "",
      url: item.url || "",
      repo_url: item.repo_url || "",
      project_type: item.project_type || "SIDE_PROJECT",
      start_date: item.start_date || "",
      end_date: item.end_date || "",
      is_ongoing: item.is_ongoing,
      description: item.description || "",
      achievements: item.achievements || "",
    });
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const tech_stack = form.tech_stack_str
        ? form.tech_stack_str.split(",").map((s) => s.trim()).filter(Boolean)
        : null;

      const payload: ProjectPayload = {
        name: form.name,
        role: form.role || null,
        tech_stack,
        url: form.url || null,
        repo_url: form.repo_url || null,
        project_type: form.project_type || null,
        start_date: form.start_date || null,
        end_date: form.is_ongoing ? null : form.end_date || null,
        is_ongoing: form.is_ongoing,
        description: form.description || null,
        achievements: form.achievements || null,
      };

      if (editingItem) {
        await profileService.updateProject(editingItem.id, payload);
      } else {
        await profileService.createProject(payload);
      }
      setModalOpen(false);
      await loadData();
    } catch {
      // Error
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this project?")) {
      try {
        await profileService.deleteProject(id);
        await loadData();
      } catch {
        // Error
      }
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Projects Portfolio</CardTitle>
          <p className="text-xs text-slate-500">Key engineering projects with repositories, live demos, and tech stacks.</p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openCreate}>
          Add Project
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="py-12 flex justify-center text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
            <FolderGit2 className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">No Projects Added Yet</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Showcase side projects, open-source work, research, or notable client deliveries.
            </p>
            <Button size="sm" variant="outline" className="mt-4" onClick={openCreate}>
              Add Project
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-start justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-purple-100 text-purple-700 rounded-xl mt-0.5 flex-shrink-0">
                    <FolderGit2 className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-semibold text-slate-900">{item.name}</h4>
                      {item.role && <Badge variant="neutral">{item.role}</Badge>}
                      {item.project_type && (
                        <Badge variant="neutral">{item.project_type.replace("_", " ")}</Badge>
                      )}
                      {item.repo_url && (
                        <a
                          href={item.repo_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-500 hover:text-slate-800"
                          title="Repository Link"
                        >
                          <Github className="w-4 h-4 inline" />
                        </a>
                      )}
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                          title="Live Demo"
                        >
                          <ExternalLink className="w-4 h-4 inline" />
                        </a>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{item.start_date || "N/A"} — {item.is_ongoing ? "Ongoing" : item.end_date || "N/A"}</span>
                    </p>
                    {item.description && (
                      <p className="text-xs text-slate-600 pt-1 leading-relaxed">{item.description}</p>
                    )}
                    {item.tech_stack && item.tech_stack.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {item.tech_stack.map((tech) => (
                          <Badge key={tech} variant="neutral">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <Button size="sm" variant="outline" leftIcon={<Edit2 className="w-3.5 h-3.5" />} onClick={() => openEdit(item)}>
                    Edit
                  </Button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-2 text-slate-400 hover:text-red-600 rounded-lg transition-colors"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingItem ? "Edit Project" : "Add Project"}
        description="Share details of applications, libraries, or architectural work you have built."
      >
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label="Project Name"
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="e.g. Distributed Event Pipeline"
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Your Role"
              value={form.role}
              onChange={(e) => setForm((p) => ({ ...p, role: e.target.value }))}
              placeholder="e.g. Lead Architect / Creator"
            />
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Project Type</label>
              <select
                value={form.project_type}
                onChange={(e) => setForm((p) => ({ ...p, project_type: e.target.value }))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="SIDE_PROJECT">Side Project</option>
                <option value="OPEN_SOURCE">Open Source</option>
                <option value="COMMERCIAL">Commercial</option>
                <option value="ACADEMIC">Academic / Research</option>
              </select>
            </div>
            <Input
              label="Repository URL"
              value={form.repo_url}
              onChange={(e) => setForm((p) => ({ ...p, repo_url: e.target.value }))}
              placeholder="https://github.com/..."
            />
            <Input
              label="Live Demo URL"
              value={form.url}
              onChange={(e) => setForm((p) => ({ ...p, url: e.target.value }))}
              placeholder="https://myproject.dev"
            />
            <Input
              label="Start Date"
              type="date"
              value={form.start_date}
              onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))}
            />
            {!form.is_ongoing && (
              <Input
                label="End Date"
                type="date"
                value={form.end_date}
                onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
              />
            )}
          </div>

          <div className="flex items-center space-x-2 pt-1">
            <input
              id="is_ongoing_proj"
              type="checkbox"
              checked={form.is_ongoing}
              onChange={(e) => setForm((p) => ({ ...p, is_ongoing: e.target.checked }))}
              className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="is_ongoing_proj" className="text-sm font-medium text-slate-700 cursor-pointer">
              Active / Ongoing Project
            </label>
          </div>

          <Input
            label="Tech Stack (comma-separated)"
            value={form.tech_stack_str}
            onChange={(e) => setForm((p) => ({ ...p, tech_stack_str: e.target.value }))}
            placeholder="e.g. Python, FastAPI, React, PostgreSQL, Docker"
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Project Description
            </label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              placeholder="What does this project do? What technical challenges did you overcome?"
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSaving}>
              {editingItem ? "Save Changes" : "Create Project"}
            </Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};
