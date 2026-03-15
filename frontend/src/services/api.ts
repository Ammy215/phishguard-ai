const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

// -- Types ------------------------------------------------------------------
export interface ThreatCheck {
  status: "ok" | "error" | "unavailable";
  risk: number;
  details: string;
  [key: string]: any;
}

export interface ThreatChecks {
  whois_age?: ThreatCheck & { age_days?: number };
  google_safe_browsing?: ThreatCheck & { flagged?: boolean };
  phishtank?: ThreatCheck & { found?: boolean };
  domain_similarity?: ThreatCheck & { is_similar?: boolean; matched_brand?: string; similarity?: number };
  redirects?: ThreatCheck & { redirect_count?: number; final_url?: string };
  shortened_url?: ThreatCheck & { is_shortened?: boolean; shortener?: string; expanded_url?: string };
  openphish?: ThreatCheck & { found?: boolean };
}

export interface PredictResponse {
  url:               string;
  result:            "phishing" | "legitimate";
  confidence:        number;
  ml_score:          number;
  rule_score:        number;
  combined_score:    number;
  risk_level:        "safe" | "low" | "medium" | "high" | "critical";
  risk_level_normalized?: "SAFE" | "SUSPICIOUS" | "PHISHING";
  ml_prediction?:    string;
  risk_score?:       number;
  flags:             string[];
  checks?:           ThreatChecks;
}

export interface ChatResponse {
  explanation: string;
}

export interface WhoisResponse {
  domain:       string;
  scheme:       string;
  port:         number | null;
  ip_addresses: string[];
  is_trusted:   boolean;
  lookup_time:  string;
  dns_error?:   string;
}

// -- /predict ---------------------------------------------------------------
export async function scanUrl(url: string): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error ?? `HTTP ${res.status}`);
  }
  return res.json();
}

// -- /chat ------------------------------------------------------------------
export async function explainResult(
  result:     string,
  confidence: number,
  flags:      string[],
  url:        string,
  risk_level: string,
  ml_score:   number,
  rule_score: number,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ result, confidence, flags, url, risk_level, ml_score, rule_score }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// -- /whois -----------------------------------------------------------------
export async function whoisLookup(url: string): Promise<WhoisResponse> {
  const res = await fetch(`${API_BASE}/whois`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// -- /health ----------------------------------------------------------------
export async function healthCheck(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
