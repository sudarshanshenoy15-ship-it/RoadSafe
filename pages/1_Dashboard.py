import plotly.express as px
import streamlit as st

from utils import analytics as an
from utils import ui

ui.setup("Dashboard")
data = ui.load_all()
ui.data_banner(data["acc"])
acc, _ = ui.sidebar_filters(data["acc"], "dash")

if acc.empty:
    st.warning("No accidents match the current filters.")
    st.stop()

m = an.summary_metrics(acc)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Recorded accidents", m["total_accidents"])
c2.metric("Total casualties", m["total_casualties"] if m["total_casualties"] is not None else "n/a",
          help=f"Sum of known values only. {m['casualties_missing']} accident(s) have no casualty count.")
c3.metric("With valid coordinates", f"{m['with_coordinates']} ({m['coordinate_pct']}%)")
c4.metric("Public / synthetic", f"{m['public']} / {m['synthetic']}")

left, right = st.columns(2)
with left:
    sev = an.severity_counts(acc)
    st.plotly_chart(px.bar(sev, x="Severity", y="Accidents", title="Accidents by severity",
                           color_discrete_sequence=["#0F766E"]))
with right:
    months = an.monthly_counts(acc)
    if months.empty:
        st.info("No valid dates to plot.")
    else:
        st.plotly_chart(px.line(months, x="Month", y="Accidents", markers=True, title="Accidents per month",
                                color_discrete_sequence=["#0F766E"]))
st.caption("Counts follow the sidebar filters. Missing values are not counted as zero.")
