<script lang="ts">
  import { untrack } from "svelte";
  import type { PresentedPerson, VarMeta } from "@popsim/sampler";
  import { drawPerson, randomSeed, warmModel } from "../lib/worker-client.ts";
  import { t, type Lang } from "../lib/i18n.ts";
  import PersonCard from "./PersonCard.svelte";

  let { lang, params }: { lang: Lang; params: URLSearchParams } = $props();

  let person = $state<PresentedPerson | null>(null);
  let vars = $state<VarMeta[]>([]);
  let seed = $state<number | null>(null);
  let loading = $state(false);
  let copied = $state(false);
  let error = $state<string | null>(null);

  async function draw(s: number) {
    loading = true;
    try {
      const r = await drawPerson(s, 0);
      person = r.person;
      vars = r.vars;
      seed = s;
      error = null;
      history.replaceState(null, "", `${location.pathname}${location.search}#/random?seed=${s}`);
    } catch (e) {
      error = `${t("draw_failed", lang)} ${e instanceof Error ? e.message : e} (${t("seed", lang)} ${s})`;
    } finally {
      loading = false;
    }
  }

  warmModel();

  $effect(() => {
    const s = params.get("seed");
    // react to the URL only: reading `seed` here would redraw the URL's person after each click
    // (the URL's seed is replaced without a route change, so `params` keeps the old one)
    if (s && /^\d+$/.test(s) && Number(s) !== untrack(() => seed)) void draw(Number(s));
  });

  async function copyLink() {
    await navigator.clipboard.writeText(location.href);
    copied = true;
    setTimeout(() => (copied = false), 1500);
  }
</script>

<section class="random">
  <p class="secondary intro">{t("random_intro", lang)}</p>
  <div class="row">
    <button class="primary" onclick={() => draw(randomSeed())} disabled={loading}>
      {loading ? t("loading_model", lang) : t("draw_person", lang)}
    </button>
    {#if seed !== null}
      <span class="muted tabular">{t("seed", lang)}: <code>{seed}</code></span>
      <button onclick={copyLink}>{copied ? t("copied", lang) : t("copy_link", lang)}</button>
    {/if}
  </div>
  {#if error}
    <p class="error" role="alert">{error}</p>
  {/if}
  {#if person}
    <PersonCard {person} {vars} {lang} />
  {/if}
</section>

<style>
  .random {
    max-width: 720px;
  }
  .intro {
    margin-top: 0;
  }
  .error {
    color: var(--series-8);
  }
  .row {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }
</style>
