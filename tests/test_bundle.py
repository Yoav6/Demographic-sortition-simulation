"""Structural checks on the compiled model bundle (model/build/model.json)."""

import json

import pytest

from popsim import paths

BUNDLE = paths.BUILD / "model.json"
pytestmark = pytest.mark.skipif(not BUNDLE.exists(), reason="bundle not built (run `popsim build` and `popsim export`)")


@pytest.fixture(scope="module")
def bundle():
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


def test_frame_total(bundle):
    frame = bundle["nodes"][0]
    assert frame["type"] == "frame"
    assert sum(frame["weights"]) == bundle["population_total"]
    assert 6_000_000 < bundle["population_total"] < 7_000_000  # eligible resident citizens


def test_parents_defined_before_children(bundle):
    seen = set()
    for n in bundle["nodes"]:
        for p in n.get("parents", []) + ([n["parent"]] if "parent" in n else []):
            assert p in seen, f"{n['id']}: parent {p} not defined before it"
        seen.update(v["id"] for v in n["vars"]) if n["type"] == "frame" else seen.add(n["id"])


def test_table_rows_are_valid(bundle):
    for n in bundle["nodes"]:
        if n["type"] != "table":
            continue
        k = len(n["values"])
        for key, (idx, w) in n["rows"].items():
            assert len(key.split("|")) == len(n["parents"]), f"{n['id']}: bad key {key}"
            assert len(idx) == len(w) > 0, f"{n['id']}[{key}] empty"
            assert all(0 <= i < k for i in idx)
            assert all(isinstance(x, int) and x > 0 for x in w)
            assert sum(w) == pytest.approx(1e9, rel=1e-6)


def test_lookups_cover_parent_domain(bundle):
    domains = {}
    for n in bundle["nodes"]:
        if n["type"] == "frame":
            for v in n["vars"]:
                domains[v["id"]] = len(v["values"])
        elif "values" in n:
            domains[n["id"]] = len(n["values"])
    for n in bundle["nodes"]:
        if n["type"] == "lookup":
            assert len(n["map"]) == domains[n["parent"]]
            assert all(0 <= x < len(n["values"]) for x in n["map"])
