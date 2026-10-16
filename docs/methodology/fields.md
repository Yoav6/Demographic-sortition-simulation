# Fields of study

<!-- he-summary -->
**תחומי לימוד.** לבעלי תואר אקדמי — תחום הלימוד של התואר הגבוה ביותר (הסקר החברתי 2024 של הלמ"ס, לפי משלח יד ומין, לפי תעודה וגיל, ולפי דתיות או מגזר ומין). לסטודנטים לתואר — תחום הלימודים הנוכחי (המועצה להשכלה גבוהה, תשפ"ד, לפי תואר ומין). שנים-עשר תחומים, כמו בפרסומי המל"ג. תחום הלימודים של סטודנטים לתואר מתקדם קשור לתחום התואר שכבר יש להם: ההנחה היא ש-60% מהם לומדים באותו תחום.
<!-- /he-summary -->

## Definition

Twelve field groups, as the Council for Higher Education (CHE) publishes them: humanities and
arts; education and teaching; social sciences; business and management; law; medicine;
paramedical professions (nursing, therapies and the like); mathematics, statistics and computer
science; physical sciences; biological sciences; agriculture; engineering and architecture.

* **`degree_field`** — the field of the person's highest academic degree; "none" for people
  without an academic degree.
* **`study_field`** — the field of the academic degree the person is studying for now; "none"
  for people who are not studying for a bachelor's, master's or doctoral degree.

## Why these parents

The field of a degree is strongly tied to what people do: most managers with a degree studied
business or the social sciences, most technicians engineering. The model draws occupation first,
so the field is drawn to fit it. Fields have also shifted over time (computer science and the
paramedical professions are far more common among younger graduates, the humanities among
older ones), differ by sex (education and the paramedical professions are mostly women's fields,
engineering mostly men's) and by population group (most Haredi graduates studied education;
Arab graduates more often studied medicine and paramedical professions). A graduate student's
field is tied to the field of the degree they already hold.

## Sources

* [`src:cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) — field of the highest academic degree (variable 1905, asked of
  holders of a bachelor's, master's or doctoral degree) by occupation (including "not employed")
  and sex, by highest diploma and age group, by religiosity and sex for Jews, by religion and sex
  for Arabs and by sex for "others" (`field_*`). Ages 20+.
* [`src:che_fields_2024`](../../SOURCES.md#src-che_fields_2024) — CHE table 14: students by field, degree, type of institution and sex,
  2023/24 (universities and academic colleges, not the Open University).

## Preprocessing

* The Social Survey's fifteen fields are grouped into the CHE's twelve: general humanities,
  languages and literatures, and the arts become "humanities and arts". "Special and
  miscellaneous programmes" (about 1% of graduates) is dropped.
* The religiosity groups are those of the media surveys: secular (and "others"), traditional
  (including traditional-religious), religious, Haredi, Arab.
* CHE: master's and doctoral students form one "graduate" group.

## Estimation

* `degree_field`: each of the three Social Survey tables is shrunk toward a main-effects fit
  (as for the other Social Survey nodes). P(field | occupation, sex) is combined with
  P(field | diploma, age group), then the result with P(field | religiosity group, sex), each
  time over the model's own population of degree holders (`common.combine`). The table is then
  written over diploma × sex × occupation × the media surveys' age groups × religiosity group.
* `study_field`:
  * bachelor's students: the CHE field mix of bachelor's students of their sex;
  * graduate students: in each sex, the table of held degree field × study field is fitted by
    IPF to the model's graduate students by the field of their degree and to the CHE's graduate
    students by field. The seed makes staying in one's field more likely, with the strength
    chosen so that **60% of graduate students study in the field of their degree**. This is an
    assumption: no source publishes how many students change field between degrees.

## Calibration

`study_field` reproduces the CHE's field mix by degree and sex exactly; `degree_field`
reproduces the Social Survey tables up to the shrinkage.

## Validation

See the generated table below: the field of the highest degree by occupation and sex, and by
religiosity and sex for Jews, against the Social Survey; the field of current studies by degree
and sex against the CHE. In the model, 24% of women with a degree studied education and 27% of
men engineering; 60% of Haredi degree holders studied education; 15% of graduates aged 18–24
studied mathematics, statistics or computer science, against 2% of those aged 65+.

## Limitations

* Twelve field groups only: "economics" is part of the social sciences, "computer science" of
  mathematics, statistics and computer science.
* The field of a person's *first* degree is not modelled, only that of the highest one.
* The share of graduate students who stay in their field (60%) is assumed.
* Field of current studies does not depend on age or population group (the CHE does not publish
  it so), and Open University students follow the field mix of the other institutions.
* The Social Survey's occupation is the current one, so "not employed" includes retirees; the
  model gives retirees their former occupation and uses it for their field.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `degree_field` — Field of the highest academic degree / תחום הלימוד של התואר האקדמי הגבוה ביותר

- **type:** `table`
- **parents:** `education`, `sex`, `occupation`, `media_age`, `media_sector`
- **back-off order:** `media_sector` → `media_age` → `occupation` → `sex`
- **distribution file:** `model/cpts/degree_field.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `humanities` | humanities and arts | מדעי הרוח והאמנויות |  |
| `education` | education and teaching | חינוך והוראה |  |
| `social_sciences` | social sciences | מדעי החברה |  |
| `business` | business and management | מנהל עסקים וניהול |  |
| `law` | law | משפטים |  |
| `medicine` | medicine | רפואה |  |
| `paramedical` | paramedical professions (such as nursing or therapy) | מקצועות עזר רפואיים (כגון סיעוד או טיפול) |  |
| `math_cs` | mathematics, statistics and computer science | מתמטיקה, סטטיסטיקה ומדעי המחשב |  |
| `physical_sciences` | physical sciences | המדעים הפיזיקליים |  |
| `biological_sciences` | biological sciences | המדעים הביולוגיים |  |
| `agriculture` | agriculture | חקלאות |  |
| `engineering` | engineering and architecture | הנדסה ואדריכלות |  |
| `none` | none | אין |  |

Sources: [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Field of the highest degree by occupation and sex (20+) | [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) | 0.0096 | 0.0000 | 0.03 | ✅ pass |
| Field of the highest degree of Jews by religiosity and sex (20+) | [`cbs_social_survey_2024`](../../SOURCES.md#src-cbs_social_survey_2024) | 0.1155 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: a field of degree exactly for holders of an academic degree | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `study_field` — Field of current academic studies / תחום הלימודים האקדמיים כיום

- **type:** `table`
- **parents:** `studying`, `sex`, `degree_field`
- **back-off order:** `degree_field` → `sex`
- **distribution file:** `model/cpts/study_field.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `humanities` | humanities and arts | מדעי הרוח והאמנויות |  |
| `education` | education and teaching | חינוך והוראה |  |
| `social_sciences` | social sciences | מדעי החברה |  |
| `business` | business and management | מנהל עסקים וניהול |  |
| `law` | law | משפטים |  |
| `medicine` | medicine | רפואה |  |
| `paramedical` | paramedical professions (such as nursing or therapy) | מקצועות עזר רפואיים (כגון סיעוד או טיפול) |  |
| `math_cs` | mathematics, statistics and computer science | מתמטיקה, סטטיסטיקה ומדעי המחשב |  |
| `physical_sciences` | physical sciences | המדעים הפיזיקליים |  |
| `biological_sciences` | biological sciences | המדעים הביולוגיים |  |
| `agriculture` | agriculture | חקלאות |  |
| `engineering` | engineering and architecture | הנדסה ואדריכלות |  |
| `none` | none | אין |  |

Sources: [`che_fields_2024`](../../SOURCES.md#src-che_fields_2024) (Council for Higher Education (CHE), Planning and Budgeting Committee)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Field of current studies by degree and sex vs the Council for Higher Education | [`che_fields_2024`](../../SOURCES.md#src-che_fields_2024) | 0.0000 | — | 0.01 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: a field of current studies exactly for students of an academic degree | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
