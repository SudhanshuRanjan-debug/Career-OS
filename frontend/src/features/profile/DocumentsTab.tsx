import React, { useState, useEffect, useRef } from "react";
import { Plus, FileCheck, Download, Trash2, Loader2, AlertCircle, UploadCloud, Filter } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { documentService } from "@/services/documentService";
import type { DocumentItem, DocumentType } from "@/types/document.types";

const DOC_CATEGORIES: { value: DocumentType; label: string }[] = [
  { value: "COVER_LETTER", label: "Cover Letter" },
  { value: "CERTIFICATE", label: "Certificate" },
  { value: "TRANSCRIPT", label: "Transcript" },
  { value: "PORTFOLIO", label: "Portfolio" },
  { value: "RECOMMENDATION", label: "Recommendation Letter" },
  { value: "OTHER", label: "Other Document" },
];

function formatBytes(bytes: number | null): string {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const DocumentsTab: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>("ALL");

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docName, setDocName] = useState("");
  const [docType, setDocType] = useState<DocumentType>("OTHER");
  const [description, setDescription] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async (categoryFilter?: string) => {
    try {
      setLoading(true);
      setError(null);
      const cat = categoryFilter && categoryFilter !== "ALL" ? categoryFilter : undefined;
      const res = await documentService.listDocuments(cat);
      setDocuments(res.items);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments(selectedFilter);
  }, [selectedFilter]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (!docName) {
        const cleanName = file.name.replace(/\.[^/.]+$/, "");
        setDocName(cleanName);
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
      await documentService.uploadDocument(
        selectedFile,
        docName.trim() || undefined,
        docType,
        description.trim() || undefined
      );
      setIsUploadOpen(false);
      setSelectedFile(null);
      setDocName("");
      setDocType("OTHER");
      setDescription("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchDocuments(selectedFilter);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (item: DocumentItem) => {
    try {
      await documentService.downloadDocument(item.id, item.original_filename);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to download document.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this document from your vault?")) return;
    try {
      await documentService.deleteDocument(id);
      await fetchDocuments(selectedFilter);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete document.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <CardTitle>Private Document Vault</CardTitle>
          <p className="text-xs text-slate-500">
            Securely store cover letters, transcripts, certificates, portfolios, and letters of recommendation.
          </p>
        </div>
        <Button
          size="sm"
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => {
            setSelectedFile(null);
            setDocName("");
            setDocType("OTHER");
            setDescription("");
            setIsUploadOpen(true);
          }}
        >
          Upload Document
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1 mr-1 flex-shrink-0">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          <button
            onClick={() => setSelectedFilter("ALL")}
            className={`px-3 py-1.5 rounded-full font-medium transition-colors flex-shrink-0 ${
              selectedFilter === "ALL"
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            All Documents
          </button>
          {DOC_CATEGORIES.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setSelectedFilter(cat.value)}
              className={`px-3 py-1.5 rounded-full font-medium transition-colors flex-shrink-0 ${
                selectedFilter === cat.value
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {cat.label}
            </button>
          ))}
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
            <span className="text-sm">Loading documents...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <FileCheck className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No documents found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              {selectedFilter === "ALL"
                ? "Upload your transcripts, recommendation letters, or writing samples to keep them organized."
                : `No documents categorized under "${DOC_CATEGORIES.find((c) => c.value === selectedFilter)?.label}".`}
            </p>
            <Button
              size="sm"
              variant="outline"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => {
                setSelectedFile(null);
                setDocName("");
                setDocType(selectedFilter !== "ALL" ? (selectedFilter as DocumentType) : "OTHER");
                setDescription("");
                setIsUploadOpen(true);
              }}
            >
              Upload Document
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-xl mt-0.5 flex-shrink-0">
                    <FileCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-semibold text-slate-900">{doc.name}</h4>
                      <Badge variant="neutral">{doc.doc_type.replace(/_/g, " ")}</Badge>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {doc.original_filename} • {formatBytes(doc.file_size_bytes)} • Uploaded{" "}
                      {new Date(doc.uploaded_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                    {doc.description && <p className="text-xs text-slate-600 mt-1">{doc.description}</p>}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Download className="w-3.5 h-3.5" />}
                    onClick={() => handleDownload(doc)}
                  >
                    Download
                  </Button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-slate-400 hover:text-red-600 rounded-lg transition-colors"
                    title="Delete document"
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
        title="Upload Document"
        description="Select a file to save into your private vault (PDF, DOCX, TXT, PNG, JPG up to 10MB)."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsUploadOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" disabled={uploading || !selectedFile} onClick={handleUpload}>
              {uploading ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              Upload Document
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleUpload}>
          <Input
            label="Document Name"
            placeholder="e.g. Official University Transcript"
            value={docName}
            onChange={(e) => setDocName(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Document Category</label>
            <select
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              value={docType}
              onChange={(e) => setDocType(e.target.value as DocumentType)}
            >
              {DOC_CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description (Optional)</label>
            <textarea
              className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              rows={2}
              placeholder="Short note or context for this document..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Document File</label>
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
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
                  <p className="text-xs font-semibold text-slate-700">Click to choose document file</p>
                  <p className="text-[11px] text-slate-500 mt-1">PDF, DOCX, TXT, images up to 10MB</p>
                </div>
              )}
            </div>
          </div>
        </form>
      </Modal>
    </Card>
  );
};
