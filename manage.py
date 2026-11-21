"""CLI for the industry version.
  python manage.py add-location Indore --mode sim --scenario storm
  python manage.py add-location Mumbai --mode api
  python manage.py refresh
  python manage.py alerts
  python manage.py dispatch
  python manage.py list"""
import argparse
from src.db import init_db
from src import service
from src.ingest import refresh_all
from src.logger import setup_logging
from src.fetch import WeatherAPIError


def main():
    setup_logging()
    init_db()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add-location")
    a.add_argument("name")
    a.add_argument("--mode", choices=["sim", "api"], default="sim")
    a.add_argument("--scenario", choices=["normal", "heat", "storm"], default="normal")
    for c in ["refresh", "alerts", "dispatch", "list", "history"]:
        sub.add_parser(c)
    args = p.parse_args()

    try:
        if args.cmd == "add-location":
            print("Location id:", service.add_location(args.name, args.mode, args.scenario))
        elif args.cmd == "list":
            for l in service.list_locations():
                print(l["id"], l["name"], l["mode"], l["scenario"])
        elif args.cmd == "refresh":
            print(refresh_all())
        elif args.cmd == "alerts":
            for l in service.list_locations():
                print(f"\n{l['name']}:")
                for al in service.get_alerts(l["id"]) or [{"code": "-", "severity": "ok", "message": "No alerts"}]:
                    print(f"  [{al['severity']}] {al['code']}: {al['message']}")
        elif args.cmd == "dispatch":
            print(service.dispatch_all())
        elif args.cmd == "history":
            for r in service.alert_history():
                print(r)
    except WeatherAPIError as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
