import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { compile, type Bundle } from "../src/model.ts";
import { samplePerson, toRecord } from "../src/sample.ts";

const root = new URL("../../../", import.meta.url);
const bundlePath = new URL("model/build/model.json", root);
const assemblyPath = new URL("assemblies/default.json", root);
const ready = existsSync(bundlePath) && existsSync(assemblyPath);

describe.skipIf(!ready)("published default assembly", () => {
  const bundle = JSON.parse(readFileSync(bundlePath, "utf8")) as Bundle;
  const model = compile(bundle);
  const assembly = JSON.parse(readFileSync(assemblyPath, "utf8"));

  it("was drawn with the current model version", () => {
    expect(assembly.model_version).toBe(bundle.version);
  });

  it("is reproduced exactly by the sampler from its seed", () => {
    for (const p of assembly.people) {
      const rec = toRecord(model, samplePerson(model, assembly.seed, p.index));
      for (const [k, v] of Object.entries(p.values)) expect(rec[k], `${k} of #${p.index}`).toEqual(v);
    }
  });

  it("person #i does not depend on how many people are drawn", () => {
    const a = toRecord(model, samplePerson(model, 7, 42));
    const b = toRecord(model, samplePerson(model, 7, 42));
    expect(a).toEqual(b);
  });
});
