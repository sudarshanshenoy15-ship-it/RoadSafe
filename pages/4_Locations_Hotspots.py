import plotly.express as px
import streamlit as st

from managers.location_manager import LocationManager
from utils import analytics as an
from utils import ui
from utils import validators as v
from utils.hotspot_detection import DEFAULT_CELL_SIZE_DEG, accident_points, grid_counts

ui.setup("Locations & Hotspots")
data = ui.load_all()
ui.data_banner(data["acc"])
acc, _ = ui.sidebar_filters(data["acc"], "loc")
loc = an.filter_by_accidents(data["loc"], acc["Accident_ID"])

points = accident_points(acc, data["loc"])
st.subheader("General hotspot map")
if data["acc"].shape[0] and an.is_synthetic(data["acc"]).all():
    st.warning("Demonstration map: all points are synthetic and are not real accident locations.")
elif not points.empty and an.is_synthetic(points).all():
    st.warning("Only synthetic demo records have coordinates in this sample. These pins are illustrative, not real accident locations; source-backed records have no GPS coordinates.")
st.caption("Shows where accidents were recorded. It is not a route or live-GPS map, and colour or size shows "
           "recorded accident counts, not future risk.")

view = st.radio("Map view", ["Points", "Grid counts"], horizontal=True)
if points.empty:
    st.info("No accidents with valid coordinates match the current filters.")
else:
    st.caption(f"{len(points)} of {len(acc)} accidents have valid coordinates and are plotted.")
    if view == "Points":
        fig = px.scatter_map(points, lat="Latitude", lon="Longitude", color="Severity", hover_name="Accident_ID",
                             hover_data=["Date"], zoom=6, height=550, opacity=0.7,
                             color_discrete_map={"Fatal": "#B91C1C", "Serious": "#EA580C", "Minor": "#0F766E", "Unknown": "#6B7280"})
    else:
        cell = st.select_slider("Grid cell size (degrees)", [0.02, 0.05, 0.1, 0.2], value=DEFAULT_CELL_SIZE_DEG)
        grid = grid_counts(points, cell)
        fig = px.scatter_map(grid, lat="Cell_Lat", lon="Cell_Lon", size="Accidents", color="Accidents",
                             hover_data=["Fatal"], zoom=6, height=550, size_max=40,
                             color_continuous_scale="Reds")
        st.caption(f"Each bubble is one {cell} degree grid cell (about {cell * 111:.0f} km tall); size and colour = accident count. "
                   "This is a simple count, not a statistical cluster test.")
        st.dataframe(grid.head(10), hide_index=True)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig)
    st.caption("Map tiles load from the internet.")

st.subheader("Road conditions")
roads = an.road_condition_counts(loc)
if roads.empty:
    st.info("No known road-condition values for the current filters.")
else:
    st.plotly_chart(px.bar(roads, x="Road_Condition", y="Records", title="Accidents by road condition",
                           color_discrete_sequence=["#0F766E"]))

st.subheader("Manage location records")
fields = [
    {"col": "Location_ID", "label": "Location_ID", "locked": True},
    {"col": "Accident_ID", "label": "Accident_ID (must exist)", "options": list(data["acc"]["Accident_ID"])},
    {"col": "Latitude", "label": "Latitude (optional)"},
    {"col": "Longitude", "label": "Longitude (optional)"},
    {"col": "Road_Type", "label": "Road_Type", "options": v.ROAD_TYPES},
    {"col": "Road_Condition", "label": "Road_Condition", "options": v.ROAD_CONDITIONS},
    {"col": "Lighting_Condition", "label": "Lighting_Condition", "options": ui.opt(v.LIGHTING, blank=True)},
    {"col": "Traffic_Density", "label": "Traffic_Density", "options": ui.opt(v.TRAFFIC_DENSITY, blank=True)},
]
ui.crud_section(LocationManager(), data["loc"], fields)
