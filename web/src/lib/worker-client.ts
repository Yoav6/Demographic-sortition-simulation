import type { Evidence, Label, PresentedPerson, QueryResult, ValueDef, VarMeta } from "@popsim/sampler";
import type { Request } from "./model.worker.ts";

let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

function call<T>(req: Request): Promise<T> {
  if (!worker) {
    worker = new Worker(new URL("./model.worker.ts", import.meta.url), { type: "module" });
    worker.onmessage = (e: MessageEvent<{ id: number; result?: unknown; error?: string }>) => {
      const p = pending.get(e.data.id);
      if (!p) return;
      pending.delete(e.data.id);
      if (e.data.error) p.reject(new Error(e.data.error));
      else p.resolve(e.data.result);
    };
  }
  const id = nextId++;
  const base = new URL("./data/", location.href).href;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve: resolve as (v: unknown) => void, reject });
    // requests are plain data; the JSON round trip strips Svelte's reactive proxies, which
    // structured cloning (postMessage) cannot copy
    worker!.postMessage({ id, base, req: JSON.parse(JSON.stringify(req)) as Request });
  });
}

export interface GraphNode {
  id: string;
  label: Label;
  type: string;
  hidden: boolean;
  doc?: string;
  deps: string[]; // variables the node depends on
  produces: string[]; // variables it defines (the frame defines several)
}

export interface ModelInfo {
  version: string;
  population_total: number;
  vars: { id: string; label: Label; values?: ValueDef[]; numeric: boolean; multi: boolean; hidden: boolean }[];
  nodes: GraphNode[];
}

export const drawAssembly = (seed: number, size = 150) =>
  call<{ people: PresentedPerson[]; vars: VarMeta[]; model_version: string }>({ type: "assembly", seed, size });
export const drawPerson = (seed: number, index = 0) => call<{ person: PresentedPerson; vars: VarMeta[] }>({ type: "person", seed, index });
export const runQuery = (evidence: Evidence, samples = 100_000, seed = 1) => call<QueryResult>({ type: "query", evidence, samples, seed });
export const modelInfo = () => call<ModelInfo>({ type: "info" });

/** A random non-negative integer seed below 2^32 (shown to the user, so it stays short). */
export function randomSeed(): number {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0];
}
