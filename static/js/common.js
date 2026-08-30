/* Shared helpers used by every page's script. */

function riskClass(level) {
  return { Low: "badge-low", Medium: "badge-medium", High: "badge-high" }[level] || "badge-info";
}

function congestionClass(level) {
  return {
    Low: "badge-low", Moderate: "badge-moderate",
    High: "badge-high", Severe: "badge-severe",
  }[level] || "badge-info";
}

function riskScoreToPct(score) {
  return Math.max(2, Math.min(98, Math.round(score * 100)));
}

function riskLevelToPct(level) {
  return { Low: 15, Medium: 50, High: 88 }[level] ?? 15;
}

function fmtTime(iso) {
  try {
    return new Date(iso.replace(" ", "T")).toLocaleString();
  } catch (e) {
    return iso;
  }
}

async function getJSON(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) throw new Error("Request failed: " + url);
  return res.json();
}

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Request failed: " + url);
  }
  return data;
}

function el(html) {
  const template = document.createElement("template");
  template.innerHTML = html.trim();
  return template.content.firstElementChild;
}
