"""Nutrition math — calories, unit conversion, and target estimation.

Ported verbatim (same formulas and constants) from the original JavaScript app
so the numbers match on both platforms. See the README for provenance.
"""

from __future__ import annotations

from typing import TypedDict

# 1 pound in kilograms (exact).
KG_PER_LB = 0.45359237

# Atwater factors: protein 4 kcal/g, carbs 4 kcal/g, fat 9 kcal/g.
CAL_PER_G = {"protein": 4, "carbs": 4, "fat": 9}

# Mifflin-St Jeor activity multipliers (BMR -> TDEE).
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very": 1.9,
}


class Targets(TypedDict):
    p: int
    c: int
    f: int


class Estimate(TypedDict):
    tdee: int
    lean: Targets
    bulk: Targets


def calories(protein: float, carbs: float, fat: float) -> float:
    """Total calories for a set of macros (grams)."""
    return protein * 4 + carbs * 4 + fat * 9


def lb_to_kg(lb: float) -> float:
    return lb * KG_PER_LB


def macros_from_calories(cal: float, kg: float, protein_per_kg: float, fat_pct: float) -> Targets:
    """Split a calorie target into protein/carbs/fat grams.

    Protein is anchored to body weight, fat is a fixed fraction of calories,
    and carbs are whatever calories remain.
    """
    p = round(protein_per_kg * kg)
    f = round((fat_pct * cal) / 9)
    c = round(max(0, cal - p * 4 - f * 9) / 4)
    return {"p": p, "c": c, "f": f}


def estimate_targets(
    sex: str,
    age: float,
    cm: float,
    kg: float,
    activity: str = "moderate",
) -> Estimate | None:
    """Evidence-based starting macro targets.

    Mifflin-St Jeor BMR -> activity factor -> TDEE, then a ~20% deficit (lean)
    and a ~10% surplus (bulk). Returns ``None`` if any input is missing/invalid.
    """
    if not sex or not (age > 0) or not (cm > 0) or not (kg > 0):
        return None
    bmr = 10 * kg + 6.25 * cm - 5 * age + (-161 if sex == "female" else 5)
    af = ACTIVITY_FACTORS.get(activity, ACTIVITY_FACTORS["moderate"])
    tdee = bmr * af
    return {
        "tdee": round(tdee),
        "lean": macros_from_calories(tdee * 0.80, kg, 2.0, 0.25),
        "bulk": macros_from_calories(tdee * 1.10, kg, 1.8, 0.25),
    }
