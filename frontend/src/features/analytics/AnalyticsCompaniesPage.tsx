/**
 * Analytics Companies Page.
 * Stage 9: Analytics & Settings.
 */

import React from "react";
import { Link, NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Building2, ArrowUpRight } from "lucide-react";
import { analyticsService } from "@/services/analyticsService";

export const AnalyticsCompaniesPage: React.FC = () => {
  const tabs = [
    { name: "Overview", path: "/analytics" },
    { name: "Trends", path: "/analytics/trends" },
    { name: "Pipeline", path: "/analytics/pipeline" },
    { name: "Companies", path: "/analytics/companies" },
    { name: "Outcomes", path: "/analytics/outcomes" },
    { name: "Time Analysis", path: "/analytics/time" },
  ];

  const { data: companyData, isLoading } = useQuery({
    queryKey: ["analytics-companies"],
    queryFn: () => analyticsService.getCompanies(),
    staleTime: 30000,
  });

  const companies = companyData?.companies || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Company Analytics"
        description="Deterministic response rates, interview progress, and offer conversion grouped by employer."
      />

      <div className="flex items-center gap-6 border-b border-slate-200 overflow-x-auto pb-1">
        {tabs.map((tab) => (
          <NavLink
            key={tab.name}
            to={tab.path}
            end={tab.path === "/analytics"}
            className={({ isActive }) =>
              `pb-3 text-sm font-semibold whitespace-nowrap transition-colors border-b-2 ${
                isActive
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`
            }
          >
            {tab.name}
          </NavLink>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-600" /> Employer Breakdown & Response Rates
          </CardTitle>
          <span className="text-xs text-slate-500 font-medium">
            {companyData?.total_companies ?? 0} distinct employers
          </span>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="p-8 text-center text-sm text-slate-500">Loading company metrics...</div>
          ) : companies.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              No company applications recorded yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Company</th>
                    <th className="py-2.5 px-3 text-center">Applications</th>
                    <th className="py-2.5 px-3 text-center">Active</th>
                    <th className="py-2.5 px-3 text-center">Interviews</th>
                    <th className="py-2.5 px-3 text-center">Offers</th>
                    <th className="py-2.5 px-3 text-center">Rejections</th>
                    <th className="py-2.5 px-3 text-right">Response Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {companies.map((c) => (
                    <tr key={c.company_name} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-3 font-semibold text-slate-900">
                        {c.company_id ? (
                          <Link
                            to={`/network/companies/${c.company_id}`}
                            className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            {c.company_name}
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        ) : (
                          c.company_name
                        )}
                      </td>
                      <td className="py-3 px-3 text-center font-bold text-slate-800">
                        {c.total_applications}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <Badge variant={c.active_applications > 0 ? "info" : "neutral"}>
                          {c.active_applications}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                          {c.interviews_count}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                          {c.offers_count}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center text-slate-500">
                        {c.rejected_count}
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-slate-900">
                        {c.response_rate.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
