"""Run every Streamlit page headlessly and check none raises."""
import glob

import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import ROOT

PAGES = ["app.py"] + [str(Path).replace(str(ROOT) + "/", "") for Path in sorted(glob.glob(str(ROOT / "pages" / "*.py")))]


@pytest.mark.parametrize("page", PAGES)
def test_page_runs_with_sample_data(page, data_dir, monkeypatch):
    monkeypatch.setenv("ROADSAFE_DATA_DIR", str(data_dir))
    at = AppTest.from_file(str(ROOT / page), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("page", PAGES)
def test_page_shows_message_not_traceback_when_data_missing(page, tmp_path, monkeypatch):
    monkeypatch.setenv("ROADSAFE_DATA_DIR", str(tmp_path))
    at = AppTest.from_file(str(ROOT / page), default_timeout=60).run()
    assert not at.exception
    assert any("not found" in e.value for e in at.error)


def test_page_handles_empty_csvs(tmp_path, monkeypatch):
    from scripts.generate_sample_data import generate
    for name, df in generate().items():
        df.iloc[0:0].to_csv(tmp_path / name, index=False)
    monkeypatch.setenv("ROADSAFE_DATA_DIR", str(tmp_path))
    for page in PAGES:
        at = AppTest.from_file(str(ROOT / page), default_timeout=60).run()
        assert not at.exception, (page, [e.value for e in at.exception])


def test_add_accident_through_the_page(data_dir, monkeypatch):
    monkeypatch.setenv("ROADSAFE_DATA_DIR", str(data_dir))
    at = AppTest.from_file(str(ROOT / "pages" / "2_Accidents.py"), default_timeout=60).run()
    at.text_input(key="add_Accident_ID").set_value("UI-1")
    at.text_input(key="add_Date").set_value("2025-05-05")
    at.button(key="add_btn").click().run()
    assert not at.exception and not at.error
    from managers.accident_manager import AccidentManager
    assert AccidentManager(data_dir).get_record("UI-1") is not None


def test_invalid_accident_through_the_page_shows_error(data_dir, monkeypatch):
    monkeypatch.setenv("ROADSAFE_DATA_DIR", str(data_dir))
    at = AppTest.from_file(str(ROOT / "pages" / "2_Accidents.py"), default_timeout=60).run()
    at.text_input(key="add_Accident_ID").set_value("UI-2")
    at.text_input(key="add_Date").set_value("not-a-date")
    at.button(key="add_btn").click().run()
    assert any("Date" in e.value for e in at.error)


def test_hotspot_page_grid_view_and_filters(data_dir, monkeypatch):
    monkeypatch.setenv("ROADSAFE_DATA_DIR", str(data_dir))
    at = AppTest.from_file(str(ROOT / "pages" / "4_Locations_Hotspots.py"), default_timeout=60).run()
    at.radio[0].set_value("Grid counts").run()
    assert not at.exception, [e.value for e in at.exception]
    # filter to a severity with no coordinates problem and to a source that has no rows -> friendly message
    at.sidebar.radio[0].set_value("Public").run()
    assert not at.exception
    assert any("No accidents with valid coordinates" in i.value for i in at.info)
