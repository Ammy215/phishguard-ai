import { useEffect, useState } from "react";
import { healthCheck } from "../services/api";
import {
  Search, ShieldAlert, ShieldCheck, TrendingUp, Clock,
  Trash2, Activity, Wifi, WifiOff, BarChart3, Crosshair
} from "lucide-react";

interface Stats {
  totalScanned:  number;
  phishingCount: number;
  safeCount:     number;
  lastUrl:       string;
}

interface HistoryEntry {
  url:        string;
  result:     string;
  confidence: number;
  ts:         number;
}

function loadStats(): Stats {
  const total    = parseInt(localStorage.getItem("totalScanned")  ?? "0");
  const phishing = parseInt(localStorage.getItem("phishingCount") ?? "0");
  return {
    totalScanned:  total,
    phishingCount: phishing,
    safeCount:     Math.max(0, total - phishing),
    lastUrl:       localStorage.getItem("lastUrl") ?? "",
  };
}

function loadHistory(): HistoryEntry[] {
  try { return JSON.parse(localStorage.getItem("scanHistory") ?? "[]"); }
  catch { return []; }
}

function timeAgo(ts: number): string {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60)   return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon:  React.ReactNode;
  color: string;
  borderColor: string;
  sub?:  string;
}

function StatCard({ label, value, icon, color, borderColor, sub }: StatCardProps) {
  return (
    <div
      className="glass p-5 flex-1 min-w-[160px] relative overflow-hidden group transition-all duration-300 hover:-translate-y-0.5"
      style={{ borderTop: `2px solid ${borderColor}` }}
    >
      <div className="flex items-center justify-between mb-4">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ background: `${color}12`, border: `1px solid ${color}20` }}
        >
          <div style={{ color }}>{icon}</div>
        </div>
        {sub && (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md" style={{ color, background: `${color}10` }}>
            {sub}
          </span>
        )}
      </div>
      <div className="text-3xl font-extrabold tracking-tight leading-none mb-1" style={{ color: "#e2e8f0" }}>
        {value}
      </div>
      <div className="text-[11px] font-semibold uppercase" style={{ color: "#475569", letterSpacing: "0.1em" }}>
        {label}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats,     setStats]     = useState<Stats>(loadStats);
  const [history,   setHistory]   = useState<HistoryEntry[]>(loadHistory);
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");

  useEffect(() => {
    const refresh = () => { setStats(loadStats()); setHistory(loadHistory()); };
    window.addEventListener("focus", refresh);
    const interval = setInterval(refresh, 5000);

    healthCheck()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));

    return () => { window.removeEventListener("focus", refresh); clearInterval(interval); };
  }, []);

  const phishRate = stats.totalScanned > 0 ? Math.round((stats.phishingCount / stats.totalScanned) * 100) : 0;
  const safeRate  = 100 - phishRate;

  const clearData = () => {
    ["totalScanned", "phishingCount", "lastUrl", "scanHistory"].forEach(k => localStorage.removeItem(k));
    setStats(loadStats());
    setHistory([]);
  };

  return (
    <div className="max-w-[960px] mx-auto animate-in">

      {/* Header */}
      <div className="mb-8 flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <Crosshair size={14} style={{ color: "#06b6d4" }} />
            <span className="text-[10px] font-bold uppercase" style={{ color: "#06b6d4", letterSpacing: "0.15em" }}>
              Security Operations
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight mb-1.5 grad-text">
            Threat Dashboard
          </h1>
          <p className="text-[13px]" style={{ color: "#64748b" }}>
            Real-time overview of your phishing detection activity.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <div
            className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg"
            style={{
              background: apiStatus === "online" ? "rgba(16,185,129,0.08)" : apiStatus === "offline" ? "rgba(239,68,68,0.08)" : "rgba(245,158,11,0.08)",
              border: `1px solid ${apiStatus === "online" ? "rgba(16,185,129,0.2)" : apiStatus === "offline" ? "rgba(239,68,68,0.2)" : "rgba(245,158,11,0.2)"}`,
            }}
          >
            {apiStatus === "checking" ? (
              <><Activity size={13} className="text-yellow-400 animate-pulse" /> <span className="text-yellow-400">Checking...</span></>
            ) : apiStatus === "online" ? (
              <><Wifi size={13} className="text-emerald-400" /> <span className="text-emerald-400">API Online</span></>
            ) : (
              <><WifiOff size={13} className="text-red-400" /> <span className="text-red-400">API Offline</span></>
            )}
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-3.5 mb-6">
        <StatCard
          label="Total Scans"
          value={stats.totalScanned}
          icon={<Search size={18} />}
          color="#06b6d4"
          borderColor="#06b6d4"
        />
        <StatCard
          label="Threats Found"
          value={stats.phishingCount}
          icon={<ShieldAlert size={18} />}
          color="#ef4444"
          borderColor="#ef4444"
          sub={`${phishRate}%`}
        />
        <StatCard
          label="Safe URLs"
          value={stats.safeCount}
          icon={<ShieldCheck size={18} />}
          color="#10b981"
          borderColor="#10b981"
          sub={`${safeRate}%`}
        />
        <StatCard
          label="Threat Rate"
          value={`${phishRate}%`}
          icon={<TrendingUp size={18} />}
          color="#a78bfa"
          borderColor="#a78bfa"
        />
      </div>

      {/* Breakdown + Last scanned */}
      <div className="grid grid-cols-2 gap-3.5 mb-6">

        {/* Threat Analysis */}
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 size={14} style={{ color: "#475569" }} />
            <span className="text-[11px] uppercase font-bold" style={{ color: "#475569", letterSpacing: "0.1em" }}>
              Threat Analysis
            </span>
          </div>
          {stats.totalScanned === 0 ? (
            <div className="text-[13px] text-center py-8" style={{ color: "#334155" }}>
              No scans yet — try the URL Scanner
            </div>
          ) : (
            <>
              <div className="flex justify-between mb-2 items-center">
                <span className="text-[13px]" style={{ color: "#94a3b8" }}>Safe</span>
                <span className="text-[13px] font-bold" style={{ color: "#10b981" }}>{safeRate}%</span>
              </div>
              <div className="rounded-lg h-2 overflow-hidden mb-5" style={{ background: "#0f172a" }}>
                <div
                  className="h-full rounded-lg transition-all duration-700"
                  style={{
                    width: `${safeRate}%`,
                    background: "linear-gradient(90deg, #059669, #10b981, #34d399)",
                    boxShadow: "0 0 12px rgba(16,185,129,0.3)",
                  }}
                />
              </div>
              <div className="flex justify-between mb-2 items-center">
                <span className="text-[13px]" style={{ color: "#94a3b8" }}>Phishing</span>
                <span className="text-[13px] font-bold" style={{ color: "#ef4444" }}>{phishRate}%</span>
              </div>
              <div className="rounded-lg h-2 overflow-hidden" style={{ background: "#0f172a" }}>
                <div
                  className="h-full rounded-lg transition-all duration-700"
                  style={{
                    width: `${phishRate}%`,
                    background: "linear-gradient(90deg, #b91c1c, #ef4444, #f87171)",
                    boxShadow: "0 0 12px rgba(239,68,68,0.3)",
                  }}
                />
              </div>
            </>
          )}
        </div>

        {/* Last Scanned URL */}
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock size={14} style={{ color: "#475569" }} />
            <span className="text-[11px] uppercase font-bold" style={{ color: "#475569", letterSpacing: "0.1em" }}>
              Last Scanned URL
            </span>
          </div>
          <div
            className="rounded-lg p-3.5 font-mono text-xs break-all leading-relaxed min-h-[52px]"
            style={{
              background: "#0f172a",
              border: "1px solid rgba(148,163,184,0.06)",
              color: "#94a3b8",
            }}
          >
            {stats.lastUrl || <span style={{ color: "#334155" }}>No scans yet</span>}
          </div>
          {stats.totalScanned > 0 && (
            <button
              onClick={clearData}
              className="mt-4 px-4 py-1.5 rounded-lg bg-transparent text-xs font-semibold cursor-pointer flex items-center gap-1.5 transition-all duration-200"
              style={{
                color: "#64748b",
                border: "1px solid rgba(148,163,184,0.1)",
              }}
              onMouseEnter={e => { e.currentTarget.style.color = "#e2e8f0"; e.currentTarget.style.borderColor = "rgba(148,163,184,0.2)"; }}
              onMouseLeave={e => { e.currentTarget.style.color = "#64748b"; e.currentTarget.style.borderColor = "rgba(148,163,184,0.1)"; }}
            >
              <Trash2 size={12} />
              Clear all data
            </button>
          )}
        </div>
      </div>

      {/* Activity Log */}
      {history.length > 0 && (
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={14} style={{ color: "#475569" }} />
            <span className="text-[11px] uppercase font-bold" style={{ color: "#475569", letterSpacing: "0.1em" }}>
              Activity Log
            </span>
            <span className="text-[10px] font-medium ml-auto px-2 py-0.5 rounded-md" style={{ color: "#64748b", background: "rgba(148,163,184,0.06)" }}>
              {history.length} entries
            </span>
          </div>

          {/* Table header */}
          <div
            className="flex items-center gap-3 px-3 py-2 rounded-lg mb-1 text-[10px] font-bold uppercase"
            style={{ color: "#334155", letterSpacing: "0.1em" }}
          >
            <span className="w-14 shrink-0">Status</span>
            <span className="flex-1">URL</span>
            <span className="w-14 text-right shrink-0">Score</span>
            <span className="w-16 text-right shrink-0">Time</span>
          </div>

          <div className="flex flex-col gap-0.5">
            {history.slice(0, 10).map((entry, i) => (
              <div
                key={i}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150"
                style={{ background: i % 2 === 0 ? "rgba(15,23,42,0.4)" : "transparent" }}
              >
                <span
                  className="text-[10px] font-bold px-2 py-0.5 rounded-md shrink-0 uppercase w-14 text-center"
                  style={{
                    letterSpacing: "0.05em",
                    background: entry.result === "phishing" ? "rgba(239,68,68,0.12)" : "rgba(16,185,129,0.12)",
                    color: entry.result === "phishing" ? "#f87171" : "#34d399",
                    border: `1px solid ${entry.result === "phishing" ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)"}`,
                  }}
                >
                  {entry.result === "phishing" ? "Threat" : "Safe"}
                </span>
                <span className="flex-1 text-[13px] overflow-hidden text-ellipsis whitespace-nowrap font-mono" style={{ color: "#64748b" }}>
                  {entry.url}
                </span>
                <span className="text-xs font-bold shrink-0 w-14 text-right" style={{ color: "#94a3b8" }}>
                  {Math.round(entry.confidence)}%
                </span>
                <span className="text-xs shrink-0 w-16 text-right" style={{ color: "#334155" }}>
                  {timeAgo(entry.ts)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
