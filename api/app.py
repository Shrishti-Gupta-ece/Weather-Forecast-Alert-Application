"""FastAPI service.  Run from project root:  uvicorn api.app:app --reload   ->  /docs"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from src.db import init_db
from src import service
from src.ingest import refresh_all, refresh_location
from src.fetch import WeatherAPIError
from src.logger import setup_logging


@asynccontextmanager
async def lifespan(app):
    setup_logging()
    init_db()
    yield


app = FastAPI(title="Weather Forecast & Alert API", version="2.0", lifespan=lifespan)


class LocationIn(BaseModel):
    name: str
    mode: str = "sim"          # 'sim' | 'api'
    scenario: str = "normal"


def _records(df):
    df = df.copy()
    df["time"] = df["time"].astype(str)
    return df.where(df.notna(), None).to_dict("records")


def _check(loc_id: int):
    if not any(l["id"] == loc_id for l in service.list_locations()):
        raise HTTPException(404, f"location {loc_id} not found")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/locations")
def locations():
    return service.list_locations()


@app.post("/locations", status_code=201)
def create_location(body: LocationIn):
    if body.mode not in ("sim", "api"):
        raise HTTPException(422, "mode must be 'sim' or 'api'")
    try:
        loc_id = service.add_location(body.name, body.mode, body.scenario)
        refresh_location(loc_id)
    except WeatherAPIError as e:
        raise HTTPException(404, str(e))
    return {"id": loc_id}


@app.post("/refresh")
def refresh():
    return refresh_all()


@app.get("/forecast/current")
def current(location_id: int):
    _check(location_id)
    return service.load_current(location_id)


@app.get("/forecast/hourly")
def hourly(location_id: int, hours: int = Query(24, ge=1, le=168)):
    _check(location_id)
    return _records(service.load_hourly(location_id, hours))


@app.get("/forecast/daily")
def daily(location_id: int, days: int = Query(7, ge=1, le=16)):
    _check(location_id)
    return _records(service.load_daily(location_id, days))


@app.get("/alerts")
def alerts(location_id: int):
    _check(location_id)
    return {"alerts": service.get_alerts(location_id)}


@app.get("/alerts/history")
def history(limit: int = 50):
    return service.alert_history(limit)
