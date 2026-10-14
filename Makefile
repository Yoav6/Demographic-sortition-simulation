# Every step of the pipeline, in order. `make all` rebuilds everything from the
# pinned sources; `make check` runs what CI runs. Run `make help` for the list.

PY := uv run

.PHONY: help setup fetch fetch-cbs-ss build export validate docs assembly web dev test check all clean

help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-14s %s\n", $$1, $$2}'

setup: ## install Python and Node dependencies and Playwright's Chromium
	uv sync
	pnpm install
	$(PY) playwright install chromium

fetch: ## download the sources into data/raw and verify their pinned SHA-256 checksums
	$(PY) popsim fetch

fetch-cbs-ss: ## re-run the CBS Social Survey table-generator queries (headless browser; ~1 min per table)
	$(PY) popsim fetch-cbs-ss

build: ## estimate every model node from data/raw and data/manual into model/
	$(PY) popsim build

export: ## compile model/ into model/build/model.json (and its fingerprint model.sha256)
	$(PY) popsim export

validate: ## compare the model with official figures; writes reports/validation.json
	$(PY) popsim validate

docs: ## regenerate SOURCES.md and the generated sections of the methodology docs
	$(PY) popsim docs

assembly: ## draw the published default assembly from its recorded beacon seed
	$(PY) popsim assembly

web: ## build the static website into web/dist
	pnpm --filter popsim-web build

dev: ## run the website locally with live reload
	pnpm --filter popsim-web dev

test: ## unit tests: Python pipeline and TypeScript sampler
	$(PY) pytest -q
	pnpm --filter @popsim/sampler test

check: ## what CI checks: tests, bundle and assembly reproduced exactly, docs up to date, site builds
	$(PY) pytest -q
	$(PY) popsim export --check
	$(PY) popsim export
	pnpm --filter @popsim/sampler test
	$(PY) popsim assembly --check
	$(PY) popsim docs --check
	pnpm --filter popsim-web check
	pnpm --filter popsim-web build

all: fetch build export validate docs assembly web ## the whole pipeline, from sources to website

clean: ## remove derived files (they are all rebuilt by `make all`)
	rm -rf data/interim model/build/*.json web/dist web/public/data
