/**
 * "How unusual?": how much a person's traits clash with each other.
 *
 * A person is drawn one trait at a time, each given the traits drawn before it. At every such
 * junction the score compares the probability of what the person got, given their other traits,
 * with its national share (the lift, or Das & Schneider's r-value):
 *
 *   r = P(value | parents) / P(value)        bits = min(cap, log2(1 / r))
 *   junction score = max(0, bits - hinge)    person's score S = sum over junctions
 *
 * A value that is rare everywhere (a doctorate, a small town) has r = 1 and scores nothing;
 * only values that the person's own traits make unlikely do (a Haredi in Tel Aviv). The
 * headline is S's percentile among all citizens, estimated from a fixed calibration sample.
 *
 * Explanations use the population of each combination of a node's parents (parent_weights):
 * the value's probability in any reference group defined by some of the person's traits is
 * exact, so the surprise (log2 P(value | all parents) - log2 P(value)) is split among the traits
 * by Shapley values, both those that make the value less usual and those that make it more so.
 * See docs/methodology/unusual.md.
 */

import { lookupRow, type CompiledModel, type Dist, type LogitNode, type MultiNode, type PercentileNode, type TableNode } from "./model.ts";
import { logitWeights, percentileValue, samplePerson, type PersonValues } from "./sample.ts";

export const UNUSUAL = {
  /** junctions up to 2^hinge times less likely than average are noise */
  hinge: 1,
  /** bits per junction at most (very small probabilities partly reflect smoothing) */
  cap: 6,
  calibrationPeople: 20_000,
  calibrationSeed: 20261014,
  /** a deviation is "major" from this many bits (16x less common), "notable" from the next */
  major: 4,
  notable: 2,
  /** traits named as the causes of one surprise (or as easing it), at most */
  causes: 3,
  /** a trait is named when its share of the surprise is at least this fraction of the strongest cause's */
  relative: 0.5,
} as const;

export type Tier = "typical" | "somewhat" | "unusual" | "very" | "exceptional";

/** Tiers by percentile (from = lowest percentile in the tier) and their population shares. */
export const TIERS: { id: Tier; from: number; share: number }[] = [
  { id: "typical", from: 0, share: 0.5 },
  { id: "somewhat", from: 50, share: 0.3 },
  { id: "unusual", from: 80, share: 0.15 },
  { id: "very", from: 95, share: 0.04 },
  { id: "exceptional", from: 99, share: 0.01 },
];

export function tierOf(percentile: number): Tier {
  let t: Tier = "typical";
  for (const x of TIERS) if (percentile >= x.from) t = x.id;
  return t;
}

/** One junction's surprise. */
export type Level = "major" | "notable" | "minor";

/** How significant a deviation of `bits` is (it already counts: bits > hinge). */
export function levelOf(bits: number): Level {
  return bits >= UNUSUAL.major ? "major" : bits >= UNUSUAL.notable ? "notable" : "minor";
}

export interface Surprise {
  /** the variable whose value is surprising */
  variable: string;
  /** value id (sets: the item) */
  value: string;
  /** sets: whether the item is included */
  present?: boolean;
  /** probability given the person's other traits, and nationally */
  pCond: number;
  pBase: number;
  bits: number;
  score: number;
  level: Level;
  /** visible variables that made the value unlikely, most decisive first */
  causes: string[];
  /** visible variables that made it more usual (though not enough to cancel the surprise) */
  eases: string[];
  /** the value's probability in widening reference groups: all citizens, then adding the
   * causes and the easing traits one at a time, then people like them (all their traits) */
  ladder?: LadderStep[];
  /** unordered tables: the most common value among people like them, if it is not theirs */
  common?: { value: string; share: number };
  /** ordered variables (income, children, ...): below or above what is usual for people like them */
  ordinal?: Ordinal;
}

export interface LadderStep {
  kind: "all" | "add" | "like";
  /** "add": the visible variable added to the reference group */
  variable?: string;
  p: number;
}

export interface Ordinal {
  direction: "lower" | "higher" | "better" | "worse";
  /** the usual (median) value for people like them */
  usual: string;
  /** share of people like them beyond this value, on the far side from usual: above it for
   * "lower", below it for "higher" */
  beyond: number;
}

export interface UnusualResult {
  score: number;
  /** 0-100: share of citizens with a lower score (ties count half) */
  percentile: number;
  tier: Tier;
  /** every deviation that counts toward the score, largest first */
  reasons: Surprise[];
}

/** An outcome of a junction: the value (or set item) the person has and its probability. */
interface Outcome {
  value: string;
  present?: boolean;
  item?: number;
  pCond: number;
  pBase: number;
}

interface Junction {
  variable: string;
  /** var indices this junction is conditioned on */
  parents: number[];
  /** the person's outcomes (one per value; sets: one per item that could be chosen) */
  outcomes(values: ArrayLike<number>): Outcome[];
  /** tables: the distribution over the values' indices among those the node applies to (and
   * that are on its scale), given the person's parents */
  distribution?(values: ArrayLike<number>): Float64Array | null;
  /** people per combination of the parents (flattened values in `parents` order, weights) */
  combos?: { v: Int32Array; w: Float64Array };
  /** cache: probability of an outcome in each combination */
  qCache?: Map<string, Float64Array>;
  /** probability of `o` given these (possibly altered) parent values; NaN if undefined */
  prob(values: ArrayLike<number>, o: Outcome): number;
}

interface Prepared {
  junctions: Junction[];
  /** national distribution per categorical variable, where known */
  marginals: (Float64Array | null)[];
  /** visible variable that each variable stands for in explanations */
  shownAs: string[];
  breakpoints?: number[];
}

const cache = new WeakMap<CompiledModel, Prepared>();

function prepared(model: CompiledModel): Prepared {
  let p = cache.get(model);
  if (!p) {
    p = prepare(model);
    cache.set(model, p);
  }
  return p;
}

function distProb(d: Dist, value: number): [number, number] {
  // [weight of value, total weight]
  const tot = d.cum[d.cum.length - 1];
  for (let j = 0; j < d.values.length; j++) {
    if (d.values[j] === value) return [d.cum[j] - (j ? d.cum[j - 1] : 0), tot];
  }
  return [0, tot];
}

function prepare(model: CompiledModel): Prepared {
  const nv = model.vars.length;
  const idx = (id: string) => model.varIndex.get(id)!;
  const marginals: (Float64Array | null)[] = new Array(nv).fill(null);
  const junctions: Junction[] = [];
  const frame = model.bundle.nodes[0];
  if (frame.type !== "frame") throw new Error("bundle has no frame node");

  // --- frame: national shares of its variables, and counts for group | locality and
  // age band | locality, group, sex
  const fv = Object.fromEntries(frame.vars.map((v) => [v.id, v.values.length])) as Record<string, number>;
  for (const v of frame.vars) marginals[idx(v.id)] = new Float64Array(v.values.length);
  const G = fv.group, S = fv.sex, A = fv.age_band;
  const wl = new Map<number, number>();
  const wlg = new Map<number, number>();
  const wlgs = new Map<number, number>();
  const wlgsa = new Map<number, number>();
  const add = (m: Map<number, number>, k: number, w: number) => m.set(k, (m.get(k) ?? 0) + w);
  let total = 0;
  frame.weights.forEach((w, r) => {
    const l = frame.rows.locality[r], g = frame.rows.group[r], s = frame.rows.sex[r], a = frame.rows.age_band[r];
    add(wl, l, w);
    add(wlg, l * G + g, w);
    add(wlgs, (l * G + g) * S + s, w);
    add(wlgsa, ((l * G + g) * S + s) * A + a, w);
    for (const v of frame.vars) marginals[idx(v.id)]![frame.rows[v.id][r]] += w;
    total += w;
  });
  for (const v of frame.vars) marginals[idx(v.id)]!.forEach((x, k, arr) => (arr[k] = x / total));

  const [iL, iG, iS, iA] = ["locality", "group", "sex", "age_band"].map(idx);
  const frameJunction = (
    variable: string,
    parents: number[],
    num: (v: ArrayLike<number>) => number,
    den: (v: ArrayLike<number>) => number,
    combos: { v: Int32Array; w: Float64Array },
  ): Junction => {
    const vi = idx(variable);
    const m = marginals[vi]!;
    const values = frame.vars.find((v) => v.id === variable)!.values;
    return {
      variable,
      parents,
      combos,
      outcomes: (v) => [{ value: values[v[vi]].id, pCond: num(v) / den(v), pBase: m[v[vi]] }],
      prob: (v) => {
        const d = den(v);
        return d > 0 ? num(v) / d : NaN;
      },
    };
  };
  const combosOf = (m: Map<number, number>, decode: (k: number) => number[]) => {
    const v: number[] = [];
    const w: number[] = [];
    for (const [k, x] of m) {
      v.push(...decode(k));
      w.push(x);
    }
    return { v: Int32Array.from(v), w: Float64Array.from(w) };
  };
  junctions.push(
    frameJunction("group", [iL], (v) => wlg.get(v[iL] * G + v[iG]) ?? 0, (v) => wl.get(v[iL]) ?? 0, combosOf(wl, (k) => [k])),
    frameJunction(
      "age_band",
      [iL, iG, iS],
      (v) => wlgsa.get(((v[iL] * G + v[iG]) * S + v[iS]) * A + v[iA]) ?? 0,
      (v) => wlgs.get((v[iL] * G + v[iG]) * S + v[iS]) ?? 0,
      combosOf(wlgs, (k) => [Math.floor(k / (G * S)), Math.floor(k / S) % G, k % S]),
    ),
  );

  // --- the other nodes, in model order
  for (const node of model.bundle.nodes) {
    if (node.type === "frame") continue;
    const vi = model.varIndex.get(node.id)!;
    if (node.type === "lookup") {
      const pm = marginals[idx(node.parent)];
      if (pm) {
        const m = new Float64Array(node.values.length);
        node.map.forEach((v, k) => (m[v] += pm[k]));
        marginals[vi] = m;
      }
      continue;
    }
    if (node.type === "table") {
      marginals[vi] = node.marginal ? Float64Array.from(node.marginal) : frameMarginal(model, node);
      if (!node.hidden && !node.numeric) junctions.push(tableJunction(model, node, marginals[vi]!));
    } else if (node.type === "logit") {
      marginals[vi] = node.marginal ? Float64Array.from(node.marginal) : null;
      if (!node.hidden && marginals[vi]) junctions.push(logitJunction(model, node, marginals[vi]!));
    } else if (node.type === "multi") {
      if (!node.hidden && node.marginal) junctions.push(multiJunction(model, node, Float64Array.from(node.marginal)));
    }
  }

  // --- what each variable stands for in explanations
  const shownAs: string[] = model.vars.map((v) => v.id);
  const resolve = (k: number): string => {
    const info = model.vars[k];
    if (!info.hidden) return info.id;
    const n = info.node;
    if (n.type !== "frame" && n.shown_as) return resolve(idx(n.shown_as));
    if (n.type === "lookup") return resolve(idx(n.parent));
    return info.id;
  };
  for (let k = 0; k < nv; k++) shownAs[k] = resolve(k);

  return { junctions, marginals, shownAs };
}

/** National distribution of a table whose parents are all frame variables (e.g. single-year age). */
function frameMarginal(model: CompiledModel, node: TableNode): Float64Array | null {
  const frame = model.bundle.nodes[0];
  if (frame.type !== "frame") return null;
  const frameVars = new Set(frame.vars.map((v) => v.id));
  if (!node.parents.every((p) => frameVars.has(p))) return null;
  const t = model.tables.get(node.id)!;
  const out = new Float64Array(node.values.length);
  const values = new Float64Array(model.vars.length);
  let total = 0;
  frame.weights.forEach((w, r) => {
    for (const v of frame.vars) values[model.varIndex.get(v.id)!] = frame.rows[v.id][r];
    const d = lookupRow<Dist>(t, values);
    const tot = d.cum[d.cum.length - 1];
    for (let j = 0; j < d.values.length; j++) out[d.values[j]] += (w * (d.cum[j] - (j ? d.cum[j - 1] : 0))) / tot;
    total += w;
  });
  return out.map((x) => x / total);
}

/** Indices of the node's "does not apply" values, and the national share of the rest. */
function applicable(values: { id: string }[], na: string[] | undefined, m: Float64Array): [Set<number>, number] {
  const set = new Set<number>();
  for (const id of na ?? []) {
    const k = values.findIndex((v) => v.id === id);
    if (k >= 0) set.add(k);
  }
  let rest = 1;
  for (const k of set) rest -= m[k];
  return [set, rest];
}

function weightsOf(pw: { v: number[]; w: number[] } | undefined): { v: Int32Array; w: Float64Array } | undefined {
  return pw ? { v: Int32Array.from(pw.v), w: Float64Array.from(pw.w) } : undefined;
}

function tableJunction(model: CompiledModel, node: TableNode, m: Float64Array): Junction {
  const vi = model.varIndex.get(node.id)!;
  const t = model.tables.get(node.id)!;
  const [na, rest] = applicable(node.values, node.not_applicable, m);
  const off = new Set(node.values.flatMap((v, k) => (node.off_scale?.includes(v.id) ? [k] : [])));
  const prob = (v: ArrayLike<number>, x: number): number => {
    let d: Dist;
    try {
      d = lookupRow<Dist>(t, v);
    } catch {
      return NaN;
    }
    const [w, tot] = distProb(d, x);
    let naW = 0;
    for (const k of na) naW += distProb(d, k)[0];
    return tot - naW > 0 ? w / (tot - naW) : NaN;
  };
  return {
    variable: node.id,
    parents: t.parentIdx,
    combos: weightsOf(node.parent_weights),
    outcomes: (v) => (na.has(v[vi]) ? [] : [{ value: node.values[v[vi]].id, pCond: prob(v, v[vi]), pBase: m[v[vi]] / rest }]),
    prob: (v, o) => prob(v, node.values.findIndex((x) => x.id === o.value)),
    distribution: (v) => {
      const d = lookupRow<Dist>(t, v);
      const w = new Float64Array(node.values.length);
      for (let j = 0; j < d.values.length; j++) {
        const x = d.values[j];
        if (!na.has(x) && !off.has(x)) w[x] = d.cum[j] - (j ? d.cum[j - 1] : 0);
      }
      const tot = w.reduce((a, b) => a + b, 0);
      return tot > 0 ? w.map((x) => x / tot) : null;
    },
  };
}

function logitJunction(model: CompiledModel, node: LogitNode, m: Float64Array): Junction {
  const vi = model.varIndex.get(node.id)!;
  const [na, rest] = applicable(node.values, node.not_applicable, m);
  const prob = (v: ArrayLike<number>, x: number): number => {
    const w = logitWeights(node, model, v);
    let tot = 0;
    for (let j = 0; j < w.length; j++) if (!na.has(j)) tot += w[j];
    return tot > 0 ? w[x] / tot : NaN;
  };
  return {
    variable: node.id,
    parents: node.parents.map((p) => model.varIndex.get(p)!),
    outcomes: (v) => (na.has(v[vi]) ? [] : [{ value: node.values[v[vi]].id, pCond: prob(v, v[vi]), pBase: m[v[vi]] / rest }]),
    prob: (v, o) => prob(v, node.values.findIndex((x) => x.id === o.value)),
  };
}

function multiJunction(model: CompiledModel, node: MultiNode, m: Float64Array): Junction {
  const vi = model.varIndex.get(node.id)!;
  const t = model.tables.get(node.id)!;
  const within = node.subset_of ? model.varIndex.get(node.subset_of)! : -1;
  const itemProb = (v: ArrayLike<number>, k: number): number => {
    try {
      return lookupRow<Float64Array>(t, v)[k] / 1e9;
    } catch {
      return NaN;
    }
  };
  return {
    variable: node.id,
    parents: t.parentIdx,
    combos: weightsOf(node.parent_weights),
    outcomes: (v) => {
      const out: Outcome[] = [];
      const mask = v[vi];
      const allowed = within >= 0 ? v[within] : -1;
      node.items.forEach((item, k) => {
        if (!(allowed & (1 << k))) return;
        const present = (mask & (1 << k)) !== 0;
        const q = itemProb(v, k);
        out.push({ value: item.id, present, item: k, pCond: present ? q : 1 - q, pBase: present ? m[k] : 1 - m[k] });
      });
      return out;
    },
    prob: (v, o) => {
      const q = itemProb(v, o.item!);
      return o.present ? q : 1 - q;
    },
  };
}

function surprise(o: Outcome): { bits: number; score: number } {
  if (!(o.pCond > 0) || !(o.pBase > 0)) return { bits: 0, score: 0 };
  const bits = Math.min(UNUSUAL.cap, Math.log2(o.pBase / o.pCond));
  return { bits, score: Math.max(0, bits - UNUSUAL.hinge) };
}

/** Variables shown but never scored: a first name is flavour, not a trait. */
export const UNSCORED = new Set(["first_name"]);

/** Each junction's largest surprise (sets: their most surprising item), in model order. */
function junctionSurprises(prep: Prepared, values: ArrayLike<number>, only?: string): { j: Junction; o: Outcome; bits: number; score: number }[] {
  const out = [];
  for (const j of prep.junctions) {
    if (only ? j.variable !== only : UNSCORED.has(j.variable)) continue;
    let best: { j: Junction; o: Outcome; bits: number; score: number } | null = null;
    for (const o of j.outcomes(values)) {
      const s = surprise(o);
      if (!best || s.bits > best.bits) best = { j, o, ...s };
    }
    if (best) out.push(best);
  }
  return out;
}

/** How common the person's first name is among people like them (not part of the score). */
export function nameSurprise(model: CompiledModel, values: ArrayLike<number>): { value: string; pCond: number; pBase: number } | null {
  const x = junctionSurprises(prepared(model), values, "first_name")[0];
  return x ? { value: x.o.value, pCond: x.o.pCond, pBase: x.o.pBase } : null;
}

/** The person's raw score S (sum of junction scores). */
export function unusualScore(model: CompiledModel, values: ArrayLike<number>): number {
  let s = 0;
  for (const x of junctionSurprises(prepared(model), values)) s += x.score;
  return s;
}

/**
 * Fallback for junctions without parent weights (the preferred-source logit). The traits that
 * made an outcome unlikely: for each parent, the outcome's probability with that parent replaced
 * by its national distribution. The parents whose removal makes the outcome at
 * least twice as likely are named (or the single strongest one), most decisive first.
 */
function causesOf(model: CompiledModel, prep: Prepared, j: Junction, o: Outcome, values: ArrayLike<number>): string[] {
  const scratch = Float64Array.from(values);
  const gains: { parent: number; gain: number }[] = [];
  for (const p of j.parents) {
    const m = prep.marginals[p];
    if (!m) continue;
    let num = 0;
    let den = 0;
    for (let v = 0; v < m.length; v++) {
      if (!(m[v] > 0)) continue;
      scratch[p] = v;
      const q = j.prob(scratch, o);
      if (Number.isFinite(q)) {
        num += m[v] * q;
        den += m[v];
      }
    }
    scratch[p] = values[p];
    if (den > 0) gains.push({ parent: p, gain: num / den / o.pCond });
  }
  gains.sort((a, b) => b.gain - a.gain);
  const picked = gains.filter((g) => g.gain >= 2);
  const chosen = picked.length ? picked : gains.slice(0, 1).filter((g) => g.gain > 1);
  const out: string[] = [];
  for (const g of chosen) {
    const id = prep.shownAs[g.parent];
    if (!out.includes(id)) out.push(id);
    if (out.length >= UNUSUAL.causes) break;
  }
  return out;
}

interface Explanation {
  causes: string[];
  eases: string[];
  ladder?: LadderStep[];
}

/**
 * Splits a surprise among the person's traits. For every set S of the junction's parents (grouped
 * by the visible variable they stand for), P(value | S) is the value's probability among people
 * who share the person's values of S, from the population of each parent combination. A trait's
 * Shapley value is its average effect on log2 P(value | S) when added to the others; they sum to
 * the whole surprise. Negative: the trait makes the value less usual (a cause); positive: more
 * usual (it eases the surprise).
 */
function explain(model: CompiledModel, prep: Prepared, j: Junction, o: Outcome, values: ArrayLike<number>): Explanation | null {
  const c = j.combos;
  const k = j.parents.length;
  if (!c || k === 0 || k > 12) return null;
  const n = c.w.length;
  // probability of the outcome in each combination (cached per outcome)
  const key = `${o.value}|${o.present ?? ""}`;
  j.qCache ??= new Map();
  let q = j.qCache.get(key);
  if (!q) {
    q = new Float64Array(n);
    const scratch = Float64Array.from(values);
    for (let r = 0; r < n; r++) {
      for (let i = 0; i < k; i++) scratch[j.parents[i]] = c.v[r * k + i];
      q[r] = j.prob(scratch, o);
    }
    j.qCache.set(key, q);
  }
  // sums by the set of parents on which a combination agrees with the person, then over supersets
  const size = 1 << k;
  const num = new Float64Array(size);
  const den = new Float64Array(size);
  for (let r = 0; r < n; r++) {
    if (!Number.isFinite(q[r])) continue;
    let mask = 0;
    for (let i = 0; i < k; i++) if (c.v[r * k + i] === values[j.parents[i]]) mask |= 1 << i;
    num[mask] += c.w[r] * q[r];
    den[mask] += c.w[r];
  }
  for (let i = 0; i < k; i++) {
    for (let mask = 0; mask < size; mask++) {
      if (!(mask & (1 << i))) {
        num[mask] += num[mask | (1 << i)];
        den[mask] += den[mask | (1 << i)];
      }
    }
  }
  if (!(den[size - 1] > 0) || !(num[size - 1] > 0)) return null;
  const p = (mask: number) => (den[mask] > 0 ? num[mask] / den[mask] : NaN);
  // players: the visible variables the parents stand for
  const players: { id: string; mask: number }[] = [];
  j.parents.forEach((pi, i) => {
    const id = prep.shownAs[pi];
    const pl = players.find((x) => x.id === id);
    if (pl) pl.mask |= 1 << i;
    else players.push({ id, mask: 1 << i });
  });
  const P = players.length;
  const maskOf = (sub: number) => players.reduce((m, pl, i) => (sub & (1 << i) ? m | pl.mask : m), 0);
  const v = new Float64Array(1 << P);
  for (let sub = 0; sub < 1 << P; sub++) v[sub] = Math.log2(p(maskOf(sub)));
  if (!v.every(Number.isFinite)) return null;
  const fact = [1];
  for (let i = 1; i <= P; i++) fact[i] = fact[i - 1] * i;
  const phi = players.map((_, i) => {
    let s = 0;
    for (let sub = 0; sub < 1 << P; sub++) {
      if (sub & (1 << i)) continue;
      let size_ = 0;
      for (let b = sub; b; b &= b - 1) size_++;
      s += ((fact[size_] * fact[P - size_ - 1]) / fact[P]) * (v[sub | (1 << i)] - v[sub]);
    }
    return s;
  });
  const order = players.map((pl, i) => ({ id: pl.id, i, phi: phi[i] }));
  // name the strongest cause, and any other trait pulling the same way at least half as hard
  const neg = order.filter((x) => x.phi < 0).sort((a, b) => a.phi - b.phi);
  const top = neg.length ? -neg[0].phi : 0;
  const causes = neg.filter((x, i) => i === 0 || -x.phi >= UNUSUAL.relative * top).slice(0, UNUSUAL.causes);
  const eases = order
    .filter((x) => x.phi > 0 && x.phi >= UNUSUAL.relative * top)
    .sort((a, b) => b.phi - a.phi)
    .slice(0, UNUSUAL.causes);
  const ladder: LadderStep[] = [{ kind: "all", p: p(0) }];
  let sub = 0;
  for (const x of [...causes, ...eases]) {
    sub |= 1 << x.i;
    ladder.push({ kind: "add", variable: x.id, p: p(maskOf(sub)) });
  }
  if (sub !== (1 << P) - 1) ladder.push({ kind: "like", p: p(size - 1) });
  else ladder[ladder.length - 1] = { ...ladder[ladder.length - 1], kind: "like" };
  return { causes: causes.map((x) => x.id), eases: eases.map((x) => x.id), ladder };
}

/** Unordered tables: the most common value among people like the person, if it is not theirs. */
function commonOf(model: CompiledModel, j: Junction, o: Outcome, values: ArrayLike<number>): { value: string; share: number } | undefined {
  const node = model.bundle.nodes.find((n) => n.id === j.variable);
  if (!node || node.type !== "table" || node.ordered) return undefined;
  const dist = j.distribution?.(values);
  if (!dist) return undefined;
  let best = 0;
  for (let i = 1; i < dist.length; i++) if (dist[i] > dist[best]) best = i;
  return node.values[best].id === o.value ? undefined : { value: node.values[best].id, share: dist[best] };
}

/** Whether an ordered value is below or above what is usual for people like the person. */
function ordinalOf(model: CompiledModel, j: Junction, o: Outcome, values: ArrayLike<number>): Ordinal | undefined {
  const node = model.bundle.nodes.find((n) => n.id === j.variable);
  if (!node || node.type !== "table" || !node.ordered || node.off_scale?.includes(o.value)) return undefined;
  const dist = j.distribution?.(values);
  if (!dist) return undefined;
  const k = node.values.findIndex((v) => v.id === o.value);
  let acc = 0;
  let median = 0;
  for (let i = 0; i < dist.length; i++) {
    acc += dist[i];
    if (acc >= 0.5) {
      median = i;
      break;
    }
  }
  if (k === median) return undefined;
  let beyond = 0;
  dist.forEach((w, i) => {
    if (k < median ? i > k : i < k) beyond += w;
  });
  const direction = node.quality_scale ? (k < median ? "better" : "worse") : k < median ? "lower" : "higher";
  return { direction, usual: node.values[median].id, beyond };
}

/** The person's surprises of more than `minBits`, largest first, with their causes. */
export function surprises(model: CompiledModel, values: ArrayLike<number>, limit = Infinity, minBits: number = UNUSUAL.hinge): Surprise[] {
  const prep = prepared(model);
  return junctionSurprises(prep, values)
    .filter((x) => x.score > 0 && x.bits >= minBits)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(({ j, o, bits, score }) => {
      const ex = explain(model, prep, j, o, values);
      const ordinal = ordinalOf(model, j, o, values);
      const common = commonOf(model, j, o, values);
      return {
        variable: j.variable,
        value: o.value,
        ...(o.present === undefined ? {} : { present: o.present }),
        pCond: o.pCond,
        pBase: o.pBase,
        bits,
        score,
        level: levelOf(bits),
        causes: ex ? ex.causes : causesOf(model, prep, j, o, values),
        eases: ex ? ex.eases : [],
        ...(ex?.ladder ? { ladder: ex.ladder } : {}),
        ...(common ? { common } : {}),
        ...(ordinal ? { ordinal } : {}),
      };
    });
}

/**
 * Percentiles 0..100 of S among all citizens, from a fixed sample (the same in the CLI and
 * the website). Computed once per model.
 */
export function calibration(model: CompiledModel): number[] {
  const prep = prepared(model);
  if (!prep.breakpoints) {
    const n = UNUSUAL.calibrationPeople;
    const scores = new Float64Array(n);
    for (let i = 0; i < n; i++) scores[i] = unusualScore(model, samplePerson(model, UNUSUAL.calibrationSeed, i));
    scores.sort();
    prep.breakpoints = Array.from({ length: 101 }, (_, p) => scores[Math.min(n - 1, Math.round((p / 100) * (n - 1)))]);
  }
  return prep.breakpoints;
}

export function unusual(model: CompiledModel, values: PersonValues): UnusualResult {
  const score = unusualScore(model, values);
  const percentile = percentileValue({ breakpoints: calibration(model) } as PercentileNode, score);
  return { score, percentile, tier: tierOf(percentile), reasons: surprises(model, values) };
}
