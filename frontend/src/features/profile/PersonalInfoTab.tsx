import React, { useEffect, useState } from "react";
import { Check, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { profileService } from "@/services/profileService";
import type { PersonalInfo } from "@/types/profile.types";

export const PersonalInfoTab: React.FC = () => {
  const [profile, setProfile] = useState<PersonalInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    preferred_name: "",
    headline: "",
    phone: "",
    location_city: "",
    location_state: "",
    location_country: "",
    timezone: "",
    website: "",
  });

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const data = await profileService.getPersonalInfo();
        setProfile(data);
        setFormData({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          preferred_name: data.preferred_name || "",
          headline: data.headline || "",
          phone: data.phone || "",
          location_city: data.location_city || "",
          location_state: data.location_state || "",
          location_country: data.location_country || "",
          timezone: data.timezone || "",
          website: data.website || "",
        });
      } catch (err: any) {
        setFeedback({
          type: "error",
          message: err.response?.data?.message || "Failed to load personal information.",
        });
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      const updated = await profileService.updatePersonalInfo(formData);
      setProfile(updated);
      setFeedback({ type: "success", message: "Personal information saved successfully!" });
      setTimeout(() => setFeedback(null), 4000);
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.response?.data?.message || "Failed to save personal information.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin mb-2" />
          <p className="text-xs">Loading personal information...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Personal Information</CardTitle>
        <p className="text-xs text-slate-500">
          Contact information and location preferences used on job applications.
        </p>
      </CardHeader>
      <CardContent>
        {feedback && (
          <div
            className={`p-3 mb-4 rounded-lg text-xs flex items-center gap-2 ${
              feedback.type === "success"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-red-50 text-red-800 border border-red-200"
            }`}
          >
            {feedback.type === "success" ? (
              <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            )}
            <span>{feedback.message}</span>
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="First Name"
              value={formData.first_name}
              onChange={(e) => handleChange("first_name", e.target.value)}
              placeholder="e.g. John"
              required
            />
            <Input
              label="Last Name"
              value={formData.last_name}
              onChange={(e) => handleChange("last_name", e.target.value)}
              placeholder="e.g. Doe"
              required
            />
            <Input
              label="Preferred / Chosen Name"
              value={formData.preferred_name}
              onChange={(e) => handleChange("preferred_name", e.target.value)}
              placeholder="e.g. JD"
            />
            <Input
              label="Account Email (Verified)"
              value={profile?.email || ""}
              disabled
            />
            <Input
              label="Professional Headline"
              value={formData.headline}
              onChange={(e) => handleChange("headline", e.target.value)}
              placeholder="e.g. Senior Full Stack & Cloud Engineer"
            />
            <Input
              label="Phone Number"
              value={formData.phone}
              onChange={(e) => handleChange("phone", e.target.value)}
              placeholder="e.g. +1 (555) 019-2834"
            />
            <Input
              label="City"
              value={formData.location_city}
              onChange={(e) => handleChange("location_city", e.target.value)}
              placeholder="e.g. San Francisco"
            />
            <Input
              label="State / Province"
              value={formData.location_state}
              onChange={(e) => handleChange("location_state", e.target.value)}
              placeholder="e.g. California"
            />
            <Input
              label="Country"
              value={formData.location_country}
              onChange={(e) => handleChange("location_country", e.target.value)}
              placeholder="e.g. United States"
            />
            <Input
              label="Timezone"
              value={formData.timezone}
              onChange={(e) => handleChange("timezone", e.target.value)}
              placeholder="e.g. America/Los_Angeles"
            />
            <div className="sm:col-span-2">
              <Input
                label="Personal Website / Portfolio"
                value={formData.website}
                onChange={(e) => handleChange("website", e.target.value)}
                placeholder="https://johndoe.dev"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <Button type="submit" variant="primary" isLoading={isSaving}>
              Save Personal Info
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
