# Living arrangement

<!-- he-summary -->
**הסדר מגורים:** עם מי האדם גר — עם בן או בת זוג, עם ההורים, עם ילדיו (ללא בן או בת זוג), עם קרובי משפחה אחרים, או באופן עצמאי. נגזר מסוג משק הבית ומהשאלה אם בן הזוג גר במשק הבית בסקר החברתי 2024, לפי קבוצת אוכלוסייה, דתיות או דת, מין, גיל, מצב משפחתי והאם נולדו לאדם ילדים. מי שגר עם הוריו מדווח על משק הבית של הוריו, ולכן הכנסת משק הבית והבעלות על הדירה תלויות בהסדר המגורים.
<!-- /he-summary -->

## Definition

Whom the person lives with, in the CBS's household terms:

* **`partner`** — with a spouse or partner (the survey's "lives with partner in the household";
  this includes unmarried couples, and married people whose spouse lives with them).
* **`parents`** — in a family household, without a partner and without children of their own:
  with their family of origin. Before 65 this is almost always the parental home.
* **`own_children`** — in a family household without a partner, having had children: a single
  parent, or an older person living with an adult child.
* **`relatives`** — the same as `parents` from age 65 on, when the household is mostly siblings
  or other relatives rather than parents.
* **`independent`** — a one-person household, or a household of unrelated people.

A CBS household is people who share a dwelling and a food budget. Flatmates who buy food
separately are therefore *separate one-person households*, so `independent` covers both people
who live alone and most people who share a flat; the website says "lives independently" rather
than "alone". A CBS family is a couple, a parent and child, or siblings without partners or
children.

`has_children` is a hidden helper: whether `children` is above zero.

## Why these parents

`marital_status` (the married live with their spouse; the never-married live with parents
until they move out), `has_children` (a parent without a partner usually lives with their
children; someone childless cannot), `age_band` (moving out is a matter of age),
`group` and `religiosity` (at 25–29, 88% of never-married Haredi Jews still live with their
parents, against 59% of secular ones; unmarried couples living together are almost only
secular or traditional Jews and "others"), and `sex` (Arab men leave home much later than Arab
women, who usually leave on marriage).

## Sources

* `src:cbs_social_survey_2024` — household type (one person; non-family; one family; family
  with others) × lives with partner in the household × marital status, by religiosity × sex ×
  age group for Jews (`living_jews_*`), sex × age for "others" (`living_others_*`) and
  religion × sex × age for Arabs outside the Jerusalem district (`living_arabs_*`). Each table
  is queried twice, for people who have had children (`_children`) and for those who have not
  (`_childless`). Ages 20+.

## Preprocessing

Each respondent's arrangement is derived in this order: lives with partner → `partner`;
one-person or non-family household → `independent`; has had children → `own_children`; aged
65+ → `relatives`; otherwise `parents`. "Unknown" answers (under 1%) are dropped. Marital
status is mapped as on the marital-status page (separated people count as married).

## Estimation

Each marital status × children slice is estimated on its own. Within it, a religiosity (or
religion) × age-group table for each sex is shrunk toward its main-effects fit with 10
pseudo-respondents, and the 45–64 groups are lightly smoothed, as on the marital-status page
and in [METHODOLOGY.md](../../METHODOLOGY.md) §3. Fitting slices separately means a row with no
respondents, such as never-married Haredi women aged 30–34, borrows from people in the same
family situation, few of whom live with a partner. Pooling all slices would let it borrow
from the married.

Arrangements that are impossible by definition are set to zero: `own_children` without
children, `parents` from 65 and `relatives` before 65.

**18–19-year-olds** use the 20–24 distribution. CBS counts soldiers in compulsory service as
members of their parents' household, so most 18–19-year-olds live with their parents in this
sense.

## Calibration

None; the survey is the target.

## Validation

Model shares of all adult citizens: 62% live with a spouse or partner, 19% with their parents,
12% independently and 6% with their children without a partner.

Living with parents by age: 88% at 18–19, 78% at 20–24, 45% at 25–29 and 15% at 30–34.
Among never-married Jews aged 25–29: Haredi 88%, Dati 82%, traditional-religious 80%,
traditional 77%, secular 59%. A further 18% of never-married secular Jews of that age live
with a partner.

For comparison with published figures (not a formal check, since they are from 2018):

* The CBS reported from the 2018 Social Survey that about a third of 25–34-year-olds lived with
  their parents: 27% unmarried and 5% married
  ([Maariv](https://www.maariv.co.il/news/israel/Article-704232)). The model gives 29.5% and
  0.7% for 2024. The married share is lower because a married couple living in the parents'
  home counts as `partner` here.
* A CBS study using Labour Force Survey data reported, for 25–29-year-olds in 2018, 40.3% of
  Jews (apparently men) and 26.9% of Jewish women, 66.4% of Arab men and 33.0% of Arab women
  living with their parents ([Globes](https://en.globes.co.il/en/article-1001361860)). The
  model gives 50%, 38%, 69% and 30% for 2024. The gap for Jews is partly the rising trend the
  study reports, and partly that a household of siblings counts as `parents` here.

The survey comparisons are in the generated table below.

## Limitations

* `independent` cannot separate living alone from sharing a flat, because the survey treats
  flatmates with separate food budgets as separate households.
* `parents` includes the uncommon case of adult siblings living together without parents, and
  `own_children` includes single parents living with their children in their own parents' home.
* A married person whose spouse does not live with them (separated, or working elsewhere) falls
  into one of the other categories.
* Arab rows depend on religion, not religiosity. Cells for Arabs, religious Jews and people
  over 35 who have never married are thin and lean on the shrinkage prior.

## Changelog

* 2026.10.0 — first version.

<!-- BEGIN GENERATED (popsim docs) -->

### Model summary (generated)

#### `has_children` — Has had children / נולדו ילדים

- **type:** `lookup` · hidden helper
- **parents:** `children`
- **distribution file:** `model/lookups/has_children.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `yes` | yes | כן |  |
| `no` | no | לא |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

#### `living_arrangement` — Living arrangement / הסדר מגורים

- **type:** `table`
- **parents:** `group`, `religiosity`, `sex`, `age_band`, `marital_status`, `has_children`
- **back-off order:** `religiosity`
- **distribution file:** `model/cpts/living_arrangement.csv`

| id | English | עברית (m) | עברית (f) |
|---|---|---|---|
| `partner` | with spouse or partner | עם בן או בת זוג |  |
| `parents` | with parents | עם ההורים |  |
| `own_children` | with own children | עם הילדים |  |
| `relatives` | with other relatives | עם קרובי משפחה אחרים |  |
| `independent` | independently | באופן עצמאי |  |

Sources: `cbs_social_survey_2024` (Central Bureau of Statistics (CBS) - Social Survey)

Validation:

| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |
|---|---|---|---|---|---|
| Living arrangement of Jews by religiosity and sex (20+) | `cbs_social_survey_2024` | 0.0089 | 0.0000 | 0.03 | ✅ pass |
| Living arrangement of Jews by marital status and sex (20+) | `cbs_social_survey_2024` | 0.0741 | 0.0000 | 0.03 | ✅ pass |
| Living arrangement of Arabs by religion and sex (20+) | `cbs_social_survey_2024` | 0.0568 | 0.0000 | 0.04 | ✅ pass |
| Sampler reproduces every table given its parents (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0402 | — | 0.001 | ✅ pass |
| National shares used by the unusualness score match the sample (n = 1,000,000; tolerance: adjusted p-value) | `model` | 0.0013 | — | 0.001 | ✅ pass |

Sample: 1,000,000 people, seed 1, model 2026.10.0. ¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). ² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).

<!-- END GENERATED -->
