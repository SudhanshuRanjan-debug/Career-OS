import React, { useState, useEffect, useRef } from "react";
import { Plus, FileText, Download, Check, Trash2, Edit2, Loader2, AlertCircle, UploadCloud } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { resumeService } from "@/services/resumeService";
import type { ResumeItem } from "@/types/resume.types";

function formatBytes(bytes: number | null): string {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const ResumesTab: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [resumeTitle, setResumeTitle] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Rename modal state
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renamingResume, setRenamingResume] = useState<ResumeItem | null>(null);
  const [newTitle, setNewTitle] = useState("");

  const fetchResumes = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await resumeService.listResumes();
      setResumes(res.items);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load resumes.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (!resumeTitle) {
        // Auto-fill title from clean filename
        const cleanName = file.name.replace(/\.[^/.]+$/, "");
        setResumeTitle(cleanName);
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please select a file to upload.");
      return;
    }

    try {
      setUploading(true);
      await resumeService.uploadResume(selectedFile, resumeTitle.trim() || undefined);
      setIsUploadOpen(false);
      setSelectedFile(null);
      setResumeTitle("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchResumes();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to upload resume.");
    } finally {
      setUploading(false);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await resumeService.setDefaultResume(id);
      await fetchResumes();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to set default resume.");
    }
  };

  const handleDownload = async (item: ResumeItem) => {
    try {
      await resumeService.downloadResume(item.id, item.original_filename);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to download resume.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this resume? Past applications that used this version will retain their historical record.")) return;
    try {
      await resumeService.deleteResume(id);
      await fetchResumes();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete resume.");
    }
  };

  const openRenameModal = (item: ResumeItem) => {
    setRenamingResume(item);
    setNewTitle(item.name);
    setIsRenameOpen(true);
  };

  const handleRename = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renamingResume || !newTitle.trim()) return;

    try {
      setRenaming(true);
      await resumeService.renameResume(renamingResume.id, newTitle.trim());
      setIsRenameOpen(false);
      await fetchResumes();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to rename resume.");
    } finally {
      setRenaming(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <CardTitle>Resume Vault & Version Management</CardTitle>
          <p className="text-xs text-slate-500">
            Maintain multiple tailored resume variants. When you submit an application, the exact version used is immutably preserved.
          </p>
        </div>
        <Button
          size="sm"
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => {
            setSelectedFile(null);
            setResumeTitle("");
            setIsUploadOpen(true);
          }}
        >
          Upload New Resume
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Historical Integrity Guarantee Banner */}
        <div className="p-3 bg-blue-50/80 border border-blue-200 rounded-lg text-xs text-blue-950 flex items-start gap-2">
          <span className="font-semibold flex-shrink-0">Historical Integrity Guarantee:</span>
          <span>
            Every application submission locks onto the specific resume record selected. Replacing or uploading resumes never mutates past submission records.
          </span>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading resumes...</span>
          </div>
        ) : resumes.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <FileText className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No resumes uploaded</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Upload your primary CV or specialized resumes (PDF, DOCX up to 10MB) to attach to future applications.
            </p>
            <Button
              size="sm"
              variant="outline"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => {
                setSelectedFile(null);
                setResumeTitle("");
                setIsUploadOpen(true);
              }}
            >
              Upload Resume
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl mt-0.5 flex-shrink-0">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-semibold text-slate-900">{resume.name}</h4>
                      <Badge variant="neutral">v{resume.version}</Badge>
                      {resume.is_default && <Badge variant="success">Default</Badge>}
                    </div>
                    <p className="text-xs text-slate-500">
                      {resume.original_filename} • {formatBytes(resume.file_size_bytes)} • Uploaded{" "}
                      {new Date(resume.uploaded_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                  {!resume.is_default && (
                    <Button
                      size="sm"
                      variant="outline"
                      leftIcon={<Check className="w-3.5 h-3.5" />}
                      onClick={() => handleSetDefault(resume.id)}
                    >
                      Set Default
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Download className="w-3.5 h-3.5" />}
                    onClick={() => handleDownload(resume)}
                  >
                    Download
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openRenameModal(resume)}
                    title="Rename resume"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </Button>
                  <button
                    onClick={() => handleDelete(resume.id)}
                    className="p-2 text-slate-400 hover:text-red-600 rounded-lg transition-colors"
                    title="Delete resume"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        title="Upload Resume Version"
        description="Select a PDF or DOCX file (up to 10MB) and assign a clear title."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsUploadOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={uploading || !selectedFile} onClick={handleUpload}>
              {uploading ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              Upload & Save
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleUpload}>
          <Input
            label="Resume Label"
            placeholder="e.g. Senior Backend Engineer v3"
            value={resumeTitle}
            onChange={(e) => setResumeTitle(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Resume File</label>
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,.doc,.docx"
              onChange={handleFileChange}
              className="hidden"
              id="resume-file-input"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="p-6 border-2 border-dashed border-slate-300 rounded-xl text-center hover:border-blue-500 transition-colors cursor-pointer bg-slate-50"
            >
              <UploadCloud className="w-8 h-8 mx-auto text-slate-400 mb-2" />
              {selectedFile ? (
                <div>
                  <p className="text-xs font-semibold text-blue-700">{selectedFile.name}</p>
                  <p className="text-[11px] text-slate-500 mt-1">{formatBytes(selectedFile.size)}</p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-semibold text-slate-700">Click to select resume file</p>
                  <p className="text-[11px] text-slate-500 mt-1">PDF, DOC, DOCX up to 10MB</p>
                </div>
              )}
            </div>
          </div>
        </form>
      </Modal>

      {/* Rename Modal */}
      <Modal
        isOpen={isRenameOpen}
        onClose={() => setIsRenameOpen(false)}
        title="Rename Resume"
        description="Update the descriptive label for this resume version."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsRenameOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={renaming || !newTitle.trim()} onClick={handleRename}>
              {renaming ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              Save Label
            </Button>
          </>
        }
      >
        <form onSubmit={handleRename}>
          <Input
            label="Resume Label"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            required
          />
        </form>
      </Modal>
    </Card>
  );
};
