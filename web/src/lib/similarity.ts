/**
 * How closely an assembly member matches the conditions chosen on the "How likely?" page.
 *
 * Each conditioned attribute scores between 0 and 1, and the similarity is their mean (every
 * attribute counts the same, however many values it names):
 * - a categorical attribute scores 1 if the member's value is allowed, else 0; but on an ordered
 *   scale (education, children, income band, health, ...) a value a step or two away from an
 *   allowed one keeps partial credit;
 * - a numeric range scores 1 inside it and falls off linearly outside, reaching 0 at a set
 *   distance (10 years of age, 20 percentile points, half the bound for amounts);
 * - a multi-valued attribute (social networks, ...) scores the share of required items present.
 */

import type { Evidence, PresentedPerson } from "@popsim/sampler";
import type { ModelInfo } from "./worker-client.ts";

type Var = ModelInfo["vars"][number];

/** distance outside a numeric range at which the score reaches 0 */
function tolerance(v: Var, edge: number): number {
  if (v.id === "age") return 10;
  if (v.id.endsWith("_percentile")) return 20;
  if (v.id === "literacy_score") return 50;
  return Math.max(Math.abs(edge) / 2, 1);
}

export function attributeScore(v: Var, con: Evidence[string], x: PresentedPerson["values"][string]): number {
  if ("ids" in con) {
    if (v.multi) {
      if (!con.ids.length) return 1;
      const have = Array.isArray(x) ? x : [];
      return con.ids.filter((i) => have.includes(i)).length / con.ids.length;
    }
    const value = String(x);
    if (con.ids.includes(value)) return 1;
    if (!v.ordered || !v.values) return 0;
    // position on the scale, skipping off-scale values ("not employed", "not applicable")
    const scale = v.values.map((y) => y.id).filter((id) => !v.offScale?.includes(id));
    const k = scale.indexOf(value);
    const allowed = con.ids.map((id) => scale.indexOf(id)).filter((i) => i >= 0);
    if (k < 0 || !allowed.length) return 0;
    const d = Math.min(...allowed.map((i) => Math.abs(i - k)));
    return Math.max(0, 1 - d / Math.max(2, (scale.length - 1) / 2));
  }
  if (x === null || x === undefined) return 0;
  const n = Number(x);
  if (con.min !== undefined && n < con.min) return Math.max(0, 1 - (con.min - n) / tolerance(v, con.min));
  if (con.max !== undefined && n > con.max) return Math.max(0, 1 - (n - con.max) / tolerance(v, con.max));
  return 1;
}

export interface Similar {
  person: PresentedPerson;
  /** 0-1 */
  score: number;
  /** conditioned attributes the member does not fully meet, worst first */
  misses: string[];
}

export function similarity(people: PresentedPerson[], ev: Evidence, vars: Map<string, Var>): Similar[] {
  const ids = Object.keys(ev);
  if (!ids.length) return [];
  return people.map((person) => {
    const parts = ids.map((id) => ({ id, s: attributeScore(vars.get(id)!, ev[id], person.values[id]) }));
    return {
      person,
      score: parts.reduce((a, p) => a + p.s, 0) / parts.length,
      misses: parts
        .filter((p) => p.s < 1)
        .sort((a, b) => a.s - b.s)
        .map((p) => p.id),
    };
  });
}
