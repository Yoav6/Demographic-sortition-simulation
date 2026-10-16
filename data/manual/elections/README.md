# Election party maps (manual)

`knesset25_parties.csv` maps the ballot letters used as column headers in the Central Elections
Committee result files (`expc.csv`, `expb.csv`) to party ids used in the model. Source: the
official list of candidate lists for the 25th Knesset
([votes25.bechirot.gov.il](https://votes25.bechirot.gov.il/); [`src:cec_knesset25`](../../../SOURCES.md#src-cec_knesset25)). Lists that did
not pass the threshold are grouped as `other_party` (all letters not listed here).

`bloc_2022` follows the government formed after the election ([Netanyahu's 37th government](https://en.wikipedia.org/wiki/Thirty-seventh_government_of_Israel):
Likud, Religious Zionism (later split into RZ/Otzma/Noam), Shas, UTJ) vs. the rest.
