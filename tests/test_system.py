"""Integration tests: simulation -> DB -> alerts -> API (temp DB)."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("WEATHER_DB", str(tmp_path / "test.db"))
    from src.db import init_db
    init_db()


def test_storm_pipeline_and_dedupe(env):
    from src import service
    from src.ingest import refresh_location
    loc = service.add_location("Indore", "sim", "storm")
    assert refresh_location(loc) == 168
    codes = {a["code"] for a in service.get_alerts(loc)}
    assert "STORM_RISK" in codes
    first = service.dispatch(loc)
    assert first                                 # pehli baar alerts jaate hain
    assert service.dispatch(loc) == []           # 12h debounce: dobara nahi


def test_add_location_is_idempotent(env):
    from src import service
    assert service.add_location("Delhi") == service.add_location("Delhi")


def test_api_endpoints(env):
    from api.app import app
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}
        r = c.post("/locations", json={"name": "Delhi", "mode": "sim", "scenario": "heat"})
        assert r.status_code == 201
        lid = r.json()["id"]
        assert len(c.get(f"/forecast/hourly?location_id={lid}&hours=24").json()) == 24
        assert len(c.get(f"/forecast/daily?location_id={lid}&days=7").json()) >= 6
        assert any(a["code"] == "HEAT_WAVE" for a in c.get(f"/alerts?location_id={lid}").json()["alerts"])
        assert c.get("/forecast/hourly?location_id=999").status_code == 404
