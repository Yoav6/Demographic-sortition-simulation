# Labour-force status

<!-- he-summary -->
**מצב בכוח העבודה** — מועסק, מובטל, לא בכוח העבודה, פנסיונר (מי שאינו בכוח העבודה בגיל 65 ומעלה), או בשירות חובה — לפי קבוצת אוכלוסייה, דתיות או דת, מין, גיל והשכלה. לוחות הסקר החברתי לפי דתיות ולפי השכלה משולבים ב-IPF על פני הרכב האוכלוסייה של המודל.
<!-- /he-summary -->

## Definition

* `employed`, `unemployed` (not working and looking for work) and `not_in_labour_force` — the
  Social Survey's labour-force status;
* `retired` — outside the labour force at age 65 or over (a label, not a separate measurement);
* `compulsory_service` — currently in compulsory IDF or national service (from `in_service`).

## Why these parents

`in_service` (soldiers are neither employed nor looking for work); `group` and `religiosity`
(Haredi men often study full-time in yeshivas; Arab women's employment is low); `sex`;
`age_band` (education, child-rearing and retirement); `education` (employment rises steeply
with education, especially for Arab women).

## Sources

* [`src:cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) — labour-force status by religiosity × sex × age for Jews
  (`employment_jews`), sex × age for "others", religion × sex × age for Arabs outside the
  Jerusalem district (`employment_arabs`), and by diploma × sex × age for Jews-and-others and
  for Arabs (`employment_by_diploma_jo`, `employment_by_diploma_arabs`). Ages 20+.

## Preprocessing

Unknowns are dropped; diplomas are mapped as on the education page.

## Estimation

Each table is shrunk toward its main-effects fit and smoothed over ages 45–64. Then, within each
sex × age band, P(status | religiosity) and P(status | education) are combined with
`combine()` — IPF over the model's own population counts of religiosity × education (computed
exactly from the frame and the religiosity, origin and education tables). For Arabs the first
table is by religion, and the "religiosity" dimension is the population group. Outside the
labour force at 65+ is relabelled `retired`. People in service get `compulsory_service`.
18–19-year-olds who are not serving use the 20–24 pattern.

## Calibration

The religiosity (or religion) margins are reproduced exactly; the education margins up to a
totals adjustment.

## Validation

Ages 25–64 in the model: 87% of secular men and 86% of secular women are employed; Haredi men
49%, Haredi women 78%; Muslim men 72%, Muslim women 48%; Druze men 86%, Druze women 58%. Over
all adults: 64% employed, 3.5% in compulsory service, 14% retired. Survey comparisons are in the
generated table below.

## Limitations

* "Retired" is defined by age, not by a pension or a question; people under 65 who retired
  early are "not in the labour force".
* Yeshiva and kollel students are "not in the labour force"; the model does not say why a
  person is not working.
* The three-way pattern religiosity × education × status is inferred, not observed.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `labour_status` — Labour-force status / מצב בכוח העבודה

- **type:** `table`
- **parents:** `in_service`, `group`, `religiosity`, `sex`, `age_band`, `education`
- **back-off order:** `religiosity` → `education` → `group` → `sex` → `age_band`
- **distribution file:** `model/cpts/labour_status.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `employed` | employed | מועסק | מועסקת |
| `unemployed` | unemployed (looking for work) | מובטל (מחפש עבודה) | מובטלת (מחפשת עבודה) |
| `not_in_labour_force` | not working and not looking for work | אינו עובד ואינו מחפש עבודה | אינה עובדת ואינה מחפשת עבודה |
| `retired` | retired | פנסיונר | פנסיונרית |
| `compulsory_service` | in compulsory military or national service | בשירות חובה צבאי או לאומי |  |

Sources: [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Labour-force status of Jews by religiosity and sex (20+) | [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) | 0.0109 | 0.0000 | 0.03 | ✅ pass |
| Labour-force status of Arabs by religion and sex (20+) | [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) | 0.0145 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: compulsory or national service only at ages 18-20 | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: retirees are 65 or older | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: an occupation only for the employed and retirees | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: every employed person has an occupation | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: earnings exactly for the employed | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people in compulsory service are not counted as students | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
