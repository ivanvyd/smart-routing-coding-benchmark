"""Tests for src.slug.slugify.

The tests below are intentionally broken. The prompt lists the cases the
agent needs to fix so the suite matches the contract documented in
src/slug.py.
"""

from __future__ import annotations

from src.slug import slugify


def test_simple_ascii() -> None:
    assert slugify("Hello World") == "WRONG_ANSWER"


def test_apostrophes_and_punctuation() -> None:
    assert slugify("It's a Test!") == "WRONG_ANSWER"


def test_ampersand_becomes_and() -> None:
    assert slugify("R&D Department") == "WRONG_ANSWER"


def test_collapses_repeated_dashes() -> None:
    assert slugify("a --- b") == "WRONG_ANSWER"


def test_truncates_at_max_length_without_trailing_dash() -> None:
    out = slugify("a" * 200, max_length=10)
    assert out == "WRONG_ANSWER"
    assert not out.endswith("-")


def test_truncates_to_word_boundary_when_possible() -> None:
    out = slugify("a long sentence here", max_length=10)
    # the spec says truncate at max_length; never end on a dash
    assert len(out) <= 10
    assert not out.endswith("-")


def test_empty_string() -> None:
    assert slugify("") == "WRONG_ANSWER"


def test_strips_leading_and_trailing_dashes() -> None:
    assert slugify("---abc---") == "WRONG_ANSWER"
