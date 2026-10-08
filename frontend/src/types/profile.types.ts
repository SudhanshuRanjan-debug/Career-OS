/**
 * Profile TypeScript interfaces for Career OS.
 */

export interface PersonalInfo {
  id: string;
  user_id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  preferred_name: string | null;
  phone: string | null;
  location_city: string | null;
  location_state: string | null;
  location_country: string | null;
  timezone: string | null;
  headline: string | null;
  website: string | null;
  profile_photo_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonalInfoUpdatePayload {
  first_name?: string | null;
  last_name?: string | null;
  preferred_name?: string | null;
  phone?: string | null;
  location_city?: string | null;
  location_state?: string | null;
  location_country?: string | null;
  timezone?: string | null;
  headline?: string | null;
  website?: string | null;
  profile_photo_key?: string | null;
}

export interface ProfessionalInfo {
  id: string;
  user_id: string;
  headline: string | null;
  professional_summary: string | null;
  career_objective: string | null;
  current_role: string | null;
  total_experience_yrs: number | null;
  notice_period_days: number | null;
  open_to_work: boolean;
  website: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProfessionalInfoUpdatePayload {
  headline?: string | null;
  professional_summary?: string | null;
  career_objective?: string | null;
  current_role?: string | null;
  total_experience_yrs?: number | null;
  notice_period_days?: number | null;
  open_to_work?: boolean;
  website?: string | null;
}

export interface CandidatePreferences {
  id: string;
  user_id: string;
  desired_job_titles: string[] | null;
  preferred_industries: string[] | null;
  preferred_locations: string[] | null;
  work_arrangement: string | null;
  employment_type: string[] | null;
  min_compensation: number | null;
  target_compensation: number | null;
  compensation_currency: string;
  compensation_period: string;
  availability: string | null;
  notice_period_days: number | null;
  work_authorization: string[] | null;
  relocation_preference: string | null;
  preferred_company_sizes: string[] | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidatePreferencesUpdatePayload {
  desired_job_titles?: string[] | null;
  preferred_industries?: string[] | null;
  preferred_locations?: string[] | null;
  work_arrangement?: string | null;
  employment_type?: string[] | null;
  min_compensation?: number | null;
  target_compensation?: number | null;
  compensation_currency?: string;
  compensation_period?: string;
  availability?: string | null;
  notice_period_days?: number | null;
  work_authorization?: string[] | null;
  relocation_preference?: string | null;
  preferred_company_sizes?: string[] | null;
  notes?: string | null;
}

export interface EducationItem {
  id: string;
  user_id: string;
  institution: string;
  degree: string | null;
  field_of_study: string | null;
  grade: string | null;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  location: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface EducationPayload {
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  grade?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  location?: string | null;
  sort_order?: number;
}

export interface ExperienceItem {
  id: string;
  user_id: string;
  company_name: string;
  title: string;
  employment_type: string | null;
  location: string | null;
  location_type: string | null;
  description: string | null;
  responsibilities: string | null;
  achievements: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ExperiencePayload {
  company_name: string;
  title: string;
  employment_type?: string | null;
  location?: string | null;
  location_type?: string | null;
  description?: string | null;
  responsibilities?: string | null;
  achievements?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  sort_order?: number;
}

export interface ProjectItem {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  role: string | null;
  tech_stack: string[] | null;
  url: string | null;
  repo_url: string | null;
  project_type: string | null;
  achievements: string | null;
  start_date: string | null;
  end_date: string | null;
  is_ongoing: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectPayload {
  name: string;
  description?: string | null;
  role?: string | null;
  tech_stack?: string[] | null;
  url?: string | null;
  repo_url?: string | null;
  project_type?: string | null;
  achievements?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_ongoing?: boolean;
  sort_order?: number;
}

export interface SkillItem {
  id: string;
  user_id: string;
  name: string;
  category: string | null;
  proficiency: string | null;
  years_of_exp: number | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface SkillPayload {
  name: string;
  category?: string | null;
  proficiency?: string | null;
  years_of_exp?: number | null;
  sort_order?: number;
}

export interface CertificationItem {
  id: string;
  user_id: string;
  name: string;
  issuing_org: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
  description: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CertificationPayload {
  name: string;
  issuing_org?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
  description?: string | null;
  sort_order?: number;
}

export interface AchievementItem {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  category: string | null;
  date: string | null;
  issuer: string | null;
  url: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface AchievementPayload {
  title: string;
  description?: string | null;
  category?: string | null;
  date?: string | null;
  issuer?: string | null;
  url?: string | null;
  sort_order?: number;
}

export interface LanguageItem {
  id: string;
  user_id: string;
  name: string;
  proficiency: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface LanguagePayload {
  name: string;
  proficiency?: string | null;
  sort_order?: number;
}

export interface ProfileLinkItem {
  id: string;
  user_id: string;
  platform: string | null;
  label: string | null;
  url: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProfileLinkPayload {
  platform?: string | null;
  label?: string | null;
  url: string;
  sort_order?: number;
}

export interface SectionCompleteness {
  completed: boolean;
  weight: number;
  missing_fields: string[];
}

export interface ProfileCompleteness {
  overall_score: number;
  sections: Record<string, SectionCompleteness>;
}

export interface ProfileOverview {
  personal: PersonalInfo | null;
  professional: ProfessionalInfo | null;
  preferences: CandidatePreferences | null;
  completeness: ProfileCompleteness;
  counts: Record<string, number>;
}
