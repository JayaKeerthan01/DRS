function severityIconBg(sev) {
  return { Low: "var(--alert-nominal-dim)", Medium: "var(--alert-warning-dim)", High: "var(--alert-critical-dim)" }[sev] || "var(--signal-info-dim)";
}
function severityIconColor(sev) {
  return { Low: "#2DD4BF", Medium: "#FFB238", High: "#FF5470" }[sev] || "#5EA8FF";
}

async function renderAlerts() {
  const container = document.getElementById("alerts-list");
  try {
    const alerts = await getJSON("/api/alerts");
    if (!alerts.length) {
      container.innerHTML = `<div class="empty-state">No alerts logged yet. The Coordinator Agent raises one automatically whenever a zone's risk reaches High.</div>`;
      return;
    }
    container.innerHTML = "";
    alerts.forEach((a) => {
      container.appendChild(
        el(`
          <div class="alert-item">
            <div class="alert-icon" style="background:${severityIconBg(a.severity)}; color:${severityIconColor(a.severity)};">⚠</div>
            <div style="flex:1;">
              <div class="alert-title">${a.title}</div>
              <div class="alert-message">${a.message}</div>
              <div class="alert-time">${fmtTime(a.created_at)} · zone: ${a.zone || "—"}</div>
            </div>
            <span class="badge ${riskClass(a.severity)}">${a.severity}</span>
          </div>
        `)
      );
    });
  } catch (e) {
    console.error(e);
  }
}

renderAlerts();
setInterval(renderAlerts, POLL_INTERVAL_MS);

function severityRowClass(sev) {
  return riskClass(sev);
}

async function renderIncidents() {
  const rows = document.getElementById("incident-rows");
  try {
    const incidents = await getJSON("/api/incidents");
    if (!incidents.length) {
      rows.innerHTML = `<tr><td colspan="5" class="empty-state">No assessments logged yet.</td></tr>`;
      return;
    }
    rows.innerHTML = "";
    incidents.forEach((i) => {
      rows.appendChild(
        el(`
          <tr>
            <td class="mono">${fmtTime(i.date)}</td>
            <td>${i.location}</td>
            <td>${i.disaster_type}</td>
            <td><span class="badge ${severityRowClass(i.severity)}">${i.severity}</span></td>
            <td class="mono">${(i.probability * 100).toFixed(1)}%</td>
          </tr>
        `)
      );
    });
  } catch (e) {
    console.error(e);
  }
}

renderIncidents();
setInterval(renderIncidents, POLL_INTERVAL_MS);
