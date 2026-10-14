# 0004 — The published assembly's seed comes from a public randomness beacon

* Status: accepted (2026-10)

## Context

The site shows one pre-drawn assembly to every visitor. If its seed were chosen by us, we could
in principle try seeds until we liked the result. Real lotteries avoid this by committing in
advance to a source of randomness nobody controls.

## Decision

The seed is derived mechanically from the **drand** public randomness beacon (mainnet, chain
`8990e7a9…`): the beacon's output at a fixed time, seed = the first 8 hexadecimal digits as an
unsigned 32-bit integer. `popsim seed --at <time>` records the round in
`assemblies/default.seed.json`; `popsim assembly` draws the assembly with that seed using the
same TypeScript sampler the website runs.

## Consequences

* Anyone can fetch the round (`https://api.drand.sh/public/<round>`), recompute the seed and
  regenerate the assembly; CI checks that the committed assembly is reproduced byte for byte.
* For the first edition (model 2026.10.0) the time — 2026-10-13 00:00 UTC, round 6,547,286 —
  was fixed on the day the assembly was first drawn, so the protection against seed shopping
  rests on the mechanical rule rather than on a public announcement. **Future editions should
  announce the beacon time publicly before it occurs** (e.g. in a tagged commit or release note).
* A new model version (for example with the 2026 vote) keeps the same seed, so the edition
  changes only as much as the model does.
