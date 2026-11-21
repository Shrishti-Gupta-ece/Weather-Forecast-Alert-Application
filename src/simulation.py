"""Virtual simulation: generates realistic fake data in the same shape as Open-Meteo, no API needed.
Scenarios: normal | heat | storm (used to test alerts)."""
import math
import random
from datetime import datetime, timedelta

CITY_BASE = {  # (base temp C, base humidity %)
    "indore": (28, 55), "delhi": (30, 50), "mumbai": (30, 75),
    "bhopal": (28, 55), "jaipur": (31, 45), "chennai": (32, 70),
}


def simulate_forecast(city: str, scenario: str = "normal", seed: int = 42) -> dict:
    rnd = random.Random(f"{city.lower()}-{scenario}-{seed}")
    base_t, base_h = CITY_BASE.get(city.lower(), (28, 60))
    if scenario == "heat":
        base_t += 11
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    start = now.replace(hour=0)

    hourly = {k: [] for k in ["time", "temperature_2m", "relative_humidity_2m",
                              "precipitation_probability", "precipitation",
                              "wind_speed_10m", "wind_gusts_10m", "uv_index"]}
    for i in range(7 * 24):
        t = start + timedelta(hours=i)
        diurnal = math.sin(2 * math.pi * (t.hour - 9) / 24)   # peak ~3 PM
        temp = base_t + 6 * diurnal + rnd.uniform(-1, 1)
        hum = min(100, max(15, base_h - 18 * diurnal + rnd.uniform(-5, 5)))
        prob = rnd.randint(5, 35)
        wind = rnd.uniform(1.5, 6)
        if scenario == "storm" and i < 36:
            prob = rnd.randint(70, 95)
            wind = rnd.uniform(8, 14)
            hum = min(100, hum + 25)
        gust = wind * rnd.uniform(1.2, 1.7)
        rain = round(rnd.uniform(0.5, 6), 1) if prob >= 60 else 0.0
        uv = max(0, 9 * math.sin(math.pi * (t.hour - 6) / 12)) if 6 <= t.hour <= 18 else 0
        for k, v in zip(hourly.keys(), [t.strftime("%Y-%m-%dT%H:%M"), round(temp, 1),
                        round(hum), prob, rain, round(wind, 1), round(gust, 1), round(uv, 1)]):
            hourly[k].append(v)

    # daily summary hourly se nikalo
    daily = {k: [] for k in ["time", "temperature_2m_max", "temperature_2m_min",
                             "precipitation_sum", "precipitation_probability_max",
                             "wind_speed_10m_max", "uv_index_max"]}
    for d in range(7):
        sl = slice(d * 24, (d + 1) * 24)
        daily["time"].append(hourly["time"][d * 24][:10])
        daily["temperature_2m_max"].append(max(hourly["temperature_2m"][sl]))
        daily["temperature_2m_min"].append(min(hourly["temperature_2m"][sl]))
        daily["precipitation_sum"].append(round(sum(hourly["precipitation"][sl]), 1))
        daily["precipitation_probability_max"].append(max(hourly["precipitation_probability"][sl]))
        daily["wind_speed_10m_max"].append(max(hourly["wind_speed_10m"][sl]))
        daily["uv_index_max"].append(max(hourly["uv_index"][sl]))

    idx = now.hour
    current = {
        "time": now.strftime("%Y-%m-%dT%H:%M"),
        "temperature_2m": hourly["temperature_2m"][idx],
        "apparent_temperature": round(hourly["temperature_2m"][idx] + 2, 1),
        "relative_humidity_2m": hourly["relative_humidity_2m"][idx],
        "precipitation": hourly["precipitation"][idx],
        "wind_speed_10m": hourly["wind_speed_10m"][idx],
        "wind_gusts_10m": hourly["wind_gusts_10m"][idx],
    }
    return {"current": current, "hourly": hourly, "daily": daily}
