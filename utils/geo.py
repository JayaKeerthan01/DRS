"""
Shared geospatial helpers.

Previously `_distance_km` (haversine) was duplicated in both
`agents/hospital_agent.py` and `agents/rescue_agent.py`. Centralized here so
there's one implementation to test and fix.
"""

import math

EARTH_RADIUS_KM = 6371


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometers."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))
