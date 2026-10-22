"""Small Streamlit helpers shared by all pages (page setup, data loading, filters, banners)."""
import pandas as pd
import streamlit as st

from managers.accident_manager import AccidentManager
from managers.location_manager import LocationManager
from managers.risk_manager import RiskManager
from managers.vehicle_manager import VehicleManager
from utils import analytics as an
from utils.data_loader import DataError, ValidationError
from utils import validators as v

SOURCE_OPTIONS = ["All", "Public", "Synthetic"]


def setup(title: str):
    st.set_page_config(page_title=f"RoadSafe | {title}", page_icon=":material/traffic:", layout="wide")
    st.title(title)
    flash = st.session_state.pop("_flash", None)
    if flash:
        st.success(flash)


def load_all() -> dict:
    """Load the four tables or show a friendly message and stop the page."""
    try:
        return {
            "acc": AccidentManager().load_data(),
            "veh": VehicleManager().load_data(),
            "loc": LocationManager().load_data(),
            "cond": RiskManager().load_data(),
        }
    except DataError as exc:
        st.error(str(exc))
        if st.button("Generate synthetic sample data"):
            from scripts.generate_sample_data import write_sample_data
            from utils.paths import get_data_dir
            try:
                write_sample_data(get_data_dir())
            except FileExistsError as exc:
                st.error(str(exc))
            else:
                st.rerun()
        st.stop()


def data_banner(acc):
    """Say clearly whether the data on screen is synthetic demo data."""
    if acc.empty:
        st.warning("No accident records yet. Add one on the Accidents page.")
        return
    synth = int(an.is_synthetic(acc).sum())
    if synth == len(acc):
        st.info("Demo data: every record is synthetic (fake). Nothing here is a real accident.")
    elif synth:
        st.info(f"Mixed data: {len(acc) - synth} public and {synth} synthetic (fake) records. Use the Source filter to separate them.")


def sidebar_filters(acc, prefix: str):
    """Date range, severity and source filters. Returns (filtered_accidents, filters_dict)."""
    st.sidebar.header("Filters")
    dates = pd.to_datetime(acc["Date"], errors="coerce").dropna()
    start = end = None
    if not dates.empty:
        lo, hi = dates.min().date(), dates.max().date()
        picked = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi, key=f"{prefix}_dates")
        if isinstance(picked, (tuple, list)) and len(picked) == 2 and (picked[0], picked[1]) != (lo, hi):
            start, end = picked
    severities = st.sidebar.multiselect("Severity", an.severity_options(acc), key=f"{prefix}_sev")
    source = st.sidebar.radio("Source", SOURCE_OPTIONS, key=f"{prefix}_src")
    filtered = an.filter_accidents(acc, start, end, severities, source)
    filters = {
        "Date range": f"{start} to {end}" if start else "all dates",
        "Severity": ", ".join(severities) if severities else "all",
        "Source": source,
    }
    return filtered, filters


# ------------------------------------------------------------------ generic CRUD panel
def run_action(action, success_message: str) -> None:
    """Run a manager call. On success show the message after a rerun; on failure show the errors."""
    try:
        action()
    except ValidationError as exc:
        for err in exc.errors:
            st.error(err)
        return
    except DataError as exc:
        st.error(str(exc))
        return
    st.session_state["_flash"] = success_message
    st.rerun()


def _widget(spec: dict, current: dict, key: str, locked: bool):
    cur = current.get(spec["col"])
    text = "" if cur is None else str(cur)
    if spec.get("options") is not None:
        options = list(spec["options"])
        if text not in options:
            options = [text] + options
        return st.selectbox(spec["label"], options, index=options.index(text), key=key,
                            format_func=lambda x: x if x else "(blank)", disabled=locked and spec.get("locked", False))
    return st.text_input(spec["label"], text, key=key, disabled=locked and spec.get("locked", False))


def _record_form(fields, current, prefix: str, editing: bool) -> dict:
    record = {}
    cols = st.columns(3)
    for i, spec in enumerate(fields):
        with cols[i % 3]:
            record[spec["col"]] = _widget(spec, current, f"{prefix}_{spec['col']}", editing)
    c1, c2 = st.columns(2)
    record["Data_Source"] = c1.text_input("Data_Source", current.get("Data_Source") or "manual_entry", key=f"{prefix}_ds")
    synthetic = c2.checkbox("Synthetic / sample record", current.get("Is_Synthetic") == "true", key=f"{prefix}_syn")
    record["Is_Synthetic"] = "true" if synthetic else "false"
    return record


def crud_section(manager, df, fields, delete_kwargs=None, delete_note=None) -> None:
    """Add / Edit / Delete tabs for one manager. `fields` = [{col, label, options?, locked?}]."""
    id_col = manager.id_col
    delete_kwargs = delete_kwargs or {}
    add_tab, edit_tab, delete_tab = st.tabs(["Add", "Edit", "Delete"])
    with add_tab:
        record = _record_form(fields, {}, "add", editing=False)
        if st.button("Add record", type="primary", key="add_btn"):
            run_action(lambda: manager.add_record(record), f"Added {record[id_col].strip() or 'record'}.")
    ids = list(df[id_col])
    with edit_tab:
        if not ids:
            st.info("Nothing to edit yet.")
        else:
            chosen = st.selectbox(f"{id_col} to edit", ids, key="edit_pick")
            edited = _record_form(fields, manager.get_record(chosen) or {}, f"edit_{chosen}", editing=True)
            if st.button("Save changes", type="primary", key="edit_btn"):
                run_action(lambda: manager.update_record(chosen, edited), f"Updated {chosen}.")
    with delete_tab:
        if not ids:
            st.info("Nothing to delete.")
        else:
            target = st.selectbox(f"{id_col} to delete", ids, key="del_pick")
            if delete_note:
                note = delete_note(target)
                if note:
                    st.warning(note)
            confirm = st.checkbox(f"Yes, permanently delete {target}", key=f"del_confirm_{target}")
            if st.button("Delete", disabled=not confirm, key="del_btn"):
                run_action(lambda: manager.delete_record(target, **delete_kwargs), f"Deleted {target}.")


def opt(values, blank=False):
    """Option list for a selectbox, optionally with a leading blank choice."""
    return ([""] if blank else []) + list(values)
