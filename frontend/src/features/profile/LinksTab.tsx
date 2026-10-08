import React, { useState, useEffect } from "react";
import { Plus, Globe, ExternalLink, Trash2, Edit2, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { profileService } from "@/services/profileService";
import type { ProfileLinkItem, ProfileLinkPayload } from "@/types/profile.types";

const PLATFORMS = [
  "LinkedIn",
  "GitHub",
  "Portfolio",
  "Personal Website",
  "LeetCode",
  "Codeforces",
  "Substack / Blog",
  "Twitter / X",
  "YouTube",
  "Other",
];

export const LinksTab: React.FC = () => {
  const [links, setLinks] = useState<ProfileLinkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ProfileLinkItem | null>(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [platform, setPlatform] = useState("LinkedIn");
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");

  const fetchLinks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await profileService.getLinks();
      setLinks(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load profile links.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLinks();
  }, []);

  const openAddModal = () => {
    setEditingItem(null);
    setPlatform("LinkedIn");
    setLabel("");
    setUrl("");
    setIsModalOpen(true);
  };

  const openEditModal = (item: ProfileLinkItem) => {
    setEditingItem(item);
    setPlatform(item.platform || "Other");
    setLabel(item.label || "");
    setUrl(item.url);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    const payload: ProfileLinkPayload = {
      platform: platform.trim() || null,
      label: label.trim() || null,
      url: url.trim(),
    };

    try {
      setSaving(true);
      if (editingItem) {
        await profileService.updateLink(editingItem.id, payload);
      } else {
        await profileService.createLink(payload);
      }
      setIsModalOpen(false);
      await fetchLinks();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save profile link.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this link?")) return;
    try {
      await profileService.deleteLink(id);
      await fetchLinks();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete profile link.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <CardTitle>Professional Profiles & Links</CardTitle>
          <p className="text-xs text-slate-500">
            Links to your external code repositories, coding profiles, personal website, and professional networks.
          </p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
          Add Link
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
            <span className="text-sm">Loading links...</span>
          </div>
        ) : links.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <Globe className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No profile links added</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Add your GitHub, LinkedIn, personal website, or technical portfolio links.
            </p>
            <Button size="sm" variant="outline" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
              Add Link
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {links.map((link) => (
              <div
                key={link.id}
                className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-2 bg-blue-100 text-blue-700 rounded-lg flex-shrink-0">
                    <Globe className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-900">{link.platform || "Web Link"}</span>
                      {link.label && <span className="text-xs text-slate-500">• {link.label}</span>}
                    </div>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-blue-600 hover:underline flex items-center gap-1 truncate mt-0.5"
                    >
                      <span className="truncate">{link.url}</span>
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <Button size="sm" variant="ghost" onClick={() => openEditModal(link)}>
                    <Edit2 className="w-3.5 h-3.5" />
                  </Button>
                  <button
                    onClick={() => handleDelete(link.id)}
                    className="p-1.5 text-slate-400 hover:text-red-600 rounded transition-colors"
                    title="Delete link"
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
        title={editingItem ? "Edit Link" : "Add Profile Link"}
        description="Share a link to your online presence, code portfolio, or social networks."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={saving} onClick={handleSave}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              {editingItem ? "Save Changes" : "Add Link"}
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleSave}>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Platform / Type</label>
            <select
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              {PLATFORMS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Label (Optional)"
            placeholder="e.g. GitHub Repositories or Tech Blog"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
          <Input
            label="URL"
            type="url"
            placeholder="https://github.com/username"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </form>
      </Modal>
    </Card>
  );
};
