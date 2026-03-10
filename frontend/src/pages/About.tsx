const About = () => {
  const card: React.CSSProperties = {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 14,
    padding: "24px 28px",
    marginBottom: 16,
  };

  const tech: { label: string; desc: string; color: string }[] = [
    { label: "Python + Flask",     desc: "REST API backend serving ML predictions and heuristic analysis", color: "#f59e0b" },
    { label: "Random Forest ML",   desc: "Trained on PhiUSIIL phishing dataset with 6 URL-derived features",  color: "#34d399" },
    { label: "Heuristic Engine",   desc: "14-rule scoring system covering IPs, TLDs, keywords, structure",    color: "#818cf8" },
    { label: "React + TypeScript", desc: "Fully typed frontend with Vite for fast dev/build cycles",          color: "#22d3ee" },
    { label: "Chrome Extension",   desc: "Browser-level phishing warnings with popup UI",                     color: "#f87171" },
  ];

  return (
    <div style={{ maxWidth: 780, margin: "0 auto", animation: "fadeIn 0.3s ease" }}>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.5px", marginBottom: 6 }}>
          <span style={{ background: "linear-gradient(135deg, #f1f5f9, #94a3b8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            About PhishGuard AI
          </span>
        </h1>
        <p style={{ color: "#475569", fontSize: 14 }}>
          An end-to-end phishing detection platform combining machine learning and rule-based analysis.
        </p>
      </div>

      {/* Overview */}
      <div style={card}>
        <div style={{ fontSize: 11, color: "#475569", textTransform: "uppercase" as const, letterSpacing: "1.2px", fontWeight: 700, marginBottom: 14 }}>
          How It Works
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          {[
            { step: "01", title: "Extract Features", desc: "URL length, domain, TLD, subdomains, HTTPS, IP usage" },
            { step: "02", title: "ML Prediction",    desc: "Random Forest model outputs a phishing probability (0–100%)" },
            { step: "03", title: "Rule Engine",      desc: "14 heuristic checks score the URL for known attack patterns" },
          ].map(({ step, title, desc }) => (
            <div key={step} style={{
              background: "#0d1117",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 10,
              padding: "16px 18px",
            }}>
              <div style={{ fontSize: 11, color: "#334155", fontWeight: 800, letterSpacing: "1px", marginBottom: 8 }}>{step}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#e2e8f0", marginBottom: 6 }}>{title}</div>
              <div style={{ fontSize: 12, color: "#475569", lineHeight: 1.5 }}>{desc}</div>
            </div>
          ))}
        </div>

        <div style={{
          marginTop: 16,
          padding: "14px 18px",
          background: "rgba(99,102,241,0.07)",
          border: "1px solid rgba(99,102,241,0.18)",
          borderRadius: 10,
          display: "flex", alignItems: "center", gap: 12,
        }}>
          <span style={{ fontSize: 13, color: "#818cf8", fontWeight: 700 }}>Combined Score</span>
          <span style={{ color: "#475569", fontSize: 13 }}>=</span>
          <span style={{ fontSize: 13, color: "#94a3b8" }}>50% ML score + 50% Heuristic score → flagged phishing if ≥ 35% or heuristic ≥ 35/100</span>
        </div>
      </div>

      {/* Tech stack */}
      <div style={card}>
        <div style={{ fontSize: 11, color: "#475569", textTransform: "uppercase" as const, letterSpacing: "1.2px", fontWeight: 700, marginBottom: 14 }}>
          Technology Stack
        </div>
        <div style={{ display: "flex", flexDirection: "column" as const, gap: 8 }}>
          {tech.map(({ label, desc, color }) => (
            <div key={label} style={{
              display: "flex", alignItems: "center", gap: 14,
              padding: "12px 14px",
              background: "#0d1117",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 9,
            }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: color,
                flexShrink: 0,
                boxShadow: `0 0 8px ${color}88`,
              }} />
              <div style={{ fontWeight: 600, fontSize: 13, color: "#e2e8f0", minWidth: 160 }}>{label}</div>
              <div style={{ fontSize: 12, color: "#475569" }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{
        ...card,
        background: "rgba(245,158,11,0.05)",
        border: "1px solid rgba(245,158,11,0.15)",
      }}>
        <div style={{ fontSize: 11, color: "#92400e", textTransform: "uppercase" as const, letterSpacing: "1.2px", fontWeight: 700, marginBottom: 10 }}>
          Disclaimer
        </div>
        <p style={{ fontSize: 13, color: "#78716c", lineHeight: 1.7 }}>
          PhishGuard AI is an educational tool. No detection system is 100% accurate.
          Always verify URLs independently and never enter sensitive information on unfamiliar sites.
          The ML model was trained on a specific dataset and may not generalise to all attack variants.
        </p>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default About;

