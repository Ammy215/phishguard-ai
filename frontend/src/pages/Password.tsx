import { useState } from "react";
import {
  Eye, EyeOff, ShieldCheck, ShieldAlert, Lock, AlertTriangle,
  CheckCircle2, XCircle, Lightbulb, Copy, Check, RefreshCw, Crosshair
} from "lucide-react";

// -- Scoring -----------------------------------------------------------------
const COMMON_PASSWORDS = new Set([
  "password","123456","123456789","qwerty","abc123","password1","iloveyou",
  "admin","letmein","welcome","monkey","dragon","master","sunshine","princess",
  "12345678","football","shadow","trustno1","iloveyou1","batman","access",
  "hello","charlie","donald","passw0rd","login","admin123","root","toor",
  "1234","12345","1234567","123123","654321","111111","000000","password123",
  "qwerty123","aa123456","abc1234","password1234","qwertyuiop",
]);

interface StrengthResult {
  score:       number;
  label:       string;
  color:       string;
  suggestions: string[];
}

function evaluatePassword(pw: string): StrengthResult {
  const suggestions: string[] = [];
  let score = 0;

  if (!pw) return { score: 0, label: "--", color: "#6b7280", suggestions: [] };

  if (pw.length >= 8)  score += 10; else suggestions.push("Use at least 8 characters");
  if (pw.length >= 12) score += 15; else if (pw.length >= 8) suggestions.push("12+ characters adds significant strength");
  if (pw.length >= 16) score += 10;
  if (pw.length >= 20) score += 5;

  const hasLower   = /[a-z]/.test(pw);
  const hasUpper   = /[A-Z]/.test(pw);
  const hasDigit   = /[0-9]/.test(pw);
  const hasSpecial = /[^a-zA-Z0-9]/.test(pw);

  if (hasLower)   score += 10; else suggestions.push("Add lowercase letters (a-z)");
  if (hasUpper)   score += 15; else suggestions.push("Add uppercase letters (A-Z)");
  if (hasDigit)   score += 15; else suggestions.push("Add numbers (0-9)");
  if (hasSpecial) score += 20; else suggestions.push("Add symbols (!@#$%^&*)");

  if (hasLower && hasUpper && hasDigit && hasSpecial) score += 10;

  const uniqueChars = new Set(pw).size;
  if (uniqueChars >= 10) score += 5;

  if (COMMON_PASSWORDS.has(pw.toLowerCase())) {
    score = 5;
    suggestions.length = 0;
    suggestions.push("This is one of the most common passwords — change it immediately!");
  }
  if (/(.)\1{2,}/.test(pw)) {
    score -= 10;
    suggestions.push("Avoid repeating characters (e.g. 'aaa')");
  }
  if (/^[a-zA-Z]+$/.test(pw)) {
    score -= 5;
    suggestions.push("Mixing letters with numbers/symbols is much stronger");
  }
  if (/^[0-9]+$/.test(pw)) {
    score -= 10;
    suggestions.push("A numeric-only password is easy to brute-force");
  }
  if (/(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)/i.test(pw)) {
    score -= 5;
    suggestions.push("Avoid sequential characters (abc, 123)");
  }
  if (/(?:qwert|asdf|zxcv|qazwsx)/i.test(pw)) {
    score -= 10;
    suggestions.push("Avoid keyboard patterns (qwerty, asdf)");
  }

  score = Math.max(0, Math.min(100, score));

  let label = "Very Weak";
  let color = "#ef4444";
  if (score >= 80) { label = "Strong";      color = "#10b981"; }
  else if (score >= 60) { label = "Good";   color = "#84cc16"; }
  else if (score >= 40) { label = "Fair";   color = "#f59e0b"; }
  else if (score >= 20) { label = "Weak";   color = "#f97316"; }

  return { score, label, color, suggestions };
}

function generatePassword(length = 16): string {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*_-+=";
  const arr = new Uint32Array(length);
  crypto.getRandomValues(arr);
  return Array.from(arr, v => chars[v % chars.length]).join("");
}

// -- Component ---------------------------------------------------------------
const Password = () => {
  const [pw,      setPw]      = useState("");
  const [visible, setVisible] = useState(false);
  const [copied,  setCopied]  = useState(false);
  const strength = evaluatePassword(pw);

  const handleGenerate = () => {
    const generated = generatePassword(20);
    setPw(generated);
    setVisible(true);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(pw);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const criteria = [
    { ok: pw.length >= 8,          text: "At least 8 characters",   icon: pw.length >= 8 ? CheckCircle2 : XCircle },
    { ok: pw.length >= 12,         text: "12+ characters",          icon: pw.length >= 12 ? CheckCircle2 : XCircle },
    { ok: /[a-z]/.test(pw),        text: "Lowercase letters",       icon: /[a-z]/.test(pw) ? CheckCircle2 : XCircle },
    { ok: /[A-Z]/.test(pw),        text: "Uppercase letters",       icon: /[A-Z]/.test(pw) ? CheckCircle2 : XCircle },
    { ok: /[0-9]/.test(pw),        text: "Numbers",                 icon: /[0-9]/.test(pw) ? CheckCircle2 : XCircle },
    { ok: /[^a-zA-Z0-9]/.test(pw), text: "Special symbols",         icon: /[^a-zA-Z0-9]/.test(pw) ? CheckCircle2 : XCircle },
  ];

  return (
    <div className="max-w-[720px] mx-auto animate-in">

      {/* Header */}
      <div className="mb-7">
        <div className="flex items-center gap-2.5 mb-2">
          <Crosshair size={14} style={{ color: "#06b6d4" }} />
          <span className="text-[10px] font-bold uppercase" style={{ color: "#06b6d4", letterSpacing: "0.15em" }}>
            Credential Analysis
          </span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight mb-1.5 grad-text">
          Password Auditor
        </h1>
        <p className="text-[13px] flex items-center gap-1.5" style={{ color: "#64748b" }}>
          <Lock size={13} />
          Check your password strength locally — nothing is sent to any server.
        </p>
      </div>

      {/* Input */}
      <div className="glass p-6 mb-4">
        <label className="text-[10px] uppercase font-bold block mb-3" style={{ color: "#475569", letterSpacing: "0.12em" }}>
          Your password
        </label>
        <div className="relative">
          <input
            className="w-full py-3 pl-4 pr-24 rounded-lg text-[15px] font-mono transition-all duration-200"
            style={{
              background: "#0f172a",
              border: "1px solid rgba(148,163,184,0.1)",
              color: "#e2e8f0",
              letterSpacing: "0.1em",
            }}
            type={visible ? "text" : "password"}
            placeholder="Enter a password to audit..."
            value={pw}
            onChange={e => setPw(e.target.value)}
            onFocus={e => e.currentTarget.style.borderColor = "rgba(6,182,212,0.4)"}
            onBlur={e => e.currentTarget.style.borderColor = "rgba(148,163,184,0.1)"}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {pw && (
              <button
                onClick={handleCopy}
                className="p-1.5 bg-transparent border-0 cursor-pointer transition-colors duration-200"
                style={{ color: "#64748b" }}
                title="Copy"
                onMouseEnter={e => e.currentTarget.style.color = "#e2e8f0"}
                onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
              >
                {copied ? <Check size={15} style={{ color: "#10b981" }} /> : <Copy size={15} />}
              </button>
            )}
            <button
              onClick={() => setVisible(v => !v)}
              className="p-1.5 bg-transparent border-0 cursor-pointer transition-colors duration-200"
              style={{ color: "#64748b" }}
              title={visible ? "Hide" : "Show"}
              onMouseEnter={e => e.currentTarget.style.color = "#e2e8f0"}
              onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
            >
              {visible ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          className="mt-3.5 px-4 py-1.5 rounded-lg bg-transparent text-xs font-semibold cursor-pointer flex items-center gap-1.5 transition-all duration-200"
          style={{ color: "#64748b", border: "1px solid rgba(148,163,184,0.1)" }}
          onMouseEnter={e => { e.currentTarget.style.color = "#e2e8f0"; e.currentTarget.style.borderColor = "rgba(148,163,184,0.2)"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "#64748b"; e.currentTarget.style.borderColor = "rgba(148,163,184,0.1)"; }}
        >
          <RefreshCw size={12} />
          Generate secure password
        </button>
      </div>

      {/* Results */}
      {pw.length > 0 && (
        <>
          {/* Strength meter */}
          <div className="glass p-6 mb-4" style={{ borderTop: `2px solid ${strength.color}` }}>
            <div className="flex justify-between items-center mb-4">
              <span className="text-[10px] uppercase font-bold" style={{ color: "#475569", letterSpacing: "0.12em" }}>
                Password Strength
              </span>
              <div className="flex items-center gap-2.5">
                {strength.score >= 60
                  ? <ShieldCheck size={18} style={{ color: strength.color }} />
                  : <ShieldAlert size={18} style={{ color: strength.color }} />
                }
                <span className="font-extrabold text-lg tracking-tight" style={{ color: strength.color }}>
                  {strength.label}
                </span>
              </div>
            </div>

            {/* Bar */}
            <div className="rounded-lg h-3 overflow-hidden mb-1.5" style={{ background: "#0f172a" }}>
              <div
                className="h-full rounded-lg transition-all duration-500"
                style={{
                  width: `${strength.score}%`,
                  background: `linear-gradient(90deg, ${strength.color}bb, ${strength.color})`,
                  boxShadow: `0 0 14px ${strength.color}44`,
                }}
              />
            </div>
            <div className="text-right text-xs font-semibold mb-5" style={{ color: "#334155" }}>
              {strength.score}/100
            </div>

            {/* Criteria */}
            <div className="grid grid-cols-2 gap-3">
              {criteria.map(({ ok, text, icon: Icon }) => (
                <div key={text} className="flex items-center gap-2.5 text-[13px]">
                  <Icon size={16} style={{ color: ok ? "#10b981" : "#1e293b" }} />
                  <span style={{ color: ok ? "#94a3b8" : "#334155" }}>{text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Suggestions */}
          {strength.suggestions.length > 0 && (
            <div className="glass p-6 mb-4" style={{ borderLeft: `3px solid ${strength.color}` }}>
              <div className="flex items-center gap-2 mb-3.5">
                <Lightbulb size={14} style={{ color: "#f59e0b" }} />
                <span className="text-[10px] uppercase font-bold" style={{ color: "#475569", letterSpacing: "0.12em" }}>
                  Improvement Tips
                </span>
              </div>
              {strength.suggestions.map((s, i) => (
                <div
                  key={i}
                  className="flex gap-2.5 py-2.5 text-[13px]"
                  style={{
                    color: "#94a3b8",
                    borderBottom: i < strength.suggestions.length - 1 ? "1px solid rgba(148,163,184,0.05)" : "none",
                  }}
                >
                  <AlertTriangle size={14} className="shrink-0 mt-0.5" style={{ color: "#f59e0b" }} />
                  {s}
                </div>
              ))}
            </div>
          )}

          {/* All good */}
          {strength.score >= 80 && strength.suggestions.length === 0 && (
            <div
              className="glass p-5 mb-4 flex gap-3 items-center"
              style={{ background: "rgba(16,185,129,0.05)", borderColor: "rgba(16,185,129,0.15)" }}
            >
              <ShieldCheck size={20} style={{ color: "#10b981" }} />
              <span className="font-semibold text-[13px]" style={{ color: "#34d399" }}>
                Excellent password! It meets all strength criteria.
              </span>
            </div>
          )}

          {/* Common password warning */}
          {COMMON_PASSWORDS.has(pw.toLowerCase()) && (
            <div
              className="glass p-5 mb-4 flex gap-3 items-center"
              style={{ background: "rgba(239,68,68,0.05)", borderColor: "rgba(239,68,68,0.2)" }}
            >
              <ShieldAlert size={20} style={{ color: "#ef4444" }} />
              <div>
                <div className="font-semibold text-[13px]" style={{ color: "#fca5a5" }}>Common Password Detected</div>
                <div className="text-xs mt-0.5" style={{ color: "rgba(252,165,165,0.6)" }}>
                  This password appears in breach databases and can be cracked instantly.
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Password;
