/**
 * The model bundle format ("popsim-model/1") and its compiled, sampling-ready form.
 *
 * The bundle is produced by the Python pipeline (pipeline/popsim/export/bundle.py).
 * Nodes are listed in sampling (topological) order. All categorical distributions are
 * stored as non-negative *integer* weights so cumulative sums are exact in every language.
 */

import { cumulate } from "./rng.ts";

export interface Label {
  en: string;
  he: string; // masculine / neutral Hebrew form
  he_f?: string; // feminine Hebrew form, when it differs
  en_f?: string; // feminine English form, when it differs (e.g. Michel / Michelle)
}

export interface ValueDef {
  id: string;
  label: Label;
  attrs?: Record<string, string | number | boolean | null>;
}

interface NodeCommon {
  id: string;
  label: Label;
  doc?: string;
  sources?: string[];
  /** Hidden nodes are technical helpers (e.g. coarse groupings) not shown to users. */
  hidden?: boolean;
}

export interface FrameVar {
  id: string;
  label: Label;
  values: ValueDef[];
  hidden?: boolean;
}

/** Root joint distribution over several variables, given as weighted rows. */
export interface FrameNode extends NodeCommon {
  type: "frame";
  vars: FrameVar[];
  rows: Record<string, number[]>; // var id -> value index per row
  weights: number[]; // integer people counts per row
}

/** Deterministic function of one parent (e.g. locality -> district). */
export interface LookupNode extends NodeCommon {
  type: "lookup";
  parent: string;
  values: ValueDef[];
  map: number[]; // value index for each parent value
}

/** Conditional probability table. Keys are parent value indices joined by "|" ("*" = any). */
export interface TableNode extends NodeCommon {
  type: "table";
  parents: string[];
  values: ValueDef[];
  numeric?: boolean; // value ids are numbers (e.g. single-year age)
  rows: Record<string, [number[], number[]]>; // key -> [value indices, integer weights]
  /** Parents to replace by "*" (cumulatively, in this order) when an exact key is missing. */
  backoff?: string[];
}

/** Multinomial logit with main effects: score_k = intercept_k + sum_p coef[p][value_p][k]. */
export interface LogitNode extends NodeCommon {
  type: "logit";
  parents: string[];
  values: ValueDef[];
  intercept: number[];
  coef: Record<string, number[][]>;
}

/** A number drawn inside the interval chosen by a categorical parent (e.g. income within a bracket). */
export interface IntervalNode extends NodeCommon {
  type: "interval";
  parent: string;
  /**
   * Per parent value: [lo, hi]; hi = null is an open-ended top bracket (Pareto tail above lo);
   * a null entry means the number does not apply (NaN), e.g. earnings of people not employed.
   */
  intervals: ([number, number | null] | null)[];
  scale: "linear" | "log";
  round?: number; // round to a multiple of this
  tail_alpha?: number; // Pareto exponent of the open-ended bracket
  tail_u_max?: number; // cap on the uniform draw in the tail (keeps amounts finite)
  /** Upper bound set by another categorical variable (e.g. earnings <= top of the household bracket). */
  cap?: { var: string; upper: (number | null)[] };
  /** Lower bound set by another numeric variable (e.g. household income >= own earnings). */
  floor?: string;
}

/** Maps a numeric parent onto 0-100 using breakpoints (value at percentile 0..100). */
export interface PercentileNode extends NodeCommon {
  type: "percentile";
  parent: string;
  breakpoints: number[];
}

/** Set-valued node: each item is included independently with a probability (x 1e9). */
export interface MultiNode extends NodeCommon {
  type: "multi";
  parents: string[];
  items: ValueDef[];
  rows: Record<string, number[]>;
  backoff?: string[];
}

export type ModelNode =
  | FrameNode
  | LookupNode
  | TableNode
  | LogitNode
  | IntervalNode
  | PercentileNode
  | MultiNode;

export interface Bundle {
  format: "popsim-model/1";
  version: string;
  reference_date: string;
  population_label: Label;
  population_total: number;
  nodes: ModelNode[];
  sources: { id: string; title: Label; publisher: string; url?: string; tier: string }[];
}

export const PROB_SCALE = 1e9;

// ---------------------------------------------------------------------------
// Compiled form

export interface Dist {
  values: Int32Array;
  cum: Float64Array;
}

export interface CompiledTable {
  node: TableNode | MultiNode;
  parentIdx: number[]; // positions of parents in the variable index
  rows: Map<string, Dist | Float64Array>;
}

export interface VarInfo {
  id: string;
  label: Label;
  values?: ValueDef[]; // categorical domain (undefined for numeric outputs)
  numeric: boolean;
  multi: boolean;
  hidden: boolean;
  node: ModelNode; // the node that produces this variable
}

export interface CompiledModel {
  bundle: Bundle;
  vars: VarInfo[];
  varIndex: Map<string, number>;
  frameCum: Float64Array;
  tables: Map<string, CompiledTable>;
}

export function compile(bundle: Bundle): CompiledModel {
  if (bundle.format !== "popsim-model/1") throw new Error(`unsupported bundle format ${bundle.format}`);
  const vars: VarInfo[] = [];
  const varIndex = new Map<string, number>();
  const add = (v: VarInfo) => {
    if (varIndex.has(v.id)) throw new Error(`duplicate variable ${v.id}`);
    varIndex.set(v.id, vars.length);
    vars.push(v);
  };
  let frameCum: Float64Array | null = null;
  const tables = new Map<string, CompiledTable>();
  const need = (id: string, by: string) => {
    if (!varIndex.has(id)) throw new Error(`${by}: parent ${id} is not defined before it`);
    return varIndex.get(id)!;
  };

  for (const node of bundle.nodes) {
    switch (node.type) {
      case "frame": {
        if (frameCum) throw new Error("only one frame node is supported");
        for (const v of node.vars) {
          add({ id: v.id, label: v.label, values: v.values, numeric: false, multi: false, hidden: !!v.hidden, node });
        }
        frameCum = cumulate(node.weights);
        break;
      }
      case "lookup":
        need(node.parent, node.id);
        add({ id: node.id, label: node.label, values: node.values, numeric: false, multi: false, hidden: !!node.hidden, node });
        break;
      case "table": {
        const parentIdx = node.parents.map((p) => need(p, node.id));
        const rows = new Map<string, Dist>();
        for (const [key, [vals, weights]] of Object.entries(node.rows)) {
          rows.set(key, { values: Int32Array.from(vals), cum: cumulate(weights) });
        }
        tables.set(node.id, { node, parentIdx, rows });
        add({ id: node.id, label: node.label, values: node.values, numeric: !!node.numeric, multi: false, hidden: !!node.hidden, node });
        break;
      }
      case "multi": {
        const parentIdx = node.parents.map((p) => need(p, node.id));
        const rows = new Map<string, Float64Array>();
        for (const [key, probs] of Object.entries(node.rows)) rows.set(key, Float64Array.from(probs));
        tables.set(node.id, { node, parentIdx, rows });
        add({ id: node.id, label: node.label, values: node.items, numeric: false, multi: true, hidden: !!node.hidden, node });
        break;
      }
      case "logit":
        for (const p of node.parents) need(p, node.id);
        add({ id: node.id, label: node.label, values: node.values, numeric: false, multi: false, hidden: !!node.hidden, node });
        break;
      case "interval":
        need(node.parent, node.id);
        if (node.cap) need(node.cap.var, node.id);
        if (node.floor) need(node.floor, node.id);
        add({ id: node.id, label: node.label, numeric: true, multi: false, hidden: !!node.hidden, node });
        break;
      case "percentile":
        need(node.parent, node.id);
        add({ id: node.id, label: node.label, numeric: true, multi: false, hidden: !!node.hidden, node });
        break;
      default:
        throw new Error(`unknown node type ${(node as ModelNode).type}`);
    }
  }
  if (!frameCum) throw new Error("bundle has no frame node");
  return { bundle, vars, varIndex, frameCum, tables };
}

/** Returns the row for a table/multi node given the person's values, applying back-off. */
export function lookupRow<T>(t: CompiledTable, values: ArrayLike<number>): T {
  const parts = t.parentIdx.map((i) => String(values[i]));
  const exact = parts.join("|");
  let row = t.rows.get(exact);
  if (row) return row as T;
  const backoff = t.node.backoff ?? [];
  for (const p of backoff) {
    const pos = t.node.parents.indexOf(p);
    parts[pos] = "*";
    row = t.rows.get(parts.join("|"));
    if (row) return row as T;
  }
  throw new Error(`${t.node.id}: no distribution for parents ${t.node.parents.join(",")} = ${exact}`);
}
