# 0006 — Media habits from the ISOC-IL survey, tied to politics through INES 2025

* Status: accepted (2026-10)

## Context

Media habits could be described from two INES 2022 questions (how often the person follows
political news, overall and on social networks) and the favourite TV news broadcast by
political camp, hand-read from the charts of the Agam Institute's media index. The Israel
Internet Association (ISOC-IL) and the Technion then published the
respondent-level data of a 2024 survey of news consumption: how often people get news from
each of seven media, which social networks they use and on which they read news, for 1,005
internet users including Haredi and Arab respondents. Publication is permitted with credit.

No single source covers everything:

* ISOC-IL asks about media *types* only (no channel, newspaper or site names), covers
  internet users only, has no weights, and does not ask about politics.
* INES 2025 asks how often people follow political news, which media they used for it in the
  past week, and which TV channels they watch regularly — including Al Jazeera and Makan 33 —
  with the 2022 vote, for all adult citizens, weighted.
* Agam gives the favourite broadcast by camp, and named news websites, only as charts and
  without Arabic-language media.
* No public source names the newspapers people read except TGI, the media industry's
  readership survey, whose headline figures (by title, and in 2018 by age) are reported in
  the press.

## Decision

* The seven media, networks used and news on networks come from the ISOC-IL respondents,
  conditioned on age group, population group, sex, education and internet use.
* They are tied to political-news frequency (and through it to the 2022 vote) with the
  association INES 2025 shows between that frequency and using each medium, by IPF in each
  demographic cell, so that each cell keeps the ISOC distribution exactly.
* TV channels come from INES 2025 (channels watched regularly, several per person) rather
  than Agam's favourite broadcast. Agam is used only for named news websites, the one thing
  no other source gives.
* The main printed newspaper comes from TGI exposure by title, with each title's 2018 age
  profile, and from the Haredi TGI for Haredim. No public source breaks readership down by
  vote, so the lean of Yedioth Ahronoth and Haaretz is borrowed from their websites' readers
  (Agam).
* The preferred news source comes from ISOC-IL, among the media the person uses most often.

## Consequences

* Media habits vary by age and population group as the survey data do, and Arab citizens
  have TV channels, Arabic-language ones included.
* The TV, radio and newspaper habits of people who do not use the internet are extrapolated
  from internet users who use no social platform.
* The newspapers' political lean is probably understated: website readers are less partisan
  than print readers.
* i24NEWS and Channel 9 are counted under "another channel", as in INES.
