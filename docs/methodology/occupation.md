# Occupation, industry and status at work

<!-- he-summary -->
**משלח יד, ענף ומעמד בעבודה.** למועסקים — משלח היד (תשע קבוצות ראשיות של הלמ"ס), הענף הכלכלי ומעמד בעבודה (שכיר, עצמאי, מנהל חברה בבעלותו). לפנסיונרים נקבעים משלח היד והענף שבהם עבדו, לפי ההתפלגות של מועסקים בעלי אותם מאפיינים. משלח היד תלוי בדתיות או בדת, במין ובהשכלה; הענף ומעמד בעבודה — במשלח היד ובמין, בנפרד ליהודים ואחרים ולערבים.
<!-- /he-summary -->

## Definition

* **`occupation`** — major group of the CBS classification of occupations (2011, based on
  ISCO-08): managers; academic professionals; practical engineers, technicians, agents and
  associate professionals; clerical workers; sales and service workers; skilled workers in
  agriculture, industry, construction and other trades; unskilled workers. For **retirees**
  this is their last occupation; for everyone else who is not employed, `none`.
* **`industry`** — the CBS 2011 classification of economic activity, at section level, with
  electricity and water supply merged, and arts and "other services" merged (18 groups).
  Retirees: the industry of their last job.
* **`work_status`** — status at work of the employed: employee, self-employed, owner-manager of
  a company, unpaid worker in a family business. Kibbutz members (a separate CBS category) are
  counted as employees, because the model does not tie them to kibbutzim.

## Why these parents

* Occupation ← `labour_status` (only the employed and retirees have one), `group` and
  `religiosity`, `sex`, `education` (the strongest single predictor).
* Industry ← `occupation`, `sex`, `group` (separately for Jews-and-others and for Arabs).
* Status at work ← `labour_status`, `occupation`, `sex`, `group`.

## Sources

* `src:cbs_social_survey_2024` — occupation by religiosity × sex × diploma for Jews
  (`occupation_jews`), sex × diploma for "others", religion × sex × diploma for Arabs outside the
  Jerusalem district (`occupation_arabs`); industry and status at work by occupation × sex, for
  Jews-and-others and for Arabs (`industry_by_occupation_*`, `work_status_by_occupation_*`).
  Employed persons aged 20+.

## Preprocessing

"Occupation unknown" (code 10) and unknown industry/status are dropped.

## Estimation

* Occupation: rows religiosity (or religion) × diploma within each sex, shrunk toward their
  main-effects fit with 10 pseudo-respondents ("others" join the Jewish table as one more
  religiosity level). The same distribution is used for employed people of every age and for
  retirees (their former occupation).
* Industry: rows occupation × sex, shrunk toward their main-effects fit, separately for the two
  population groups.
* Status at work: likewise.

## Calibration

None; the survey is the target.

## Validation

Employed Jews in the model: academic professionals 36%, technicians and associate
professionals 17%, sales and services 18%, managers 9%; employed Muslims: skilled workers 30%,
sales and services 26%, academic professionals 20%, unskilled 11%. Self-employed or company
owners: 17% of employed Jews and 17% of employed Arabs. Largest industries overall: health and
welfare, education, manufacturing, trade. Survey comparisons are in the generated table below.

## Limitations

* Retirees' former occupations follow today's occupational structure for people with their
  education and religiosity; past occupational structures (more industrial work, fewer
  academic professions) are not modelled beyond what education captures.
* Occupation does not depend on age or locality given education (e.g. no higher share of
  managers among older workers, no regional labour markets); industry does not depend on
  locality.
* Arab rows depend on religion, not religiosity.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `occupation` — Occupation (current, or last one for retirees) / משלח יד (נוכחי, או האחרון לפנסיונרים)

- **type:** `table`
- **parents:** `labour_status`, `group`, `religiosity`, `sex`, `education`
- **back-off order:** `religiosity` → `education` → `sex` → `group` → `labour_status`
- **distribution file:** `model/cpts/occupation.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `managers` | manager | מנהל | מנהלת |
| `professionals` | academic professional | בעל משלח יד אקדמי | בעלת משלח יד אקדמי |
| `technicians` | technician or associate professional | הנדסאי, טכנאי או בעל מקצוע נלווה | הנדסאית, טכנאית או בעלת מקצוע נלווה |
| `clerical` | clerical worker | פקיד או עובד משרד | פקידה או עובדת משרד |
| `sales_services` | sales or service worker | עובד מכירות ושירותים | עובדת מכירות ושירותים |
| `skilled_workers` | skilled worker (industry, construction, agriculture) | עובד מקצועי בתעשייה, בבינוי או בחקלאות | עובדת מקצועית בתעשייה, בבינוי או בחקלאות |
| `unskilled` | unskilled worker | עובד לא מקצועי | עובדת לא מקצועית |
| `none` | none | אין |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Occupation of employed Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0098 | 0.0000 | 0.03 | ✅ pass |
| Occupation of employed Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0042 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: an occupation only for the employed and retirees | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: every employed person has an occupation | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: an industry exactly when there is an occupation | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `industry` — Industry (current, or last one for retirees) / ענף כלכלי (נוכחי, או האחרון לפנסיונרים)

- **type:** `table`
- **parents:** `occupation`, `sex`, `group`
- **back-off order:** `group` → `sex`
- **distribution file:** `model/cpts/industry.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `agriculture` | agriculture | חקלאות |  |
| `manufacturing` | manufacturing and mining | תעשייה וכרייה |  |
| `utilities` | electricity and water utilities | אספקת חשמל ומים |  |
| `construction` | construction | בינוי |  |
| `trade` | wholesale and retail trade | מסחר סיטוני וקמעוני |  |
| `transport` | transport and storage | תחבורה ואחסנה |  |
| `hospitality` | accommodation and food services | שירותי אירוח ואוכל |  |
| `ict` | information and communication | מידע ותקשורת |  |
| `finance` | finance and insurance | פיננסים וביטוח |  |
| `real_estate` | real estate | נדל"ן |  |
| `professional` | professional, scientific and technical services | שירותים מקצועיים, מדעיים וטכניים |  |
| `admin_support` | administrative and support services | שירותי ניהול ותמיכה |  |
| `public_admin` | public administration and defence | מינהל ציבורי וביטחון |  |
| `education` | education | חינוך |  |
| `health_welfare` | health and welfare | בריאות ורווחה |  |
| `arts_other` | arts, entertainment and other services | אמנות, בידור ושירותים אחרים |  |
| `households` | private households as employers | משקי בית כמעסיקים |  |
| `extraterritorial` | international organisations | ארגונים בין-לאומיים |  |
| `none` | none | אין |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: an industry exactly when there is an occupation | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `work_status` — Status at work / מעמד בעבודה

- **type:** `table`
- **parents:** `labour_status`, `occupation`, `sex`, `group`
- **back-off order:** `occupation` → `sex` → `group` → `labour_status`
- **distribution file:** `model/cpts/work_status.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `employee` | employee | שכיר | שכירה |
| `self_employed` | self-employed | עצמאי | עצמאית |
| `company_owner` | owner-manager of a company | מנהל חברה בבעלותו | מנהלת חברה בבעלותה |
| `unpaid_family` | unpaid worker in a family business | עובד ללא שכר בעסק משפחתי | עובדת ללא שכר בעסק משפחתי |
| `none` | not applicable | לא רלוונטי |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
