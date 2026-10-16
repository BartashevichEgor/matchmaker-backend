from math import sqrt


def cosine(left: dict[int, int], right: dict[int, int]) -> float:
    """Sparse vectors share the complete skills catalogue as their coordinate system."""
    denominator = sqrt(sum(v * v for v in left.values())) * sqrt(sum(v * v for v in right.values()))
    if denominator == 0:
        return 0.0
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    return max(0.0, min(1.0, dot / denominator))
