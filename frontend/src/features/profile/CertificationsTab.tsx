import React, { useState, useEffect } from "react";
import { Plus, Award, ExternalLink, Calendar, Trash2, Edit2, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { profileService } from "@/services/profileService";
import type { CertificationItem, CertificationPayload } from "@/types/profile.types";

export const CertificationsTab: React.FC = () => {
  const [certifications, setCertifications] = useState<CertificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCert, setEditingCert] = useState<CertificationItem | null>(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [name, setName] = useState("");
  const [issuingOrg, setIssuingOrg] = useState("");
  const [issueDate, setIssueDate] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [credentialId, setCredentialId] = useState("");
  const [credentialUrl, setCredentialUrl] = useState("");
  const [description, setDescription] = useState("");

  const fetchCertifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await profileService.getCertifications();
      setCertifications(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load certifications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCertifications();
  }, []);

  const openAddModal = () => {
    setEditingCert(null);
    setName("");
    setIssuingOrg("");
    setIssueDate("");
    setExpiryDate("");
    setCredentialId("");
    setCredentialUrl("");
    setDescription("");
    setIsModalOpen(true);
  };

  const openEditModal = (item: CertificationItem) => {
    setEditingCert(item);
    setName(item.name);
    setIssuingOrg(item.issuing_org || "");
    setIssueDate(item.issue_date || "");
    setExpiryDate(item.expiry_date || "");
    setCredentialId(item.credential_id || "");
    setCredentialUrl(item.credential_url || "");
    setDescription(item.description || "");
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload: CertificationPayload = {
      name: name.trim(),
      issuing_org: issuingOrg.trim() || null,
      issue_date: issueDate || null,
      expiry_date: expiryDate || null,
      credential_id: credentialId.trim() || null,
      credential_url: credentialUrl.trim() || null,
      description: description.trim() || null,
    };

    try {
      setSaving(true);
      if (editingCert) {
        await profileService.updateCertification(editingCert.id, payload);
      } else {
        await profileService.createCertification(payload);
      }
      setIsModalOpen(false);
      await fetchCertifications();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save certification.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this certification?")) return;
    try {
      await profileService.deleteCertification(id);
      await fetchCertifications();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete certification.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <CardTitle>Certifications & Credentials</CardTitle>
          <p className="text-xs text-slate-500">Verified licenses, cloud certifications, and technical credentials.</p>
        </div>
        <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
          Add Certification
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
            <span className="text-sm">Loading certifications...</span>
          </div>
        ) : certifications.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <Award className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No certifications recorded</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Add your cloud certifications, vendor accreditations, or specialized technical licenses.
            </p>
            <Button size="sm" variant="outline" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
              Add Your First Certification
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {certifications.map((item) => (
              <div
                key={item.id}
                className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl mt-0.5 flex-shrink-0">
                    <Award className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">{item.name}</h4>
                    <p className="text-xs text-slate-600 font-medium mt-0.5">
                      {item.issuing_org || "Self-Reported"}
                      {item.issue_date && ` • Issued ${item.issue_date}`}
                      {item.expiry_date ? ` (Expires ${item.expiry_date})` : item.issue_date ? " (No Expiration)" : ""}
                    </p>
                    {item.credential_id && (
                      <p className="text-xs text-slate-500 font-mono mt-1">Credential ID: {item.credential_id}</p>
                    )}
                    {item.description && <p className="text-xs text-slate-600 mt-1.5">{item.description}</p>}
                    {item.credential_url && (
                      <a
                        href={item.credential_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2 font-medium"
                      >
                        Verify Credential <ExternalLink className="w-3 h-3" />
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
                    title="Delete certification"
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
        title={editingCert ? "Edit Certification" : "Add Certification"}
        description="Record details about your credential, licensing authority, and verification link."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={saving} onClick={handleSave}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              {editingCert ? "Save Changes" : "Add Certification"}
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleSave}>
          <Input
            label="Certification Name"
            placeholder="e.g. AWS Certified Solutions Architect - Associate"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="Issuing Organization"
            placeholder="e.g. Amazon Web Services (AWS)"
            value={issuingOrg}
            onChange={(e) => setIssuingOrg(e.target.value)}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Issue Date"
              type="date"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
            />
            <Input
              label="Expiration Date (optional)"
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
            />
          </div>
          <Input
            label="Credential ID"
            placeholder="e.g. AWS-ASA-123456"
            value={credentialId}
            onChange={(e) => setCredentialId(e.target.value)}
          />
          <Input
            label="Verification / Credential URL"
            placeholder="https://cp.certmetrics.com/..."
            value={credentialUrl}
            onChange={(e) => setCredentialUrl(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description / Notes</label>
            <textarea
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              rows={3}
              placeholder="Brief summary of skills or domains covered..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </form>
      </Modal>
    </Card>
  );
};
