import React, { useState, useEffect } from "react";
import { Check, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { profileService } from "@/services/profileService";
import type { CandidatePreferencesUpdatePayload } from "@/types/profile.types";

const WORK_ARRANGEMENTS = [
  { value: "REMOTE", label: "Remote Only" },
  { value: "HYBRID", label: "Hybrid" },
  { value: "ON_SITE", label: "On-Site" },
  { value: "ANY", label: "Open to Any" },
];

const EMPLOYMENT_TYPES = ["Full-time", "Contract", "Part-time", "Internship"];

const COMPANY_SIZES = [
  "Early Stage (1-20)",
  "Growth (21-100)",
  "Mid-Market (101-1000)",
  "Enterprise (1000+)",
];

const RELOCATION_OPTIONS = [
  { value: "WILLING", label: "Willing to relocate" },
  { value: "OPEN_TO_DISCUSS", label: "Open to discussion / hybrid" },
  { value: "NOT_WILLING", label: "Not willing to relocate" },
];

export const PreferencesTab: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form State
  const [desiredTitles, setDesiredTitles] = useState("");
  const [preferredIndustries, setPreferredIndustries] = useState("");
  const [preferredLocations, setPreferredLocations] = useState("");
  const [workArrangement, setWorkArrangement] = useState("REMOTE");
  const [selectedEmploymentTypes, setSelectedEmploymentTypes] = useState<string[]>(["Full-time"]);
  const [minComp, setMinComp] = useState("");
  const [targetComp, setTargetComp] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [period, setPeriod] = useState("YEARLY");
  const [availability, setAvailability] = useState("1_MONTH");
  const [noticeDays, setNoticeDays] = useState("30");
  const [workAuth, setWorkAuth] = useState("");
  const [relocation, setRelocation] = useState("OPEN_TO_DISCUSS");
  const [selectedCompanySizes, setSelectedCompanySizes] = useState<string[]>([]);
  const [notes, setNotes] = useState("");

  const fetchPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await profileService.getPreferences();
      if (data) {
        setDesiredTitles((data.desired_job_titles || []).join(", "));
        setPreferredIndustries((data.preferred_industries || []).join(", "));
        setPreferredLocations((data.preferred_locations || []).join(", "));
        setWorkArrangement(data.work_arrangement || "REMOTE");
        setSelectedEmploymentTypes(data.employment_type || ["Full-time"]);
        setMinComp(data.min_compensation != null ? String(data.min_compensation) : "");
        setTargetComp(data.target_compensation != null ? String(data.target_compensation) : "");
        setCurrency(data.compensation_currency || "USD");
        setPeriod(data.compensation_period || "YEARLY");
        setAvailability(data.availability || "1_MONTH");
        setNoticeDays(data.notice_period_days != null ? String(data.notice_period_days) : "30");
        setWorkAuth((data.work_authorization || []).join(", "));
        setRelocation(data.relocation_preference || "OPEN_TO_DISCUSS");
        setSelectedCompanySizes(data.preferred_company_sizes || []);
        setNotes(data.notes || "");
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load preferences.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPreferences();
  }, []);

  const toggleEmploymentType = (type: string) => {
    if (selectedEmploymentTypes.includes(type)) {
      setSelectedEmploymentTypes(selectedEmploymentTypes.filter((t) => t !== type));
    } else {
      setSelectedEmploymentTypes([...selectedEmploymentTypes, type]);
    }
  };

  const toggleCompanySize = (size: string) => {
    if (selectedCompanySizes.includes(size)) {
      setSelectedCompanySizes(selectedCompanySizes.filter((s) => s !== size));
    } else {
      setSelectedCompanySizes([...selectedCompanySizes, size]);
    }
  };

  const parseCommaList = (str: string): string[] => {
    return str
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const payload: CandidatePreferencesUpdatePayload = {
      desired_job_titles: parseCommaList(desiredTitles),
      preferred_industries: parseCommaList(preferredIndustries),
      preferred_locations: parseCommaList(preferredLocations),
      work_arrangement: workArrangement || null,
      employment_type: selectedEmploymentTypes,
      min_compensation: minComp ? parseFloat(minComp) : null,
      target_compensation: targetComp ? parseFloat(targetComp) : null,
      compensation_currency: currency,
      compensation_period: period,
      availability: availability || null,
      notice_period_days: noticeDays ? parseInt(noticeDays, 10) : null,
      work_authorization: parseCommaList(workAuth),
      relocation_preference: relocation || null,
      preferred_company_sizes: selectedCompanySizes,
      notes: notes.trim() || null,
    };

    try {
      setSaving(true);
      await profileService.updatePreferences(payload);
      setSuccess("Preferences updated successfully.");
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to update preferences.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 flex items-center justify-center text-slate-400 gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading career preferences...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Search Preferences</CardTitle>
        <p className="text-xs text-slate-500">
          Target career parameters that define your ideal role, compensation, and work conditions.
        </p>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-center gap-2">
            <Check className="w-4 h-4 flex-shrink-0" />
            <span>{success}</span>
          </div>
        )}

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Desired Job Titles (comma-separated)"
              placeholder="e.g. Senior Backend Engineer, Distributed Systems Lead"
              value={desiredTitles}
              onChange={(e) => setDesiredTitles(e.target.value)}
            />
            <Input
              label="Preferred Industries (comma-separated)"
              placeholder="e.g. Cloud Infrastructure, Enterprise SaaS, Fintech"
              value={preferredIndustries}
              onChange={(e) => setPreferredIndustries(e.target.value)}
            />
            <Input
              label="Preferred Locations (comma-separated)"
              placeholder="e.g. San Francisco, New York, Austin, Remote"
              value={preferredLocations}
              onChange={(e) => setPreferredLocations(e.target.value)}
            />
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Work Arrangement
              </label>
              <select
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                value={workArrangement}
                onChange={(e) => setWorkArrangement(e.target.value)}
              >
                {WORK_ARRANGEMENTS.map((wa) => (
                  <option key={wa.value} value={wa.value}>
                    {wa.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Employment Types
              </label>
              <div className="flex flex-wrap gap-3 pt-1">
                {EMPLOYMENT_TYPES.map((type) => (
                  <label key={type} className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedEmploymentTypes.includes(type)}
                      onChange={() => toggleEmploymentType(type)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    {type}
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Input
                label="Minimum Comp"
                placeholder="150000"
                type="number"
                value={minComp}
                onChange={(e) => setMinComp(e.target.value)}
              />
              <Input
                label="Target Comp"
                placeholder="200000"
                type="number"
                value={targetComp}
                onChange={(e) => setTargetComp(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Currency</label>
                <select
                  className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="CAD">CAD (C$)</option>
                  <option value="INR">INR (₹)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Period</label>
                <select
                  className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  <option value="YEARLY">Yearly</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="HOURLY">Hourly</option>
                </select>
              </div>
            </div>

            <Input
              label="Notice Period (Days)"
              placeholder="30"
              type="number"
              value={noticeDays}
              onChange={(e) => setNoticeDays(e.target.value)}
            />

            <Input
              label="Work Authorization (comma-separated)"
              placeholder="e.g. US Citizen, Permanent Resident, H1B Transfer"
              value={workAuth}
              onChange={(e) => setWorkAuth(e.target.value)}
            />

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Relocation Preference
              </label>
              <select
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                value={relocation}
                onChange={(e) => setRelocation(e.target.value)}
              >
                {RELOCATION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Target Company Sizes
              </label>
              <div className="flex flex-wrap gap-4 pt-1">
                {COMPANY_SIZES.map((size) => (
                  <label key={size} className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedCompanySizes.includes(size)}
                      onChange={() => toggleCompanySize(size)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    {size}
                  </label>
                ))}
              </div>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Additional Notes / Priorities
              </label>
              <textarea
                className="w-full p-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                rows={3}
                placeholder="Specific team dynamics, technical stacks, or company culture requirements..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
              Save Preferences
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
