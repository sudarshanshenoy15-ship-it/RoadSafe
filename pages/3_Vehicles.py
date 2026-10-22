import plotly.express as px
import streamlit as st

from managers.vehicle_manager import VehicleManager
from utils import analytics as an
from utils import ui
from utils import validators as v

ui.setup("Vehicles")
data = ui.load_all()
ui.data_banner(data["acc"])
acc, _ = ui.sidebar_filters(data["acc"], "veh")
veh = an.filter_by_accidents(data["veh"], acc["Accident_ID"])

types = st.sidebar.multiselect("Vehicle type", v.VEHICLE_TYPES, key="veh_type")
if types:
    veh = veh[veh["Vehicle_Type"].isin(types)]

st.dataframe(veh, hide_index=True)
st.caption(f"{len(veh)} vehicle records shown (linked to the accidents selected in the filters).")

left, right = st.columns(2)
with left:
    counts = an.vehicle_type_counts(veh)
    if counts.empty:
        st.info("No vehicle counts available for the current filters.")
    else:
        st.plotly_chart(px.bar(counts, x="Vehicle_Type", y="Vehicles", title="Vehicles by type (sum of Vehicle_Count)",
                               color_discrete_sequence=["#0F766E"]))
with right:
    speeds = an.speed_limit_counts(veh)
    if speeds.empty:
        st.info("No speed-limit values available.")
    else:
        st.plotly_chart(px.bar(speeds, x="Speed_Limit", y="Records", title="Posted speed limit (km/h)",
                               color_discrete_sequence=["#0F766E"]))
        st.caption("Speed_Limit is the posted limit in km/h. Blank means unknown and is not plotted.")

st.subheader("Manage vehicle records")
fields = [
    {"col": "Vehicle_ID", "label": "Vehicle_ID", "locked": True},
    {"col": "Accident_ID", "label": "Accident_ID (must exist)", "options": list(data["acc"]["Accident_ID"])},
    {"col": "Vehicle_Type", "label": "Vehicle_Type", "options": v.VEHICLE_TYPES},
    {"col": "Vehicle_Count", "label": "Vehicle_Count (optional)"},
    {"col": "Speed_Limit", "label": "Speed_Limit km/h (optional)"},
    {"col": "Vehicle_Movement", "label": "Vehicle_Movement (optional)"},
]
ui.crud_section(VehicleManager(), data["veh"], fields)
