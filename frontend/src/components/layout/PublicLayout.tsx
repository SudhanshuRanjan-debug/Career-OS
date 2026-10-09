import React, { useEffect } from "react";
import { Outlet, Link, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export const PublicLayout: React.FC = () => {
  const { user, isAuthenticated, isInitializing, initializeAuth } = useAuthStore();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-600 text-white font-bold text-2xl shadow-md animate-pulse">
            C
          </div>
          <div className="flex items-center gap-2 text-slate-500 text-xs font-medium">
            <svg
              className="animate-spin h-4 w-4 text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Verifying Career OS session...
          </div>
        </div>
      </div>
    );
  }

  if (isAuthenticated && user) {
    const dest = user.role === "HIRER" ? "/recruiter/jobs" : "/dashboard";
    return <Navigate to={dest} replace />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center gap-2">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-600 text-white font-bold text-xl shadow-sm">
            C
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-900">Career OS</span>
        </Link>
        <p className="mt-2 text-xs text-slate-500 font-medium">Personal Career Operating System</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm sm:rounded-xl sm:px-10 border border-slate-200">
          <Outlet />
        </div>
      </div>
    </div>
  );
};
