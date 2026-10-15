# Methodology

<!-- he-summary -->
**בקצרה:** המודל הוא רשת בייסיאנית — שרשרת של טבלאות הסתברות מותנית. בבסיס עומדת "מסגרת אוכלוסייה": מספר האזרחים בני 18+ המתגוררים בישראל, לפי יישוב, קבוצת אוכלוסייה, מין וקבוצת גיל (על בסיס נתוני הלמ"ס לסוף 2024, בניכוי תושבי קבע שאינם אזרחים במזרח ירושלים ובגולן). כל מאפיין נוסף (דתיות, שם, השכלה, הצבעה...) נדגם מטבלה המותנית במאפיינים שכבר נקבעו. כל טבלה נבנית מנתונים מפורסמים (הלמ"ס, ועדת הבחירות, הסקר הלאומי של הבחירות ועוד), מכוילת לסיכומים הרשמיים ומתועדת בנפרד. הדגימה דטרמיניסטית: אותו סיד מפיק תמיד את אותם אנשים.
<!-- /he-summary -->

This page explains how the model turns public statistics into 150 synthetic members of a
citizens' assembly. Every attribute has its own page (see the list on the left, or
`docs/methodology/`) with its sources, estimation steps, assumptions, validation results and
known limitations. Every source is listed, with checksums, in [SOURCES.md](SOURCES.md).

## 1. Who is in the pool

The assembly is drawn from **Israeli citizens aged 18 and over who live in Israel**,
including residents of Israeli localities in the West Bank. Excluded:

* citizens living abroad. They remain on the voter roll (roughly 0.5–0.6 million people), but
  are not part of the CBS resident population and could not realistically attend an assembly;
* permanent residents who are not citizens — most Palestinians of East Jerusalem
  (about 95%) and most Druze of the Golan Heights;
* foreign nationals (labour migrants, asylum seekers), whom CBS counts separately.

Decision record: [docs/decisions/0001-target-population.md](docs/decisions/0001-target-population.md).

## 2. The model: a Bayesian network of conditional tables

A full joint table of all attributes is impossible to estimate — no public data source
cross-tabulates locality × religiosity × income × vote × health. Instead the joint
distribution is factorised into a chain of conditional distributions, each of which *is*
supported by data:

```
frame:          P(locality, population group, sex, age band)       (root, a joint table)
derived:        district, type of locality, sector                   (deterministic)
age:            P(single-year age | group, sex, age band)
religiosity:    P(religiosity | group, sex, age band, locality profile)
first name:     P(name | group, sex, birth cohort)
origin:         P(origin | group, age band, religiosity, immigrant share of locality)
marital status: P(status | group, religiosity, sex, age band)
children:       P(children | group, religiosity, sex, age band, marital status)
living with:    P(partner / parents / own children / relatives / independently | group, religiosity, sex, age band, marital status, has children)
education:      P(diploma | group, religiosity, sex, age band, continent of birth)
service:        P(IDF / national / none | group, religiosity, sex, age band, continent of birth)
labour status:  P(status | in service, group, religiosity, sex, age band, education)
studies:        P(not studying / degree / yeshiva / post-secondary / other | group, religiosity, sex, age band, labour status, education)
fields:         P(field of degree | diploma, sex, occupation, age group, religiosity group); P(field of studies | studies, sex, field of degree)
occupation:     P(occupation | labour status, group, religiosity, sex, education)
industry, status at work, earnings, household income (by living arrangement), home ownership
health:         P(self-rated health | group, religiosity, sex, age band, education) → chronic illness → disability
vote (2022):    P(list or abstention | electoral area, religiosity, age, education, origin group)
media:          internet use; political-news frequency (by vote bloc) → how often each of seven media
                (by age, group, sex, education) → networks used, news on them; TV channels
                (by vote bloc, age); main printed newspaper (by group, age)
literacy:       P(proficiency level | group, religiosity, sex, age band, education) → score → percentile
```

Each node's parents are chosen because (a) they strongly affect it and (b) a source
tabulates the node against them. The network structure lives in
[`model/dag.yaml`](model/dag.yaml); each node's table is a CSV file in `model/cpts/` with one
row per parent combination and value. The whole model compiles into a single JSON bundle
(`model/build/model.json`) that the website and the command-line sampler share.

## 3. Estimation toolkit

| Situation | Method |
|---|---|
| A published cross-tab with exactly the node's parents | used directly, normalised to conditional probabilities |
| Several partial tables (e.g. religiosity by sex, and by age, and in total) | **iterative proportional fitting (IPF)**: start from a seed table and rescale alternately to each known margin until all match |
| Survey cross-tabs with thin cells (CBS Social Survey) | **shrinkage toward a main-effects fit**, with the number of respondents behind each cell taken from the published standard errors |
| Two survey tables conditioning on different variables (employment by religiosity, and by education) | **combining over the model's own population**: IPF over the model's joint counts of the two conditioning variables |
| Survey microdata (INES, ISOC-IL) | weighted logits with a ridge penalty, or cross-tabs with thin cells shrunk toward broader groups (pseudo-counts) |
| Two surveys that each measure part of what is needed (media use by demographics in one, its link to political news in the other) | **fusion by IPF**: in each cell, a table fitted to both surveys' margins, starting from the association the second survey shows |
| A locality-level quantity with no direct source (religiosity mix) | **ecological inference** from election results (see the religiosity page) |
| Model output vs. official totals | **calibration**: CPTs are raked until the model's implied totals match the official ones |

**IPF.** For a seed table *x* and margins *m₁…m_k*: repeat `x ← x · m_j / (sum of x over the
axes not in m_j)` for each margin in turn until the largest relative change is below 10⁻⁹.
Cells that are zero in the seed (structural zeros, e.g. a Haredi Muslim) stay zero.

**Respondents behind a survey cell.** The CBS table generator reports a weighted count and its
relative standard error (RSE) for every cell. For a cell that is a small part of the survey,
RSE² ≈ 1 / (respondents in the cell) — design effects included — so a row of a table rests on
*n* = Σ 1/RSE² respondents.

**Shrinkage toward a main-effects fit** (`survey.main_effects`). Take a table such as
religiosity × age group × marital status for one sex. Its *main-effects fit* is the table, fitted
by IPF to the religiosity × status, age × status and religiosity × age margins, in which
religiosity and age each shift the distribution of marital status but do not interact. Each row
is then

```
p(status | religiosity, age) = (n · observed share + k · main-effects fit) / (n + k),   k = 10
```

so a row with many respondents keeps its own pattern, and a thin row (Haredi men aged 20–24)
borrows from Haredi men of all ages *and* from the age pattern of everyone — rather than from
all men of that age, which would erase the very differences the model is about. Half a
pseudo-respondent per row, spread like the whole table, keeps categories that a small group's
sample happened to miss possible but rare. The 45–64 age groups are then lightly smoothed
(¼ previous + ½ own + ¼ next group).

**Combining two tables over the model's population** (`common.combine`). Given
P(t | a) and P(t | b) — e.g. employment by religiosity and by education — and the model's own
population counts W(a, b), computed exactly from the frame and the tables already estimated
(`joint.joint`), IPF finds counts X(a, b, t) whose sums over t are W(a, b), over b are
W(a)·P(t | a), and over a are W(b)·P′(t | b), where P′ is P(t | b) adjusted so that both tables
imply the same totals. It starts from the naive-Bayes product W(a,b)·P(t|a)·P(t|b)/P(t), so a
and b interact only as much as the data require (the maximum-entropy solution). A test in the
pipeline checks that it recovers a known logit-additive truth exactly.

**Fusing two surveys** (media). ISOC-IL measures how often people use each medium, by age,
group, sex and education, but not how closely they follow politics; INES 2025 measures both
political-news frequency and the media used for it. In each demographic cell, the table of
political-news frequency × medium frequency is fitted by IPF to the model's distribution of
political-news frequency and to the ISOC distribution of the medium, starting from INES's
probability of using the medium at each political-news frequency. The cell keeps the ISOC
distribution exactly and takes its association with politics from INES (see the media page).

## 4. Citizenship and other adjustments

* **East Jerusalem.** CBS counts all of Jerusalem's ~401,000 Arab residents. Only those who are
  citizens can vote: their number is measured from the 2022 voter roll in polling stations
  where Arab parties won a majority, scaled up by the share of Arab-party votes cast in those
  stations (≈ 28,500 adults).
* **Golan Druze villages** (Majdal Shams, Mas'ade, Buq'ata, Ein Qiniyye): adults = eligible
  voters on the 2022 roll (≈ 14–18% of adult residents are citizens).
* **Bedouin "tribe" localities** (unrecognised or dispersed communities) have no CBS
  population figure; their adults are taken from the voter roll, with the age-sex profile of
  the Bedouin regional councils.
* **Survey data** on "Arabs" from CBS includes East Jerusalem. All Social Survey tables used for
  Arabs are therefore queried for Arabs *outside the Jerusalem district*; where only figures
  including East Jerusalem exist, the limitation is noted on the node's page.

## 5. Sampling and reproducibility

* The sampler walks the nodes in order and draws each from its table given the person's
  parents (ancestral sampling) by inverse-CDF on **integer weights** (probabilities × 10⁹), so
  cumulative sums are exact in every language.
* Every random number is a pure function of *(seed, person number, node, draw number)*: a
  counter-based hash (`lowbias32` chained over the inputs; `packages/sampler/src/rng.ts`, with
  a Python twin checked against shared test vectors). Person #i is therefore identical whether
  1 or 150 people are drawn, and changing one node's table never reshuffles another node's
  random numbers.
* **Set-valued attributes** (social networks, TV channels) include each item with its own
  probability given the parents. A set nested in another (the networks someone reads news on,
  within the networks they use) can include an item only if the person has it in the
  enclosing set; its probabilities are conditional on that.
* The **published assembly** uses a seed taken from the [drand](https://drand.love) public
  randomness beacon at a time fixed in advance (2026-10-13 00:00 UTC, round 6,547,286):
  seed = the first 8 hex digits of the beacon's output. Anyone can verify the round at
  <https://api.drand.sh/public/6547286> and regenerate the assembly. See
  [docs/decisions/0004-default-assembly-seed.md](docs/decisions/0004-default-assembly-seed.md).
* **Data acquisition is scripted.** `popsim fetch` downloads every source and pins its
  SHA-256 in `sources.lock.json`; a changed upstream file stops the build until accepted with
  `--update`. Pages that need a browser are scripted with Playwright; values that exist only
  as charts are transcribed into `data/manual/` with page references.

## 6. Validation

`popsim validate` runs three kinds of checks and writes `reports/validation.json`; each node's
page shows the checks that cover it.

1. **Survey margins.** The distribution the model implies for a variable — computed exactly
   for the survey's universe (ages 20+) — is compared with the survey's weighted shares at cuts
   coarser than those used in estimation (e.g. by religiosity and sex, pooling ages). Model
   shares are age-standardised to the survey's age mix within each cell, so the check tests the
   estimated conditionals; the age composition itself is checked separately. A check passes when
   no cell differs by more than its tolerance beyond two standard errors of the survey share
   (computed from the respondents behind the cell, as if the model were right). For survey
   microdata (ISOC-IL, INES 2025) each respondent gets the model's prediction for their own
   cell, so the comparison is standardised to the respondents' mix, and cells with fewer than
   30 respondents are not judged.
2. **Sampler.** A sample of 1,000,000 people drawn by the TypeScript sampler — the code the
   website runs — must reproduce every table given its parents: a chi-square test for each node
   and each of its most common parent combinations (each item, for set-valued nodes), passing
   when the smallest Bonferroni-adjusted p-value is above 0.001.
3. **Constraints.** The sample must contain no combination forbidden in
   [`model/constraints.yaml`](model/constraints.yaml) (no degree at 18–19, no retiree under 65,
   household income at least the person's own earnings, …).

The pipeline's unit tests check the RNG, IPF, the bundle's structure and that the published
assembly is reproduced exactly from its seed.

## 7. How unusual is each member?

Every member also gets a **"How unusual?"** score: how much their traits clash with each
other, not how rare they are. At each step of the draw, the probability of what the person
got, given their other traits, is compared with its national share (Das & Schneider's
r-value). Steps more than twice less likely than average add their surprise in bits (capped at
6). The total is shown as a percentile among all citizens, in five tiers, with every
deviation listed by significance and the traits behind it. Details, examples and limitations:
[docs/methodology/unusual.md](docs/methodology/unusual.md).

## 8. What this model is not

It is a model of the *distribution* of attributes in the eligible population, built from
aggregates. Combinations that no source measures jointly are filled in by the assumptions of
the network structure (conditional independence given the parents). The characters are
synthetic; none corresponds to a real person. Each node's page lists its specific limitations.
