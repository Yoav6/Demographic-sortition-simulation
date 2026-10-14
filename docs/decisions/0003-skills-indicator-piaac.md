# 0003 — The "intelligence" indicator is PIAAC literacy, not IQ

* Status: accepted (2026-10)

## Context

The project brief asked for an intelligence indicator "if cross-sectionally available". No
representative measurement of intelligence (IQ) of Israeli adults exists, and published national
IQ estimates are contested and not broken down by population group, age or education. The OECD
Survey of Adult Skills (PIAAC) tests a representative sample of adults aged 16–65 in literacy,
numeracy and adaptive problem solving; Israel took part in 2014–15 and 2022–23, with results
published by population group (Bank of Israel), age, education and gender (OECD).

## Decision

Model **literacy proficiency** on the PIAAC scale (level, score and percentile), labelled
everywhere as a modelled skills estimate — never as intelligence or IQ. The open public-use
microdata require registration with the OECD and are not used; the model is calibrated to
published means and validated against published distributions instead.

## Consequences

* The indicator reflects schooling, language and practice as much as ability; the methodology
  page says so, and the site's labels read "modelled literacy".
* Ages over 65 (outside PIAAC) are extrapolated.
* If the public-use file is obtained later (free registration at the OECD), the model can be
  re-estimated from microdata through the restricted-data path.
