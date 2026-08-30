async function findCitizenRoute() {
  const fromZone = document.getElementById("from-zone").value;
  const resultBox = document.getElementById("route-result");
  resultBox.innerHTML = `<div class="empty-state">Calculating the safest route…</div>`;
  try {
    const route = await getJSON(`/api/route?from=${encodeURIComponent(fromZone)}`);
    resultBox.innerHTML = `
      <div class="risk-card-lg risk-low">
        <div>
          <div class="zone-name">Head toward ${route.to}</div>
          <div class="zone-detail">About ${route.distance_km} km · roughly ${route.duration_min} minutes by road</div>
        </div>
      </div>
      <p style="color:var(--fog-300); font-size:13.5px; margin-top:10px;">
        This is the lowest-congestion direction right now, recalculated live.
        If conditions change quickly, check back before you leave.
      </p>
    `;
  } catch (e) {
    resultBox.innerHTML = `<div class="empty-state">Couldn't compute a route. Try again in a moment.</div>`;
  }
}

document.getElementById("route-btn").addEventListener("click", findCitizenRoute);
