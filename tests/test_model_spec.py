"""dag.yaml parsing rules."""

import pytest

from popsim.model_spec import load_spec

HEAD = """version: test
reference_date: 2024-12-31
population: {label: {en: test, he: test}}
nodes:
  - id: frame
    type: frame
    label: {en: frame, he: frame}
    vars:
      - {id: sex, label: {en: sex, he: sex}, values: [{id: male, label: {en: m, he: m}}]}
"""


def multi(node_id: str, items: list[str], extra: str = "") -> str:
    vals = "".join(f"\n      - {{id: {i}, label: {{en: {i}, he: {i}}}}}" for i in items)
    return f"""  - id: {node_id}
    type: multi
    parents: [sex]
    label: {{en: {node_id}, he: {node_id}}}{extra}
    values:{vals}
"""


def test_subset_of_needs_matching_items(tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text(HEAD + multi("uses", ["a", "b"]) + multi("news", ["a", "b"], "\n    subset_of: uses"))
    assert load_spec(good).node("news").raw["subset_of"] == "uses"

    bad = tmp_path / "bad.yaml"
    bad.write_text(HEAD + multi("uses", ["a", "b"]) + multi("news", ["b", "a"], "\n    subset_of: uses"))
    with pytest.raises(ValueError, match="same items"):
        load_spec(bad)


def test_subset_of_must_come_earlier(tmp_path):
    p = tmp_path / "order.yaml"
    p.write_text(HEAD + multi("news", ["a"], "\n    subset_of: uses") + multi("uses", ["a"]))
    with pytest.raises(ValueError, match="earlier"):
        load_spec(p)
