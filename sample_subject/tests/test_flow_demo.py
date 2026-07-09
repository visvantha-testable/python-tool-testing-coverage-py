"""Full test suite for 100% statement and branch coverage."""

import pytest

from app.flow_demo import aggregate, classify, make_multiplier, pipeline, safe_divide


def test_classify_above_threshold():
    assert classify(15, 10) == 15


def test_classify_below_threshold():
    assert classify(5, 10, mode="relaxed") == -5


def test_classify_equal_threshold():
    assert classify(10, 10) == 0


def test_classify_strict_negative():
    assert classify(5, 10, mode="strict") == 0


def test_classify_relaxed_overflow():
    assert classify(200, 10, mode="relaxed") == 100


def test_aggregate_empty():
    assert aggregate([]) == []


def test_aggregate_skip_negative():
    assert aggregate([1, -1, 2], skip_negative=True) == [2, 4]


def test_aggregate_include_negative():
    assert aggregate([-2], skip_negative=False) == [-4]


def test_aggregate_zero_item():
    assert aggregate([0]) == [1]


def test_safe_divide_ok():
    assert safe_divide(10, 2) == 5


def test_safe_divide_zero():
    assert safe_divide(10, 0) is None


def test_safe_divide_type_error():
    assert safe_divide(10, "x") == 0


def test_make_multiplier_above():
    fn = make_multiplier(3)
    assert fn(5) == 15


def test_make_multiplier_below():
    fn = make_multiplier(3)
    assert fn(1) == 4


def test_pipeline_no_scaled_append():
    """Cover falsy scaled branch in pipeline."""
    result = pipeline({"value": 10, "threshold": 10, "items": [1], "factor": 2})
    assert result == [4]


def test_pipeline_full():
    result = pipeline({"value": 12, "threshold": 10, "items": [0, 2], "factor": 2})
    assert result == [3, 8, 12]
