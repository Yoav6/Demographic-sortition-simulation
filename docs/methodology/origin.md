# Origin, generation and ancestry

<!-- he-summary -->
**מוצא.** לכל יהודי (ולמי שאינו רשום כיהודי או כערבי) נקבעים ארץ מוצא ודור בישראל, לפי הגדרת הלמ"ס: עולים — לפי ארץ הלידה; ילידי ישראל — לפי ארץ הלידה של האב; ילידי ישראל שאביהם יליד ישראל — "דור שלישי". ההתפלגות לפי גיל מבוססת על לוח הלמ"ס של יהודים לפי ארץ מוצא וגיל (2020, מקודם בארבע שנים), הקשר לדתיות — על הסקר הלאומי של הבחירות 2022, והריכוז הגאוגרפי של עולי ברית המועצות לשעבר — על שיעור עולי 1990 ואילך ברשות המקומית. לבני דור שלישי נקבע גם מוצא עדתי לפי הגדרה עצמית (אשכנזי, מזרחי, מעורב, "ישראלי"). ערבים ודרוזים מסומנים "ילידים".
<!-- /he-summary -->

## Definition

**Origin** (`origin`) follows the CBS definition for Jews and "others":

* an **immigrant** is classified by own country of birth (`morocco_immigrant`, `fsu_immigrant`, …);
* an **Israeli-born** person by the father's country of birth (`morocco_second_gen`, …);
* an Israeli-born person whose father was also born in Israel is **third generation or more**
  (`israel_3gen`).

Countries are grouped into the 25 origins CBS tabulates separately (the former USSR; Morocco,
Iraq, Iran, Yemen, Ethiopia, Tunisia/Algeria, Libya, Egypt, Turkey, India, Syria/Lebanon, other
Asia, other Africa; Poland, Romania, Bulgaria/Greece, Germany/Austria, Czechia/Slovakia/Hungary,
France, the UK, other Europe, North America, Argentina, other Latin America). Muslims, Arab
Christians and Druze get `native` (no origin attribute).

Derived from origin:

* **`generation`** (lookup): immigrant / second generation / third generation or more / native.
* **`birth_region`** (lookup, hidden): continent of birth as CBS groups it — Israel (second and
  third generation, Arabs and Druze), Europe-America (including the former USSR), Asia,
  Africa. It is a parent of education and military service, which the Social Survey
  tabulates by continent of birth.
* **`ancestry`** (third generation only): self-identified Ashkenazi, Mizrahi or Sephardi, mixed,
  or "simply Israeli" — the question Israelis are asked when the official origin no longer says
  anything (INES). Everyone else gets `not_applicable`, since their origin country is shown.

**`immigrant_bucket`** (lookup, hidden) is a property of the locality: the share of residents
who immigrated in 1990 or later in its local authority (< 5%, 5–10, 10–20, 20–30, 30%+).

## Why these parents

* `group` — only Jews and "others" have an origin.
* `age_band` — immigration came in waves (North Africa and Iraq in the 1950s, the former USSR in
  the 1990s, Ethiopia in 1984–91), so origin and generation depend strongly on birth year.
* `religiosity` — origin and religiosity are associated (Jews of Asian and North African origin
  are more often traditional; former-Soviet immigrants mostly secular).
* `immigrant_bucket` — former-Soviet immigrants are concentrated in particular towns (Ashdod,
  Ashkelon, Haifa, Nazareth Illit/Nof HaGalil, Ma'alot-Tarshiha...). It lets the locality
  shape origin without a full locality × origin table, which CBS does not publish.

## Sources

* `src:cbs_abstract_2021_origin` — Statistical Abstract 2021, table 2.8: Jews by country of
  origin, generation and age group (2020 average). The last edition with the country-level
  breakdown.
* `src:cbs_abstract_2025_population` — the frame's Jewish adults by sex and age.
* `src:ines_2022` — Israel National Election Studies 2022: own and father's birthplace by
  religiosity; third-generation respondents' ethnic self-identification.
* `src:cbs_local_authorities_2024` — share of 1990+ immigrants by local authority.

## Preprocessing

* **Ageing the 2020 table to the end of 2024.** Each age group's count is spread evenly over its
  single years (the open top group with a geometric decline of 15% a year) and shifted four
  years older, then summed into the frame's age bands. This ignores deaths and immigration
  since 2020 (see Limitations).
* **INES birthplaces** (own and father's) are mapped to four continent groups: Asia-Africa,
  Europe-America, former USSR, and Israel (third generation). Respondents are weighted with
  the panel weights.
* **Immigrant buckets**: localities without a local-authority figure (e.g. small localities
  inside regional councils without the item) fall into the lowest bucket.

## Estimation

For Jews, one iterative proportional fitting (IPF) over age band × religiosity × immigrant
bucket × continent group × "former-Soviet immigrant" flag × origin, with four margins:

1. the frame's Jewish adults by age band, religiosity and bucket (frame × religiosity table);
2. CBS origin by age band (aged as above), scaled to the frame's Jewish adults;
3. INES religiosity × continent group, itself raked to the model's religiosity totals and the
   CBS continent-group totals (keeping INES's association, not its levels);
4. former-Soviet immigrants by bucket, proportional to each bucket's adults × its average share
   of 1990+ immigrants, scaled to the national number of former-Soviet immigrants.

The fitted table gives P(origin | age band, religiosity, bucket). Cells with no population fall
back to the national P(origin | age band).

**Others** (not registered as Jews or Arabs — mostly immigrants from the former USSR under the
Law of Return and their children) are former-Soviet immigrants or Israeli-born of former-Soviet
origin, split by age band in the same proportion as former-Soviet-origin Jews.

**Ancestry.** For third-generation INES respondents, by religiosity, shrunk toward the overall
third-generation mix with 15 pseudo-respondents.

## Calibration

National origin by age band reproduces the aged CBS table by construction (margin 2), and the
religiosity totals of the religiosity node by construction (margin 1).

## Validation

National mix of Jewish adults (model): third generation 37.9%, former-Soviet immigrants 11.6%,
Israeli-born of Moroccan origin 6.5%, Israeli-born of former-Soviet origin 3.9%, Israeli-born of
Iraqi origin 3.1%, Moroccan-born 2.6%. Born abroad: about 4% of Jews aged 18–24 and 86% of
those aged 75+. Education and military service by continent of birth are checked against the
Social Survey (see those pages).

## Limitations

* The country table is from 2020 and aged mechanically: it misses deaths since 2020 (immigrant
  cohorts are older, so they are slightly overstated) and the 2022–2024 immigration from Russia
  and Ukraine (tens of thousands of adults, mostly in the "former USSR" origin).
* Only former-Soviet immigrants are placed geographically (through the bucket). Other origins
  (e.g. Ethiopian Israelis, concentrated in particular towns) follow the national pattern given
  age and religiosity.
* The INES association between religiosity and origin rests on about 1,200 Jewish
  respondents, grouped into four continent groups.
* "Others" are all assigned former-Soviet origin; the few from other countries are not modelled.
* Self-identified ancestry is asked only of third-generation Israelis, as in INES.

## Changelog

* 2026.10.0 — first version. Fixed the Hebrew "from India" label (מהודו).

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `immigrant_bucket` — Share of 1990+ immigrants in the locality / שיעור עולי 1990 ואילך ביישוב

- **type:** `lookup` · hidden helper
- **parents:** `locality`
- **distribution file:** `model/lookups/immigrant_bucket.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `imm_lt5` | imm_lt5 | imm_lt5 |  |
| `imm_5_10` | imm_5_10 | imm_5_10 |  |
| `imm_10_20` | imm_10_20 | imm_10_20 |  |
| `imm_20_30` | imm_20_30 | imm_20_30 |  |
| `imm_30plus` | imm_30plus | imm_30plus |  |

Sources: `cbs_local_authorities_2024` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `origin` — Origin / מוצא

- **type:** `table`
- **parents:** `group`, `age_band`, `religiosity`, `immigrant_bucket`
- **back-off order:** `immigrant_bucket` → `religiosity` → `age_band`
- **distribution file:** `model/cpts/origin.csv`
- **categories:** 52 (see the domain file)

Sources: `cbs_abstract_2021_origin` (Central Bureau of Statistics (CBS)); `cbs_abstract_2025_population` (Central Bureau of Statistics (CBS)); `ines_2022` (Israel National Election Studies, Tel Aviv University); `cbs_local_authorities_2024` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `generation` — Generation in Israel / דור בישראל

- **type:** `lookup`
- **parents:** `origin`
- **distribution file:** `model/lookups/generation.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `immigrant` | Immigrant (born abroad) | עולה (יליד חו"ל) | עולה (ילידת חו"ל) |
| `second_gen` | Second generation (Israeli-born to an immigrant father) | דור שני בישראל |  |
| `third_gen` | Third generation or more | דור שלישי ומעלה בישראל |  |
| `native` | Native (Arab or Druze citizen) | ילידי (אזרח ערבי או דרוזי) | ילידית (אזרחית ערבייה או דרוזית) |

Sources: `cbs_abstract_2021_origin` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `ancestry` — Ancestry (self-identified, third generation) / מוצא עדתי (הגדרה עצמית, דור שלישי)

- **type:** `table`
- **parents:** `origin`, `religiosity`
- **back-off order:** `religiosity` → `origin`
- **distribution file:** `model/cpts/ancestry.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `ashkenazi` | of Ashkenazi descent | ממוצא אשכנזי |  |
| `mizrahi` | of Mizrahi or Sephardi descent | ממוצא מזרחי או ספרדי |  |
| `mixed` | of mixed Ashkenazi and Mizrahi descent | ממוצא מעורב, אשכנזי ומזרחי |  |
| `israeli_only` | identifying simply as Israeli | המגדיר את עצמו פשוט ישראלי | המגדירה את עצמה פשוט ישראלית |
| `not_applicable` | not applicable | לא רלוונטי |  |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `birth_region` — Continent of birth / יבשת לידה

- **type:** `lookup` · hidden helper
- **parents:** `origin`
- **distribution file:** `model/lookups/birth_region.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `israel` | Israel | ישראל |  |
| `europe_america` | Europe or the Americas | אירופה או אמריקה |  |
| `asia` | Asia | אסיה |  |
| `africa` | Africa | אפריקה |  |

Sources: `cbs_abstract_2021_origin` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Highest diploma of Jews by continent of birth and sex (20+) | `cbs_social_survey_2024` | 0.0208 | 0.0000 | 0.03 | ✅ pass |
| Military/national service of Jews by continent of birth and sex (20+) | `cbs_social_survey_2024` | 0.0400 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
