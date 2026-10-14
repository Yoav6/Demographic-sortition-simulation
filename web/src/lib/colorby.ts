/**
 * "Colour seats by" options. Each option maps a person to one of a few ordered groups.
 * Nominal options use the categorical palette slots in fixed order; ordered options
 * (age, religiosity, ...) use a one-hue light-to-dark ramp. Palettes are the validated
 * defaults of the dataviz guide (see web/src/app.css for the light/dark tokens).
 */

import { TIERS, type PresentedPerson } from "@popsim/sampler";
import type { Lang } from "./i18n.ts";

export interface Group {
  key: string;
  label: { he: string; en: string };
}

export interface ColorOption {
  id: string;
  /** model variable the option reads */
  variable: string;
  label: { he: string; en: string };
  kind: "categorical" | "ordinal";
  groups: Group[];
  /** maps a value id (or number, for age) of `variable` to a group key */
  mapValue: (v: string | number) => string;
  /** population shares when they are known exactly (e.g. percentile quartiles), instead of
   * summing the variable's categorical marginal */
  expected?: Record<string, number>;
  /** reads the value from the person instead of `values[variable]` (e.g. the unusualness tier) */
  read?: (p: PresentedPerson) => string | number;
}

export function groupOf(option: ColorOption, p: PresentedPerson): string {
  return option.mapValue(option.read ? option.read(p) : (p.values[option.variable] as string | number));
}

// "How unusual?" tiers; the two smallest (4% + 1%) share the darkest step of the four-step ramp
const UNUSUAL_GROUP: Record<string, string> = { typical: "typical", somewhat: "somewhat", unusual: "unusual", very: "very", exceptional: "very" };
const tierShare = (id: string) => TIERS.filter((x) => UNUSUAL_GROUP[x.id] === id).reduce((a, x) => a + x.share, 0);

const g = (key: string, he: string, en: string): Group => ({ key, label: { he, en } });

const AGE_GROUPS = [g("18-29", "18–29", "18–29"), g("30-44", "30–44", "30–44"), g("45-64", "45–64", "45–64"), g("65+", "65+", "65+")];

function ageGroup(age: number): string {
  if (age < 30) return "18-29";
  if (age < 45) return "30-44";
  if (age < 65) return "45-64";
  return "65+";
}

const RELIGIOSITY_LEVEL: Record<string, string> = {
  hiloni: "secular",
  not_religious: "secular",
  masorti: "traditional",
  not_so_religious: "traditional",
  masorti_dati: "religious",
  dati: "religious",
  religious: "religious",
  haredi: "very",
  very_religious: "very",
};

const LOCALITY_TYPE_GROUP: Record<string, string> = {
  large_city: "large_city",
  city: "city",
  town: "town",
  arab_city: "arab",
  arab_town: "arab",
  bedouin_tribe: "arab",
  moshav: "rural",
  kibbutz: "rural",
  community: "rural",
  rural_other: "rural",
  other: "rural",
};

export const COLOR_OPTIONS: ColorOption[] = [
  {
    id: "sector",
    label: { he: "מגזר", en: "Sector" },
    kind: "categorical",
    groups: [
      g("jewish", "יהודים", "Jewish"),
      g("arab_muslim", "ערבים מוסלמים", "Arab Muslim"),
      g("bedouin", "בדואים", "Bedouin"),
      g("arab_christian", "ערבים נוצרים", "Arab Christian"),
      g("druze", "דרוזים", "Druze"),
      g("circassian", "צ'רקסים", "Circassian"),
      g("other", "לא רשומים כיהודים או כערבים", "Not registered as Jewish or Arab"),
    ],
    variable: "sector",
    mapValue: (v) => String(v),
  },
  {
    id: "religiosity",
    label: { he: "מידת דתיות", en: "Religiosity" },
    kind: "ordinal",
    groups: [
      g("secular", "חילונים / לא דתיים", "Secular / not religious"),
      g("traditional", "מסורתיים / לא כל כך דתיים", "Traditional / not so religious"),
      g("religious", "דתיים / מסורתיים-דתיים", "Religious / traditional-religious"),
      g("very", "חרדים / דתיים מאוד", "Haredi / very religious"),
    ],
    variable: "religiosity",
    mapValue: (v) => RELIGIOSITY_LEVEL[String(v)] ?? "secular",
  },
  {
    id: "sex",
    label: { he: "מין", en: "Sex" },
    kind: "categorical",
    groups: [g("female", "נשים", "Women"), g("male", "גברים", "Men")],
    variable: "sex",
    mapValue: (v) => String(v),
  },
  {
    id: "age",
    label: { he: "גיל", en: "Age" },
    kind: "ordinal",
    groups: AGE_GROUPS,
    variable: "age",
    mapValue: (v) => ageGroup(Number(v)),
  },
  {
    id: "district",
    label: { he: "מחוז", en: "District" },
    kind: "categorical",
    groups: [
      g("jerusalem", "ירושלים", "Jerusalem"),
      g("north", "הצפון", "North"),
      g("haifa", "חיפה", "Haifa"),
      g("center", "המרכז", "Center"),
      g("tel_aviv", "תל אביב", "Tel Aviv"),
      g("south", "הדרום", "South"),
      g("judea_samaria", "יהודה ושומרון", "Judea & Samaria"),
    ],
    variable: "district",
    mapValue: (v) => String(v),
  },
  {
    id: "locality_type",
    label: { he: "סוג יישוב", en: "Type of locality" },
    kind: "categorical",
    groups: [
      g("large_city", "עיר גדולה (100 אלף+)", "Large city (100k+)"),
      g("city", "עיר בינונית", "Medium city"),
      g("town", "עיירה", "Small town"),
      g("arab", "יישוב ערבי או בדואי", "Arab or Bedouin locality"),
      g("rural", "מושב, קיבוץ או יישוב קהילתי", "Moshav, kibbutz or community"),
    ],
    variable: "locality_type",
    mapValue: (v) => LOCALITY_TYPE_GROUP[String(v)] ?? "rural",
  },
];

const EDUCATION_LEVEL: Record<string, string> = {
  no_diploma: "below_bagrut",
  primary: "below_bagrut",
  secondary: "below_bagrut",
  bagrut: "bagrut",
  post_secondary: "bagrut",
  other_diploma: "bagrut",
  ba: "ba",
  ma: "graduate",
  phd: "graduate",
};

const GENERATION_GROUP: Record<string, string> = {
  immigrant: "immigrant",
  second_gen: "second_gen",
  third_gen: "third_gen",
  native: "native",
};

function quartile(p: number): string {
  if (p < 25) return "q1";
  if (p < 50) return "q2";
  if (p < 75) return "q3";
  return "q4";
}

const BLOC_OF: Record<string, string> = {
  likud: "coalition",
  religious_zionism: "coalition",
  shas: "coalition",
  utj: "coalition",
  yesh_atid: "opposition",
  national_unity: "opposition",
  yisrael_beiteinu: "opposition",
  labor: "opposition",
  meretz: "opposition",
  raam: "arab",
  hadash_taal: "arab",
  balad: "arab",
  jewish_home: "other",
  other_party: "other",
  did_not_vote: "did_not_vote",
  too_young: "too_young",
};

COLOR_OPTIONS.push(
  {
    id: "vote_2022",
    label: { he: "הצבעה ב-2022", en: "2022 vote" },
    kind: "categorical",
    groups: [
      g("coalition", "מפלגות הקואליציה", "Coalition parties"),
      g("opposition", "מפלגות האופוזיציה היהודיות", "Jewish opposition parties"),
      g("arab", "מפלגות ערביות", "Arab parties"),
      g("other", "אחרות (מתחת לאחוז החסימה)", "Other (below threshold)"),
      g("did_not_vote", "לא הצביעו", "Did not vote"),
      g("too_young", "צעירים מדי להצביע", "Too young to vote"),
    ],
    variable: "vote_2022",
    mapValue: (v) => BLOC_OF[String(v)] ?? "other",
  },
  {
    id: "preferred_source",
    label: { he: "מקור החדשות המועדף", en: "Preferred news source" },
    kind: "categorical",
    groups: [
      g("tv", "טלוויזיה", "TV"),
      g("sites", "אתרי חדשות", "News websites"),
      g("social", "רשתות חברתיות", "Social media"),
      g("radio", "רדיו", "Radio"),
      g("print", "עיתונים מודפסים", "Printed newspapers"),
      g("other", "מנועי חיפוש או פודקאסטים", "Search engines or podcasts"),
      g("none", "אינם מתעדכנים בחדשות", "Do not follow the news"),
    ],
    variable: "preferred_source",
    mapValue: (v) => (["tv", "sites", "social", "radio", "print", "none"].includes(String(v)) ? String(v) : "other"),
  },
  {
    id: "generation",
    label: { he: "דור בישראל", en: "Generation in Israel" },
    kind: "categorical",
    groups: [
      g("immigrant", "עולים", "Immigrants"),
      g("second_gen", "דור שני", "Second generation"),
      g("third_gen", "דור שלישי ומעלה", "Third generation or more"),
      g("native", "ערבים ודרוזים", "Arab and Druze citizens"),
    ],
    variable: "generation",
    mapValue: (v) => GENERATION_GROUP[String(v)] ?? "native",
  },
  {
    id: "marital_status",
    label: { he: "מצב משפחתי", en: "Marital status" },
    kind: "categorical",
    groups: [
      g("married", "נשואים", "Married"),
      g("never_married", "רווקים", "Single"),
      g("divorced", "גרושים", "Divorced"),
      g("widowed", "אלמנים", "Widowed"),
    ],
    variable: "marital_status",
    mapValue: (v) => String(v),
  },
  {
    id: "education",
    label: { he: "השכלה", en: "Education" },
    kind: "ordinal",
    groups: [
      g("below_bagrut", "ללא בגרות", "No matriculation"),
      g("bagrut", "בגרות או על-תיכונית", "Matriculation or post-secondary"),
      g("ba", "תואר ראשון", "Bachelor's degree"),
      g("graduate", "תואר שני או שלישי", "Master's or doctorate"),
    ],
    variable: "education",
    mapValue: (v) => EDUCATION_LEVEL[String(v)] ?? "below_bagrut",
  },
  {
    id: "military_service",
    label: { he: "שירות", en: "Service" },
    kind: "categorical",
    groups: [
      g("idf", 'שירתו בצה"ל', "Served in the IDF"),
      g("national_service", "שירות לאומי-אזרחי", "National or civic service"),
      g("none", "לא שירתו", "Did not serve"),
    ],
    variable: "military_service",
    mapValue: (v) => String(v),
  },
  {
    id: "labour_status",
    label: { he: "תעסוקה", en: "Work" },
    kind: "categorical",
    groups: [
      g("employed", "מועסקים", "Employed"),
      g("retired", "פנסיונרים", "Retired"),
      g("not_in_labour_force", "לא בכוח העבודה", "Not in the labour force"),
      g("unemployed", "מובטלים", "Unemployed"),
      g("compulsory_service", "בשירות חובה", "In compulsory service"),
    ],
    variable: "labour_status",
    mapValue: (v) => String(v),
  },
  {
    id: "household_income",
    label: { he: "הכנסת משק הבית", en: "Household income" },
    kind: "ordinal",
    groups: [
      g("q1", "הרבע התחתון", "Bottom quarter"),
      g("q2", "הרבע השני", "Second quarter"),
      g("q3", "הרבע השלישי", "Third quarter"),
      g("q4", "הרבע העליון", "Top quarter"),
    ],
    variable: "household_income_percentile",
    mapValue: (v) => quartile(Number(v)),
    expected: { q1: 0.25, q2: 0.25, q3: 0.25, q4: 0.25 },
  },
  {
    id: "unusual",
    label: { he: "עד כמה יוצאי דופן", en: "How unusual" },
    kind: "ordinal",
    groups: [
      g("typical", "שגרתיים", "Typical"),
      g("somewhat", "קצת יוצאי דופן", "Somewhat unusual"),
      g("unusual", "יוצאי דופן", "Unusual"),
      g("very", "יוצאי דופן מאוד או חריגים במיוחד", "Very unusual or exceptional"),
    ],
    variable: "unusual",
    read: (p) => p.unusual?.tier ?? "typical",
    mapValue: (v) => UNUSUAL_GROUP[String(v)] ?? "typical",
    expected: { typical: tierShare("typical"), somewhat: tierShare("somewhat"), unusual: tierShare("unusual"), very: tierShare("very") },
  },
);

export function optionLabel(o: { label: { he: string; en: string } }, lang: Lang) {
  return o.label[lang];
}

/** CSS variable for a group's fill: categorical slots or ordinal ramp steps. */
export function groupColor(option: ColorOption, index: number): string {
  if (option.kind === "ordinal") {
    const n = option.groups.length;
    const step = n <= 1 ? 3 : Math.round((index * 3) / (n - 1));
    return `var(--ramp-${step})`;
  }
  return `var(--series-${(index % 8) + 1})`;
}
