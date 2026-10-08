import React, { useState, useEffect } from "react";
import { Plus, Languages, Trash2, Edit2, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { profileService } from "@/services/profileService";
import type { LanguageItem, LanguagePayload } from "@/types/profile.types";

const PROFICIENCIES = [
  "Native or Bilingual",
  "Full Professional",
  "Professional Working",
  "Limited Working",
  "Elementary",
];

export const LanguagesTab: React.FC = () => {
  const [languages, setLanguages] = useState<LanguageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<LanguageItem | null>(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [name, setName] = useState("");
  const [proficiency, setProficiency] = useState("Professional Working");

  const fetchLanguages = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await profileService.getLanguages();
      setLanguages(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load languages.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLanguages();
  }, []);

  const openAddModal = () => {
    setEditingItem(null);
    setName("");
    setProficiency("Professional Working");
    setIsModalOpen(true);
  };

  const openEditModal = (item: LanguageItem) => {
    setEditingItem(item);
    setName(item.name);
    setProficiency(item.proficiency || "Professional Working");
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload: LanguagePayload = {
      name: name.trim(),
      proficiency: proficiency.trim() || null,
    };

    try {
      setSaving(true);
      if (editingItem) {
        await profileService.updateLanguage(editingItem.id, payload);
      } else {
        await profileService.createLanguage(payload);
      }
      setIsModalOpen(false);
      await fetchLanguages();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save language.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this language?")) return;
    try {
      await profileService.deleteLanguage(id);
      await fetchLanguages();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete language.");
    }
  };

  const getBadgeVariant = (prof: string | null) => {
    if (!prof) return "neutral";
    const lower = prof.toLowerCase();
    if (lower.includes("native")) return "success";
    if (lower.includes("full") || lower.includes("professional")) return "info";
    return "neutral";
  };

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <CardTitle>Languages</CardTitle>
          <p className="text-xs text-slate-500">Spoken and written language proficiencies.</p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
          Add Language
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading languages...</span>
          </div>
        ) : languages.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <Languages className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No languages recorded</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Add your spoken and written languages along with your estimated fluency level.
            </p>
            <Button size="sm" variant="outline" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
              Add Language
            </Button>
          </div>
        ) : (
          <div className="space-y-2.5">
            {languages.map((item) => (
              <div
                key={item.id}
                className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
                    <Languages className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-900">{item.name}</span>
                    <p className="text-xs text-slate-500 mt-0.5">{item.proficiency || "Proficiency not specified"}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {item.proficiency && (
                    <Badge variant={getBadgeVariant(item.proficiency)}>
                      {item.proficiency}
                    </Badge>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => openEditModal(item)}>
                    <Edit2 className="w-3.5 h-3.5" />
                  </Button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1 text-slate-400 hover:text-red-600 rounded transition-colors"
                    title="Delete language"
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
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingItem ? "Edit Language" : "Add Language"}
        description="Specify the language name and your self-reported working proficiency."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={saving} onClick={handleSave}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              {editingItem ? "Save Changes" : "Add Language"}
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleSave}>
          <Input
            label="Language Name"
            placeholder="e.g. English, Spanish, Mandarin, French"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Proficiency Level</label>
            <select
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              value={proficiency}
              onChange={(e) => setProficiency(e.target.value)}
            >
              {PROFICIENCIES.map((prof) => (
                <option key={prof} value={prof}>
                  {prof}
                </option>
              ))}
            </select>
          </div>
        </form>
      </Modal>
    </Card>
  );
};
