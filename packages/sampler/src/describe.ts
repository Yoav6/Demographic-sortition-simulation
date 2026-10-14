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
import { nameSurprise, unusual, type Level, type Ordinal, type Tier } from "./unusual.ts";

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
  unusual?: UnusualTemplates;
}

/** Wording of the "How unusual?" section (ICU messages; {gender} is available in all). */
export interface UnusualTemplates {
  /** the question above the score: {name}, gender */
  title: string;
  /** tooltip at the name: {name}, {cond}, {base} (the name is not part of the score) */
  name_note: string;
  tiers: Record<Tier, string>;
  /** headline above / below the median: {x} = percent of citizens */
  more: string;
  less: string;
  /** when nothing deviates */
  none: string;
  /** level names, and the count of deviations per level ({n}, {major}, {notable}, {minor}), shown
   * from two deviations on */
  levels: Record<Level, string>;
  /** level names as used in the summary's list of counts ("2 notable"); {n}, {parts} */
  levels_plural: Record<Level, string>;
  /** headings of the lists of deviations per level */
  level_titles: Record<Level, string>;
  summary_part: string;
  summary: string;
  /** one reason: {label}, {value}, {causes}, {cond}, {base} */
  reason: string;
  /** a reason without a named cause */
  reason_plain: string;
  /** reasons for ordered variables (income, ...): also {dir} (below/above usual), {usual} (the
   * usual value for people like them) and {x}, {beyond}: percent of them on the far side */
  reason_ordered: string;
  reason_ordered_plain: string;
  directions: Record<Ordinal["direction"], { dir: string; beyond: string }>;
  /** value phrase for a set item the person does not have: {item} */
  absent: string;
  /** frequencies: {n} in "1 in n", or {p} percent */
  one_in: string;
  percent: string;
  /** short variable names for reasons (default: the variable's label) */
  names: Record<string, string>;
  /** "given ..." phrases per variable (default: the variable's label) */
  causes: Record<string, string>;
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

/** The "How unusual?" score of a presented person, with its wording in both languages. */
export interface PresentedUnusual {
  /** raw score (sum of bits beyond the hinge) and its percentile among citizens (0-100) */
  score: number;
  percentile: number;
  tier: Tier;
  reasons: { variable: string; value: string; present?: boolean; pCond: number; pBase: number; causes: string[]; level: Level; bits: number; ordinal?: Ordinal }[];
  text: Record<Lang, { title: string; name_note: string; tier: string; headline: string; summary: string; levels: Record<Level, string>; level_titles: Record<Level, string>; reasons: string[] }>;
}

/** Display-ready form of a person: value ids, gendered labels and prose in both languages. */
export interface PresentedPerson {
  index: number;
  values: Record<string, string | number | string[] | null>;
  labels: { he: Record<string, string>; en: Record<string, string> };
  text: { he: string[]; en: string[] };
  unusual?: PresentedUnusual;
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
  const out: PresentedPerson = {
    index,
    values: ids,
    labels,
    text: { he: describe(model, values, templates.he), en: describe(model, values, templates.en) },
  };
  if (templates.he.unusual && templates.en.unusual) out.unusual = presentUnusual(model, values, female, templates);
  return out;
}

const sig = (x: number, digits: number) => Number(x.toPrecision(digits));

/** "1 in 80" when both shares are small, else percentages. */
function frequencies(t: UnusualTemplates, lang: Lang, pCond: number, pBase: number): [string, string] {
  const nf = new Intl.NumberFormat(lang === "he" ? "he-IL" : "en-US", { maximumSignificantDigits: 2 });
  const one = (p: number) => format(lang, t.one_in, { n: nf.format(Math.max(2, sig(1 / p, 2))) });
  const pct = (p: number) => format(lang, t.percent, { p: nf.format(p * 100) });
  return Math.max(pCond, pBase) <= 0.2 ? [one(pCond), one(pBase)] : [pct(pCond), pct(pBase)];
}

export function presentUnusual(
  model: CompiledModel,
  values: PersonValues,
  female: boolean,
  templates: { he: Templates; en: Templates },
): PresentedUnusual {
  const u = unusual(model, values);
  const text = {} as PresentedUnusual["text"];
  for (const lang of ["he", "en"] as const) {
    const t = templates[lang].unusual!;
    const g = { gender: female ? "female" : "male" };
    const and = new Intl.ListFormat(lang, { style: "long", type: "conjunction" });
    const pct = Math.round(u.percentile);
    const counts = { major: 0, notable: 0, minor: 0 };
    for (const r of u.reasons) counts[r.level]++;
    const nm = nameSurprise(model, values);
    const first = model.vars[model.varIndex.get("first_name")!];
    const name = nm ? labelFor(first.values!.find((x) => x.id === nm.value)!.label, lang, female) : "";
    const [nameCond, nameBase] = nm ? frequencies(t, lang, nm.pCond, nm.pBase) : ["", ""];
    const reasons = u.reasons.map((r) => {
      const info = model.vars[model.varIndex.get(r.variable)!];
      const v = info.values!.find((x) => x.id === r.value)!;
      const name = labelFor(v.label, lang, female);
      const value = r.present === false ? format(lang, t.absent, { ...g, item: name }) : name;
      const [cond, base] = frequencies(t, lang, r.pCond, r.pBase);
      const causes = r.causes.map((c) =>
        t.causes[c] ? format(lang, t.causes[c], g) : labelFor(model.vars[model.varIndex.get(c)!].label, lang, female),
      );
      const label = t.names[r.variable] ?? labelFor(info.label, lang, female);
      const o = r.ordinal;
      if (o) {
        const usual = labelFor(info.values!.find((x) => x.id === o.usual)!.label, lang, female);
        const d = t.directions[o.direction];
        const x = Math.min(99, Math.max(1, Math.round(o.beyond * 100)));
        const msg = causes.length ? t.reason_ordered : t.reason_ordered_plain;
        return format(lang, msg, { ...g, label, value, causes: and.format(causes), cond, base, dir: d.dir, beyond: d.beyond, usual, x });
      }
      const msg = causes.length ? t.reason : t.reason_plain;
      return format(lang, msg, { ...g, label, value, causes: and.format(causes), cond, base });
    });
    text[lang] = {
      title: format(lang, t.title, { ...g, name }),
      name_note: nm ? format(lang, t.name_note, { ...g, name, cond: nameCond, base: nameBase }) : "",
      tier: format(lang, t.tiers[u.tier], g),
      headline: format(lang, pct >= 50 ? t.more : t.less, { ...g, x: pct >= 50 ? pct : 100 - pct }),
      summary:
        u.reasons.length >= 2
          ? format(lang, t.summary, {
              ...g,
              n: u.reasons.length,
              parts: (["major", "notable", "minor"] as const).filter((l) => counts[l]).map((l) => format(lang, t.summary_part, { x: counts[l], level: t.levels_plural[l] })).join(lang === "he" ? ", " : ", "),
            })
          : "",
      levels: t.levels,
      level_titles: t.level_titles,
      reasons: reasons.length ? reasons : [format(lang, t.none, g)],
    };
  }
  return {
    score: sig(u.score, 4),
    percentile: u.percentile,
    tier: u.tier,
    reasons: u.reasons.map((r) => ({
      variable: r.variable,
      value: r.value,
      ...(r.present === undefined ? {} : { present: r.present }),
      pCond: sig(r.pCond, 4),
      pBase: sig(r.pBase, 4),
      causes: r.causes,
      level: r.level,
      bits: sig(r.bits, 3),
      ...(r.ordinal ? { ordinal: r.ordinal } : {}),
    })),
    text,
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
