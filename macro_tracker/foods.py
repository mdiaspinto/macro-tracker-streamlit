"""Food data import — offline table and Open Food Facts lookup.

These are the "data importing" functions the test suite targets. The network
call is isolated behind an injectable ``fetcher`` so tests run fully offline.
"""

from __future__ import annotations

from collections.abc import Callable

import requests

# Per-100g macros as (protein_g, carbs_g, fat_g). Ported from the JS app.
OFFLINE_FOODS: dict[str, tuple[float, float, float]] = {
    "chicken breast": (31, 0, 3.6), "chicken thigh": (26, 0, 11), "chicken": (27, 0, 7),
    "turkey breast": (29, 0, 1), "turkey": (29, 0, 7), "beef": (26, 0, 15),
    "ground beef": (26, 0, 15), "steak": (27, 0, 11), "pork": (27, 0, 9),
    "pork chop": (27, 0, 9), "bacon": (37, 1.4, 42), "salmon": (20, 0, 13),
    "tuna": (26, 0, 1), "cod": (18, 0, 0.7), "white fish": (18, 0, 0.7),
    "shrimp": (24, 0.2, 0.3), "egg": (13, 1.1, 11), "eggs": (13, 1.1, 11),
    "egg white": (11, 0.7, 0.2), "milk": (3.4, 5, 3.6), "whole milk": (3.4, 5, 3.6),
    "skim milk": (3.4, 5, 0.1), "greek yogurt": (10, 3.6, 0.4), "yogurt": (10, 3.6, 0.4),
    "cheese": (25, 1.3, 33), "cheddar": (25, 1.3, 33), "cottage cheese": (11, 3.4, 4.3),
    "butter": (0.9, 0.1, 81), "rice": (2.7, 28, 0.3), "white rice": (2.7, 28, 0.3),
    "brown rice": (2.6, 23, 0.9), "pasta": (5, 25, 1.1), "spaghetti": (5, 25, 1.1),
    "bread": (9, 49, 3.2), "white bread": (9, 49, 3.2), "oats": (13, 67, 7),
    "oatmeal": (13, 67, 7), "quinoa": (4.4, 21, 1.9), "potato": (2, 17, 0.1),
    "sweet potato": (1.6, 20, 0.1), "corn": (3.4, 19, 1.5), "banana": (1.1, 23, 0.3),
    "apple": (0.3, 14, 0.2), "orange": (0.9, 12, 0.1), "strawberries": (0.7, 8, 0.3),
    "blueberries": (0.7, 14, 0.3), "grapes": (0.7, 18, 0.2), "avocado": (2, 9, 15),
    "broccoli": (2.8, 7, 0.4), "spinach": (2.9, 3.6, 0.4), "carrot": (0.9, 10, 0.2),
    "tomato": (0.9, 3.9, 0.2), "lettuce": (1.4, 2.9, 0.2), "cucumber": (0.7, 3.6, 0.1),
    "onion": (1.1, 9, 0.1), "black beans": (9, 24, 0.5), "beans": (9, 24, 0.5),
    "lentils": (9, 20, 0.4), "chickpeas": (9, 27, 2.6), "tofu": (8, 2, 4.8),
    "almonds": (21, 22, 49), "peanut butter": (25, 20, 50), "peanuts": (26, 16, 49),
    "walnuts": (15, 14, 65), "olive oil": (0, 0, 100), "honey": (0.3, 82, 0),
    "sugar": (0, 100, 0), "whey protein": (80, 8, 6), "protein powder": (80, 8, 6),
    "protein shake": (80, 8, 6),
}

OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"

# A fetcher takes a food name and returns the decoded JSON (or None on failure).
Fetcher = Callable[[str], dict | None]


def offline_lookup(name: str) -> tuple[float, float, float] | None:
    """Per-100g macros from the offline table.

    Exact match first, otherwise the longest key that overlaps the query as a
    substring (either direction). Returns ``None`` if nothing matches.
    """
    q = (name or "").strip().lower()
    if not q:
        return None
    if q in OFFLINE_FOODS:
        return OFFLINE_FOODS[q]
    best: tuple[float, float, float] | None = None
    best_len = 0
    for key, macros in OFFLINE_FOODS.items():
        if (q in key or key in q) and len(key) > best_len:
            best, best_len = macros, len(key)
    return best


def scale_per_100g(
    per_100g: tuple[float, float, float], grams: float
) -> tuple[float, float, float]:
    """Scale per-100g macros to an arbitrary portion size in grams."""
    factor = grams / 100.0
    p, c, f = per_100g
    return (round(p * factor, 2), round(c * factor, 2), round(f * factor, 2))


def _default_fetcher(name: str) -> dict | None:
    resp = requests.get(
        OPEN_FOOD_FACTS_URL,
        params={
            "search_terms": name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 1,
        },
        timeout=8,
    )
    resp.raise_for_status()
    return resp.json()


def parse_openfoodfacts(payload: dict | None) -> tuple[float, float, float] | None:
    """Extract per-100g (protein, carbs, fat) from an Open Food Facts payload."""
    if not payload:
        return None
    products = payload.get("products") or []
    if not products:
        return None
    n = products[0].get("nutriments") or {}
    try:
        return (
            float(n["proteins_100g"]),
            float(n["carbohydrates_100g"]),
            float(n["fat_100g"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def search_openfoodfacts(
    name: str,
    fetcher: Fetcher = _default_fetcher,
) -> tuple[float, float, float] | None:
    """Look up per-100g macros online, falling back to the offline table.

    ``fetcher`` is injectable so tests never touch the network.
    """
    try:
        macros = parse_openfoodfacts(fetcher(name))
    except (requests.RequestException, ValueError):
        macros = None
    return macros if macros is not None else offline_lookup(name)
