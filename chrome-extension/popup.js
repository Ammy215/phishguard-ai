const API_BASE = "http://127.0.0.1:5000";

const RISK_COLORS = {
  safe: "#22c55e", low: "#84cc16", medium: "#f59e0b", high: "#f97316", critical: "#ef4444",
};

// Get and display current tab URL on popup open
chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
  const url = tabs[0] && tabs[0].url ? tabs[0].url : "";
  document.getElementById("urlDisplay").textContent = url || "No URL detected";
});

document.getElementById("checkBtn").addEventListener("click", async function() {
  const btn = document.getElementById("checkBtn");
  const errorMsg = document.getElementById("errorMsg");
  const resultCard = document.getElementById("resultCard");

  // Reset
  resultCard.className = "result-card";
  errorMsg.className = "error-msg";

  // Get current tab URL
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tabs[0] && tabs[0].url ? tabs[0].url : "";

  if (!url || url.startsWith("chrome://") || url.startsWith("chrome-extension://")) {
    errorMsg.textContent = "Cannot scan browser internal pages.";
    errorMsg.className = "error-msg show";
    return;
  }

  btn.disabled = true;
  btn.textContent = "Scanning...";

  try {
    const response = await fetch(API_BASE + "/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url }),
    });

    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }

    const data = await response.json();
    const isPhishing = data.result === "phishing";
    const riskColor = RISK_COLORS[data.risk_level] || "#6b7280";

    // Show result card
    resultCard.className = "result-card show " + (isPhishing ? "danger" : "safe");

    // Badge
    const badge = document.getElementById("resultBadge");
    badge.className = "result-badge " + (isPhishing ? "danger" : "safe");
    badge.textContent = isPhishing ? "PHISHING DETECTED" : "LOOKS LEGITIMATE";

    // Confidence
    document.getElementById("confidence").textContent = data.confidence + "%";

    // Risk bar
    const barFill = document.getElementById("riskBarFill");
    barFill.style.width = data.confidence + "%";
    barFill.style.background = isPhishing
      ? "linear-gradient(90deg, #dc2626, #f87171)"
      : "linear-gradient(90deg, #059669, #34d399)";

    // Risk level
    const riskLabel = document.getElementById("riskLevel");
    riskLabel.textContent = (data.risk_level || "unknown").toUpperCase() + " RISK";
    riskLabel.style.color = riskColor;

    // Scores
    document.getElementById("mlScore").textContent = data.ml_score + "%";
    document.getElementById("ruleScore").textContent = data.rule_score + "/100";

    // Flags
    const flagsSection = document.getElementById("flagsSection");
    flagsSection.innerHTML = "";

    if (data.flags && data.flags.length > 0) {
      data.flags.forEach(function(flag) {
        const div = document.createElement("div");
        div.className = "flag-item";
        div.innerHTML = '<span class="flag-icon">&#9873;</span> ' + flag;
        flagsSection.appendChild(div);
      });
    }

  } catch (error) {
    errorMsg.textContent = "Could not connect to PhishGuard API. Make sure Flask is running on localhost:5000.";
    errorMsg.className = "error-msg show";
  } finally {
    btn.disabled = false;
    btn.textContent = "Scan This Website";
  }
});
