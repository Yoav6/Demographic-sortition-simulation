import { existsSync, readFileSync } from "node:fs";
import { describe as suite, expect, it } from "vitest";
import { compile, type Bundle } from "../src/model.ts";
import { samplePerson } from "../src/sample.ts";
import { describe, type Templates } from "../src/describe.ts";

const root = new URL("../../../", import.meta.url);
const bundlePath = new URL("model/build/model.json", root);

suite.skipIf(!existsSync(bundlePath))("Hebrew and English descriptions", () => {
  const model = compile(JSON.parse(readFileSync(bundlePath, "utf8")) as Bundle);
  const he = JSON.parse(readFileSync(new URL("templates/he.json", root), "utf8")) as Templates;
  const en = JSON.parse(readFileSync(new URL("templates/en.json", root), "utf8")) as Templates;
  const sexIdx = model.varIndex.get("sex")!;

  it("agrees with the person's grammatical gender", () => {
    let women = 0;
    let men = 0;
    for (let i = 0; i < 400 && (women < 20 || men < 20); i++) {
      const p = samplePerson(model, 123, i);
      const female = model.vars[sexIdx].values![p[sexIdx]].id === "female";
      const text = describe(model, p, he).join(" ");
      const textEn = describe(model, p, en).join(" ");
      if (female) {
        women++;
        expect(text).toContain("היא");
        expect(text).not.toContain(" הוא ");
        expect(textEn).toContain("She");
      } else {
        men++;
        expect(text).toContain("הוא");
        expect(text).not.toContain(" היא ");
        expect(textEn).toContain("He");
      }
      expect(text).not.toMatch(/\{|\}/);
    }
    expect(women).toBeGreaterThan(0);
    expect(men).toBeGreaterThan(0);
  });
});
