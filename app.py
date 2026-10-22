"""RoadSafe entry point. Run with:  streamlit run app.py"""
import streamlit as st

from utils import analytics as an
from utils import ui

ui.setup("RoadSafe")
st.caption("Road accident hotspot and safety analytics (aligned with UN SDG 11: Sustainable Cities and Communities)")

data = ui.load_all()
ui.data_banner(data["acc"])

st.markdown(
    """
RoadSafe stores accident records in four linked CSV files and shows descriptive analytics.

- **Dashboard** - headline numbers, severity and time trend
- **Accidents** - search, add, edit and delete accident records
- **Vehicles** - vehicle records and vehicle-type analysis
- **Locations & Hotspots** - general map of recorded accident concentration
- **Risk Analysis** - casualties by weather and a transparent 0-100 risk score
- **Reports** - download CSV and text summaries

This is a general historical map and descriptive tool. It does not give routes or live GPS,
and it does not predict future accidents.
"""
)
metrics = an.summary_metrics(data["acc"])
c1, c2, c3 = st.columns(3)
c1.metric("Accident records", metrics["total_accidents"])
c2.metric("Public records", metrics["public"])
c3.metric("Synthetic records", metrics["synthetic"])
