/**
 * Resume TypeScript interfaces.
 */

export interface ResumeItem {
  id: string;
  user_id: string;
  name: string;
  original_filename: string;
  storage_key: string;
  file_size_bytes: number | null;
  mime_type: string | null;
  version: number;
  is_default: boolean;
  uploaded_at: string;
  updated_at: string;
}

export interface ResumeListResponse {
  items: ResumeItem[];
  total: number;
}
