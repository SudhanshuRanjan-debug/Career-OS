/**
 * Document Vault TypeScript interfaces.
 */

export type DocumentType =
  | "COVER_LETTER"
  | "CERTIFICATE"
  | "TRANSCRIPT"
  | "PORTFOLIO"
  | "RECOMMENDATION"
  | "OTHER";

export interface DocumentItem {
  id: string;
  user_id: string;
  name: string;
  doc_type: DocumentType | string;
  original_filename: string;
  storage_key: string;
  file_size_bytes: number | null;
  mime_type: string | null;
  description: string | null;
  version: number;
  uploaded_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}
