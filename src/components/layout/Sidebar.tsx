import { NavLink, useNavigate } from "react-router-dom";
import { Zap, LayoutDashboard, Radio, Phone, Layers, Globe, Users, Wallet, Settings as SettingsIcon, LogOut } from "lucide-react";
import { setToken } from "@/lib/api";
import { cn } from "@/lib/utils";

const LINKS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/otp", label: "Live OTP", icon: Radio },
  { to: "/numbers", label: "Numbers", icon: Phone },
  { to: "/services", label: "Services", icon: Layers },
  { to: "/countries", label: "Countries", icon: Globe },
  { to: "/users", label: "Users", icon: Users },
  { to: "/withdrawals", label: "Withdrawals", icon: Wallet },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export default function Sidebar() {
  const nav = useNavigate();
  const logout = () => { setToken(null); nav("/login"); };

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar/80 backdrop-blur-xl">
      <div className="flex items-center gap-2 px-6 py-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-primary shadow-elegant">
          <Zap className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <div className="font-display text-lg font-semibold tracking-tight text-sidebar-accent-foreground">Seven1tel</div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/60">Admin Panel</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {LINKS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-gradient-primary text-primary-foreground shadow-elegant"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-destructive/15 hover:text-destructive"
        >
          <LogOut className="h-4 w-4" /> Logout
        </button>
      </div>
    </aside>
  );
}
