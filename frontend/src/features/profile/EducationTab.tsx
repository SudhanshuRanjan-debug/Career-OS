import React, { useEffect, useState } from "react";
import { Plus, GraduationCap, Trash2, Edit2, Loader2, Calendar } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { profileService } from "@/services/profileService";
import type { EducationItem, EducationPayload } from "@/types/profile.types";

export const EducationTab: React.FC = () => {
  const [items, setItems] = useState<EducationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<EducationItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [form, setForm] = useState<EducationPayload>({
    institution: "",
    degree: "",
    field_of_study: "",
    grade: "",
    start_date: "",
    end_date: "",
    is_current: false,
    location: "",
    description: "",
  });

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await profileService.getEducations();
      setItems(data);
    } catch {
      // Error handling
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
      institution: "",
      degree: "",
      field_of_study: "",
      grade: "",
      start_date: "",
      end_date: "",
      is_current: false,
      location: "",
      description: "",
    });
    setModalOpen(true);
  };

  const openEdit = (item: EducationItem) => {
    setEditingItem(item);
    setForm({
      institution: item.institution,
      degree: item.degree || "",
      field_of_study: item.field_of_study || "",
      grade: item.grade || "",
      start_date: item.start_date || "",
      end_date: item.end_date || "",
      is_current: item.is_current,
      location: item.location || "",
      description: item.description || "",
    });
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload: EducationPayload = {
        institution: form.institution,
        degree: form.degree || null,
        field_of_study: form.field_of_study || null,
        grade: form.grade || null,
        start_date: form.start_date || null,
        end_date: form.is_current ? null : form.end_date || null,
        is_current: form.is_current,
        location: form.location || null,
        description: form.description || null,
      };

      if (editingItem) {
        await profileService.updateEducation(editingItem.id, payload);
      } else {
        await profileService.createEducation(payload);
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
    if (window.confirm("Are you sure you want to delete this education record?")) {
      try {
        await profileService.deleteEducation(id);
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
          <CardTitle>Education Records</CardTitle>
          <p className="text-xs text-slate-500">Degree, institution, academic history, and coursework.</p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openCreate}>
          Add Education
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="py-12 flex justify-center text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
            <GraduationCap className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">No Education Records Yet</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Add your university degrees, colleges, academic achievements, and certifications.
            </p>
            <Button size="sm" variant="outline" className="mt-4" onClick={openCreate}>
              Add Your First Education
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
                  <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl mt-0.5 flex-shrink-0">
                    <GraduationCap className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-slate-900">
                      {item.degree ? `${item.degree} in ` : ""}{item.field_of_study || "General Studies"}
                    </h4>
                    <p className="text-xs font-medium text-slate-700">{item.institution}</p>
                    <p className="text-xs text-slate-500 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{item.start_date || "N/A"} — {item.is_current ? "Present" : item.end_date || "N/A"}</span>
                      {item.grade && <span>• Grade: {item.grade}</span>}
                      {item.location && <span>• {item.location}</span>}
                    </p>
                    {item.description && (
                      <p className="text-xs text-slate-600 pt-1 leading-relaxed">{item.description}</p>
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
        title={editingItem ? "Edit Education Record" : "Add Education Record"}
        description="Provide details regarding your academic institution and degree."
      >
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label="Institution / University"
            value={form.institution}
            onChange={(e) => setForm((p) => ({ ...p, institution: e.target.value }))}
            placeholder="e.g. Stanford University"
            required
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Degree"
              value={form.degree || ""}
              onChange={(e) => setForm((p) => ({ ...p, degree: e.target.value }))}
              placeholder="e.g. Bachelor of Science"
            />
            <Input
              label="Field of Study / Major"
              value={form.field_of_study || ""}
              onChange={(e) => setForm((p) => ({ ...p, field_of_study: e.target.value }))}
              placeholder="e.g. Computer Science"
            />
            <Input
              label="Grade / GPA"
              value={form.grade || ""}
              onChange={(e) => setForm((p) => ({ ...p, grade: e.target.value }))}
              placeholder="e.g. 3.9 / 4.0"
            />
            <Input
              label="Location"
              value={form.location || ""}
              onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
              placeholder="e.g. Stanford, CA"
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
              id="is_current_edu"
              type="checkbox"
              checked={form.is_current}
              onChange={(e) => setForm((p) => ({ ...p, is_current: e.target.checked }))}
              className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="is_current_edu" className="text-sm font-medium text-slate-700 cursor-pointer">
              I am currently studying here
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Description / Coursework / Honors
            </label>
            <textarea
              rows={3}
              value={form.description || ""}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              placeholder="Relevant coursework, academic honors, activities..."
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
