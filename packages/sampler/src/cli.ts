#!/usr/bin/env -S npx tsx
/**
 * popsim-sample: draw people from a compiled model bundle.
 *
 *   pnpm sample -- --model model/build/model.json --seed 20261027 --n 150 --format assembly
 *   pnpm sample -- --model ... --seed 1 --n 1000000 --format csv --out reports/tmp/sample.csv
 *   pnpm sample -- --model ... --seed 7 --n 3 --format text --lang he
 */

import { createWriteStream, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { compile, type Bundle } from "./model.ts";
import { samplePerson, toRecord } from "./sample.ts";
import { describe, presentPerson, visibleVars, type Templates } from "./describe.ts";
import { SAMPLER_VERSION } from "./index.ts";

function args(argv: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) out[key] = "true";
      else {
        out[key] = next;
        i++;
      }
    }
  }
  return out;
}

function csvCell(x: unknown): string {
  const s = x === null || x === undefined ? "" : Array.isArray(x) ? x.join(";") : String(x);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

// `pnpm sample` runs this script from packages/sampler; relative paths are meant from the
// directory pnpm was invoked in (INIT_CWD).
const base = process.env.npm_lifecycle_event === "cli" && process.env.INIT_CWD ? process.env.INIT_CWD : process.cwd();
const path = (p: string) => resolve(base, p);

async function main() {
  const a = args(process.argv.slice(2));
  for (const k of ["model", "out", "templates"]) if (a[k]) a[k] = path(a[k]);
  const modelPath = a.model ?? path("model/build/model.json");
  const seed = Number(a.seed ?? "0");
  const n = Number(a.n ?? "150");
  const start = Number(a.start ?? "0");
  const format = a.format ?? "json";
  const bundle = JSON.parse(readFileSync(modelPath, "utf8")) as Bundle;
  const model = compile(bundle);

  if (format === "csv") {
    const out = a.out ? createWriteStream(a.out) : process.stdout;
    const ids = model.vars.map((v) => v.id);
    out.write(["index", ...ids].join(",") + "\n");
    for (let i = start; i < start + n; i++) {
      const rec = toRecord(model, samplePerson(model, seed, i));
      out.write([i, ...ids.map((id) => csvCell(rec[id]))].join(",") + "\n");
    }
    if (a.out) await new Promise<void>((res) => (out as ReturnType<typeof createWriteStream>).end(res));
    return;
  }

  const people = [];
  for (let i = start; i < start + n; i++) people.push(samplePerson(model, seed, i));

  if (format === "text") {
    const lang = (a.lang ?? "he") as "he" | "en";
    const templates = JSON.parse(readFileSync(a.templates ?? path(`templates/${lang}.json`), "utf8")) as Templates;
    const text = people.map((p, k) => `#${start + k}\n` + describe(model, p, templates).join(" ")).join("\n\n");
    if (a.out) writeFileSync(a.out, text + "\n");
    else console.log(text);
    return;
  }

  let payload: unknown;
  if (format === "assembly") {
    const dir = a.templates ?? path("templates");
    const templates = {
      he: JSON.parse(readFileSync(`${dir}/he.json`, "utf8")) as Templates,
      en: JSON.parse(readFileSync(`${dir}/en.json`, "utf8")) as Templates,
    };
    payload = {
      format: "popsim-assembly/1",
      seed,
      size: n,
      model_version: bundle.version,
      sampler_version: SAMPLER_VERSION,
      reference_date: bundle.reference_date,
      population_label: bundle.population_label,
      population_total: bundle.population_total,
      vars: visibleVars(model),
      people: people.map((p, k) => presentPerson(model, p, start + k, templates)),
    };
  } else {
    payload = people.map((p, k) => ({ index: start + k, ...toRecord(model, p) }));
  }
  const json = JSON.stringify(payload, null, 1) + "\n";
  if (a.out) writeFileSync(a.out, json);
  else process.stdout.write(json);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
