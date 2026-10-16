# Earnings from work

<!-- he-summary -->
**הכנסה מעבודה.** למועסקים בלבד — מדרגת ההכנסה החודשית ברוטו (הסקר החברתי שואל רק מועסקים), סכום מדויק בתוך המדרגה, ואחוזון בקרב המועסקים. המדרגה תלויה במשלח היד, במין, בגיל ובקבוצת האוכלוסייה. הסכום מוגרל בתוך המדרגה בהתפלגות לוג-אחידה; במדרגה העליונה (מעל 21,000 ₪) — זנב פארטו. ההכנסה אינה עולה על תקרת מדרגת ההכנסה של משק הבית.
<!-- /he-summary -->

## Definition

* **`income`** — gross monthly income bracket of **employed** persons, on the Social Survey
  scale: up to ₪2,000, ₪2,001–3,000, … ₪14,001–21,000, over ₪21,000. Everyone who is not
  employed gets `not_employed`. The generator calls the variable "personal gross income", but
  it is asked only of employed persons (non-employed respondents are "not relevant"), so we
  treat it as earnings from work.
* **`income_amount`** — a monthly amount in shekels drawn inside the bracket, rounded to ₪100;
  not applicable for people who are not employed.
* **`income_percentile`** — the share of employed citizens in the model who earn less.

## Why these parents

`occupation` and `sex` (the gender gap in earnings is large in every occupation), `age_band`
(earnings rise with experience), `group` (Jews-and-others vs Arabs, separately tabulated),
`labour_status` (only the employed have earnings).

## Sources

* [`src:cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) — income bracket by occupation × sex × age group, for
  Jews-and-others (`income_by_occupation_jo`) and for Arabs outside the Jerusalem district
  (`income_by_occupation_arabs`). Employed persons aged 20+.

## Preprocessing

Unknowns, and the rare "no income" answers of employed persons (about 2%), are dropped.

## Estimation

* **Bracket.** Rows occupation × age group within each sex, shrunk toward their main-effects
  fit (10 pseudo-respondents) and smoothed over ages 45–64; separately for the two population
  groups. Retirees, the unemployed, people outside the labour force and soldiers get
  `not_employed`.
* **Amount.** Inside a closed bracket the amount is log-uniform. The open top bracket (over
  ₪21,000) has a Pareto tail with exponent α = 3, truncated where the uniform draw reaches
  0.999 (about ₪210,000). The amount is capped at the top of the person's *household* income
  bracket, so earnings never exceed household income.
* **Percentile.** Breakpoints (the amount at percentiles 0–100) are computed from the model's
  own distribution of brackets among the employed and the within-bracket shapes above, so
  percentiles are uniform over the simulated employed population.

## Calibration

None beyond the survey.

## Validation

Employed citizens in the model: median ₪10,500 a month, mean about ₪13,200; 10th percentile
₪3,900, 90th percentile ₪24,800. Medians: Jewish men ₪13,800, Jewish women ₪9,100; Muslim men
₪9,100, Muslim women ₪4,900. The bracket distribution by occupation and sex is compared with the
survey in the generated table below.

## Limitations

* Brackets, not amounts, come from data; amounts inside a bracket are a modelling choice, and
  the Pareto exponent of the top bracket (α = 3) is our own choice, neither estimated from
  Israeli data nor taken from a published estimate. Percentiles do not depend on these choices (within a bracket
  the rank is uniform whatever the shape); displayed amounts do.
* Self-reported income from a survey; no administrative (tax or National Insurance) data.
* No income is modelled for people who are not employed: pensions, allowances and capital
  income are reflected only in household income.
* Earnings do not depend on religiosity or education given occupation, sex and age.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `income` — Gross monthly earnings from work (bracket) / הכנסה חודשית ברוטו מעבודה (מדרגה)

- **type:** `table`
- **parents:** `labour_status`, `group`, `occupation`, `sex`, `age_band`
- **back-off order:** `occupation` → `sex` → `group` → `age_band`
- **distribution file:** `model/cpts/income.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `not_employed` | not employed | לא מועסק | לא מועסקת |
| `b01` | up to ₪2,000 | עד 2,000 ₪ |  |
| `b02` | ₪2,001–3,000 | 2,001–3,000 ₪ |  |
| `b03` | ₪3,001–4,000 | 3,001–4,000 ₪ |  |
| `b04` | ₪4,001–5,000 | 4,001–5,000 ₪ |  |
| `b05` | ₪5,001–6,000 | 5,001–6,000 ₪ |  |
| `b06` | ₪6,001–7,500 | 6,001–7,500 ₪ |  |
| `b07` | ₪7,501–10,000 | 7,501–10,000 ₪ |  |
| `b08` | ₪10,001–14,000 | 10,001–14,000 ₪ |  |
| `b09` | ₪14,001–21,000 | 14,001–21,000 ₪ |  |
| `b10` | over ₪21,000 | מעל 21,000 ₪ |  |

Sources: [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Earnings bracket of the employed by occupation and sex (20+) - Jews and others | [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) | 0.0095 | 0.0000 | 0.03 | ✅ pass |
| Earnings bracket of the employed by occupation and sex (20+) - Arabs | [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) | 0.0196 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: earnings exactly for the employed | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `income_amount` — Gross monthly earnings from work (₪) / הכנסה חודשית ברוטו מעבודה (ש"ח)

- **type:** `interval`
- **parents:** `income`
- **capped by:** `household_income`
- **distribution file:** `model/cpts/income_amount.csv`

Sources: [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Constraint: household income is at least the person's own earnings | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `income_percentile` — Earnings percentile among employed citizens / אחוזון ההכנסה מעבודה בקרב המועסקים

- **type:** `percentile`
- **parents:** `income_amount`
- **distribution file:** `model/cpts/income_percentile.csv`

Sources: [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Percentile is uniform among employed citizens (n = 638,050) | `model` | 0.0061 | — | 0.01 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
