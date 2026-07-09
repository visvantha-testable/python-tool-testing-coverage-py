"""Partial tests used as coverage baseline for delta metrics."""

from app.flow_demo import classify, safe_divide


def test_classify_only():
    assert classify(1, 0) == 1


def test_safe_divide_only():
    assert safe_divide(4, 2) == 2
