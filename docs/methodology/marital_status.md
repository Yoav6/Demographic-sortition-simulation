# Marital status

<!-- he-summary -->
**מצב משפחתי** — נשוי, גרוש, אלמן, רווק — לפי קבוצת אוכלוסייה, דתיות (ליהודים) או דת (לערבים), מין וגיל, מתוך הסקר החברתי 2024 של הלמ"ס (בני 20 ומעלה). לבני 18–19, שאינם בסקר, שיעור הנשואים נגזר ממספר הנישאים בגילים אלה (שנתון 2025, לוח 2.24) ומגודל שכבת הגיל.
<!-- /he-summary -->

## Definition

Legal marital status on the CBS scale: `married` (including married people living apart),
`divorced`, `widowed`, `never_married` (shown as "single"). Labels agree with the person's
grammatical gender in Hebrew (נשוי / נשואה...).

## Why these parents

`group` and `religiosity` (Haredim marry young and almost universally; divorce is rare among
Arab Christians); `sex` (women marry younger and are widowed more often); `age_band` (the
strongest single factor). The Social Survey tabulates marital status against exactly these.

## Sources

* `src:cbs_social_survey_2024` — table-generator cross-tabulations of marital status by
  religiosity × sex × 5-year age group for Jews (`marital_jews`), by sex × age for "others"
  (`marital_others`), and by religion × sex × age for Arabs outside the Jerusalem district
  (`marital_arabs`). Persons aged 20+.
* `src:cbs_abstract_2025_marriages` — persons marrying in 2023 by single year of age, sex and
  religion (table 2.24), for ages 18–19.
* `src:cbs_abstract_2025_population` — population aged 18 and 19 by religion and sex.

## Preprocessing

* "Living separately" (survey code 2) is counted as married. "Unknown" answers are dropped.
* Arab tables exclude the Jerusalem district, whose Arab residents are mostly not citizens.
* Survey age groups map to the model's age bands (65–74 → 65–69 and 70–74; 75+ → 75–79, 80–84,
  85+).

## Estimation

**Ages 20+.** For each sex, the survey counts form a table religiosity × age group × status
("others" join the Jewish table as one more religiosity level; Arabs use religion instead).
Each row is shrunk toward a *main-effects* fit — the table in which religiosity and age each
shift the distribution but do not interact, fitted by IPF to the row and column margins — with
10 pseudo-respondents:

```
p(status | rel, age) = (n · share + 10 · main-effects fit) / (n + 10)
```

where *n* is the number of respondents behind the row (the sum of 1/RSE² over its cells,
from the relative standard errors the generator reports). The 45–64 age groups are then lightly
smoothed (¼ previous + ½ own + ¼ next group). See [METHODOLOGY.md](../../METHODOLOGY.md) §3.

**Ages 18–19.** The survey starts at 20, and marriage at 18–19 is much rarer than at 20–24.
In a steady state the number of married 18–19-year-olds is about
`2·m(≤17) + 1.5·m(18) + 0.5·m(19)`, where *m(a)* is the number of persons marrying at age *a* in
a year (someone marrying at 18.5 spends 1.5 more years in the band). Divided by the population
aged 18–19, this gives the married share by religion and sex: Jewish women 2.6%, Jewish men
1.4%, Muslim women 6.4%, Muslim men 0.3%, Druze women 1.5%, Druze and Christian men ≈ 0,
Christian women 0.1%. The 20–24 pattern's odds of being married are then multiplied by one
factor per religion and sex so that the population-weighted share matches (so Haredi
18–19-year-olds remain far more often married than secular ones); the divorced share is scaled
by the same ratio and the widowed share set to zero. "Others" use the Jewish level.

## Calibration

None beyond the 18–19 adjustment: the survey is the calibration target.

## Validation

Model shares for ages 20+ (age-standardised to the survey) are compared with the survey's own
shares by religiosity (or religion) and sex — see the generated table below. Model, ages 20+:
65% of Jewish men and 60% of Jewish women are married; 26% / 21% never married; 7.4% of Jewish
women are widowed. Among Muslims, 65% of men and 66% of women are married.

## Limitations

* Small groups have few respondents: about 300 each for Arab Christians, Druze and "others".
  Their estimates lean more on the main-effects prior.
* CBS records legal status: couples living together without marriage are "single" or
  "divorced", and marriages abroad count only once registered.
* Arab rows depend on religion, not on religiosity (the survey crosses Arabs' marital status
  with religion).
* The 18–19 estimate assumes a steady state (constant marriage rates and cohort sizes) and uses
  2023 marriages, a year disrupted by the war from October.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `marital_status` — Marital status / מצב משפחתי

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/marital_status.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `married` | married | נשוי | נשואה |
| `divorced` | divorced | גרוש | גרושה |
| `widowed` | widowed | אלמן | אלמנה |
| `never_married` | single | רווק | רווקה |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey); `cbs_abstract_2025_marriages` (Central Bureau of Statistics (CBS)); `cbs_abstract_2025_population` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Marital status of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0058 | 0.0000 | 0.03 | ✅ pass |
| Marital status of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0131 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| Constraint: no widowed 18-19-year-olds | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
