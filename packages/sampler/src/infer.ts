/**
 * Conditional queries ("what are the odds?") by likelihood weighting.
 *
 * Each sample walks the network like the sampler does, except that a node with evidence
 * is forced into the allowed values and the sample's weight is multiplied by the
 * probability of that evidence given the node's parents. Weighted tallies of all other
 * variables then estimate their distribution given the evidence.
 *
 * Evidence on frame variables (and on lookups of them, e.g. district) is handled
 * exactly by restricting the frame rows. Results are deterministic for a given seed.
 */

import { PROB_SCALE, lookupRow, type CompiledModel, type Dist, type LookupNode, type ModelNode } from "./model.ts";
import { pickIndex, uniform } from "./rng.ts";
import { intervalBounds, intervalCdf, intervalQuantile, intervalValue, logitWeights, nodeStream, percentileValue, roundTo } from "./sample.ts";

/** Allowed value ids for categorical/multi vars (multi: items that must be present), or a numeric range. */
export type Constraint = { ids: string[] } | { min?: number; max?: number };
export type Evidence = Record<string, Constraint>;

export interface Marginal {
  id: string;
  /** Categorical: probability per value (same order as the domain). Multi: inclusion probability per item. */
  probs?: number[];
  /** Numeric: weighted quantiles at 5,25,50,75,95 and the weighted mean, among people the number applies to. */
  quantiles?: number[];
  mean?: number;
  /** Numeric: share of people the number applies to (e.g. earnings: the employed). */
  applicable?: number;
}

export interface QueryResult {
  samples: number;
  effectiveSampleSize: number;
  evidenceProbability: number; // estimated P(evidence), i.e. the share of the population matching
  marginals: Record<string, Marginal>;
}

interface Prepared {
  frameRows: Int32Array; // allowed frame rows
  frameCum: Float64Array;
  frameMass: number; // P(frame evidence)
  allowed: Map<number, Set<number>>; // var index -> allowed value indices (non-frame categorical)
  ranges: Map<number, [number, number]>; // var index -> numeric range
}

function prepare(model: CompiledModel, evidence: Evidence): Prepared {
  const allowed = new Map<number, Set<number>>();
  const ranges = new Map<number, [number, number]>();
  const frameAllowed = new Map<string, Set<number>>();
  const frame = model.bundle.nodes.find((n) => n.type === "frame")!;
  if (frame.type !== "frame") throw new Error("unreachable");
  const frameVars = new Set(frame.vars.map((v) => v.id));

  for (const [id, c] of Object.entries(evidence)) {
    const vi = model.varIndex.get(id);
    if (vi === undefined) throw new Error(`unknown variable ${id}`);
    const info = model.vars[vi];
    if ("ids" in c) {
      if (!info.values) throw new Error(`${id} is numeric; use a range`);
      const set = new Set<number>();
      for (const vid of c.ids) {
        const k = info.values.findIndex((v) => v.id === vid);
        if (k < 0) throw new Error(`${id} has no value ${vid}`);
        set.add(k);
      }
      if (frameVars.has(id)) {
        frameAllowed.set(id, set);
      } else if (info.node.type === "lookup" && frameVars.has((info.node as LookupNode).parent)) {
        // e.g. district -> the localities in those districts
        const ln = info.node as LookupNode;
        const parentSet = new Set<number>();
        ln.map.forEach((v, parentValue) => {
          if (set.has(v)) parentSet.add(parentValue);
        });
        const prev = frameAllowed.get(ln.parent);
        frameAllowed.set(ln.parent, prev ? new Set([...prev].filter((x) => parentSet.has(x))) : parentSet);
      } else {
        allowed.set(vi, set);
      }
    } else {
      let lo = c.min ?? -Infinity;
      let hi = c.max ?? Infinity;
      if (info.values && info.numeric) {
        // numeric table node (e.g. single-year age): convert the range into allowed values
        const set = new Set<number>();
        info.values.forEach((v, k) => {
          const x = Number(v.id);
          if (x >= lo && x <= hi) set.add(k);
        });
        allowed.set(vi, set);
        continue;
      }
      if (info.node.type === "percentile") {
        // percentile is monotone in its parent: convert to a range on the parent value
        const node = info.node;
        const b = node.breakpoints;
        const at = (p: number) => {
          const x = (p / 100) * (b.length - 1);
          const i = Math.min(Math.floor(x), b.length - 2);
          return b[i] + (x - i) * (b[i + 1] - b[i]);
        };
        const pv = model.varIndex.get(node.parent)!;
        lo = Number.isFinite(lo) ? at(Math.max(0, lo)) : -Infinity;
        hi = Number.isFinite(hi) ? at(Math.min(100, hi)) : Infinity;
        ranges.set(pv, [lo, hi]);
        continue;
      }
      ranges.set(vi, [lo, hi]);
    }
  }

  const n = frame.weights.length;
  const rows: number[] = [];
  for (let r = 0; r < n; r++) {
    let ok = true;
    for (const [vid, set] of frameAllowed) {
      if (!set.has(frame.rows[vid][r])) {
        ok = false;
        break;
      }
    }
    if (ok && frame.weights[r] > 0) rows.push(r);
  }
  const frameRows = Int32Array.from(rows);
  const frameCum = new Float64Array(rows.length);
  let s = 0;
  rows.forEach((r, i) => {
    s += frame.weights[r];
    frameCum[i] = s;
  });
  const total = model.frameCum[model.frameCum.length - 1];
  return { frameRows, frameCum, frameMass: s / total, allowed, ranges };
}

/** Draws from integer weights restricted to an allowed set; returns [index, mass fraction]. */
function restrictedPick(weights: ArrayLike<number>, valueIds: ArrayLike<number>, allowed: Set<number>, u: number): [number, number] {
  let total = 0;
  let kept = 0;
  const keptIdx: number[] = [];
  const keptCum: number[] = [];
  for (let j = 0; j < weights.length; j++) {
    total += weights[j];
    if (allowed.has(valueIds[j]) && weights[j] > 0) {
      kept += weights[j];
      keptIdx.push(j);
      keptCum.push(kept);
    }
  }
  if (kept === 0) return [-1, 0];
  return [keptIdx[pickIndex(keptCum, u)], kept / total];
}

export function query(model: CompiledModel, evidence: Evidence, samples = 100_000, seed = 1): QueryResult {
  const prep = prepare(model, evidence);
  const nv = model.vars.length;
  const tallies = model.vars.map((v) => (v.values ? new Float64Array(v.values.length) : null));
  const numeric: { x: number; w: number }[][] = model.vars.map(() => []);
  let sumW = 0;
  let sumW2 = 0;
  const values = new Float64Array(nv);

  if (prep.frameRows.length === 0) {
    return { samples, effectiveSampleSize: 0, evidenceProbability: 0, marginals: {} };
  }

  for (let i = 0; i < samples; i++) {
    let w = prep.frameMass;
    for (const node of model.bundle.nodes) {
      if (w === 0) break;
      w = drawNode(model, node, values, seed, i, prep, w);
    }
    if (w === 0) continue;
    sumW += w;
    sumW2 += w * w;
    for (let k = 0; k < nv; k++) {
      const info = model.vars[k];
      const t = tallies[k];
      if (info.multi && t) {
        const mask = values[k];
        for (let j = 0; j < t.length; j++) if (mask & (1 << j)) t[j] += w;
      } else if (t) {
        t[values[k]] += w;
      } else if (!Number.isNaN(values[k])) {
        numeric[k].push({ x: values[k], w });
      }
    }
  }

  const marginals: Record<string, Marginal> = {};
  model.vars.forEach((info, k) => {
    const t = tallies[k];
    if (t) {
      marginals[info.id] = { id: info.id, probs: Array.from(t, (x) => (sumW > 0 ? x / sumW : 0)) };
    } else {
      // quantiles among people to whom the number applies (NaN = not applicable)
      const pts = numeric[k].sort((a, b) => a.x - b.x);
      const sumA = pts.reduce((a, pt) => a + pt.w, 0);
      const q = [0.05, 0.25, 0.5, 0.75, 0.95].map((p) => {
        let acc = 0;
        for (const pt of pts) {
          acc += pt.w;
          if (acc >= p * sumA) return pt.x;
        }
        return pts.length ? pts[pts.length - 1].x : NaN;
      });
      const mean = pts.reduce((a, pt) => a + pt.x * pt.w, 0) / (sumA || 1);
      marginals[info.id] = { id: info.id, quantiles: q, mean, applicable: sumW > 0 ? sumA / sumW : 0 };
    }
  });

  return {
    samples,
    effectiveSampleSize: sumW2 > 0 ? (sumW * sumW) / sumW2 : 0,
    evidenceProbability: sumW / samples,
    marginals,
  };
}

function drawNode(
  model: CompiledModel,
  node: ModelNode,
  values: Float64Array,
  seed: number,
  i: number,
  prep: Prepared,
  w: number,
): number {
  const stream = nodeStream(node.id);
  const vi = node.type === "frame" ? -1 : model.varIndex.get(node.id)!;
  switch (node.type) {
    case "frame": {
      const r = prep.frameRows[pickIndex(prep.frameCum, uniform(seed, i, stream, 0))];
      for (const v of node.vars) values[model.varIndex.get(v.id)!] = node.rows[v.id][r];
      return w;
    }
    case "lookup": {
      values[vi] = node.map[values[model.varIndex.get(node.parent)!]];
      const set = prep.allowed.get(vi);
      return set && !set.has(values[vi]) ? 0 : w;
    }
    case "table": {
      const dist = lookupRow<Dist>(model.tables.get(node.id)!, values);
      const u = uniform(seed, i, stream, 0);
      const set = prep.allowed.get(vi);
      if (!set) {
        values[vi] = dist.values[pickIndex(dist.cum, u)];
        return w;
      }
      const weights = new Float64Array(dist.cum.length);
      for (let j = 0; j < weights.length; j++) weights[j] = dist.cum[j] - (j ? dist.cum[j - 1] : 0);
      const [j, mass] = restrictedPick(weights, dist.values, set, u);
      if (j < 0) return 0;
      values[vi] = dist.values[j];
      return w * mass;
    }
    case "logit": {
      const weights = logitWeights(node, model, values);
      const u = uniform(seed, i, stream, 0);
      const set = prep.allowed.get(vi);
      const ids = Int32Array.from(weights, (_, j) => j);
      const [j, mass] = restrictedPick(weights, ids, set ?? new Set(ids), u);
      if (j < 0) return 0;
      values[vi] = j;
      return w * mass;
    }
    case "interval": {
      const range = prep.ranges.get(vi);
      const u = uniform(seed, i, stream, 0);
      if (!range) {
        values[vi] = intervalValue(node, model, values, u);
        return w;
      }
      const b = intervalBounds(node, model, values);
      if (!b) return 0; // the number does not apply, so no range can hold
      if (!(b.hi > b.lo)) {
        if (b.lo < range[0] || b.lo > range[1]) return 0;
        values[vi] = roundTo(node, b.lo, b);
        return w;
      }
      const a = Math.max(b.lo, range[0]);
      const z = Math.min(b.hi, range[1]);
      if (!(z > a)) return 0;
      const fa = intervalCdf(node, b, a);
      const mass = intervalCdf(node, b, z) - fa;
      values[vi] = roundTo(node, intervalQuantile(node, b, fa + u * mass), b);
      return w * mass;
    }
    case "percentile":
      values[vi] = percentileValue(node, values[model.varIndex.get(node.parent)!]);
      return w;
    case "multi": {
      const probs = lookupRow<Float64Array>(model.tables.get(node.id)!, values);
      const required = prep.allowed.get(vi);
      let mask = 0;
      for (let k = 0; k < node.items.length; k++) {
        if (required && required.has(k)) {
          mask |= 1 << k;
          w *= probs[k] / PROB_SCALE;
        } else if (Math.floor(uniform(seed, i, stream, k) * PROB_SCALE) < probs[k]) {
          mask |= 1 << k;
        }
      }
      values[vi] = mask;
      return w;
    }
  }
}
