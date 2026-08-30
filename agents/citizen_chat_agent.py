"""
Citizen Chat Agent

Answers plain-language public questions about risk, evacuation, and
hospitals using only the live data the other four agents already produce —
there's no separate knowledge base to keep in sync, so an answer can never
drift from what the dashboard itself is showing.

Two modes, matching the same simulate-by-default pattern already used in
api/weather_api.py and api/maps_api.py:
  - Default: a small keyword/intent matcher. Zero dependencies, zero
    network calls, always available, fully deterministic (easy to test).
  - If Config.ANTHROPIC_API_KEY is set: the same live context is handed to
    Claude for a more natural free-form answer, constrained to only use
    the data provided. Falls back to the rule-based matcher if the API
    call fails or the key is missing, so the chatbot never just breaks.
"""

from config import Config
from database.db import get_zones
from agents.weather_agent import weather_agent
from agents.traffic_agent import traffic_agent
from agents.hospital_agent import hospital_agent
from agents.rescue_agent import rescue_agent

try:
    import anthropic
except ImportError:
    anthropic = None


def find_zone(text, zones):
    """Loose zone-name lookup: full name match first, then first-word match
    (so "hsr" matches "HSR Layout"). Pure function — no I/O — so it's
    tested directly in tests/test_citizen_chat.py without a live DB."""
    text_l = text.lower()
    for z in zones:
        if z["name"].lower() in text_l:
            return z
    for z in zones:
        first_word = z["name"].split()[0].lower()
        if first_word and first_word in text_l:
            return z
    return None


def _build_context():
    weather = weather_agent.assess_all_zones()
    weather_by_zone = {w["zone"]: w for w in weather}
    traffic = traffic_agent.assess_all_zones(weather_by_zone)
    hospitals = hospital_agent.get_all_hospitals()
    rescue_summary = rescue_agent.status_summary()
    return weather, traffic, hospitals, rescue_summary


def _rule_based_answer(question, zones):
    q = question.lower().strip()
    weather, traffic, hospitals, rescue_summary = _build_context()
    zone = find_zone(question, zones)

    if len(q) < 20 and any(g in q for g in ("hello", "hi", "hey", "help")):
        return (
            "Hi! I can tell you about flood/cyclone/landslide risk, hospital "
            "contacts, and the safest evacuation route for your area. Try "
            "\"What's the risk in Koramangala?\" or \"Nearest hospital to HSR Layout\"."
        )

    if any(k in q for k in ("evacuat", "route", "escape", "safe way")):
        if not zone:
            return "Tell me which area you're evacuating from — for example \"evacuation route from Koramangala\"."
        route = traffic_agent.safest_route(zone["name"], traffic)
        return (
            f"From {zone['name']}, the safest route right now leads toward "
            f"{route['to']} — about {route['distance_km']} km, roughly "
            f"{route['duration_min']} minutes by road."
        )

    if any(k in q for k in ("hospital", "medical", "doctor", "clinic", "ambulance")):
        if zone:
            recs = hospital_agent.recommend_for_zone(zone, top_n=2)
            if recs:
                parts = [
                    f"{h['hospital_name']} ({h['distance_km']} km away, "
                    f"{h['beds_available']} beds free) — call {h['contact']}"
                    for h in recs
                ]
                return "Nearest hospitals for you: " + "; ".join(parts) + "."
        parts = [f"{h['hospital_name']} — {h['contact']}" for h in hospitals]
        return "Hospital contacts: " + "; ".join(parts) + "."

    if any(k in q for k in ("risk", "flood", "cyclone", "landslide", "danger")):
        if zone:
            w = next((x for x in weather if x["zone"] == zone["name"]), None)
            if w:
                return (
                    f"{zone['name']} is currently at {w['risk_level'].upper()} risk "
                    f"— most likely {w['prediction']} (confidence {round(w['risk_score'] * 100)}%). "
                    f"Current conditions: {w['weather']['rainfall_mm']}mm rainfall, "
                    f"{w['weather']['wind_speed_kmh']}km/h wind."
                )
        worst = max(weather, key=lambda w: w["risk_score"]) if weather else None
        if worst:
            return (
                f"The highest-risk area right now is {worst['zone']} "
                f"({worst['risk_level']} risk, {worst['prediction']}). "
                f"Ask about your own area by name for a specific answer."
            )

    if any(k in q for k in ("contact", "emergency", "helpline", "number", "call")):
        parts = [f"{h['hospital_name']}: {h['contact']}" for h in hospitals]
        return (
            "Emergency contacts — " + "; ".join(parts) + ". "
            f"Rescue teams available right now: {rescue_summary['teams_available']}/{rescue_summary['teams_total']}."
        )

    zone_names = ", ".join(z["name"] for z in zones)
    return (
        "I'm not sure how to answer that yet. I can help with risk levels, "
        f"evacuation routes, and hospital contacts for: {zone_names}. Try "
        "\"What's the risk in <your area>?\""
    )


def _claude_answer(question):
    if not Config.ANTHROPIC_API_KEY or anthropic is None:
        return None
    try:
        weather, traffic, hospitals, rescue_summary = _build_context()
        lines = []
        for w in weather:
            lines.append(f"- {w['zone']}: {w['risk_level']} risk, likely {w['prediction']} "
                          f"({w['weather']['rainfall_mm']}mm rain, {w['weather']['wind_speed_kmh']}km/h wind)")
        for t in traffic:
            lines.append(f"- {t['zone']} roads: {t['road_status']} ({t['congestion_level']} congestion)")
        for h in hospitals:
            lines.append(f"- Hospital {h['hospital_name']} in {h['location']}: "
                          f"{h['beds_available']}/{h['beds_total']} beds free, contact {h['contact']}")
        lines.append(f"- Rescue teams available: {rescue_summary['teams_available']}/{rescue_summary['teams_total']}")
        context = "\n".join(lines)

        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=Config.ANTHROPIC_CHAT_MODEL,
            max_tokens=300,
            system=(
                "You are a calm, concise public assistant for a disaster-response "
                "dashboard. Answer ONLY using the live data below — never invent a "
                "risk level, hospital name, phone number, or distance that isn't in "
                "it. If the question needs data that isn't listed, say so plainly and "
                "suggest checking back or calling local emergency services. Keep "
                "answers short and practical; this may be read by someone in a "
                "stressful situation.\n\nLive data:\n" + context
            ),
            messages=[{"role": "user", "content": question}],
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", None) == "text").strip()
        return text or None
    except Exception:
        return None  # fall back to the rule-based matcher below


def answer(question):
    """Public entry point. Always returns a usable answer — never raises,
    never returns an empty string — regardless of which mode served it."""
    zones = get_zones()
    if not question or not question.strip():
        return {"answer": "Ask me something like \"What's the risk in my area?\"", "source": "rule_based"}

    claude_reply = _claude_answer(question)
    if claude_reply:
        return {"answer": claude_reply, "source": "claude"}
    return {"answer": _rule_based_answer(question, zones), "source": "rule_based"}
