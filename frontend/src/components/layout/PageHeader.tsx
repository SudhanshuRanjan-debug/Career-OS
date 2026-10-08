import React from "react";

export interface PageHeaderProps {
  title: string;
  description?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  subtitle,
  actions,
  breadcrumbs,
}) => {
  const subtitleText = description || subtitle;
  return (
    <div className="mb-6 pb-4 border-b border-slate-200">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1.5 text-xs text-slate-500 mb-2">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={crumb.label}>
              {idx > 0 && <span className="text-slate-400">/</span>}
              {crumb.href ? (
                <a href={crumb.href} className="hover:text-slate-900 transition-colors">
                  {crumb.label}
                </a>
              ) : (
                <span className="text-slate-800 font-medium">{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          {subtitleText && <p className="text-sm text-slate-500 mt-1">{subtitleText}</p>}
        </div>
        {actions && <div className="flex items-center gap-3 flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
};
