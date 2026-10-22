import streamlit as st

from managers.accident_manager import AccidentManager
from utils import ui
from utils import validators as v

ui.setup("Accidents")
data = ui.load_all()
manager = AccidentManager()
ui.data_banner(data["acc"])
acc, _ = ui.sidebar_filters(data["acc"], "acc")

search = st.text_input("Search by Accident_ID")
shown = acc[acc["Accident_ID"].str.contains(search.strip(), case=False, regex=False)] if search.strip() else acc
st.dataframe(shown, hide_index=True)
st.caption(f"{len(shown)} of {len(data['acc'])} records shown.")

fields = [
    {"col": "Accident_ID", "label": "Accident_ID", "locked": True},
    {"col": "Date", "label": "Date (YYYY-MM-DD)"},
    {"col": "Time", "label": "Time (HH:MM, optional)"},
    {"col": "Latitude", "label": "Latitude (optional)"},
    {"col": "Longitude", "label": "Longitude (optional)"},
    {"col": "Severity", "label": "Severity", "options": v.SEVERITIES},
    {"col": "Number_of_Casualties", "label": "Number of casualties (optional)"},
    {"col": "Number_of_Vehicles", "label": "Number of vehicles (optional)"},
]


def delete_note(accident_id):
    linked = manager.linked_counts(accident_id)
    if sum(linked.values()):
        return f"{accident_id} has linked records {linked}. Deleting it will delete these too."
    return None


ui.crud_section(manager, data["acc"], fields, delete_kwargs={"cascade": True}, delete_note=delete_note)
