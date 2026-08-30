function statusBadgeClass(status) {
  return { available: "badge-available", deployed: "badge-medium" }[status] || "badge-info";
}

async function renderRescue() {
  try {
    const data = await getJSON("/api/rescue");

    document.getElementById("r-teams").textContent =
      data.summary.teams_available + " / " + data.summary.teams_total;
    document.getElementById("r-ambulances").textContent = data.summary.ambulances_total;
    document.getElementById("r-fire").textContent = data.summary.fire_units_total;
    document.getElementById("r-deployments").textContent = data.deployment.length;

    const depRows = document.getElementById("deployment-rows");
    depRows.innerHTML = "";
    if (!data.deployment.length) {
      depRows.appendChild(el(`<tr><td colspan="5" class="empty-state">No active deployments — all zones nominal.</td></tr>`));
    }
    data.deployment.forEach((d) => {
      depRows.appendChild(
        el(`
          <tr>
            <td>${d.zone} <span class="badge ${riskClass(d.risk_level)}" style="margin-left:6px;">${d.risk_level}</span></td>
            <td>${d.team_name}</td>
            <td class="mono">${d.distance_km} km</td>
            <td class="mono">${d.vehicles}veh · ${d.ambulances}amb · ${d.fire_units}fire · ${d.personnel}pax</td>
            <td><button class="btn btn-primary deploy-btn" data-zone="${d.zone}" style="padding:6px 12px; font-size:12.5px;">Deploy</button></td>
          </tr>
        `)
      );
    });
    depRows.querySelectorAll(".deploy-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Dispatching…";
        try {
          await postJSON("/api/deploy", { zone: btn.dataset.zone });
          await renderRescue();
        } catch (e) {
          alert(e.message);
          btn.disabled = false;
          btn.textContent = "Deploy";
        }
      });
    });

    const activeRows = document.getElementById("active-deployment-rows");
    activeRows.innerHTML = "";
    if (!data.active_deployments.length) {
      activeRows.appendChild(el(`<tr><td colspan="4" class="empty-state">No teams currently in the field.</td></tr>`));
    }
    data.active_deployments.forEach((d) => {
      activeRows.appendChild(
        el(`
          <tr>
            <td>Team #${d.team_id}</td>
            <td>${d.zone}</td>
            <td class="mono">${fmtTime(d.deployed_at)}</td>
            <td><button class="btn btn-ghost recall-btn" data-deployment-id="${d.id}" style="padding:6px 12px; font-size:12.5px;">Recall</button></td>
          </tr>
        `)
      );
    });
    activeRows.querySelectorAll(".recall-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Recalling…";
        try {
          await postJSON("/api/recall", { deployment_id: parseInt(btn.dataset.deploymentId, 10) });
          await renderRescue();
        } catch (e) {
          alert(e.message);
          btn.disabled = false;
          btn.textContent = "Recall";
        }
      });
    });

    const teamRows = document.getElementById("team-rows");
    teamRows.innerHTML = "";
    data.teams.forEach((t) => {
      teamRows.appendChild(
        el(`
          <tr>
            <td>${t.team_name}</td>
            <td>${t.zone}</td>
            <td><span class="badge ${statusBadgeClass(t.status)}">${t.status}</span></td>
          </tr>
        `)
      );
    });
  } catch (e) {
    console.error(e);
  }
}

renderRescue();
setInterval(renderRescue, POLL_INTERVAL_MS);
