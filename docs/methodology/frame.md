# Population frame: place of residence, population group, sex and age

<!-- he-summary -->
**מסגרת האוכלוסייה** היא נקודת המוצא של כל אדם: יישוב מגורים, קבוצת אוכלוסייה (יהודים, מוסלמים, נוצרים ערבים, דרוזים, ואחרים — בעיקר עולים ובני משפחותיהם שאינם רשומים כיהודים), מין וקבוצת גיל. היא נבנית מקובץ היישובים של הלמ"ס (סוף 2024), מקובץ הרשויות המקומיות (הרכב דתות, גילים ומין לכל רשות) ומלוח האוכלוסייה של השנתון הסטטיסטי לפי דת, מין וגיל. תושבי מזרח ירושלים ורמת הגולן שאינם אזרחים מוצאים בעזרת פנקס הבוחרים של 2022, ושבטי הבדואים בפזורה מתווספים לפי מספר בעלי זכות הבחירה. התוצאה: כ-6.45 מיליון אזרחים בני 18+ ב-1,239 יישובים.
<!-- /he-summary -->

## Definition

The frame is the root of the model: a joint table of the number of **eligible citizens**
(Israeli citizens aged 18+ living in Israel) by

* `locality` — 1,239 CBS localities (cities, local councils, kibbutzim, moshavim, community
  settlements, Arab towns and villages, Bedouin towns and tribe localities), each with district,
  sub-district, type, socio-economic cluster, peripherality cluster and coordinates;
* `group` — registered population group/religion: `jewish`, `muslim`, `christian_arab`, `druze`,
  and `other` (not registered as Jewish or Arab: mostly immigrants under the Law of Return and
  their families from the former Soviet Union, plus non-Arab Christians);
* `sex` — `male`, `female`;
* `age_band` — 18–19, 20–24, …, 80–84, 85+.

Derived from it deterministically: `district`, `locality_type`, and `sector` (Muslims living in
Bedouin localities are shown as Bedouin, those in Kafr Kama and Rehaniya as Circassian). The
single-year `age` is drawn within the band from the national single-year age profile of the
person's group and sex.

## Why these parents

The frame has no parents. Locality, group, sex and age are the four attributes that official
statistics publish for (almost) the whole population, so they are fixed first and every other
node conditions on some of them. Age and sex are needed jointly with group because the groups
have very different age structures (the median Muslim citizen is much younger than the median
"other"), and locality because most later attributes vary strongly by place.

## Sources

* `src:cbs_localities_2024` — population of every locality at the end of 2024, split into
  "Jews and others" and "Arabs" (foreign nationals excluded), with locality type, district,
  local authority and coordinates.
* `src:cbs_local_authorities_2024` — for each of the 257 local authorities: the share of Jews
  among "Jews and others"; the shares of Muslims, Christians and Druze among Arabs; the age
  distribution (0–4, 5–9, 10–14, 15–19, 20–29, 30–44, 45–59, 60–64, 65+); men and women; and
  the socio-economic and peripherality clusters.
* `src:cbs_abstract_2025_population` — Statistical Abstract 2025, table 2.3: Israelis by
  population group and religion, sex and single year of age (2024 average).
* `src:cec_knesset25` — 2022 voter roll by polling station, used for the citizenship
  adjustments and the Bedouin tribe localities.

## Preprocessing

* Locality coordinates (ITM, EPSG:2039, encoded as 6+6 digits) are converted to WGS84
  latitude/longitude with `pyproj`.
* Single-year national profiles are built for each group and sex; open-ended bands (e.g. 95+)
  are spread over ages up to 100 with a geometric decline. "Others" = "Jews and others" minus
  Jews.
* Local-authority percentages that are missing are treated as unknown and the national
  profile is used for that authority.
* **Bedouin and Circassian localities** are identified from the CBS locality type (Bedouin
  "tribe" localities), membership of the Al-Kasom and Neve Midbar regional councils, and a
  documented list of Negev Bedouin towns, Galilee Bedouin villages and the two Circassian
  villages (`data/manual/localities/sector_localities.csv`).

## Estimation

1. **Group split per locality.** Jews = "Jews and others" × the authority's share of Jews;
   others = the remainder. Arabs are split into Muslims, Arab Christians and Druze with the
   authority's shares (localities inside a regional council share the council's shares).
2. **Age-sex structure per authority and group** by IPF on a table
   group × sex × single year of age. Seed: each group's national single-year profile × the
   authority's group totals. Margins: the authority's group totals, its age-group totals
   (age-group shares × population) and its totals of men and women. The fitted table gives
   P(sex, age | authority, group); every locality in the authority uses it.
3. Each locality's group totals are multiplied by these profiles and aggregated into the frame's
   adult age bands (ages under 18 are dropped).
4. **Citizenship adjustments** (see below) and **Bedouin tribe localities** are applied.

## Calibration

* **East Jerusalem**: CBS's 401,426 Arab residents of Jerusalem are mostly permanent
  residents. Adult Arab *citizens* are estimated from the 2022 roll: the eligible voters in the
  27 Jerusalem polling stations where Arab parties won a majority (16,450), divided by the share
  of Jerusalem's Arab-party votes cast in those stations. Jerusalem's Muslim and Christian adults
  are scaled down to this total (≈ 28,500), keeping their age-sex structure.
* **Golan Druze villages**: adult Druze in Majdal Shams, Mas'ade, Buq'ata and Ein Qiniyye are set
  to their eligible voters in 2022 (1,338; 461; 749; 207).
* **Bedouin tribe localities** (CBS publishes no population for them): adults = eligible voters
  in 2022, with the adult age-sex profile of Muslims in the Bedouin regional councils.

The result: 6.45 million eligible citizens. As a cross-check, the 2022 roll (6.79 million,
including citizens abroad) grown by ~3% to 2024 and minus 0.5–0.6 million citizens abroad gives
6.4–6.5 million.

## Validation

Group totals of the frame compared with the national adults in table 2.3 (2024 average):
Jews 1.013 (the frame is end-2024, the table an annual average); Muslims 0.82 and Arab
Christians 0.97 (East Jerusalem non-citizens removed); Druze 0.87 (Golan non-citizens
removed); others 1.04. Automated checks appear below once `popsim validate` has run.

## Limitations

* Localities inside a regional council share the council's religion shares and age profile
  (a kibbutz and a Bedouin village in the same council are distinguished only by the
  locality's "Jews and others"/"Arabs" counts).
* Non-citizen "others" (e.g. some spouses with residency status) are not removed — no data.
* East Jerusalem Arab citizens are estimated from 2022 polling stations; naturalisations since
  then (a few thousand) are not included.
* Bedouin tribe localities use 2022 eligible voters (no growth to 2024).
* The reference date is the end of 2024; growth since then is not modelled.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `frame` — Population frame / מסגרת האוכלוסייה

- **type:** `frame`
- **frame variable** `locality` (Place of residence): 1239 values
- **frame variable** `group` (Population group (registered religion)): 5 values
- **frame variable** `sex` (Sex): 2 values
- **frame variable** `age_band` (Age group): 15 values
- **distribution file:** `model/frame.csv`

Sources: `cbs_localities_2024` (Central Bureau of Statistics (CBS)); `cbs_local_authorities_2024` (Central Bureau of Statistics (CBS)); `cbs_abstract_2025_population` (Central Bureau of Statistics (CBS)); `cec_knesset25` (Central Elections Committee (CEC))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Age composition of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0188 | 0.0000 | 0.03 | ✅ pass |
| Age composition of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0901 | 0.0075 | 0.03 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `district` — District / מחוז

- **type:** `lookup`
- **parents:** `locality`
- **distribution file:** `model/lookups/district.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `jerusalem` | Jerusalem District | מחוז ירושלים |  |
| `north` | Northern District | מחוז הצפון |  |
| `haifa` | Haifa District | מחוז חיפה |  |
| `center` | Central District | מחוז המרכז |  |
| `tel_aviv` | Tel Aviv District | מחוז תל אביב |  |
| `south` | Southern District | מחוז הדרום |  |
| `judea_samaria` | Judea and Samaria (West Bank) | אזור יהודה ושומרון |  |

Sources: `cbs_localities_2024` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `locality_type` — Type of locality / סוג יישוב

- **type:** `lookup`
- **parents:** `locality`
- **distribution file:** `model/lookups/locality_type.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `large_city` | city of 100,000+ | עיר של 100,000 תושבים ומעלה |  |
| `city` | city of 20,000-100,000 | עיר של 20,000-100,000 תושבים |  |
| `town` | small town | עיירה |  |
| `arab_city` | Arab city | עיר ערבית |  |
| `arab_town` | Arab town or village | יישוב ערבי |  |
| `moshav` | moshav | מושב |  |
| `kibbutz` | kibbutz | קיבוץ |  |
| `community` | community settlement | יישוב קהילתי |  |
| `bedouin_tribe` | Bedouin tribe (unrecognised or dispersed locality) | שבט בדואי (פזורה) |  |
| `rural_other` | other rural locality | יישוב כפרי אחר |  |
| `other` | other | אחר |  |

Sources: `cbs_localities_2024` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `sector` — Sector / מגזר

- **type:** `table`
- **parents:** `group`, `locality`
- **back-off order:** `locality`
- **distribution file:** `model/cpts/sector.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `jewish` | Jewish | יהודי | יהודייה |
| `arab_muslim` | Arab Muslim | ערבי מוסלמי | ערבייה מוסלמית |
| `bedouin` | Bedouin | בדואי | בדואית |
| `circassian` | Circassian | צ'רקסי | צ'רקסית |
| `arab_christian` | Arab Christian | ערבי נוצרי | ערבייה נוצרייה |
| `druze` | Druze | דרוזי | דרוזית |
| `other` | not registered as Jewish or Arab | לא רשום כיהודי או כערבי | לא רשומה כיהודייה או כערבייה |

Sources: `cbs_localities_2024` (Central Bureau of Statistics (CBS))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `age` — Age / גיל

- **type:** `table`
- **parents:** `group`, `sex`, `age_band`
- **distribution file:** `model/cpts/age.csv`
- **categories:** 83 (see the domain file)

Sources: `cbs_abstract_2025_population` (Central Bureau of Statistics (CBS))

Validation:

_No automated validation checks cover this node yet._

<!-- END GENERATED -->
