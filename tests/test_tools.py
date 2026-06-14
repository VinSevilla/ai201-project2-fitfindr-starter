from unittest.mock import MagicMock, patch

import pytest

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

# ── helpers ───────────────────────────────────────────────────────────────────

FAKE_ITEM = {
    "title": "Vintage Band Tee",
    "category": "tops",
    "colors": ["black", "white"],
    "style_tags": ["vintage", "graphic", "streetwear"],
    "price": 18.0,
    "platform": "depop",
}


def _mock_groq(response_text):
    """Return a fake Groq client whose first completion returns response_text."""
    mock = MagicMock()
    mock.chat.completions.create.return_value.choices[0].message.content = response_text
    return mock


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter_case_insensitive():
    results = search_listings("top", size="m", max_price=None)
    assert all("m" in item["size"].lower() for item in results)


def test_search_no_optional_args():
    results = search_listings("vintage")
    assert isinstance(results, list)


# ── suggest_outfit ────────────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe_returns_string():
    with patch("tools._get_groq_client", return_value=_mock_groq("Outfit 1: tee + baggy jeans + chunky sneakers")):
        result = suggest_outfit(FAKE_ITEM, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_empty_wardrobe_returns_nonempty_string():
    # Failure mode: wardrobe is empty — should return general advice, not "" or an exception
    with patch("tools._get_groq_client", return_value=_mock_groq("Pair with high-waisted jeans for a 90s look.")):
        result = suggest_outfit(FAKE_ITEM, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_fit_card_empty_outfit_returns_error_string():
    # Failure mode: empty outfit — should return error message, not raise
    result = create_fit_card("", FAKE_ITEM)
    assert isinstance(result, str)
    assert "Error" in result


def test_fit_card_whitespace_outfit_returns_error_string():
    # Failure mode: whitespace-only outfit — same guard as empty
    result = create_fit_card("   ", FAKE_ITEM)
    assert isinstance(result, str)
    assert "Error" in result


def test_fit_card_returns_string():
    outfit = "Pair with baggy jeans and chunky sneakers for a 90s vibe."
    with patch("tools._get_groq_client", return_value=_mock_groq("scored this vintage band tee on depop for $18 and it's everything")):
        result = create_fit_card(outfit, FAKE_ITEM)
    assert isinstance(result, str)
    assert len(result) > 0
