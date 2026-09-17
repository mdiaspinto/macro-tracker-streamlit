"""Tests for the nutrition math (calories, conversion, target estimation)."""

import pytest

from macro_tracker import nutrition


def test_calories_atwater_factors():
    # 10g protein, 20g carbs, 5g fat = 40 + 80 + 45 = 165
    assert nutrition.calories(10, 20, 5) == 165


def test_calories_zero():
    assert nutrition.calories(0, 0, 0) == 0


def test_lb_to_kg():
    assert nutrition.lb_to_kg(100) == pytest.approx(45.359237)


def test_macros_from_calories_split():
    # 2000 kcal, 80 kg, 2 g/kg protein, 25% fat.
    m = nutrition.macros_from_calories(2000, 80, 2.0, 0.25)
    assert m["p"] == 160          # 2 * 80
    assert m["f"] == round(0.25 * 2000 / 9)   # 56
    # carbs = remaining calories / 4
    assert m["c"] == round(max(0, 2000 - 160 * 4 - m["f"] * 9) / 4)


def test_estimate_targets_known_case():
    # Male, 30y, 180cm, 80kg, moderate.
    est = nutrition.estimate_targets("male", 30, 180, 80, "moderate")
    # BMR = 10*80 + 6.25*180 - 5*30 + 5 = 1780; TDEE = 1780*1.55 = 2759
    assert est["tdee"] == 2759
    assert est["lean"]["p"] == 160   # 2.0 g/kg * 80
    assert est["bulk"]["p"] == 144   # 1.8 g/kg * 80


def test_estimate_targets_female_uses_minus_161():
    est = nutrition.estimate_targets("female", 30, 165, 60, "sedentary")
    # BMR = 10*60 + 6.25*165 - 5*30 - 161 = 1320.25; TDEE = *1.2 = 1584.3
    assert est["tdee"] == round(1320.25 * 1.2)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sex": "", "age": 30, "cm": 180, "kg": 80},
        {"sex": "male", "age": 0, "cm": 180, "kg": 80},
        {"sex": "male", "age": 30, "cm": 0, "kg": 80},
        {"sex": "male", "age": 30, "cm": 180, "kg": 0},
    ],
)
def test_estimate_targets_incomplete_returns_none(kwargs):
    assert nutrition.estimate_targets(**kwargs) is None


def test_estimate_targets_unknown_activity_defaults_to_moderate():
    a = nutrition.estimate_targets("male", 30, 180, 80, "bogus")
    b = nutrition.estimate_targets("male", 30, 180, 80, "moderate")
    assert a == b
