import React from "react";
import { Link } from "react-router-dom";
import { Search, Bell, Menu, Plus } from "lucide-react";
import { useUIStore } from "@/store/uiStore";
import { useAuthStore } from "@/store/authStore";
import { useQuery } from "@tanstack/react-query";
import { notificationService } from "@/services/notificationService";
import { Button } from "@/components/ui/Button";

export const TopBar: React.FC = () => {
  const { toggleMobileMenu } = useUIStore();
  const { user } = useAuthStore();

  const { data: unreadData } = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: () => notificationService.getUnreadCount(),
    refetchInterval: 30000,
  });
  const unreadCount = unreadData?.unread_count ?? 0;

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between h-16 px-4 md:px-8 bg-white border-b border-slate-200">
      {/* Left: Mobile hamburger & search bar */}
      <div className="flex items-center gap-4 flex-1 max-w-lg">
        <button
          onClick={toggleMobileMenu}
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 md:hidden"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative w-full hidden sm:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            placeholder="Search applications, companies, skills, notes..."
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white text-slate-900 placeholder-slate-400"
          />
        </div>
      </div>

      {/* Right: Quick actions & notification badge */}
      <div className="flex items-center gap-3">
        <Link to="/applications">
          <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
            New Application
          </Button>
        </Link>

        <Link
          to="/notifications"
          className="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
          title="Notifications"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 flex items-center justify-center min-w-4 h-4 px-1 rounded-full bg-blue-600 text-white text-[10px] font-bold">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Link>

        <div className="h-6 w-px bg-slate-200 mx-1 hidden sm:block" />

        <Link to="/profile" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-xs shadow-sm">
            {user?.username ? user.username.slice(0, 2).toUpperCase() : "U"}
          </div>
        </Link>

      </div>
    </header>
  );
};
