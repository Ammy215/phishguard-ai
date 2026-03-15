const RISK_COLORS = {
  safe: "#22c55e",
  low: "#84cc16",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
  suspicious: "#f59e0b",
  phishing: "#ef4444",
};

console.log("[PhishGuard] Popup script loaded");

function resetUi() {
  const resultCard = document.getElementById("resultCard");
  const errorMsg = document.getElementById("errorMsg");
  resultCard.className = "result-card";
  errorMsg.className = "error-msg";
}

function showError(message) {
  const errorMsg = document.getElementById("errorMsg");
  errorMsg.textContent = message;
  errorMsg.className = "error-msg show";
}

function renderResult(data) {
  if (!data || typeof data !== "object") {
    console.log("[PhishGuard] Invalid data to render:", data);
    return;
  }

  const resultCard = document.getElementById("resultCard");
  const isPhishing = data.result === "phishing";
  const riskLevel = String((data.risk_level_legacy || data.risk_level) || "unknown").toLowerCase();
  const riskColor = RISK_COLORS[riskLevel] || "#6b7280";

  console.log("[PhishGuard] Rendering result:", { isPhishing, riskLevel, result: data.result });

  resultCard.className = "result-card show " + (isPhishing ? "danger" : "safe");

  const badge = document.getElementById("resultBadge");
  if (badge) {
    badge.className = "result-badge " + (isPhishing ? "danger" : "safe");
    badge.textContent = isPhishing ? "PHISHING DETECTED" : "LOOKS LEGITIMATE";
  }

  const confidence = Number(data.confidence) || 0;
  const confElement = document.getElementById("confidence");
  if (confElement) confElement.textContent = confidence + "%";

  const barFill = document.getElementById("riskBarFill");
  if (barFill) {
    barFill.style.width = confidence + "%";
    barFill.style.background = isPhishing
      ? "linear-gradient(90deg, #dc2626, #f87171)"
      : "linear-gradient(90deg, #059669, #34d399)";
  }

  const riskLabel = document.getElementById("riskLevel");
  if (riskLabel) {
    riskLabel.textContent = String(data.risk_level || data.risk_level_legacy || "unknown").toUpperCase() + " RISK";
    riskLabel.style.color = riskColor;
  }

  const mlScore = document.getElementById("mlScore");
  if (mlScore) mlScore.textContent = (data.ml_score || 0) + "%";

  const ruleScore = document.getElementById("ruleScore");
  if (ruleScore) ruleScore.textContent = (data.rule_score || 0) + "/100";

  const flagsSection = document.getElementById("flagsSection");
  if (flagsSection) {
    flagsSection.innerHTML = "";
    if (data.flags && Array.isArray(data.flags) && data.flags.length > 0) {
      data.flags.forEach(function(flag) {
        const div = document.createElement("div");
        div.className = "flag-item";
        div.innerHTML = '<span class="flag-icon">&#9873;</span> ' + String(flag);
        flagsSection.appendChild(div);
      });
    }
  }
}

// On popup open: get active tab and load cached result if available
console.log("[PhishGuard] Popup opening, checking for cached scan...");

chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
  if (!tabs || tabs.length === 0) {
    console.log("[PhishGuard] No active tab found");
    return;
  }

  const tabId = tabs[0].id;
  const url = tabs[0].url;
  console.log("[PhishGuard] Active tab ID:", tabId, "URL:", url);

  // Display the URL
  const urlDisplay = document.getElementById("urlDisplay");
  if (urlDisplay) urlDisplay.textContent = url || "No URL detected";

  // Try to load cached scan result
  chrome.storage.local.get([String(tabId)], function(result) {
    console.log("[PhishGuard] Storage check result:", result);
    if (result[String(tabId)]) {
      console.log("[PhishGuard] Found cached scan, displaying result");
      renderResult(result[String(tabId)]);
    } else {
      console.log("[PhishGuard] No cached scan found");
    }
  });
});

function requestBackgroundScan() {
  return new Promise((resolve) => {
    console.log("[PhishGuard] Requesting background scan...");
    chrome.runtime.sendMessage({ type: "SCAN_ACTIVE_TAB" }, (response) => {
      console.log("[PhishGuard] Background scan response:", response);
      if (chrome.runtime.lastError) {
        console.error("[PhishGuard] Message error:", chrome.runtime.lastError);
        resolve({ error: chrome.runtime.lastError.message });
        return;
      }
      resolve(response || { error: "No response from background worker" });
    });
  });
}

document.getElementById("checkBtn").addEventListener("click", async function() {
  const btn = document.getElementById("checkBtn");
  console.log("[PhishGuard] Manual scan button clicked");
  resetUi();

  btn.disabled = true;
  btn.textContent = "Scanning...";

  try {
    const response = await requestBackgroundScan();
    console.log("[PhishGuard] Manual scan response:", response);
    if (response && response.result) {
      renderResult(response);
    } else if (response && response.error) {
      showError("Scan error: " + response.error);
    } else {
      showError("Could not connect to PhishGuard API. Make sure Flask is running on localhost:5000.");
    }
  } catch (error) {
    console.error("[PhishGuard] Manual scan error:", error);
    showError("Could not connect to PhishGuard API. Make sure Flask is running on localhost:5000.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Scan This Website";
  }
});
