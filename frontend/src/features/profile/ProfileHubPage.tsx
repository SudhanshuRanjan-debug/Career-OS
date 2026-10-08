import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, Link } from "react-router-dom";
import { CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { profileService } from "@/services/profileService";
import type { ProfileCompleteness } from "@/types/profile.types";

const profileTabs = [
  { name: "Personal", href: "/profile/personal", key: "personal" },
  { name: "Professional", href: "/profile/professional", key: "professional" },
  { name: "Education", href: "/profile/education", key: "education" },
  { name: "Experience", href: "/profile/experience", key: "experience" },
  { name: "Projects", href: "/profile/projects", key: "projects" },
  { name: "Skills", href: "/profile/skills", key: "skills" },
  { name: "Certifications", href: "/profile/certifications", key: "certifications" },
  { name: "Achievements", href: "/profile/achievements", key: "achievements" },
  { name: "Languages", href: "/profile/languages", key: "languages" },
  { name: "Resumes", href: "/profile/resumes", key: "resumes" },
  { name: "Documents", href: "/profile/documents", key: "documents" },
  { name: "Preferences", href: "/profile/preferences", key: "preferences" },
  { name: "Links", href: "/profile/links", key: "links" },
];

export const ProfileHubPage: React.FC = () => {
  const location = useLocation();
  const [completeness, setCompleteness] = useState<ProfileCompleteness | null>(null);

  const loadCompleteness = async () => {
    try {
      const data = await profileService.getCompleteness();
      setCompleteness(data);
    } catch {
      // Non-blocking for offline or during edits
    }
  };

  useEffect(() => {
    loadCompleteness();
  }, [location.pathname]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Candidate Profile"
        description="Manage your professional career identity, resume variants, credentials, and job preferences."
      />

      {/* Deterministic Profile Completeness Card */}
      {completeness && (
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                <Sparkles className="w-4 h-4" />
              </span>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Profile Completeness — {completeness.overall_score}%
                </h3>
                <p className="text-xs text-slate-500">
                  {completeness.overall_score === 100
                    ? "Your professional profile is 100% complete and application-ready!"
                    : "Complete all sections to maximize your opportunity readiness."}
                </p>
              </div>
            </div>
            <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full self-start sm:self-auto">
              {completeness.overall_score} / 100 Points
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                completeness.overall_score >= 80
                  ? "bg-emerald-500"
                  : completeness.overall_score >= 50
                  ? "bg-blue-600"
                  : "bg-amber-500"
              }`}
              style={{ width: `${completeness.overall_score}%` }}
            />
          </div>

          {/* Section Breakdown Pills */}
          <div className="flex flex-wrap gap-2 pt-1">
            {Object.entries(completeness.sections).map(([key, sec]) => {
              const tab = profileTabs.find((t) => t.key === key);
              const href = tab ? tab.href : `/profile/${key}`;
              const label = tab ? tab.name : key;

              return (
                <Link
                  key={key}
                  to={href}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    sec.completed
                      ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                      : "bg-amber-50 text-amber-800 hover:bg-amber-100"
                  }`}
                  title={
                    sec.completed
                      ? `${label}: Complete (+${sec.weight}pts)`
                      : `${label}: Missing ${sec.missing_fields.join(", ")}`
                  }
                >
                  {sec.completed ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                  )}
                  <span>{label}</span>
                  <span className="text-[10px] opacity-75">
                    {sec.completed ? `+${sec.weight}%` : `-${sec.weight}%`}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Profile Subsections Horizontal Tab Bar */}
      <div className="border-b border-slate-200 overflow-x-auto">
        <nav className="flex space-x-1 pb-1 min-w-max">
          {profileTabs.map((tab) => {
            const isActive =
              location.pathname === tab.href ||
              (tab.href === "/profile/personal" && location.pathname === "/profile");

            return (
              <NavLink
                key={tab.name}
                to={tab.href}
                className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-semibold border-b-2 border-blue-600 rounded-b-none"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                {tab.name}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="pt-2">
        <Outlet />
      </div>
    </div>
  );
};
