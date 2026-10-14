import { describe, expect, it } from "vitest";
import { compile, type Bundle } from "../src/model.ts";
import { samplePerson, toRecord } from "../src/sample.ts";
import { query } from "../src/infer.ts";
import { addLists, type Templates } from "../src/describe.ts";

// sex -> uses (networks a, b, c) -> news (on which of the networks used; subset_of uses)
const lab = (s: string) => ({ en: s, he: s });
const vals = (...ids: string[]) => ids.map((id) => ({ id, label: lab(id) }));
const P = (...ps: number[]) => ps.map((p) => p * 1e9);
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
      vars: [{ id: "sex", label: lab("sex"), values: vals("male", "female") }],
      rows: { sex: [0, 1] },
      weights: [50, 50],
    },
    { id: "uses", type: "multi", label: lab("uses"), parents: ["sex"], items: vals("a", "b", "c"), rows: { "0": P(0.9, 0.5, 0.1), "1": P(0.6, 0.6, 0.6) } },
    {
      id: "news",
      type: "multi",
      label: lab("news"),
      parents: ["sex"],
      items: vals("a", "b", "c"),
      subset_of: "uses",
      rows: { "0": P(0.5, 0.5, 0.5), "1": P(0.2, 0.8, 1.0) },
    },
  ],
};

describe("set-valued nodes within another set (subset_of)", () => {
  const model = compile(bundle);

  it("only chooses items the person has in the enclosing set, with conditional probabilities", () => {
    let maleA = 0;
    let men = 0;
    for (let i = 0; i < 20_000; i++) {
      const r = toRecord(model, samplePerson(model, 11, i));
      const uses = r.uses as string[];
      const news = r.news as string[];
      for (const x of news) expect(uses).toContain(x);
      if (r.sex === "male") {
        men++;
        if (news.includes("a")) maleA++;
      }
    }
    expect(maleA / men).toBeCloseTo(0.9 * 0.5, 1);
  });

  it("conditions on an item, which forces it into the enclosing set", () => {
    const res = query(model, { news: { ids: ["c"] } }, 100_000, 4);
    expect(res.evidenceProbability).toBeCloseTo(0.5 * 0.1 * 0.5 + 0.5 * 0.6 * 1.0, 2);
    expect(res.marginals.uses.probs![2]).toBeCloseTo(1, 6);
  });
});

describe("template lists", () => {
  const templates = (lang: "he" | "en", items: Record<string, string>, groups: Record<string, string>): Templates => ({
    lang,
    sentences: [],
    lists: { media: { items, groups, separate: "never" } },
  });
  const ctx = () => ({ tv__id: "often", sites__id: "often", radio__id: "rarely", print__id: "never", pods__id: "never", channel: "Kan 11" });

  it("groups variables by value, in the order of the groups, and lists the rest apart", () => {
    const c: Record<string, unknown> = ctx();
    addLists(c, templates("en", { tv: "TV ({channel})", sites: "news sites", radio: "the radio", print: "newspapers", pods: "podcasts" },
      { often: "often from {list}", sometimes: "sometimes from {list}", rarely: "rarely from {list}" }));
    expect(c.media).toBe("often from TV (Kan 11) and news sites and rarely from the radio");
    expect(c.media__n).toBe(2);
    expect(c.media__never).toBe("newspapers or podcasts");
    expect(c.media__never_n).toBe(2);
  });

  it("joins Hebrew lists with a prefixed vav", () => {
    const c: Record<string, unknown> = ctx();
    addLists(c, templates("he", { tv: "בטלוויזיה", sites: "באתרים", radio: "ברדיו", print: "בעיתונים", pods: "בפודקאסטים" },
      { often: "לעיתים קרובות {list}", rarely: "לעיתים רחוקות {list}" }));
    expect(c.media).toBe("לעיתים קרובות בטלוויזיה ובאתרים ולעיתים רחוקות ברדיו");
    expect(c.media__never).toBe("בעיתונים או בפודקאסטים");
  });
});
