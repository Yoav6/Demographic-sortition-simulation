# Agam Institute Media Index (December 2024) — hand transcription

Source: [`src:agam_media_index_2024`](../../../SOURCES.md#src-agam_media_index_2024) (the PDF is downloaded and checksummed by
`popsim fetch`). The report publishes its results only as charts, so the values used by the
model are transcribed here by hand, with the page they come from.

## favorite_news.csv

"Which news broadcast do you most like to watch?" (באיזו מהדורת חדשות אתה הכי אוהב לצפות?)

* `all` — page 11, all respondents (1,201 citizens aged 18+, of whom 325 Arab).
* `coalition` / `opposition` — page 12, by current voting intention (supporters of coalition vs
  opposition parties).

`how_read`: `labelled` values are printed on the chart. Bars too small to carry a label (i24NEWS,
Channel 9, other) are estimated from the axis and are approximate (±0.5 points); `all` lists only
the five broadcasts shown, and the remainder to 100% is recorded as `other`. Shares are
renormalised to 100% in the model.

The report does not cover Arabic-language media, so these figures are used only for Jewish and
"other" citizens.

## news_sites.csv

"How often do you visit each of these news sites?" — page 14, all respondents, in percent:
several times a day, daily, several times a week, once a week, once a month, never. All values
are printed on the chart (the smallest without a % sign). The chart is titled "top
10" but shows nine sites.

## news_sites_by_camp.csv

Mean visit frequency on the same scale (1 = never … 6 = several times a day) — page 15, a line
chart without value labels, read from the axis (±0.03): all Israelis, Jews, Arabs, right-wing
voters and liberal voters (Agam's "מצביעי ימין" and "מצביעים ליברליים", by current voting
intention). Check: the means implied by page 14 (ynet 3.28, Haaretz 1.64, Rotter 1.60) agree
with the "all" line.

`favorite_news.csv` (pages 11-12) is kept for reference; the model takes TV channels from INES 2025.
