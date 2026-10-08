import React from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  User,
  Compass,
  Briefcase,
  Building2,
  CalendarCheck,
  CheckSquare,
  Calendar,
  Users2,
  BarChart3,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Search,
} from "lucide-react";
import { useUIStore } from "@/store/uiStore";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const candidateNavItems: NavItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Explore Jobs", href: "/jobs", icon: Search },
  { name: "Profile", href: "/profile", icon: User },
  { name: "Opportunities", href: "/opportunities", icon: Compass },
  { name: "Applications", href: "/applications", icon: Briefcase },
  { name: "Companies", href: "/companies", icon: Building2 },
  { name: "Interviews", href: "/interviews", icon: CalendarCheck },
  { name: "Tasks", href: "/tasks", icon: CheckSquare },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Network", href: "/network", icon: Users2 },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "Settings", href: "/settings", icon: Settings },
];

const recruiterNavItems: NavItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Job Postings", href: "/recruiter/jobs", icon: Briefcase },
  { name: "Company Profile", href: "/recruiter/organization", icon: Building2 },
  { name: "Explore Jobs", href: "/jobs", icon: Search },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { user, clearAuth } = useAuthStore();

  const navItems = user?.role === "HIRER" ? recruiterNavItems : candidateNavItems;

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      clearAuth();
      navigate("/signin", { replace: true });
    }
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 flex flex-col bg-white border-r border-slate-200 transition-all duration-200 ease-in-out ${
        sidebarCollapsed ? "w-20" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-100">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-600 text-white font-bold text-lg shadow-sm">
            C
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-slate-900">Career OS</span>
              <span className="text-[11px] text-slate-500 font-medium">
                {user?.role === "HIRER" ? "Recruiter Portal" : "Personal Platform"}
              </span>
            </div>
          )}
        </div>
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors hidden md:flex"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            location.pathname === item.href ||
            (item.href !== "/dashboard" && location.pathname.startsWith(item.href));

          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              } ${sidebarCollapsed ? "justify-center px-2" : ""}`}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
              {!sidebarCollapsed && <span className="truncate">{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer / User Profile summary */}
      {!sidebarCollapsed && (
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-xs flex-shrink-0">
                {user?.username ? user.username.slice(0, 2).toUpperCase() : "U"}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-slate-900 truncate">
                  {user?.username || "Authenticated User"}
                </span>
                <span className="text-[11px] text-slate-500 truncate">{user?.email || ""}</span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
};
