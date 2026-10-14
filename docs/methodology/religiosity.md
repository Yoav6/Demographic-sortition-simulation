# Religiosity

<!-- he-summary -->
**מידת דתיות** לפי הגדרה עצמית. ליהודים — חרדי, דתי, מסורתי-דתי, מסורתי, חילוני (סולם הסקר החברתי של הלמ"ס); לערבים ולדרוזים — דתי מאוד, דתי, לא כל כך דתי, לא דתי. ההתפלגות הארצית ליהודים לפי מין וגיל מכוילת בדיוק לסקר החברתי 2024 (11.4% חרדים, 12.0% דתיים, 12.0% מסורתיים-דתיים, 21.5% מסורתיים, 42.7% חילונים). ההבדלים בין יישובים מוערכים מתוצאות הבחירות 2022: לכל יישוב מוסקת תערובת הדתיות שמסבירה הכי טוב את הצבעתו, לפי דפוסי ההצבעה של כל קבוצה בסקר הלאומי של הבחירות (INES). כך בני ברק יוצאת 70% חרדית ותל אביב 70% חילונית.
<!-- /he-summary -->

## Definition

Self-defined religiosity, on the CBS Social Survey scales:

* Jews (and "others"): `haredi` (ultra-Orthodox), `dati` (religious), `masorti_dati`
  (traditional-religious), `masorti` (traditional, not so religious), `hiloni` (secular);
* Muslims, Arab Christians and Druze: `very_religious`, `religious`, `not_so_religious`,
  `not_religious`.

## Why these parents

`group` selects the scale and the overall level; `sex` and `age_band` matter (Haredim are a
much larger share of young adults than of the elderly; women report somewhat higher religiosity
among non-Jews); `locality_profile` captures the strong geographic concentration of religious
communities (Bnei Brak, Modi'in Illit, settlements, Tel Aviv...). Locality profiles are groups
of localities with similar estimated religious composition, which keeps the table compact.

## Sources

* `src:cbs_abstract_2025_attitudes` — CBS Social Survey 2024 (persons 20+): religiosity of Jews
  by sex and by age group (20–44, 45–64, 65+) on a 4-category scale, the 5-category national
  split, and the share religious/not religious among members of other religions by sex and age.
* `src:cbs_social_survey_2024` — the same survey through the CBS table generator: religiosity
  of Jews by sex and 5-year age group (n ≈ 5,500 Jewish respondents; summed over the
  marital-status table `marital_jews`).
* `src:ines_2022` — Israel National Election Studies 2022 (n = 1,585, weighted): vote by
  religiosity (for the ecological inference); religiosity of Arab respondents by religion;
  respondents of "other" religion.
* `src:cec_knesset25` — 2022 results by locality and polling station.

## Preprocessing

* INES: the 5-point question (v144) is mapped to the CBS categories; for Arab respondents
  points 2 and 3 are both "religious". Respondents are weighted with the panel weights.
* Social Survey religiosity by sex × age group: each age row is shrunk toward the main-effects
  fit of sex and age with 10 pseudo-respondents (see [METHODOLOGY.md](../../METHODOLOGY.md) §3).
* Election results: in mixed cities only polling stations where Arab parties did *not* win a
  majority are used for the Jewish composition.

## Estimation

**National level (Jews).** IPF on sex × age band × CBS age group × 4-category religiosity ×
within-category split. Seed: the Social Survey's religiosity by sex and 5-year age group × the
frame's Jewish adults (18–19-year-olds take the 20–24 pattern).
Margins: the frame's adults by sex and age band; CBS 2024 religiosity by sex; by age group; and
the 5-category national split (traditional = 12.0% religious-traditional + 21.5%
not-so-religious traditional). CBS covers ages 20+; 18–19-year-olds join the 20–44 group.

**Locality level: ecological inference from votes.** INES gives, for Jewish voters, the
probability of voting for each party given religiosity (*M[k,p]*). A locality's Jewish vote
counts *v* are modelled as a mixture of these five profiles; the mixture weights *x* (religiosity
among voters) are estimated by EM with a Dirichlet prior centred on the national mix:

```
r[k,p] = x[k]·M[k,p] / Σ_k' x[k']·M[k',p]
x[k]  ← (Σ_p v[p]·r[k,p] + a·prior[k]) / (Σ_p v[p] + a),   a = 50
```

Party profiles are not identical everywhere (secular voters in Beer Sheva vote Likud more than
in Tel Aviv), so the likelihood is tempered: at most 200 votes count as data. Voter shares are
divided by INES turnout by religiosity to get adult shares. Localities are then binned by the
estimated Haredi share (cut points 5, 15, 35, 60, 80%), Dati + traditional-religious share (20,
30, 45, 60%) and secular share (30, 45, 60%) into **34 profiles**; localities with fewer than 20
Jewish votes use a "national" profile.

**Combining.** The profiles' religiosity totals are raked so that they add up to the national
totals; then, for each profile, IPF fits sex × age band × religiosity to the profile's adults by
sex and age band and to its religiosity totals, starting from the national conditional pattern.

**Muslims, Arab Christians, Druze.** INES gives the shape of the 4-point distribution for Muslims
and for Christians/Druze (INES does not separate the two). The share "very religious or
religious" is then adjusted by sex and age with the relative pattern of the CBS 2024 figures for
non-Jews, around each group's own level.

**Others.** INES respondents of "other" religion (n = 30, Jewish scale; 88% secular) are combined
with 30 pseudo-respondents distributed like CBS immigrants of 1990+ (Haredi share set to zero).

## Calibration

National Jewish religiosity is calibrated exactly to the CBS Social Survey 2024: Haredi 11.4%,
Dati 12.0%, traditional-religious 12.0%, traditional 21.6%, secular 42.9% (model, adults 18+).

## Validation

Spot checks of the estimated adult Jewish composition: Bnei Brak 70% Haredi; Modi'in Illit ≈ 80%;
Jerusalem 33% Haredi, 27% secular; Tel Aviv-Yafo 70% secular; Kiryat Arba ≈ 60% Dati. Automated
checks appear below.

## Limitations

* The ecological inference assumes that within a locality, members of each religiosity group
  vote like the national average of their group (tempered). This is the classic ecological
  fallacy risk; the tempering and the prior limit, but do not remove, it.
* INES has no geography, small cells for Arab respondents, and does not separate Christians
  from Druze, so these two share one shape.
* Religiosity of "others" rests on 30 survey respondents and a prior.
* CBS's figures for non-Jews include East Jerusalem residents.

## Changelog

* 2026.10.0 — first version. The national age pattern is seeded from the Social Survey's
  5-year age groups (n ≈ 5,500) rather than INES's 8 age groups (n ≈ 1,200), after validation
  showed the INES-seeded age composition differed from the survey by up to 6 points in some
  religiosity × age cells.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `locality_profile` — Religiosity profile of the locality / פרופיל דתיות של היישוב

- **type:** `lookup` · hidden helper
- **parents:** `locality`
- **distribution file:** `model/lookups/locality_profile.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `h0d0s0` | h0d0s0 | h0d0s0 |  |
| `h0d0s1` | h0d0s1 | h0d0s1 |  |
| `h0d0s2` | h0d0s2 | h0d0s2 |  |
| `h0d0s3` | h0d0s3 | h0d0s3 |  |
| `h0d1s0` | h0d1s0 | h0d1s0 |  |
| `h0d1s1` | h0d1s1 | h0d1s1 |  |
| `h0d1s2` | h0d1s2 | h0d1s2 |  |
| `h0d2s0` | h0d2s0 | h0d2s0 |  |
| `h0d2s1` | h0d2s1 | h0d2s1 |  |
| `h0d3s0` | h0d3s0 | h0d3s0 |  |
| `h0d3s1` | h0d3s1 | h0d3s1 |  |
| `h0d4s0` | h0d4s0 | h0d4s0 |  |
| `h1d0s1` | h1d0s1 | h1d0s1 |  |
| `h1d0s2` | h1d0s2 | h1d0s2 |  |
| `h1d0s3` | h1d0s3 | h1d0s3 |  |
| `h1d1s0` | h1d1s0 | h1d1s0 |  |
| `h1d1s1` | h1d1s1 | h1d1s1 |  |
| `h1d1s2` | h1d1s2 | h1d1s2 |  |
| `h1d2s0` | h1d2s0 | h1d2s0 |  |
| `h1d2s1` | h1d2s1 | h1d2s1 |  |
| `h1d3s0` | h1d3s0 | h1d3s0 |  |
| `h1d4s0` | h1d4s0 | h1d4s0 |  |
| `h2d0s1` | h2d0s1 | h2d0s1 |  |
| `h2d1s0` | h2d1s0 | h2d1s0 |  |
| `h2d2s0` | h2d2s0 | h2d2s0 |  |
| `h2d3s0` | h2d3s0 | h2d3s0 |  |
| `h2d4s0` | h2d4s0 | h2d4s0 |  |
| `h3d0s0` | h3d0s0 | h3d0s0 |  |
| `h3d1s0` | h3d1s0 | h3d1s0 |  |
| `h3d2s0` | h3d2s0 | h3d2s0 |  |
| `h4d0s0` | h4d0s0 | h4d0s0 |  |
| `h4d1s0` | h4d1s0 | h4d1s0 |  |
| `h5d0s0` | h5d0s0 | h5d0s0 |  |
| `national` | national | national |  |

Sources: `cec_knesset25` (Central Elections Committee (CEC)); `ines_2022` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `religiosity` — Religiosity (self-defined) / מידת דתיות (הגדרה עצמית)

- **type:** `table`
- **parents:** `group`, `sex`, `age_band`, `locality_profile`
- **back-off order:** `locality_profile`
- **distribution file:** `model/cpts/religiosity.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `haredi` | Ultra-Orthodox (Haredi) | חרדי | חרדית |
| `dati` | Religious (Dati) | דתי | דתייה |
| `masorti_dati` | Traditional-religious | מסורתי-דתי | מסורתית-דתייה |
| `masorti` | Traditional | מסורתי | מסורתית |
| `hiloni` | Secular | חילוני | חילונית |
| `very_religious` | Very religious | דתי מאוד | דתייה מאוד |
| `religious` | Religious | דתי | דתייה |
| `not_so_religious` | Not so religious | לא כל כך דתי | לא כל כך דתייה |
| `not_religious` | Not religious | לא דתי | לא דתייה |

Sources: `cbs_abstract_2025_attitudes` (Central Bureau of Statistics (CBS) - Social Survey); `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey); `ines_2022` (Israel National Election Studies, Tel Aviv University); `cec_knesset25` (Central Elections Committee (CEC))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Age composition of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0188 | 0.0000 | 0.03 | ✅ pass |
| Age composition of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0901 | 0.0075 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
