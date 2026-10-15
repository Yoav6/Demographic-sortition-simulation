# Health: self-rated health, chronic illness, severe disability

<!-- he-summary -->
**בריאות.** מצב בריאות לפי הערכה עצמית (טוב מאוד עד לא טוב בכלל), מחלה או בעיה בריאותית כרונית, ומוגבלות תפקודית חמורה — לפי קבוצת אוכלוסייה, דתיות או דת, מין וגיל, ובנוסף: מצב הבריאות תלוי בהשכלה, המחלה הכרונית במצב הבריאות, והמוגבלות בשניהם. כל צומת משלב לוח של הסקר החברתי 2024 לפי דתיות עם לוח לפי ההורה הנוסף, בהתאמה פרופורציונית איטרטיבית על פני הרכב האוכלוסייה של המודל.
<!-- /he-summary -->

## Definition

* **`health`** — self-rated health in the Social Survey: very good, good, not so good, poor
  ("not good at all").
* **`chronic`** — has a chronic illness or health problem (yes/no).
* **`disability`** — a severe functional disability: CBS's derived indicator of a health problem
  or disability that disturbs daily functioning very much (yes/no).

## Why these parents

All three depend on `age_band` and `sex`, and differ by `group` and `religiosity`. Self-rated
health also falls steeply with lower `education`, at every age. Chronic illness is closely tied
to self-rated `health`, and severe disability to both — so the three form a chain, and a person
who rates their health as poor will usually have a chronic condition.

## Sources

* `src:cbs_social_survey_2024` — self-rated health, chronic illness and severe disability by
  religiosity × sex × age for Jews (`health_jews`, `chronic_jews`, `disability_jews`), sex × age
  for "others", religion × sex × age for Arabs outside the Jerusalem district; self-rated health
  by diploma × sex × age (`health_by_diploma`), chronic illness by self-rated health × sex × age
  (`chronic_by_health`), and severe disability by self-rated health × chronic illness × age
  (`disability_by_health`). Ages 20+.

## Preprocessing

Unknowns are dropped. The table by health and chronic illness has no breakdown by sex; it is
used for both sexes (sex enters through the population table).

## Estimation

Each table is shrunk toward its main-effects fit (10 pseudo-respondents) and smoothed over ages
45–64. Then, as for labour-force status, the population table P(t | religiosity or religion,
sex, age) is combined with the table by the other parent — P(health | diploma, sex, age),
P(chronic | health, sex, age), P(disability | health × chronic, age) — by IPF over the model's
own joint counts within each sex × age band (`with_second()`). 18–19-year-olds use the 20–24
pattern.

## Calibration

The religiosity (or religion) margins are reproduced exactly; the second table's margins up to
a totals adjustment.

## Validation

In the model, 78% of 18–24-year-olds rate their health as very good, against 9% at 75+;
chronic illness rises from 14% to 74%, and severe disability from 8% to 47%. Among people who
rate their health as poor, 90% have a severe disability; among those in very good health, 4%.
Survey comparisons by religiosity (or religion) and sex are in the generated table below.

## Limitations

* Self-reported health, not diagnoses: the model says nothing about specific conditions.
* The survey covers people living in households; residents of nursing homes and other
  institutions — a notable share of the oldest — are not represented, so health at 85+ is
  probably overstated.
* Arab rows depend on religion, not religiosity.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `health` — Self-rated health / מצב בריאות (הערכה עצמית)

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `education`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/health.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `very_good` | very good | טוב מאוד |  |
| `good` | good | טוב |  |
| `not_so_good` | not so good | לא כל כך טוב |  |
| `not_good` | poor | לא טוב בכלל |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Self-rated health of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0126 | 0.0000 | 0.03 | ✅ pass |
| Self-rated health of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0123 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `chronic` — Chronic illness or health problem / מחלה או בעיה בריאותית כרונית

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `health`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/chronic.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `yes` | yes | כן |  |
| `no` | no | לא |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Chronic illness of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0061 | 0.0000 | 0.03 | ✅ pass |
| Chronic illness of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0065 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `disability` — Severe functional disability / מוגבלות תפקודית חמורה

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `health`, `chronic`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/disability.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `yes` | yes | כן |  |
| `no` | no | לא |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Severe disability of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0043 | 0.0000 | 0.03 | ✅ pass |
| Severe disability of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0125 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
