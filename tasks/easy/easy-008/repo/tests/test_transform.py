"""Tests for src.transform."""

from __future__ import annotations

import csv
import io

from src.transform import flatten, flatten_and_to_csv, records_to_csv


def test_flatten_simple() -> None:
    assert flatten({"a": 1, "b": {"c": 2}}) == {"a": 1, "b.c": 2}


def test_flatten_list_of_primitives() -> None:
    assert flatten({"a": [1, 2, 3]}) == {"a": "1|2|3"}


def test_flatten_list_of_dicts() -> None:
    assert flatten({"a": [{"x": 1}, {"x": 2}]}) == {"a.0.x": 1, "a.1.x": 2}


def test_records_to_csv_stable_header() -> None:
    csv_text = records_to_csv([{"a": 1, "b": {"c": 2}}, {"a": 3, "b": {"c": 4}}])
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert rows == [{"a": "1", "b.c": "2"}, {"a": "3", "b.c": "4"}]


def test_flatten_and_to_csv_from_string() -> None:
    out = flatten_and_to_csv('[{"a": 1, "b": {"c": 2}}]')
    rows = list(csv.DictReader(io.StringIO(out)))
    assert rows == [{"a": "1", "b.c": "2"}]


def test_records_to_csv_empty() -> None:
    assert records_to_csv([]) == ""
