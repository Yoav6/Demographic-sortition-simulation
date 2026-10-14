import numpy as np

from popsim.estimate.common import ipf


def test_ipf_matches_margins():
    rng = np.random.default_rng(0)
    seed = rng.random((4, 3)) + 0.1
    rows = np.array([10.0, 20.0, 30.0, 40.0])
    cols = np.array([50.0, 30.0, 20.0])
    fitted = ipf(seed, [((0,), rows), ((1,), cols)])
    assert np.allclose(fitted.sum(axis=1), rows, rtol=1e-6)
    assert np.allclose(fitted.sum(axis=0), cols, rtol=1e-6)


def test_ipf_keeps_structural_zeros():
    seed = np.array([[1.0, 0.0], [1.0, 1.0]])
    fitted = ipf(seed, [((0,), np.array([5.0, 5.0])), ((1,), np.array([7.0, 3.0]))])
    assert fitted[0, 1] == 0.0
