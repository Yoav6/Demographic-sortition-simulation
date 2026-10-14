# Media diet

<!-- he-summary -->
**צריכת תקשורת.** שימוש באינטרנט וברשתות חברתיות (הסקר החברתי 2024, לפי דתיות, מין וגיל); תדירות המעקב אחר חדשות ומידע פוליטי, ותדירות הקריאה של חדשות ברשתות החברתיות (הסקר הלאומי של הבחירות 2022, לפי דתיות, גיל, השכלה וגוש ההצבעה); ומהדורת החדשות האהובה בטלוויזיה (מדד התקשורת של מכון אגם, דצמבר 2024, לפי תמיכה בקואליציה או באופוזיציה). מדד אגם אינו מכסה תקשורת בשפה הערבית, ולכן לאזרחים ערבים ודרוזים המהדורה האהובה מסומנת "לא נמדד".
<!-- /he-summary -->

## Definition

* **`online`** — uses the internet and social networks / uses the internet but not social
  networks / does not use the internet (Social Survey: social networks used in the last three
  months).
* **`news_frequency`** — how many times in the past week the person caught up on political
  information and news: more than once a day, almost every day, two or three times a week,
  about once a week, hardly ever (INES 2022, question v601b).
* **`social_news`** — the same, on social networks (INES v506); "does not use social networks"
  for people who do not.
* **`favorite_news`** — favourite TV news broadcast: Channel 12 News, Channel 14, Kan 11 News,
  Channel 13 News, i24NEWS, Channel 9, another, none; "not measured" for Arab and Druze citizens.
* **`vote_bloc`** (hidden) — the 2022 vote grouped into coalition parties (Likud, Religious
  Zionism, Shas, UTJ), Jewish opposition parties, Arab parties, other lists, did not vote, too
  young.

## Why these parents

Internet use falls with age and is low among Haredim (many use filtered phones or none);
political interest and news habits differ by religiosity, age and education; and since 2023 the
choice of TV news has become strongly political — Channel 14 for coalition supporters, Channel 12
and Kan for the opposition. The 2022 vote stands in for current political alignment. News on
social networks depends above all on how much the person follows the news at all.

## Sources

* `src:cbs_social_survey_2024` — use of social networks (including "does not use the
  internet") by religiosity × sex × age for Jews, sex × age for "others", religion × sex × age for
  Arabs outside the Jerusalem district (`social_networks_*`). Ages 20+.
* `src:ines_2022` — political news frequency overall and on social networks (1,569 and 1,364
  respondents with answers; panel weights).
* `src:agam_media_index_2024` — favourite news broadcast of all respondents (page 11) and of
  coalition and opposition supporters (page 12), transcribed by hand into
  `data/manual/agam/favorite_news.csv` (online panel of 1,201 citizens, November 2024).

## Preprocessing

* Agam's charts are transcribed with their page numbers; small unlabelled bars (i24NEWS, Channel
  9, other) are read from the axis and are approximate (±0.5 points). See
  `data/manual/agam/README.md`.
* INES age groups and education are mapped as on the vote page; the 2022 vote is grouped into
  blocs; respondents without a reported vote get no bloc effect.

## Estimation

* `online`: as for the other Social Survey nodes — rows shrunk toward a main-effects fit,
  smoothed over ages 45–64, 18–19-year-olds with the 20–24 pattern.
* `news_frequency`: weighted multinomial logit (ridge λ = 1) on religiosity (9 levels, Jewish
  and Arab scales), age group, education and bloc; written out as a table over those parents.
  People too young to have voted in 2022 get the 18–29 age effect and no bloc effect.
* `social_news`: for people who use social networks, P(frequency on social networks | overall
  frequency, age group) from INES respondents who use social networks, each row shrunk toward
  the overall-frequency row with 10 pseudo-respondents. Everyone else: "does not use social
  networks".
* `favorite_news`: Jewish and "other" citizens who voted for coalition parties get Agam's
  coalition distribution; for the Jewish opposition (and the few Jewish voters of Arab parties),
  the opposition distribution; everyone else (other lists, non-voters, too young), the overall
  distribution. Arab and Druze citizens: "not measured".

## Calibration

None; the surveys are the targets.

## Validation

Model: 80% of secular Jews use social networks, 14% of Haredim (32% of whom do not use the
internet at all); 35% of people aged 75+ use social networks. Among people who hardly ever
follow political news, 67% hardly ever read it on social networks either. The sampler check
covers these nodes; there is no independent source to compare with.

## Limitations

* Agam is an online panel; people without internet access (notably many Haredim and older
  people) are under-represented, so their TV preferences follow those of online
  supporters of the same bloc.
* Arabic-language media (Al Jazeera, Makan 33, Hala, Arab news sites) are not covered by any
  source used here.
* Political alignment is the 2022 vote, while Agam asked about voting intention in November
  2024; some voters have changed sides since 2022.
* The ten most popular news sites, the trust in media outlets and the favourite journalists
  that Agam reports are not modelled.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `online` — Internet and social networks / אינטרנט ורשתות חברתיות

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/online.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `social` | uses the internet and social networks | משתמש באינטרנט וברשתות חברתיות | משתמשת באינטרנט וברשתות חברתיות |
| `internet_only` | uses the internet but not social networks | משתמש באינטרנט אך לא ברשתות חברתיות | משתמשת באינטרנט אך לא ברשתות חברתיות |
| `offline` | does not use the internet | אינו משתמש באינטרנט | אינה משתמשת באינטרנט |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `vote_bloc` — 2022 vote bloc / גוש הצבעה ב-2022

- **type:** `lookup` · hidden helper
- **parents:** `vote_2022`
- **distribution file:** `model/lookups/vote_bloc.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `coalition` | coalition parties | מפלגות הקואליציה |  |
| `opposition` | Jewish opposition parties | מפלגות האופוזיציה היהודיות |  |
| `arab` | Arab parties | מפלגות ערביות |  |
| `other` | other parties | מפלגות אחרות |  |
| `did_not_vote` | did not vote | לא הצביע | לא הצביעה |
| `too_young` | too young to vote | צעיר מדי להצביע | צעירה מדי להצביע |

Sources: `cec_knesset25` (Central Elections Committee (CEC))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_frequency` — Follows political news / מעקב אחר חדשות ומידע פוליטי

- **type:** `table`
- **parents:** `religiosity`, `vote_age`, `vote_education`, `vote_bloc`
- **distribution file:** `model/cpts/news_frequency.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `several_daily` | more than once a day | יותר מפעם ביום |  |
| `daily` | almost every day | כמעט כל יום |  |
| `few_times_week` | two or three times a week | פעמיים-שלוש בשבוע |  |
| `weekly` | about once a week | בערך פעם בשבוע |  |
| `never` | hardly ever | כמעט אף פעם |  |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `social_news` — Political news on social networks / חדשות ומידע פוליטי ברשתות החברתיות

- **type:** `table`
- **parents:** `online`, `news_frequency`, `vote_age`
- **back-off order:** `news_frequency` → `vote_age`
- **distribution file:** `model/cpts/social_news.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `several_daily` | more than once a day | יותר מפעם ביום |  |
| `daily` | almost every day | כמעט כל יום |  |
| `few_times_week` | two or three times a week | פעמיים-שלוש בשבוע |  |
| `weekly` | about once a week | בערך פעם בשבוע |  |
| `never` | hardly ever | כמעט אף פעם |  |
| `no_social_media` | does not use social networks | אינו משתמש ברשתות חברתיות | אינה משתמשת ברשתות חברתיות |

Sources: `ines_2022` (Israel National Election Studies, Tel Aviv University); `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `favorite_news` — Favourite TV news broadcast / מהדורת החדשות האהובה

- **type:** `table`
- **parents:** `group`, `vote_bloc`
- **back-off order:** `vote_bloc` → `group`
- **distribution file:** `model/cpts/favorite_news.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `news12` | Channel 12 News | חדשות 12 |  |
| `channel14` | Channel 14 | עכשיו 14 |  |
| `kan11` | Kan 11 News | כאן חדשות |  |
| `news13` | Channel 13 News | חדשות 13 |  |
| `i24` | i24NEWS | i24NEWS |  |
| `channel9` | Channel 9 | ערוץ 9 |  |
| `other` | another broadcast | מהדורה אחרת |  |
| `none` | none | אף אחת |  |
| `not_measured` | not measured (Arabic-language media were not surveyed) | לא נמדד (התקשורת בערבית לא נסקרה) |  |

Sources: `agam_media_index_2024` (Agam Institute (Nimrod Nir, Dr. Gayil Talshir, Assa Shapira))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 200,000; tolerance: adjusted p-value) | `model` | 0.0296 | — | 0.001 | ✅ pass |

Sample: 200,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
