"""Saare alert thresholds ek jagah. Yahan badalne se poora system badal jaata hai."""

THRESHOLDS = {
    "rain_prob_pct": 60,      # next 12h me rain probability >= 60% -> RAIN alert
    "heat_tmax_c": 40,        # aaj/kal max temp >= 40C -> HEAT alert
    "wind_gust_ms": 15,       # next 24h me gust >= 15 m/s (54 km/h) -> WIND alert
    "humidity_pct": 85,       # abhi humidity >= 85% -> HUMIDITY alert
    "uv_index": 8,            # aaj UV >= 8 -> UV alert
}

DEFAULT_CITY = "Indore"
OUTPUT_DIR = "outputs"
REPORT_DIR = "reports"
