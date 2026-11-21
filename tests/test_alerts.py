"""Golden tests: known input -> expected alerts."""
import pandas as pd
from src.alerts import evaluate


def frames(prob=10, gust=3, tmax=30, uv=5, hum=50):
    times = pd.date_range("2026-01-01 10:00", periods=48, freq="h")
    hourly = pd.DataFrame({"time": times, "precipitation_probability": prob, "wind_gusts_10m": gust})
    daily = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=3),
                          "temperature_2m_max": tmax, "uv_index_max": uv})
    cur = {"time": "2026-01-01T10:00", "relative_humidity_2m": hum}
    return cur, hourly, daily


def codes(**kw):
    return {a["code"] for a in evaluate(*frames(**kw))}


def test_calm_weather_has_no_alerts():
    assert codes() == set()


def test_rain_alert():
    assert "RAIN_SOON" in codes(prob=75)


def test_heat_alert_is_critical():
    res = evaluate(*frames(tmax=43))
    assert any(a["code"] == "HEAT_WAVE" and a["severity"] == "critical" for a in res)


def test_wind_and_humidity_and_uv():
    c = codes(gust=20, hum=92, uv=9)
    assert {"WIND_HIGH", "HUMIDITY_HIGH", "UV_HIGH"} <= c


def test_storm_needs_rain_and_wind():
    assert "STORM_RISK" in codes(prob=80, gust=20)
    assert "STORM_RISK" not in codes(prob=80, gust=5)
