<script lang="ts">
  import type { PresentedPerson, VarMeta } from "@popsim/sampler";
  import { t, type Lang } from "../lib/i18n.ts";

  let {
    person,
    vars,
    lang,
    seedInfo = "",
    onclose,
  }: { person: PresentedPerson; vars: VarMeta[]; lang: Lang; seedInfo?: string; onclose?: () => void } = $props();

  const docAnchor = (doc?: string) => (doc ? `#/method/${doc.replace(/^.*\//, "").replace(/\.md$/, "")}` : "#/method");
  const varLabel = (v: VarMeta) => (lang === "he" ? v.label.he : v.label.en);
</script>

<article class="card person" aria-label={t("person", lang)}>
  <header>
    <h2>{person.labels[lang].first_name}</h2>
    {#if onclose}
      <button class="close" onclick={onclose} aria-label={t("close", lang)}>✕</button>
    {/if}
  </header>
  <p class="bio">{person.text[lang].join(" ")}</p>
  <table>
    <thead>
      <tr><th>{t("attribute", lang)}</th><th>{t("value", lang)}</th><th></th></tr>
    </thead>
    <tbody>
      {#each vars as v}
        {#if person.labels[lang][v.id] !== undefined && v.id !== "first_name"}
          <tr>
            <td class="secondary">{varLabel(v)}</td>
            <td>{person.labels[lang][v.id]}</td>
            <td class="how"><a href={docAnchor(v.doc)} title={t("how_estimated", lang)} aria-label={t("how_estimated", lang)}>?</a></td>
          </tr>
        {/if}
      {/each}
    </tbody>
  </table>
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
