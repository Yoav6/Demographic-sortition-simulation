# TGI newspaper readership — hand transcription

TGI is the Israeli media industry's readership survey. Its data are sold to subscribers; only
the headline figures reach the public, through press reports. The figures the model uses are
transcribed here with the sentence they come from.

## titles.csv

Average-issue exposure ("read or browsed the last issue") by title, in percent of the survey
population.

* `tgi_2025_26` — general TGI, July 2025 – June 2026: a representative sample of Jewish adults
  aged 18+ (about 5,000 respondents). Reported by Arutz Sheva on 22 July 2026,
  <https://www.inn.co.il/news/702128> (`tgi_readership` in `sources.yaml`). `weekday` is an
  average weekday issue (Globes: Monday–Thursday; Maariv: *Maariv HaBoker*); `weekend` is the
  Friday edition.
* `tgi_haredi_2017` — the Haredi TGI, a separate survey of the Haredi sector, 2017 (the latest
  release found online). Reported by ice.co.il on 22 March 2018,
  <https://www.ice.co.il/media/news/article/738702>.

Titles that the latest release does not report (Calcalist, TheMarker, Maariv's mid-week
*Maariv HaShavua*) are not modelled.

## age_profile_2018.csv

Weekday exposure by age group, TGI first half of 2018, from tables 2 and 4 of a Knesset
Research and Information Center document of 7 November 2018 (`knesset_rc_newspapers_2018`;
the PDF is pinned by `popsim fetch`). The model uses only the *relative* age gradient of each
title; the levels come from `titles.csv`.
