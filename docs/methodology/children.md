# Number of children

<!-- he-summary -->
**מספר ילדים** שנולדו לאדם (0 עד 6, ו-7 ומעלה), לפי קבוצת אוכלוסייה, דתיות או דת, מין, גיל ומצב משפחתי, מתוך הסקר החברתי 2024. לבני 18–19 — לפי דפוס בני 20–24 באותו מצב משפחתי, עם תקרה של ילד אחד.
<!-- /he-summary -->

## Definition

Children ever born to the person (for men: children they fathered), as answered in the Social
Survey: 0, 1, …, 6, and "7 or more". It counts children of any age, whether or not they live
with the person.

## Why these parents

`marital_status` (most children are born within marriage), `age_band` (completed family
size grows with age), `group` and `religiosity` (Haredi families average about six children at
40–44; secular Jewish families about two), and `sex` (men become fathers later than women
become mothers).

## Sources

* `src:cbs_social_survey_2024` — children born by marital status, crossed with religiosity ×
  sex × age group for Jews (`children_jews`), sex × age for "others" (`children_others`) and
  religion × sex × age for Arabs outside the Jerusalem district (`children_arabs`). Ages 20+.

## Preprocessing

"Unknown" and "not relevant" answers are dropped (under 1%). Marital status is mapped as on the
marital-status page.

## Estimation

Within each sex × marital status slice, a religiosity (or religion) × age-group table is shrunk
toward its main-effects fit with 10 pseudo-respondents, and the 45–64 groups are lightly
smoothed — the method described on the marital-status page and in
[METHODOLOGY.md](../../METHODOLOGY.md) §3.

**18–19-year-olds** use the 20–24 distribution for their marital status, with two or more
children moved to one child (a married 19-year-old typically married within the past year or
two).

## Calibration

None; the survey is the target.

## Validation

Mean number of children at ages 40–44 in the model: Haredi women 6.0 and men 5.8; Dati 4.0 /
4.1; traditional-religious 2.8 / 2.5; traditional 2.3 / 2.6; secular 2.2 / 2.0; Muslim women 3.9,
men 3.2; Druze women 3.5; Arab Christian women 2.7. The survey comparison by religiosity and sex
is in the generated table below.

## Limitations

* Children ever born, not the household's current composition: the model does not know who
  lives with whom.
* Arab rows depend on religion, not religiosity.
* The cap at one child for 18–19-year-olds is a simplification.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `children` — Number of children / מספר ילדים

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `marital_status`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/children.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `0` | none | אין |  |
| `1` | 1 | 1 |  |
| `2` | 2 | 2 |  |
| `3` | 3 | 3 |  |
| `4` | 4 | 4 |  |
| `5` | 5 | 5 |  |
| `6` | 6 | 6 |  |
| `7` | 7 or more | 7 ומעלה |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Children of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0065 | 0.0000 | 0.03 | ✅ pass |
| Children of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0307 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |
| Constraint: at most one child at 18-19 | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
