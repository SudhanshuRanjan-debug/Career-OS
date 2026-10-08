import React from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { DocumentsTab } from "@/features/profile/DocumentsTab";
import { ArrowLeft, User } from "lucide-react";

export const DocumentsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between text-sm text-slate-500">
        <Link to="/profile" className="hover:text-blue-600 flex items-center gap-1">
          <User className="w-4 h-4" /> Go to Full Profile
        </Link>
      </div>

      <PageHeader
        title="Document Vault"
        subtitle="Secure private storage for cover letters, academic transcripts, recommendation letters, and certifications."
      />

      <DocumentsTab />
    </div>
  );
};
