<script lang="ts">
  import type { Constraint, Evidence, QueryResult } from "@popsim/sampler";
  import type { PresentedPerson } from "@popsim/sampler";
  import { modelInfo, runQuery, type ModelInfo } from "../lib/worker-client.ts";
  import { loadAssembly, type Assembly } from "../lib/data.ts";
  import { t, type Lang } from "../lib/i18n.ts";
  import PersonCard from "./PersonCard.svelte";

  let { lang }: { lang: Lang } = $props();

  type Var = ModelInfo["vars"][number];
  interface Condition {
    varId: string;
    ids: string[]; // categorical
    min?: number;
    max?: number;
  }

  let info = $state<ModelInfo | null>(null);
  let conditions = $state<Condition[]>([]);
  let result = $state<QueryResult | null>(null);
  let running = $state(false);
  let newVar = $state("");
  let filterText = $state<Record<number, string>>({});

  let assembly = $state<Assembly | null>(null);
  let matches = $state<PresentedPerson[]>([]);
  let selected = $state<PresentedPerson | null>(null);

  modelInfo().then((i) => (info = i));
  loadAssembly().then((a) => (assembly = a));

  /** Members of the published assembly who satisfy every condition ("people like me"). */
  function matching(): PresentedPerson[] {
    if (!assembly) return [];
    return assembly.people.filter((p) =>
      conditions.every((c) => {
        const v = byId.get(c.varId)!;
        const x = p.values[c.varId];
        if (v.numeric) {
          if (c.min === undefined && c.max === undefined) return true;
          if (x === null || x === undefined) return false;
          const n = Number(x);
          return (c.min === undefined || n >= c.min) && (c.max === undefined || n <= c.max);
        }
        return !c.ids.length || c.ids.includes(String(x));
      }),
    );
  }

  /** Input bounds for a numeric condition (ages are 18-100; percentiles 0-100). */
  function bounds(v: Var): { min?: number; max?: number } {
    if (v.id === "age") return { min: 18, max: 100 };
    if (v.id.endsWith("_percentile")) return { min: 0, max: 100 };
    return { min: 0 };
  }

  const visible = $derived(info ? info.vars.filter((v) => !v.hidden) : []);
  const byId = $derived(new Map(visible.map((v) => [v.id, v])));
  const label = (v: { label: { he: string; en: string } }) => (lang === "he" ? v.label.he : v.label.en);

  function addCondition() {
    const v = byId.get(newVar);
    if (!v) return;
    conditions = [...conditions, v.numeric ? { varId: v.id, ids: [], min: undefined, max: undefined } : { varId: v.id, ids: [] }];
    newVar = "";
    result = null;
  }

  function evidence(): Evidence {
    const ev: Evidence = {};
    for (const c of conditions) {
      const v = byId.get(c.varId)!;
      let con: Constraint | null = null;
      if (v.numeric) {
        if (c.min !== undefined || c.max !== undefined) con = { min: c.min, max: c.max };
      } else if (c.ids.length) con = { ids: c.ids };
      if (con) ev[c.varId] = con;
    }
    return ev;
  }

  async function run() {
    running = true;
    try {
      result = await runQuery(evidence(), 150_000, 11);
      matches = matching();
    } finally {
      running = false;
    }
  }

  function options(v: Var, filter: string) {
    const f = filter.trim().toLowerCase();
    const vals = v.values ?? [];
    const list = f ? vals.filter((x) => x.label.he.includes(filter.trim()) || x.label.en.toLowerCase().includes(f)) : vals;
    return list.slice(0, 200);
  }

  function top(probs: number[], v: Var, k = 6) {
    return (v.values ?? [])
      .map((val, i) => ({ val, p: probs[i] ?? 0 }))
      .filter((x) => x.p > 0.0005)
      .sort((a, b) => b.p - a.p)
      .slice(0, k);
  }

  const fmtPct = (p: number) => `${(p * 100).toFixed(p < 0.1 ? 1 : 0)}%`;
</script>

<section>
  <p class="secondary">{t("explore_intro", lang)}</p>
  {#if !info}
    <p class="muted">{t("loading_model", lang)}</p>
  {:else}
    <div class="card conditions">
      {#each conditions as c, i}
        {@const v = byId.get(c.varId)!}
        <div class="condition">
          <strong>{label(v)}</strong>
          {#if v.numeric}
            {@const b = bounds(v)}
            <label>≥ <input type="number" bind:value={c.min} min={b.min} max={b.max} /></label>
            <label>≤ <input type="number" bind:value={c.max} min={b.min} max={b.max} /></label>
          {:else}
            {#if (v.values?.length ?? 0) > 30}
              <input placeholder="…" bind:value={filterText[i]} />
            {/if}
            <select multiple size={Math.min(6, v.values?.length ?? 1)} bind:value={c.ids}>
              {#each options(v, filterText[i] ?? "") as val}
                <option value={val.id}>{lang === "he" ? val.label.he : val.label.en}</option>
              {/each}
            </select>
          {/if}
          <button onclick={() => (conditions = conditions.filter((_, j) => j !== i))}>{t("remove", lang)}</button>
        </div>
      {/each}
      <div class="add">
        <select bind:value={newVar}>
          <option value="">{t("add_condition", lang)}…</option>
          {#each visible.filter((v) => !conditions.some((c) => c.varId === v.id)) as v}
            <option value={v.id}>{label(v)}</option>
          {/each}
        </select>
        <button onclick={addCondition} disabled={!newVar}>+</button>
        <button class="primary" onclick={run} disabled={running}>{running ? "…" : t("run", lang)}</button>
      </div>
    </div>

    {#if result}
      <div class="summary card tabular">
        <div><span class="muted">{t("matching_share", lang)}</span> <strong>{fmtPct(result.evidenceProbability)}</strong></div>
        <div><span class="muted">{t("expected_seats", lang)}</span> <strong>{(result.evidenceProbability * 150).toFixed(1)}</strong></div>
        <div><span class="muted">{t("effective_n", lang)}</span> <strong>{Math.round(result.effectiveSampleSize).toLocaleString()}</strong></div>
      </div>
      {#if assembly && conditions.length}
        <div class="card members">
          <h4>
            {lang === "he"
              ? `חברי האספה שפורסמה שעונים על התנאים: ${matches.length}`
              : `Members of the published assembly who match: ${matches.length}`}
          </h4>
          <div class="chips">
            {#each matches.slice(0, 30) as p (p.index)}
              <button class="chip" onclick={() => (selected = p)}>{p.labels[lang].first_name}, {p.labels[lang].age}</button>
            {/each}
            {#if matches.length > 30}<span class="muted">+{matches.length - 30}</span>{/if}
          </div>
        </div>
      {/if}
      {#if result.effectiveSampleSize < 200}
        <p class="warn">⚠ {lang === "he" ? "מעט מאוד אנשים עונים על התנאים — ההערכות לא יציבות." : "Very few people match — estimates are unstable."}</p>
      {/if}
      <div class="grid">
        {#each visible.filter((v) => !conditions.some((c) => c.varId === v.id)) as v}
          {@const m = result.marginals[v.id]}
          {#if m}
            <div class="card dist">
              <h4>{label(v)}</h4>
              {#if m.probs && !v.numeric}
                {#each top(m.probs, v) as row}
                  <div class="bar-row">
                    <span class="name">{lang === "he" ? row.val.label.he : row.val.label.en}</span>
                    <span class="bar"><span style:width={`${Math.max(row.p * 100, 0.5)}%`}></span></span>
                    <span class="pct tabular">{fmtPct(row.p)}</span>
                  </div>
                {/each}
              {:else if m.probs && v.numeric}
                {@const vals = (v.values ?? []).map((val, i) => ({ x: Number(val.id), p: m.probs![i] ?? 0 }))}
                {@const mean = vals.reduce((a, r) => a + r.x * r.p, 0)}
                <p class="tabular">{lang === "he" ? "ממוצע" : "mean"}: <strong>{mean.toFixed(1)}</strong></p>
              {:else if m.quantiles}
                {#if (m.applicable ?? 1) <= 0}
                  <p class="muted">{lang === "he" ? "לא רלוונטי לאף אחד מהם" : "applies to none of them"}</p>
                {:else}
                  <p class="tabular">{lang === "he" ? "חציון" : "median"}: <strong>{m.quantiles[2].toLocaleString()}</strong> ({m.quantiles[1].toLocaleString()}–{m.quantiles[3].toLocaleString()})</p>
                  {#if (m.applicable ?? 1) < 0.995}
                    <p class="muted small">{lang === "he" ? `רלוונטי ל-${fmtPct(m.applicable ?? 0)} מהם` : `applies to ${fmtPct(m.applicable ?? 0)} of them`}</p>
                  {/if}
                {/if}
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    {/if}
  {/if}
  {#if selected && assembly}
    <div class="overlay" role="presentation" onclick={(e) => e.target === e.currentTarget && (selected = null)}>
      <div class="dialog" role="dialog" aria-modal="true">
        <PersonCard person={selected} vars={assembly.vars} {lang} seedInfo={`${t("seed", lang)} ${assembly.seed} · #${selected.index}`} onclose={() => (selected = null)} />
      </div>
    </div>
  {/if}
</section>

<style>
  .conditions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .condition {
    display: flex;
    gap: 0.6rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .condition select[multiple] {
    min-width: 220px;
  }
  .condition input[type="number"] {
    width: 5rem;
  }
  .add {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .summary {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    margin: 1rem 0;
  }
  .warn {
    color: var(--series-8);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.75rem;
  }
  .dist h4 {
    margin: 0 0 0.5rem;
  }
  .bar-row {
    display: grid;
    grid-template-columns: minmax(0, 1.3fr) 1fr 3.2rem;
    gap: 0.5rem;
    align-items: center;
    font-size: 0.9rem;
  }
  .name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .bar {
    background: var(--surface-2);
    height: 0.6rem;
    border-radius: 4px;
    overflow: hidden;
  }
  .bar span {
    display: block;
    height: 100%;
    background: var(--series-1);
    border-radius: 4px;
  }
  .pct {
    text-align: end;
  }
  .members {
    margin-bottom: 1rem;
  }
  .members h4 {
    margin: 0 0 0.5rem;
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
  }
  .chip {
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    font-size: 0.9rem;
  }
  .small {
    font-size: 0.85rem;
    margin: 0.2rem 0 0;
  }
</style>
