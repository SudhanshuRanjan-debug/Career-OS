/**
 * TypeScript interfaces for the Opportunity and SavedOpportunity domain.
 */

export type OpportunityStatus = "ACTIVE" | "SAVED" | "CONSIDERING" | "ARCHIVED" | "NOT_INTERESTED";
export type LocationType = "REMOTE" | "HYBRID" | "ON_SITE";
export type EmploymentType = "FULL_TIME" | "PART_TIME" | "CONTRACT" | "INTERNSHIP";

export interface Opportunity {
  id: string;
  user_id: string;
  company_id: string | null;
  job_posting_id?: string | null;
  title: string;
  company_name: string | null;
  source: string | null;
  source_url: string | null;
  location: string | null;
  location_type: LocationType | null;
  employment_type: EmploymentType | null;
  description: string | null;
  requirements: string | null;
  compensation_min: number | null;
  compensation_max: number | null;
  compensation_currency: string | null;
  posted_date: string | null;
  expiry_date: string | null;
  status: OpportunityStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  is_saved: boolean;
}

export interface OpportunityCreateInput {
  title: string;
  company_name?: string | null;
  company_id?: string | null;
  source?: string | null;
  source_url?: string | null;
  location?: string | null;
  location_type?: LocationType | null;
  employment_type?: EmploymentType | null;
  description?: string | null;
  requirements?: string | null;
  compensation_min?: number | null;
  compensation_max?: number | null;
  compensation_currency?: string | null;
  posted_date?: string | null;
  expiry_date?: string | null;
  status?: OpportunityStatus;
  notes?: string | null;
}

export interface OpportunityUpdateInput {
  title?: string;
  company_name?: string | null;
  company_id?: string | null;
  source?: string | null;
  source_url?: string | null;
  location?: string | null;
  location_type?: LocationType | null;
  employment_type?: EmploymentType | null;
  description?: string | null;
  requirements?: string | null;
  compensation_min?: number | null;
  compensation_max?: number | null;
  compensation_currency?: string | null;
  posted_date?: string | null;
  expiry_date?: string | null;
  status?: OpportunityStatus;
  notes?: string | null;
}

export interface OpportunityFilterParams {
  search?: string;
  status?: string;
  location_type?: string;
  employment_type?: string;
  is_saved?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface OpportunityListResponse {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SavedOpportunity {
  id: string;
  user_id: string;
  opportunity_id: string;
  saved_at: string;
  notes: string | null;
  opportunity?: Opportunity;
}

export interface SavedOpportunityListResponse {
  items: SavedOpportunity[];
  total: number;
}
