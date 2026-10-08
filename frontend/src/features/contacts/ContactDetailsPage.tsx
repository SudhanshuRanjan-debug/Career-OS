/**
 * Contact Details Page.
 * Stage 6: Network / Contacts.
 */

import React, { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import {
  ArrowLeft,
  Mail,
  Phone,
  Linkedin,
  Building2,
  Briefcase,
  Calendar,
  Edit2,
  Trash2,
  ExternalLink,
  AlertCircle,
  FileText,
  UserCheck,
  Globe,
  MapPin,
  Clock,
  Layers,
} from "lucide-react";
import { contactService } from "@/services/contactService";
import type {
  ContactType,
  ContactUpdateInput,
} from "@/types/contact.types";

const CONTACT_TYPE_LABELS: Record<string, string> = {
  RECRUITER: "Recruiter",
  HIRING_MANAGER: "Hiring Manager",
  INTERVIEWER: "Interviewer",
  REFERRAL: "Referral",
  EMPLOYEE: "Employee",
  OTHER: "Other",
};

export const ContactDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Modals state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Edit form state
  const [editFormData, setEditFormData] = useState<ContactUpdateInput>({
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

  // Company quick create vs select in edit modal
  const [isCreatingNewCompany, setIsCreatingNewCompany] = useState(false);
  const [newCompanyName, setNewCompanyName] = useState("");

  // Query: Fetch contact details
  const {
    data: contact,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["contact", id],
    queryFn: () => contactService.getContact(id!),
    enabled: !!id,
  });

  // Query: Fetch target companies for selector
  const { data: companiesData } = useQuery({
    queryKey: ["companies"],
    queryFn: () => contactService.listCompanies({ page_size: 100 }),
    enabled: isEditModalOpen,
  });

  // Mutation: Update contact
  const updateMutation = useMutation({
    mutationFn: async (payload: ContactUpdateInput) => {
      let finalCompanyId = payload.company_id;
      if (isCreatingNewCompany && newCompanyName.trim()) {
        const createdCompany = await contactService.createCompany({
          name: newCompanyName.trim(),
        });
        finalCompanyId = createdCompany.id;
      }
      return contactService.updateContact(id!, {
        ...payload,
        company_id: finalCompanyId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contact", id] });
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      setIsEditModalOpen(false);
      setIsCreatingNewCompany(false);
      setNewCompanyName("");
      setFormError(null);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to update contact.";
      setFormError(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });

  // Mutation: Delete contact
  const deleteMutation = useMutation({
    mutationFn: () => contactService.deleteContact(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      navigate("/network");
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to delete contact.";
      setFormError(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });

  const openEditModal = () => {
    if (!contact) return;
    setEditFormData({
      first_name: contact.first_name,
      last_name: contact.last_name || "",
      role: contact.role || "",
      contact_type: (contact.contact_type as ContactType) || "RECRUITER",
      email: contact.email || "",
      phone: contact.phone || "",
      linkedin_url: contact.linkedin_url || "",
      relationship: contact.relationship || "",
      notes: contact.notes || "",
      company_id: contact.company_id || null,
    });
    setIsCreatingNewCompany(false);
    setNewCompanyName("");
    setFormError(null);
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFormData.first_name?.trim()) {
      setFormError("First name is required.");
      return;
    }
    setFormError(null);
    updateMutation.mutate(editFormData);
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
        return <Badge variant="neutral">{type || "Other"}</Badge>;
    }
  };

  const getStageBadgeVariant = (stage: string) => {
    switch (stage) {
      case "OFFER":
      case "ACCEPTED":
        return "success";
      case "INTERVIEW":
      case "ASSESSMENT":
      case "PHONE_SCREEN":
        return "info";
      case "APPLIED":
        return "neutral";
      case "REJECTED":
      case "WITHDRAWN":
        return "danger";
      default:
        return "neutral";
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 bg-slate-200 rounded w-40 animate-pulse" />
        <Card className="p-8 space-y-4 animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-1/3" />
          <div className="h-4 bg-slate-100 rounded w-1/4" />
        </Card>
      </div>
    );
  }

  if (isError || !contact) {
    return (
      <div className="space-y-6">
        <Link
          to="/network"
          className="inline-flex items-center text-sm text-slate-500 hover:text-blue-600"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Network
        </Link>
        <Card className="p-8 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-lg font-bold text-slate-900">Contact Not Found</h2>
          <p className="text-sm text-slate-500">
            The requested contact does not exist or you do not have permission to view it.
          </p>
          <Link to="/network">
            <Button variant="primary" size="sm">
              Return to Network
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const fullName = `${contact.first_name} ${contact.last_name || ""}`.trim();

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/network" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Network
        </Link>
      </div>

      {/* Header */}
      <PageHeader
        title={fullName}
        subtitle={`${contact.role || "Role Unspecified"}${
          contact.company ? ` at ${contact.company.name}` : ""
        }`}
        actions={
          <div className="flex items-center gap-3">
            {contact.email && (
              <a href={`mailto:${contact.email}`}>
                <Button variant="primary">
                  <Mail className="w-4 h-4 mr-1.5" /> Email
                </Button>
              </a>
            )}
            {contact.phone && (
              <a href={`tel:${contact.phone}`}>
                <Button variant="outline">
                  <Phone className="w-4 h-4 mr-1.5" /> Call
                </Button>
              </a>
            )}
            {contact.linkedin_url && (
              <a
                href={contact.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline">
                  <Linkedin className="w-4 h-4 mr-1.5" /> LinkedIn
                </Button>
              </a>
            )}
            <Button variant="outline" onClick={openEditModal}>
              <Edit2 className="w-4 h-4 mr-1.5" /> Edit
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setFormError(null);
                setIsDeleteModalOpen(true);
              }}
            >
              <Trash2 className="w-4 h-4 text-red-500" />
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Notes & Linked Applications */}
        <div className="lg:col-span-2 space-y-6">
          {/* Relationship & Notes */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" /> Relationship & Notes
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={openEditModal}>
                <Edit2 className="w-3.5 h-3.5 mr-1" /> Edit Notes
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {contact.relationship && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-xs font-semibold text-slate-500 block mb-0.5 uppercase tracking-wide">
                    Relationship Context
                  </span>
                  <p className="text-sm font-medium text-slate-800">
                    {contact.relationship}
                  </p>
                </div>
              )}

              <div>
                <span className="text-xs font-semibold text-slate-500 block mb-1 uppercase tracking-wide">
                  Private Notes
                </span>
                {contact.notes ? (
                  <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed bg-slate-50/50 p-4 rounded-lg border border-slate-100">
                    {contact.notes}
                  </p>
                ) : (
                  <p className="text-sm text-slate-400 italic">
                    No notes recorded for this contact yet. Click "Edit Notes" to add touchpoints, referral notes, or context.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Linked Applications Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-blue-600" /> Linked Applications (
                  {contact.linked_applications?.length || 0})
                </CardTitle>
                <Link to="/applications">
                  <Button variant="outline" size="sm">
                    View All Applications
                  </Button>
                </Link>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Candidate job applications associated with {fullName} as primary contact, recruiter, or interviewer.
              </p>
            </CardHeader>
            <CardContent>
              {contact.linked_applications && contact.linked_applications.length > 0 ? (
                <div className="space-y-3">
                  {contact.linked_applications.map((app) => (
                    <div
                      key={app.id}
                      className="p-4 bg-white border border-slate-200 rounded-lg hover:border-blue-300 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Link
                            to={`/applications/${app.id}`}
                            className="font-semibold text-sm text-slate-900 hover:text-blue-600"
                          >
                            {app.job_title}
                          </Link>
                          <Badge variant={getStageBadgeVariant(app.current_stage)}>
                            {app.current_stage.replace("_", " ")}
                          </Badge>
                          <Badge variant={app.status === "ACTIVE" ? "success" : "neutral"}>
                            {app.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1 font-medium text-slate-700">
                            <Building2 className="w-3.5 h-3.5 text-slate-400" />
                            {app.company_name}
                          </span>
                          {app.applied_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3.5 h-3.5 text-slate-400" />
                              Applied: {app.applied_date}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Link to={`/applications/${app.id}`}>
                          <Button variant="outline" size="sm">
                            View Application <ExternalLink className="w-3.5 h-3.5 ml-1" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 border border-dashed border-slate-200 rounded-lg space-y-2">
                  <Briefcase className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-sm font-medium text-slate-700">
                    No applications currently linked
                  </p>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Link contacts to job applications during application creation or in the application details page.
                  </p>
                  <div className="pt-2">
                    <Link to="/applications">
                      <Button variant="outline" size="sm">
                        Go to Applications
                      </Button>
                    </Link>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Contact Metadata & Target Company */}
        <div className="space-y-6">
          {/* Contact Details Card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-blue-600" /> Contact Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Type</span>
                {getContactTypeBadge(contact.contact_type)}
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Role</span>
                <span className="font-medium text-slate-900">
                  {contact.role || "Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Email</span>
                {contact.email ? (
                  <a
                    href={`mailto:${contact.email}`}
                    className="font-medium text-blue-600 hover:underline flex items-center gap-1"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    {contact.email}
                  </a>
                ) : (
                  <span className="text-slate-400 italic">None</span>
                )}
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Phone</span>
                {contact.phone ? (
                  <a
                    href={`tel:${contact.phone}`}
                    className="font-medium text-slate-900 hover:text-blue-600 flex items-center gap-1"
                  >
                    <Phone className="w-3.5 h-3.5" />
                    {contact.phone}
                  </a>
                ) : (
                  <span className="text-slate-400 italic">None</span>
                )}
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">LinkedIn</span>
                {contact.linkedin_url ? (
                  <a
                    href={contact.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-blue-600 hover:underline flex items-center gap-1"
                  >
                    <Linkedin className="w-3.5 h-3.5" />
                    Profile <ExternalLink className="w-3 h-3 ml-0.5" />
                  </a>
                ) : (
                  <span className="text-slate-400 italic">None</span>
                )}
              </div>

              <div className="pt-2 text-xs text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span>{new Date(contact.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Updated:</span>
                  <span>{new Date(contact.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Associated Company Card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="w-4 h-4 text-blue-600" /> Target Company
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {contact.company ? (
                <>
                  <div className="flex items-center justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Name</span>
                    <span className="font-semibold text-slate-900">
                      {contact.company.name}
                    </span>
                  </div>

                  {contact.company.website && (
                    <div className="flex items-center justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Website</span>
                      <a
                        href={
                          contact.company.website.startsWith("http")
                            ? contact.company.website
                            : `https://${contact.company.website}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline flex items-center gap-1 font-medium"
                      >
                        <Globe className="w-3.5 h-3.5" />
                        Visit <ExternalLink className="w-3 h-3 ml-0.5" />
                      </a>
                    </div>
                  )}

                  {contact.company.industry && (
                    <div className="flex items-center justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Industry</span>
                      <span className="text-slate-800">{contact.company.industry}</span>
                    </div>
                  )}

                  {contact.company.location && (
                    <div className="flex items-center justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Location</span>
                      <span className="text-slate-800 flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {contact.company.location}
                      </span>
                    </div>
                  )}

                  {contact.company.size && (
                    <div className="flex items-center justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Size</span>
                      <span className="text-slate-800">{contact.company.size}</span>
                    </div>
                  )}

                  <div className="pt-2">
                    <Link to="/companies">
                      <Button variant="outline" size="sm" className="w-full">
                        View in Companies Directory
                      </Button>
                    </Link>
                  </div>
                </>
              ) : (
                <div className="text-center py-4 space-y-2">
                  <p className="text-sm text-slate-500 italic">
                    No target company linked to this contact.
                  </p>
                  <Button variant="outline" size="sm" onClick={openEditModal}>
                    Associate Company
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Contact Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Professional Contact"
        description="Update contact details, relationship notes, and company association."
        maxWidth="lg"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="First Name *"
              placeholder="e.g. Jane"
              value={editFormData.first_name}
              onChange={(e) =>
                setEditFormData({ ...editFormData, first_name: e.target.value })
              }
              required
            />
            <Input
              label="Last Name"
              placeholder="e.g. Doe"
              value={editFormData.last_name || ""}
              onChange={(e) =>
                setEditFormData({ ...editFormData, last_name: e.target.value })
              }
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Job Role / Title"
              placeholder="e.g. Technical Recruiter"
              value={editFormData.role || ""}
              onChange={(e) =>
                setEditFormData({ ...editFormData, role: e.target.value })
              }
            />
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Contact Type</label>
              <select
                value={editFormData.contact_type || "RECRUITER"}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    contact_type: e.target.value as ContactType,
                  })
                }
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(CONTACT_TYPE_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Company Association */}
          <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-slate-500" /> Target Company Association
              </label>
              <button
                type="button"
                onClick={() => {
                  setIsCreatingNewCompany(!isCreatingNewCompany);
                  setNewCompanyName("");
                }}
                className="text-xs text-blue-600 hover:underline font-medium"
              >
                {isCreatingNewCompany ? "Choose existing company" : "+ Quick create new company"}
              </button>
            </div>

            {isCreatingNewCompany ? (
              <Input
                placeholder="Enter new company name (e.g. OpenAI)..."
                value={newCompanyName}
                onChange={(e) => setNewCompanyName(e.target.value)}
              />
            ) : (
              <select
                value={editFormData.company_id || ""}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    company_id: e.target.value || null,
                  })
                }
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No Company Associated</option>
                {companiesData?.items.map((comp) => (
                  <option key={comp.id} value={comp.id}>
                    {comp.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              type="email"
              label="Email"
              placeholder="e.g. jane.doe@company.com"
              value={editFormData.email || ""}
              onChange={(e) =>
                setEditFormData({ ...editFormData, email: e.target.value })
              }
            />
            <Input
              label="Phone"
              placeholder="e.g. +1 (555) 000-0000"
              value={editFormData.phone || ""}
              onChange={(e) =>
                setEditFormData({ ...editFormData, phone: e.target.value })
              }
            />
          </div>

          <Input
            label="LinkedIn URL"
            placeholder="https://linkedin.com/in/username"
            value={editFormData.linkedin_url || ""}
            onChange={(e) =>
              setEditFormData({ ...editFormData, linkedin_url: e.target.value })
            }
          />

          <Input
            label="Relationship"
            placeholder="e.g. Met at tech conference / Referred by Sarah"
            value={editFormData.relationship || ""}
            onChange={(e) =>
              setEditFormData({ ...editFormData, relationship: e.target.value })
            }
          />

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Private Notes</label>
            <textarea
              rows={3}
              placeholder="Interview touchpoints, preparation recommendations, interaction logs..."
              value={editFormData.notes || ""}
              onChange={(e) =>
                setEditFormData({ ...editFormData, notes: e.target.value })
              }
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsEditModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Contact Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Delete Professional Contact"
        description="Are you sure you want to delete this contact?"
        maxWidth="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            You are about to delete <strong className="text-slate-900">{fullName}</strong>.
            This action cannot be undone.
          </p>
          <p className="text-xs text-slate-500 bg-amber-50 p-2.5 rounded border border-amber-200">
            Note: Associated job applications will remain intact with their contact reference unlinked.
          </p>
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-600">
              {formError}
            </div>
          )}
          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => setIsDeleteModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete Contact"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
