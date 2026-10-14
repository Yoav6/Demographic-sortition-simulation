# How unusual? A score for each member

<!-- he-summary -->
**עד כמה יוצא דופן?** לכל משתתף מחושב ציון שמודד עד כמה מאפייניו "מתנגשים" זה בזה — לא עד כמה הם נדירים כשלעצמם. מגורים ביישוב קטן או תואר שלישי אינם חריגים בפני עצמם; חרדית שגרה ביישוב חילוני, או חרדי שהצביע לעבודה, כן. בכל שלב בהגרלה משווים את ההסתברות של מה שהאדם קיבל, בהינתן מאפייניו האחרים, לשכיחות שלו בכלל האוכלוסייה. רק מה שנדיר פי 2 ומעלה ממה שמצופה נספר, וכל שלב תורם לכל היותר 6 ביטים. הציון הכולל מוצג כאחוזון בכלל האזרחים (שגרתי, קצת יוצא דופן, יוצא דופן, יוצא דופן מאוד, חריג במיוחד), ולצידו עד שלושה מאפיינים שתרמו לו, עם הסיבה ("בהינתן מקום מגוריה") והמספרים.
<!-- /he-summary -->

## Definition

Every member's card has a **"How unusual?"** section, titled with the person's name and
gender ("How unusual is Rivka?" / "כמה יוצאת דופן רבקה?"). It shows:

* a **percentile**: the share of all citizens who are less unusual than this person (ties count
  half);
* a **tier**, by percentile:

  | Tier | Percentile | Share of citizens |
  |---|---|---|
  | Typical | below 50 | 50% |
  | Somewhat unusual | 50–80 | 30% |
  | Unusual | 80–95 | 15% |
  | Very unusual | 95–99 | 4% |
  | Exceptional | 99 and above | 1% |

* **every deviation that counts toward the score** (more than 2× less common than usual
  given the person's other traits), grouped by significance:

  | Level | Colour | Surprise |
  |---|---|---|
  | Major | red | at least 4 bits (16× less common than usual) |
  | Notable | orange | 2 to 4 bits |
  | Minor | amber | 1 to 2 bits |

  Each has the traits responsible and the two frequencies. Example: "2022 vote: Labor —
  unusual given his religiosity. People like him: 1 in 1,800; all citizens: 1 in 35." From two
  deviations on, a line counts them per level, so a score made of many small deviations is
  explained too: it is simply their sum, and each is listed. The deviations' scores add up
  exactly to the person's score.

On the card, attribute rows that carry a deviation are marked with ◆ in the colour of the
strongest one; hovering shows the explanations. (The level is also in the tooltip, so colour is
not the only cue.) The seats can also be
coloured by tier; there, the two smallest tiers are merged.

"Unusual" here means **incongruous**: the traits clash with each other. It does not mean
rare. Living in a small locality, holding a doctorate or having an uncommon name is not
unusual in itself. A Haredi woman who served in the IDF is.

## Why this measure

The model draws a person one trait at a time, each given the traits that come before it in
the network ([`model/dag.yaml`](../../model/dag.yaml)). The obvious score is the
probability of the whole person, P(x) = Π P(xᵢ | parentsᵢ), or its surprisal −log P(x). It
is the standard Bayesian-network anomaly score, but it measures **rarity**. Anyone in one of
1,200 localities, or with one of 7,000 first names, is "improbable". Das & Schneider (2007)
built their categorical anomaly detector to correct exactly this. They flag a record only for
an unlikely *combination* of values, scored by the ratio

```
r(a, b) = P(a, b) / (P(a) · P(b))  =  P(a | b) / P(a)
```

A value that is rare everywhere has r = 1. A value that the rest of the record makes unlikely
has r well below 1. Conditional anomaly detection (Song et al. 2007) frames the same idea as
judging *behavioural* attributes against what their *context* predicts. In the network,
each node's parents are its context.

Alternatives considered and rejected:

* **Typicality** (surprisal minus the node's entropy). It corrects for the number of values,
  but still flags people in small localities.
* **Probability given all other traits** (the Markov blanket), or **Shapley values**. These
  would make the attribution independent of the network's order. But redundant evidence
  hides clashes: a Haredi who votes UTJ and lives in Tel Aviv looks "Haredi given everything
  else". Shapley values also cost exponential time.

## Computation

Each **junction** is a step of the draw where the person got a value:

* every visible table, logit and set node, except single-year age, which only refines the age
  group, and the **first name**: a name is there for immersion, not as a trait, so it never
  counts. How common the name is among people like the member is computed anyway
  (`nameSurprise`) and shown in a tooltip beside the name at the top of the card;
* from the population frame, two more junctions: population group given locality, and age
  group given locality, group and sex.

Locality itself is the root, so it is never surprising on its own. Hidden helper nodes are not
judged, but they do serve as context.

For a junction with the person's value x:

```
r      = P(x | parents) / P(x)          P(x): national share among all citizens
bits   = min(6, log₂(1 / r))           1 bit = twice less common than average
score  = max(0, bits − 1)
S      = Σ score over junctions
```

* **The threshold (1 bit).** Being up to twice less common than average is noise. Without
  it, dozens of slightly less common traits add up and drown a single real clash.
* **The cap (6 bits = 64×).** Very small probabilities partly reflect how sparse survey
  cells are smoothed (see each node's Estimation section), not data. One such value should
  not decide the score.
* **Common values cannot score high.** Because P(x) ≤ 1, r ≤ 1/8 forces P(x | parents)
  ≤ 1/8.
* **Deterministic steps score nothing.** When a parent fixes the value (e.g. "no newspaper"
  for someone who never reads printed papers), r ≥ 1 automatically.
* **Values that do not apply.** Examples: the occupation of someone not employed, the degree
  field of someone without a degree. These are listed under `not_applicable` in dag.yaml.
  They score nothing; the step that decided them (e.g. labour-force status) carries any
  surprise. For the other values, both probabilities are taken among the people the node
  applies to. Otherwise every employed person's occupation would look 1.6× "more likely"
  than average.
* **Sets** (networks used, TV channels, news sites). Each item counts whether it is present
  ("watches Channel 14") or missing ("no WhatsApp"). Within an enclosing set, only items the
  person has there count. A set is one junction, scored by its most surprising item;
  otherwise the many items of the media sets would dominate the score.

**National shares** are computed exactly from the frame and the distribution files by
`popsim build marginals` and written to `model/marginals.json`. The bundle carries them as
`marginal`. This follows the same rules as the model's joint distributions
([`pipeline/popsim/estimate/joint.py`](../../pipeline/popsim/estimate/joint.py)).
The media nodes are computed on one shared joint of their common parents. The preferred-source
logit is averaged exactly over the combinations of the seven media frequencies, which are
independent given those parents.

The score is computed by
[`packages/sampler/src/unusual.ts`](../../packages/sampler/src/unusual.ts), the same code in
the website and the command-line sampler. It is stored with each member of the published
assembly.

## Calibration

The percentile is computed against 20,000 people drawn from the model with a fixed seed
(20261014). They give 101 breakpoints of S, and a person's score is placed among them like
the other percentiles in the model. About 12% of citizens score exactly 0. Approximate
breakpoints:

| Percentile | 10 | 25 | 50 | 75 | 90 | 95 | 99 |
|---|---|---|---|---|---|---|---|
| S (bits) | 0 | 0.3 | 1.0 | 2.1 | 3.3 | 4.2 | 6.2 |

## Explanations

A reason names the **traits that made the value unlikely**. For each parent of the junction,
the probability of the person's value is recomputed with that parent replaced by its national
distribution: Σᵥ P(parent = v) · P(x | parents, with that one set to v). The parents whose
removal makes the value at least twice as likely are named, the most decisive first, at most
two. If none reaches that, the strongest one is named.

For **ordered** variables (earnings and household income brackets, number of children, literacy
level, highest diploma and self-rated health, where "other diploma" is off the scale and gets no direction, and health is "better" or "worse" than usual rather than below or above; flagged `ordered: true` in dag.yaml) the reason also says whether the value is *below*
or *above* what is usual, what is usual (the median of the distribution given the person's
other traits, e.g. "typical for people like her: ₪10,001–14,000"), and the share of people like
them on the far side ("97% of them are above this"). That is how much: the distance in
brackets, and how lopsided it is.

Hidden helpers are named by the visible trait they stand for:

* the locality's religiosity profile, immigrant share and electoral area → place of residence;
* the age groupings of the media and vote nodes → age;
* sector → religiosity;
* education level → education;
* vote bloc → vote;
* origin group and continent of birth → origin;
* current service → military or national service.

Frequencies are shown as "1 in N" when both are below 20%, and as percentages otherwise.

### Worked example

**Where she lives: below the threshold.** Take a Jewish Haredi woman aged 30–34.

* In localities like Bnei Brak, 79% of women like her are Haredi. Against 8.7% of all
  citizens, r ≈ 9: the opposite of a surprise.
* In localities like Tel Aviv-Yafo, the model makes 4.6% of them Haredi. That gives
  r = 0.53, or 0.9 bits, under the 1-bit threshold, so her religiosity alone does not make
  her unusual.
* The religiosity node puts Haredim at no less than about 2–3% of Jewish women of that age
  anywhere. So even in the most secular localities, being Haredi is at most about 1.6 bits
  of surprise (see Limitations).

**Strong clashes.** One person in a 20,000-person test sample is a 31-year-old Haredi woman:

* *never married*: 1 in 340 among Haredi women her age, against 27% of all citizens. That is
  6.6 bits, capped at 6.
* *served in the IDF*: 1.2% of people like her, against 51% nationally, or 5.4 bits.

With these and a smaller surprise, S = 11.6, above the 99th percentile: "Exceptional".

## Validation

* `popsim validate` checks that the national shares in `model/marginals.json` match the
  frequencies in a 200,000-person sample drawn by the TypeScript sampler. There is a
  chi-square test per node and one per set item; the check passes when the smallest
  Bonferroni-adjusted p-value is above 0.001.
* The sampler's unit tests (`packages/sampler/test/unusual.test.ts`) check:
  * on a toy model: the threshold and the cap, values that do not apply, sets, the frame
    junctions, and that a cause given by a hidden helper is named by its visible trait;
  * on the published model: that a fresh sample of 20,000 people falls into the tiers within
    1.5 points of 50/30/15/4/1%;
  * that the same Haredi woman scores higher when moved from Bnei Brak to Tel Aviv-Yafo, with
    her locality as the cause;
  * that every explanation renders in Hebrew and English.

## Limitations

* **Only the network's own clashes can be detected.** The score knows only the dependencies
  the model represents. For example, education does not depend on locality in the model, so
  "a doctorate in a peripheral town" cannot be unusual, whatever the reality. Combinations no
  source measures jointly are filled in by conditional independence (see
  [the overview](../../METHODOLOGY.md#8-what-this-model-is-not)), and are therefore never
  surprising.
* **The order of the draw decides who gets the blame.** In a clash between locality and
  religiosity, religiosity is the junction that scores, because it is drawn after locality.
  The reason text names both sides ("Haredi — unusual given where she lives").
* **Smoothing.** Small survey cells are shrunk toward broader groups. This makes extreme
  combinations less extreme than reality (e.g. the Haredi floor of about 2–3% in secular
  localities, from the religiosity profile of localities), and very rare outcomes partly an
  artefact of the pseudo-counts (hence the cap).
* **A national baseline.** Values that exist only in one population group (e.g. the Arab
  religiosity scale) have small national shares, so they are rarely surprising.
* **Media habits weigh in.** Even with one junction per set, the media nodes are many; an
  unusual news diet is a frequent reason. That reflects the model's detail on media, not
  their importance.
* The calibration sample has 20,000 people, so percentiles near 100 are accurate to roughly
  ±0.1.

## References

* K. Das and J. Schneider, *Detecting anomalous records in categorical datasets*, KDD 2007,
  pp. 220–229.
  The r-value is restated in K. Das, J. Schneider and D. B. Neill, *Anomaly pattern detection
  in categorical datasets*, KDD 2008.
* X. Song, M. Wu, C. Jermaine and S. Ranka, *Conditional anomaly detection*, IEEE TKDE 19(5),
  2007.
