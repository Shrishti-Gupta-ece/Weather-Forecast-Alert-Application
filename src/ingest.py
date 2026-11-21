"""Ingestion: provider (API/simulation) -> raw store + normalized tables.
Retry with exponential backoff, idempotent upserts."""
import json
import logging
import time
from datetime import datetime, timezone

from .db import get_conn
from .fetch import fetch_forecast, WeatherAPIError
from .simulation import simulate_forecast

log = logging.getLogger(__name__)


def with_retry(fn, tries: int = 3, base_delay: float = 1.0):
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except WeatherAPIError as e:
            if attempt == tries:
                raise
            delay = base_delay * 2 ** (attempt - 1)
            log.warning("Fetch fail (%s). Retry %d/%d in %.1fs", e, attempt, tries - 1, delay)
            time.sleep(delay)


def _at(d: dict, key: str, i: int):
    arr = d.get(key)
    return arr[i] if arr else None


def save_weather(con, loc_id: int, provider: str, data: dict):
    """Raw payload + normalized rows. Missing fields -> None (NULL)."""
    con.execute("INSERT INTO weather_raw(location_id,fetched_at,provider,payload) VALUES (?,?,?,?)",
                (loc_id, datetime.now(timezone.utc).isoformat(), provider, json.dumps(data)))
    c = data["current"]
    con.execute("INSERT OR REPLACE INTO weather_current VALUES (?,?,?,?,?,?,?,?)",
                (loc_id, c["time"], c.get("temperature_2m"), c.get("apparent_temperature"),
                 c.get("relative_humidity_2m"), c.get("wind_speed_10m"),
                 c.get("wind_gusts_10m"), c.get("precipitation")))
    h = data["hourly"]
    con.executemany(
        "INSERT OR REPLACE INTO weather_hourly VALUES (?,?,?,?,?,?,?,?,?)",
        [(loc_id, ts, _at(h, "temperature_2m", i), _at(h, "relative_humidity_2m", i),
          _at(h, "precipitation_probability", i), _at(h, "precipitation", i),
          _at(h, "wind_speed_10m", i), _at(h, "wind_gusts_10m", i), _at(h, "uv_index", i))
         for i, ts in enumerate(h["time"])])
    d = data["daily"]
    con.executemany(
        "INSERT OR REPLACE INTO weather_daily VALUES (?,?,?,?,?,?,?,?)",
        [(loc_id, day, _at(d, "temperature_2m_max", i), _at(d, "temperature_2m_min", i),
          _at(d, "precipitation_sum", i), _at(d, "precipitation_probability_max", i),
          _at(d, "wind_speed_10m_max", i), _at(d, "uv_index_max", i))
         for i, day in enumerate(d["time"])])


def refresh_location(loc_id: int) -> int:
    con = get_conn()
    loc = con.execute("SELECT * FROM locations WHERE id=?", (loc_id,)).fetchone()
    if loc is None:
        con.close()
        raise ValueError(f"location_id {loc_id} does not exist")
    if loc["mode"] == "api":
        data = with_retry(lambda: fetch_forecast(loc["lat"], loc["lon"]))
        provider = "open-meteo"
    else:
        data = simulate_forecast(loc["name"], loc["scenario"])
        provider = "simulation"
    save_weather(con, loc_id, provider, data)
    con.commit()
    n = len(data["hourly"]["time"])
    con.close()
    log.info("Refreshed %s (%s): %d hourly rows", loc["name"], provider, n)
    return n


def refresh_all() -> dict:
    con = get_conn()
    ids = [r["id"] for r in con.execute("SELECT id FROM locations")]
    con.close()
    results = {}
    for i in ids:
        try:
            results[i] = refresh_location(i)
        except Exception as e:           # ek city fail ho to baaki chalti rahen
            log.error("Refresh fail for location %s: %s", i, e)
            results[i] = f"error: {e}"
    return results
