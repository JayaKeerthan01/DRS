function riskWord(level) {
  return { Low: "All clear", Medium: "Stay alert", High: "Take action" }[level] || level;
}

async function refreshCitizenRisk() {
  const container = document.getElementById("risk-list");
  try {
    const zones = await getJSON("/api/weather");
    container.innerHTML = "";
    zones
      .sort((a, b) => b.risk_score - a.risk_score)
      .forEach((w) => {
        container.appendChild(
          el(`
            <div class="risk-card-lg risk-${w.risk_level.toLowerCase()}">
              <div>
                <div class="zone-name">${w.zone}</div>
                <div class="zone-detail">${w.prediction} · ${w.weather.rainfall_mm}mm rain · ${w.weather.wind_speed_kmh}km/h wind</div>
              </div>
              <div class="risk-word">${riskWord(w.risk_level)}</div>
            </div>
          `)
        );
      });
  } catch (e) {
    container.innerHTML = `<div class="empty-state">Couldn't load risk data. Try refreshing the page.</div>`;
    console.error(e);
  }
}

refreshCitizenRisk();
setInterval(refreshCitizenRisk, POLL_INTERVAL_MS);
