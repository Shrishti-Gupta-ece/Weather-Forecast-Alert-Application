"""CSV, text report aur chart save karna."""
import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _slug(text):
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")


def save_outputs(result: dict, out_dir="outputs", report_dir="reports", chart=True) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    tag = f"{_slug(result['place'])}_{datetime.now():%Y%m%d_%H%M}"
    paths = {}

    paths["hourly_csv"] = f"{out_dir}/hourly_{tag}.csv"
    paths["daily_csv"] = f"{out_dir}/daily_{tag}.csv"
    result["hourly"].to_csv(paths["hourly_csv"], index=False)
    result["daily"].to_csv(paths["daily_csv"], index=False)

    paths["alerts_csv"] = f"{out_dir}/alerts_{tag}.csv"
    pd.DataFrame(result["alerts"], columns=["code", "severity", "message"]).to_csv(paths["alerts_csv"], index=False)

    paths["report_txt"] = f"{report_dir}/report_{tag}.txt"
    with open(paths["report_txt"], "w", encoding="utf-8") as f:
        f.write(text_report(result))

    if chart:
        paths["chart_png"] = f"{out_dir}/chart_{tag}.png"
        make_chart(result, paths["chart_png"])
    return paths


def text_report(result: dict) -> str:
    c, d = result["current"], result["daily"]
    lines = [f"WEATHER REPORT - {result['place']}",
             f"Generated: {datetime.now():%Y-%m-%d %H:%M}", "=" * 50,
             "CURRENT WEATHER",
             f"  Temperature : {c['temperature_2m']} C (feels {c.get('apparent_temperature')} C)",
             f"  Humidity    : {c['relative_humidity_2m']} %",
             f"  Wind        : {c['wind_speed_10m']} m/s (gust {c['wind_gusts_10m']} m/s)",
             f"  Rain now    : {c['precipitation']} mm", "", "7-DAY FORECAST"]
    for _, r in d.iterrows():
        lines.append(f"  {r['time']:%a %d %b}: {r['temperature_2m_min']:.0f}-{r['temperature_2m_max']:.0f} C, "
                     f"rain {r['precipitation_sum']} mm ({r['precipitation_probability_max']:.0f}%)")
    lines += ["", "ALERTS"]
    if result["alerts"]:
        lines += [f"  [{a['severity'].upper()}] {a['code']}: {a['message']}" for a in result["alerts"]]
    else:
        lines.append("  No alerts. Mausam theek hai.")
    return "\n".join(lines) + "\n"


def make_chart(result: dict, path: str):
    h, d = result["hourly"], result["daily"]
    now = pd.Timestamp(result["current"]["time"])
    h24 = h[h["time"] >= now].head(24)
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    ax[0].plot(h24["time"], h24["temperature_2m"], color="tab:red", marker="o", ms=3)
    ax[0].set_title("Next 24h Temperature (C)")
    ax[0].tick_params(axis="x", rotation=45)
    ax[0].grid(alpha=0.3)
    ax[1].bar(d["time"].dt.strftime("%d %b"), d["precipitation_sum"], color="tab:blue")
    ax[1].set_title("7-Day Rain (mm)")
    fig.suptitle(f"Weather - {result['place']}")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
