import React from "react";
import { Outlet, Link } from "react-router-dom";

export const PublicLayout: React.FC = () => {
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
