import { NavLink } from "react-router-dom";
import { LayoutDashboard, ScanSearch, KeyRound, Info, Shield, Terminal } from "lucide-react";

const navItems = [
  { to: "/",         icon: LayoutDashboard, label: "Dashboard" },
  { to: "/scanner",  icon: ScanSearch,      label: "URL Scanner" },
  { to: "/password", icon: KeyRound,        label: "Password Audit" },
  { to: "/about",    icon: Info,            label: "About" },
];

export default function Sidebar() {
  return (
    <aside
      className="w-[260px] min-h-screen flex flex-col shrink-0 sticky top-0 h-screen"
      style={{
        background: "linear-gradient(180deg, #0a0f1a 0%, #020617 100%)",
        borderRight: "1px solid rgba(148,163,184,0.06)",
      }}
    >
      {/* Brand */}
      <div className="px-6 pt-8 pb-6" style={{ borderBottom: "1px solid rgba(148,163,184,0.06)" }}>
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center relative"
            style={{
              background: "linear-gradient(135deg, #06b6d4, #0891b2)",
              boxShadow: "0 0 24px rgba(6,182,212,0.35), 0 0 48px rgba(6,182,212,0.08)",
            }}
          >
            <Shield size={20} className="text-white" />
            <div
              className="absolute inset-0 rounded-xl"
              style={{
                border: "1px solid rgba(6,182,212,0.4)",
                animation: "borderGlow 3s ease-in-out infinite",
              }}
            />
          </div>
          <div>
            <div className="font-extrabold text-[16px] tracking-tight" style={{ color: "#e2e8f0" }}>
              PhishGuard
            </div>
            <div
              className="text-[10px] font-bold uppercase"
              style={{ color: "#06b6d4", letterSpacing: "0.2em" }}
            >
              AI Security
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-3 pt-5 flex-1">
        <div
          className="text-[10px] font-bold uppercase px-3 pb-3"
          style={{ color: "#334155", letterSpacing: "0.15em" }}
        >
          Main Menu
        </div>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 no-underline text-[13px] transition-all duration-200"
            style={({ isActive }) => ({
              color: isActive ? "#e2e8f0" : "#64748b",
              fontWeight: isActive ? 600 : 500,
              background: isActive ? "rgba(6,182,212,0.08)" : undefined,
              borderLeft: isActive ? "2px solid #06b6d4" : "2px solid transparent",
              boxShadow: isActive ? "inset 0 0 24px rgba(6,182,212,0.04)" : undefined,
            })}
          >
            <Icon size={17} style={{ opacity: 0.85 }} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Engine Status */}
      <div className="px-4 pb-6">
        <div
          className="rounded-xl px-4 py-3.5"
          style={{
            background: "rgba(6,182,212,0.04)",
            border: "1px solid rgba(6,182,212,0.1)",
          }}
        >
          <div className="flex items-center gap-2 mb-1.5">
            <div
              className="status-dot"
              style={{ background: "#10b981", boxShadow: "0 0 8px rgba(16,185,129,0.6)" }}
            />
            <span
              className="text-[11px] font-bold uppercase"
              style={{ color: "#10b981", letterSpacing: "0.08em" }}
            >
              Operational
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px]" style={{ color: "#475569" }}>
            <Terminal size={11} />
            ML Engine v1.0 Active
          </div>
        </div>
      </div>
    </aside>
  );
}
