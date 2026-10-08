import React, { useState, useEffect } from "react";
import { Plus, Trophy, ExternalLink, Trash2, Edit2, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { profileService } from "@/services/profileService";
import type { AchievementItem, AchievementPayload } from "@/types/profile.types";

const CATEGORIES = [
  "Hackathon",
  "Competition",
  "Award",
  "Scholarship",
  "Publication",
  "Leadership",
  "Open Source",
  "Honor",
  "Other",
];

export const AchievementsTab: React.FC = () => {
  const [achievements, setAchievements] = useState<AchievementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<AchievementItem | null>(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Hackathon");
  const [issuer, setIssuer] = useState("");
  const [date, setDate] = useState("");
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");

  const fetchAchievements = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await profileService.getAchievements();
      setAchievements(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load achievements.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAchievements();
  }, []);

  const openAddModal = () => {
    setEditingItem(null);
    setTitle("");
    setCategory("Hackathon");
    setIssuer("");
    setDate("");
    setUrl("");
    setDescription("");
    setIsModalOpen(true);
  };

  const openEditModal = (item: AchievementItem) => {
    setEditingItem(item);
    setTitle(item.title);
    setCategory(item.category || "Other");
    setIssuer(item.issuer || "");
    setDate(item.date || "");
    setUrl(item.url || "");
    setDescription(item.description || "");
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const payload: AchievementPayload = {
      title: title.trim(),
      category: category.trim() || null,
      issuer: issuer.trim() || null,
      date: date || null,
      url: url.trim() || null,
      description: description.trim() || null,
    };

    try {
      setSaving(true);
      if (editingItem) {
        await profileService.updateAchievement(editingItem.id, payload);
      } else {
        await profileService.createAchievement(payload);
      }
      setIsModalOpen(false);
      await fetchAchievements();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save achievement.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this achievement?")) return;
    try {
      await profileService.deleteAchievement(id);
      await fetchAchievements();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete achievement.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <CardTitle>Achievements & Honors</CardTitle>
          <p className="text-xs text-slate-500">Hackathon awards, publications, scholarships, and open-source contributions.</p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
          Add Achievement
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
            <span className="text-sm">Loading achievements...</span>
          </div>
        ) : achievements.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <Trophy className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No achievements recorded</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Highlight hackathon wins, published papers, academic honors, or notable leadership milestones.
            </p>
            <Button size="sm" variant="outline" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
              Add Your First Achievement
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {achievements.map((item) => (
              <div
                key={item.id}
                className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-amber-100 text-amber-700 rounded-xl mt-0.5 flex-shrink-0">
                    <Trophy className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-semibold text-slate-900">{item.title}</h4>
                      {item.category && <Badge variant="neutral">{item.category}</Badge>}
                    </div>
                    {(item.issuer || item.date) && (
                      <p className="text-xs text-slate-500 mt-1">
                        {item.issuer ? `Conferred by ${item.issuer}` : ""}
                        {item.issuer && item.date ? " • " : ""}
                        {item.date ? item.date : ""}
                      </p>
                    )}
                    {item.description && <p className="text-xs text-slate-600 mt-1.5">{item.description}</p>}
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2 font-medium"
                      >
                        View Details / Proof <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                  <Button size="sm" variant="outline" leftIcon={<Edit2 className="w-3.5 h-3.5" />} onClick={() => openEditModal(item)}>
                    Edit
                  </Button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-2 text-slate-400 hover:text-red-600 rounded-lg transition-colors"
                    title="Delete achievement"
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
        title={editingItem ? "Edit Achievement" : "Add Achievement"}
        description="Record awards, contest finishes, recognitions, or publications."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={saving} onClick={handleSave}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              {editingItem ? "Save Changes" : "Add Achievement"}
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleSave}>
          <Input
            label="Achievement Title"
            placeholder="e.g. 1st Place — National Cloud Hackathon"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Date Conferred"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          <Input
            label="Conferring Entity / Issuer"
            placeholder="e.g. ACM, TechFest, IEEE, University"
            value={issuer}
            onChange={(e) => setIssuer(e.target.value)}
          />
          <Input
            label="Proof / Project / Article URL"
            placeholder="https://devpost.com/software/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              rows={3}
              placeholder="What did you achieve, what was the impact, and how many competitors participated?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </form>
      </Modal>
    </Card>
  );
};
