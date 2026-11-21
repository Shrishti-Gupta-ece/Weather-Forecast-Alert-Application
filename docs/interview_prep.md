# Interview Prep — Weather Forecast & Alert Application

**Explain your project (60 sec):**
"Maine ek weather pipeline banayi hai: Open-Meteo API se (ya simulation se) forecast fetch hota hai, normalized SQLite tables me store hota hai, ek rule engine rain/heat/wind/UV/storm alerts nikalta hai, FastAPI unhe serve karti hai, APScheduler data auto-refresh karta hai, aur Streamlit dashboard + Telegram/console notifications milte hain. Alerts 12 ghante ke debounce ke saath jaate hain taaki spam na ho."

1. **Why provider-agnostic?** Vendor logic `fetch.py`/`ingest.py` me isolated hai; provider badalne par rules/API/UI untouched.
2. **Why store raw + normalized?** Raw = provenance/debugging, normalized = fast queries & rules.
3. **How do you avoid duplicate alerts?** `alert_log` table; same (location, code) 12h me dobara nahi.
4. **Error handling?** Retry with exponential backoff, custom `WeatherAPIError`, per-city try/except in `refresh_all`, NULL for missing fields.
5. **How do you test?** Golden tests (known data → expected alerts), simulation scenarios, API tests with temp DB.
6. **Why simulation mode?** Offline development, deterministic demos, testing alert paths (heat/storm).
7. **Idempotency?** `INSERT OR REPLACE` on primary keys (location_id, ts) → re-running refresh is safe.
8. **How to scale?** SQLite → PostgreSQL, Redis cache, Celery/cron workers, multi-provider ensemble.
9. **Secrets?** `.env` + `.gitignore`, only `.env.example` committed.
10. **Non-technical explanation:** "Ye system city ka mausam khud check karta hai aur baarish, garmi ya toofan ho to turant warning bhejta hai."
