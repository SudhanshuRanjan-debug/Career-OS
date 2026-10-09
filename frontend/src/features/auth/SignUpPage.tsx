import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";

export const SignUpPage: React.FC = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const [role, setRole] = useState<"CANDIDATE" | "HIRER">("CANDIDATE");
  const [organizationName, setOrganizationName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side pre-validation
    if (role === "HIRER" && !organizationName.trim()) {
      setError("Please enter your company or organization name.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (!/[A-Z]/.test(password)) {
      setError("Password must contain at least one uppercase letter.");
      return;
    }
    if (!/[0-9]/.test(password)) {
      setError("Password must contain at least one number.");
      return;
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      setError("Password must contain at least one special character.");
      return;
    }

    setLoading(true);

    try {
      const response = await authService.register({
        username: username.trim(),
        email: email.trim(),
        password,
        role,
        organization_name: role === "HIRER" ? organizationName.trim() : undefined,
      });
      setAuth(response.user, response.access_token);
      if (role === "HIRER") {
        navigate("/recruiter/jobs", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (err: any) {
      let msg = "Registration failed. Please try again.";
      if (err?.response?.data?.detail) {
        if (typeof err.response.data.detail === "string") {
          msg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          msg = err.response.data.detail.map((d: any) => d.msg || d.message).join("; ");
        }
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900 text-center">Create your account</h2>
        <p className="mt-1 text-xs text-slate-500 text-center">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign in
          </Link>
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Role Selection */}
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => setRole("CANDIDATE")}
          className={`p-3 rounded-lg border text-left transition-all ${
            role === "CANDIDATE"
              ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20"
              : "border-slate-200 hover:border-slate-300 bg-white"
          }`}
        >
          <div className="text-sm font-semibold text-slate-900">Candidate / Applicant</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Job seeker finding jobs & tracking applications</div>
        </button>
        <button
          type="button"
          onClick={() => setRole("HIRER")}
          className={`p-3 rounded-lg border text-left transition-all ${
            role === "HIRER"
              ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20"
              : "border-slate-200 hover:border-slate-300 bg-white"
          }`}
        >
          <div className="text-sm font-semibold text-slate-900">Hirer / Recruiter</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Employer posting openings & reviewing talent</div>
        </button>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {role === "HIRER" && (
          <Input
            label="Company / Organization Name"
            placeholder="e.g. Acme Innovations Inc."
            value={organizationName}
            onChange={(e) => setOrganizationName(e.target.value)}
            required
          />
        )}
        <Input
          label="Username"
          placeholder="johndoe"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <Input
          label="Email address"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <div>
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <p className="mt-1 text-[11px] text-slate-400">
            Min 8 chars with uppercase, number & special symbol.
          </p>
        </div>

        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading
            ? "Creating account..."
            : role === "HIRER"
            ? "Create Hirer / Recruiter Account"
            : "Create Candidate / Applicant Account"}
        </Button>
      </form>
    </div>
  );
};
