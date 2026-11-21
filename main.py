"""Weather Forecast & Alert Application - terminal runner.

Examples:
  python main.py --mode sim --city Indore --scenario storm
  python main.py --mode api --city Mumbai
"""
import argparse
from src.config import DEFAULT_CITY
from src.pipeline import run_pipeline
from src.report import save_outputs
from src.fetch import WeatherAPIError

ICON = {"info": "[i]", "warn": "[!]", "critical": "[!!!]"}


def main():
    p = argparse.ArgumentParser(description="Weather Forecast & Alert Application")
    p.add_argument("--city", default=DEFAULT_CITY)
    p.add_argument("--mode", choices=["sim", "api"], default="sim")
    p.add_argument("--scenario", choices=["normal", "heat", "storm"], default="normal",
                   help="sirf sim mode me: alerts test karne ke liye")
    p.add_argument("--notify", action="store_true", help="Telegram alert bhejo (optional)")
    p.add_argument("--no-chart", action="store_true")
    a = p.parse_args()

    try:
        res = run_pipeline(a.city, a.mode, a.scenario)
    except WeatherAPIError as e:
        print(f"ERROR: {e}")
        return

    c = res["current"]
    print(f"\n=== CURRENT WEATHER: {res['place']} ===")
    print(f"Temp: {c['temperature_2m']} C | Humidity: {c['relative_humidity_2m']}% | "
          f"Wind: {c['wind_speed_10m']} m/s | Rain: {c['precipitation']} mm")

    print("\n=== 7-DAY FORECAST ===")
    for _, r in res["daily"].iterrows():
        print(f"{r['time']:%a %d %b}: {r['temperature_2m_min']:.0f}-{r['temperature_2m_max']:.0f} C | "
              f"rain {r['precipitation_sum']} mm ({r['precipitation_probability_max']:.0f}%)")

    print("\n=== ALERTS ===")
    if res["alerts"]:
        for al in res["alerts"]:
            print(f"{ICON[al['severity']]} {al['code']}: {al['message']}")
    else:
        print("No alerts. Mausam theek hai.")

    paths = save_outputs(res, chart=not a.no_chart)
    print("\n=== SAVED FILES ===")
    for k, v in paths.items():
        print(f"{k}: {v}")

    if a.notify and res["alerts"]:
        from src.notify import send_telegram
        send_telegram("\n".join(f"{x['code']}: {x['message']}" for x in res["alerts"]))


if __name__ == "__main__":
    main()
