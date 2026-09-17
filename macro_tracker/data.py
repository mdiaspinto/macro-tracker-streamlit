"""Food-log data layer — importing and filtering / aggregation.

The food log is a pandas ``DataFrame`` with the columns in ``LOG_COLUMNS``.
Every function here is pure (no I/O beyond an explicit path/buffer) so the test
suite can exercise the import and filtering logic directly.
"""

from __future__ import annotations

from typing import IO

import pandas as pd

from .nutrition import calories

LOG_COLUMNS = ["date", "name", "protein", "carbs", "fat", "eaten"]
_NUMERIC = ["protein", "carbs", "fat"]


def empty_log() -> pd.DataFrame:
    """A correctly typed, empty food log."""
    df = pd.DataFrame({c: [] for c in LOG_COLUMNS})
    df["eaten"] = df["eaten"].astype(bool)
    for c in _NUMERIC:
        df[c] = df[c].astype(float)
    return df


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    """Validate columns and coerce types on an incoming log."""
    missing = [c for c in LOG_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"log is missing required columns: {missing}")
    df = df[LOG_COLUMNS].copy()
    df["date"] = df["date"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    for c in _NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype(float)
    df["eaten"] = (
        df["eaten"].map(
            {True: True, False: False, "true": True, "false": False, "True": True,
             "False": False, 1: True, 0: False, "1": True, "0": False}
        ).fillna(True).astype(bool)
    )
    return df.reset_index(drop=True)


def load_log_csv(source: str | IO[str]) -> pd.DataFrame:
    """Import a food log from a CSV path or file-like buffer.

    Raises ``ValueError`` if required columns are absent.
    """
    return _coerce(pd.read_csv(source))


def add_entry(
    log: pd.DataFrame,
    date: str,
    name: str,
    protein: float,
    carbs: float,
    fat: float,
    eaten: bool = True,
) -> pd.DataFrame:
    """Return a new log with one entry appended (input is not mutated)."""
    row = pd.DataFrame(
        [[str(date).strip(), str(name).strip(), float(protein), float(carbs),
          float(fat), bool(eaten)]],
        columns=LOG_COLUMNS,
    )
    return _coerce(pd.concat([log, row], ignore_index=True))


def filter_by_date_range(log: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Rows whose ``date`` falls within [start, end] inclusive (string dates)."""
    mask = (log["date"] >= str(start)) & (log["date"] <= str(end))
    return log[mask].reset_index(drop=True)


def filter_eaten(log: pd.DataFrame, eaten: bool = True) -> pd.DataFrame:
    """Rows matching the ``eaten`` flag (True = actually eaten, not what-if)."""
    return log[log["eaten"] == eaten].reset_index(drop=True)


def _with_calories(log: pd.DataFrame) -> pd.DataFrame:
    df = log.copy()
    df["calories"] = calories(df["protein"], df["carbs"], df["fat"])
    return df


def daily_calorie_series(log: pd.DataFrame) -> pd.DataFrame:
    """Calories eaten per day (excludes what-if entries, drops zero days).

    Returns a DataFrame with columns ``date`` and ``calories`` sorted by date.
    """
    eaten = _with_calories(filter_eaten(log))
    if eaten.empty:
        return pd.DataFrame({"date": [], "calories": []})
    out = eaten.groupby("date", as_index=False)["calories"].sum()
    out = out[out["calories"] > 0].sort_values("date").reset_index(drop=True)
    return out


def daily_macro_series(log: pd.DataFrame) -> pd.DataFrame:
    """Protein / carbs / fat grams eaten per day, one row per date."""
    eaten = filter_eaten(log)
    if eaten.empty:
        return pd.DataFrame({c: [] for c in ["date", "protein", "carbs", "fat"]})
    out = eaten.groupby("date", as_index=False)[_NUMERIC].sum()
    return out.sort_values("date").reset_index(drop=True)


def weight_series(weights: dict) -> pd.DataFrame:
    """Turn a ``{YYYY-MM-DD: kg}`` mapping into a date-sorted DataFrame."""
    if not weights:
        return pd.DataFrame({"date": [], "kg": []})
    out = pd.DataFrame({"date": list(weights.keys()), "kg": list(weights.values())})
    out["kg"] = pd.to_numeric(out["kg"], errors="coerce")
    return out.dropna().sort_values("date").reset_index(drop=True)
