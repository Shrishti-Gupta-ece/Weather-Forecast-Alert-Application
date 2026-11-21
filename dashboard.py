"""Streamlit dashboard (DB se padhta hai).  streamlit run dashboard.py"""
import pandas as pd
import streamlit as st
from src.db import init_db
from src import service
from src.ingest import refresh_all
from src.fetch import WeatherAPIError

init_db()
st.set_page_config(page_title="Weather & Alerts", page_icon="⛅", layout="wide")
st.title("⛅ Weather Forecast & Alert Dashboard")

with st.sidebar:
    st.header("Add location")
    name = st.text_input("City", "Indore")
    mode = st.radio("Mode", ["sim", "api"])
    scenario = st.selectbox("Scenario (sim)", ["normal", "heat", "storm"])
    if st.button("Add"):
        try:
            service.add_location(name, mode, scenario)
            refresh_all()
            st.success("Added")
        except WeatherAPIError as e:
            st.error(str(e))
    if st.button("🔄 Refresh all data"):
        refresh_all()
        st.success("Refreshed")

locs = service.list_locations()
if not locs:
    st.info("Sidebar se pehli city add karo.")
    st.stop()

sel = st.selectbox("Location", locs, format_func=lambda l: f"{l['name']} ({l['mode']})")
cur = service.load_current(sel["id"])
if cur is None:
    st.warning("Data nahi hai. 'Refresh all data' dabao.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Temperature", f"{cur['temperature_2m']} °C")
c2.metric("Humidity", f"{cur['relative_humidity_2m']} %")
c3.metric("Wind", f"{cur['wind_speed_10m']} m/s")
c4.metric("Rain now", f"{cur['precipitation']} mm")

st.subheader("Active alerts")
alerts = service.get_alerts(sel["id"])
if not alerts:
    st.success("No alerts")
for a in alerts:
    {"critical": st.error, "warn": st.warning, "info": st.info}[a["severity"]](f"**{a['code']}** — {a['message']}")

h = service.load_hourly(sel["id"], 24).set_index("time")
d = service.load_daily(sel["id"], 7).set_index("time")
l, r = st.columns(2)
l.subheader("Next 24h temperature (°C)")
l.line_chart(h["temperature_2m"])
r.subheader("7-day rain (mm)")
r.bar_chart(d["precipitation_sum"])

st.subheader("Alert history")
st.dataframe(pd.DataFrame(service.alert_history(30)), use_container_width=True)
