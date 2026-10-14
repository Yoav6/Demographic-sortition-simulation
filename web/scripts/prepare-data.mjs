// Copies the published model artefacts into public/data so the static site can load them.
import { copyFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const out = join(root, "web", "public", "data");
mkdirSync(out, { recursive: true });

const copy = (from, to) => {
  if (!existsSync(from)) throw new Error(`missing ${from} - run the pipeline first (make build export assembly)`);
  copyFileSync(from, join(out, to));
};
copy(join(root, "model", "build", "model.json"), "model.json");
copy(join(root, "assemblies", "default.json"), "assembly.json");
copy(join(root, "model", "build", "sources.json"), "sources.json");
copy(join(root, "templates", "he.json"), "templates.he.json");
copy(join(root, "templates", "en.json"), "templates.en.json");

// methodology docs (markdown), bundled as one JSON file
const docsDir = join(root, "docs", "methodology");
const docs = { overview: "" };
const overview = join(root, "METHODOLOGY.md");
if (existsSync(overview)) docs.overview = (await import("node:fs")).readFileSync(overview, "utf8");
for (const f of readdirSync(docsDir)) {
  if (f.endsWith(".md")) docs[f.replace(/\.md$/, "")] = (await import("node:fs")).readFileSync(join(docsDir, f), "utf8");
}
writeFileSync(join(out, "methodology.json"), JSON.stringify(docs));
console.log("prepared", readdirSync(out).join(", "));
