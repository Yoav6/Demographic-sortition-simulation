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
  const sections = $derived(
    SECTIONS.map((s) => ({
      ...s,
      rows: s.lines
        .filter((l) => meta.has(l.doc))
        .map((l) => ({ label: (l.label ?? meta.get(l.doc)!.label)[lang], value: l.value(person, lang), doc: meta.get(l.doc)!.doc }))
        .filter((r) => r.value !== null && r.value !== undefined && r.value !== ""),
    })),
  );
</script>

<article class="card person" aria-label={t("person", lang)}>
  <header>
    <h2>{person.labels[lang].first_name}</h2>
    {#if onclose}
      <button class="close" onclick={onclose} aria-label={t("close", lang)}>✕</button>
    {/if}
  </header>
  <p class="bio">{person.text[lang].join(" ")}</p>
  {#each sections as s (s.id)}
    <h3>{s.label[lang]}</h3>
    <table>
      <tbody>
        {#each s.rows as r}
          <tr>
            <td class="secondary">{r.label}</td>
            <td>{r.value}</td>
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
</style>
