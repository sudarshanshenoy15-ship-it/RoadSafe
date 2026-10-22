from datetime import datetime

import streamlit as st

from utils import analytics as an
from utils import ui
from utils.report_generator import SECTIONS, build_csv_report, build_text_report

ui.setup("Reports")
data = ui.load_all()
ui.data_banner(data["acc"])
acc, filters = ui.sidebar_filters(data["acc"], "rep")

if acc.empty:
    st.warning("No accidents match the current filters, so there is nothing to report.")
    st.stop()

sections = st.multiselect("Sections to include", SECTIONS, default=SECTIONS)
ids = acc["Accident_ID"]
veh, loc, cond = (an.filter_by_accidents(data[k], ids) for k in ("veh", "loc", "cond"))
now = datetime.now()
stamp = now.strftime("%Y%m%d_%H%M%S")

text = build_text_report(filters, acc, veh, loc, cond, sections, now)
st.text_area("Report preview", text, height=420)

c1, c2, c3 = st.columns(3)
c1.download_button("Download text report", text, f"roadsafe_report_{stamp}.txt", "text/plain")
c2.download_button("Download CSV summary", build_csv_report(filters, acc, veh, loc, cond, sections, now),
                   f"roadsafe_summary_{stamp}.csv", "text/csv")
c3.download_button("Download filtered accidents (CSV)", acc.to_csv(index=False), f"roadsafe_accidents_{stamp}.csv", "text/csv")
