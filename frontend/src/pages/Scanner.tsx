import { useState } from "react";
import { scanUrl, explainResult, whoisLookup } from "../services/api";
import type { PredictResponse, WhoisResponse } from "../services/api";
import {
  Search, ShieldCheck, ShieldAlert, AlertTriangle, Flag, Brain,
  Activity, Cpu, Globe, Loader2, ExternalLink, Info, ChevronDown,
  ChevronUp, Server, Crosshair,
} from "lucide-react";

// -- helpers ----------------------------------------------------------------
function saveToHistory(entry: { url: string; result: string; confidence: number }) {
  const raw  = localStorage.getItem("scanHistory") ?? "[]";
  const list = JSON.parse(raw) as (typeof entry & { ts: number })[];
  list.unshift({ ...entry, ts: Date.now() });
  localStorage.setItem("scanHistory", JSON.stringify(list.slice(0, 50)));
  const total    = parseInt(localStorage.getItem("totalScanned")  ?? "0") + 1;
  const phishing = parseInt(localStorage.getItem("phishingCount") ?? "0") + (entry.result === "phishing" ? 1 : 0);
  localStorage.setItem("totalScanned",  String(total));
  localStorage.setItem("phishingCount", String(phishing));
  localStorage.setItem("lastUrl",       entry.url);
}

const RISK_COLORS: Record<string, string> = {
  safe: "#10b981", low: "#84cc16", medium: "#f59e0b", high: "#f97316", critical: "#ef4444",
};

function riskGradient(level: string) {
  const c = RISK_COLORS[level] || "#6b7280";
  return `linear-gradient(90deg, ${c}cc, ${c})`;
}

function ExplanationText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="text-[13px] leading-relaxed" style={{ color: "#94a3b8" }}>
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-2" />;
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        const rendered = parts.map((part, j) =>
          part.startsWith("**") && part.endsWith("**")
            ? <strong key={j} className="font-semibold" style={{ color: "#e2e8f0" }}>{part.slice(2, -2)}</strong>
            : part
        );
        if (line.trim().startsWith("*") && !line.trim().startsWith("**")) {
          return (
            <div key={i} className="flex gap-2 py-0.5 pl-2">
              <span style={{ color: "#06b6d4" }} className="shrink-0">{"›"}</span>
              <span>{rendered}</span>
            </div>
          );
        }
        return <div key={i}>{rendered}</div>;
      })}
    </div>
  );
}

// -- component --------------------------------------------------------------
const Scanner = () => {
  const [url,         setUrl]         = useState("");
  const [loading,     setLoading]     = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [result,      setResult]      = useState<PredictResponse | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [whoisData,   setWhoisData]   = useState<WhoisResponse | null>(null);
  const [whoisOpen,   setWhoisOpen]   = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  const handleScan = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    setLoading(true);
    setResult(null);
    setExplanation(null);
    setWhoisData(null);
    setWhoisOpen(false);
    setError(null);

    try {
      const data = await scanUrl(trimmed);
      setResult(data);
      saveToHistory({ url: data.url, result: data.result, confidence: data.confidence });

      setChatLoading(true);
      const chat = await explainResult(
        data.result, data.confidence, data.flags, data.url,
        data.risk_level, data.ml_score, data.rule_score,
      );
      setExplanation(chat.explanation);

      whoisLookup(data.url).then(setWhoisData).catch(() => {});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not reach backend. Is Flask running?");
    } finally {
      setLoading(false);
      setChatLoading(false);
    }
  };

  const isPhishing = result?.result === "phishing";
  const riskColor  = result ? (RISK_COLORS[result.risk_level] || "#6b7280") : "#6b7280";

  return (
    <div className="max-w-[880px] mx-auto animate-in">

      {/* Header */}
      <div className="mb-7">
        <div className="flex items-center gap-2.5 mb-2">
          <Crosshair size={14} style={{ color: "#06b6d4" }} />
          <span className="text-[10px] font-bold uppercase" style={{ color: "#06b6d4", letterSpacing: "0.15em" }}>
            Threat Analysis
          </span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight mb-1.5 grad-text">
          URL Scanner
        </h1>
        <p className="text-[13px]" style={{ color: "#64748b" }}>
          Analyze any URL using machine learning and heuristic rule engine.
        </p>
      </div>

      {/* Input card */}
      <div className="glass p-6 mb-4">
        <label className="text-[10px] uppercase font-bold block mb-3" style={{ color: "#475569", letterSpacing: "0.12em" }}>
          Target URL
        </label>
        <div className="flex gap-2.5">
          <div className="flex-1 relative">
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "#334155" }}>
              <Globe size={16} />
            </div>
            <input
              className="w-full py-3 pl-10 pr-4 rounded-lg text-[13px] font-mono transition-all duration-200"
              style={{
                background: "#0f172a",
                border: "1px solid rgba(148,163,184,0.1)",
                color: "#e2e8f0",
              }}
              type="text"
              placeholder="https://example.com/login"
              value={url}
              onChange={e => setUrl(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleScan()}
              onFocus={e => e.currentTarget.style.borderColor = "rgba(6,182,212,0.4)"}
              onBlur={e => e.currentTarget.style.borderColor = "rgba(148,163,184,0.1)"}
            />
            {loading && (
              <div className="absolute inset-0 rounded-lg overflow-hidden pointer-events-none">
                <div
                  className="absolute top-0 left-0 w-[30%] h-full"
                  style={{
                    background: "linear-gradient(90deg, transparent, rgba(6,182,212,0.12), transparent)",
                    animation: "scan-line 1.2s ease-in-out infinite",
                  }}
                />
              </div>
            )}
          </div>
          <button
            onClick={handleScan}
            disabled={loading || !url.trim()}
            className="px-6 py-3 rounded-lg border-0 text-white font-semibold text-[13px] whitespace-nowrap tracking-tight transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            style={{
              background: loading ? "rgba(6,182,212,0.3)" : "linear-gradient(135deg, #0891b2, #06b6d4)",
              cursor: loading ? "wait" : "pointer",
              boxShadow: loading ? "none" : "0 0 24px rgba(6,182,212,0.25)",
            }}
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            {loading ? "Scanning..." : "Analyze"}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div
          className="glass p-5 mb-4 flex gap-3 items-start"
          style={{ background: "rgba(239,68,68,0.06)", borderColor: "rgba(239,68,68,0.2)" }}
        >
          <AlertTriangle size={18} className="shrink-0 mt-0.5" style={{ color: "#ef4444" }} />
          <div>
            <div className="font-semibold text-[13px] mb-0.5" style={{ color: "#fca5a5" }}>Connection Error</div>
            <div className="text-[12px]" style={{ color: "rgba(252,165,165,0.7)" }}>{error}</div>
          </div>
        </div>
      )}

      {/* Result card */}
      {result && (
        <div
          className="glass p-6 mb-4 animate-in"
          style={{
            borderColor: isPhishing ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)",
            borderTop: `2px solid ${isPhishing ? "#ef4444" : "#10b981"}`,
          }}
        >
          {/* Header: badge + risk */}
          <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
            <div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-[13px]"
              style={{
                background: isPhishing ? "rgba(239,68,68,0.1)" : "rgba(16,185,129,0.1)",
                border: `1px solid ${isPhishing ? "rgba(239,68,68,0.25)" : "rgba(16,185,129,0.25)"}`,
                color: isPhishing ? "#f87171" : "#34d399",
                letterSpacing: "0.05em",
              }}
            >
              {isPhishing ? <ShieldAlert size={18} /> : <ShieldCheck size={18} />}
              {isPhishing ? "THREAT DETECTED" : "LOOKS LEGITIMATE"}
            </div>
            <div className="flex items-center gap-2.5">
              <span className="text-[11px] uppercase font-bold" style={{ color: riskColor, letterSpacing: "0.1em" }}>
                {result.risk_level} risk
              </span>
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: riskColor, boxShadow: `0 0 10px ${riskColor}88` }}
              />
            </div>
          </div>

          {/* Scanned URL */}
          <div
            className="flex items-center gap-2 mb-5 px-3.5 py-2.5 rounded-lg"
            style={{ background: "#0f172a", border: "1px solid rgba(148,163,184,0.06)" }}
          >
            <ExternalLink size={13} style={{ color: "#334155" }} className="shrink-0" />
            <span className="text-xs font-mono break-all" style={{ color: "#64748b" }}>{result.url}</span>
          </div>

          {/* Risk meter */}
          <div className="mb-6">
            <div className="flex justify-between mb-2 items-center">
              <span className="text-[10px] uppercase font-bold" style={{ color: "#475569", letterSpacing: "0.12em" }}>
                Combined Risk Score
              </span>
              <span className="font-extrabold text-2xl tracking-tight" style={{ color: riskColor }}>
                {result.confidence}%
              </span>
            </div>
            <div className="rounded-lg h-2.5 overflow-hidden" style={{ background: "#0f172a" }}>
              <div
                className="h-full rounded-lg transition-all duration-700 ease-out"
                style={{
                  width: `${result.confidence}%`,
                  background: riskGradient(result.risk_level),
                  boxShadow: `0 0 16px ${riskColor}44`,
                }}
              />
            </div>
          </div>

          {/* Score breakdown */}
          <div className="grid grid-cols-4 gap-3 mb-5">
            {[
              { label: "ML Model",  value: `${result.ml_score}%`,       icon: <Cpu size={16} />,      color: "#06b6d4" },
              { label: "Rules",     value: `${result.rule_score}/100`,   icon: <Activity size={16} />, color: "#a78bfa" },
              { label: "Combined",  value: `${result.combined_score}%`,  icon: <Brain size={16} />,    color: "#f59e0b" },
              { label: "Flags",     value: `${result.flags.length}`,     icon: <Flag size={16} />,     color: "#fb923c" },
            ].map(({ label, value, icon, color }) => (
              <div
                key={label}
                className="rounded-xl p-3.5 text-center"
                style={{
                  background: "#0f172a",
                  border: "1px solid rgba(148,163,184,0.06)",
                }}
              >
                <div className="flex justify-center mb-2" style={{ color }}>{icon}</div>
                <div className="text-xl font-extrabold tracking-tight" style={{ color }}>{value}</div>
                <div className="text-[10px] font-semibold uppercase mt-1" style={{ color: "#475569", letterSpacing: "0.08em" }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Flags */}
          {result.flags.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-bold mb-2.5" style={{ color: "#475569", letterSpacing: "0.12em" }}>
                Detection Flags
              </div>
              <div className="flex flex-col gap-1.5">
                {result.flags.map((flag, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-[13px]"
                    style={{
                      background: isPhishing ? "rgba(239,68,68,0.04)" : "rgba(245,158,11,0.04)",
                      border: `1px solid ${isPhishing ? "rgba(239,68,68,0.1)" : "rgba(245,158,11,0.1)"}`,
                      color: isPhishing ? "#fca5a5" : "#fcd34d",
                    }}
                  >
                    <AlertTriangle size={14} className="shrink-0" style={{ color: isPhishing ? "#ef4444" : "#f59e0b" }} />
                    {flag}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Threat Intelligence Checks */}
          {result?.checks && (
            <div className="mt-6 border-t border-gray-700 pt-6">
              <div className="flex items-center gap-2.5 mb-4">
                <div
                  className="w-5 h-5 rounded flex items-center justify-center text-xs font-bold"
                  style={{
                    background: "rgba(99, 102, 241, 0.2)",
                    color: "#818cf8",
                  }}
                >
                  ⚡
                </div>
                <span className="text-[10px] font-bold uppercase" style={{ color: "#475569", letterSpacing: "0.12em" }}>
                  Threat Intelligence
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                {/* WHOIS Age */}
                {result.checks.whois_age && (
                  <div
                    className="rounded-lg p-3.5"
                    style={{
                      background: "#0f172a",
                      border: "1px solid rgba(148,163,184,0.06)",
                    }}
                  >
                    <div className="text-[11px] font-bold mb-2" style={{ color: "#94a3b8" }}>
                      Domain Age
                    </div>
                    <div className="text-sm font-semibold" style={{
                      color: result.checks.whois_age.age_days && result.checks.whois_age.age_days < 180 ? "#f87171" : "#34d399"
                    }}>
                      {result.checks.whois_age.age_days ? `${result.checks.whois_age.age_days} days` : "Unknown"}
                    </div>
                    <div className="text-xs mt-1" style={{ color: "#64748b" }}>
                      {result.checks.whois_age.details}
                    </div>
                  </div>
                )}

                {/* Domain Similarity */}
                {result.checks.domain_similarity && (
                  <div
                    className="rounded-lg p-3.5"
                    style={{
                      background: "#0f172a",
                      border: `1px solid ${result.checks.domain_similarity.is_similar ? "rgba(239,68,68,0.15)" : "rgba(148,163,184,0.06)"}`,
                    }}
                  >
                    <div className="text-[11px] font-bold mb-2" style={{ color: "#94a3b8" }}>
                      Brand Similarity
                    </div>
                    <div className="text-sm font-semibold" style={{
                      color: result.checks.domain_similarity.is_similar ? "#f87171" : "#34d399"
                    }}>
                      {result.checks.domain_similarity.matched_brand ? `${result.checks.domain_similarity.matched_brand} (${((result.checks.domain_similarity.similarity ?? 0) * 100).toFixed(1)}%)` : "Clean"}
                    </div>
                    <div className="text-xs mt-1" style={{ color: "#64748b" }}>
                      {result.checks.domain_similarity.details}
                    </div>
                  </div>
                )}

                {/* PhishTank */}
                {result.checks.phishtank && (
                  <div
                    className="rounded-lg p-3.5"
                    style={{
                      background: "#0f172a",
                      border: `1px solid ${result.checks.phishtank.found ? "rgba(239,68,68,0.15)" : "rgba(148,163,184,0.06)"}`,
                    }}
                  >
                    <div className="text-[11px] font-bold mb-2" style={{ color: "#94a3b8" }}>
                      PhishTank
                    </div>
                    <div className="text-sm font-semibold" style={{
                      color: result.checks.phishtank.found ? "#f87171" : "#34d399"
                    }}>
                      {result.checks.phishtank.found ? "⚠️ Found" : "✓ Not found"}
                    </div>
                    <div className="text-xs mt-1" style={{ color: "#64748b" }}>
                      {result.checks.phishtank.details}
                    </div>
                  </div>
                )}

                {/* OpenPhish */}
                {result.checks.openphish && (
                  <div
                    className="rounded-lg p-3.5"
                    style={{
                      background: "#0f172a",
                      border: `1px solid ${result.checks.openphish.found ? "rgba(239,68,68,0.15)" : "rgba(148,163,184,0.06)"}`,
                    }}
                  >
                    <div className="text-[11px] font-bold mb-2" style={{ color: "#94a3b8" }}>
                      OpenPhish Feed
                    </div>
                    <div className="text-sm font-semibold" style={{
                      color: result.checks.openphish.found ? "#f87171" : "#34d399"
                    }}>
                      {result.checks.openphish.found ? "⚠️ Found" : "✓ Not found"}
                    </div>
                    <div className="text-xs mt-1" style={{ color: "#64748b" }}>
                      {result.checks.openphish.details}
                    </div>
                  </div>
                )}

                {/* Redirect Chain */}
                {result.checks.redirects && (
                  <div
                    className="rounded-lg p-3.5"
                    style={{
                      background: "#0f172a",
                      border: `1px solid ${(result.checks.redirects.redirect_count ?? 0) > 2 ? "rgba(245,158,11,0.15)" : "rgba(148,163,184,0.06)"}`,
                    }}
                  >
                    <div className="text-[11px] font-bold mb-2" style={{ color: "#94a3b8" }}>
                      Redirect Chain
                    </div>
                    <div className="text-sm font-semibold" style={{
                      color: (result.checks.redirects.redirect_count ?? 0) > 3 ? "#f87171" : ((result.checks.redirects.redirect_count ?? 0) > 2 ? "#f59e0b" : "#34d399")
                    }}>
                      {result.checks.redirects.redirect_count ?? 0} redirects
                    </div>
                    <div className="text-xs mt-1" style={{ color: "#64748b" }}>
                      {result.checks.redirects.details}
                    </div>
                  </div>
                )}

                {/* Shortened URL */}
                {result.checks.shortened_url && (
                  <div
                    className="rounded-lg p-3.5"
                    style={{
                      background: "#0f172a",
                      border: `1px solid ${result.checks.shortened_url.is_shortened ? "rgba(245,158,11,0.15)" : "rgba(148,163,184,0.06)"}`,
                    }}
                  >
                    <div className="text-[11px] font-bold mb-2" style={{ color: "#94a3b8" }}>
                      Shortened URL
                    </div>
                    <div className="text-sm font-semibold" style={{
                      color: result.checks.shortened_url.is_shortened ? "#f59e0b" : "#34d399"
                    }}>
                      {result.checks.shortened_url.is_shortened ? `⚠️ ${result.checks.shortened_url.shortener}` : "✓ No"}
                    </div>
                    <div className="text-xs mt-1" style={{ color: "#64748b" }}>
                      {result.checks.shortened_url.details}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* WHOIS */}
          {whoisData && (
            <div className="mt-5">
              <button
                onClick={() => setWhoisOpen(o => !o)}
                className="flex items-center gap-2 text-xs font-bold uppercase cursor-pointer bg-transparent border-0 p-0 transition-colors duration-200"
                style={{ color: "#64748b", letterSpacing: "0.08em" }}
                onMouseEnter={e => e.currentTarget.style.color = "#e2e8f0"}
                onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
              >
                <Server size={14} />
                Domain Intelligence
                {whoisOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              {whoisOpen && (
                <div
                  className="mt-3 rounded-lg p-4 grid grid-cols-2 gap-3 text-sm animate-in"
                  style={{ background: "#0f172a", border: "1px solid rgba(148,163,184,0.06)" }}
                >
                  <div>
                    <div className="text-[10px] uppercase mb-1" style={{ color: "#334155", letterSpacing: "0.1em" }}>Domain</div>
                    <div className="font-mono text-xs" style={{ color: "#94a3b8" }}>{whoisData.domain}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase mb-1" style={{ color: "#334155", letterSpacing: "0.1em" }}>Trusted</div>
                    <div style={{ color: whoisData.is_trusted ? "#34d399" : "#f87171" }}>
                      {whoisData.is_trusted ? "Yes" : "No"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase mb-1" style={{ color: "#334155", letterSpacing: "0.1em" }}>IP Addresses</div>
                    <div className="font-mono text-xs" style={{ color: "#64748b" }}>
                      {whoisData.ip_addresses.length > 0 ? whoisData.ip_addresses.join(", ") : "N/A"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase mb-1" style={{ color: "#334155", letterSpacing: "0.1em" }}>Protocol</div>
                    <div className="uppercase text-xs" style={{ color: "#64748b" }}>{whoisData.scheme}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* AI Explanation */}
      {(chatLoading || explanation) && (
        <div className="glass p-6 mb-4 animate-in" style={{ borderTop: "2px solid #6366f1" }}>
          <div className="flex items-center gap-2.5 mb-4">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{
                background: "linear-gradient(135deg, #6366f1, #06b6d4)",
                boxShadow: "0 0 16px rgba(99,102,241,0.25)",
              }}
            >
              <Brain size={14} className="text-white" />
            </div>
            <span className="text-[11px] font-bold uppercase" style={{ color: "#475569", letterSpacing: "0.12em" }}>
              AI Threat Analysis
            </span>
          </div>
          {chatLoading && !explanation ? (
            <div className="flex items-center gap-2.5 text-[13px]" style={{ color: "#64748b" }}>
              <Loader2 size={16} className="animate-spin" style={{ color: "#06b6d4" }} />
              Generating analysis...
            </div>
          ) : (
            explanation && <ExplanationText text={explanation} />
          )}
        </div>
      )}

      {/* Tips */}
      {!result && !loading && (
        <div className="glass p-6 animate-in">
          <div className="flex items-center gap-2 mb-4">
            <Info size={14} style={{ color: "#06b6d4" }} />
            <span className="text-[11px] font-bold uppercase" style={{ color: "#475569", letterSpacing: "0.12em" }}>
              Scanner Tips
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-[12px]" style={{ color: "#64748b" }}>
            {[
              { n: "01", t: "Paste full URLs including https:// for best accuracy" },
              { n: "02", t: "The scanner checks 16+ heuristic rules and ML patterns" },
              { n: "03", t: "Typosquatting detection catches brand impersonation" },
              { n: "04", t: "AI explains every detection in plain language" },
            ].map(({ n, t }) => (
              <div key={n} className="flex items-start gap-2.5">
                <span className="font-bold font-mono" style={{ color: "#06b6d4" }}>{n}</span>
                <span>{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Scanner;
