# First name

<!-- he-summary -->
**שם פרטי** נדגם לפי קבוצת האוכלוסייה, המין ושנתון הלידה (קבוצות של 5 שנים), מתוך קובץ השמות של הלמ"ס: השמות הנוכחיים של כל ילידי 1949–2024 לפי שנת לידה, מין ומגזר — כולל עולים. ל"אחרים" (לא רשומים כיהודים או כערבים) אין גיליון בקובץ, ולכן נעשה שימוש בטבלאות מרשם האוכלוסין של האגודה לחקר שורשי משפחה (IGRA) לדת "אחר", בשילוב פרופיל הגיל של כל שם מהטבלה היהודית. לילידי 1948 ומטה משמשים שמות השנתון 1949–1953. השמות באנגלית לקוחים מרשימה ידנית ומוויקינתונים — בכתיב הנהוג בישראל (יהודה: Yehuda) או בכתיב ערבי לנושאי השם הערבים (עומר: Omar) — עם תעתיק כללי כגיבוי.
<!-- /he-summary -->

## Definition

The person's current registered first name (Hebrew spelling as in the Population Registry), with
an English form for the English interface.

## Why these parents

Name choice depends above all on the community (`group`), on `sex` and on the period of birth
(`birth_cohort`, five-year cohorts derived from age): the most common Jewish men's name among
people born in 1949–53 (David) differs from 2004–06 (David, Noam, Uri…), and immigrants' names
reflect their cohort of origin. The CBS table is published exactly by these three variables.

## Sources

* `src:cbs_names` — CBS release 391/2025, table 1: current first names of everyone born
  1949–2024 (registry), by sex, population group (Jews, Muslims, Christian Arabs, Druze) and year
  of birth. It includes immigrants (e.g. 8,152 Jewish women named Svetlana).
* `src:igra_registry_names` — Israel Genealogy Research Association's tables of registry first
  names for religion "Other" (Nov 2021), by sex, without birth years.
* `src:wikidata_given_names` — English labels of Wikidata given-name items, for display.

## Preprocessing

* Cells under 5 are suppressed by CBS (".."); each name's suppressed cells share the name's
  residual (published total minus shown cells) equally, capped at 4.
* Numbers with thousands separators ("1,478") are parsed.
* Five-year birth cohorts: 1949–53, 1954–58, …, 1999–2003, 2004–2006 (the youngest adults).

## Estimation

* Jews, Muslims, Christian Arabs, Druze: the names of each (group, sex, cohort) are ranked by count
  and the most common names covering 97% of people (at most 600) are kept and renormalised.
* Others: each IGRA name's registry count is multiplied by its relative frequency in the cohort
  among Jews of the same sex (count in cohort / name total, divided by the cohort's share of all
  Jewish names), or 1 if the name does not appear in the Jewish table; then the same top-97%
  rule is applied per cohort.
* People born before 1949 (aged 76+) use the 1949–53 cohort.
* Names of Muslims, Arab Christians and Druze get their own ids (`ar:` + the Hebrew spelling),
  because the same Hebrew spelling is often written differently in English for Jewish and
  Arab bearers (עומר: Omer / Omar; יוסף: Yosef / Yusuf; מרים: Miriam / Maryam).

**English forms** (display only; the model samples Hebrew registry spellings), in order:

1. a curated override (`data/manual/names/english_overrides.csv`, about 420 names), optionally
   limited to Jewish or Arab bearers;
2. otherwise, among the English labels of Wikidata given-name items with that Hebrew label, the
   one closest (edit distance) to a rule-based transliteration in the bearer community's style —
   so Israeli spellings such as Yehuda, Moshe, Avraham or Shmuel win over English biblical
   forms such as Judah, Moses, Abraham or Samuel; a different feminine form is kept for
   spellings shared by both sexes (Michel / Michelle);
3. otherwise the rule-based transliteration itself (about two-thirds of the 7,100 names, mostly
   rare ones).

The 160 most common Jewish names of each sex and the 130 most common Arab names of each sex
were reviewed by hand, and wrong choices fixed with overrides (e.g. David rather than Dovid,
Rivka rather than Rebeca, Ayoub rather than Hiob).

## Calibration

None beyond the source counts.

## Validation

Spot checks of the most common names per cell: Jewish men born 1949–53 — David, Yosef, Moshe,
Yaakov, Avraham; Jewish women born 1984–88 — Adi, Shiran, Rachel, Shani; "others" born 1974–78 —
Natalia, Elena, Olga, Tatiana, Yulia; "others" born 2004–06 — Daniel, Michael, Adam, David.

## Limitations

* No name × country-of-origin or name × religiosity data exist, so a Haredi man and a secular man
  of the same cohort draw from the same distribution.
* The rarest 3% of names are not represented.
* The oldest adults reuse the 1949–53 cohort.
* The "other" distribution borrows Jewish age profiles.
* Rare names fall back to a rough rule-based transliteration in English.

## Changelog

* 2026.10.0 — first version. English forms chosen by closeness to an Israeli or Arabic
  transliteration; separate ids for Arab citizens' names.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `birth_cohort` — Birth cohort / שנתון לידה

- **type:** `lookup` · hidden helper
- **parents:** `age`
- **distribution file:** `model/lookups/birth_cohort.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `1949-1953` | 1949-1953 | 1949-1953 |  |
| `1954-1958` | 1954-1958 | 1954-1958 |  |
| `1959-1963` | 1959-1963 | 1959-1963 |  |
| `1964-1968` | 1964-1968 | 1964-1968 |  |
| `1969-1973` | 1969-1973 | 1969-1973 |  |
| `1974-1978` | 1974-1978 | 1974-1978 |  |
| `1979-1983` | 1979-1983 | 1979-1983 |  |
| `1984-1988` | 1984-1988 | 1984-1988 |  |
| `1989-1993` | 1989-1993 | 1989-1993 |  |
| `1994-1998` | 1994-1998 | 1994-1998 |  |
| `1999-2003` | 1999-2003 | 1999-2003 |  |
| `2004-2006` | 2004-2006 | 2004-2006 |  |

Sources: `cbs_names` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `first_name` — First name / שם פרטי

- **type:** `table`
- **parents:** `group`, `sex`, `birth_cohort`
- **distribution file:** `model/cpts/first_name.csv`
- **categories:** 7101 (see the domain file)

Sources: `cbs_names` (Central Bureau of Statistics (CBS)); `igra_registry_names` (Israel Genealogy Research Association (IGRA), compiled by Philip Trauring)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
