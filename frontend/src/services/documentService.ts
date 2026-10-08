/**
 * Document Vault API Service.
 */

import { apiClient } from "@/lib/axios";
import type { DocumentItem, DocumentListResponse } from "@/types/document.types";

export const documentService = {
  async listDocuments(docType?: string): Promise<DocumentListResponse> {
    const params = docType ? { doc_type: docType } : {};
    const res = await apiClient.get<DocumentListResponse>("/documents", { params });
    return res.data;
  },

  async uploadDocument(
    file: File,
    name?: string,
    docType: string = "OTHER",
    description?: string
  ): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append("file", file);
    if (name) formData.append("name", name);
    if (docType) formData.append("doc_type", docType);
    if (description) formData.append("description", description);

    const res = await apiClient.post<DocumentItem>("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return res.data;
  },

  async downloadDocument(id: string, filename: string): Promise<void> {
    const res = await apiClient.get(`/documents/${id}/download`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async deleteDocument(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/documents/${id}`);
    return res.data;
  },
};
