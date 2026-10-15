# Vote in the 2022 Knesset election

<!-- he-summary -->
**הצבעה בבחירות לכנסת ה-25 (נובמבר 2022)**, כולל הימנעות מהצבעה. ליהודים ול"אחרים": מודל לוגיט רב-ערכי על נתוני הסקר הלאומי של הבחירות 2022 (דתיות, גיל, השכלה, מוצא), שמכויל לכל פרופיל יישובים כך שיתאים בדיוק לתוצאות הרשמיות בקלפיות היהודיות של אותם יישובים, כולל שיעור ההצבעה. לערבים ולדרוזים: התוצאה הרשמית ביישובם (או בקלפיות שבהן זכו המפלגות הערביות ברוב, בערים מעורבות). מי שהיה מתחת לגיל 18 בבחירות מסומן "צעיר מדי להצביע". הבחירות לכנסת ה-26 יחליפו את הצומת הזה לאחר פרסום התוצאות הרשמיות.
<!-- /he-summary -->

## Definition

How the person voted in the election to the 25th Knesset (1 November 2022): one of the 13 lists
that won seats or came close (Likud, Yesh Atid, Religious Zionism, National Unity, Shas, United
Torah Judaism, Yisrael Beiteinu, Labor, Meretz, Jewish Home, Ra'am, Hadash-Ta'al, Balad), another
list, did not vote, or too young to vote (under 18 on election day: aged 18–19 at the end of
2024). Invalid and blank ballots (0.6%) are counted as not voting.

Hidden helper nodes:

* `vote_age` — age group on election day (18–29, 30–49, 50+), or too young;
* `vote_education` — no matriculation / matriculation or post-secondary / academic degree;
* `vote_origin` — continent of origin (Asia-Africa, Europe-America, former USSR); third
  generation by self-identified ancestry (Ashkenazi, Mizrahi, other);
* `vote_area` — for Jewish and "other" citizens, their locality's religiosity profile; for Arab
  and Druze citizens, their locality (or the Arab-majority polling stations of a mixed city),
  and for Druze outside Druze-majority localities, the pooled Druze-majority localities.

## Why these parents

Religiosity is by far the strongest predictor of the Jewish vote (Haredim vote Shas and UTJ;
religious Zionists vote Religious Zionism; secular voters split between Yesh Atid, National
Unity, Labor and Meretz). Origin (Mizrahi vs Ashkenazi, former USSR), age and education add
large, well-documented differences (Likud among Mizrahi and less-educated voters, Yisrael
Beiteinu among former-Soviet immigrants). Geography adds what individual traits miss: the
locality profile carries everything the official results reveal beyond the person's own
characteristics. For Arab and Druze citizens, voting differs mostly by locality (Ra'am in the
Negev and the Triangle, Hadash-Ta'al in the Galilee, Zionist parties in Druze villages), and the
official locality results describe it directly.

## Sources

* `src:ines_2022` — Israel National Election Studies 2022 pre/post-election panel: reported vote
  or abstention, religiosity, age, education, own and father's birthplace, ethnic
  self-identification (1,062 Jewish and "other" respondents with a usable answer, panel weights).
* `src:cec_knesset25` — official results by polling station and locality, eligible voters, and
  the national total including double-envelope votes.

## Preprocessing

* Polling stations where Arab parties won a majority of valid votes are separated from the rest
  (`extract/cec.py`). Jewish targets use all stations of localities with under 80% Arab or Druze
  adults, minus the Arab-majority stations of mixed localities; Arab targets use all stations of
  localities with 80%+ Arab or Druze adults, or the Arab-majority stations of mixed localities.
* **Double envelopes** — 462,807 votes (9.7%) cast by soldiers, diplomats, hospital patients,
  prisoners and others, which have no locality — are added back by scaling each party's votes
  everywhere by its national ratio of double-envelope to station votes.
* **Denominator**: the model's eligible adults (aged 20+ at the end of 2024, i.e. 18+ on election
  day) in the area, not the voter roll. The roll also lists about half a million citizens living
  abroad, who are outside the model's population; dividing by residents gives turnout among
  people who could actually vote (77.5% nationally vs 70.6% of the roll).
* INES age groups, education and birthplace are mapped to the helper categories; "other"
  respondents are of former-Soviet origin.

## Estimation

1. **Individual model (Jews and others).** A weighted multinomial logit of the 15 outcomes
   (14 lists + did not vote) on religiosity, age group, education and origin, with a ridge
   penalty (λ = 1) on the slopes, fitted by L-BFGS. INES over-reports turnout and has few
   respondents for some lists; both are corrected in the next step.
2. **Calibration to the official results.** For each of the 34 locality profiles, one
   additive shift per outcome is found (iterative scaling) so that the model's implied
   distribution over the profile's eligible adults — computed exactly from the frame and the
   religiosity, origin and education tables — reproduces the official result of the profile's
   Jewish polling stations, abstention included. The relative effects of religiosity, age,
   education and origin within a profile come from INES; the levels come from the official
   count.
3. **Arab and Druze citizens.** P(outcome | area) = the area's official votes per list divided by
   its eligible adults; the remainder did not vote (turnout capped at 97%).
4. Under-18s on election day: `too_young`.

## Calibration

Profile totals reproduce the official Jewish station results (largest residual below 10⁻⁷), and
Arab areas their official results, by construction. National shares therefore match the
official count, double envelopes included.

## Validation

Model shares among voters vs the official national result: all lists within 0.07 points (the
generated table below); turnout among eligible residents 77.5%. Within the model, 46% of Haredi
adults voted UTJ and 33% Shas (10% abstained); 41% of Dati adults voted Religious Zionism; 42%
of traditional Jews voted Likud; 32% of secular Jews voted Yesh Atid. Among Druze voters, National
Unity 32%, Yisrael Beiteinu 16%, Meretz 15%, Likud 13% — as in the Druze-majority villages.

## Limitations

* The vote of a locality profile is fitted as a whole; differences between localities within a
  profile come only from their religiosity, origin, age and education mix.
* Arab citizens of a mixed Muslim–Christian locality share one distribution: Arab Christians in
  Nazareth or Haifa get some Ra'am vote that Christians rarely cast. Within an Arab locality, the
  vote does not depend on age, religiosity or education.
* INES is a survey of about 1,500 people; small lists (Meretz, Labor, Jewish Home) rest on few
  respondents, though calibration fixes their totals.
* Double-envelope voters are spread in proportion to each party's station votes, not by where
  soldiers or hospital patients actually live.
* People who voted in 2022 and have since died or emigrated are not in the population; recent
  immigrants (2022–24) who were not yet eligible are treated as if they had been.

## Changelog

* 2026.10.0 — first version (25th Knesset, 2022). To be replaced by the 26th Knesset election
  (27 October 2026) once the certified results are published; see
  [decision 0002](../decisions/0002-politics-2022-then-2026.md).

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `vote_age` — Age group in November 2022 / קבוצת גיל בנובמבר 2022

- **type:** `lookup` · hidden helper
- **parents:** `age`
- **distribution file:** `model/lookups/vote_age.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `too_young` | under 18 | מתחת ל-18 |  |
| `y` | 18-29 | 18-29 |  |
| `m` | 30-49 | 30-49 |  |
| `o` | 50+ | 50+ |  |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `vote_education` — Education (3 levels) / השכלה (3 רמות)

- **type:** `lookup` · hidden helper
- **parents:** `education`
- **distribution file:** `model/lookups/vote_education.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `low` | no matriculation | ללא בגרות |  |
| `mid` | matriculation or post-secondary | בגרות או על-תיכונית |  |
| `academic` | academic degree | תואר אקדמי |  |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `vote_origin` — Origin group / קבוצת מוצא

- **type:** `table` · hidden helper
- **parents:** `origin`, `ancestry`
- **back-off order:** `ancestry`
- **distribution file:** `model/cpts/vote_origin.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `AA` | Asia-Africa | אסיה-אפריקה |  |
| `EA` | Europe-America | אירופה-אמריקה |  |
| `FSU` | former USSR | ברית המועצות לשעבר |  |
| `IL3_ashkenazi` | third generation, Ashkenazi | דור שלישי, אשכנזי |  |
| `IL3_mizrahi` | third generation, Mizrahi | דור שלישי, מזרחי |  |
| `IL3_other` | third generation, other | דור שלישי, אחר |  |
| `native` | Arab or Druze | ערבי או דרוזי |  |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `vote_area` — Electoral area / אזור בחירה

- **type:** `table` · hidden helper
- **parents:** `group`, `locality`
- **distribution file:** `model/cpts/vote_area.csv`
- **categories:** 190 (see the domain file)

Sources: `cec_knesset25` (Central Elections Committee (CEC))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `vote_2022` — Vote in the 2022 Knesset election / הצבעה בבחירות לכנסת 2022

- **type:** `table`
- **parents:** `vote_area`, `religiosity`, `vote_age`, `vote_education`, `vote_origin`
- **back-off order:** `religiosity` → `vote_education` → `vote_origin` → `vote_area`
- **distribution file:** `model/cpts/vote_2022.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `likud` | Likud | הליכוד |  |
| `yesh_atid` | Yesh Atid | יש עתיד |  |
| `religious_zionism` | Religious Zionism (Smotrich - Ben Gvir) | הציונות הדתית |  |
| `national_unity` | National Unity (Gantz) | המחנה הממלכתי |  |
| `shas` | Shas | ש"ס |  |
| `utj` | United Torah Judaism | יהדות התורה |  |
| `yisrael_beiteinu` | Yisrael Beiteinu | ישראל ביתנו |  |
| `labor` | Labor | העבודה |  |
| `meretz` | Meretz | מרצ |  |
| `jewish_home` | Jewish Home (Shaked) | הבית היהודי |  |
| `raam` | Ra'am (United Arab List) | רע"ם |  |
| `hadash_taal` | Hadash-Ta'al | חד"ש-תע"ל |  |
| `balad` | Balad | בל"ד |  |
| `other_party` | another party | מפלגה אחרת |  |
| `did_not_vote` | did not vote | לא הצביע | לא הצביעה |
| `too_young` | too young to vote in 2022 | צעיר מדי להצביע ב-2022 | צעירה מדי להצביע ב-2022 |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University); `cec_knesset25` (Central Elections Committee (CEC))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| 2022 election: national vote shares | `cec_knesset25` | 0.0006 | — | 0.005 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people under 18 in November 2022 did not vote then | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
