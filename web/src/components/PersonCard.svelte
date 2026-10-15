<script lang="ts">
  import type { PresentedPerson, VarMeta } from "@popsim/sampler";
  import { SECTIONS } from "../lib/card.ts";
  import { t, type Lang } from "../lib/i18n.ts";

  let {
    person,
    vars,
    lang,
    seedInfo = "",
    onclose,
  }: { person: PresentedPerson; vars: VarMeta[]; lang: Lang; seedInfo?: string; onclose?: () => void } = $props();

  const docAnchor = (doc?: string) => (doc ? `#/method/${doc.replace(/^.*\//, "").replace(/\.md$/, "")}` : "#/method");
  const meta = $derived(new Map(vars.map((v) => [v.id, v])));
  const unusual = $derived(person.unusual);
  const unusualText = $derived(unusual?.text[lang]);
  const LEVELS = ["major", "notable", "minor"] as const;
  type Level = (typeof LEVELS)[number];
  // the person's deviations with their wording, in order, and grouped by significance
  const items = $derived(
    (unusual?.reasons ?? []).map((r, i) => ({
      variable: r.variable,
      level: r.level as Level,
      bits: r.bits,
      text: unusualText!.reasons[i],
      detail: unusualText!.details?.[i] ?? "",
    })),
  );
  const byLevel = $derived(LEVELS.map((l) => ({ level: l, items: items.filter((x) => x.level === l) })).filter((g) => g.items.length));
  // marker on the rows a deviation concerns: the strongest level among them, all their texts as tooltip
  function markerFor(vars: string[]): { level: Level; title: string } | null {
    const hits = items.filter((x) => vars.includes(x.variable));
    if (!hits.length) return null;
    const level = LEVELS.find((l) => hits.some((h) => h.level === l))!;
    return { level, title: hits.map((h) => `${unusualText!.levels[h.level]}: ${h.text}\n${h.detail}`).join("\n\n") };
  }
  const sections = $derived(
    SECTIONS.map((s) => ({
      ...s,
      rows: s.lines
        .filter((l) => meta.has(l.doc))
        .map((l) => ({
          label: (l.label ?? meta.get(l.doc)!.label)[lang],
          value: l.value(person, lang),
          doc: meta.get(l.doc)!.doc,
          surprise: markerFor(l.vars ?? [l.doc]),
        }))
        .filter((r) => r.value !== null && r.value !== undefined && r.value !== ""),
    })),
  );
</script>

<article class="card person" aria-label={t("person", lang)}>
  <header>
    <h2>
      {person.labels[lang].first_name}
      {#if unusualText?.name_note}<span class="name-note" title={unusualText.name_note} aria-label={unusualText.name_note}>ⓘ</span>{/if}
    </h2>
    {#if onclose}
      <button class="close" onclick={onclose} aria-label={t("close", lang)}>✕</button>
    {/if}
  </header>
  <p class="bio">{person.text[lang].join(" ")}</p>
  {#if unusual && unusualText}
    <section class="unusual" aria-label={unusualText.title}>
      <h3>
        {unusualText.title}
        <span class="how"><a href="#/method/unusual" title={t("how_estimated", lang)} aria-label={t("how_estimated", lang)}>?</a></span>
      </h3>
      <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow={Math.round(unusual.percentile)} aria-label={unusualText.headline}>
        <div class="fill" style:inline-size={`${Math.max(2, unusual.percentile)}%`}></div>
      </div>
      <p><strong>{unusualText.tier}</strong> — {unusualText.headline}</p>
      {#if items.length}
        {#if unusualText.summary}<p class="small muted">{unusualText.summary}</p>{/if}
        {#each byLevel as g (g.level)}
          <div class="group">
            <h4 class={g.level}>{unusualText.level_titles[g.level]}</h4>
            <ul>
              {#each g.items as r}
                <li>
                  {r.text}
                  {#if r.detail}<div class="detail">{r.detail}</div>{/if}
                </li>
              {/each}
            </ul>
          </div>
        {/each}
      {:else}
        <p class="muted">{unusualText.reasons[0]}</p>
      {/if}
    </section>
  {/if}
  {#each sections as s (s.id)}
    <h3>{s.label[lang]}</h3>
    <table>
      <tbody>
        {#each s.rows as r}
          <tr>
            <td class="secondary">{r.label}</td>
            <td>
              {r.value}
              {#if r.surprise}<span class="surprise {r.surprise.level}" title={r.surprise.title} aria-label={r.surprise.title}>◆</span>{/if}
            </td>
            <td class="how"><a href={docAnchor(r.doc)} title={t("how_estimated", lang)} aria-label={t("how_estimated", lang)}>?</a></td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/each}
  {#if seedInfo}
    <p class="muted small">{seedInfo}</p>
  {/if}
</article>

<style>
  .person header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  h2 {
    margin: 0;
    font-size: 1.5rem;
  }
  h3 {
    margin: 1.25rem 0 0.25rem;
    font-size: 1rem;
  }
  table {
    width: 100%;
  }
  td.secondary {
    width: 40%;
  }
  .bio {
    font-size: 1.08rem;
    line-height: 1.6;
  }
  .close {
    border: none;
    background: transparent;
    font-size: 1.2rem;
  }
  .how a {
    display: inline-block;
    width: 1.4rem;
    height: 1.4rem;
    border-radius: 50%;
    border: 1px solid var(--border);
    text-align: center;
    line-height: 1.3rem;
    text-decoration: none;
    font-size: 0.85rem;
  }
  .small {
    font-size: 0.85rem;
  }
  .name-note {
    font-size: 0.9rem;
    color: var(--text-muted);
    cursor: help;
  }
  .unusual h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .unusual p {
    margin: 0.4rem 0 0.25rem;
  }
  .unusual ul {
    margin: 0;
    padding-inline-start: 1.2rem;
    line-height: 1.5;
  }
  .unusual li + li {
    margin-top: 0.25rem;
  }
  .detail {
    font-size: 0.85rem;
    color: var(--text-muted);
  }
  .unusual h4 {
    margin: 0.75rem 0 0.2rem;
    font-size: 0.9rem;
  }
  .group:has(.minor) ul {
    font-size: 0.92rem;
    color: var(--text-secondary);
  }
  .meter {
    block-size: 0.5rem;
    border-radius: 0.25rem;
    background: var(--surface-2);
    overflow: hidden;
  }
  .meter .fill {
    block-size: 100%;
    background: var(--ramp-2);
  }
  .surprise {
    font-size: 0.75rem;
    margin-inline-start: 0.35rem;
    cursor: help;
  }
  /* significance: red = major (16x or more less common), orange = notable, amber = minor */
  .major {
    color: var(--series-8);
  }
  .notable {
    color: var(--series-2);
  }
  .minor {
    color: var(--series-4);
  }
</style>
