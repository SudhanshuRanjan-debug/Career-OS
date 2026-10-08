import React, { useEffect, useState } from "react";
import { Plus, Wrench, Trash2, Edit2, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { profileService } from "@/services/profileService";
import type { SkillItem, SkillPayload } from "@/types/profile.types";

export const SkillsTab: React.FC = () => {
  const [items, setItems] = useState<SkillItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<SkillItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [form, setForm] = useState({
    name: "",
    category: "TECHNICAL",
    proficiency: "INTERMEDIATE",
    years_of_exp: "",
  });

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await profileService.getSkills();
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
      category: "TECHNICAL",
      proficiency: "INTERMEDIATE",
      years_of_exp: "",
    });
    setModalOpen(true);
  };

  const openEdit = (item: SkillItem) => {
    setEditingItem(item);
    setForm({
      name: item.name,
      category: item.category || "TECHNICAL",
      proficiency: item.proficiency || "INTERMEDIATE",
      years_of_exp: item.years_of_exp !== null ? String(item.years_of_exp) : "",
    });
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload: SkillPayload = {
        name: form.name.trim(),
        category: form.category || null,
        proficiency: form.proficiency || null,
        years_of_exp: form.years_of_exp ? parseFloat(form.years_of_exp) : null,
      };

      if (editingItem) {
        await profileService.updateSkill(editingItem.id, payload);
      } else {
        await profileService.createSkill(payload);
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
    if (window.confirm("Remove this skill from your profile?")) {
      try {
        await profileService.deleteSkill(id);
        await loadData();
      } catch {
        // Error
      }
    }
  };

  // Group by category
  const categories = Array.from(new Set(items.map((i) => i.category || "TECHNICAL")));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Skills & Competencies</CardTitle>
          <p className="text-xs text-slate-500">
            Technical languages, frameworks, cloud tools, databases, and professional competencies.
          </p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openCreate}>
          Add Skill
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="py-12 flex justify-center text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
            <Wrench className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">No Skills Added Yet</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Add at least 3 skills to unlock your profile completeness bonus.
            </p>
            <Button size="sm" variant="outline" className="mt-4" onClick={openCreate}>
              Add First Skill
            </Button>
          </div>
        ) : (
          categories.map((cat) => {
            const catItems = items.filter((i) => (i.category || "TECHNICAL") === cat);
            return (
              <div key={cat} className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {cat.replace("_", " ")} ({catItems.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {catItems.map((skill) => (
                    <div
                      key={skill.id}
                      className="group flex items-center gap-2 pl-3 pr-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs hover:border-slate-300 transition-colors"
                    >
                      <span className="font-semibold text-slate-900">{skill.name}</span>
                      {skill.proficiency && (
                        <Badge
                          variant={
                            skill.proficiency === "EXPERT"
                              ? "success"
                              : skill.proficiency === "ADVANCED"
                              ? "info"
                              : "neutral"
                          }
                        >
                          {skill.proficiency}
                        </Badge>
                      )}
                      {skill.years_of_exp !== null && (
                        <span className="text-slate-400 text-[11px]">{skill.years_of_exp} yrs</span>
                      )}
                      <div className="flex items-center ml-1 space-x-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => openEdit(skill)}
                          className="p-1 text-slate-400 hover:text-blue-600 rounded"
                          title="Edit skill"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleDelete(skill.id)}
                          className="p-1 text-slate-400 hover:text-red-600 rounded"
                          title="Delete skill"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </CardContent>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingItem ? "Edit Skill" : "Add Skill"}
        description="Add a skill and self-assess your proficiency level."
      >
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label="Skill Name"
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="e.g. Python, React, PostgreSQL, Docker"
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select
                value={form.category}
                onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="TECHNICAL">Technical (Languages / Frameworks)</option>
                <option value="TOOL">Developer Tool / Environment</option>
                <option value="CLOUD">Cloud & Infrastructure</option>
                <option value="DATABASE">Database & Storage</option>
                <option value="SOFT">Soft Skill / Leadership</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Proficiency Level</label>
              <select
                value={form.proficiency}
                onChange={(e) => setForm((p) => ({ ...p, proficiency: e.target.value }))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="BEGINNER">Beginner</option>
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
                <option value="EXPERT">Expert</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <Input
                label="Years of Experience"
                type="number"
                step="0.5"
                min="0"
                max="50"
                value={form.years_of_exp}
                onChange={(e) => setForm((p) => ({ ...p, years_of_exp: e.target.value }))}
                placeholder="e.g. 4.5"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSaving}>
              {editingItem ? "Save Changes" : "Add Skill"}
            </Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};
