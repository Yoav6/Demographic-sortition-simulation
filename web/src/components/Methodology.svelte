<script lang="ts">
  import { Marked } from "marked";
  import { loadMethodology } from "../lib/data.ts";
  import { t, type Lang } from "../lib/i18n.ts";
  import { modelInfo, type GraphNode } from "../lib/worker-client.ts";
  import ModelGraph from "./ModelGraph.svelte";

  let { lang, anchor }: { lang: Lang; anchor: string } = $props();

  let docs = $state<Record<string, string> | null>(null);
  let graph = $state<GraphNode[] | null>(null);
  loadMethodology().then((d) => (docs = d));
  modelInfo().then((i) => (graph = i.nodes));

  // Each methodology doc may start with a Hebrew summary block:
  //   <!-- he-summary --> ... <!-- /he-summary -->
  function split(md: string): { he: string; body: string } {
    const m = md.match(/<!-- he-summary -->([\s\S]*?)<!-- \/he-summary -->/);
    return { he: m ? m[1].trim() : "", body: md.replace(/<!-- he-summary -->[\s\S]*?<!-- \/he-summary -->/, "") };
  }

  const order = $derived(docs ? Object.keys(docs).filter((k) => k !== "overview").sort() : []);
  const current = $derived(anchor && docs?.[anchor] ? anchor : "overview");

  // The docs are written for GitHub, so their relative links point at repo files. Map them to the
  // site's own pages where one exists (a cited source -> its entry on the Sources page), else to
  // the file on GitHub.
  const REPO = "https://github.com/Yoav6/popsim/blob/main/";
  function siteHref(href: string, base: string): string {
    if (/^([a-z][a-z0-9+.-]*:|#)/i.test(href)) return href;
    const [path, frag = ""] = href.split("#");
    const file = new URL(path, `https://repo/${base}`).pathname.slice(1);
    if (file === "SOURCES.md") return frag ? `#/sources/${frag}` : "#/sources";
    if (file === "METHODOLOGY.md") return "#/method";
    const doc = file.match(/^docs\/methodology\/([^/]+)\.md$/);
    if (doc) return `#/method/${doc[1]}`;
    return REPO + file + (frag ? `#${frag}` : "");
  }
  const parser = (base: string) =>
    new Marked({
      walkTokens(token) {
        if (token.type === "link") token.href = siteHref(token.href, base);
      },
    });
  const rootDoc = parser("");
  const nodeDoc = parser("docs/methodology/");
  const render = (key: string, md: string) => (key === "overview" ? rootDoc : nodeDoc).parse(md) as string;

  function title(md: string): string {
    return md.match(/^#\s+(.+)$/m)?.[1] ?? "";
  }
</script>

<section class="method">
  <p class="secondary">{t("method_intro", lang)}</p>
  {#if docs}
    <nav class="toc card">
      <a href="#/method" class:active={current === "overview"}>{lang === "he" ? "סקירה כללית" : "Overview"}</a>
      {#each order as key}
        <a href={`#/method/${key}`} class:active={current === key}>{title(docs[key]) || key}</a>
      {/each}
    </nav>
    <div class="content">
      {#if current === "overview" && graph}
        <section class="card structure">
          <h3>{lang === "he" ? "מבנה המודל" : "Model structure"}</h3>
          <ModelGraph nodes={graph} {lang} />
        </section>
      {/if}
      <article class="card doc" dir="ltr" lang="en">
        {#if lang === "he" && split(docs[current]).he}
          <div class="he-summary" dir="rtl" lang="he">{@html render(current, split(docs[current]).he)}</div>
        {/if}
        {@html render(current, split(docs[current]).body)}
      </article>
    </div>
  {:else}
    <p class="muted">…</p>
  {/if}
</section>

<style>
  .content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-width: 0;
  }
  .structure h3 {
    margin-top: 0;
  }
  .method {
    display: grid;
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 1rem;
    align-items: start;
  }
  .method > p {
    grid-column: 1 / -1;
    margin: 0;
  }
  .toc {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    position: sticky;
    top: 1rem;
  }
  .toc a {
    text-decoration: none;
    color: var(--text-secondary);
    padding: 0.2rem 0.4rem;
    border-radius: 6px;
  }
  .toc a.active {
    background: var(--surface-2);
    color: var(--text-primary);
    font-weight: 600;
  }
  .doc :global(table) {
    font-size: 0.9rem;
    display: block;
    overflow-x: auto;
  }
  .doc :global(code) {
    background: var(--surface-2);
    padding: 0 0.25rem;
    border-radius: 4px;
    font-size: 0.88em;
  }
  .doc :global(pre) {
    overflow-x: auto;
    background: var(--surface-2);
    padding: 0.75rem;
    border-radius: 8px;
  }
  .he-summary {
    background: var(--surface-2);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-bottom: 1rem;
  }
  @media (max-width: 760px) {
    .method {
      grid-template-columns: 1fr;
    }
    .toc {
      position: static;
    }
  }
</style>
