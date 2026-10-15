import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { compile, type Bundle, type CompiledModel } from "../src/model.ts";
import { samplePerson } from "../src/sample.ts";
import { presentPerson, presentUnusual, type Templates } from "../src/describe.ts";
import { TIERS, UNUSUAL, calibration, surprises, unusual, unusualScore } from "../src/unusual.ts";

// locality -> (hidden profile) -> religiosity -> job (with "does not apply") and networks
const lab = (s: string) => ({ en: s, he: s });
const vals = (...ids: string[]) => ids.map((id) => ({ id, label: lab(id) }));
const P = (...ps: number[]) => ps.map((p) => Math.round(p * 1e9));
// frame rows: locality x group x sex x age_band; secular town 80 people, Haredi town 20
const rows = { locality: [0, 0, 0, 1, 1], group: [0, 0, 1, 0, 1], sex: [0, 1, 0, 1, 0], age_band: [0, 1, 0, 0, 1] };
const weights = [40, 30, 10, 19, 1];
const pHarediSecular = 0.02;
const pHarediTown = 0.9;
const share = (secular: number, town: number) => 0.8 * secular + 0.2 * town;
const bundle: Bundle = {
  format: "popsim-model/1",
  version: "test",
  reference_date: "2024-12-31",
  population_label: lab("test"),
  population_total: 100,
  sources: [],
  nodes: [
    {
      id: "frame",
      type: "frame",
      label: lab("frame"),
      vars: [
        { id: "locality", label: lab("locality"), values: vals("secular_town", "haredi_town") },
        { id: "group", label: lab("group"), values: vals("jewish", "arab") },
        { id: "sex", label: lab("sex"), values: vals("male", "female") },
        { id: "age_band", label: lab("age_band"), values: vals("young", "old") },
      ],
      rows,
      weights,
    },
    { id: "profile", type: "lookup", hidden: true, label: lab("profile"), parent: "locality", values: vals("s", "h"), map: [0, 1] },
    {
      id: "religiosity",
      type: "table",
      label: lab("religiosity"),
      parents: ["profile"],
      values: vals("haredi", "hiloni"),
      rows: { "0": [[0, 1], P(pHarediSecular, 1 - pHarediSecular)], "1": [[0, 1], P(pHarediTown, 1 - pHarediTown)] },
      marginal: [share(pHarediSecular, pHarediTown), 1 - share(pHarediSecular, pHarediTown)],
      parent_weights: { v: [0, 1], w: [80, 20] },
    },
    {
      id: "job",
      type: "table",
      label: lab("job"),
      parents: ["religiosity"],
      values: vals("none", "rabbi", "pilot"),
      // Haredim: half have no job; a Haredi pilot is 1 in a million
      rows: { "0": [[0, 1, 2], P(0.5, 0.499999, 0.000001)], "1": [[0, 1, 2], P(0.2, 0.001, 0.799)] },
      marginal: [0.25, 0.1, 0.65],
      not_applicable: ["none"],
    },
    {
      id: "nets",
      type: "multi",
      label: lab("nets"),
      parents: ["religiosity"],
      items: vals("x", "y"),
      rows: { "0": P(0.05, 0.1), "1": P(0.9, 0.9) },
      marginal: [0.75, 0.75],
    },
  ],
};

function person(model: CompiledModel, ids: Record<string, string | string[]>): Float64Array {
  const v = new Float64Array(model.vars.length);
  for (const [id, x] of Object.entries(ids)) {
    const k = model.varIndex.get(id)!;
    const dom = model.vars[k].values!;
    v[k] = Array.isArray(x) ? x.reduce((m, item) => m | (1 << dom.findIndex((d) => d.id === item)), 0) : dom.findIndex((d) => d.id === x);
  }
  const loc = v[model.varIndex.get("locality")!];
  v[model.varIndex.get("profile")!] = loc; // the lookup
  return v;
}

describe("How unusual? (toy model)", () => {
  const model = compile(bundle);
  const base = { group: "jewish", sex: "male", age_band: "young", job: "rabbi", nets: ["x", "y"] };
  const inSecular = person(model, { ...base, locality: "secular_town", religiosity: "haredi" });
  const inTown = person(model, { ...base, locality: "haredi_town", religiosity: "haredi" });

  it("a Haredi in a secular town is more unusual than one in a Haredi town, because of where they live", () => {
    expect(unusualScore(model, inSecular)).toBeGreaterThan(unusualScore(model, inTown));
    const r = surprises(model, inSecular).find((s) => s.variable === "religiosity")!;
    const bits = Math.log2(share(pHarediSecular, pHarediTown) / pHarediSecular);
    expect(r.bits).toBeCloseTo(bits, 9);
    expect(r.score).toBeCloseTo(bits - UNUSUAL.hinge, 9);
    expect(r.causes).toEqual(["locality"]); // the hidden profile is explained by the visible locality
    expect(r.ladder!.map((x) => x.kind)).toEqual(["all", "like"]);
    expect(r.ladder![0].p).toBeCloseTo(share(pHarediSecular, pHarediTown), 12);
    expect(r.ladder![1].p).toBeCloseTo(pHarediSecular, 12);
    expect(surprises(model, inTown).find((s) => s.variable === "religiosity")).toBeUndefined();
  });

  it("caps a junction's surprise", () => {
    const pilot = person(model, { ...base, locality: "haredi_town", religiosity: "haredi", job: "pilot" });
    const r = surprises(model, pilot).find((s) => s.variable === "job")!;
    expect(r.bits).toBe(UNUSUAL.cap);
  });

  it("skips values that do not apply, and leaves them out of the national share", () => {
    const none = person(model, { ...base, locality: "haredi_town", religiosity: "hiloni", job: "none" });
    expect(surprises(model, none, Infinity, 0).find((s) => s.variable === "job")).toBeUndefined();
    const rabbi = person(model, { ...base, locality: "haredi_town", religiosity: "hiloni" });
    const r = surprises(model, rabbi, Infinity, 0).find((s) => s.variable === "job")!;
    expect(r.pBase).toBeCloseTo(0.1 / 0.75, 12);
    expect(r.pCond).toBeCloseTo(0.001 / 0.8, 12);
  });

  it("scores a set by its single most surprising item, present or missing", () => {
    const p = person(model, { ...base, locality: "haredi_town", religiosity: "haredi", nets: ["x"] });
    const nets = surprises(model, p, Infinity, 0).filter((s) => s.variable === "nets");
    expect(nets).toHaveLength(1);
    expect(nets[0].value).toBe("x"); // having x (5% vs 75%) beats missing y (90% vs 25%)
    expect(nets[0].present).toBe(true);
  });

  it("judges population group given the locality from the frame", () => {
    const arab = person(model, { ...base, group: "arab", age_band: "old", locality: "haredi_town", religiosity: "hiloni" });
    const r = surprises(model, arab, Infinity, 0).find((s) => s.variable === "group")!;
    expect(r.pCond).toBeCloseTo(1 / 20, 12);
    expect(r.pBase).toBeCloseTo(11 / 100, 12);
  });

  it("gives tiers in their population shares", () => {
    const bp = calibration(model);
    expect(bp).toHaveLength(101);
    expect(unusual(model, inTown).percentile).toBeLessThanOrEqual(unusual(model, inSecular).percentile);
  });
});

const root = new URL("../../../", import.meta.url);
const bundlePath = new URL("model/build/model.json", root);

describe.skipIf(!existsSync(bundlePath))("How unusual? (published model)", () => {
  const model = compile(JSON.parse(readFileSync(bundlePath, "utf8")) as Bundle);
  const id = (p: ArrayLike<number>, v: string) => model.vars[model.varIndex.get(v)!].values![p[model.varIndex.get(v)!]].id;

  it("puts citizens into the tiers in the advertised shares", () => {
    const n = 20_000;
    const counts: Record<string, number> = {};
    for (let i = 0; i < n; i++) {
      const t = unusual(model, samplePerson(model, 4242, i)).tier;
      counts[t] = (counts[t] ?? 0) + 1;
    }
    for (const t of TIERS) expect(Math.abs((counts[t.id] ?? 0) / n - t.share)).toBeLessThan(0.015);
  }, 60_000);

  it("finds a Haredi woman more unusual in Tel Aviv-Yafo than in Bnei Brak", () => {
    const locality = model.varIndex.get("locality")!;
    const localities = model.vars[locality].values!;
    const ta = localities.findIndex((v) => v.label.en === "Tel Aviv-Yafo");
    const bb = localities.findIndex((v) => v.label.en === "Bene Beraq");
    let found: Float64Array | null = null;
    for (let i = 0; i < 200_000 && !found; i++) {
      const p = samplePerson(model, 5, i);
      if (p[locality] === bb && id(p, "religiosity") === "haredi" && id(p, "sex") === "female") found = p;
    }
    expect(found).not.toBeNull();
    const moved = Float64Array.from(found!);
    moved[locality] = ta;
    for (const n of model.bundle.nodes) if (n.type === "lookup" && n.parent === "locality") moved[model.varIndex.get(n.id)!] = n.map[ta];
    expect(unusualScore(model, moved)).toBeGreaterThan(unusualScore(model, found!));
    const r = surprises(model, moved, Infinity, 0).find((s) => s.variable === "religiosity")!;
    expect(r.causes[0]).toBe("locality");
    expect(surprises(model, found!, Infinity, 0).find((s) => s.variable === "religiosity")).toBeUndefined();
  });

  it("says whether an ordered value is below or above usual, and what is usual", () => {
    let found = 0;
    for (let i = 0; i < 3000 && found < 5; i++) {
      for (const r of surprises(model, samplePerson(model, 12, i))) {
        if (!r.ordinal) continue;
        found++;
        expect(["income", "household_income", "children", "literacy_level", "education", "health"]).toContain(r.variable);
        expect(r.ordinal.usual).not.toBe(r.value);
        expect(r.ordinal.beyond).toBeGreaterThan(0.5); // a surprise has most people on the far side
        const dom = model.vars[model.varIndex.get(r.variable)!].values!.map((v) => v.id);
        const below = dom.indexOf(r.value) < dom.indexOf(r.ordinal.usual);
        expect(r.ordinal.direction).toBe(r.variable === "health" ? (below ? "better" : "worse") : below ? "lower" : "higher");
      }
    }
    expect(found).toBeGreaterThan(0);
  });

  it("splits a surprise among the traits, both those that make it less usual and those that ease it", () => {
    // Na'ama in the published assembly: a religious woman of 24 who did not serve. Not serving is
    // unusual because of her religiosity (most young religious women do national service).
    const asm = JSON.parse(readFileSync(new URL("assemblies/default.json", root), "utf8"));
    for (let i = 0; i < 400; i++) {
      const p = samplePerson(model, asm.seed as number, i);
      for (const r of surprises(model, p)) {
        if (!r.ladder) continue;
        expect(r.ladder[0].kind).toBe("all");
        expect(r.ladder.at(-1)!.kind).toBe("like");
        expect(r.ladder.at(-1)!.p).toBeCloseTo(r.pCond, 6);
        if (!model.bundle.nodes.find((n) => n.id === r.variable && n.type === "multi" && n.subset_of)) {
          expect(r.ladder[0].p).toBeCloseTo(r.pBase, 3);
        }
        for (const c of r.causes) expect(r.eases).not.toContain(c);
      }
    }
    const naama = samplePerson(model, asm.seed as number, 70);
    expect(id(naama, "religiosity")).toBe("dati");
    const service = surprises(model, naama).find((s) => s.variable === "military_service")!;
    expect(service.causes[0]).toBe("religiosity");
    expect(service.common?.value).toBe("national_service");
  });

  it("leaves the first name out of the score but still describes it", () => {
    const he = JSON.parse(readFileSync(new URL("templates/he.json", root), "utf8")) as Templates;
    const en = JSON.parse(readFileSync(new URL("templates/en.json", root), "utf8")) as Templates;
    for (let i = 0; i < 40; i++) {
      const p = samplePerson(model, 8, i);
      expect(surprises(model, p, Infinity, 0).some((s) => s.variable === "first_name")).toBe(false);
      const u = presentUnusual(model, p, id(p, "sex") === "female", { he, en });
      expect(u.text.en.title).toContain(model.vars[model.varIndex.get("first_name")!].values![p[model.varIndex.get("first_name")!]].label.en);
      expect(u.text.he.name_note).not.toMatch(/[{}]|undefined|NaN/);
      expect(u.text.he.name_note).not.toBe("");
    }
  });

  it("lists every deviation that counts, with a level, so the parts add up to the score", () => {
    for (let i = 0; i < 200; i++) {
      const p = samplePerson(model, 31, i);
      const list = surprises(model, p);
      expect(list.reduce((a, r) => a + r.score, 0)).toBeCloseTo(unusualScore(model, p), 9);
      for (const r of list) expect(r.level).toBe(r.bits >= UNUSUAL.major ? "major" : r.bits >= UNUSUAL.notable ? "notable" : "minor");
    }
  });

  it("explains the score in Hebrew and English", () => {
    const he = JSON.parse(readFileSync(new URL("templates/he.json", root), "utf8")) as Templates;
    const en = JSON.parse(readFileSync(new URL("templates/en.json", root), "utf8")) as Templates;
    for (let i = 0; i < 60; i++) {
      const u = presentPerson(model, samplePerson(model, 77, i), i, { he, en }).unusual!;
      for (const lang of ["he", "en"] as const) {
        const t = u.text[lang];
        expect(t.reasons.length).toBeGreaterThan(0);
        for (const s of [t.tier, t.headline, ...t.reasons]) expect(s).not.toMatch(/[{}]|undefined|NaN/);
      }
    }
  });
});
