# Interview Prep — Weather Forecast & Alert Application

**Explain your project (60 seconds):**
"I built a weather pipeline in Python. It fetches forecasts from the Open-Meteo API (or from a built-in simulation mode), stores raw and normalized data in SQLite, and runs a rule engine that generates rain, heat, wind, UV and storm alerts. A FastAPI service exposes the data, APScheduler refreshes it automatically, and a Streamlit dashboard plus Telegram/console notifications deliver it to users. Alerts are de-duplicated over a 12-hour window so users are not spammed."

1. **Why is it provider-agnostic?** Vendor-specific logic is isolated in `fetch.py` and `ingest.py`. Swapping providers does not affect the rules, API or UI.
2. **Why store raw and normalized data?** Raw payloads give provenance and help debugging; normalized tables make queries and rule evaluation fast.
3. **How do you avoid duplicate alerts?** An `alert_log` table records every sent alert. The same (location, code) pair is not sent again within 12 hours.
4. **How do you handle errors?** Retry with exponential backoff, a custom `WeatherAPIError`, per-city try/except during refresh so one failure does not stop the rest, and NULL for missing fields.
5. **How do you test it?** Golden tests (known input → expected alerts), simulation scenarios, and API tests against a temporary database.
6. **Why a simulation mode?** It allows offline development, deterministic demos, and testing heat/storm alert paths without waiting for real weather.
7. **What does idempotency mean here?** Writes use `INSERT OR REPLACE` on primary keys such as (location_id, ts), so re-running a refresh never creates duplicates.
8. **How would you scale it?** Move SQLite to PostgreSQL, add a Redis cache, run workers with Celery or cron, and combine multiple weather providers.
9. **How do you handle secrets?** Keys live in `.env`, which is git-ignored. Only `.env.example` is committed.
10. **How would you explain it to a non-technical person?** "It checks the weather for your city automatically and warns you when there is rain, extreme heat or a storm coming."
