import React, { useEffect, useState } from "react";
import { Check, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { profileService } from "@/services/profileService";

export const ProfessionalSummaryTab: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const [formData, setFormData] = useState({
    headline: "",
    professional_summary: "",
    career_objective: "",
    current_role: "",
    total_experience_yrs: "",
    notice_period_days: "",
    open_to_work: true,
  });

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const data = await profileService.getProfessionalInfo();
        setFormData({
          headline: data.headline || "",
          professional_summary: data.professional_summary || "",
          career_objective: data.career_objective || "",
          current_role: data.current_role || "",
          total_experience_yrs: data.total_experience_yrs !== null ? String(data.total_experience_yrs) : "",
          notice_period_days: data.notice_period_days !== null ? String(data.notice_period_days) : "",
          open_to_work: data.open_to_work,
        });
      } catch (err: any) {
        setFeedback({
          type: "error",
          message: err.response?.data?.message || "Failed to load professional information.",
        });
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      await profileService.updateProfessionalInfo({
        headline: formData.headline || null,
        professional_summary: formData.professional_summary || null,
        career_objective: formData.career_objective || null,
        current_role: formData.current_role || null,
        total_experience_yrs: formData.total_experience_yrs ? parseFloat(formData.total_experience_yrs) : null,
        notice_period_days: formData.notice_period_days ? parseInt(formData.notice_period_days, 10) : null,
        open_to_work: formData.open_to_work,
      });
      setFeedback({ type: "success", message: "Professional profile updated successfully!" });
      setTimeout(() => setFeedback(null), 4000);
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.response?.data?.message || "Failed to save professional profile.",
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
          <p className="text-xs">Loading professional profile...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Professional Profile & Summary</CardTitle>
        <p className="text-xs text-slate-500">
          Executive summary of your qualifications, career trajectory, current role, and availability.
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
            <div className="sm:col-span-2">
              <Input
                label="Professional Headline"
                value={formData.headline}
                onChange={(e) => setFormData((p) => ({ ...p, headline: e.target.value }))}
                placeholder="e.g. Senior Cloud Architect & Distributed Systems Engineer"
                required
              />
            </div>

            <Input
              label="Current Role / Title"
              value={formData.current_role}
              onChange={(e) => setFormData((p) => ({ ...p, current_role: e.target.value }))}
              placeholder="e.g. Lead Software Engineer"
            />

            <Input
              label="Total Experience (Years)"
              type="number"
              step="0.5"
              min="0"
              max="70"
              value={formData.total_experience_yrs}
              onChange={(e) => setFormData((p) => ({ ...p, total_experience_yrs: e.target.value }))}
              placeholder="e.g. 6.5"
            />

            <Input
              label="Notice Period (Days)"
              type="number"
              min="0"
              max="365"
              value={formData.notice_period_days}
              onChange={(e) => setFormData((p) => ({ ...p, notice_period_days: e.target.value }))}
              placeholder="e.g. 30"
            />

            <div className="flex items-center space-x-3 pt-6">
              <input
                id="open_to_work"
                type="checkbox"
                checked={formData.open_to_work}
                onChange={(e) => setFormData((p) => ({ ...p, open_to_work: e.target.checked }))}
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="open_to_work" className="text-sm font-medium text-slate-700 cursor-pointer">
                Actively Open to Work & New Opportunities
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Professional Summary
            </label>
            <textarea
              rows={4}
              value={formData.professional_summary}
              onChange={(e) => setFormData((p) => ({ ...p, professional_summary: e.target.value }))}
              placeholder="Provide a comprehensive summary of your expertise, key strengths, technologies, and career impact..."
              className="w-full p-3 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Career Objective
            </label>
            <textarea
              rows={3}
              value={formData.career_objective}
              onChange={(e) => setFormData((p) => ({ ...p, career_objective: e.target.value }))}
              placeholder="What target roles and environments are you seeking next in your career journey?"
              className="w-full p-3 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end pt-2">
            <Button type="submit" variant="primary" isLoading={isSaving}>
              Save Professional Profile
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
