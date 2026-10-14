"""The Python RNG twin must agree with the vectors the TypeScript tests also check."""

import json
from pathlib import Path

from popsim.rng import lowbias32, stream_id, uniform

VECTORS = json.loads((Path(__file__).parent / "rng_vectors.json").read_text(encoding="utf-8"))


def test_lowbias32():
    for x, y in VECTORS["lowbias32"]:
        assert lowbias32(x) == y


def test_stream_id():
    for s, y in VECTORS["stream_id"]:
        assert stream_id(s) == y


def test_uniform():
    for c in VECTORS["uniform"]:
        assert uniform(c["seed"], c["person"], stream_id(c["stream"]), c["k"]) == c["u"]


def test_uniform_range():
    for i in range(2000):
        u = uniform(99, i, 7)
        assert 0.0 <= u < 1.0
