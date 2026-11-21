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
        add("RAIN_SOON", "warn", f"Rain likely in the next 12 hours ({rain_prob:.0f}% chance) - carry an umbrella.")
    if tmax >= T["heat_tmax_c"]:
        add("HEAT_WAVE", "critical", f"Max temperature of {tmax:.1f}°C expected today/tomorrow - avoid midday sun and stay hydrated.")
    if gust >= T["wind_gust_ms"]:
        add("WIND_HIGH", "warn", f"Strong wind gusts expected in the next 24 hours ({gust:.1f} m/s = {gust*3.6:.0f} km/h).")
    if hum is not None and hum >= T["humidity_pct"]:
        add("HUMIDITY_HIGH", "info", f"Humidity is {hum}% - expect muggy, uncomfortable conditions.")
    if uv >= T["uv_index"]:
        add("UV_HIGH", "warn", f"UV index {uv:.1f} - wear sunscreen and limit sun exposure.")
    if rain_prob >= 70 and gust >= T["wind_gust_ms"]:
        add("STORM_RISK", "critical", "Heavy rain combined with strong wind - storm-like conditions, avoid going outdoors.")
    return alerts
