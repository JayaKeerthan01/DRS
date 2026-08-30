"""
Traffic Analysis Agent

Responsibilities:
  1. Predict congestion level for every zone using the traffic ML model.
  2. Flag roads as blocked/high-risk when a zone's disaster risk is High.
  3. Recommend the safest evacuation route between an affected zone and the
     nearest zone that is currently low-risk.
"""

from datetime import datetime

from api import maps_api
from ml import traffic_prediction
from database.db import get_zones

CONGESTION_TO_ROAD_STATUS = {
    "Low": "Clear",
    "Moderate": "Slow-moving",
    "High": "Heavily congested",
    "Severe": "Blocked / impassable",
}


class TrafficAgent:
    name = "Traffic Agent"

    def assess_zone(self, zone, weather_condition="clear"):
        hour = datetime.now().hour
        result = traffic_prediction.predict(hour, zone["name"], weather_condition)
        road_status = CONGESTION_TO_ROAD_STATUS[result["congestion_level"]]

        return {
            "zone": zone["name"],
            "lat": zone["lat"],
            "lon": zone["lon"],
            "congestion_level": result["congestion_level"],
            "confidence": result["confidence"],
            "road_status": road_status,
            "blocked": result["congestion_level"] == "Severe",
        }

    def assess_all_zones(self, weather_by_zone=None):
        weather_by_zone = weather_by_zone or {}
        assessments = []
        for zone in get_zones():
            w = weather_by_zone.get(zone["name"])
            condition = "clear"
            if w:
                if w.get("risk_level") == "High":
                    condition = "flood_alert"
                elif w.get("weather", {}).get("rainfall_mm", 0) > 80:
                    condition = "storm"
                elif w.get("weather", {}).get("rainfall_mm", 0) > 20:
                    condition = "rain"
            assessments.append(self.assess_zone(zone, condition))
        return assessments

    def safest_route(self, from_zone_name, traffic_assessments):
        """Pick the least-congested other zone and return a route to it."""
        zones_by_name = {z["name"]: z for z in get_zones()}
        from_zone = zones_by_name[from_zone_name]

        candidates = [a for a in traffic_assessments if a["zone"] != from_zone_name]
        congestion_rank = {"Low": 0, "Moderate": 1, "High": 2, "Severe": 3}
        candidates.sort(key=lambda a: congestion_rank[a["congestion_level"]])
        best = candidates[0]
        destination_zone = zones_by_name[best["zone"]]

        route = maps_api.get_directions(from_zone, destination_zone)
        route["from"] = from_zone_name
        route["to"] = best["zone"]
        return route


traffic_agent = TrafficAgent()
