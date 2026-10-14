# Military or national service

<!-- he-summary -->
**שירות צבאי או לאומי** — שירת בצה"ל, עשה שירות לאומי-אזרחי, או לא שירת — לפי קבוצת אוכלוסייה, דתיות או דת, מין, גיל ויבשת לידה, מתוך הסקר החברתי 2024. גברים בני 18–20 ונשים בנות 18–19 שמסלולם צה"ל נחשבים משרתים כעת בשירות חובה; בשירות לאומי — בני 18–19.
<!-- /he-summary -->

## Definition

* **`military_service`**: `idf` — served (or is serving) in the IDF; `national_service` — did
  not serve in the IDF but did national or civic service (Sherut Leumi); `none` — neither.
* **`in_service`** (hidden): currently in compulsory service — `idf` for men aged 18–20 and
  women aged 18–19 whose service is `idf`; `national_service` for 18–19-year-olds whose service
  is national service; otherwise `no`. People in service get the labour-force status
  `compulsory_service`.

## Why these parents

`group` (Druze and Circassian men are conscripted; Muslim and Christian Arabs are exempt);
`religiosity` (most Haredi men defer service for yeshiva study; religious women mostly do
national service instead); `sex`; `age_band` (service patterns changed across cohorts);
`birth_region` (immigrants who arrived as adults rarely served).

## Sources

* `src:cbs_social_survey_2024` — IDF service (`military_*`) and national service
  (`national_service_*`) by religiosity × sex × age for Jews, sex × age for "others", religion ×
  sex × age for Arabs outside the Jerusalem district, and by continent of birth × sex × age for
  Jews (`*_by_birth_jews`). Ages 20+.

## Preprocessing

* The survey asks about national service **only those who did not serve in the IDF** (verified:
  the national-service question is "not relevant" exactly for IDF veterans). So the three
  categories are: IDF = served; national service = did not serve, did national service;
  none = the rest.
* The IDF question was **not asked of Muslims** and of about half of Arab Christians; those not
  asked are treated as not having served in the IDF (Bedouin and Christian volunteers are
  therefore missing from the data).

## Estimation

As for education: each table is shrunk toward its main-effects fit (10 pseudo-respondents) and
smoothed over ages 45–64; for Jews and "others" the religiosity and continent-of-birth tables are
combined by IPF over the model's own population counts of religiosity × continent of birth
(`combine()`, see the education page). Arab rows come from the religion table. 18–19-year-olds
use the 20–24 pattern, which includes people currently serving.

`in_service` is deterministic given age, sex and `military_service`.

## Calibration

The religiosity margins are reproduced exactly; the birthplace margins up to a totals
adjustment.

## Validation

Ages 20–44 in the model: IDF service for 87% of secular men and 85% of secular women; 85% of
Dati men and 21% of Dati women (54% of whom did national service); 13% of Haredi men and 4% of
Haredi women. Ages 20+: 68% of Druze men served in the IDF; among "others" (mostly
former-Soviet immigrants, many of whom arrived as adults), 37% of men and 17% of women. Survey
comparisons are in the generated table below.

## Limitations

* Being "in service" is approximated from age: deferrals, pre-army programmes (mechina, service
  year) and the longer service of some men are ignored, and 18-year-olds who have not yet been
  drafted are counted as serving.
* Reserve duty is not modelled.
* Volunteers among Muslim and Christian Arabs are not captured (see Preprocessing).
* The IDF figure for ages 20–24 includes people still serving at the time of the survey.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `military_service` — Military or national service / שירות צבאי או לאומי

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `birth_region`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/military_service.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `idf` | served in the IDF | שירת בצה"ל | שירתה בצה"ל |
| `national_service` | did national or civic service | עשה שירות לאומי-אזרחי | עשתה שירות לאומי-אזרחי |
| `none` | did not serve | לא שירת | לא שירתה |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Military/national service of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0161 | 0.0000 | 0.03 | ✅ pass |
| Military/national service of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0451 | 0.0000 | 0.04 | ✅ pass |
| Military/national service of Jews by continent of birth and sex (20+) | `cbs_social_survey_2024` | 0.0400 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| Constraint: people in service have the matching service history | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `in_service` — Currently in compulsory service / בשירות חובה כעת

- **type:** `table` · hidden helper
- **parents:** `age`, `sex`, `military_service`
- **back-off order:** `age` → `sex` → `military_service`
- **distribution file:** `model/cpts/in_service.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `no` | no | לא |  |
| `idf` | serving in the IDF | משרת בצה"ל | משרתת בצה"ל |
| `national_service` | in national service | בשירות לאומי |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| Constraint: compulsory or national service only at ages 18-20 | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people in service have the matching service history | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
