"""Tests for the data importing and filtering / aggregation functions."""

import io

import pytest

from macro_tracker import data

CSV = (
    "date,name,protein,carbs,fat,eaten\n"
    "2026-01-01,Chicken,31,0,3.6,true\n"
    "2026-01-01,Rice,2.7,28,0.3,true\n"
    "2026-01-02,Protein Shake,80,8,6,true\n"
    "2026-01-02,Cake (what-if),5,60,20,false\n"
)


@pytest.fixture
def log():
    return data.load_log_csv(io.StringIO(CSV))


# ---- importing ----------------------------------------------------------

def test_load_log_csv_shape_and_types(log):
    assert list(log.columns) == data.LOG_COLUMNS
    assert len(log) == 4
    assert log["protein"].dtype == float
    assert log["eaten"].dtype == bool


def test_load_log_csv_parses_eaten_strings(log):
    assert log.loc[0, "eaten"] is True or bool(log.loc[0, "eaten"]) is True
    assert bool(log.loc[3, "eaten"]) is False


def test_load_log_csv_missing_column_raises():
    bad = io.StringIO("date,name,protein\n2026-01-01,x,10\n")
    with pytest.raises(ValueError):
        data.load_log_csv(bad)


def test_load_log_csv_coerces_bad_numbers_to_zero():
    src = io.StringIO("date,name,protein,carbs,fat,eaten\n2026-01-01,x,,abc,3,true\n")
    df = data.load_log_csv(src)
    assert df.loc[0, "protein"] == 0.0
    assert df.loc[0, "carbs"] == 0.0
    assert df.loc[0, "fat"] == 3.0


def test_empty_log_is_typed_and_empty():
    df = data.empty_log()
    assert len(df) == 0
    assert list(df.columns) == data.LOG_COLUMNS


def test_add_entry_does_not_mutate_input():
    base = data.empty_log()
    out = data.add_entry(base, "2026-02-01", "Egg", 13, 1.1, 11)
    assert len(base) == 0
    assert len(out) == 1
    assert out.loc[0, "name"] == "Egg"


# ---- filtering ----------------------------------------------------------

def test_filter_by_date_range_inclusive(log):
    only_first = data.filter_by_date_range(log, "2026-01-01", "2026-01-01")
    assert set(only_first["date"]) == {"2026-01-01"}
    assert len(only_first) == 2


def test_filter_by_date_range_empty_when_outside(log):
    assert data.filter_by_date_range(log, "2025-01-01", "2025-12-31").empty


def test_filter_eaten_excludes_what_if(log):
    eaten = data.filter_eaten(log)
    assert len(eaten) == 3
    assert eaten["eaten"].all()


# ---- aggregation --------------------------------------------------------

def test_daily_calorie_series_excludes_what_if(log):
    series = data.daily_calorie_series(log)
    by_date = dict(zip(series["date"], series["calories"], strict=False))
    # Day 1: chicken (31*4+3.6*9=156.4) + rice (2.7*4+28*4+0.3*9=125.5) = 281.9
    assert by_date["2026-01-01"] == pytest.approx(281.9, abs=0.1)
    # Day 2: only the eaten shake counts, not the what-if cake.
    assert by_date["2026-01-02"] == pytest.approx(80 * 4 + 8 * 4 + 6 * 9, abs=0.1)


def test_daily_calorie_series_sorted_by_date(log):
    series = data.daily_calorie_series(log)
    assert list(series["date"]) == sorted(series["date"])


def test_daily_macro_series_sums_per_day(log):
    macros = data.daily_macro_series(log)
    day1 = macros[macros["date"] == "2026-01-01"].iloc[0]
    assert day1["protein"] == pytest.approx(33.7)
    assert day1["carbs"] == pytest.approx(28.0)


def test_series_on_empty_log_are_empty():
    empty = data.empty_log()
    assert data.daily_calorie_series(empty).empty
    assert data.daily_macro_series(empty).empty


def test_weight_series_sorted_and_numeric():
    ws = data.weight_series({"2026-01-03": 80.0, "2026-01-01": 82.5})
    assert list(ws["date"]) == ["2026-01-01", "2026-01-03"]
    assert ws.loc[0, "kg"] == 82.5


def test_weight_series_empty():
    assert data.weight_series({}).empty
