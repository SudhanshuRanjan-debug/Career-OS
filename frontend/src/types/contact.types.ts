/**
 * Contact & Company Domain Types.
 * Stage 6: Network / Contacts.
 */

export type ContactType =
  | "RECRUITER"
  | "HIRING_MANAGER"
  | "INTERVIEWER"
  | "EMPLOYEE"
  | "REFERRAL"
  | "OTHER";

export type CompanySize =
  | "STARTUP"
  | "SMALL"
  | "MEDIUM"
  | "LARGE"
  | "ENTERPRISE";

export interface CompanySummary {
  id: string;
  name: string;
  website?: string | null;
  industry?: string | null;
  location?: string | null;
  size?: CompanySize | string | null;
  logo_url?: string | null;
}

export interface Company extends CompanySummary {
  description?: string | null;
  notes?: string | null;
  linkedin_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanyCreateInput {
  name: string;
  website?: string | null;
  industry?: string | null;
  size?: CompanySize | string | null;
  location?: string | null;
  description?: string | null;
  notes?: string | null;
  logo_url?: string | null;
  linkedin_url?: string | null;
}

export interface CompanyUpdateInput {
  name?: string;
  website?: string | null;
  industry?: string | null;
  size?: CompanySize | string | null;
  location?: string | null;
  description?: string | null;
  notes?: string | null;
  logo_url?: string | null;
  linkedin_url?: string | null;
}

export interface CompanyListResponse {
  items: Company[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApplicationSummary {
  id: string;
  job_title: string;
  company_name: string;
  current_stage: string;
  status: string;
  applied_date?: string | null;
}

export interface Contact {
  id: string;
  user_id: string;
  first_name: string;
  last_name?: string | null;
  role?: string | null;
  contact_type?: ContactType | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  relationship?: string | null;
  notes?: string | null;
  company_id?: string | null;
  created_at: string;
  updated_at: string;
  company?: CompanySummary | null;
}

export interface ContactSummary {
  id: string;
  first_name: string;
  last_name?: string | null;
  role?: string | null;
  email?: string | null;
  phone?: string | null;
  contact_type?: ContactType | null;
  company_name?: string | null;
}

export interface ContactDetail extends Contact {
  linked_applications: ApplicationSummary[];
}

export interface ContactCreateInput {
  first_name: string;
  last_name?: string | null;
  role?: string | null;
  contact_type?: ContactType | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  relationship?: string | null;
  notes?: string | null;
  company_id?: string | null;
}

export interface ContactUpdateInput {
  first_name?: string;
  last_name?: string | null;
  role?: string | null;
  contact_type?: ContactType | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  relationship?: string | null;
  notes?: string | null;
  company_id?: string | null;
}

export interface ContactListResponse {
  items: Contact[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
