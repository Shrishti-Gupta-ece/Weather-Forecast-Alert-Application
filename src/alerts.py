"""Rule engine: weather data + thresholds -> human readable alerts."""
import pandas as pd
from .config import THRESHOLDS as T


def evaluate(current: dict, hourly: pd.DataFrame, daily: pd.DataFrame) -> list[dict]:
    now = pd.Timestamp(current["time"])
    upcoming = hourly[hourly["time"] >= now]
    next12, next24 = upcoming.head(12), upcoming.head(24)

    rain_prob = next12["precipitation_probability"].max()
    gust = next24["wind_gusts_10m"].max()
    tmax = daily.head(2)["temperature_2m_max"].max()
    uv = daily.iloc[0]["uv_index_max"]
    hum = current.get("relative_humidity_2m")

    alerts = []

    def add(code, severity, message):
        alerts.append({"code": code, "severity": severity, "message": message})

    if rain_prob >= T["rain_prob_pct"]:
        add("RAIN_SOON", "warn", f"Agle 12 ghante me baarish ki sambhavna {rain_prob:.0f}% - chhata saath rakho.")
    if tmax >= T["heat_tmax_c"]:
        add("HEAT_WAVE", "critical", f"Aaj/kal max temperature {tmax:.1f}C - dhoop se bacho, paani piyo.")
    if gust >= T["wind_gust_ms"]:
        add("WIND_HIGH", "warn", f"Agle 24 ghante me tez hawa (gust {gust:.1f} m/s = {gust*3.6:.0f} km/h).")
    if hum is not None and hum >= T["humidity_pct"]:
        add("HUMIDITY_HIGH", "info", f"Humidity {hum}% - mausam umas bhara rahega.")
    if uv >= T["uv_index"]:
        add("UV_HIGH", "warn", f"UV index {uv:.1f} - sunscreen lagao.")
    if rain_prob >= 70 and gust >= T["wind_gust_ms"]:
        add("STORM_RISK", "critical", "Baarish + tez hawa saath me - toofan jaisa mausam, bahar jaane se bacho.")
    return alerts
