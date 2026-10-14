# Household income and home ownership

<!-- he-summary -->
**הכנסת משק הבית ובעלות על דירה.** מדרגת ההכנסה החודשית ברוטו של משק הבית (מכל המקורות), סכום בתוך המדרגה ואחוזון בקרב האזרחים הבוגרים, ובעלות משק הבית על הדירה. למועסקים — לפי ההכנסה מעבודה, המצב המשפחתי והגיל; לשאינם מועסקים — לפי המצב בכוח העבודה, הגיל והמצב המשפחתי. הכנסת משק הבית אינה נמוכה מההכנסה האישית. הבעלות על הדירה תלויה בהכנסת משק הבית, בגיל ובמצב המשפחתי.
<!-- /he-summary -->

## Definition

* **`household_income`** — gross monthly income of the person's household from all sources, on
  the Social Survey scale: up to ₪2,500, ₪2,501–4,000, … ₪17,001–24,000, over ₪24,000, or no
  income.
* **`household_income_amount`** — an amount inside the bracket, rounded to ₪100.
* **`household_income_percentile`** — the share of adult citizens in the model whose household
  has a lower income (person-weighted: every adult counts once, so large households count
  several times).
* **`home_ownership`** — whether the household owns the dwelling it lives in (asked about the
  household: 74% of 20–24-year-olds, most living with their parents, answer yes).

## Why these parents

Household income ← `labour_status`, `income` (own earnings), `marital_status` (a spouse's
earnings), `age_band` (adult children at home, pensions), `group`. Home ownership ←
`household_income`, `age_band`, `marital_status`, `group`.

## Sources

* `src:cbs_social_survey_2024` — household income by marital status × own earnings bracket ×
  age for employed persons (`household_income_employed_*`); by labour-force status × age ×
  marital status for everyone (`household_income_by_status_*`); home ownership by household
  income × age × marital status (`home_ownership_*`). Each for Jews-and-others and for Arabs
  outside the Jerusalem district. Ages 20+.

## Preprocessing

About 27% of respondents did not report household income. They are dropped, which assumes
that within each cell those who answered resemble those who did not.

## Estimation

* **Employed people**: rows own-earnings bracket × age group within each marital status,
  shrunk toward their main-effects fit (10 pseudo-respondents). Household brackets lying
  entirely below the person's own earnings bracket are set to zero and the rest renormalised
  (a few survey answers are inconsistent, e.g. confusing net and gross).
* **Everyone else**: rows labour-force status × age group within each marital status.
  Retirees use "outside the labour force" at their age; soldiers in compulsory service use
  "outside the labour force" at 20–24.
* **Amount**: log-uniform inside a closed bracket; Pareto tail with α = 2.5 above ₪24,000;
  never below the person's own earnings (`floor_by: income_amount`).
* **Percentile**: breakpoints from the model's own distribution among all adult citizens.
* **Home ownership**: rows household bracket × age group within each marital status, shrunk
  toward their main-effects fit.

## Calibration

None beyond the survey.

## Validation

Model medians of household gross income: Jews ₪17,800, "others" ₪16,900, Druze ₪12,200, Arab
Christians ₪11,600, Muslims ₪10,400; ₪20,900 for employed adults and about ₪8,600 for retirees.
Homes owned by the household: 70% of Jewish adults, 78% of Muslims, 81% of Arab Christians.
Survey comparisons are in the generated table below.

## Limitations

* No individual wealth data exist; home ownership is the only wealth indicator.
* Household size and composition are not modelled, so household income is not per capita.
* About 2% of Jewish and 11% of Arab adults report a household with no income at all; the
  model keeps these answers.
* The household Pareto exponent (α = 2.5) is an assumption; percentiles do not depend on it.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `household_income` — Household gross monthly income / הכנסה חודשית ברוטו של משק הבית

- **type:** `table`
- **parents:** `labour_status`, `group`, `marital_status`, `income`, `age_band`
- **distribution file:** `model/cpts/household_income.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `none` | no income | אין הכנסה |  |
| `h01` | up to ₪2,500 | עד 2,500 ₪ |  |
| `h02` | ₪2,501–4,000 | 2,501–4,000 ₪ |  |
| `h03` | ₪4,001–5,000 | 4,001–5,000 ₪ |  |
| `h04` | ₪5,001–6,500 | 5,001–6,500 ₪ |  |
| `h05` | ₪6,501–8,000 | 6,501–8,000 ₪ |  |
| `h06` | ₪8,001–10,000 | 8,001–10,000 ₪ |  |
| `h07` | ₪10,001–13,000 | 10,001–13,000 ₪ |  |
| `h08` | ₪13,001–17,000 | 13,001–17,000 ₪ |  |
| `h09` | ₪17,001–24,000 | 17,001–24,000 ₪ |  |
| `h10` | over ₪24,000 | מעל 24,000 ₪ |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Household income bracket by labour-force status (20+) - Jews and others | `cbs_social_survey_2024` | 0.0332 | 0.0058 | 0.03 | ✅ pass |
| Household income bracket by labour-force status (20+) - Arabs | `cbs_social_survey_2024` | 0.0297 | 0.0094 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `household_income_amount` — Household gross monthly income (₪) / הכנסה חודשית ברוטו של משק הבית (ש"ח)

- **type:** `interval`
- **parents:** `household_income`
- **floored by:** `income_amount`
- **distribution file:** `model/cpts/household_income_amount.csv`

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Constraint: household income is at least the person's own earnings | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `household_income_percentile` — Household income percentile among adult citizens / אחוזון הכנסת משק הבית בקרב האזרחים הבוגרים

- **type:** `percentile`
- **parents:** `household_income_amount`
- **distribution file:** `model/cpts/household_income_percentile.csv`

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Percentile is uniform among adult citizens (n = 1,000,000) | `model` | 0.0035 | — | 0.01 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `home_ownership` — Home ownership (household) / בעלות על הדירה (משק הבית)

- **type:** `table`
- **parents:** `group`, `household_income`, `age_band`, `marital_status`
- **distribution file:** `model/cpts/home_ownership.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `yes` | owns its home | הדירה בבעלות משק הבית |  |
| `no` | does not own its home | הדירה אינה בבעלות משק הבית |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Home ownership by household income bracket (20+) - Jews and others | `cbs_social_survey_2024` | 0.0442 | 0.0000 | 0.03 | ✅ pass |
| Home ownership by household income bracket (20+) - Arabs | `cbs_social_survey_2024` | 0.0158 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
