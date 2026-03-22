const API_ENDPOINTS = ["http://127.0.0.1:5000", "http://localhost:5000"];
const REQUEST_TIMEOUT_MS = 8000;

console.log("PhishGuard AI Background Service Worker Loaded");

async function fetchWithTimeout(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function predictUrl(targetUrl) {
  let lastError = null;

  for (const base of API_ENDPOINTS) {
    try {
      const res = await fetchWithTimeout(base + "/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: targetUrl }),
      });

      if (!res.ok) {
        const body = await res.text().catch(() => "");
        
        // 400 = client validation error (invalid URL format) - skip quietly
        if (res.status === 400) {
          console.warn("[PhishGuard] Skipping invalid URL format:", targetUrl);
          throw new Error("Invalid URL format - skipping");
        }
        
        throw new Error("Backend returned " + res.status + " " + res.statusText + (body ? " - " + body : ""));
      }

      return await res.json();
    } catch (err) {
      lastError = err;
      // Only log non-validation errors
      if (err.message !== "Invalid URL format - skipping") {
        console.warn("[PhishGuard] Backend attempt failed:", base, err && err.message ? err.message : err);
      }
    }
  }

  // If last error was validation, don't spam the user
  if (lastError && lastError.message === "Invalid URL format - skipping") {
    throw lastError;
  }

  const reason = lastError && lastError.message ? lastError.message : "Unknown network error";
  throw new Error(
    "Unable to reach local PhishGuard backend on port 5000. " +
      "Start backend/app.py and ensure firewall allows localhost. Last error: " +
      reason
  );
}

// Listen for page load completion and auto-scan
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only trigger on page completion
  if (changeInfo.status !== "complete" || !tab.url) {
    return;
  }

  // Skip internal Chrome pages
  if (
    tab.url.startsWith("chrome://") ||
    tab.url.startsWith("edge://") ||
    tab.url.startsWith("about:")
  ) {
    console.log("[PhishGuard] Skipping internal page:", tab.url);
    return;
  }

  // Only scan http/https URLs
  if (!tab.url.startsWith("http://") && !tab.url.startsWith("https://")) {
    console.log("[PhishGuard] Skipping non-http URL:", tab.url);
    return;
  }

  console.log("[PhishGuard] Auto-scanning tab", tabId, ":", tab.url);

  // Send to backend
  predictUrl(tab.url)
    .then((data) => {
      // Store result with tabId as key
      chrome.storage.local.set({ [String(tabId)]: data });
      console.log("[PhishGuard] Auto-scan result stored for tab", tabId, ":", data);
    })
    .catch((err) => {
      // Skip validation errors silently
      if (err && err.message === "Invalid URL format - skipping") {
        return;
      }
      console.error("[PhishGuard] Auto-scan failed for tab", tabId, ":", err);
      chrome.storage.local.set({
        [String(tabId)]: {
          error: err && err.message ? err.message : "Auto-scan failed",
          result: "error",
          risk_level: "ERROR",
        },
      });
    });
});

// Handle manual scan requests from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "SCAN_ACTIVE_TAB") {
    return;
  }

  console.log("[PhishGuard] Manual scan requested from popup");

  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const tab = tabs[0];
    if (!tab || !tab.url) {
      console.error("[PhishGuard] No active tab found");
      sendResponse({ error: "No active tab" });
      return;
    }

    const url = tab.url;
    if (url.startsWith("chrome://") || url.startsWith("edge://") || url.startsWith("about:")) {
      console.log("[PhishGuard] Cannot scan internal page:", url);
      sendResponse({ error: "Cannot scan internal pages" });
      return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      console.log("[PhishGuard] Cannot scan non-http URL:", url);
      sendResponse({ error: "Cannot scan non-http URLs" });
      return;
    }

    console.log("[PhishGuard] Manual scanning:", url);

    predictUrl(url)
      .then((data) => {
        chrome.storage.local.set({ [String(tab.id)]: data });
        console.log("[PhishGuard] Manual scan result stored for tab", tab.id, ":", data);
        sendResponse(data);
      })
      .catch((err) => {
        // Skip validation errors, return user-friendly message
        if (err && err.message === "Invalid URL format - skipping") {
          sendResponse({ error: "URL format not supported", status: "skip" });
          return;
        }
        console.error("[PhishGuard] Manual scan failed:", err);
        sendResponse({ error: err && err.message ? err.message : "Scan failed" });
      });
  });

  return true;
});
