import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";

export const SignInPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await authService.login({ email, password });
      setAuth(response.user, response.access_token);

      const defaultDest = response.user.role === "HIRER" ? "/recruiter/jobs" : "/dashboard";
      const fromPath = (location.state as { from?: { pathname?: string } })?.from?.pathname;
      const destination =
        fromPath && fromPath !== "/" && fromPath !== "/login" && fromPath !== "/signin"
          ? fromPath
          : defaultDest;
      navigate(destination, { replace: true });
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || "Unable to sign in. Please verify your email and password.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900 text-center">Sign in to your account</h2>
        <p className="mt-1 text-xs text-slate-500 text-center">
          Or{" "}
          <Link to="/signup" className="text-blue-600 hover:text-blue-700 font-medium">
            create a new account
          </Link>
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input
          label="Email address"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <div className="flex items-center justify-between text-xs">
          <label className="flex items-center gap-2 text-slate-600">
            <input
              type="checkbox"
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Remember me
          </label>
          <Link to="/forgot-password" className="text-blue-600 hover:text-blue-700 font-medium">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </form>
    </div>
  );
};
