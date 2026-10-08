/**
 * Contact and Company API Service.
 * Stage 6: Network / Contacts.
 */

import { apiClient } from "@/lib/axios";
import type {
  Company,
  CompanyCreateInput,
  CompanyListResponse,
  CompanyUpdateInput,
  Contact,
  ContactCreateInput,
  ContactDetail,
  ContactListResponse,
  ContactUpdateInput,
} from "@/types/contact.types";

export interface ContactFilterParams {
  search?: string;
  contact_type?: string;
  company_id?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface CompanyFilterParams {
  search?: string;
  industry?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export const contactService = {
  // -------------------------------------------------------------------------
  // Contacts
  // -------------------------------------------------------------------------

  async listContacts(params?: ContactFilterParams): Promise<ContactListResponse> {
    const res = await apiClient.get<ContactListResponse>("/network/contacts", { params });
    return res.data;
  },

  async createContact(data: ContactCreateInput): Promise<Contact> {
    const res = await apiClient.post<Contact>("/network/contacts", data);
    return res.data;
  },

  async getContact(id: string): Promise<ContactDetail> {
    const res = await apiClient.get<ContactDetail>(`/network/contacts/${id}`);
    return res.data;
  },

  async updateContact(id: string, data: ContactUpdateInput): Promise<Contact> {
    const res = await apiClient.put<Contact>(`/network/contacts/${id}`, data);
    return res.data;
  },

  async deleteContact(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/network/contacts/${id}`);
    return res.data;
  },

  // -------------------------------------------------------------------------
  // Companies
  // -------------------------------------------------------------------------

  async listCompanies(params?: CompanyFilterParams): Promise<CompanyListResponse> {
    const res = await apiClient.get<CompanyListResponse>("/companies", { params });
    return res.data;
  },

  async createCompany(data: CompanyCreateInput): Promise<Company> {
    const res = await apiClient.post<Company>("/companies", data);
    return res.data;
  },

  async getCompany(id: string): Promise<Company> {
    const res = await apiClient.get<Company>(`/companies/${id}`);
    return res.data;
  },

  async updateCompany(id: string, data: CompanyUpdateInput): Promise<Company> {
    const res = await apiClient.put<Company>(`/companies/${id}`, data);
    return res.data;
  },

  async deleteCompany(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/companies/${id}`);
    return res.data;
  },
};
