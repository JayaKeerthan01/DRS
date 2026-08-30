const charts = {};

function buildCard(w) {
  const pct = riskScoreToPct(w.risk_score);
  return el(`
    <div class="card">
      <div class="card-eyebrow">${w.zone} <span class="live-dot"></span></div>
      <div style="display:flex; align-items:baseline; justify-content:space-between;">
        <div class="metric-value">${w.prediction}</div>
        <span class="badge ${riskClass(w.risk_level)}">${w.risk_level} risk</span>
      </div>
      <div class="risk-spectrum"><div class="marker" style="left:${pct}%"></div></div>
      <div class="risk-spectrum-labels"><span>Nominal</span><span>Watch</span><span>Critical</span></div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin: 16px 0; font-family: var(--font-mono); font-size:12px; color: var(--fog-300);">
        <div>Rainfall: ${w.weather.rainfall_mm} mm</div>
        <div>Wind: ${w.weather.wind_speed_kmh} km/h</div>
        <div>Humidity: ${w.weather.humidity_pct}%</div>
        <div>Temp: ${w.weather.temperature_c}°C</div>
      </div>

      <canvas id="chart-${w.zone.replace(/\s+/g, '-')}" height="110"></canvas>
    </div>
  `);
}

function renderChart(w) {
  if (typeof Chart === "undefined") return; // Chart.js CDN unavailable — cards still render without it
  const canvasId = `chart-${w.zone.replace(/\s+/g, "-")}`;
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const labels = Object.keys(w.probabilities);
  const values = Object.values(w.probabilities).map((v) => Math.round(v * 100));
  const colors = labels.map((l) =>
    l === "Normal" ? "#2DD4BF" : l === "Flood" ? "#5EA8FF" : l === "Cyclone" ? "#FFB238" : "#FF5470"
  );

  if (charts[canvasId]) charts[canvasId].destroy();
  charts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderRadius: 4 }] },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { max: 100, grid: { color: "#28395A" }, ticks: { color: "#7C8FAE", font: { family: "IBM Plex Mono", size: 10 } } },
        y: { grid: { display: false }, ticks: { color: "#EAF1FB", font: { family: "Inter", size: 12 } } },
      },
    },
  });
}

async function refreshPredictions() {
  try {
    const zones = await getJSON("/api/weather");
    const container = document.getElementById("prediction-cards");
    container.innerHTML = "";
    zones.forEach((w) => container.appendChild(buildCard(w)));
    zones.forEach((w) => {
      try {
        renderChart(w);
      } catch (err) {
        console.warn("Chart render failed for", w.zone, err);
      }
    });
  } catch (e) {
    console.error(e);
  }
}

refreshPredictions();
setInterval(refreshPredictions, POLL_INTERVAL_MS);
