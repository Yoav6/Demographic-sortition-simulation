# Literacy (adult skills)

<!-- he-summary -->
**מיומנות קריאה (משוערת).** במקום "מדד אינטליגנציה" — שאין לו נתונים ייצוגיים בישראל — המודל משתמש במיומנות הקריאה בסקר מיומנויות הבוגרים של ה-OECD (PIAAC 2022–2023): סולם 0–500 וחמש רמות מיומנות. הציון של כל אדם משוער כסכום של השפעות קבוצת האוכלוסייה (ערבים, חרדים, יהודים אחרים), הגיל, ההשכלה והמין, ועוד רעש אקראי — כך שהממוצעים במודל משחזרים את הממוצעים שפרסמו ה-OECD ובנק ישראל. זהו מדד למיומנויות, הרגיש לשפה ולאיכות החינוך, ולא מנת משכל. בגילאים מעל 65, שהסקר אינו מכסה, ההשפעה של הגיל מוחצנת (אקסטרפולציה).
<!-- /he-summary -->

## Definition

* **`literacy_level`** — literacy proficiency on the PIAAC scale: below level 1 (under 176
  points), level 1 (176–225), level 2 (226–275), level 3 (276–325), level 4 or 5 (326+). At level 1
  adults can understand short texts and find clearly indicated information; at levels 4–5 they can
  understand and evaluate long, dense texts (OECD descriptions).
* **`literacy_score`** — a score inside the level (0–500 scale), rounded to a point.
* **`literacy_percentile`** — the share of adult citizens in the model with a lower score.

This is the "intelligence indicator" of the project brief: there is no representative,
cross-sectional measure of intelligence for Israel, whereas PIAAC tests a representative sample
of adults. It measures **skills** — reading and understanding written information — which depend
on language, schooling and practice; it is **not** an IQ score. See
[decision 0003](../decisions/0003-skills-indicator-piaac.md).

## Why these parents

Population group (Arab, Haredi, other Jewish), age, education and sex are the characteristics by
which PIAAC results for Israel are published. Education and age matter most within groups;
the Arab–Jewish gap (62 points) is the largest in the OECD data for Israel.

## Sources

* `src:oecd_piaac_2023_tables` — OECD, Survey of Adult Skills 2023, annex tables for Israel (6,092
  adults aged 16–65, tested in Hebrew or Arabic): mean literacy 243.6 and standard deviation 60.5
  (Table A.2.1), proficiency levels (A.2.2), means by age group (A.2.4), by education for ages 25–65
  (A.2.5) and by gender (A.2.7); and the share of low performers by each.
* `src:boi_piaac_note_2024` — Bank of Israel policy note 2024.03, Figure 2b: mean literacy of
  non-Haredi Jews (261), Haredim (251) and Arabs (199), computed in the CBS research room
  (transcribed in `data/manual/piaac/`).

## Preprocessing

* Education: no diploma or primary → below upper secondary; secondary, matriculation, other
  diploma → upper secondary; post-secondary non-academic and academic degrees → tertiary (in the
  international classification, Israel's post-secondary non-academic diplomas are short-cycle
  tertiary).
* Age: the model's bands are grouped into PIAAC's (18–24 with 16–24, ..., 55–64 with 55–65).

## Estimation

1. **Mean score of each cell** (population group × age band × education × sex):
   `μ = base + group + age + education + sex`. The nine effects are fitted by least squares so
   that the model population's mean scores (citizens aged 18–64, weighted by the model's own
   counts) reproduce the 13 published means: 5 age groups, 3 education levels, 2 genders, 3
   population groups. All are matched within 1.2 points except non-Haredi Jews (model 256 vs
   261): PIAAC's population (residents aged 16–65) differs slightly from the model's.
2. **Spread within cells**: the national standard deviation (60.5) minus the part the effects
   explain leaves a within-cell standard deviation of about 51 points; scores within a cell are
   taken as normally distributed.
3. **Proficiency level** = probability mass of that normal distribution between the PIAAC
   cut-offs. The score is then drawn uniformly within the level, and the percentile ranks it
   among all adult citizens in the model.
4. **Ages over 65** (outside PIAAC): the decline of the age effect between 45–54 and 55–65 (net
   of education) is continued linearly to age 80 and held constant beyond.

## Calibration

The effects are calibrated to the published means (step 1).

## Validation

Checks against figures the model was **not** fitted to (ages 18–64, generated table below): the
national distribution over proficiency levels is within 3 points of the published one (e.g.
below level 1: model 13.1%, published 13.8%; level 4–5: 8.4% vs 7.3%); the share of low
performers by age group, education and gender is within 2 points in every group (e.g. ages
55–65: 54.5% vs 53.6%; below upper secondary: 72.0% vs 73.6%).

## Limitations

* A model of averages, not a measurement: two people with the same group, age, education and sex
  differ only by random noise. Combinations PIAAC does not publish (e.g. Haredi women with a
  degree) follow from the additive model.
* The scores of people over 65 are extrapolated.
* PIAAC skills depend on language and schooling and should not be read as innate ability.
* Only literacy is modelled; numeracy and adaptive problem solving are published too and could be
  added the same way.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `literacy_level` — Literacy proficiency (modelled; OECD adult-skills scale) / מיומנות קריאה (משוערת; סולם מיומנויות הבוגרים של ה-OECD)

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `education`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/literacy_level.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `below1` | below OECD level 1 | מתחת לרמת OECD 1 |  |
| `level1` | OECD level 1 | רמת OECD 1 |  |
| `level2` | OECD level 2 | רמת OECD 2 |  |
| `level3` | OECD level 3 | רמת OECD 3 |  |
| `level4_5` | OECD level 4 or 5 | רמת OECD 4 או 5 |  |

Sources: `oecd_piaac_2023_tables` (OECD); `boi_piaac_note_2024` (Bank of Israel (Sefi Bahar and Elad DeMalach))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Literacy: national distribution over proficiency levels (18-64) | `oecd_piaac_2023_tables` | 0.0270 | — | 0.04 | ✅ pass |
| Literacy: share of low performers (level 1 or below) by age group | `oecd_piaac_2023_tables` | 0.0171 | — | 0.06 | ✅ pass |
| Literacy: share of low performers (level 1 or below) by education (25-65) | `oecd_piaac_2023_tables` | 0.0159 | — | 0.06 | ✅ pass |
| Literacy: share of low performers (level 1 or below) by gender | `oecd_piaac_2023_tables` | 0.0182 | — | 0.06 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `literacy_score` — Literacy score (modelled; 0-500 scale) / ציון אוריינות קריאה (משוער; סולם 0-500)

- **type:** `interval`
- **parents:** `literacy_level`
- **distribution file:** `model/cpts/literacy_score.csv`

Sources: `oecd_piaac_2023_tables` (OECD)

Validation:

_No automated validation checks cover this node yet._

#### `literacy_percentile` — Literacy percentile among adult citizens (modelled) / אחוזון מיומנות הקריאה בקרב האזרחים הבוגרים (משוער)

- **type:** `percentile`
- **parents:** `literacy_score`
- **distribution file:** `model/cpts/literacy_percentile.csv`

Sources: `oecd_piaac_2023_tables` (OECD)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Percentile is uniform among adult citizens (n = 1,000,000) | `model` | 0.0023 | — | 0.01 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
