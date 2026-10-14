<script lang="ts">
  import { onMount } from "svelte";
  import { t, type Lang } from "./lib/i18n.ts";
  import AssemblyView from "./components/AssemblyView.svelte";
  import RandomPerson from "./components/RandomPerson.svelte";
  import Explorer from "./components/Explorer.svelte";
  import Methodology from "./components/Methodology.svelte";
  import Sources from "./components/Sources.svelte";

  type Page = "assembly" | "random" | "explore" | "method" | "sources";
  const PAGES: Page[] = ["assembly", "random", "explore", "method", "sources"];
  const NAV = { assembly: "nav_assembly", random: "nav_random", explore: "nav_explore", method: "nav_method", sources: "nav_sources" } as const;

  function readLang(): Lang {
    return new URLSearchParams(location.search).get("lang") === "en" ? "en" : "he";
  }

  function readRoute(): { page: Page; params: URLSearchParams; anchor: string } {
    const raw = location.hash.replace(/^#\/?/, "");
    const [path, query = ""] = raw.split("?");
    const [first, ...rest] = path.split("/");
    const page = (PAGES as string[]).includes(first) ? (first as Page) : "assembly";
    return { page, params: new URLSearchParams(query), anchor: rest.join("/") };
  }

  let lang = $state<Lang>(readLang());
  let route = $state(readRoute());

  function applyLang(l: Lang) {
    document.documentElement.lang = l;
    document.documentElement.dir = l === "he" ? "rtl" : "ltr";
  }

  function setLang(l: Lang) {
    lang = l;
    const url = new URL(location.href);
    if (l === "en") url.searchParams.set("lang", "en");
    else url.searchParams.delete("lang");
    history.replaceState(null, "", url);
    applyLang(l);
  }

  onMount(() => {
    applyLang(lang);
    const onHash = () => (route = readRoute());
    addEventListener("hashchange", onHash);
    return () => removeEventListener("hashchange", onHash);
  });
</script>

<header class="site-header">
  <div class="container header-row">
    <div class="titles">
      <h1>{t("title", lang)}</h1>
      <p class="secondary">{t("subtitle", lang)}</p>
    </div>
    <div class="lang-switch" role="group" aria-label="Language">
      <button class:active={lang === "he"} onclick={() => setLang("he")} lang="he">עברית</button>
      <button class:active={lang === "en"} onclick={() => setLang("en")} lang="en">English</button>
    </div>
  </div>
  <nav class="container tabs">
    {#each PAGES as p}
      <a href={`#/${p}`} class:active={route.page === p} aria-current={route.page === p ? "page" : undefined}>{t(NAV[p], lang)}</a>
    {/each}
  </nav>
</header>

<main class="container">
  {#if route.page === "assembly"}
    <AssemblyView {lang} params={route.params} />
  {:else if route.page === "random"}
    <RandomPerson {lang} params={route.params} />
  {:else if route.page === "explore"}
    <Explorer {lang} />
  {:else if route.page === "method"}
    <Methodology {lang} anchor={route.anchor} />
  {:else}
    <Sources {lang} />
  {/if}
</main>

<footer class="container footer muted">
  <p>
    {lang === "he"
      ? "סימולציה בלבד: כל אדם כאן הוא דמות סינתטית שהוגרלה ממודל סטטיסטי, לא אדם אמיתי."
      : "Simulation only: every person shown is a synthetic character drawn from a statistical model, not a real individual."}
    <a href="#/method">{t("nav_method", lang)}</a> · <a href="#/sources">{t("nav_sources", lang)}</a>
  </p>
</footer>

<style>
  .site-header {
    background: var(--surface-1);
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.25rem;
  }
  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    padding-top: 1rem;
  }
  h1 {
    margin: 0;
    font-size: 1.7rem;
    line-height: 1.2;
  }
  .titles p {
    margin: 0.25rem 0 0;
  }
  .lang-switch {
    display: flex;
    gap: 0.25rem;
    flex-shrink: 0;
  }
  .lang-switch button.active {
    background: var(--text-primary);
    color: var(--surface-1);
    border-color: var(--text-primary);
  }
  .tabs {
    display: flex;
    gap: 0.25rem;
    overflow-x: auto;
    padding-top: 0.75rem;
  }
  .tabs a {
    padding: 0.5rem 0.9rem;
    text-decoration: none;
    color: var(--text-secondary);
    border-bottom: 3px solid transparent;
    white-space: nowrap;
  }
  .tabs a.active {
    color: var(--text-primary);
    border-bottom-color: var(--accent);
    font-weight: 600;
  }
  .footer {
    margin-top: 3rem;
    padding-bottom: 2rem;
    font-size: 0.9rem;
  }
  @media (max-width: 640px) {
    h1 {
      font-size: 1.35rem;
    }
    .header-row {
      flex-direction: column;
    }
  }
</style>
