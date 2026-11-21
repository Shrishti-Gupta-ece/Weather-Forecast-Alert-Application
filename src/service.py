"""Business layer: locations, DB -> DataFrames -> alerts, de-duplicated dispatch."""
import logging
import pandas as pd

from .db import get_conn
from .fetch import geocode
from .alerts import evaluate
from .notify import notify_all

log = logging.getLogger(__name__)


def add_location(name: str, mode: str = "sim", scenario: str = "normal") -> int:
    if mode == "api":
        g = geocode(name)
        canon = f"{g['name']}, {g.get('country_code', '')}"
        lat, lon, tz = g["latitude"], g["longitude"], g.get("timezone")
    else:
        canon, lat, lon, tz = name.title(), 0.0, 0.0, None
    con = get_conn()
    row = con.execute("SELECT id FROM locations WHERE name=?", (canon,)).fetchone()
    if row:
        loc_id = row["id"]
    else:
        loc_id = con.execute("INSERT INTO locations(name,lat,lon,tz,mode,scenario) VALUES (?,?,?,?,?,?)",
                             (canon, lat, lon, tz, mode, scenario)).lastrowid
        con.commit()
    con.close()
    return loc_id


def list_locations() -> list[dict]:
    con = get_conn()
    rows = [dict(r) for r in con.execute("SELECT * FROM locations ORDER BY name")]
    con.close()
    return rows


def _now_ts(con, loc_id):
    r = con.execute("SELECT ts FROM weather_current WHERE location_id=?", (loc_id,)).fetchone()
    return r["ts"] if r else None


def load_current(loc_id: int) -> dict | None:
    con = get_conn()
    r = con.execute("""SELECT ts AS time, temp_c AS temperature_2m, feels_c AS apparent_temperature,
        humidity AS relative_humidity_2m, wind_ms AS wind_speed_10m, gust_ms AS wind_gusts_10m,
        precip_mm AS precipitation FROM weather_current WHERE location_id=?""", (loc_id,)).fetchone()
    con.close()
    return dict(r) if r else None


def load_hourly(loc_id: int, hours: int = 48) -> pd.DataFrame:
    con = get_conn()
    now = _now_ts(con, loc_id) or "0000"
    df = pd.read_sql_query("""SELECT ts AS time, temp_c AS temperature_2m,
        humidity AS relative_humidity_2m, precip_prob AS precipitation_probability,
        precip_mm AS precipitation, wind_ms AS wind_speed_10m, gust_ms AS wind_gusts_10m,
        uv AS uv_index FROM weather_hourly WHERE location_id=? AND ts>=? ORDER BY ts LIMIT ?""",
                           con, params=(loc_id, now, hours))
    con.close()
    df["time"] = pd.to_datetime(df["time"])
    return df


def load_daily(loc_id: int, days: int = 7) -> pd.DataFrame:
    con = get_conn()
    now = (_now_ts(con, loc_id) or "0000")[:10]
    df = pd.read_sql_query("""SELECT date AS time, tmax_c AS temperature_2m_max,
        tmin_c AS temperature_2m_min, rain_mm AS precipitation_sum,
        rain_prob AS precipitation_probability_max, wind_max_ms AS wind_speed_10m_max,
        uv_max AS uv_index_max FROM weather_daily WHERE location_id=? AND date>=?
        ORDER BY date LIMIT ?""", con, params=(loc_id, now, days))
    con.close()
    df["time"] = pd.to_datetime(df["time"])
    return df


def get_alerts(loc_id: int) -> list[dict]:
    cur = load_current(loc_id)
    if cur is None:
        return []
    return evaluate(cur, load_hourly(loc_id, 48), load_daily(loc_id, 3))


def dispatch(loc_id: int, debounce_hours: int = 12) -> list[dict]:
    """Send new alerts only. The same (location, code) is not re-sent within the debounce window (12h)."""
    con = get_conn()
    name = con.execute("SELECT name FROM locations WHERE id=?", (loc_id,)).fetchone()["name"]
    sent = []
    for a in get_alerts(loc_id):
        recent = con.execute(
            "SELECT 1 FROM alert_log WHERE location_id=? AND code=? AND sent_at>=datetime('now',?)",
            (loc_id, a["code"], f"-{debounce_hours} hours")).fetchone()
        if recent:
            continue
        notify_all(f"[{a['severity'].upper()}] {name}: {a['message']}")
        con.execute("INSERT INTO alert_log(location_id,code,severity,message,sent_at) "
                    "VALUES (?,?,?,?,datetime('now'))", (loc_id, a["code"], a["severity"], a["message"]))
        sent.append(a)
    con.commit()
    con.close()
    return sent


def dispatch_all() -> dict:
    return {l["id"]: dispatch(l["id"]) for l in list_locations()}


def alert_history(limit: int = 50) -> list[dict]:
    con = get_conn()
    rows = [dict(r) for r in con.execute("""SELECT a.sent_at, l.name AS location, a.code, a.severity, a.message
        FROM alert_log a JOIN locations l ON l.id=a.location_id ORDER BY a.id DESC LIMIT ?""", (limit,))]
    con.close()
    return rows
