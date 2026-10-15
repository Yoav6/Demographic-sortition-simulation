<!--
  The active filters as chips: accent-tinted for "show only", red for exclusions. Clicking a
  chip's text switches its mode (when it can be excluded); × removes it.
-->
<script lang="ts">
  import { t, type Lang } from "../lib/i18n.ts";

  let {
    items,
    lang,
    ontoggle,
    onremove,
    onclear,
  }: {
    items: { label: string; exclude: boolean; toggleable: boolean }[];
    lang: Lang;
    ontoggle: (i: number) => void;
    onremove: (i: number) => void;
    onclear: () => void;
  } = $props();
</script>

{#if items.length}
  <div class="chips">
    {#each items as f, i}
      <span class="chip" class:excluded={f.exclude}>
        {#if f.toggleable}
          <button onclick={() => ontoggle(i)} title={f.exclude ? t("make_include", lang) : t("make_exclude", lang)}>{f.label}</button>
        {:else}
          <span class="text">{f.label}</span>
        {/if}
        <button class="x" onclick={() => onremove(i)} aria-label={`${t("remove", lang)}: ${f.label}`}>×</button>
      </span>
    {/each}
    <button class="link" onclick={onclear}>{t("clear_filters", lang)}</button>
  </div>
{/if}

<style>
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
    margin-bottom: 0.25rem;
  }
  /* show-only filters are tinted with the accent, exclusions with red */
  .chip {
    --tone: var(--accent);
    display: inline-flex;
    border: 1px solid color-mix(in srgb, var(--tone) 55%, transparent);
    background: color-mix(in srgb, var(--tone) 14%, var(--surface-1));
    border-radius: 999px;
    font-size: 0.9rem;
    overflow: hidden;
  }
  .chip.excluded {
    --tone: var(--series-8);
  }
  .chip button,
  .chip .text {
    border: none;
    border-radius: 0;
    background: none;
    padding-block: 0.15rem;
    padding-inline: 0.7rem 0.3rem;
  }
  .chip .x {
    padding-inline: 0.3rem 0.6rem;
  }
  .link {
    border: none;
    background: none;
    padding: 0;
    color: var(--accent);
  }
</style>
