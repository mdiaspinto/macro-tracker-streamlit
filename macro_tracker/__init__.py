"""Macro Tracker — data-science core.

Pure, testable functions for importing foods and filtering / aggregating a
food log. Ported from the original single-file JavaScript Macro Tracker.
"""

from .data import (
    LOG_COLUMNS,
    add_entry,
    daily_calorie_series,
    daily_macro_series,
    empty_log,
    filter_by_date_range,
    filter_eaten,
    load_log_csv,
    weight_series,
)
from .foods import OFFLINE_FOODS, offline_lookup, scale_per_100g, search_openfoodfacts
from .nutrition import (
    ACTIVITY_FACTORS,
    KG_PER_LB,
    calories,
    estimate_targets,
    lb_to_kg,
    macros_from_calories,
)

__all__ = [
    "ACTIVITY_FACTORS",
    "KG_PER_LB",
    "calories",
    "estimate_targets",
    "lb_to_kg",
    "macros_from_calories",
    "OFFLINE_FOODS",
    "offline_lookup",
    "scale_per_100g",
    "search_openfoodfacts",
    "LOG_COLUMNS",
    "add_entry",
    "daily_calorie_series",
    "daily_macro_series",
    "empty_log",
    "filter_by_date_range",
    "filter_eaten",
    "load_log_csv",
    "weight_series",
]
