<!--
  A dropdown of attributes whose values open in a flyout beside the hovered attribute (on a
  phone, in place under it). Used to add filters to the members list and conditions to the
  explorer. Long value lists get a search box; numeric attributes get a from/to range.
-->
<script lang="ts" module>
  export interface MenuAttr {
    id: string;
    label: string;
    /** heading of the group of attributes this one starts (shown above it) */
    section?: string;
    values?: { id: string; label: string; alt?: string }[];
    /** numeric attribute: picked as a range within these bounds */
    range?: { min?: number; max?: number };
    /** whether it can be picked in exclude mode */
    excludable?: boolean;
  }
  export interface Pick {
    attr: string;
    value?: string;
    min?: number;
    max?: number;
    exclude: boolean;
  }
</script>

<script lang="ts">
  import { t, type Lang } from "../lib/i18n.ts";

  let {
    attrs,
    lang,
    label,
    withMode = false,
    onpick,
  }: { attrs: MenuAttr[]; lang: Lang; label: string; withMode?: boolean; onpick: (p: Pick) => void } = $props();

  const SEARCH_FROM = 15;

  let open = $state(false);
  let exclude = $state(false);
  // attribute whose values are showing in the flyout
  let active = $state("");
  let search = $state("");
  let range = $state<{ min?: number; max?: number }>({});
  let root: HTMLDivElement;

  const shown = $derived(attrs.filter((a) => !exclude || a.excludable));

  const normalize = (s: string) => s.toLocaleLowerCase().normalize("NFKD").replace(/[̀-֑ͯ-ׇ]/g, "");
  function valuesOf(a: MenuAttr) {
    const vals = a.values ?? [];
    const q = normalize(search.trim());
    return q ? vals.filter((v) => [v.label, v.alt].some((x) => x && normalize(x).includes(q))) : vals;
  }

  function activate(id: string) {
    if (active === id) return;
    active = id;
    search = "";
    range = {};
  }

  function close() {
    open = false;
    active = "";
  }

  function pick(p: Omit<Pick, "exclude">) {
    onpick({ ...p, exclude });
    close();
  }

  function onWindowClick(e: MouseEvent) {
    if (open && !root.contains(e.target as Node)) close();
  }
</script>

<svelte:window onclick={onWindowClick} onkeydown={(e) => e.key === "Escape" && close()} />

<div class="menu" bind:this={root}>
  <button class="menu-button" aria-haspopup="menu" aria-expanded={open} onclick={() => (open ? close() : (open = true))} disabled={!attrs.length}>
    {label} <span aria-hidden="true">▾</span>
  </button>
  {#if open}
    <ul class="popup" role="menu">
      {#if withMode}
        <li class="mode" role="none">
          <div role="radiogroup" aria-label={t("filter_mode", lang)}>
            <button role="radio" aria-checked={!exclude} class:on={!exclude} onclick={() => (exclude = false)} onpointerenter={() => (active = "")}>
              {t("show_only", lang)}
            </button>
            <button role="radio" aria-checked={exclude} class:on={exclude} onclick={() => (exclude = true)} onpointerenter={() => (active = "")}>
              {t("exclude", lang)}
            </button>
          </div>
        </li>
      {/if}
      {#each shown as a (a.id)}
        {#if a.section}
          <li class="section" role="presentation">{a.section}</li>
        {/if}
        <li class="attr" class:open={active === a.id} role="none" onpointerenter={(e) => e.pointerType === "mouse" && activate(a.id)}>
          <button role="menuitem" aria-haspopup="menu" aria-expanded={active === a.id} onclick={() => activate(a.id)}>
            {a.label} <span class="chevron" aria-hidden="true">›</span>
          </button>
          {#if active === a.id}
            {#if a.range}
              <form class="popup sub range" onsubmit={(e) => { e.preventDefault(); if (range.min !== undefined || range.max !== undefined) pick({ attr: a.id, ...range }); }}>
                <label>{t("from", lang)} <input type="number" bind:value={range.min} min={a.range.min} max={a.range.max} /></label>
                <label>{t("to", lang)} <input type="number" bind:value={range.max} min={a.range.min} max={a.range.max} /></label>
                <button type="submit" class="primary" disabled={range.min === undefined && range.max === undefined}>{t("add", lang)}</button>
              </form>
            {:else}
              {@const vals = valuesOf(a)}
              <ul class="popup sub" role="menu" aria-label={a.label} class:long={(a.values?.length ?? 0) >= SEARCH_FROM}>
                {#if (a.values?.length ?? 0) >= SEARCH_FROM}
                  <li role="none" class="search">
                    <!-- svelte-ignore a11y_autofocus -->
                    <input type="search" bind:value={search} placeholder={t("search", lang)} aria-label={t("search", lang)} autofocus />
                  </li>
                {/if}
                {#each vals.slice(0, 200) as v (v.id)}
                  <li role="none"><button role="menuitem" onclick={() => pick({ attr: a.id, value: v.id })}>{v.label}</button></li>
                {/each}
                {#if vals.length > 200}
                  <li role="none" class="more muted">+{vals.length - 200}</li>
                {/if}
              </ul>
            {/if}
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .menu {
    position: relative;
  }
  .menu-button {
    white-space: nowrap;
  }
  .popup {
    position: absolute;
    z-index: 10;
    top: calc(100% + 4px);
    inset-inline-start: 0;
    margin: 0;
    padding: 0.3rem 0;
    list-style: none;
    min-width: 13rem;
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: var(--shadow);
  }
  .attr {
    position: relative;
  }
  .popup button {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    width: 100%;
    border: none;
    border-radius: 0;
    background: none;
    text-align: start;
    padding: 0.35rem 0.9rem;
    white-space: nowrap;
  }
  .popup button:hover,
  .popup button:focus-visible,
  .attr.open > button {
    background: var(--surface-2);
  }
  .chevron {
    color: var(--text-muted);
  }
  :global([dir="rtl"]) .chevron {
    transform: scaleX(-1);
  }
  .section {
    padding: 0.5rem 0.9rem 0.15rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
  }
  .section:not(:first-child) {
    border-top: 1px solid var(--hairline);
    margin-top: 0.2rem;
  }
  /* the values open beside their attribute, in reading direction */
  .sub {
    top: -0.3rem;
    inset-inline-start: 100%;
  }
  .sub.long {
    max-height: 22rem;
    overflow-y: auto;
  }
  .search {
    position: sticky;
    top: -0.3rem;
    padding: 0.2rem 0.5rem 0.35rem;
    background: var(--surface-1);
  }
  .search input {
    width: 100%;
  }
  .more {
    padding: 0.2rem 0.9rem;
    font-size: 0.85rem;
  }
  .range {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.6rem 0.9rem;
  }
  .range label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.6rem;
  }
  .range input {
    width: 6rem;
  }
  .popup.range button.primary {
    justify-content: center;
    background: var(--accent);
    color: #fff;
    border-radius: 8px;
  }
  .popup.range button.primary:disabled {
    opacity: 0.5;
  }
  .mode {
    padding: 0.2rem 0.6rem 0.4rem;
    border-bottom: 1px solid var(--hairline);
    margin-bottom: 0.2rem;
  }
  .mode div {
    display: flex;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  .popup .mode button {
    justify-content: center;
    padding: 0.2rem 0.6rem;
    font-size: 0.9rem;
  }
  .popup .mode button.on {
    background: var(--text-primary);
    color: var(--surface-1);
  }
  /* no room beside it on a phone: the menu spans its row and values open in place, under the
     attribute */
  @media (max-width: 640px) {
    .menu {
      flex: 1 1 100%;
    }
    .menu-button {
      width: 100%;
    }
    .popup:not(.sub) {
      inset-inline: 0;
      max-height: 70vh;
      overflow-y: auto;
    }
    .sub {
      position: static;
      box-shadow: none;
      border: none;
      border-radius: 0;
      background: var(--surface-2);
      min-width: 0;
    }
    .sub button {
      padding-inline-start: 1.8rem;
    }
    .search {
      background: var(--surface-2);
    }
  }
</style>
