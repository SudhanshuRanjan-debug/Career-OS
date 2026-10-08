import React, { useEffect, useState } from "react";
import { Plus, Building2, Trash2, Edit2, Loader2, Calendar } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { profileService } from "@/services/profileService";
import type { ExperienceItem, ExperiencePayload } from "@/types/profile.types";

export const ExperienceTab: React.FC = () => {
  const [items, setItems] = useState<ExperienceItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ExperienceItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [form, setForm] = useState<ExperiencePayload>({
    company_name: "",
    title: "",
    employment_type: "FULL_TIME",
    location: "",
    location_type: "REMOTE",
    start_date: "",
    end_date: "",
    is_current: false,
    description: "",
    responsibilities: "",
    achievements: "",
  });

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await profileService.getExperiences();
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
      company_name: "",
      title: "",
      employment_type: "FULL_TIME",
      location: "",
      location_type: "REMOTE",
      start_date: "",
      end_date: "",
      is_current: false,
      description: "",
      responsibilities: "",
      achievements: "",
    });
    setModalOpen(true);
  };

  const openEdit = (item: ExperienceItem) => {
    setEditingItem(item);
    setForm({
      company_name: item.company_name,
      title: item.title,
      employment_type: item.employment_type || "FULL_TIME",
      location: item.location || "",
      location_type: item.location_type || "REMOTE",
      start_date: item.start_date || "",
      end_date: item.end_date || "",
      is_current: item.is_current,
      description: item.description || "",
      responsibilities: item.responsibilities || "",
      achievements: item.achievements || "",
    });
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload: ExperiencePayload = {
        company_name: form.company_name,
        title: form.title,
        employment_type: form.employment_type || null,
        location: form.location || null,
        location_type: form.location_type || null,
        start_date: form.start_date || null,
        end_date: form.is_current ? null : form.end_date || null,
        is_current: form.is_current,
        description: form.description || null,
        responsibilities: form.responsibilities || null,
        achievements: form.achievements || null,
      };

      if (editingItem) {
        await profileService.updateExperience(editingItem.id, payload);
      } else {
        await profileService.createExperience(payload);
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
    if (window.confirm("Are you sure you want to delete this experience record?")) {
      try {
        await profileService.deleteExperience(id);
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
          <CardTitle>Work Experience</CardTitle>
          <p className="text-xs text-slate-500">Employment history, roles, responsibilities, and achievements.</p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openCreate}>
          Add Experience
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="py-12 flex justify-center text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
            <Building2 className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">No Work Experience Added</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Add past or current full-time, part-time, internship, or contracting roles.
            </p>
            <Button size="sm" variant="outline" className="mt-4" onClick={openCreate}>
              Add Experience Record
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
                  <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-xl mt-0.5 flex-shrink-0">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-semibold text-slate-900">{item.title}</h4>
                      {item.is_current && <Badge variant="success">Current</Badge>}
                      {item.location_type && <Badge variant="neutral">{item.location_type.replace("_", " ")}</Badge>}
                    </div>
                    <p className="text-xs font-medium text-slate-700">
                      {item.company_name} {item.location ? `• ${item.location}` : ""}
                    </p>
                    <p className="text-xs text-slate-500 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{item.start_date || "N/A"} — {item.is_current ? "Present" : item.end_date || "N/A"}</span>
                    </p>
                    {item.description && (
                      <p className="text-xs text-slate-600 pt-1 leading-relaxed">{item.description}</p>
                    )}
                    {item.achievements && (
                      <div className="pt-1 text-xs text-slate-700">
                        <span className="font-semibold text-slate-800">Key Achievements: </span>
                        <span>{item.achievements}</span>
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
                    title="Delete record"
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
        title={editingItem ? "Edit Experience Record" : "Add Experience Record"}
        description="Detail your role, responsibilities, and achievements at the company."
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Company Name"
              value={form.company_name}
              onChange={(e) => setForm((p) => ({ ...p, company_name: e.target.value }))}
              placeholder="e.g. Acme Corp"
              required
            />
            <Input
              label="Job Title"
              value={form.title}
              onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              placeholder="e.g. Senior Software Engineer"
              required
            />
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Employment Type</label>
              <select
                value={form.employment_type || "FULL_TIME"}
                onChange={(e) => setForm((p) => ({ ...p, employment_type: e.target.value }))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="FULL_TIME">Full-Time</option>
                <option value="PART_TIME">Part-Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
                <option value="FREELANCE">Freelance</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Location Arrangement</label>
              <select
                value={form.location_type || "REMOTE"}
                onChange={(e) => setForm((p) => ({ ...p, location_type: e.target.value }))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="REMOTE">Remote</option>
                <option value="HYBRID">Hybrid</option>
                <option value="ON_SITE">On-site</option>
              </select>
            </div>
            <Input
              label="Location (City, State / Country)"
              value={form.location || ""}
              onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
              placeholder="e.g. New York, NY"
            />
            <Input
              label="Start Date"
              type="date"
              value={form.start_date || ""}
              onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))}
            />
            {!form.is_current && (
              <Input
                label="End Date"
                type="date"
                value={form.end_date || ""}
                onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
              />
            )}
          </div>

          <div className="flex items-center space-x-2 pt-1">
            <input
              id="is_current_exp"
              type="checkbox"
              checked={form.is_current}
              onChange={(e) => setForm((p) => ({ ...p, is_current: e.target.checked }))}
              className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="is_current_exp" className="text-sm font-medium text-slate-700 cursor-pointer">
              I currently work here
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Description / Responsibilities
            </label>
            <textarea
              rows={3}
              value={form.description || ""}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              placeholder="Key responsibilities and initiatives delivered in this role..."
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Key Achievements & Impact
            </label>
            <textarea
              rows={2}
              value={form.achievements || ""}
              onChange={(e) => setForm((p) => ({ ...p, achievements: e.target.value }))}
              placeholder="Measurable outcomes (e.g., Reduced latency by 45%, increased revenue by $1.2M)..."
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSaving}>
              {editingItem ? "Save Changes" : "Create Record"}
            </Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};
