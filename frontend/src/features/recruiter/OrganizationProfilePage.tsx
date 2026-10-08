import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Building2, Check, Globe, Linkedin, MapPin, Save } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { jobService } from "@/services/jobService";
import type { Organization } from "@/types/job.types";

export const OrganizationProfilePage: React.FC = () => {
  const [org, setOrg] = useState<Organization | null>(null);
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [industry, setIndustry] = useState("");
  const [size, setSize] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    const fetchOrg = async () => {
      setLoading(true);
      try {
        const data = await jobService.getOrganization();
        setOrg(data);
        setName(data.name || "");
        setWebsite(data.website || "");
        setIndustry(data.industry || "");
        setSize(data.size || "");
        setLocation(data.location || "");
        setDescription(data.description || "");
        setLinkedinUrl(data.linkedin_url || "");
      } catch (err) {
        console.error("Failed to load organization profile", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrg();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSavedSuccess(false);

    if (!name.trim()) {
      setError("Organization name cannot be empty.");
      return;
    }

    setSaving(true);
    try {
      const updated = await jobService.updateOrganization({
        name: name.trim(),
        website: website.trim() || null,
        industry: industry.trim() || null,
        size: size || null,
        location: location.trim() || null,
        description: description.trim() || null,
        linkedin_url: linkedinUrl.trim() || null,
      });
      setOrg(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <Link
          to="/recruiter/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Job Postings
        </Link>
        <h1 className="text-xl font-bold text-slate-900">Organization Profile</h1>
        <p className="text-xs text-slate-500 mt-1">
          Company profile displayed on job postings and seen by applicants.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-600" />
          Organization profile updated successfully!
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <Card className="p-6 bg-white border border-slate-200">
          <form onSubmit={handleSave} className="space-y-4">
            <Input
              label="Organization / Company Name *"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Acme Innovations Inc."
              required
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Website URL"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="https://example.com"
              />
              <Input
                label="LinkedIn Profile URL"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/company/acme"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Input
                label="Industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. Fintech, SaaS"
              />

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Company Size</label>
                <select
                  value={size}
                  onChange={(e) => setSize(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select size</option>
                  <option value="STARTUP">Startup (1-10)</option>
                  <option value="SMALL">Small (11-50)</option>
                  <option value="MEDIUM">Medium (51-200)</option>
                  <option value="LARGE">Large (201-1000)</option>
                  <option value="ENTERPRISE">Enterprise (1000+)</option>
                </select>
              </div>

              <Input
                label="Headquarters / Location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Bengaluru, India"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">About Company</label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Company mission, culture, team values, and workplace environment..."
                className="w-full text-xs rounded-lg border border-slate-300 p-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <Button type="submit" variant="primary" disabled={saving} className="gap-1.5">
                <Save className="w-4 h-4" />
                {saving ? "Saving..." : "Save Profile"}
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
};
