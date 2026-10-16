# 0001 — Target population: adult citizens living in Israel

* Status: accepted (2026-10)

## Context

A citizens' assembly is drawn from people who could serve on it. Three candidate pools exist:
everyone on the voter roll (citizens 18+, including roughly 0.6 million living abroad — our
estimate, see below; no official count is published), all
adult residents (including non-citizen permanent residents of East Jerusalem and the Golan, and
foreign nationals), or adult citizens who live in Israel.

## Decision

The pool is **Israeli citizens aged 18 and over who live in Israel**, including residents of
Israeli localities in the West Bank. Residents abroad, non-citizen permanent residents and
foreign nationals are excluded.

## Consequences

* The frame starts from CBS resident population figures (end of 2024; [`src:cbs_local_authorities_2024`](../../SOURCES.md#src-cbs_local_authorities_2024)) and removes non-citizens:
  East Jerusalem Arabs except the ~5% who are citizens (estimated from the 2022 voter roll in
  Arab-majority polling stations), and non-citizen Golan Druze (adults = eligible voters).
* Election turnout is expressed relative to eligible *residents*, which is higher than turnout
  relative to the roll (77.5% vs 70.6% in 2022; [`src:cec_knesset25`](../../SOURCES.md#src-cec_knesset25)). The same two figures give
  the estimate of citizens abroad: 6.79 million on the roll × 70.6% / 77.5% ≈ 6.18 million
  eligible residents, so about 0.6 million on the roll live abroad.
* CBS survey figures for Arabs include East Jerusalem; survey tables are therefore queried for
  Arabs outside the Jerusalem district.
