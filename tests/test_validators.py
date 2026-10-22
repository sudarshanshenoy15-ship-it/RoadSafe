import pytest

from utils import validators as v


@pytest.mark.parametrize("value,ok", [("2025-01-31", True), ("2025-02-30", False), ("31/01/2025", False),
                                      ("", False), ("2999-01-01", False)])
def test_date(value, ok):
    assert (v.check_date(value) is None) == ok


def test_time():
    assert v.check_time("") is None          # optional
    assert v.check_time("23:59") is None
    assert v.check_time("24:00") is not None
    assert v.check_time("9pm") is not None


@pytest.mark.parametrize("lat,lon,n_errors", [("9.9", "76.2", 0), ("", "", 0), ("91", "76", 1), ("9", "181", 1),
                                              ("abc", "76", 1), ("9.9", "", 1), ("nan", "76", 1)])
def test_coordinate_pair(lat, lon, n_errors):
    assert len(v.check_coordinate_pair(lat, lon)) == n_errors


def test_counts():
    assert v.check_count("3", "X") is None
    assert v.check_count("3.0", "X") is None
    assert v.check_count("", "X") is None
    assert v.check_count("", "X", required=True) is not None
    assert v.check_count("-1", "X") is not None
    assert v.check_count("2.5", "X") is not None
    assert v.check_count("two", "X") is not None


def test_speed_limit():
    assert v.check_speed_limit("") is None
    assert v.check_speed_limit("60") is None
    assert v.check_speed_limit("0") is not None
    assert v.check_speed_limit("-5") is not None
    assert v.check_speed_limit("500") is not None


def test_bool_and_id():
    assert v.check_bool_like("true") is None and v.check_bool_like("FALSE") is None
    assert v.check_bool_like("yes") is not None
    assert v.check_id("  ", "ID") is not None


def test_normalize_severity():
    assert v.normalize_severity("Fatal") == "Fatal"
    assert v.normalize_severity("grievous injury") == "Serious"
    assert v.normalize_severity("Slight") == "Minor"
    assert v.normalize_severity("3") == "Minor"
    assert v.normalize_severity("") == "Unknown"
    assert v.normalize_severity("banana") == "Unknown"
