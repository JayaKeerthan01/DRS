let tMap, tZoneLayer, tRouteLayer;
let trafficMapReady = false;

function initTrafficMap() {
  try {
    if (typeof L === "undefined") throw new Error("Leaflet failed to load");
    tMap = L.map("traffic-map", { attributionControl: false }).setView([12.9121, 77.6446], 12);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 18 }).addTo(tMap);
    tZoneLayer = L.layerGroup().addTo(tMap);
    tRouteLayer = L.layerGroup().addTo(tMap);
    trafficMapReady = true;
  } catch (e) {
    console.warn("Traffic map unavailable:", e.message);
    const el = document.getElementById("traffic-map");
    if (el) el.innerHTML = '<div class="empty-state">Map tiles unavailable — check browser internet access.</div>';
  }
}

async function renderTrafficTable() {
  const rows = document.getElementById("traffic-rows");
  try {
    const data = await getJSON("/api/traffic");
    rows.innerHTML = "";
    if (trafficMapReady) tZoneLayer.clearLayers();

    data.forEach((t) => {
      rows.appendChild(
        el(`
          <tr>
            <td>${t.zone}</td>
            <td><span class="badge ${congestionClass(t.congestion_level)}">${t.congestion_level}</span></td>
            <td>${t.road_status}</td>
            <td class="mono">${Math.round(t.confidence * 100)}%</td>
          </tr>
        `)
      );

      if (trafficMapReady) {
        const color = { Low: "#2DD4BF", Moderate: "#FFB238", High: "#f97316", Severe: "#FF5470" }[t.congestion_level];
        L.circleMarker([t.lat, t.lon], { radius: 10, color, fillColor: color, fillOpacity: 0.4, weight: 2 })
          .bindPopup(`<b>${t.zone}</b><br>${t.road_status}`)
          .addTo(tZoneLayer);
      }
    });
  } catch (e) {
    console.error(e);
  }
}

async function findRoute() {
  const fromZone = document.getElementById("from-zone").value;
  const resultBox = document.getElementById("route-result");
  resultBox.innerHTML = `<div class="empty-state">Calculating…</div>`;
  try {
    const route = await getJSON(`/api/route?from=${encodeURIComponent(fromZone)}`);
    resultBox.innerHTML = `
      <div class="zone-row">
        <div>
          <div class="zone-name">${route.from} → ${route.to}</div>
          <div class="zone-meta">${route.distance_km} km · est. ${route.duration_min} min · source: ${route.source}</div>
        </div>
        <span class="badge badge-info">Recommended</span>
      </div>
    `;
    if (trafficMapReady && route.path) {
      tRouteLayer.clearLayers();
      const line = L.polyline(route.path, { color: "#5EA8FF", weight: 4 }).addTo(tRouteLayer);
      tMap.fitBounds(line.getBounds(), { padding: [30, 30] });
    }
  } catch (e) {
    resultBox.innerHTML = `<div class="empty-state">Could not compute a route.</div>`;
  }
}

initTrafficMap();
renderTrafficTable();
setInterval(renderTrafficTable, POLL_INTERVAL_MS);
document.getElementById("route-btn").addEventListener("click", findRoute);
