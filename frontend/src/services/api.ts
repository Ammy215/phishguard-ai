const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

// -- Types ------------------------------------------------------------------
export interface PredictResponse {
  url:            string;
  result:         "phishing" | "legitimate";
  confidence:     number;
  ml_score:       number;
  rule_score:     number;
  combined_score: number;
  risk_level:     "safe" | "low" | "medium" | "high" | "critical";
  flags:          string[];
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
