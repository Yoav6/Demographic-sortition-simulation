# Current studies

<!-- he-summary -->
**לימודים כיום.** האם האדם לומד כיום ובאיזו מסגרת: תואר ראשון, תואר שני או שלישי, ישיבה או כולל (לנשים: מדרשה), מוסד על-תיכוני (כגון הנדסאות או סמינר) או קורסים ומסגרות אחרות. ההסתברות ללמוד נלקחת מהסקר החברתי 2024 של הלמ"ס ("לומד כיום"), לפי דתיות או דת, מין, גיל, מצב בכוח העבודה ותעודה גבוהה ביותר. החלוקה בין סוגי המסגרות מותאמת למספרי הסטודנטים שמפרסמים הלמ"ס (לפי תואר, גיל, מין וקבוצת אוכלוסייה; תלמידי ישיבות וכוללים לפי גיל; תלמידי החינוך העל-תיכוני), המועצה להשכלה גבוהה (סטודנטים ערבים) והמכון הישראלי לדמוקרטיה (סטודנטים חרדים).
<!-- /he-summary -->

## Definition

**`studying`** — whether the person is studying now (including during vacations) and in what
framework:

* **not studying**;
* **a bachelor's degree** (universities, the Open University, academic colleges and colleges of
  education);
* **a master's degree or doctorate**;
* **a yeshiva or kollel** — for women, a midrasha (a women's college of Torah study);
* **a post-secondary institution** — practical engineering and technicians' courses, teachers'
  seminaries and other short-cycle tertiary programmes;
* **other courses** — anything else the survey counts as studying (vocational and evening
  courses, pre-academic preparatory programmes, and so on).

## Why these parents

Studying is above all a matter of age and population group: most students are in their
twenties, and most Haredi men study in a yeshiva or kollel well into adulthood. Labour status
matters because students work less (and because people in compulsory service are not counted
as students). The highest diploma decides what someone can study: a master's degree after a
bachelor's, a bachelor's mostly after matriculation.

## Sources

* `src:cbs_social_survey_2024` — "studied in the past / studies now, including vacations /
  never studied" (variable 1831) by religiosity, sex, age group and labour-force status for
  Jews, by sex, age and labour-force status for "others", by religion, sex, age and labour-force
  status for Arabs outside the Jerusalem district; and by highest diploma, sex and age group for
  Jews and others and for Arabs (`studying_*`). Ages 20+.
* `src:cbs_abstract_education` — Statistical Abstract tables: students by degree, 2024/25
  (4.31, 2025); their composition by age, sex and population group, 2022/23 (4.73, 2024);
  students as a share of the population aged 18–39 (4.70, 2024, for comparison); yeshiva and
  kollel students by type, age and citizenship, 2023/24 (4.17, 2025); post-secondary students
  by sex and age, 2023/24 (4.27, 2025).
* `src:che_arab_students_2024` — Council for Higher Education table 15: Arab students by degree
  and sex, 2023/24.
* `src:idi_haredi_report_2025` — Israel Democracy Institute: Haredi students in higher
  education, 2024/25 (15,812 bachelor's, 3,141 postgraduate), transcribed in
  `data/manual/students/`.

## Preprocessing

* Social Survey: "studies now, including vacations" counts as studying; "studied in the past"
  and "never studied" as not.
* Yeshiva students: Israeli citizens only (table 4.17 gives citizenship by type; each type's
  age distribution is scaled to its citizens). Men: kollels and higher yeshivas (175,800);
  women: midrashas (4,200). Hesder students are serving soldiers in the model
  (labour status "compulsory service") and are left out.
* Degree counts: the 2024/25 totals by degree (table 4.31), split by the 2022/23 composition by
  age and sex (table 4.73); Arab students from the CHE (2023/24), Haredi students from the IDI
  (2024/25). Master's and doctoral students form one category.

## Estimation

1. **Whether the person studies.** The Social Survey tables by religiosity (or religion), sex,
   age group and labour-force status are shrunk toward a main-effects fit as for the other
   Social Survey nodes (`by_population`, with labour-force status as an extra dimension;
   retirees count as "not in the labour force"). In every sex × age band, this is combined with
   the table by highest diploma over the model's own population counts (`common.combine`), so
   the probability depends on both. People in compulsory service do not study.
2. **What they study.** The model's students in every cell of population group × religiosity ×
   sex × age band × labour status × diploma are split between the five kinds of study by IPF to
   these counts: bachelor's students by age group, sex, Arabs, Arab women and Haredim; graduate
   students by age group, sex, Arabs and Haredim; yeshiva and kollel men by age group, midrasha
   women; post-secondary students by age group and sex. The seed allows only what the diploma,
   sex and religiosity allow: a bachelor's degree mostly after matriculation (one tenth as
   likely without it or after a first degree), a graduate degree after a first or second degree
   and not at 18–19, a yeshiva or kollel for Haredi men (some religious and traditional-religious
   men), a midrasha for religious women, post-secondary studies below a graduate degree. "Other
   courses" takes the students left over in each cell.
3. Outside the Jewish group, rows do not depend on religiosity and are written once.

## Calibration

The split is fitted to the published counts above (step 2).

## Validation

The model reproduces the Social Survey's share of people studying by religiosity (or religion)
and sex, and the published counts by kind of study, age, sex and population group (see the
generated table below). The model's students: about 215,000 bachelor's, 81,000 graduate,
164,000 yeshiva and kollel, 65,000 post-secondary and 173,000 in other courses. Among people
aged 20–34, 59% of Haredi men study in a yeshiva or kollel, and 12–16% of Jewish women and
13–15% of Arab women study for a bachelor's degree.

## Limitations

* The CBS counts of yeshiva students "up to 19" include 17-year-olds, who are outside the
  model; the model has 16,000 yeshiva students aged 18–19 against 27,000 in the count. Ages 20–24
  fall 10% short as well: the Social Survey's share of young Haredi men studying is lower than
  the yeshiva registers imply.
* The CBS student counts include non-citizens (a few thousand foreign and East Jerusalem
  students); the model's population is citizens.
* The Social Survey starts at age 20; 18–19-year-olds borrow the 20–24 pattern, and the student
  counts decide what they study.
* Haredi students in higher education are known only in total by degree, not by age or sex.
* "Other courses" is what remains of the survey's broad "studying now" after the counted
  frameworks; it is not measured directly.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `studying` — Current studies / לימודים כיום

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `labour_status`, `education`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/studying.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `none` | not studying | אינו לומד | אינה לומדת |
| `first_degree` | studying for a bachelor's degree | לומד לתואר ראשון | לומדת לתואר ראשון |
| `graduate` | studying for a master's degree or doctorate | לומד לתואר שני או שלישי | לומדת לתואר שני או שלישי |
| `yeshiva` | studying at a yeshiva or kollel | לומד בישיבה או בכולל | לומדת במדרשה |
| `post_secondary` | studying at a post-secondary institution (such as practical engineering or a teachers' seminary) | לומד במוסד על-תיכוני (כגון הנדסאות או סמינר) | לומדת במוסד על-תיכוני (כגון הנדסאות או סמינר) |
| `other` | taking other courses | לומד בקורסים או במסגרות אחרות | לומדת בקורסים או במסגרות אחרות |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey); `cbs_abstract_education` (Central Bureau of Statistics (CBS)); `che_arab_students_2024` (Council for Higher Education (CHE), Planning and Budgeting Committee); `idi_haredi_report_2025` (Israel Democracy Institute (Lee Cahaner, Gilad Malach))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Currently studying, Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0094 | 0.0000 | 0.03 | ✅ pass |
| Currently studying, Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0108 | 0.0000 | 0.04 | ✅ pass |
| Students by kind of study, age, sex and population group vs published counts (relative difference) | `cbs_abstract_education` | 0.1023 | — | 0.12 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people in compulsory service are not counted as students | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: graduate students already hold an academic degree | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: yeshiva, kollel and midrasha students are Jewish | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: a field of current studies exactly for students of an academic degree | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
