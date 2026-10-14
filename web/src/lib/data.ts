import { compile, type Bundle, type CompiledModel, type Label, type PresentedPerson, type Templates, type VarMeta } from "@popsim/sampler";

export interface Assembly {
  format: string;
  seed: number;
  size: number;
  model_version: string;
  sampler_version: string;
  reference_date: string;
  population_label: Label;
  population_total: number;
  vars: VarMeta[];
  people: PresentedPerson[];
}

export interface SourceInfo {
  id: string;
  title: { en: string; he: string };
  publisher: string;
  tier: string;
  url?: string;
  license: string;
  as_of?: string;
  used_by: string[];
  notes?: string;
  files: { path: string; url: string; sha256?: string; retrieved?: string }[];
}

const base = "./data/";

async function json<T>(name: string): Promise<T> {
  const r = await fetch(base + name);
  if (!r.ok) throw new Error(`failed to load ${name}: ${r.status}`);
  return (await r.json()) as T;
}

export const loadAssembly = () => json<Assembly>("assembly.json");
export const loadSources = () => json<SourceInfo[]>("sources.json");
export const loadMethodology = () => json<Record<string, string>>("methodology.json");

let modelPromise: Promise<CompiledModel> | null = null;
export function loadModel(): Promise<CompiledModel> {
  modelPromise ??= json<Bundle>("model.json").then(compile);
  return modelPromise;
}

let templatesPromise: Promise<{ he: Templates; en: Templates }> | null = null;
export function loadTemplates() {
  templatesPromise ??= Promise.all([json<Templates>("templates.he.json"), json<Templates>("templates.en.json")]).then(
    ([he, en]) => ({ he, en }),
  );
  return templatesPromise;
}
