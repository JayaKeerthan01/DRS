"""
Generates synthetic-but-realistic historical datasets used to TRAIN the demo
ML models, since no real historical disaster/traffic archive ships with a
student project.

Replace `datasets/weather_history.csv` and `datasets/traffic_history.csv`
with real historical records whenever you have them — disaster_prediction.py
and traffic_prediction.py don't care where the CSV came from, only that the
column names match.

Run directly:  python -m ml.generate_datasets
"""

import os
import numpy as np
import pandas as pd

from config import Config


def _label_disaster(rainfall, temperature, humidity, wind_speed, rng):
    """Rule-of-thumb physical relationships + noise, used only to build a
    plausible synthetic ground truth for training the demo classifier."""
    flood_score = (rainfall / 300) * 0.75 + (humidity / 100) * 0.25 + rng.normal(0, 0.03)
    cyclone_score = (wind_speed / 150) * 0.8 + (rainfall / 300) * 0.2 + rng.normal(0, 0.03)
    landslide_score = (rainfall / 300) * 0.55 + (humidity / 100) * 0.35 + rng.normal(0, 0.05)

    scores = {"Flood": flood_score, "Cyclone": cyclone_score, "Landslide": landslide_score}
    best = max(scores, key=scores.get)
    if scores[best] < 0.4:
        return "Normal"
    return best


def generate_weather_history(n=1500, seed=42):
    rng = np.random.default_rng(seed)
    rainfall = rng.gamma(shape=2.0, scale=35, size=n)          # mm
    temperature = rng.normal(29, 4, size=n)                     # deg C
    humidity = np.clip(rng.normal(70, 15, size=n), 20, 100)     # %
    wind_speed = rng.gamma(shape=2.0, scale=20, size=n)         # km/h

    labels = [
        _label_disaster(r, t, h, w, rng)
        for r, t, h, w in zip(rainfall, temperature, humidity, wind_speed)
    ]

    df = pd.DataFrame(
        {
            "rainfall_mm": rainfall.round(1),
            "temperature_c": temperature.round(1),
            "humidity_pct": humidity.round(1),
            "wind_speed_kmh": wind_speed.round(1),
            "disaster_type": labels,
        }
    )
    return df


def generate_traffic_history(n=2000, seed=7):
    rng = np.random.default_rng(seed)
    hour = rng.integers(0, 24, size=n)
    # Uses the seed zone list rather than the live DB, since this script
    # generates *training* data and may run before the DB even exists.
    # Any zone added later via /admin/zones is handled fine at inference
    # time regardless — traffic_prediction.py's OrdinalEncoder maps unseen
    # locations to -1 rather than crashing.
    locations = [z["name"] for z in Config.DEFAULT_ZONES]
    location = rng.choice(locations, size=n)
    weather_severity = rng.choice(
        ["clear", "rain", "storm", "flood_alert"], size=n, p=[0.55, 0.25, 0.12, 0.08]
    )

    rush_hour = np.isin(hour, [7, 8, 9, 17, 18, 19, 20]).astype(int)
    weather_penalty = pd.Series(weather_severity).map(
        {"clear": 0, "rain": 1, "storm": 2, "flood_alert": 3}
    ).to_numpy()

    congestion_score = rush_hour * 1.5 + weather_penalty * 1.2 + rng.normal(0, 0.6, size=n)

    def bucket(score):
        if score < 1.0:
            return "Low"
        elif score < 2.5:
            return "Moderate"
        elif score < 4.0:
            return "High"
        else:
            return "Severe"

    congestion_level = [bucket(s) for s in congestion_score]

    df = pd.DataFrame(
        {
            "hour": hour,
            "location": location,
            "weather_condition": weather_severity,
            "congestion_level": congestion_level,
        }
    )
    return df


def main():
    os.makedirs(Config.DATASETS_DIR, exist_ok=True)

    weather_df = generate_weather_history()
    weather_df.to_csv(Config.WEATHER_HISTORY_CSV, index=False)
    print(f"Wrote {len(weather_df)} rows -> {Config.WEATHER_HISTORY_CSV}")

    traffic_df = generate_traffic_history()
    traffic_df.to_csv(Config.TRAFFIC_HISTORY_CSV, index=False)
    print(f"Wrote {len(traffic_df)} rows -> {Config.TRAFFIC_HISTORY_CSV}")


if __name__ == "__main__":
    main()
