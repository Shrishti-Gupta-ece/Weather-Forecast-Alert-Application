"""Auto-refresh + alert dispatch.
  python -m src.scheduler          # runs forever
  python -m src.scheduler --once   # ek baar refresh + dispatch"""
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from .db import init_db
from .ingest import refresh_all
from .service import dispatch_all
from .logger import setup_logging


def job():
    refresh_all()
    dispatch_all()


if __name__ == "__main__":
    setup_logging()
    init_db()
    if "--once" in sys.argv:
        job()
    else:
        sched = BlockingScheduler()
        sched.add_job(refresh_all, "interval", hours=2, id="refresh")
        sched.add_job(dispatch_all, "interval", minutes=30, id="alerts")
        job()  # start hote hi ek baar
        print("Scheduler chalu: refresh har 2h, alerts har 30 min. Ctrl+C se band.")
        sched.start()
