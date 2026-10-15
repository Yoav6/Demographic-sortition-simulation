<script lang="ts">
  import type { Constraint, Evidence, QueryResult } from "@popsim/sampler";
  import type { PresentedPerson } from "@popsim/sampler";
  import { modelInfo, runQuery, type ModelInfo } from "../lib/worker-client.ts";
  import { loadAssembly, type Assembly } from "../lib/data.ts";
  import { t, type Lang } from "../lib/i18n.ts";
  import { SECTIONS } from "../lib/card.ts";
  import { similarity, type Similar } from "../lib/similarity.ts";
  import PersonCard from "./PersonCard.svelte";
  import AttributeMenu, { type MenuAttr, type Pick } from "./AttributeMenu.svelte";
  import FilterChips from "./FilterChips.svelte";

  let { lang }: { lang: Lang } = $props();

  type Var = ModelInfo["vars"][number];
  /** One chip: a value to require (or rule out), or a numeric range. Several values of one
   * categorical attribute mean "any of them"; of a multi-valued one, "all of them". */
  interface Condition {
    varId: string;
    value?: string;
    min?: number;
    max?: number;
    exclude: boolean;
  }

  let info = $state<ModelInfo | null>(null);
  let conditions = $state<Condition[]>([]);
  let result = $state<QueryResult | null>(null);
  let running = $state(false);

  let assembly = $state<Assembly | null>(null);
  let matches = $state<PresentedPerson[]>([]);
  // the closest members who do not match exactly
  let similar = $state<Similar[]>([]);
  const SIMILAR_MIN = 0.5;
  let selected = $state<PresentedPerson | null>(null);

  modelInfo().then((i) => (info = i));
  loadAssembly().then((a) => (assembly = a));

  /** Each condition attribute's constraint: a range, the items a multi-valued attribute must
   * include, or the allowed values of a categorical one. */
  function evidence(): Evidence {
    const ev: Evidence = {};
    for (const id of new Set(conditions.map((c) => c.varId))) {
      const v = byId.get(id)!;
      const cs = conditions.filter((c) => c.varId === id);
      if (v.numeric) {
        const r = cs[cs.length - 1];
        ev[id] = { min: r.min, max: r.max };
      } else if (v.multi) {
        ev[id] = { ids: cs.map((c) => c.value!) };
      } else {
        const inc = cs.filter((c) => !c.exclude).map((c) => c.value!);
        const exc = new Set(cs.filter((c) => c.exclude).map((c) => c.value!));
        const base = inc.length ? inc : (v.values ?? []).map((x) => x.id);
        ev[id] = { ids: base.filter((x) => !exc.has(x)) };
      }
    }
    return ev;
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
  const other = (l: { he: string; en: string }) => (lang === "he" ? l.en : l.he);

  // attributes in the member card's order and sections; the rest under "Other"
  const ordered = $derived.by(() => {
    const out: { v: Var; section: string }[] = [];
    const seen = new Set<string>();
    const add = (id: string, section: string) => {
      const v = byId.get(id);
      if (v && !seen.has(id)) out.push({ v, section }), seen.add(id);
    };
    for (const s of SECTIONS) for (const l of s.lines) for (const id of l.vars ?? [l.doc]) add(id, s.label[lang]);
    for (const v of visible) add(v.id, lang === "he" ? "אחר" : "Other");
    return out;
  });

  const menuAttrs = $derived<MenuAttr[]>(
    ordered
      .map(({ v, section }, i): MenuAttr => {
        const used = new Set(conditions.filter((c) => c.varId === v.id).map((c) => c.value));
        return {
          id: v.id,
          label: label(v),
          section: i === 0 || ordered[i - 1].section !== section ? section : undefined,
          range: v.numeric ? bounds(v) : undefined,
          values: v.numeric ? undefined : (v.values ?? []).filter((x) => !used.has(x.id)).map((x) => ({ id: x.id, label: label(x), alt: other(x.label) })),
          excludable: !v.numeric && !v.multi,
        };
      })
      .filter((a) => a.range || a.values?.length),
  );

  function addCondition(p: Pick) {
    const c: Condition = { varId: p.attr, value: p.value, min: p.min, max: p.max, exclude: p.exclude };
    // a new range replaces the attribute's old one
    conditions = [...conditions.filter((x) => !(p.value === undefined && x.varId === p.attr)), c];
    result = null;
  }

  function conditionLabel(c: Condition): string {
    const v = byId.get(c.varId)!;
    if (v.numeric) {
      const r = c.min !== undefined && c.max !== undefined ? `${c.min}–${c.max}` : c.min !== undefined ? `≥ ${c.min}` : `≤ ${c.max}`;
      return `${label(v)}: ${r}`;
    }
    const val = v.values?.find((x) => x.id === c.value);
    const text = val ? label(val) : c.value;
    return `${label(v)}: ${c.exclude ? `${t("not", lang)} ${text}` : text}`;
  }

  async function run() {
    running = true;
    try {
      const ev = evidence();
      result = await runQuery(ev, 150_000, 11);
      const scored = assembly ? similarity(assembly.people, ev, byId).sort((a, b) => b.score - a.score || a.person.index - b.person.index) : [];
      matches = scored.filter((x) => x.score === 1).map((x) => x.person);
      similar = scored.filter((x) => x.score < 1 && x.score >= SIMILAR_MIN);
    } finally {
      running = false;
    }
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
      <FilterChips
        items={conditions.map((c) => ({ label: conditionLabel(c), exclude: c.exclude, toggleable: c.value !== undefined && !byId.get(c.varId)!.multi }))}
        {lang}
        ontoggle={(i) => ((conditions = conditions.map((c, j) => (j === i ? { ...c, exclude: !c.exclude } : c))), (result = null))}
        onremove={(i) => ((conditions = conditions.filter((_, j) => j !== i)), (result = null))}
        onclear={() => ((conditions = []), (result = null))}
      />
      <div class="add">
        <AttributeMenu attrs={menuAttrs} {lang} label={t("add_condition", lang)} withMode onpick={addCondition} />
        <button class="primary" onclick={run} disabled={running}>{running ? "…" : t("run", lang)}</button>
      </div>
    </div>

    {#if result}
      <div class="summary card tabular">
        <div><span class="muted">{t("matching_share", lang)}</span> <strong>{fmtPct(result.evidenceProbability)}</strong></div>
        <div><span class="muted">{t("expected_seats", lang)}</span> <strong>{(result.evidenceProbability * 150).toFixed(1)}</strong></div>
        <div><span class="muted help" title={t("effective_n_help", lang)}>{t("effective_n", lang)} <span aria-hidden="true">ⓘ</span></span> <strong>{Math.round(result.effectiveSampleSize).toLocaleString()}</strong></div>
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
          {#if similar.length}
            <details class="similar-box">
            <summary><h4>{lang === "he" ? `הקרובים ביותר שאינם עונים על כל התנאים: ${similar.length}` : `Closest members who don't match exactly: ${similar.length}`}</h4></summary>
            <ul class="similar">
              {#each similar as s (s.person.index)}
                {@const p = s.person}
                <li>
                  <button onclick={() => (selected = p)}>
                    <span class="score tabular" title={lang === "he" ? "ציון דמיון" : "Similarity score"}>{Math.round(s.score * 100)}%</span>
                    <span class="who">{p.labels[lang].first_name}, {p.labels[lang].age} · <span class="muted">{p.labels[lang].locality}</span></span>
                    <span class="misses secondary">
                      {lang === "he" ? "שונה ב:" : "differs in:"}
                      {s.misses.map((id) => `${label(byId.get(id)!)} (${p.labels[lang][id]})`).join("; ")}
                    </span>
                  </button>
                </li>
              {/each}
            </ul>
            <p class="muted small">
              {lang === "he"
                ? "ציון הדמיון הוא ממוצע ההתאמה לכל תנאי, כשהתאמה מלאה מקבלת 100%. בסולמות מדורגים (השכלה, הכנסה, מספר ילדים…) ובטווחים מספריים ערך קרוב מקבל ניקוד חלקי. מוצגים כל בעלי ציון של 50% ומעלה."
                : "The similarity score is the average fit to each condition: a full match is 100%; on ordered scales (education, income, number of children, ...) and numeric ranges a nearby value gets partial credit. All members scoring 50% or more are shown."}
            </p>
            </details>
          {/if}
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
  .help {
    cursor: help;
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
  .similar-box {
    margin-top: 1rem;
  }
  .similar-box summary {
    cursor: pointer;
  }
  .similar-box summary h4 {
    display: inline;
  }
  .similar {
    list-style: none;
    margin: 0 0 0.5rem;
    padding: 0;
  }
  .similar button {
    display: grid;
    grid-template-columns: 3.2rem minmax(0, 12rem) minmax(0, 1fr);
    gap: 0.75rem;
    align-items: baseline;
    width: 100%;
    text-align: start;
    border: none;
    border-bottom: 1px solid var(--hairline);
    border-radius: 0;
    background: none;
    padding: 0.4rem 0.2rem;
  }
  .similar button:hover {
    background: var(--surface-2);
  }
  .score {
    font-weight: 600;
  }
  .misses {
    font-size: 0.9rem;
  }
  @media (max-width: 640px) {
    .similar button {
      grid-template-columns: 3.2rem minmax(0, 1fr);
    }
    .misses {
      grid-column: 2;
    }
  }
  .small {
    font-size: 0.85rem;
    margin: 0.2rem 0 0;
  }
</style>
