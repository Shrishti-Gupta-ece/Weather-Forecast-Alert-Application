"""Poora flow: city -> data (API/sim) -> DataFrames -> alerts."""
import pandas as pd
from .fetch import geocode, fetch_forecast
from .simulation import simulate_forecast
from .alerts import evaluate


def run_pipeline(city: str, mode: str = "sim", scenario: str = "normal") -> dict:
    if mode == "api":
        place = geocode(city)
        data = fetch_forecast(place["latitude"], place["longitude"])
        place_name = f"{place['name']}, {place.get('country', '')}"
    else:
        data = simulate_forecast(city, scenario)
        place_name = f"{city.title()} (SIMULATION: {scenario})"

    hourly = pd.DataFrame(data["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"])
    daily = pd.DataFrame(data["daily"])
    daily["time"] = pd.to_datetime(daily["time"])
    current = data["current"]
    alerts = evaluate(current, hourly, daily)
    return {"place": place_name, "mode": mode, "current": current,
            "hourly": hourly, "daily": daily, "alerts": alerts}
