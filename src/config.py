"""All alert thresholds in one place. Change a value here to tune the whole system."""

THRESHOLDS = {
    "rain_prob_pct": 60,      # rain probability in next 12h >= 60% -> RAIN alert
    "heat_tmax_c": 40,        # max temp today/tomorrow >= 40C -> HEAT alert
    "wind_gust_ms": 15,       # gust in next 24h >= 15 m/s (54 km/h) -> WIND alert
    "humidity_pct": 85,       # current humidity >= 85% -> HUMIDITY alert
    "uv_index": 8,            # today's UV >= 8 -> UV alert
}

DEFAULT_CITY = "Indore"
OUTPUT_DIR = "outputs"
REPORT_DIR = "reports"
