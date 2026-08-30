"""
Pure scoring functions used by the Hospital and Rescue agents.

These were previously inlined inside the agent classes, which meant testing
the actual decision math required a live SQLite connection. Pulling them out
as plain functions (no DB, no I/O) makes them trivial to unit test — see
tests/test_scoring.py.
"""

RISK_WEIGHT = {"Low": 0.2, "Medium": 0.55, "High": 1.0}


def hospital_capacity_score(beds_available, beds_total, icu_available, doctors_available):
    """0..~1 score: higher = more spare capacity to take patients."""
    beds_total = max(beds_total, 1)
    return (
        (beds_available / beds_total) * 0.5
        + min(icu_available / 10, 1) * 0.3
        + min(doctors_available / 40, 1) * 0.2
    )


def hospital_suitability(capacity_score, distance_km):
    """Higher = better choice: more capacity, closer distance."""
    return capacity_score * 100 - distance_km * 1.5


def rescue_priority_score(risk_level, density):
    """0..1 zone priority: weighted disaster severity + population density."""
    severity_weight = RISK_WEIGHT.get(risk_level, 0.2)
    return severity_weight * 0.65 + density * 0.35
