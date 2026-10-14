import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { cumulate, lowbias32, pickIndex, streamId, uniform } from "../src/rng.ts";

// Shared with the Python twin (pipeline/popsim/rng.py), which generated these vectors.
const vectors = JSON.parse(readFileSync(new URL("../../../tests/rng_vectors.json", import.meta.url), "utf8"));

describe("rng matches the Python implementation", () => {
  it("lowbias32", () => {
    for (const [x, y] of vectors.lowbias32) expect(lowbias32(x)).toBe(y);
  });
  it("streamId", () => {
    for (const [s, y] of vectors.stream_id) expect(streamId(s)).toBe(y);
  });
  it("uniform", () => {
    for (const c of vectors.uniform) expect(uniform(c.seed, c.person, streamId(c.stream), c.k)).toBe(c.u);
  });
});

describe("pickIndex", () => {
  it("inverts the cumulative distribution", () => {
    const cum = cumulate([1, 0, 3]);
    expect(pickIndex(cum, 0)).toBe(0);
    expect(pickIndex(cum, 0.2499)).toBe(0);
    expect(pickIndex(cum, 0.25)).toBe(2);
    expect(pickIndex(cum, 0.999999)).toBe(2);
  });
  it("is roughly uniform", () => {
    const counts = [0, 0, 0, 0];
    const cum = cumulate([1, 1, 1, 1]);
    for (let i = 0; i < 40000; i++) counts[pickIndex(cum, uniform(7, i, 1))]++;
    for (const c of counts) expect(Math.abs(c - 10000)).toBeLessThan(400);
  });
});
