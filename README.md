# popsim — a citizens' assembly by lot, simulated

**אספה אזרחית בהגרלה:** 150 אזרחיות ואזרחי ישראל שנבחרו באקראי — סימולציה מבוססת נתונים.

What would a citizens' assembly look like if its 150 members were drawn by lot from all Israeli
citizens? popsim builds a statistical model of the eligible population — **Israeli citizens aged
18 and over living in Israel (6.45 million people)** — from public data, draws 150 synthetic
members from it, and describes each of them in Hebrew and English:

> *Gefen is a 29-year-old Jewish woman who describes herself as traditional-religious. She is a
> third-generation Israeli, of Mizrahi or Sephardi descent. She lives in Hadera, Haifa District.
> She is single and has no children. She has a bachelor's degree. She served in the IDF. She is
> unemployed and looking for work…* — member #1 of the published assembly

Every member has 39 attributes: place of residence, population group, sex, age, religiosity,
first name, origin and ancestry, marital status and children, education, military or national
service, work (status, occupation, industry), earnings and household income (with percentiles),
home ownership, health, disability, the 2022 vote, media habits, and a modelled literacy score.

The website shows the assembly as a 150-seat hemicycle, coloured by an attribute of your choice
and compared with the population, and as a map of the members' localities. It also draws random
people. Its "What are the odds?" explorer gives the distribution of every other attribute for
any combination you choose, the number of seats such people would expect in an assembly, and the
members who match ("people like me"). The methodology pages include a clickable diagram of the
model's structure.

## How it works

* **A Bayesian network of conditional tables.** The model is a chain of tables, each giving one
  attribute's distribution given a few others: religiosity given group, sex, age and the
  locality's religious profile; education given religiosity, sex, age and continent of birth;
  and so on. The root is a joint table of locality × population group × sex × age band. The
  structure is in [`model/dag.yaml`](model/dag.yaml); each table is a CSV file in `model/cpts/`.
* **Built only from public data.** Sources include the CBS (population, localities, Statistical
  Abstract, first names, 56 Social Survey cross-tabulations queried from the official table
  generator), the Central Elections Committee (2022 results by polling station), the Israel
  National Election Studies, the OECD and Bank of Israel (adult skills), the Agam Institute
  (media), Wikidata (name transliteration) and IGRA (registry names). All are listed with
  checksums in [SOURCES.md](SOURCES.md).
* **Calibrated and validated.** Tables are combined with iterative proportional fitting over the
  model's own population and calibrated to official totals. For example, national 2022 vote
  shares match the official result within 0.1 points. `popsim validate` runs 49 checks against
  published figures, tests the sampler, and audits impossible combinations; results are in
  [reports/validation.json](reports/validation.json) and on each attribute's methodology page.
* **Deterministic.** Every random number is a hash of (seed, person, attribute), so the same seed
  always gives the same people in Node and in the browser. The published assembly's seed comes
  from the [drand](https://drand.love) public randomness beacon.

Full methodology: [METHODOLOGY.md](METHODOLOGY.md) (overview), [docs/methodology/](docs/methodology)
(one page per attribute, with sources, estimation steps, validation and limitations) and
[docs/decisions/](docs/decisions) (decision records).

## Quick start

Requirements: [uv](https://docs.astral.sh/uv/), Node 22 with [pnpm](https://pnpm.io/), and
`make`.

```sh
make setup      # Python and Node dependencies, Playwright's Chromium
make fetch      # download the sources (~30 MB) and verify their SHA-256 pins
make build      # estimate every table of the model
make export     # compile the model into model/build/model.json
make validate   # compare the model with official figures
make assembly   # draw the published assembly from its seed
make dev        # run the website locally
```

`make all` runs the whole pipeline; `make check` runs what CI runs; `make help` lists every
target. To draw people from the command line:

```sh
pnpm sample -- --model model/build/model.json --seed 7 --n 3 --format text --lang en
```

## Reproducibility

* `popsim fetch` refuses a source file whose checksum differs from `sources.lock.json` unless it
  is accepted with `--update`. Files that need a browser (the CBS Social Survey generator) are
  queried by scripts whose specs are committed (`data/manual/cbs_ss/queries/`). Values available
  only as charts are transcribed in `data/manual/` with page references.
* `popsim export --check` verifies that the committed tables compile to the recorded
  fingerprint (`model/build/model.sha256`).
* `popsim assembly --check` verifies that the published assembly is reproduced byte for byte
  from its seed.

## Repository layout

```
pipeline/popsim/   Python pipeline: fetch/ extract/ estimate/ (one module per group of nodes) export/ validate/
packages/sampler/  TypeScript sampler shared by the CLI and the website (RNG, sampling, inference, descriptions)
web/               Svelte website
model/             dag.yaml, frame.csv, cpts/, lookups/, domains/, constraints.yaml
data/manual/       committed inputs: Social Survey tables, transcriptions, name overrides, election party map
templates/         Hebrew and English description templates (ICU MessageFormat)
assemblies/        the published assembly and its beacon seed
docs/              methodology pages and decision records
```

## Status

Model version 2026.10.0. The political attribute is the vote in the **2022** election; it will
be replaced by the **26th Knesset election (27 October 2026)** once its certified results are
published, as a new model version and a new edition of the published assembly.

## Licence

Code: MIT ([LICENSE](LICENSE)). Model, assemblies, templates and documentation: CC BY 4.0
([LICENSE-DATA.md](LICENSE-DATA.md)). The sources keep their own terms; see
[SOURCES.md](SOURCES.md). All people shown are synthetic characters, not real individuals.
