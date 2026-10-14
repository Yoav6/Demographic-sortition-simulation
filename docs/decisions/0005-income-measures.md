# 0005 — Income: earnings for the employed, household income for everyone

* Status: accepted (2026-10)

## Context

The economic attributes requested were salary, wealth, and a population percentile. The CBS
Social Survey's personal gross income question is asked **only of employed persons** (everyone
else is "not relevant"), so it measures earnings from work; household gross income is asked of
everyone; there is no individual wealth data in any open source.

## Decision

* `income` / `income_amount` / `income_percentile`: gross monthly earnings of the employed, with
  their percentile among employed citizens; "not employed" (no number) for everyone else.
* `household_income` / `household_income_amount` / `household_income_percentile`: for everyone,
  with the percentile among all adult citizens — the economic-status measure that also covers
  retirees, students and homemakers.
* `home_ownership` of the household is the only wealth indicator.
* Amounts inside a bracket are drawn log-uniformly (Pareto tails for the open top brackets);
  earnings never exceed the household's bracket, and household income is never below the
  person's earnings.

## Consequences

* Pensions and allowances of people who are not employed appear only through household income.
* Displayed amounts within a bracket are modelled, not observed; percentiles are exact ranks in
  the simulated population whatever the within-bracket shape.
