"""Control-flow patterns: statements, branches, loops, exceptions, cross-function."""


def classify(value, threshold, mode="strict"):
    """Nested branches for boolean and decision coverage."""
    total = 0
    if value > threshold:
        total += value
    elif value < threshold:
        total -= value
    else:
        total = 0

    if mode == "strict" and total < 0:
        return 0
    if mode == "relaxed" and total > 100:
        return 100
    return total


def aggregate(items, skip_negative=True):
    """Loop paths: zero-trip, one-trip, and multi-trip."""
    result = []
    for item in items:
        if skip_negative and item < 0:
            continue
        if item == 0:
            result.append(1)
        else:
            result.append(item * 2)
    return result


def safe_divide(a, b):
    """Exception path handling."""
    try:
        return a / b
    except ZeroDivisionError:
        return None
    except TypeError:
        return 0


def make_multiplier(factor):
    """Cross-function use via closure."""

    def multiply(value):
        if value > factor:
            return value * factor
        return value + factor

    return multiply


def pipeline(data):
    """Multi-function execution path."""
    scaled = classify(data.get("value", 0), data.get("threshold", 10))
    items = aggregate(data.get("items", []))
    multiplier = make_multiplier(data.get("factor", 2))
    mapped = [multiplier(x) for x in items]
    if scaled:
        mapped.append(scaled)
    return mapped
