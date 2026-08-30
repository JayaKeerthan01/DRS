"""
Hospital Resource Agent

Responsibilities:
  1. Monitor bed / doctor / ambulance / ICU availability at every hospital.
  2. Recommend the best hospital(s) for a given affected zone, weighing
     capacity against distance.
  3. Reserve/release beds when a deployment is actually dispatched/recalled,
     so capacity numbers reflect real state instead of a static suggestion.

Changelog (hardening pass):
  - `_distance_km` used to be duplicated here and in rescue_agent.py — now
    both import utils.geo.haversine_km.
  - Suitability scoring moved to agents/scoring.py as pure functions so it
    can be unit tested without a live DB (see tests/test_scoring.py).
  - beds_available previously never changed after a deployment — added
    reserve_for_deployment()/release_beds() called from the /api/deploy and
    /api/recall routes.
"""

from config import Config
from database.db import query, adjust_hospital_beds
from utils.geo import haversine_km
from agents.scoring import hospital_capacity_score, hospital_suitability


class HospitalAgent:
    name = "Hospital Agent"

    def get_all_hospitals(self):
        return query("SELECT * FROM hospitals ORDER BY hospital_name")

    def recommend_for_zone(self, zone, top_n=3):
        hospitals = self.get_all_hospitals()
        scored = []
        for h in hospitals:
            distance = haversine_km(zone["lat"], zone["lon"], h["lat"], h["lon"])
            capacity_score = hospital_capacity_score(
                h["beds_available"], h["beds_total"], h["icu_available"], h["doctors_available"]
            )
            suitability = hospital_suitability(capacity_score, distance)
            scored.append({**h, "distance_km": round(distance, 1), "suitability": round(suitability, 1)})

        scored.sort(key=lambda h: h["suitability"], reverse=True)
        return scored[:top_n]

    def status_summary(self):
        hospitals = self.get_all_hospitals()
        total_beds = sum(h["beds_total"] for h in hospitals)
        available_beds = sum(h["beds_available"] for h in hospitals)
        return {
            "hospitals_online": len(hospitals),
            "total_beds": total_beds,
            "beds_available": available_beds,
            "occupancy_pct": round(100 * (1 - available_beds / max(total_beds, 1)), 1),
        }

    def reserve_for_deployment(self, hospital_id, beds=None):
        """Called when a deployment is dispatched — reserves an estimated
        number of beds at the chosen hospital so capacity numbers stay
        honest until the deployment is recalled."""
        beds = beds if beds is not None else Config.BEDS_RESERVED_PER_DEPLOYMENT
        adjust_hospital_beds(hospital_id, -beds)
        return beds

    def release_beds(self, hospital_id, beds):
        adjust_hospital_beds(hospital_id, beds)


hospital_agent = HospitalAgent()
