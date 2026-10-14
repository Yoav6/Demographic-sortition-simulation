<script lang="ts">
  import type { PresentedPerson, VarMeta } from "@popsim/sampler";
  import { loadAssembly, type Assembly } from "../lib/data.ts";
  import { COLOR_OPTIONS, groupColor, groupOf, type ColorOption } from "../lib/colorby.ts";
  import { drawAssembly, runQuery, modelInfo, type ModelInfo } from "../lib/worker-client.ts";
  import { t, type Lang } from "../lib/i18n.ts";
  import Hemicycle from "./Hemicycle.svelte";
  import MembersMap from "./MembersMap.svelte";
  import PersonCard from "./PersonCard.svelte";

  let { lang, params }: { lang: Lang; params: URLSearchParams } = $props();

  let published = $state<Assembly | null>(null);
  let custom = $state<{ seed: number; people: PresentedPerson[]; vars: VarMeta[]; model_version: string } | null>(null);
  let error = $state("");
  let optionId = $state("sector");
  let selected = $state<PresentedPerson | null>(null);
  let seedInput = $state("");
  let busy = $state(false);
  let popShares = $state<Record<string, Record<string, number>> | null>(null);
  let info = $state<ModelInfo | null>(null);
  const localities = $derived(info?.vars.find((v) => v.id === "locality")?.values ?? []);

  const option = $derived(COLOR_OPTIONS.find((o) => o.id === optionId)!);
  const people = $derived(custom ? custom.people : (published?.people ?? []));
  const vars = $derived(custom ? custom.vars : (published?.vars ?? []));
  const seed = $derived(custom ? custom.seed : published?.seed);
  const version = $derived(custom ? custom.model_version : published?.model_version);

  loadAssembly()
    .then((a) => (published = a))
    .catch((e) => (error = String(e)));

  // A custom seed in the URL (#/assembly?seed=123) shows an alternative assembly.
  $effect(() => {
    const s = params.get("seed");
    if (s && /^\d+$/.test(s)) void drawCustom(Number(s), false);
    else custom = null;
  });

  // Population shares for the legend, computed once in the worker from the model.
  $effect(() => {
    if (popShares) return;
    Promise.all([runQuery({}, 60_000, 7), modelInfo()]).then(([res, mi]) => {
      const out: Record<string, Record<string, number>> = {};
      for (const o of COLOR_OPTIONS) out[o.id] = sharesFor(o, res.marginals[o.variable]?.probs ?? [], mi);
      popShares = out;
      info = mi;
    });
  });

  function sharesFor(o: ColorOption, probs: number[], info: ModelInfo): Record<string, number> {
    if (o.expected) return o.expected;
    const v = info.vars.find((x) => x.id === o.variable);
    const out: Record<string, number> = {};
    v?.values?.forEach((val, i) => {
      const key = o.mapValue(v.numeric ? Number(val.id) : val.id);
      out[key] = (out[key] ?? 0) + (probs[i] ?? 0);
    });
    return out;
  }

  async function drawCustom(s: number, push = true) {
    busy = true;
    try {
      const r = await drawAssembly(s, 150);
      custom = { seed: s, ...r };
      if (push) location.hash = `#/assembly?seed=${s}`;
    } catch (e) {
      error = String(e);
    } finally {
      busy = false;
    }
  }

  const counts = $derived.by(() => {
    const c = new Map<string, number>();
    for (const p of people) c.set(groupOf(option, p), (c.get(groupOf(option, p)) ?? 0) + 1);
    return c;
  });

  function download(kind: "csv" | "json") {
    const rows = people.map((p) => ({ index: p.index, ...p.labels[lang] }));
    let blob: Blob;
    if (kind === "json") {
      blob = new Blob([JSON.stringify({ seed, model_version: version, people }, null, 1)], { type: "application/json" });
    } else {
      const cols = ["index", ...vars.map((v) => v.id)];
      const esc = (x: unknown) => {
        const s = x === undefined ? "" : String(x);
        return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
      };
      const header = ["#", ...vars.map((v) => (lang === "he" ? v.label.he : v.label.en))];
      const text = [header.map(esc).join(","), ...rows.map((r) => cols.map((c) => esc((r as Record<string, unknown>)[c])).join(","))].join("\n");
      blob = new Blob(["﻿" + text], { type: "text/csv" });
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `assembly-seed-${seed}.${kind}`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
</script>

{#if error}
  <p class="card">⚠ {error}</p>
{:else if !published}
  <p class="muted">…</p>
{:else}
  <section class="layout">
    <div class="chart card">
      <div class="controls">
        <label>
          {t("color_by", lang)}
          <select bind:value={optionId}>
            {#each COLOR_OPTIONS as o}
              <option value={o.id}>{o.label[lang]}</option>
            {/each}
          </select>
        </label>
        <span class="badge" class:custom={!!custom}>
          {custom ? t("custom_assembly", lang) : t("default_assembly", lang)}
        </span>
      </div>
      <Hemicycle {people} {option} {lang} onselect={(p) => (selected = p)} />
      <p class="muted meta tabular">
        {t("seed", lang)}: <code>{seed}</code> · {t("model_version", lang)}: <code>{version}</code> ·
        {t("population", lang)}: {published.population_label[lang]} ({published.population_total.toLocaleString(lang === "he" ? "he-IL" : "en-US")})
      </p>
      <div class="actions">
        <button onclick={() => download("csv")}>{t("download_csv", lang)}</button>
        <button onclick={() => download("json")}>{t("download_json", lang)}</button>
        {#if custom}
          <a href="#/assembly" class="back">{t("back_default", lang)}</a>
        {/if}
      </div>
      <details class="other-seed">
        <summary>{t("draw_other", lang)}</summary>
        <form onsubmit={(e) => { e.preventDefault(); if (/^\d+$/.test(seedInput)) drawCustom(Number(seedInput)); }}>
          <input inputmode="numeric" pattern="[0-9]*" bind:value={seedInput} placeholder="12345" aria-label={t("seed", lang)} />
          <button type="submit" disabled={busy}>{t("draw", lang)}</button>
        </form>
      </details>
    </div>

    <aside class="card legend" aria-label={option.label[lang]}>
      <h3>{option.label[lang]}</h3>
      <table class="tabular">
        <thead>
          <tr>
            <th></th>
            <th>{t("in_assembly", lang)}</th>
            <th>{t("in_population", lang)}</th>
          </tr>
        </thead>
        <tbody>
          {#each option.groups as g, i}
            {@const n = counts.get(g.key) ?? 0}
            {@const share = popShares?.[option.id]?.[g.key]}
            {#if n > 0 || (share ?? 0) > 0.001}
              <tr>
                <td><span class="swatch" style:background={groupColor(option, i)}></span>{g.label[lang]}</td>
                <td>{n}</td>
                <td class="muted">{share === undefined ? "…" : (share * 150).toFixed(1)}</td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
      <p class="muted note">
        {lang === "he"
          ? "״באוכלוסייה״ = מספר המושבים הצפוי לכל קבוצה מתוך 150, לפי המודל."
          : "“In the population” = expected seats out of 150 for each group, according to the model."}
      </p>
    </aside>
  </section>

  {#if localities.length}
    <section class="card map-card">
      <h3>{lang === "he" ? "היכן גרים חברי האספה" : "Where the members live"}</h3>
      <MembersMap {people} {option} {localities} {lang} onselect={(p) => (selected = p)} />
    </section>
  {/if}

  {#if selected}
    <div class="overlay" role="presentation" onclick={(e) => e.target === e.currentTarget && (selected = null)}>
      <div class="dialog" role="dialog" aria-modal="true">
        <PersonCard person={selected} {vars} {lang} seedInfo={`${t("seed", lang)} ${seed} · #${selected.index}`} onclose={() => (selected = null)} />
      </div>
    </div>
  {/if}
{/if}

<style>
  .map-card {
    margin-top: 1rem;
  }
  .map-card h3 {
    margin-top: 0;
  }
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 2.2fr) minmax(260px, 1fr);
    gap: 1rem;
    align-items: start;
  }
  .controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
  }
  .controls label {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  .badge {
    font-size: 0.85rem;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--text-secondary);
  }
  .badge.custom {
    background: var(--series-4);
    color: #111;
  }
  .meta {
    font-size: 0.85rem;
    margin: 0.4rem 0;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .other-seed {
    margin-top: 0.75rem;
  }
  .other-seed form {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
  .legend h3 {
    margin: 0 0 0.5rem;
  }
  .swatch {
    display: inline-block;
    width: 0.8rem;
    height: 0.8rem;
    border-radius: 50%;
    margin-inline-end: 0.4rem;
    vertical-align: -0.05rem;
  }
  .note {
    font-size: 0.8rem;
  }
  @media (max-width: 860px) {
    .layout {
      grid-template-columns: 1fr;
    }
  }
</style>
