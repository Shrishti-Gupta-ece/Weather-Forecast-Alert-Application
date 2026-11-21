"""Open-Meteo se real weather data lana (free, no API key)."""
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherAPIError(Exception):
    """Hamara custom error, taaki user ko saaf message dikhe."""


def geocode(city: str) -> dict:
    """City name -> latitude/longitude."""
    try:
        r = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=15)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise WeatherAPIError(f"Geocoding fail hui (internet check karo): {e}")
    results = r.json().get("results")
    if not results:
        raise WeatherAPIError(f"City '{city}' nahi mili. Spelling check karo.")
    return results[0]


def fetch_forecast(lat: float, lon: float) -> dict:
    """Current + hourly + 7-day daily forecast."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "precipitation,wind_speed_10m,wind_gusts_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,"
                  "precipitation,wind_speed_10m,wind_gusts_10m,uv_index",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                 "precipitation_probability_max,wind_speed_10m_max,uv_index_max",
        "timezone": "auto",
        "forecast_days": 7,
        "wind_speed_unit": "ms",
    }
    try:
        r = requests.get(FORECAST_URL, params=params, timeout=20)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise WeatherAPIError(f"API error: {e}")
    except requests.exceptions.RequestException as e:
        raise WeatherAPIError(f"Network problem: {e}")
    return r.json()
