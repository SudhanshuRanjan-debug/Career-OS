/**
 * Candidate Profile API Service.
 */

import { apiClient } from "@/lib/axios";
import type {
  AchievementItem,
  AchievementPayload,
  CandidatePreferences,
  CandidatePreferencesUpdatePayload,
  CertificationItem,
  CertificationPayload,
  EducationItem,
  EducationPayload,
  ExperienceItem,
  ExperiencePayload,
  LanguageItem,
  LanguagePayload,
  PersonalInfo,
  PersonalInfoUpdatePayload,
  ProfessionalInfo,
  ProfessionalInfoUpdatePayload,
  ProfileCompleteness,
  ProfileLinkItem,
  ProfileLinkPayload,
  ProfileOverview,
  ProjectItem,
  ProjectPayload,
  SkillItem,
  SkillPayload,
} from "@/types/profile.types";

export const profileService = {
  // Overview & Completeness
  async getOverview(): Promise<ProfileOverview> {
    const res = await apiClient.get<ProfileOverview>("/profile/overview");
    return res.data;
  },

  async getCompleteness(): Promise<ProfileCompleteness> {
    const res = await apiClient.get<ProfileCompleteness>("/profile/completeness");
    return res.data;
  },

  // Personal Info
  async getPersonalInfo(): Promise<PersonalInfo> {
    const res = await apiClient.get<PersonalInfo>("/profile/personal");
    return res.data;
  },

  async updatePersonalInfo(payload: PersonalInfoUpdatePayload): Promise<PersonalInfo> {
    const res = await apiClient.put<PersonalInfo>("/profile/personal", payload);
    return res.data;
  },

  // Professional Info
  async getProfessionalInfo(): Promise<ProfessionalInfo> {
    const res = await apiClient.get<ProfessionalInfo>("/profile/professional");
    return res.data;
  },

  async updateProfessionalInfo(payload: ProfessionalInfoUpdatePayload): Promise<ProfessionalInfo> {
    const res = await apiClient.put<ProfessionalInfo>("/profile/professional", payload);
    return res.data;
  },

  // Job Preferences
  async getPreferences(): Promise<CandidatePreferences> {
    const res = await apiClient.get<CandidatePreferences>("/profile/preferences");
    return res.data;
  },

  async updatePreferences(payload: CandidatePreferencesUpdatePayload): Promise<CandidatePreferences> {
    const res = await apiClient.put<CandidatePreferences>("/profile/preferences", payload);
    return res.data;
  },

  // Education
  async getEducations(): Promise<EducationItem[]> {
    const res = await apiClient.get<EducationItem[]>("/profile/education");
    return res.data;
  },

  async createEducation(payload: EducationPayload): Promise<EducationItem> {
    const res = await apiClient.post<EducationItem>("/profile/education", payload);
    return res.data;
  },

  async updateEducation(id: string, payload: Partial<EducationPayload>): Promise<EducationItem> {
    const res = await apiClient.put<EducationItem>(`/profile/education/${id}`, payload);
    return res.data;
  },

  async deleteEducation(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/education/${id}`);
    return res.data;
  },

  // Experience
  async getExperiences(): Promise<ExperienceItem[]> {
    const res = await apiClient.get<ExperienceItem[]>("/profile/experience");
    return res.data;
  },

  async createExperience(payload: ExperiencePayload): Promise<ExperienceItem> {
    const res = await apiClient.post<ExperienceItem>("/profile/experience", payload);
    return res.data;
  },

  async updateExperience(id: string, payload: Partial<ExperiencePayload>): Promise<ExperienceItem> {
    const res = await apiClient.put<ExperienceItem>(`/profile/experience/${id}`, payload);
    return res.data;
  },

  async deleteExperience(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/experience/${id}`);
    return res.data;
  },

  // Projects
  async getProjects(): Promise<ProjectItem[]> {
    const res = await apiClient.get<ProjectItem[]>("/profile/projects");
    return res.data;
  },

  async createProject(payload: ProjectPayload): Promise<ProjectItem> {
    const res = await apiClient.post<ProjectItem>("/profile/projects", payload);
    return res.data;
  },

  async updateProject(id: string, payload: Partial<ProjectPayload>): Promise<ProjectItem> {
    const res = await apiClient.put<ProjectItem>(`/profile/projects/${id}`, payload);
    return res.data;
  },

  async deleteProject(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/projects/${id}`);
    return res.data;
  },

  // Skills
  async getSkills(): Promise<SkillItem[]> {
    const res = await apiClient.get<SkillItem[]>("/profile/skills");
    return res.data;
  },

  async createSkill(payload: SkillPayload): Promise<SkillItem> {
    const res = await apiClient.post<SkillItem>("/profile/skills", payload);
    return res.data;
  },

  async updateSkill(id: string, payload: Partial<SkillPayload>): Promise<SkillItem> {
    const res = await apiClient.put<SkillItem>(`/profile/skills/${id}`, payload);
    return res.data;
  },

  async deleteSkill(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/skills/${id}`);
    return res.data;
  },

  // Certifications
  async getCertifications(): Promise<CertificationItem[]> {
    const res = await apiClient.get<CertificationItem[]>("/profile/certifications");
    return res.data;
  },

  async createCertification(payload: CertificationPayload): Promise<CertificationItem> {
    const res = await apiClient.post<CertificationItem>("/profile/certifications", payload);
    return res.data;
  },

  async updateCertification(id: string, payload: Partial<CertificationPayload>): Promise<CertificationItem> {
    const res = await apiClient.put<CertificationItem>(`/profile/certifications/${id}`, payload);
    return res.data;
  },

  async deleteCertification(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/certifications/${id}`);
    return res.data;
  },

  // Achievements
  async getAchievements(): Promise<AchievementItem[]> {
    const res = await apiClient.get<AchievementItem[]>("/profile/achievements");
    return res.data;
  },

  async createAchievement(payload: AchievementPayload): Promise<AchievementItem> {
    const res = await apiClient.post<AchievementItem>("/profile/achievements", payload);
    return res.data;
  },

  async updateAchievement(id: string, payload: Partial<AchievementPayload>): Promise<AchievementItem> {
    const res = await apiClient.put<AchievementItem>(`/profile/achievements/${id}`, payload);
    return res.data;
  },

  async deleteAchievement(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/achievements/${id}`);
    return res.data;
  },

  // Languages
  async getLanguages(): Promise<LanguageItem[]> {
    const res = await apiClient.get<LanguageItem[]>("/profile/languages");
    return res.data;
  },

  async createLanguage(payload: LanguagePayload): Promise<LanguageItem> {
    const res = await apiClient.post<LanguageItem>("/profile/languages", payload);
    return res.data;
  },

  async updateLanguage(id: string, payload: Partial<LanguagePayload>): Promise<LanguageItem> {
    const res = await apiClient.put<LanguageItem>(`/profile/languages/${id}`, payload);
    return res.data;
  },

  async deleteLanguage(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/languages/${id}`);
    return res.data;
  },

  // Profile Links
  async getLinks(): Promise<ProfileLinkItem[]> {
    const res = await apiClient.get<ProfileLinkItem[]>("/profile/links");
    return res.data;
  },

  async createLink(payload: ProfileLinkPayload): Promise<ProfileLinkItem> {
    const res = await apiClient.post<ProfileLinkItem>("/profile/links", payload);
    return res.data;
  },

  async updateLink(id: string, payload: Partial<ProfileLinkPayload>): Promise<ProfileLinkItem> {
    const res = await apiClient.put<ProfileLinkItem>(`/profile/links/${id}`, payload);
    return res.data;
  },

  async deleteLink(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/profile/links/${id}`);
    return res.data;
  },
};
