# Media diet

<!-- he-summary -->
**צריכת תקשורת.** שימוש באינטרנט וברשתות חברתיות (הסקר החברתי 2024); תדירות המעקב אחר חדשות פוליטיות (הסקר הלאומי של הבחירות 2022); באיזו תדירות האדם מתעדכן בחדשות בכל אחד משבעה אמצעים — טלוויזיה, רדיו, עיתונים מודפסים, אתרי חדשות, רשתות חברתיות, מנועי חיפוש ופודקאסטים — באילו רשתות חברתיות הוא משתמש ובאילו מהן הוא מתעדכן בחדשות (סקר איגוד האינטרנט הישראלי והטכניון, אוקטובר 2024, לפי גיל, מגזר, מין והשכלה); באילו ערוצי טלוויזיה הוא צופה בחדשות באופן קבוע (הסקר הלאומי של הבחירות 2025, לפי גיל, מגזר וגוש ההצבעה, כולל אל-ג'זירה ומכאן 33); באילו אתרי חדשות הוא מבקר לפחות פעם בשבוע (מדד התקשורת של מכון אגם, לפי מחנה פוליטי); מהו העיתון המודפס העיקרי שלו (סקר TGI, כשהנטייה הפוליטית של קוראי ידיעות אחרונות והארץ נלקחת מזו של קוראי אתריהם); ומהו מקור החדשות המועדף עליו (סקר איגוד האינטרנט). הקשר בין תדירות המעקב אחר חדשות פוליטיות לבין השימוש בכל אמצעי נלקח מהסקר הלאומי של הבחירות 2025.
<!-- /he-summary -->

## Definition

* **`online`** — uses the internet and social networks / uses the internet but not social
  networks / does not use the internet (Social Survey: social networks used in the last three
  months).
* **`news_frequency`** — how many times in the past week the person caught up on political
  information and news: more than once a day, almost every day, two or three times a week,
  about once a week, hardly ever (INES 2022, question v601b).
* **`news_tv`, `news_radio`, `news_print`, `news_sites`, `news_social`, `news_search`,
  `news_podcasts`** — how often the person gets news from television, the radio, printed
  newspapers, news websites and apps, social media (Facebook, X, Instagram, TikTok…), search
  engines and podcasts: often, sometimes, rarely, never (ISOC-IL question 1, "How often do you
  catch up on the news through…").
* **`social_networks`** — the social networks and messaging apps the person uses (WhatsApp,
  Facebook, YouTube, Instagram, Telegram, TikTok, LinkedIn, Pinterest, X, Snapchat; ISOC-IL
  question 3). People who use the internet but not social networks can still use the
  messaging apps (WhatsApp, Telegram); people who do not use the internet use none.
* **`news_networks`** — those of them on which the person regularly reads or watches news or
  headlines (ISOC-IL question 4). Always a subset of `social_networks`.
* **`tv_channels`** — the channels the person watches regularly to catch up on the news:
  Channel 12, Kan 11, Channel 13, Channel 14, Al Jazeera, Makan 33, another channel (INES 2025
  question 614); empty for people who never watch TV news.
* **`news_websites`** — the news sites the person visits at least once a week: ynet, N12,
  Mako, Walla, Kan, Haaretz, Rotter, Kikar HaShabbat, Behadrei Haredim (Agam Media Index);
  empty for people who use news sites rarely or never.
* **`preferred_source`** — the medium the person prefers for news, among those they use most
  often (ISOC-IL question 2); "none" only for people who use none of the seven media.
* **`newspaper`** — the printed newspaper the person reads most: Israel Hayom, Yedioth
  Ahronoth, Haaretz, Maariv, Globes, Makor Rishon, Besheva, the Haredi papers Hamodia, Yated
  Ne'eman, Hamevaser, HaPeles, Mishpacha, Bakehila and Yom LeYom, or "a newspaper in Arabic";
  "none" for people who never read printed newspapers.
* Hidden helpers: **`vote_bloc`** (the 2022 vote grouped into coalition parties, Jewish
  opposition parties, Arab parties, other lists, did not vote, too young), **`media_age`**
  (the media surveys' age groups: 18–24, 25–29, 30–39, 40–49, 50–64, 65+) and
  **`media_sector`** (secular Jewish or other, traditional, religious, Haredi, Arab or Druze —
  from religiosity; traditional includes traditional-religious).

## Why these parents

Age is the strongest single driver of media habits: printed newspapers and TV news are
read and watched most by people over 65, TikTok and Instagram are used most by the young.
Population group matters almost as much — Haredim read newspapers far more and watch
television far less than secular Jews, and Arab citizens get more of their news from social
media — and sex and education shape radio, podcasts and news websites. People who use no
social network cannot read news there, and people who do not use the internet get no news
online. How often someone follows political news (which depends on the 2022 vote, among
other things) ties the seven media together: people who follow politics closely use more
media, more often. The choice of TV channel has become strongly political since 2023, so it
depends on the 2022 vote bloc as well as on age and population group, and so do news sites
(ynet and Haaretz are read more by opposition voters, Channel 14's audience leans right).
Newspapers lean politically too, but no source shows it directly; it is borrowed from the
papers' own websites.

## Sources

* `src:isoc_media_survey_2024` — the Israel Internet Association (ISOC-IL) and Technion
  survey of news consumption and disinformation: respondent-level data of 1,005 internet users
  aged 18+ (805 Jewish, with Haredim over-sampled, and 200 Arab respondents; iPanel, October
  2024; no weights supplied). Used for the seven media, networks used and news on networks.
  Publication is permitted to cite with credit and a link:
  <https://www.isoc.org.il/sts-data/media-and-disinformation-survey-il>.
* `src:ines_2025` — the Israel National Election Studies off-cycle survey (March–April 2025;
  1,588 citizens, 280 of them Arab, weighted): political news frequency (v612), the sources
  used for political news in the past week (v613: news websites, TV news, radio, daily
  newspapers, Facebook, Instagram, TikTok, WhatsApp groups, Telegram channels, X) and the TV
  channels watched regularly (v614).
* `src:ines_2022` — political news frequency (1,569 respondents with answers; panel weights).
* `src:cbs_social_survey_2024` — use of social networks, including "does not use the
  internet", by religiosity, sex and age (ages 20+).
* `src:tgi_readership` — TGI average-issue readership by title: the general survey of Jewish
  adults (July 2025 – June 2026) and the Haredi TGI (2017, the latest release found online),
  as published in press reports; transcribed in `data/manual/tgi/` with the sentences quoted.
* `src:knesset_rc_newspapers_2018` — the age profile of each title's readers (TGI, first
  half of 2018), from a Knesset Research and Information Center document.

* `src:agam_media_index_2024` — the Agam Institute media index (online panel of 1,201
  citizens, November 2024): how often people visit nine news sites (page 14) and the mean
  frequency by camp — Jews, Arabs, right-wing and liberal voters (page 15), transcribed in
  `data/manual/agam/`. Only the news sites are used: TV channels come from INES 2025, which
  gives them as respondent-level data and for Arab citizens as well (see
  [decision 0006](../decisions/0006-media-sources.md)).

## Preprocessing

* ISOC: the first data row of each file (the question wording) is dropped; categories are
  mapped to the model's ids (`pipeline/popsim/extract/isoc.py`). The survey's age groups
  25–30 and 31–39 are treated as the model's 25–29 and 30–39. Yeshiva or seminary as the
  highest education counts as "no matriculation" for men and "post-secondary" for women,
  as the model classifies Haredi men and women. Nine respondents with no stated sex or
  education are left out (996 remain).
* Respondents who use no social platform — none of Facebook, YouTube, X, Instagram,
  Snapchat, LinkedIn, TikTok and Pinterest, though perhaps WhatsApp or Telegram (108, 73 of
  them Haredim) — stand for the model's "uses the internet but not social networks": the
  Social Survey asks about social networks, not messaging apps.
* 23 respondents who said they never get news from social media but ticked a social platform
  (mostly YouTube) as a place where they regularly read news are counted as not reading news
  there: the frequency question is taken as the primary answer. WhatsApp and Telegram groups
  count as messaging, not social media, and are kept.
* INES 2025: sources and channels were asked only of people who follow political news at
  all; "did not have the right to vote" in 2022 is the bloc "too young".

## Estimation

* `online`: as for the other Social Survey nodes — rows shrunk toward a main-effects fit,
  smoothed over ages 45–64, 18–19-year-olds with the 20–24 pattern.
* `news_frequency`: weighted multinomial logit (ridge λ = 1) on religiosity (9 levels, Jewish
  and Arab scales), age group, education and bloc, written out as a table. People too young to
  have voted in 2022 get the 18–29 age effect and no bloc effect.
* **The seven media** are estimated in two steps.
  1. *How often, by demographic cell.* For each medium, a multinomial logit (ridge λ = 1) on
     the ISOC respondents, with main effects of age group, population group, sex, education
     and "uses no social platform", gives P(often, sometimes, rarely, never) in every cell of
     age × population group × sex × education × internet use. (Interactions were not needed:
     the main effects reproduce every age × population-group cell with 30+ respondents within
     two standard errors.)
  2. *Tied to political news.* ISOC did not ask how often people follow political news, but
     INES 2025 asked both that and which media people used for it in the past week. For each
     medium, a weighted logit on INES 2025 gives r(f) = P(used the medium in the past week |
     political-news frequency f, age group, population group, sex, education), with the
     frequency as a linear score (once a week = 1 … more than once a day = 4; "hardly ever",
     which INES did not ask about sources, is extrapolated to 0). Then, in every cell, the
     table of political-news frequency × medium frequency is fitted by IPF to the model's
     distribution of `news_frequency` in the cell and to the ISOC distribution of the medium,
     starting from r(f) for "often" and "sometimes" and 1 − r(f) for "rarely" and "never". The
     result keeps the ISOC distribution of every cell exactly and gives it the association
     with political news that INES shows. INES items standing for each medium: TV news, radio
     and daily newspapers for the first three; news websites for websites, search engines and
     podcasts (INES has no item for the last two); any of Facebook, Instagram, TikTok,
     WhatsApp groups, Telegram channels or X for social media.
  3. People who do not use the internet get TV, radio and newspapers as internet users of the
     same cell who use no social platform, and never get news online; people who use the
     internet but not social networks never get news from social media.
* `social_networks`: one logit per network (ridge λ = 1) — age group, population group, sex,
  education — on the 888 ISOC respondents who use social platforms, for people who use social
  networks; for people who use the internet but not social networks, WhatsApp and Telegram
  only, on the 108 respondents who use no platform. Networks are drawn independently given
  the person's cell. People who do not use the internet use none.
* `news_networks`: for the users of each network, a logit on how often they get news from
  social media, age group and population group. The sampler draws a network only if the person
  uses it (`subset_of: social_networks`). People who never get news from social media read
  news on no social platform (WhatsApp and Telegram aside).
* `tv_channels`: one weighted logit per channel on INES 2025 respondents who follow the news —
  whether they watched TV news in the past week, population group, 2022 vote bloc and age
  group; Al Jazeera and Makan 33 on Arab respondents only (no Jewish respondent named them).
  "Often" or "sometimes" in `news_tv` counts as having watched TV news in the past week,
  "rarely" as not. People who never watch TV news watch no channel.
* `news_websites`: for each site, Agam's distribution of visit frequency (page 14) is
  shifted on a cumulative-logit scale so that each camp's mean is the one on page 15; that
  gives the share of internet users in the camp who visit the site at least weekly. The
  model's camps: Arab citizens; coalition voters ("right"), opposition voters ("liberal") and
  other Jewish and other citizens ("Jews"). In each population group × bloc cell, that share
  is spread over the people who use news sites often and sometimes, with odds three times as
  high for "often"; people who use news sites rarely or never visit none regularly. Walla has
  no breakdown and gets its national share everywhere. Kikar HaShabbat and Behadrei Haredim
  have no breakdown either; they get an assumed gradient — log-odds +2 for Haredim, +1 for
  religious, 0 for traditional, −1 for secular Jews, none for Arab citizens — calibrated to
  their national share.
* `preferred_source`: every ISOC respondent who answered question 2 prefers a medium they
  use *often* (those who use none often were not asked), so the model picks among the media
  the person uses at their highest frequency — often, else sometimes, else rarely. Within
  them, a conditional logit on the 884 respondents who answered (medium constants plus
  age-group and population-group effects per medium, ridge 1). It is stored as a logit node.
* `newspaper`: among people who read printed newspapers, each title's probability is
  proportional to its TGI average-issue exposure — weekday editions for people who read
  newspapers often, weekend editions for the others.
  * Non-Haredi Jewish and "other" readers: the general TGI of July 2025 – June 2026 (Israel
    Hayom, Yedioth Ahronoth, Haaretz, Maariv, Globes; at the weekend also Makor Rishon and
    Besheva), each title multiplied by its age index — its 2018 exposure in the person's TGI
    age group (18–34, 35–54, 55+) relative to its population-weighted mean. The two
    religious-Zionist weeklies, Makor Rishon and Besheva, go to religious and traditional
    readers only, scaled up so that their national weight is TGI's (religious and traditional
    readers are 55% of the occasional non-Haredi Jewish readers).
  * Political lean: Yedioth Ahronoth and Haaretz are weighted by how much more or less
    their websites (ynet and haaretz.co.il) are visited weekly by coalition, opposition and
    other voters than by Jews overall (Agam); then every title is rescaled so that its
    national share among readers is unchanged. Opposition voters are 2.1 times as likely as
    coalition voters (relative to the other titles) to read Haaretz, and 1.7 times as likely to
    read Yedioth; Israel Hayom and the religious weeklies take up the difference.
  * Haredi readers: the Haredi TGI (Hamodia, Yated Ne'eman, Hamevaser, HaPeles; at the
    weekend also Mishpacha, Bakehila and Yom LeYom).
  * Arab readers: "a newspaper in Arabic" (no source gives titles).

## Calibration

None beyond the coupling above; the surveys are the targets.

## Validation

The generated table below compares the model with the ISOC respondents (how often each
medium is used, by population group and age; networks used; news on each network) and with
INES 2025 (TV channels by 2022 vote bloc and for Arab viewers) and Agam (weekly visitors of
each news site among internet users, nationally and by camp), checks the preferred source
against the ISOC respondents, and lists the constraints:
nobody offline gets news online or uses a network; people who use the internet but not
social networks use at most WhatsApp and Telegram and get no news from social media; nobody
who never watches TV news has a channel; and there is a main newspaper exactly for readers.
The ISOC comparisons are standardised to the respondents' own mix of sex, education and
internet use within each cell, and judge cells with 30 or more respondents.

Some of what the model implies for all adult citizens (a 60,000-person sample): 16% read
printed newspapers often — 27% of people aged 65+ and 10–11% of people in their thirties and
forties, but 17% at 18–24, where Haredim are numerous; 71% of Haredim and 34% of secular
Jews read them often or sometimes. 8% of people aged 65+ and 23% of those aged 18–24 never
watch TV news. Of social-network users, 62% of 18–24-year-olds use TikTok and 21% of those
aged 65+.

TGI as an outside check: 42% of non-Haredi Jewish and other adults read newspapers often or
sometimes in the model, against TGI's 33.5% for the average weekday issue; 17% of them read
Israel Hayom often or sometimes (TGI: 22.0% average-issue exposure). The measures differ —
TGI counts everyone who looked at yesterday's issue of each title, including readers of
several papers, while the model gives each reader one main paper.

## Limitations

* ISOC covers internet users only. The TV, radio and newspaper habits of the 12% of adults
  who do not use the internet (mostly older people, and Haredim) are those of internet users
  of the same age, group, sex and education who use no social platform.
* ISOC has no weights and over-samples Haredim; the estimates condition on the cells
  rather than relying on the sample's composition. Its age groups end at 65+ (94
  respondents), so the model does not distinguish 65–74 from 85+ within internet users.
* The link between political news and the seven media is borrowed from another survey
  (INES 2025) and assumes that "used the medium for political news in the past week" moves
  with the frequency question as "often or sometimes" does.
* No public source breaks newspaper readership down by vote; the lean of Yedioth Ahronoth
  and Haaretz is borrowed from their websites, whose readers are probably less partisan than
  the print readers, so the model likely understates how left-leaning Haaretz's readers are
  and how right-leaning Israel Hayom's. Arabic-language news sites (Panet, Arab48…) are not
  covered by Agam. The newspaper age profiles are from 2018 and the Haredi figures from 2017; Calcalist and
  TheMarker, which the latest TGI release does not report, are not modelled, nor are local
  papers or Russian-, English- and Arabic-language titles.
* TV channels: i24NEWS and Channel 9 are counted under "another channel" in INES.
* Networks are drawn independently given the person's cell, so the model does not know that
  heavy users of one network tend to use others.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `media_age` — Age group (media surveys) / קבוצת גיל (סקרי תקשורת)

- **type:** `lookup` · hidden helper
- **parents:** `age`
- **distribution file:** `model/lookups/media_age.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `18_24` | 18-24 | 18-24 |  |
| `25_29` | 25-29 | 25-29 |  |
| `30_39` | 30-39 | 30-39 |  |
| `40_49` | 40-49 | 40-49 |  |
| `50_64` | 50-64 | 50-64 |  |
| `65_plus` | 65+ | 65+ |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `media_sector` — Population group (media surveys) / מגזר (סקרי תקשורת)

- **type:** `lookup` · hidden helper
- **parents:** `religiosity`
- **distribution file:** `model/lookups/media_sector.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `secular` | secular Jewish or other | יהודי חילוני או אחר |  |
| `traditional` | traditional Jewish | יהודי מסורתי |  |
| `religious` | religious Jewish | יהודי דתי |  |
| `haredi` | Haredi | חרדי |  |
| `arab` | Arab or Druze | ערבי או דרוזי |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

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
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who do not use the internet get no news from websites, social media, search engines or podcasts | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people who use the internet but not social networks use at most WhatsApp and Telegram and get no news from social media | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people who do not use the internet use no network or messaging app | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

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
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

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
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_tv` — News on TV / חדשות בטלוויזיה

- **type:** `table`
- **parents:** `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`, `online`
- **distribution file:** `model/cpts/news_tv.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who never watch TV news watch no channel regularly | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_radio` — News on the radio / חדשות ברדיו

- **type:** `table`
- **parents:** `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`, `online`
- **distribution file:** `model/cpts/news_radio.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_print` — Printed newspapers / עיתונים מודפסים

- **type:** `table`
- **parents:** `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`, `online`
- **distribution file:** `model/cpts/news_print.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: no main newspaper for people who never read printed newspapers | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people who read printed newspapers have a main newspaper | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_sites` — News websites and apps / אתרי חדשות ואפליקציות

- **type:** `table`
- **parents:** `online`, `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`
- **back-off order:** `news_frequency` → `media_age` → `media_sector` → `sex` → `vote_education`
- **distribution file:** `model/cpts/news_sites.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who do not use the internet get no news from websites, social media, search engines or podcasts | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_social` — News on social media / חדשות ברשתות החברתיות

- **type:** `table`
- **parents:** `online`, `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`
- **back-off order:** `news_frequency` → `media_age` → `media_sector` → `sex` → `vote_education`
- **distribution file:** `model/cpts/news_social.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who do not use the internet get no news from websites, social media, search engines or podcasts | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people who use the internet but not social networks use at most WhatsApp and Telegram and get no news from social media | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_search` — News through search engines / חדשות דרך מנועי חיפוש

- **type:** `table`
- **parents:** `online`, `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`
- **back-off order:** `news_frequency` → `media_age` → `media_sector` → `sex` → `vote_education`
- **distribution file:** `model/cpts/news_search.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who do not use the internet get no news from websites, social media, search engines or podcasts | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_podcasts` — News podcasts / פודקאסטים

- **type:** `table`
- **parents:** `online`, `news_frequency`, `media_age`, `media_sector`, `sex`, `vote_education`
- **back-off order:** `news_frequency` → `media_age` → `media_sector` → `sex` → `vote_education`
- **distribution file:** `model/cpts/news_podcasts.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `often` | often | לעיתים קרובות |  |
| `sometimes` | sometimes | מדי פעם |  |
| `rarely` | rarely | לעיתים רחוקות |  |
| `never` | never | אף פעם |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology); `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: how often each medium is used, by population group and age (internet users) | `isoc_media_survey_2024` | 0.1323 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who do not use the internet get no news from websites, social media, search engines or podcasts | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `social_networks` — Social networks and messaging apps used / רשתות חברתיות ואפליקציות מסרים

- **type:** `multi`
- **parents:** `online`, `media_age`, `media_sector`, `sex`, `vote_education`
- **back-off order:** `media_age` → `media_sector` → `sex` → `vote_education`
- **distribution file:** `model/cpts/social_networks.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `whatsapp` | WhatsApp | וואטסאפ |  |
| `facebook` | Facebook | פייסבוק |  |
| `youtube` | YouTube | יוטיוב |  |
| `instagram` | Instagram | אינסטגרם |  |
| `telegram` | Telegram | טלגרם |  |
| `tiktok` | TikTok | טיקטוק |  |
| `linkedin` | LinkedIn | לינקדאין |  |
| `pinterest` | Pinterest | פינטרסט |  |
| `x` | X (Twitter) | X (טוויטר) |  |
| `snapchat` | Snapchat | סנאפצ'ט |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: social networks used, by population group and age (social-network users) | `isoc_media_survey_2024` | 0.1390 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who use the internet but not social networks use at most WhatsApp and Telegram and get no news from social media | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people who do not use the internet use no network or messaging app | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_networks` — Networks where they regularly follow news / רשתות שבהן מתעדכן בחדשות באופן קבוע

- **type:** `multi`
- **parents:** `news_social`, `media_age`, `media_sector`
- **distribution file:** `model/cpts/news_networks.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `whatsapp` | WhatsApp | וואטסאפ |  |
| `facebook` | Facebook | פייסבוק |  |
| `youtube` | YouTube | יוטיוב |  |
| `instagram` | Instagram | אינסטגרם |  |
| `telegram` | Telegram | טלגרם |  |
| `tiktok` | TikTok | טיקטוק |  |
| `linkedin` | LinkedIn | לינקדאין |  |
| `pinterest` | Pinterest | פינטרסט |  |
| `x` | X (Twitter) | X (טוויטר) |  |
| `snapchat` | Snapchat | סנאפצ'ט |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: news on each network among its users, by population group | `isoc_media_survey_2024` | 0.0370 | 0.0000 | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `tv_channels` — TV news channels watched regularly / ערוצי חדשות שבהם צופה באופן קבוע

- **type:** `multi`
- **parents:** `news_tv`, `media_sector`, `vote_bloc`, `media_age`
- **back-off order:** `vote_bloc` → `media_age` → `media_sector`
- **distribution file:** `model/cpts/tv_channels.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `news12` | Channel 12 | ערוץ 12 |  |
| `kan11` | Kan 11 | כאן 11 |  |
| `news13` | Channel 13 | ערוץ 13 |  |
| `channel14` | Channel 14 | ערוץ 14 |  |
| `al_jazeera` | Al Jazeera | אל-ג'זירה |  |
| `makan33` | Makan 33 | מכאן 33 |  |
| `other` | another channel | ערוץ אחר |  |

Sources: `ines_2025` (Israel National Election Studies, Tel Aviv University)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: TV news channels watched regularly, by 2022 vote bloc (Jewish and other viewers) and for Arab viewers | `ines_2025` | 0.0512 | 0.0000 | 0.05 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: people who never watch TV news watch no channel regularly | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `news_websites` — News websites visited at least weekly / אתרי חדשות שבהם מבקר לפחות פעם בשבוע

- **type:** `multi`
- **parents:** `news_sites`, `media_sector`, `vote_bloc`
- **back-off order:** `vote_bloc` → `media_sector`
- **distribution file:** `model/cpts/news_websites.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `ynet` | ynet | ynet |  |
| `n12` | N12 | N12 |  |
| `mako` | Mako | mako |  |
| `walla` | Walla | וואלה |  |
| `kan` | Kan | כאן |  |
| `haaretz` | Haaretz | הארץ |  |
| `rotter` | Rotter | רוטר |  |
| `kikar` | Kikar HaShabbat | כיכר השבת |  |
| `bhol` | Behadrei Haredim | בחדרי חרדים |  |

Sources: `agam_media_index_2024` (Agam Institute (Nimrod Nir, Dr. Gayil Talshir, Assa Shapira))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: news websites visited at least weekly by internet users, nationally and by camp | `agam_media_index_2024` | 0.0150 | — | 0.03 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `newspaper` — Main printed newspaper / העיתון המודפס העיקרי

- **type:** `table`
- **parents:** `news_print`, `media_sector`, `media_age`, `vote_bloc`
- **back-off order:** `vote_bloc` → `media_age` → `media_sector`
- **distribution file:** `model/cpts/newspaper.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `israel_hayom` | Israel Hayom | ישראל היום |  |
| `yedioth` | Yedioth Ahronoth | ידיעות אחרונות |  |
| `haaretz` | Haaretz | הארץ |  |
| `maariv` | Maariv | מעריב |  |
| `globes` | Globes | גלובס |  |
| `makor_rishon` | Makor Rishon | מקור ראשון |  |
| `besheva` | Besheva | בשבע |  |
| `hamodia` | Hamodia | המודיע |  |
| `yated_neeman` | Yated Ne'eman | יתד נאמן |  |
| `hamevaser` | Hamevaser | המבשר |  |
| `hapeles` | HaPeles | הפלס |  |
| `mishpacha` | Mishpacha | משפחה |  |
| `bakehila` | Bakehila | בקהילה |  |
| `yom_leyom` | Yom LeYom | יום ליום |  |
| `arabic` | an Arabic-language newspaper | עיתון בערבית |  |
| `none` | none (does not read printed newspapers) | אין (אינו קורא עיתונים מודפסים) | אין (אינה קוראת עיתונים מודפסים) |

Sources: `tgi_readership` (TGI Israel; figures reported by Arutz Sheva (22 July 2026) and ice.co.il (22 March 2018)); `knesset_rc_newspapers_2018` (Knesset Research and Information Center); `agam_media_index_2024` (Agam Institute (Nimrod Nir, Dr. Gayil Talshir, Assa Shapira))

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |
| Constraint: no main newspaper for people who never read printed newspapers | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |
| Constraint: people who read printed newspapers have a main newspaper | `model/constraints.yaml` | 0.0000 | — | 0.0 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `preferred_source` — Preferred news source / מקור החדשות המועדף

- **type:** `logit`
- **parents:** `news_tv`, `news_radio`, `news_print`, `news_sites`, `news_social`, `news_search`, `news_podcasts`, `media_age`, `media_sector`
- **distribution file:** `model/cpts/preferred_source.json`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `tv` | TV | טלוויזיה |  |
| `radio` | the radio | רדיו |  |
| `print` | printed newspapers | עיתונים מודפסים |  |
| `sites` | news websites | אתרי חדשות |  |
| `social` | social media | רשתות חברתיות |  |
| `search` | search engines | מנועי חיפוש |  |
| `podcasts` | podcasts | פודקאסטים |  |
| `none` | none | אין |  |

Sources: `isoc_media_survey_2024` (Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Media: preferred news source, by population group and by age (respondents who use a medium often) | `isoc_media_survey_2024` | 0.0124 | 0.0000 | 0.03 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
