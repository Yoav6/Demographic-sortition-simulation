/// <reference lib="webworker" />
/**
 * Runs the model off the main thread: loading, sampling assemblies/people, and
 * likelihood-weighted conditional queries.
 */
import {
  compile,
  presentPerson,
  query,
  samplePerson,
  visibleVars,
  type Bundle,
  type CompiledModel,
  type Evidence,
  type Templates,
} from "@popsim/sampler";

let model: CompiledModel | null = null;
let templates: { he: Templates; en: Templates } | null = null;

async function ensure(base: string) {
  if (!model) {
    const bundle = (await (await fetch(new URL("model.json", base))).json()) as Bundle;
    model = compile(bundle);
  }
  if (!templates) {
    const [he, en] = await Promise.all([
      fetch(new URL("templates.he.json", base)).then((r) => r.json()),
      fetch(new URL("templates.en.json", base)).then((r) => r.json()),
    ]);
    templates = { he, en };
  }
  return { model, templates };
}

export type Request =
  | { type: "assembly"; seed: number; size: number }
  | { type: "person"; seed: number; index: number }
  | { type: "query"; evidence: Evidence; samples: number; seed: number }
  | { type: "info" };

self.onmessage = async (e: MessageEvent<{ id: number; base: string; req: Request }>) => {
  const { id, base, req } = e.data;
  try {
    const { model: m, templates: tpl } = await ensure(base);
    let result: unknown;
    switch (req.type) {
      case "assembly":
        result = {
          people: Array.from({ length: req.size }, (_, i) => presentPerson(m, samplePerson(m, req.seed, i), i, tpl)),
          vars: visibleVars(m),
          model_version: m.bundle.version,
        };
        break;
      case "person":
        result = { person: presentPerson(m, samplePerson(m, req.seed, req.index), req.index, tpl), vars: visibleVars(m) };
        break;
      case "query":
        result = query(m, req.evidence, req.samples, req.seed);
        break;
      case "info":
        result = {
          version: m.bundle.version,
          population_total: m.bundle.population_total,
          vars: m.vars.map((v) => ({
            id: v.id,
            label: v.label,
            values: v.values,
            numeric: v.numeric,
            multi: v.multi,
            hidden: v.hidden,
            ordered: v.node.type === "table" && !!v.node.ordered,
            offScale: v.node.type === "table" ? v.node.off_scale : undefined,
          })),
          // the network's structure, for the methodology diagram: each node and the variables it depends on
          nodes: m.bundle.nodes.map((n) => {
            const deps =
              n.type === "frame"
                ? []
                : n.type === "lookup" || n.type === "percentile"
                  ? [n.parent]
                  : n.type === "interval"
                    ? [n.parent, ...(n.cap ? [n.cap.var] : []), ...(n.floor ? [n.floor] : [])]
                    : n.parents;
            const produces = n.type === "frame" ? n.vars.map((v) => v.id) : [n.id];
            return { id: n.id, label: n.label, type: n.type, hidden: !!n.hidden, doc: n.doc, deps, produces };
          }),
        };
        break;
    }
    (self as unknown as Worker).postMessage({ id, result });
  } catch (err) {
    (self as unknown as Worker).postMessage({ id, error: String(err) });
  }
};
