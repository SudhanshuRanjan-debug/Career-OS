import React from "react";

export interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  showPercent?: boolean;
  size?: "sm" | "md" | "lg";
  color?: "blue" | "emerald" | "amber" | "rose" | "primary" | "success" | "warning" | "danger";
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercent = true,
  size = "md",
  color = "blue",
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  const sizeStyles = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  };

  const colorStyles: Record<string, string> = {
    blue: "bg-blue-600",
    primary: "bg-blue-600",
    emerald: "bg-emerald-500",
    success: "bg-emerald-500",
    amber: "bg-amber-500",
    warning: "bg-amber-500",
    rose: "bg-rose-500",
    danger: "bg-rose-500",
  };

  return (
    <div className="w-full space-y-1.5">
      {(label || showPercent) && (
        <div className="flex items-center justify-between text-xs font-medium text-slate-700">
          {label && <span>{label}</span>}
          {showPercent && <span className="text-slate-500">{clampedValue}%</span>}
        </div>
      )}
      <div className={`w-full bg-slate-200 rounded-full overflow-hidden ${sizeStyles[size]}`}>
        <div
          className={`${sizeStyles[size]} ${colorStyles[color]} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};
