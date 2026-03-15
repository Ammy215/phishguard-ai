const API_BASE = "http://127.0.0.1:5000";

console.log("PhishGuard AI Background Service Worker Loaded");

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
  fetch(API_BASE + "/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: tab.url }),
  })
    .then((res) => res.json())
    .then((data) => {
      // Store result with tabId as key
      chrome.storage.local.set({ [String(tabId)]: data });
      console.log("[PhishGuard] Auto-scan result stored for tab", tabId, ":", data);
    })
    .catch((err) => {
      console.error("[PhishGuard] Auto-scan failed for tab", tabId, ":", err);
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

    fetch(API_BASE + "/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url }),
    })
      .then((res) => res.json())
      .then((data) => {
        chrome.storage.local.set({ [String(tab.id)]: data });
        console.log("[PhishGuard] Manual scan result stored for tab", tab.id, ":", data);
        sendResponse(data);
      })
      .catch((err) => {
        console.error("[PhishGuard] Manual scan failed:", err);
        sendResponse({ error: err.message });
      });
  });

  return true;
});
