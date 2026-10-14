/**
 * Ancestral sampling: walk the nodes in order, drawing each from its distribution given
 * the values already drawn for its parents.
 *
 * A person is a Float64Array indexed like `model.vars`:
 *   categorical -> value index, numeric -> the number, multi -> bitmask of chosen items.
 */

import {
  PROB_SCALE,
  lookupRow,
  type CompiledModel,
  type Dist,
  type IntervalNode,
  type LogitNode,
  type PercentileNode,
} from "./model.ts";
import { cumulate, pickIndex, streamId, uniform } from "./rng.ts";

export type PersonValues = Float64Array;

const streamCache = new Map<string, number>();
export function nodeStream(id: string): number {
  let s = streamCache.get(id);
  if (s === undefined) {
    s = streamId(id);
    streamCache.set(id, s);
  }
  return s;
}

export function logitWeights(node: LogitNode, model: CompiledModel, values: ArrayLike<number>): Float64Array {
  const k = node.values.length;
  const scores = Float64Array.from(node.intercept);
  for (const p of node.parents) {
    const table = node.coef[p];
    if (!table) continue;
    const row = table[values[model.varIndex.get(p)!]];
    if (!row) continue;
    for (let j = 0; j < k; j++) scores[j] += row[j];
  }
  let max = -Infinity;
  for (let j = 0; j < k; j++) if (scores[j] > max) max = scores[j];
  let sum = 0;
  const p = new Float64Array(k);
  for (let j = 0; j < k; j++) {
    p[j] = Math.exp(scores[j] - max);
    sum += p[j];
  }
  const w = new Float64Array(k);
  for (let j = 0; j < k; j++) w[j] = Math.round((p[j] / sum) * PROB_SCALE);
  return w;
}

/** The range a person's number is drawn from (see intervalBounds). */
export interface Bounds {
  lo: number;
  hi: number;
  pareto: boolean; // open-ended bracket: Pareto tail truncated at hi
}

/**
 * The interval of the parent value, narrowed by the node's optional cap (an upper bound set by
 * another categorical variable) and floor (a lower bound set by another number). null when the
 * number does not apply (e.g. earnings of people who are not employed).
 */
export function intervalBounds(node: IntervalNode, model: CompiledModel, values: ArrayLike<number>): Bounds | null {
  const iv = node.intervals[values[model.varIndex.get(node.parent)!]];
  if (!iv) return null;
  let lo = iv[0];
  const pareto = iv[1] === null;
  let hi = pareto ? lo * Math.pow(1 - (node.tail_u_max ?? 0.999), -1 / (node.tail_alpha ?? 3)) : (iv[1] as number);
  if (node.cap) {
    const c = node.cap.upper[values[model.varIndex.get(node.cap.var)!]];
    if (c !== null && c !== undefined) hi = Math.min(hi, c);
  }
  if (node.floor) {
    const f = values[model.varIndex.get(node.floor)!];
    if (!Number.isNaN(f)) lo = Math.max(lo, Math.min(f, hi));
  }
  return { lo, hi, pareto };
}

/** Inverse CDF of the within-interval distribution: truncated Pareto, log-uniform or uniform.
 * Mirrored by _quantile()/_cdf() in pipeline/popsim/estimate/socioeconomic.py (percentile breakpoints). */
export function intervalQuantile(node: IntervalNode, b: Bounds, v: number): number {
  const { lo, hi } = b;
  if (!(hi > lo)) return lo;
  if (b.pareto) {
    const a = node.tail_alpha ?? 3;
    return lo * Math.pow(1 - v * (1 - Math.pow(lo / hi, a)), -1 / a);
  }
  if (node.scale === "log" && lo > 0) return Math.exp(Math.log(lo) + v * (Math.log(hi) - Math.log(lo)));
  return lo + v * (hi - lo);
}

/** CDF matching intervalQuantile (0 below lo, 1 above hi). */
export function intervalCdf(node: IntervalNode, b: Bounds, x: number): number {
  const { lo, hi } = b;
  if (x <= lo) return 0;
  if (x >= hi) return 1;
  if (b.pareto) {
    const a = node.tail_alpha ?? 3;
    return (1 - Math.pow(lo / x, a)) / (1 - Math.pow(lo / hi, a));
  }
  if (node.scale === "log" && lo > 0) return (Math.log(x) - Math.log(lo)) / (Math.log(hi) - Math.log(lo));
  return (x - lo) / (hi - lo);
}

/** Rounds to the node's step, staying inside the interval (a value rounded across a bracket
 * edge would contradict the bracket's label). */
export function roundTo(node: IntervalNode, x: number, b?: Bounds): number {
  if (!node.round) return x;
  const step = node.round;
  let r = Math.round(x / step) * step;
  if (b) {
    if (r < b.lo) r = Math.ceil(b.lo / step) * step;
    if (r > b.hi) r = Math.floor(b.hi / step) * step;
    if (r < b.lo) r = b.lo; // interval narrower than one step
  }
  return r;
}

/** The person's number (NaN when it does not apply). */
export function intervalValue(node: IntervalNode, model: CompiledModel, values: ArrayLike<number>, u: number): number {
  const b = intervalBounds(node, model, values);
  return b ? roundTo(node, intervalQuantile(node, b, u), b) : NaN;
}

/**
 * Percentile (0-100, one decimal) of x given breakpoints[p] = value at percentile p.
 * A value shared by a run of breakpoints (a tie) maps to the middle of the run. NaN stays NaN.
 */
export function percentileValue(node: PercentileNode, x: number): number {
  if (Number.isNaN(x)) return NaN;
  const b = node.breakpoints;
  const last = b.length - 1;
  if (x < b[0]) return 0;
  if (x > b[last]) return 100;
  let i = 0; // first index with b[i] >= x
  while (b[i] < x) i++;
  let pct: number;
  if (b[i] === x) {
    let j = i;
    while (j < last && b[j + 1] === x) j++;
    pct = (i + j) / 2;
  } else {
    pct = i - 1 + (x - b[i - 1]) / (b[i] - b[i - 1]);
  }
  return Math.round((pct * 100) / last * 10) / 10;
}

/** Draws one person. `index` is the person's position in the sample (its RNG counter). */
export function samplePerson(model: CompiledModel, seed: number, index: number): PersonValues {
  const values = new Float64Array(model.vars.length);
  for (const node of model.bundle.nodes) {
    const stream = nodeStream(node.id);
    switch (node.type) {
      case "frame": {
        const row = pickIndex(model.frameCum, uniform(seed, index, stream, 0));
        for (const v of node.vars) values[model.varIndex.get(v.id)!] = node.rows[v.id][row];
        break;
      }
      case "lookup":
        values[model.varIndex.get(node.id)!] = node.map[values[model.varIndex.get(node.parent)!]];
        break;
      case "table": {
        const dist = lookupRow<Dist>(model.tables.get(node.id)!, values);
        values[model.varIndex.get(node.id)!] = dist.values[pickIndex(dist.cum, uniform(seed, index, stream, 0))];
        break;
      }
      case "logit": {
        const cum = cumulate(logitWeights(node, model, values));
        values[model.varIndex.get(node.id)!] = pickIndex(cum, uniform(seed, index, stream, 0));
        break;
      }
      case "interval":
        values[model.varIndex.get(node.id)!] = intervalValue(node, model, values, uniform(seed, index, stream, 0));
        break;
      case "percentile":
        values[model.varIndex.get(node.id)!] = percentileValue(node, values[model.varIndex.get(node.parent)!]);
        break;
      case "multi": {
        const probs = lookupRow<Float64Array>(model.tables.get(node.id)!, values);
        const within = node.subset_of ? values[model.varIndex.get(node.subset_of)!] : -1;
        let mask = 0;
        for (let k = 0; k < node.items.length; k++) {
          if (!(within & (1 << k))) continue;
          if (Math.floor(uniform(seed, index, stream, k) * PROB_SCALE) < probs[k]) mask |= 1 << k;
        }
        values[model.varIndex.get(node.id)!] = mask;
        break;
      }
    }
  }
  return values;
}

export function sampleMany(model: CompiledModel, seed: number, n: number, start = 0): PersonValues[] {
  const out: PersonValues[] = [];
  for (let i = start; i < start + n; i++) out.push(samplePerson(model, seed, i));
  return out;
}

/** Stable, human-readable form: value ids instead of indices; null = not applicable. */
export type PersonRecord = Record<string, string | number | string[] | null>;

export function toRecord(model: CompiledModel, values: PersonValues): PersonRecord {
  const rec: PersonRecord = {};
  model.vars.forEach((v, i) => {
    const x = values[i];
    if (v.multi) {
      rec[v.id] = v.values!.filter((_, k) => (x & (1 << k)) !== 0).map((d) => d.id);
    } else if (v.values && !v.numeric) {
      rec[v.id] = v.values[x].id;
    } else if (v.values && v.numeric) {
      rec[v.id] = Number(v.values[x].id);
    } else {
      rec[v.id] = Number.isNaN(x) ? null : x;
    }
  });
  return rec;
}
