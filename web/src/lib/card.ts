/**
 * The member card's table: attributes grouped into sections, with related attributes merged
 * into one line ("printed newspapers: sometimes, mainly Yedioth Ahronoth"). Each line names the
 * variable whose methodology page its "?" link opens.
 */

import type { PresentedPerson } from "@popsim/sampler";
import type { Lang } from "./i18n.ts";

type L = { he: string; en: string };

export interface Line {
  /** variable whose label (unless `label` is given) and methodology page the line uses */
  doc: string;
  /** all variables the line shows (default: [doc]); a "How unusual?" reason about any of them
   * marks the line */
  vars?: string[];
  label?: L;
  /** the value text, or null to leave the line out */
  value: (p: PresentedPerson, lang: Lang) => string | null;
}

export interface Section {
  id: string;
  label: L;
  lines: Line[];
}

const lab = (p: PresentedPerson, lang: Lang, id: string) => p.labels[lang][id];
const val = (p: PresentedPerson, id: string) => p.values[id];
const list = (p: PresentedPerson, id: string) => (Array.isArray(val(p, id)) ? (val(p, id) as string[]) : []);
const pct = (p: PresentedPerson, id: string) => String(Math.round(Number(val(p, id))));
const plain = (id: string): Line => ({ doc: id, value: (p, lang) => lab(p, lang, id) ?? null });
const words: Record<string, L> = {
  mainly: { he: "בעיקר", en: "mainly" },
  score: { he: "ציון", en: "score" },
  higher_adults: { he: "גבוה מ-{x}% מהאזרחים הבוגרים", en: "higher than {x}% of adult citizens" },
  higher_employed: { he: "גבוה מ-{x}% מהמועסקים", en: "higher than {x}% of employed citizens" },
  per_month: { he: "בחודש", en: "a month" },
  children: { he: "ילדים", en: "children" },
  chronic: { he: "מחלה כרונית", en: "chronic illness" },
  disability: { he: "מוגבלות חמורה", en: "severe disability" },
};
const w = (k: string, lang: Lang, x = "") => words[k][lang].replace("{x}", x);

/** frequency, then the outlets (TV channels, sites, networks) or the main newspaper */
function medium(freq: string, detail?: string, mainly = false): Line {
  return {
    doc: freq,
    vars: detail ? [freq, detail] : [freq],
    value: (p, lang) => {
      const f = lab(p, lang, freq);
      if (!detail || val(p, freq) === "never") return f;
      if (mainly) return val(p, detail) === "none" ? f : `${f}, ${w("mainly", lang)} ${lab(p, lang, detail)}`;
      const items = list(p, detail);
      return items.length ? `${f} — ${lab(p, lang, detail)}` : f;
    },
  };
}

export const SECTIONS: Section[] = [
  {
    id: "personal",
    label: { he: "אישי", en: "Personal" },
    lines: [
      {
        doc: "locality",
        vars: ["locality", "locality_type", "district"],
        value: (p, lang) => `${lab(p, lang, "locality")} (${lab(p, lang, "locality_type")}), ${lab(p, lang, "district")}`,
      },
      {
        doc: "age",
        vars: ["age", "age_band", "sex"],
        label: { he: "מין וגיל", en: "Sex and age" },
        value: (p, lang) => `${lab(p, lang, "sex")}, ${lab(p, lang, "age")}`,
      },
      {
        doc: "sector",
        vars: ["sector", "group"],
        label: { he: "מגזר (דת רשומה)", en: "Sector (registered religion)" },
        value: (p, lang) => {
          const s = lab(p, lang, "sector");
          const g = lab(p, lang, "group");
          return g && g !== s ? `${s} (${g})` : s;
        },
      },
      plain("religiosity"),
      {
        doc: "origin",
        vars: ["origin", "ancestry"],
        value: (p, lang) =>
          val(p, "ancestry") && val(p, "ancestry") !== "not_applicable" ? `${lab(p, lang, "origin")}; ${lab(p, lang, "ancestry")}` : lab(p, lang, "origin"),
      },
      {
        doc: "marital_status",
        vars: ["marital_status", "children"],
        label: { he: "משפחה", en: "Family" },
        value: (p, lang) => `${lab(p, lang, "marital_status")}; ${w("children", lang)}: ${lab(p, lang, "children")}`,
      },
      plain("military_service"),
      {
        doc: "health",
        vars: ["health", "chronic", "disability"],
        value: (p, lang) =>
          [lab(p, lang, "health"), val(p, "chronic") === "yes" ? w("chronic", lang) : null, val(p, "disability") === "yes" ? w("disability", lang) : null]
            .filter(Boolean)
            .join("; "),
      },
      plain("vote_2022"),
    ],
  },
  {
    id: "education",
    label: { he: "השכלה", en: "Education" },
    lines: [
      {
        doc: "education",
        vars: ["education", "degree_field"],
        value: (p, lang) => (val(p, "degree_field") && val(p, "degree_field") !== "none" ? `${lab(p, lang, "education")} — ${lab(p, lang, "degree_field")}` : lab(p, lang, "education")),
      },
      {
        doc: "studying",
        vars: ["studying", "study_field"],
        value: (p, lang) => (val(p, "study_field") && val(p, "study_field") !== "none" ? `${lab(p, lang, "studying")} — ${lab(p, lang, "study_field")}` : lab(p, lang, "studying")),
      },
      {
        doc: "literacy_level",
        label: { he: "מיומנות קריאה (משוערת)", en: "Literacy (modelled)" },
        value: (p, lang) =>
          `${lab(p, lang, "literacy_level")} (${w("score", lang)} ${lab(p, lang, "literacy_score")}/500; ${w("higher_adults", lang, pct(p, "literacy_percentile"))})`,
      },
    ],
  },
  {
    id: "work",
    label: { he: "עבודה וכלכלה", en: "Work and finances" },
    lines: [
      {
        doc: "labour_status",
        vars: ["labour_status", "occupation"],
        value: (p, lang) => (val(p, "occupation") === "none" ? lab(p, lang, "labour_status") : `${lab(p, lang, "labour_status")} — ${lab(p, lang, "occupation")}`),
      },
      {
        doc: "industry",
        vars: ["industry", "work_status"],
        value: (p, lang) =>
          val(p, "industry") === "none" ? null : val(p, "work_status") === "none" ? lab(p, lang, "industry") : `${lab(p, lang, "industry")} (${lab(p, lang, "work_status")})`,
      },
      {
        doc: "income_amount",
        vars: ["income", "income_amount"],
        label: { he: "הכנסה חודשית ברוטו מעבודה", en: "Gross monthly earnings" },
        value: (p, lang) =>
          val(p, "income_amount") === null ? null : `₪${lab(p, lang, "income_amount")} (${w("higher_employed", lang, pct(p, "income_percentile"))})`,
      },
      {
        doc: "household_income_amount",
        vars: ["household_income", "household_income_amount"],
        label: { he: "הכנסת משק הבית (ברוטו, חודשית)", en: "Household gross monthly income" },
        value: (p, lang) =>
          `₪${lab(p, lang, "household_income_amount")} (${w("higher_adults", lang, pct(p, "household_income_percentile"))})`,
      },
      plain("home_ownership"),
    ],
  },
  {
    id: "media",
    label: { he: "תקשורת", en: "Media" },
    lines: [
      { ...plain("online"), vars: ["online", "social_networks"] },
      plain("news_frequency"),
      plain("preferred_source"),
      medium("news_tv", "tv_channels"),
      medium("news_radio"),
      medium("news_print", "newspaper", true),
      medium("news_sites", "news_websites"),
      medium("news_social"),
      { doc: "news_networks", value: (p, lang) => (list(p, "news_networks").length ? lab(p, lang, "news_networks") : null) },
      medium("news_search"),
      medium("news_podcasts"),
    ],
  },
];
