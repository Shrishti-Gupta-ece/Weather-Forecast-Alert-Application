"""SQLite storage layer: schema + connection helper."""
import os
import sqlite3


def db_path() -> str:
    return os.getenv("WEATHER_DB", "db/weather.db")   # overridable via env (tests/docker)


SCHEMA = """
CREATE TABLE IF NOT EXISTS locations(
  id INTEGER PRIMARY KEY, name TEXT UNIQUE, lat REAL, lon REAL, tz TEXT,
  mode TEXT DEFAULT 'api',            -- 'api' | 'sim'
  scenario TEXT DEFAULT 'normal'      -- sim scenario
);
CREATE TABLE IF NOT EXISTS weather_raw(
  id INTEGER PRIMARY KEY, location_id INTEGER, fetched_at TEXT, provider TEXT, payload TEXT,
  FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS weather_current(
  location_id INTEGER PRIMARY KEY, ts TEXT, temp_c REAL, feels_c REAL, humidity REAL,
  wind_ms REAL, gust_ms REAL, precip_mm REAL
);
CREATE TABLE IF NOT EXISTS weather_hourly(
  location_id INTEGER, ts TEXT, temp_c REAL, humidity REAL, precip_prob REAL,
  precip_mm REAL, wind_ms REAL, gust_ms REAL, uv REAL,
  PRIMARY KEY(location_id, ts)
);
CREATE TABLE IF NOT EXISTS weather_daily(
  location_id INTEGER, date TEXT, tmax_c REAL, tmin_c REAL, rain_mm REAL,
  rain_prob REAL, wind_max_ms REAL, uv_max REAL,
  PRIMARY KEY(location_id, date)
);
CREATE TABLE IF NOT EXISTS alert_log(
  id INTEGER PRIMARY KEY, location_id INTEGER, code TEXT, severity TEXT,
  message TEXT, sent_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_hourly_loc_ts ON weather_hourly(location_id, ts);
CREATE INDEX IF NOT EXISTS idx_alert_loc_code ON alert_log(location_id, code, sent_at);
"""


def get_conn() -> sqlite3.Connection:
    path = db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db():
    con = get_conn()
    con.executescript(SCHEMA)
    con.commit()
    con.close()
