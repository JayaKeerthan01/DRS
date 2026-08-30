"""
Model 1: Disaster Prediction

Input features : rainfall (mm), temperature (C), humidity (%), wind speed (km/h)
Output         : disaster type (Flood / Cyclone / Landslide / None) + per-class
                 probability, which the Weather Agent turns into a risk level.
"""

import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from config import Config
from ml.generate_datasets import generate_weather_history

FEATURES = ["rainfall_mm", "temperature_c", "humidity_pct", "wind_speed_kmh"]


def train(save=True):
    if os.path.exists(Config.WEATHER_HISTORY_CSV):
        df = pd.read_csv(Config.WEATHER_HISTORY_CSV)
    else:
        df = generate_weather_history()

    X = df[FEATURES]
    y = df["disaster_type"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=8, random_state=42, class_weight="balanced"
    )
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"[disaster_prediction] validation accuracy: {acc:.3f}")

    if save:
        os.makedirs(Config.MODELS_DIR, exist_ok=True)
        joblib.dump(model, Config.DISASTER_MODEL_PATH)

    return model


def load_model():
    if os.path.exists(Config.DISASTER_MODEL_PATH):
        return joblib.load(Config.DISASTER_MODEL_PATH)
    return train(save=True)


def predict(rainfall_mm, temperature_c, humidity_pct, wind_speed_kmh):
    """Returns dict: {prediction, probabilities: {class: prob}, risk_level, risk_score}"""
    model = load_model()
    row = pd.DataFrame(
        [[rainfall_mm, temperature_c, humidity_pct, wind_speed_kmh]], columns=FEATURES
    )
    proba = model.predict_proba(row)[0]
    classes = model.classes_
    probabilities = {cls: round(float(p), 3) for cls, p in zip(classes, proba)}

    prediction = max(probabilities, key=probabilities.get)
    non_none_risk = sum(p for cls, p in probabilities.items() if cls != "Normal")

    if non_none_risk >= 0.66:
        risk_level = "High"
    elif non_none_risk >= 0.35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "prediction": prediction,
        "probabilities": probabilities,
        "risk_level": risk_level,
        "risk_score": round(float(non_none_risk), 3),
    }


if __name__ == "__main__":
    train()
    print(predict(180, 30, 88, 40))
