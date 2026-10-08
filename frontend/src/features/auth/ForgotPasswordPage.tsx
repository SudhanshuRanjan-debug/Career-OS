import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { authService } from "@/services/authService";

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await authService.forgotPassword({ email: email.trim() });
      setSubmitted(true);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || "An error occurred. Please try again later."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900 text-center">Reset your password</h2>
        <p className="mt-1 text-xs text-slate-500 text-center">
          Enter your email address and we'll send you a password reset link.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      {submitted ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 text-center space-y-2">
          <p className="font-semibold">Reset link dispatched</p>
          <p>If that email is registered, password reset instructions have been sent.</p>
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          <Input
            label="Email address"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Button type="submit" variant="primary" className="w-full" disabled={loading}>
            {loading ? "Sending..." : "Send Reset Link"}
          </Button>
        </form>
      )}

      <div className="text-center text-xs">
        <Link to="/signin" className="text-blue-600 hover:text-blue-700 font-medium">
          Back to sign in
        </Link>
      </div>
    </div>
  );
};
