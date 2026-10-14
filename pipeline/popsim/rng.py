"""Python twin of packages/sampler/src/rng.ts (see that file for the design notes).

Both implementations are checked against tests/rng_vectors.json.
"""

from __future__ import annotations

M32 = 0xFFFFFFFF
TWO_32 = 1 << 32
TWO_53 = 1 << 53


def lowbias32(x: int) -> int:
    x &= M32
    x ^= x >> 16
    x = (x * 0x7FEB352D) & M32
    x ^= x >> 15
    x = (x * 0x846CA68B) & M32
    x ^= x >> 16
    return x


def stream_id(name: str) -> int:
    """FNV-1a over UTF-16 code units, matching JavaScript's charCodeAt."""
    h = 0x811C9DC5
    data = name.encode("utf-16-le")
    for i in range(0, len(data), 2):
        h ^= data[i] | (data[i + 1] << 8)
        h = (h * 0x01000193) & M32
    return h


def _chain(seed_hi: int, seed_lo: int, person: int, stream: int, k: int, salt: int) -> int:
    h = lowbias32(salt ^ 0x9E3779B9)
    h = lowbias32(h ^ seed_lo)
    h = lowbias32(h ^ seed_hi)
    h = lowbias32(h ^ (person & M32))
    h = lowbias32(h ^ stream)
    h = lowbias32(h ^ (k & M32))
    return h


def split_seed(seed: int) -> tuple[int, int]:
    if seed < 0 or seed >= TWO_53:
        raise ValueError("seed must be in [0, 2^53)")
    return seed // TWO_32, seed & M32


def uniform(seed: int, person: int, stream: int, k: int = 0) -> float:
    hi, lo = split_seed(seed)
    a = _chain(hi, lo, person, stream, k, 1) >> 5
    b = _chain(hi, lo, person, stream, k, 2) >> 6
    return (a * 67108864 + b) / TWO_53
