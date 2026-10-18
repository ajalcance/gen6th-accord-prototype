"""Validate stored normalized vectors before exact similarity arithmetic."""

import math

from accord.personas.face_contracts import FaceResult

Vectors = tuple[tuple[float, ...], ...]


def unit_vector(value: object, dimensions: int) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != dimensions:
        raise RuntimeError("invalid representation dimensions")
    if any(
        isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
        for v in value
    ):
        raise RuntimeError("invalid representation values")
    vector = tuple(float(v) for v in value)
    if abs(math.fsum(v * v for v in vector) - 1) > 1e-6:
        raise RuntimeError("invalid representation normalization")
    return vector


def stored_vectors(result: FaceResult, value: object) -> Vectors:
    if not isinstance(value, (list, tuple)):
        raise RuntimeError("invalid stored vectors")
    if result.representation is None:
        if value:
            raise RuntimeError("unexpected stored vectors")
        return ()
    if len(value) != 2:
        raise RuntimeError("dual representation required")
    return tuple(unit_vector(v, result.representation.dimensions) for v in value)


def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or not left:
        raise RuntimeError("incompatible representations")
    # Only absorb floating point rounding at the endpoints, never malformed input.
    unit_vector(left, len(left))
    unit_vector(right, len(right))
    return max(-1.0, min(1.0, math.fsum(a * b for a, b in zip(left, right, strict=True))))
