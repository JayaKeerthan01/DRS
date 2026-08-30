"""
Mapping / routing data source.

The dashboard renders maps client-side with Leaflet.js + OpenStreetMap tiles
(free, no API key required). This module supplies the *data* Leaflet draws:
zone markers, hospital/rescue-team positions, and evacuation route polylines.

If Config.GOOGLE_MAPS_API_KEY is set, `get_directions()` will call the real
Google Directions API instead of the built-in synthetic route generator —
useful once you're ready to go live with turn-by-turn routing.
"""

import logging
import math
import random

from config import Config

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None


def get_zone_markers():
    from database.db import get_zones
    return [
        {"name": z["name"], "lat": z["lat"], "lon": z["lon"], "density": z["density"]}
        for z in get_zones()
    ]


def _synthetic_route(start, end, n_points=6):
    """Builds a plausible curved polyline between two points so the map has
    something realistic to draw without a real routing engine."""
    lat1, lon1 = start
    lat2, lon2 = end
    points = []
    rng = random.Random(f"{lat1}{lon1}{lat2}{lon2}")
    for i in range(n_points + 1):
        f = i / n_points
        lat = lat1 + (lat2 - lat1) * f
        lon = lon1 + (lon2 - lon1) * f
        # small perpendicular jitter so the line isn't perfectly straight
        jitter = math.sin(f * math.pi) * rng.uniform(-0.01, 0.01)
        points.append([round(lat + jitter, 5), round(lon + jitter, 5)])
    return points

def _decode_polyline(encoded):
    """Decodes Google's encoded polyline format into [[lat, lon], ...]."""
    points = []
    index = lat = lon = 0
    while index < len(encoded):
        for coord in ("lat", "lon"):
            shift = result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else (result >> 1)
            if coord == "lat":
                lat += delta
            else:
                lon += delta
        points.append([lat / 1e5, lon / 1e5])
    return points

def get_directions(start_zone, end_zone):
    """Returns dict: {distance_km, duration_min, path: [[lat, lon], ...]}"""
    start = (start_zone["lat"], start_zone["lon"])
    end = (end_zone["lat"], end_zone["lon"])

    if Config.GOOGLE_MAPS_API_KEY and requests is not None:
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": f"{start[0]},{start[1]}",
                    "destination": f"{end[0]},{end[1]}",
                    "key": Config.GOOGLE_MAPS_API_KEY,
                },
                timeout=5,
            )
            data = resp.json()
            leg = data["routes"][0]["legs"][0]
            return {
                "distance_km": round(leg["distance"]["value"] / 1000, 1),
                "duration_min": round(leg["duration"]["value"] / 60, 1),
                "path": _decode_polyline(data["routes"][0]["overview_polyline"]["points"]),  # polyline decode omitted for brevity
                "source": "google_maps",
            }
        except Exception as exc:
            logger.warning(
                "Google Directions call failed (%s); falling back to simulated route", exc,
            )

    # Haversine distance as a stand-in for real routing distance
    from utils.geo import haversine_km
    distance_km = haversine_km(*start, *end) * 1.35  # *1.35 road-vs-straight-line factor

    return {
        "distance_km": round(distance_km, 1),
        "duration_min": round(distance_km * 2.1, 1),  # ~28 km/h average urban speed
        "path": _synthetic_route(start, end),
        "source": "simulated",
    }
