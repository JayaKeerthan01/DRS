async function refreshCitizenHospitals() {
  const container = document.getElementById("hospital-list");
  try {
    const hospitals = await getJSON("/api/hospitals");
    container.innerHTML = "";
    hospitals.forEach((h) => {
      const telHref = "tel:" + h.contact.replace(/[^0-9+]/g, "");
      container.appendChild(
        el(`
          <div class="hospital-card-lg">
            <div>
              <div class="hospital-name">${h.hospital_name}</div>
              <div class="hospital-meta">${h.location} · ${h.beds_available}/${h.beds_total} beds free · ${h.icu_available} ICU · ${h.doctors_available} doctors on duty</div>
            </div>
            <a class="call-btn" href="${telHref}">Call ${h.contact}</a>
          </div>
        `)
      );
    });
  } catch (e) {
    container.innerHTML = `<div class="empty-state">Couldn't load hospital data. Try refreshing.</div>`;
    console.error(e);
  }
}

refreshCitizenHospitals();
setInterval(refreshCitizenHospitals, POLL_INTERVAL_MS);
