# Highest diploma

<!-- he-summary -->
**התעודה הגבוהה ביותר** — מללא תעודה ועד תואר שלישי — לפי קבוצת אוכלוסייה, דתיות או דת, מין, גיל ויבשת לידה. שני לוחות של הסקר החברתי 2024 (לפי דתיות, ולפי יבשת לידה) משולבים בהתאמה פרופורציונית איטרטיבית (IPF) על פני הרכב האוכלוסייה של המודל. לבני 18–19 אין תארים אקדמיים או תעודות על-תיכוניות.
<!-- /he-summary -->

## Definition

The highest diploma received, on the Social Survey scale: `no_diploma` (never attended school, or
attended without receiving any certificate), `primary` (elementary or middle school, including
those who attended high school without finishing), `secondary` (high-school completion without
matriculation), `bagrut` (matriculation certificate), `post_secondary` (non-academic
post-secondary diploma, e.g. practical engineer or teaching seminary), `ba`, `ma` (including
medical doctors), `phd`, and `other_diploma`.

## Why these parents

`group` and `religiosity` (Haredi men mostly study in yeshivas, which award no recognised
diploma; Arab citizens' attainment differs by religion); `sex`; `age_band` (attainment has risen
steeply across cohorts); `birth_region` (immigrants from the former USSR are highly educated;
older immigrants from North Africa much less). The Social Survey tabulates diplomas against
each of these, but not all at once.

## Sources

* `src:cbs_social_survey_2024` — highest diploma by religiosity × sex × age group for Jews
  (`diploma_jews`), sex × age for "others" (`diploma_others`), religion × sex × age for Arabs
  outside the Jerusalem district (`diploma_arabs`), and continent of birth × sex × age for Jews
  (`diploma_by_birth_jews`). Ages 20+.

## Preprocessing

"Never attended" (code 0) and "no certificate" (code 9) are merged into `no_diploma`; unknowns
are dropped. Continent of birth uses the CBS grouping (the former USSR is Europe).

## Estimation

1. **Each table separately**: shrinkage toward the main-effects fit (10 pseudo-respondents)
   and light smoothing of the 45–64 groups, as on the marital-status page.
2. **Combining religiosity and birthplace.** For Jews, the two tables give
   P(diploma | religiosity, sex, age) and P(diploma | continent of birth, sex, age). Within each
   sex × age band, they are combined with `combine()`: IPF over the model's own population
   counts of religiosity × continent of birth (computed exactly from the frame, religiosity and
   origin tables), finding P(diploma | religiosity, birthplace) whose averages over birthplace
   reproduce the religiosity table exactly and whose averages over religiosity reproduce the
   birthplace table (adjusted to the same overall totals). The starting point is the
   naive-Bayes product, so the two factors interact only as much as the data require. "Others"
   use the same procedure with a single religiosity level.
3. **Arabs** use their religion table (all are born in Israel in the model).
4. **18–19-year-olds** use the 20–24 distribution with post-secondary and academic diplomas
   moved to matriculation, since they are too young to hold them.

## Calibration

Step 2 reproduces the religiosity table exactly and the birthplace table up to the totals
adjustment.

## Validation

Ages 25–64 in the model: academic degree (BA, MA or PhD) for 45% of Jews — 56% of the secular,
51% of Dati, 21% of Haredim (who also have the highest shares with no diploma, 22%, and with
"other" diplomas, 12%) — and for 22% of Muslims, 35% of Arab Christians and 22% of Druze.
Among Jews aged 25–64 born in Europe-America, 53% hold a degree; born in Africa, 20%. Survey
comparisons by religiosity/religion and sex and by continent of birth are in the generated
table below.

## Limitations

* The three-way pattern religiosity × birthplace × diploma is inferred (IPF), not observed.
* Arab rows depend on religion, not religiosity.
* Foreign degrees are counted as reported by respondents, whatever their recognition in Israel.
* "Other diploma" is not defined further by CBS; for Haredi men it likely includes yeshiva and
  rabbinical certificates.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `education` — Highest diploma / התעודה הגבוהה ביותר

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `birth_region`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/education.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `no_diploma` | no diploma | ללא תעודה |  |
| `primary` | elementary or middle school | בית ספר יסודי או חטיבת ביניים |  |
| `secondary` | high school without matriculation | תיכון ללא בגרות |  |
| `bagrut` | matriculation (bagrut) | תעודת בגרות |  |
| `post_secondary` | post-secondary non-academic diploma | תעודה על-תיכונית לא אקדמית |  |
| `ba` | bachelor's degree | תואר ראשון |  |
| `ma` | master's degree | תואר שני |  |
| `phd` | doctorate | תואר שלישי |  |
| `other_diploma` | other diploma | תעודה אחרת |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Highest diploma of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0056 | 0.0000 | 0.03 | ✅ pass |
| Highest diploma of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0163 | 0.0000 | 0.04 | ✅ pass |
| Highest diploma of Jews by continent of birth and sex (20+) | `cbs_social_survey_2024` | 0.0208 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: no academic or post-secondary diploma at 18-19 | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: graduate students already hold an academic degree | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: a field of degree exactly for holders of an academic degree | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
