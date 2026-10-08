/**
 * Professional Network & Contacts Page.
 * Stage 6: Network / Contacts.
 */

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import {
  Users2,
  Plus,
  Search,
  Mail,
  Linkedin,
  Phone,
  Building2,
  ChevronRight,
  Trash2,
  Filter,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { contactService, type ContactFilterParams } from "@/services/contactService";
import type {
  Contact,
  ContactCreateInput,
  ContactType,
} from "@/types/contact.types";

const CONTACT_TYPE_OPTIONS: { label: string; value: string }[] = [
  { label: "All Contacts", value: "ALL" },
  { label: "Recruiters", value: "RECRUITER" },
  { label: "Hiring Managers", value: "HIRING_MANAGER" },
  { label: "Interviewers", value: "INTERVIEWER" },
  { label: "Referrals", value: "REFERRAL" },
  { label: "Employees", value: "EMPLOYEE" },
  { label: "Other", value: "OTHER" },
];

export const ContactsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Filter and search state
  const [search, setSearch] = useState("");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("ALL");
  const [page, setPage] = useState(1);

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [contactToDelete, setContactToDelete] = useState<Contact | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Quick company create vs select
  const [isCreatingNewCompany, setIsCreatingNewCompany] = useState(false);
  const [newCompanyName, setNewCompanyName] = useState("");

  // Create form state
  const [formData, setFormData] = useState<ContactCreateInput>({
    first_name: "",
    last_name: "",
    role: "",
    contact_type: "RECRUITER",
    email: "",
    phone: "",
    linkedin_url: "",
    relationship: "",
    notes: "",
    company_id: null,
  });

  // Query: Fetch candidate's target companies for selector
  const { data: companiesData } = useQuery({
    queryKey: ["companies"],
    queryFn: () => contactService.listCompanies({ page_size: 100 }),
  });

  // Query: Fetch contacts with server-side filtering
  const queryParams: ContactFilterParams = {
    page,
    page_size: 12,
    search: search.trim() || undefined,
    contact_type: selectedType !== "ALL" ? selectedType : undefined,
    company_id: selectedCompanyId !== "ALL" ? selectedCompanyId : undefined,
    sort_by: "created_at",
    sort_order: "desc",
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["contacts", queryParams],
    queryFn: () => contactService.listContacts(queryParams),
  });

  // Mutation: Create contact
  const createMutation = useMutation({
    mutationFn: async (payload: ContactCreateInput) => {
      let finalCompanyId = payload.company_id;
      if (isCreatingNewCompany && newCompanyName.trim()) {
        const createdCompany = await contactService.createCompany({
          name: newCompanyName.trim(),
        });
        finalCompanyId = createdCompany.id;
      }
      return contactService.createContact({
        ...payload,
        company_id: finalCompanyId,
      });
    },
    onSuccess: (newContact) => {
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      setIsAddModalOpen(false);
      setIsCreatingNewCompany(false);
      setNewCompanyName("");
      setFormData({
        first_name: "",
        last_name: "",
        role: "",
        contact_type: "RECRUITER",
        email: "",
        phone: "",
        linkedin_url: "",
        relationship: "",
        notes: "",
        company_id: null,
      });
      navigate(`/network/${newContact.id}`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail;
      setFormError(typeof msg === "string" ? msg : "Failed to create contact.");
    },
  });

  // Mutation: Delete contact
  const deleteMutation = useMutation({
    mutationFn: (contactId: string) => contactService.deleteContact(contactId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      setContactToDelete(null);
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.first_name.trim()) {
      setFormError("First name is required.");
      return;
    }

    if (formData.linkedin_url && formData.linkedin_url.trim()) {
      const urlLower = formData.linkedin_url.trim().toLowerCase();
      if (!urlLower.startsWith("http://") && !urlLower.startsWith("https://")) {
        setFormError("LinkedIn URL must start with http:// or https://");
        return;
      }
    }

    createMutation.mutate({
      first_name: formData.first_name.trim(),
      last_name: formData.last_name?.trim() || null,
      role: formData.role?.trim() || null,
      contact_type: formData.contact_type || "RECRUITER",
      email: formData.email?.trim() || null,
      phone: formData.phone?.trim() || null,
      linkedin_url: formData.linkedin_url?.trim() || null,
      relationship: formData.relationship?.trim() || null,
      notes: formData.notes?.trim() || null,
      company_id: formData.company_id || null,
    });
  };

  const getContactTypeBadge = (type?: string | null) => {
    switch (type) {
      case "RECRUITER":
        return <Badge variant="info">Recruiter</Badge>;
      case "HIRING_MANAGER":
        return <Badge variant="success">Hiring Manager</Badge>;
      case "INTERVIEWER":
        return <Badge variant="warning">Interviewer</Badge>;
      case "REFERRAL":
        return <Badge variant="default">Referral</Badge>;
      case "EMPLOYEE":
        return <Badge variant="neutral">Employee</Badge>;
      default:
        return <Badge variant="neutral">Contact</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Professional Network & Contacts"
        subtitle="Manage recruiters, hiring managers, interviewers, and referral touchpoints across your career pipeline."
        actions={
          <Button
            variant="primary"
            onClick={() => {
              setFormError(null);
              setIsAddModalOpen(true);
            }}
          >
            <Plus className="w-4 h-4 mr-1.5" /> Add Contact
          </Button>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            placeholder="Search contacts by name, role, email, or company..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="w-48">
            <select
              value={selectedCompanyId}
              onChange={(e) => {
                setSelectedCompanyId(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Companies</option>
              {companiesData?.items.map((comp) => (
                <option key={comp.id} value={comp.id}>
                  {comp.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Contact Type Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-slate-400 font-medium flex items-center gap-1 shrink-0 mr-1">
          <Filter className="w-3.5 h-3.5" /> Type:
        </span>
        {CONTACT_TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => {
              setSelectedType(opt.value);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-full transition-all font-medium shrink-0 ${
              selectedType === opt.value
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Contacts Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-44 bg-slate-100 animate-pulse rounded-xl border border-slate-200" />
          ))}
        </div>
      ) : isError ? (
        <Card className="p-8 text-center text-red-600 bg-red-50 border-red-200">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-red-500" />
          <p className="font-semibold text-sm">Failed to load professional contacts</p>
          <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-3">
            Retry
          </Button>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card className="p-12 text-center border-dashed border-2 border-slate-300">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <Users2 className="w-6 h-6" />
          </div>
          <h3 className="font-semibold text-slate-800 text-base">No contacts found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {search || selectedType !== "ALL" || selectedCompanyId !== "ALL"
              ? "No contacts match your active filters. Try adjusting your query or resetting filters."
              : "Add your first recruiter, hiring manager, or professional referral to start tracking relationships."}
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setFormError(null);
              setIsAddModalOpen(true);
            }}
            className="mt-4"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Add Contact
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data?.items.map((c) => {
              const initials = `${c.first_name[0] || ""}${c.last_name?.[0] || ""}`.toUpperCase();
              return (
                <Card
                  key={c.id}
                  className="p-5 hover:border-blue-300 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm shrink-0">
                          {initials || "C"}
                        </div>
                        <div className="min-w-0">
                          <Link
                            to={`/network/${c.id}`}
                            className="font-semibold text-slate-900 text-sm hover:text-blue-600 truncate block"
                          >
                            {c.first_name} {c.last_name || ""}
                          </Link>
                          <p className="text-xs text-slate-500 truncate">{c.role || "Role unspecified"}</p>
                        </div>
                      </div>
                      {getContactTypeBadge(c.contact_type)}
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs text-slate-600">
                      <div className="flex items-center gap-1.5 font-medium text-slate-800 truncate">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">
                          {c.company?.name || "Company Unspecified"}
                        </span>
                      </div>

                      {c.email && (
                        <div className="flex items-center gap-1.5 text-slate-500 truncate">
                          <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <a href={`mailto:${c.email}`} className="truncate hover:text-blue-600">
                            {c.email}
                          </a>
                        </div>
                      )}

                      {c.phone && (
                        <div className="flex items-center gap-1.5 text-slate-500 truncate">
                          <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <a href={`tel:${c.phone}`} className="truncate hover:text-blue-600">
                            {c.phone}
                          </a>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 mt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    {c.linkedin_url ? (
                      <a
                        href={c.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                      >
                        <Linkedin className="w-3.5 h-3.5" /> LinkedIn
                      </a>
                    ) : (
                      <span className="text-slate-400 text-[11px]">No profile URL</span>
                    )}

                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setContactToDelete(c)}
                        className="text-slate-400 hover:text-red-600 p-1.5 h-auto"
                        title="Delete contact"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                      <Link to={`/network/${c.id}`}>
                        <Button variant="outline" size="sm" className="h-7 text-xs px-2.5">
                          Details <ChevronRight className="w-3 h-3 ml-1" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500">
                Showing {((page - 1) * 12) + 1}–{Math.min(page * 12, data.total)} of {data.total} contacts
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= data.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add Contact Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Professional Contact"
        description="Curate a recruiter, hiring manager, interviewer, or referral contact."
        maxWidth="md"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="First Name *"
              placeholder="e.g. Sarah"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              required
            />
            <Input
              label="Last Name"
              placeholder="e.g. Jenkins"
              value={formData.last_name || ""}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Role / Title"
              placeholder="e.g. Senior Technical Recruiter"
              value={formData.role || ""}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            />
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Contact Type</label>
              <select
                value={formData.contact_type || "RECRUITER"}
                onChange={(e) => setFormData({ ...formData, contact_type: e.target.value as ContactType })}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="RECRUITER">Recruiter</option>
                <option value="HIRING_MANAGER">Hiring Manager</option>
                <option value="INTERVIEWER">Interviewer</option>
                <option value="REFERRAL">Referral</option>
                <option value="EMPLOYEE">Employee</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>

          {/* Company selector with quick create option */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700">Associated Company</label>
              <button
                type="button"
                onClick={() => setIsCreatingNewCompany(!isCreatingNewCompany)}
                className="text-[11px] text-blue-600 hover:underline font-medium"
              >
                {isCreatingNewCompany ? "Choose Existing Company" : "+ New Company"}
              </button>
            </div>

            {isCreatingNewCompany ? (
              <Input
                placeholder="Enter company name (e.g. Google, Stripe)"
                value={newCompanyName}
                onChange={(e) => setNewCompanyName(e.target.value)}
                helperText="Will reuse existing record if name already exists in your target companies."
              />
            ) : (
              <select
                value={formData.company_id || ""}
                onChange={(e) => setFormData({ ...formData, company_id: e.target.value || null })}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- No company linked --</option>
                {companiesData?.items.map((comp) => (
                  <option key={comp.id} value={comp.id}>
                    {comp.name} {comp.industry ? `(${comp.industry})` : ""}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Email"
              type="email"
              placeholder="e.g. sarahj@google.com"
              value={formData.email || ""}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <Input
              label="Phone"
              placeholder="e.g. +1 (650) 253-0000"
              value={formData.phone || ""}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>

          <Input
            label="LinkedIn Profile URL"
            placeholder="https://linkedin.com/in/..."
            value={formData.linkedin_url || ""}
            onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
          />

          <Input
            label="Relationship Context"
            placeholder="e.g. Recruiter for Core Systems; met at TechConf 2026"
            value={formData.relationship || ""}
            onChange={(e) => setFormData({ ...formData, relationship: e.target.value })}
          />

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Private Notes (Optional)</label>
            <textarea
              rows={3}
              placeholder="Notes on communication style, referral source, preferred contact times..."
              value={formData.notes || ""}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createMutation.isPending}
            >
              Create Contact
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!contactToDelete}
        onClose={() => setContactToDelete(null)}
        title="Delete Contact"
        description="Are you sure you want to remove this contact from your network?"
        maxWidth="sm"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setContactToDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={deleteMutation.isPending}
              onClick={() => contactToDelete && deleteMutation.mutate(contactToDelete.id)}
            >
              Delete
            </Button>
          </>
        }
      >
        <p className="text-xs text-slate-600">
          This will permanently remove <strong>{contactToDelete?.first_name} {contactToDelete?.last_name}</strong>.
          Any linked applications will remain intact with the contact unlinked.
        </p>
      </Modal>
    </div>
  );
};
