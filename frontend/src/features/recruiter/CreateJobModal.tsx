import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { jobService } from "@/services/jobService";
import type { CreateJobPayload, EmploymentType, ExperienceLevel, LocationType } from "@/types/job.types";

interface CreateJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateJobModal: React.FC<CreateJobModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [locationType, setLocationType] = useState<LocationType>("ON_SITE");
  const [employmentType, setEmploymentType] = useState<EmploymentType>("FULL_TIME");
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>("MID");
  const [compensationMin, setCompensationMin] = useState<string>("");
  const [compensationMax, setCompensationMax] = useState<string>("");
  const [compensationCurrency, setCompensationCurrency] = useState("INR");
  const [deadlineDate, setDeadlineDate] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim() || !description.trim()) {
      setError("Job title and description are required.");
      return;
    }

    const skills = skillsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const payload: CreateJobPayload = {
      title: title.trim(),
      description: description.trim(),
      requirements: requirements.trim() || undefined,
      location: location.trim() || undefined,
      location_type: locationType,
      employment_type: employmentType,
      experience_level: experienceLevel,
      compensation_min: compensationMin ? parseFloat(compensationMin) : undefined,
      compensation_max: compensationMax ? parseFloat(compensationMax) : undefined,
      compensation_currency: compensationCurrency.trim().toUpperCase() || "INR",
      deadline_date: deadlineDate || undefined,
      skills,
    };

    setLoading(true);
    try {
      await jobService.createJob(payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to create job posting. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Job Posting"
      description="Draft a new role for your organization. You can review and publish it when ready."
      maxWidth="lg"
    >
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      <form id="create-job-form" onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Job Title *"
          placeholder="e.g. Senior Backend Engineer"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Workplace Type</label>
            <select
              value={locationType}
              onChange={(e) => setLocationType(e.target.value as LocationType)}
              className="w-full text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="REMOTE">Remote</option>
              <option value="HYBRID">Hybrid</option>
              <option value="ON_SITE">On-Site</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Employment Type</label>
            <select
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value as EmploymentType)}
              className="w-full text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="FULL_TIME">Full Time</option>
              <option value="PART_TIME">Part Time</option>
              <option value="CONTRACT">Contract</option>
              <option value="INTERNSHIP">Internship</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Experience Level</label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value as ExperienceLevel)}
              className="w-full text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ENTRY">Entry Level</option>
              <option value="MID">Mid Level</option>
              <option value="SENIOR">Senior</option>
              <option value="LEAD">Lead / Staff</option>
              <option value="EXECUTIVE">Executive</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input
            label="Location"
            placeholder="e.g. Bengaluru, India or Mumbai"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
          <Input
            label="Deadline Date"
            type="date"
            value={deadlineDate}
            onChange={(e) => setDeadlineDate(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Input
            label="Min Compensation"
            type="number"
            placeholder="e.g. 1500000"
            value={compensationMin}
            onChange={(e) => setCompensationMin(e.target.value)}
          />
          <Input
            label="Max Compensation"
            type="number"
            placeholder="e.g. 2500000"
            value={compensationMax}
            onChange={(e) => setCompensationMax(e.target.value)}
          />
          <Input
            label="Currency"
            placeholder="INR"
            value={compensationCurrency}
            onChange={(e) => setCompensationCurrency(e.target.value)}
          />
        </div>

        <Input
          label="Required Skills (comma-separated)"
          placeholder="e.g. Python, FastAPI, PostgreSQL, Docker, AWS"
          value={skillsInput}
          onChange={(e) => setSkillsInput(e.target.value)}
        />

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Job Description *</label>
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Detailed description of the role, team, and day-to-day responsibilities..."
            className="w-full text-xs rounded-lg border border-slate-300 p-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Requirements & Qualifications</label>
          <textarea
            rows={3}
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="Key technical qualifications, educational background, years of experience..."
            className="w-full text-xs rounded-lg border border-slate-300 p-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
          <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? "Creating..." : "Save Job Draft"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
