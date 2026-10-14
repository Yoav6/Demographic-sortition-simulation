import { describe, expect, it } from "vitest";
import { compile, type Bundle } from "../src/model.ts";
import { query } from "../src/infer.ts";

// A tiny network small enough to enumerate exactly:
//   frame: region (a, b) x sex (m, f)  ->  smoker | region, sex  ->  cough | smoker
const lab = (s: string) => ({ en: s, he: s });
const vals = (...ids: string[]) => ids.map((id) => ({ id, label: lab(id) }));
const bundle: Bundle = {
  format: "popsim-model/1",
  version: "test",
  reference_date: "2024-12-31",
  population_label: lab("test"),
  population_total: 100,
  sources: [],
  nodes: [
    {
      id: "frame",
      type: "frame",
      label: lab("frame"),
      vars: [
        { id: "region", label: lab("region"), values: vals("a", "b") },
        { id: "sex", label: lab("sex"), values: vals("male", "female") },
      ],
      rows: { region: [0, 0, 1, 1], sex: [0, 1, 0, 1] },
      weights: [30, 20, 10, 40],
    },
    {
      id: "smoker",
      type: "table",
      label: lab("smoker"),
      parents: ["region", "sex"],
      values: vals("yes", "no"),
      rows: {
        "0|0": [[0, 1], [400_000_000, 600_000_000]],
        "0|1": [[0, 1], [200_000_000, 800_000_000]],
        "1|0": [[0, 1], [500_000_000, 500_000_000]],
        "1|1": [[0, 1], [100_000_000, 900_000_000]],
      },
    },
    {
      id: "cough",
      type: "table",
      label: lab("cough"),
      parents: ["smoker"],
      values: vals("yes", "no"),
      rows: { "0": [[0, 1], [700_000_000, 300_000_000]], "1": [[0, 1], [100_000_000, 900_000_000]] },
    },
  ],
};

function exact(evidence: (r: number, s: number, sm: number, c: number) => boolean) {
  const frameW = [0.3, 0.2, 0.1, 0.4];
  const sm = [[0.4, 0.6], [0.2, 0.8], [0.5, 0.5], [0.1, 0.9]];
  const co = [[0.7, 0.3], [0.1, 0.9]];
  let total = 0;
  const region = [0, 0];
  for (let row = 0; row < 4; row++) {
    const r = row >> 1;
    const s = row & 1;
    for (let a = 0; a < 2; a++) for (let c = 0; c < 2; c++) {
      const p = frameW[row] * sm[row][a] * co[a][c];
      if (evidence(r, s, a, c)) {
        total += p;
        region[r] += p;
      }
    }
  }
  return { total, region: region.map((x) => x / total) };
}

describe("likelihood-weighted queries", () => {
  const model = compile(bundle);

  it("conditions on a downstream node (cough = yes)", () => {
    const res = query(model, { cough: { ids: ["yes"] } }, 200_000, 3);
    const ex = exact((_r, _s, _a, c) => c === 0);
    expect(res.evidenceProbability).toBeCloseTo(ex.total, 2);
    expect(res.marginals.region.probs![0]).toBeCloseTo(ex.region[0], 2);
  });

  it("conditions on a frame variable exactly", () => {
    const res = query(model, { sex: { ids: ["female"] } }, 50_000, 5);
    expect(res.evidenceProbability).toBeCloseTo(0.6, 6);
    expect(res.marginals.region.probs![0]).toBeCloseTo(0.2 / 0.6, 2);
  });

  it("combines frame and downstream evidence", () => {
    const res = query(model, { sex: { ids: ["male"] }, smoker: { ids: ["yes"] } }, 200_000, 9);
    const ex = exact((_r, s, a) => s === 0 && a === 0);
    expect(res.evidenceProbability).toBeCloseTo(ex.total, 2);
    expect(res.marginals.region.probs![0]).toBeCloseTo(ex.region[0], 2);
  });
});
