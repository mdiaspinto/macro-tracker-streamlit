"""Tests for food importing — offline lookup and Open Food Facts (mocked)."""


from macro_tracker import foods

# ---- offline lookup -----------------------------------------------------

def test_offline_lookup_exact():
    assert foods.offline_lookup("chicken breast") == (31, 0, 3.6)


def test_offline_lookup_is_case_and_space_insensitive():
    assert foods.offline_lookup("  Chicken Breast ") == (31, 0, 3.6)


def test_offline_lookup_longest_substring_wins():
    # "grilled chicken breast" should match "chicken breast", not "chicken".
    assert foods.offline_lookup("grilled chicken breast") == (31, 0, 3.6)


def test_offline_lookup_unknown_returns_none():
    assert foods.offline_lookup("dragonfruit surprise") is None


def test_offline_lookup_empty_returns_none():
    assert foods.offline_lookup("") is None
    assert foods.offline_lookup("   ") is None


def test_scale_per_100g():
    assert foods.scale_per_100g((31, 0, 3.6), 200) == (62.0, 0.0, 7.2)
    assert foods.scale_per_100g((10, 20, 5), 50) == (5.0, 10.0, 2.5)


# ---- Open Food Facts (network isolated behind an injected fetcher) -------

def _payload(p, c, f):
    return {"products": [{"nutriments": {
        "proteins_100g": p, "carbohydrates_100g": c, "fat_100g": f}}]}


def test_parse_openfoodfacts_ok():
    assert foods.parse_openfoodfacts(_payload(20, 5, 3)) == (20.0, 5.0, 3.0)


def test_parse_openfoodfacts_no_products():
    assert foods.parse_openfoodfacts({"products": []}) is None
    assert foods.parse_openfoodfacts(None) is None


def test_parse_openfoodfacts_missing_nutriment():
    assert foods.parse_openfoodfacts({"products": [{"nutriments": {}}]}) is None


def test_search_uses_online_when_available():
    result = foods.search_openfoodfacts("anything", fetcher=lambda name: _payload(50, 10, 2))
    assert result == (50.0, 10.0, 2.0)


def test_search_falls_back_to_offline_on_empty_online():
    result = foods.search_openfoodfacts("chicken breast", fetcher=lambda name: {"products": []})
    assert result == (31, 0, 3.6)


def test_search_falls_back_to_offline_on_network_error():
    import requests

    def boom(name):
        raise requests.RequestException("no network")

    assert foods.search_openfoodfacts("rice", fetcher=boom) == (2.7, 28, 0.3)


def test_search_returns_none_when_online_empty_and_offline_unknown():
    result = foods.search_openfoodfacts("dragonfruit surprise", fetcher=lambda name: None)
    assert result is None
