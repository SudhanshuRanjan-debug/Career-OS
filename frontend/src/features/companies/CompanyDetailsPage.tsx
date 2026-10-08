import React from "react";
import { useParams, Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  ArrowLeft,
  Building2,
  MapPin,
  Globe,
  Users,
  Briefcase,
  UserCheck,
  Plus,
  Calendar,
} from "lucide-react";

export const CompanyDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const company = {
    id: id || "comp-1",
    name: "Google",
    industry: "Technology & Cloud Computing",
    location: "Mountain View, CA",
    size: "100,000+ employees",
    website: "https://careers.google.com",
    description:
      "A multinational technology company focusing on search, online advertising, cloud computing, computer software, quantum computing, e-commerce, and artificial intelligence.",
    applications: [
      {
        id: "app-1",
        role: "Software Engineer III",
        stage: "Technical Interview",
        status: "Active",
        appliedDate: "2026-08-20",
      },
    ],
    contacts: [
      {
        id: "con-1",
        name: "Sarah Jenkins",
        role: "Technical Recruiter",
        email: "sarahj@google.com",
      },
      {
        id: "con-2",
        name: "David Chen",
        role: "Staff Infrastructure Engineer",
        email: "dchen@google.com",
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/companies" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Companies
        </Link>
      </div>

      <PageHeader
        title={company.name}
        subtitle={`${company.industry} • ${company.location}`}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline">
              <Plus className="w-4 h-4 mr-1.5" /> Add Contact
            </Button>
            <Button variant="primary">
              <Plus className="w-4 h-4 mr-1.5" /> Add Application
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>About Organization</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-700 leading-relaxed">{company.description}</p>
            </CardContent>
          </Card>

          {/* Applications at this company */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-blue-600" /> Linked Applications
              </CardTitle>
              <Badge variant="neutral">{company.applications.length}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {company.applications.map((app) => (
                <div
                  key={app.id}
                  className="flex items-center justify-between p-3.5 bg-slate-50 rounded-lg border border-slate-200/70"
                >
                  <div>
                    <h4 className="font-semibold text-sm text-slate-900">{app.role}</h4>
                    <span className="text-xs text-slate-500">Applied: {app.appliedDate}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="info">{app.stage}</Badge>
                    <Link to={`/applications/${app.id}`}>
                      <Button variant="outline" size="sm">
                        View Application
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Contacts at this company */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-indigo-600" /> Key Contacts & Recruiters
              </CardTitle>
              <Badge variant="neutral">{company.contacts.length}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {company.contacts.map((con) => (
                <div
                  key={con.id}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200/70 text-sm"
                >
                  <div>
                    <span className="font-semibold text-slate-900">{con.name}</span>
                    <span className="text-xs text-slate-500 block">{con.role}</span>
                  </div>
                  <span className="text-xs text-blue-600 font-mono">{con.email}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Company Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Headquarters</span>
                <span className="font-medium text-slate-900">{company.location}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Company Size</span>
                <span className="font-medium text-slate-900">{company.size}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Career Portal</span>
                <a
                  href={company.website}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-blue-600 hover:underline"
                >
                  Visit Website
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
