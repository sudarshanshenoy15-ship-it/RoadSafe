import plotly.express as px
import streamlit as st

from managers.risk_manager import RiskManager
from utils import analytics as an
from utils import ui
from utils import validators as v

ui.setup("Risk Analysis")
data = ui.load_all()
ui.data_banner(data["acc"])
acc, _ = ui.sidebar_filters(data["acc"], "risk")
ids = acc["Accident_ID"]
cond = an.filter_by_accidents(data["cond"], ids)
loc = an.filter_by_accidents(data["loc"], ids)

st.subheader("Casualties")
if cond.empty:
    st.info("No weather/casualty records for the current filters.")
else:
    c1, c2, c3 = st.columns(3)
    for box, col in zip((c1, c2, c3), ("Casualties", "Fatalities", "Injuries")):
        box.metric(col, int(cond[col].sum()) if cond[col].notna().any() else "n/a",
                   help=f"{int(cond[col].isna().sum())} record(s) have no value (not counted as zero).")
    weather = an.weather_casualty_summary(cond)
    if weather.empty:
        st.info("No known weather values to chart.")
    else:
        st.plotly_chart(px.bar(weather, x="Weather", y="Casualties", title="Casualties by weather (recorded totals)",
                               color_discrete_sequence=["#0F766E"]))
        st.caption("Totals depend on how many accidents occurred in each weather type. They do not show that weather caused casualties.")

st.subheader("Risk score (0-100)")
table = an.build_risk_table(acc, loc, cond)
scored = table.dropna(subset=["Risk_Score"])
c1, c2 = st.columns(2)
c1.metric("Accidents scored", len(scored))
c2.metric("Insufficient data", int(table["Risk_Score"].isna().sum()))
if scored.empty:
    st.info("Insufficient data: no accident has all six inputs needed for the score.")
else:
    st.plotly_chart(px.histogram(scored, x="Risk_Score", nbins=10, title="Risk score distribution",
                                 color_discrete_sequence=["#0F766E"]))
display = table.copy()
display["Risk_Score"] = display["Risk_Score"].map(lambda x: "Insufficient data" if x != x else f"{x:.1f}")
st.dataframe(display, hide_index=True)

with st.expander("How the score works and its limitations", expanded=True):
    st.write(an.RISK_FORMULA_TEXT)
    st.table({
        "Factor": list(an.RISK_WEIGHTS), "Max points": list(an.RISK_WEIGHTS.values()),
        "Scaling (0-1)": [
            "Fatal 1.0, Serious 0.6, Minor 0.2", f"fatalities / {an.FATALITY_CAP}, capped at 1",
            f"injuries / {an.INJURY_CAP}, capped at 1", "Clear 0, Cloudy 0.25, Rain 0.6, Fog 0.9, Storm 1.0",
            "Dry 0, Wet 0.6, Damaged 0.8, Waterlogged 1.0", "Daylight 0, Dusk 0.4, Night-Lit 0.6, Night-Unlit 1.0"],
    })
    st.write("Bands: Low below 34, Medium 34 to 66.9, High 67 and above.")
    for item in an.RISK_LIMITATIONS:
        st.write(f"- {item}")
    st.write("The `Risk_Factor` column in the CSV is an optional note and is not used in the score.")

st.subheader("Manage weather and casualty records")
fields = [
    {"col": "Record_ID", "label": "Record_ID", "locked": True},
    {"col": "Accident_ID", "label": "Accident_ID (must exist)", "options": list(data["acc"]["Accident_ID"])},
    {"col": "Weather", "label": "Weather", "options": v.WEATHER},
    {"col": "Visibility", "label": "Visibility", "options": ui.opt(v.VISIBILITY, blank=True)},
    {"col": "Casualties", "label": "Casualties (optional)"},
    {"col": "Fatalities", "label": "Fatalities (optional)"},
    {"col": "Injuries", "label": "Injuries (optional)"},
    {"col": "Risk_Factor", "label": "Risk_Factor note (optional, not used in score)"},
]
ui.crud_section(RiskManager(), data["cond"], fields)
