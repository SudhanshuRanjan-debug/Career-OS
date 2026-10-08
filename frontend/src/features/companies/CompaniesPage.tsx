import React, { useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Building2, Plus, Search, MapPin, Globe, Users, Briefcase } from "lucide-react";

export const CompaniesPage: React.FC = () => {
  const [search, setSearch] = useState("");

  const companies = [
    {
      id: "comp-1",
      name: "Google",
      industry: "Technology / Cloud / AI",
      location: "Mountain View, CA",
      size: "100,000+ employees",
      website: "https://google.com",
      applicationCount: 2,
      activeContactsCount: 3,
    },
    {
      id: "comp-2",
      name: "Stripe",
      industry: "Financial Services / FinTech",
      location: "San Francisco, CA",
      size: "7,000+ employees",
      website: "https://stripe.com",
      applicationCount: 1,
      activeContactsCount: 1,
    },
    {
      id: "comp-3",
      name: "Databricks",
      industry: "Data Intelligence / Lakehouse",
      location: "San Francisco, CA",
      size: "6,000+ employees",
      website: "https://databricks.com",
      applicationCount: 1,
      activeContactsCount: 2,
    },
    {
      id: "comp-4",
      name: "Amazon Web Services",
      industry: "Cloud Computing",
      location: "Seattle, WA",
      size: "100,000+ employees",
      website: "https://aws.amazon.com",
      applicationCount: 1,
      activeContactsCount: 1,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Companies"
        subtitle="Explore organizations you are targeting, tracking applications, recruiters, and interview history."
        actions={
          <Button variant="primary">
            <Plus className="w-4 h-4 mr-1.5" /> Add Company
          </Button>
        }
      />

      <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="w-full sm:w-80">
          <Input
            placeholder="Search companies by name or industry..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {companies.map((comp) => (
          <Card key={comp.id} className="p-5 hover:border-blue-300 transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700 font-bold">
                  {comp.name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 text-base">{comp.name}</h3>
                  <p className="text-xs text-slate-500">{comp.industry}</p>
                </div>
              </div>
              <Link to={`/companies/${comp.id}`}>
                <Button variant="outline" size="sm">
                  View Profile
                </Button>
              </Link>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-100 text-xs text-slate-600">
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>{comp.location}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>{comp.size}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                <span>{comp.applicationCount} Applications</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <a href={comp.website} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                  Website
                </a>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
