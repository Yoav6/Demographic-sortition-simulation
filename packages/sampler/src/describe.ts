/**
 * Turns a sampled person into prose using ICU MessageFormat templates (templates/he.json,
 * templates/en.json).
 *
 * Template context, for every variable `x` of the model:
 *   {x}          the value's label, in the person's grammatical gender for Hebrew
 *   {x__attr}    a label-valued attribute of the value (e.g. occupation__phrase)
 *   {x__id}      the raw value id (useful in `select`)
 *   numeric variables are passed as numbers ({age}, {income, number})
 *   set-valued variables: {x} the items joined into a list, {x__count}, {x__attr} the list
 *   of the items' attribute labels
 *   lists declared in the templates file ({name}, {name__n}, ...; see ListSpec)
 * Sentences may carry `when: {var: [allowed ids]}` and are skipped otherwise.
 */

import { IntlMessageFormat } from "intl-messageformat";
import type { CompiledModel, Label } from "./model.ts";
import type { PersonValues } from "./sample.ts";

export type Lang = "he" | "en";

export interface Sentence {
  id: string;
  text: string;
  when?: Record<string, string[]>;
  unless?: Record<string, string[]>;
}

/**
 * A sentence fragment that groups several variables by their value, e.g. media by how often the
 * person uses them: "often from TV and news sites, sometimes from social media". `items` maps
 * each variable to its phrase (an ICU message, formatted with the person's context); `groups`
 * maps a value id to the fragment for the variables with that value ({list}), in output order.
 * {name} joins the fragments, {name__n} counts them. The variables with the `separate` value
 * are listed apart as {name__<value>} ("or" list) with the count {name__<value>_n}.
 */
export interface ListSpec {
  items: Record<string, string>;
  groups: Record<string, string>;
  separate?: string;
}

export interface Templates {
  lang: Lang;
  sentences: Sentence[];
  lists?: Record<string, ListSpec>;
}

export function labelFor(label: Label, lang: Lang, female: boolean): string {
  if (lang === "en") return female && label.en_f ? label.en_f : label.en;
  return female && label.he_f ? label.he_f : label.he;
}

function isLabel(x: unknown): x is Label {
  return typeof x === "object" && x !== null && "en" in x && "he" in x;
}

export function buildContext(model: CompiledModel, values: PersonValues, lang: Lang): Record<string, unknown> {
  const sexIdx = model.varIndex.get("sex");
  const female = sexIdx !== undefined && model.vars[sexIdx].values![values[sexIdx]].id === "female";
  const ctx: Record<string, unknown> = {};
  model.vars.forEach((info, k) => {
    const x = values[k];
    if (info.multi) {
      const chosen = info.values!.filter((_, j) => (x & (1 << j)) !== 0);
      const list = new Intl.ListFormat(lang, { style: "long", type: "conjunction" });
      ctx[info.id] = list.format(chosen.map((v) => labelFor(v.label, lang, female)));
      ctx[`${info.id}__count`] = chosen.length;
      ctx[`${info.id}__id`] = chosen.map((v) => v.id).join(",") || "none";
      const attrs = new Set(info.values!.flatMap((v) => Object.keys(v.attrs ?? {})));
      for (const attr of attrs) {
        ctx[`${info.id}__${attr}`] = list.format(
          chosen.map((v) => {
            const a = v.attrs?.[attr];
            return isLabel(a) ? labelFor(a, lang, female) : labelFor(v.label, lang, female);
          }),
        );
      }
    } else if (info.values && !info.numeric) {
      const v = info.values[x];
      ctx[info.id] = labelFor(v.label, lang, female);
      ctx[`${info.id}__id`] = v.id;
      for (const [attr, val] of Object.entries(v.attrs ?? {})) {
        ctx[`${info.id}__${attr}`] = isLabel(val) ? labelFor(val, lang, female) : val;
      }
    } else if (info.values && info.numeric) {
      ctx[info.id] = Number(info.values[x].id);
      ctx[`${info.id}__an`] = englishArticle(Number(info.values[x].id));
    } else {
      ctx[info.id] = x;
      ctx[`${info.id}__an`] = englishArticle(x);
    }
  });
  ctx.gender = female ? "female" : "male";
  return ctx;
}

/** "an" before numbers read with a leading vowel sound (8, 11, 18, 80-89, 800...), else "a". */
export function englishArticle(n: number): string {
  const k = Math.floor(Math.abs(n));
  const s = String(k);
  return s.startsWith("8") || k === 11 || k === 18 || (k >= 11000 && k < 12000) || (k >= 18000 && k < 19000) ? "an" : "a";
}

function applies(s: Sentence, ctx: Record<string, unknown>): boolean {
  for (const [v, ids] of Object.entries(s.when ?? {})) {
    if (!ids.includes(String(ctx[`${v}__id`] ?? ctx[v]))) return false;
  }
  for (const [v, ids] of Object.entries(s.unless ?? {})) {
    if (ids.includes(String(ctx[`${v}__id`] ?? ctx[v]))) return false;
  }
  return true;
}

export interface VarMeta {
  id: string;
  label: Label;
  doc?: string;
}

/** User-facing variables in model order, with the methodology doc that explains each. */
export function visibleVars(model: CompiledModel): VarMeta[] {
  return model.vars.filter((v) => !v.hidden).map((v) => ({ id: v.id, label: v.label, doc: v.node.doc }));
}

/** Display-ready form of a person: value ids, gendered labels and prose in both languages. */
export interface PresentedPerson {
  index: number;
  values: Record<string, string | number | string[] | null>;
  labels: { he: Record<string, string>; en: Record<string, string> };
  text: { he: string[]; en: string[] };
}

export function presentPerson(
  model: CompiledModel,
  values: PersonValues,
  index: number,
  templates: { he: Templates; en: Templates },
): PresentedPerson {
  const ids: Record<string, string | number | string[] | null> = {};
  const labels = { he: {} as Record<string, string>, en: {} as Record<string, string> };
  const sexIdx = model.varIndex.get("sex");
  const female = sexIdx !== undefined && model.vars[sexIdx].values![values[sexIdx]].id === "female";
  model.vars.forEach((info, k) => {
    if (info.hidden) return;
    const x = values[k];
    if (info.multi) {
      const chosen = info.values!.filter((_, j) => (x & (1 << j)) !== 0);
      ids[info.id] = chosen.map((v) => v.id);
      for (const lang of ["he", "en"] as const) {
        labels[lang][info.id] = chosen.map((v) => labelFor(v.label, lang, female)).join(", ");
      }
    } else if (info.values && !info.numeric) {
      ids[info.id] = info.values[x].id;
      for (const lang of ["he", "en"] as const) labels[lang][info.id] = labelFor(info.values[x].label, lang, female);
    } else {
      const n = info.values ? Number(info.values[x].id) : x;
      ids[info.id] = Number.isNaN(n) ? null : n;
      for (const lang of ["he", "en"] as const) {
        labels[lang][info.id] = Number.isNaN(n) ? "—" : new Intl.NumberFormat(lang === "he" ? "he-IL" : "en-US").format(n);
      }
    }
  });
  return {
    index,
    values: ids,
    labels,
    text: { he: describe(model, values, templates.he), en: describe(model, values, templates.en) },
  };
}

const cache = new Map<string, IntlMessageFormat>();

function message(lang: Lang, text: string): IntlMessageFormat {
  const key = `${lang}:${text}`;
  let fmt = cache.get(key);
  if (!fmt) {
    fmt = new IntlMessageFormat(text, lang);
    cache.set(key, fmt);
  }
  return fmt;
}

function format(lang: Lang, text: string, ctx: Record<string, unknown>): string {
  return String(message(lang, text).format(ctx as Record<string, string | number>)).trim();
}

/** Adds the templates' lists (see ListSpec) to the context. */
export function addLists(ctx: Record<string, unknown>, templates: Templates): void {
  const lang = templates.lang;
  const and = new Intl.ListFormat(lang, { style: "long", type: "conjunction" });
  const or = new Intl.ListFormat(lang, { style: "long", type: "disjunction" });
  for (const [name, spec] of Object.entries(templates.lists ?? {})) {
    const byValue = new Map<string, string[]>();
    for (const [varId, phrase] of Object.entries(spec.items)) {
      const v = String(ctx[`${varId}__id`]);
      if (!byValue.has(v)) byValue.set(v, []);
      byValue.get(v)!.push(format(lang, phrase, ctx));
    }
    const parts = Object.entries(spec.groups)
      .filter(([v]) => byValue.has(v))
      .map(([v, t]) => format(lang, t, { ...ctx, list: and.format(byValue.get(v)!) }));
    ctx[name] = and.format(parts);
    ctx[`${name}__n`] = parts.length;
    if (spec.separate) {
      const apart = byValue.get(spec.separate) ?? [];
      ctx[`${name}__${spec.separate}`] = or.format(apart);
      ctx[`${name}__${spec.separate}_n`] = apart.length;
    }
  }
}

export function describe(
  model: CompiledModel,
  values: PersonValues,
  templates: Templates,
  extra: Record<string, unknown> = {},
): string[] {
  const ctx: Record<string, unknown> = { ...buildContext(model, values, templates.lang), ...extra };
  addLists(ctx, templates);
  const out: string[] = [];
  for (const s of templates.sentences) {
    if (!applies(s, ctx)) continue;
    const text = format(templates.lang, s.text, ctx);
    if (text) out.push(text);
  }
  return out;
}
