<script lang="ts">
  import type { PresentedPerson, VarMeta } from "@popsim/sampler";
  import { COLOR_OPTIONS, groupOf } from "../lib/colorby.ts";
  import { t, type Lang } from "../lib/i18n.ts";

  let {
    people,
    vars,
    lang,
    onselect,
  }: { people: PresentedPerson[]; vars: VarMeta[]; lang: Lang; onselect: (p: PresentedPerson) => void } = $props();

  type Key = number | string | null;
  interface Column {
    /** model variable shown (or "index" / "unusual") */
    id: string;
    label: { he: string; en: string };
    text: (p: PresentedPerson) => string;
    /** sort key; defaults to the colour-by group order (when there is an option for the
     * variable), then the shown text */
    key?: (p: PresentedPerson) => Key;
  }

  const optionFor = new Map(COLOR_OPTIONS.map((o) => [o.id, o]));
  const lab = (id: string) => (p: PresentedPerson) => p.labels[lang][id] ?? "";
  const L = (he: string, en: string) => ({ he, en });
  // short headings (the model's attribute labels are written for the member card)
  const COLUMNS: Column[] = [
    { id: "index", label: L("#", "#"), text: (p) => String(p.index + 1), key: (p) => p.index },
    { id: "first_name", label: L("שם", "Name"), text: lab("first_name") },
    { id: "sex", label: L("מין", "Sex"), text: lab("sex") },
    { id: "age", label: L("גיל", "Age"), text: lab("age"), key: (p) => Number(p.values.age) },
    { id: "locality", label: L("יישוב", "Locality"), text: lab("locality") },
    { id: "sector", label: L("מגזר", "Sector"), text: lab("sector") },
    { id: "religiosity", label: L("מידת דתיות", "Religiosity"), text: lab("religiosity") },
    { id: "education", label: L("השכלה", "Education"), text: lab("education") },
    { id: "labour_status", label: L("תעסוקה", "Work"), text: lab("labour_status") },
    { id: "vote_2022", label: L("בחירות 2022", "2022 election"), text: lab("vote_2022") },
    {
      id: "unusual",
      label: L("יוצא/ת דופן", "Unusual"),
      text: (p) => p.unusual?.text[lang].tier ?? "",
      key: (p) => p.unusual?.percentile ?? null,
    },
  ];

  // columns whose variable the assembly has (a custom draw from an older model may lack some)
  const varIds = $derived(new Set(vars.map((v) => v.id)));
  const columns = $derived(COLUMNS.filter((c) => c.id === "index" || c.id === "unusual" || varIds.has(c.id)));

  let query = $state("");
  let sortBy = $state("index");
  let descending = $state(false);
  interface Filter {
    option: string;
    group: string;
    /** hide the members in the group instead of showing only them */
    exclude: boolean;
  }
  let filters = $state<Filter[]>([]);
  let menuOpen = $state(false);
  // whether values picked in the menu are added as exclusions
  let excludeMode = $state(false);
  // attribute whose values are showing in the submenu
  let active = $state("");
  let menu: HTMLDivElement;

  const collator = $derived(new Intl.Collator(lang === "he" ? "he" : "en", { numeric: true, sensitivity: "base" }));

  function sortKey(c: Column, p: PresentedPerson): Key[] {
    if (c.key) return [c.key(p)];
    const o = optionFor.get(c.id);
    const g = o ? o.groups.findIndex((x) => x.key === groupOf(o, p)) : 0;
    return [g, c.text(p)];
  }

  function compare(a: Key[], b: Key[]): number {
    for (let i = 0; i < a.length; i++) {
      const x = a[i];
      const y = b[i];
      if (x === y) continue;
      // missing values always go last
      if (x === null || x === "") return 1;
      if (y === null || y === "") return -1;
      const d = typeof x === "number" && typeof y === "number" ? x - y : collator.compare(String(x), String(y));
      if (d) return descending ? -d : d;
    }
    return 0;
  }

  function sortOn(id: string) {
    if (sortBy === id) descending = !descending;
    else {
      sortBy = id;
      descending = false;
    }
  }

  const normalize = (s: string) => s.toLocaleLowerCase().normalize("NFKD").replace(/[\u0300-\u036f\u0591-\u05c7]/g, "");
  const SEARCHED = ["first_name", "locality"];

  // per attribute: a member must be in one of its included groups (if any) and in none of its
  // excluded ones; different attributes must all hold
  function passes(p: PresentedPerson): boolean {
    const byOption = new Map<string, Filter[]>();
    for (const f of filters) byOption.set(f.option, [...(byOption.get(f.option) ?? []), f]);
    for (const [id, fs] of byOption) {
      const g = groupOf(optionFor.get(id)!, p);
      const inc = fs.filter((f) => !f.exclude);
      if (inc.length && !inc.some((f) => f.group === g)) return false;
      if (fs.some((f) => f.exclude && f.group === g)) return false;
    }
    return true;
  }

  const rows = $derived.by(() => {
    const q = normalize(query.trim());
    const col = columns.find((c) => c.id === sortBy) ?? columns[0];
    return people
      .filter((p) => !q || SEARCHED.some((id) => [p.labels.he[id], p.labels.en[id]].some((x) => x && normalize(x).includes(q))))
      .filter(passes)
      .map((p) => ({ p, k: sortKey(col, p) }))
      .sort((a, b) => compare(a.k, b.k) || a.p.index - b.p.index)
      .map((r) => r.p);
  });

  // each attribute with the values that occur in the assembly and are not filtered on yet, so
  // the menu never offers an empty or repeated choice
  const filterable = $derived(
    COLOR_OPTIONS.map((o) => {
      const present = new Set(people.map((p) => groupOf(o, p)));
      const used = new Set(filters.filter((f) => f.option === o.id).map((f) => f.group));
      return { o, groups: o.groups.filter((g) => present.has(g.key) && !used.has(g.key)) };
    }).filter((x) => x.groups.length),
  );

  function addFilter(option: string, group: string) {
    filters = [...filters, { option, group, exclude: excludeMode }];
    closeMenu();
  }

  function toggleExclude(i: number) {
    filters = filters.map((f, j) => (j === i ? { ...f, exclude: !f.exclude } : f));
  }

  function closeMenu() {
    menuOpen = false;
    active = "";
  }

  function onWindowClick(e: MouseEvent) {
    if (menuOpen && !menu.contains(e.target as Node)) closeMenu();
  }

  const filterLabel = (f: Filter) => {
    const o = optionFor.get(f.option)!;
    const g = o.groups.find((x) => x.key === f.group)?.label[lang] ?? f.group;
    return `${o.label[lang]}: ${f.exclude ? `${t("not", lang)} ${g}` : g}`;
  };

  const nf = $derived(new Intl.NumberFormat(lang === "he" ? "he-IL" : "en-US"));
</script>

<svelte:window onclick={onWindowClick} onkeydown={(e) => e.key === "Escape" && closeMenu()} />

<div class="controls">
  <div class="menu" bind:this={menu}>
    <button class="menu-button" aria-haspopup="menu" aria-expanded={menuOpen} onclick={() => (menuOpen ? closeMenu() : (menuOpen = true))} disabled={!filterable.length}>
      {t("add_filter", lang)} <span aria-hidden="true">▾</span>
    </button>
    {#if menuOpen}
      <ul class="popup" role="menu">
        <li class="mode" role="none">
          <div role="radiogroup" aria-label={t("filter_mode", lang)}>
            <button role="radio" aria-checked={!excludeMode} class:on={!excludeMode} onclick={() => (excludeMode = false)} onpointerenter={() => (active = "")}>
              {t("show_only", lang)}
            </button>
            <button role="radio" aria-checked={excludeMode} class:on={excludeMode} onclick={() => (excludeMode = true)} onpointerenter={() => (active = "")}>
              {t("exclude", lang)}
            </button>
          </div>
        </li>
        {#each filterable as { o, groups } (o.id)}
          <li class="attr" class:open={active === o.id} role="none" onpointerenter={(e) => e.pointerType === "mouse" && (active = o.id)}>
            <button role="menuitem" aria-haspopup="menu" aria-expanded={active === o.id} onclick={() => (active = o.id)}>
              {o.label[lang]} <span class="chevron" aria-hidden="true">›</span>
            </button>
            {#if active === o.id}
              <ul class="popup sub" role="menu" aria-label={o.label[lang]}>
                {#each groups as g (g.key)}
                  <li role="none"><button role="menuitem" onclick={() => addFilter(o.id, g.key)}>{g.label[lang]}</button></li>
                {/each}
              </ul>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </div>
  <input type="search" bind:value={query} placeholder={t("search_name", lang)} aria-label={t("search_name", lang)} />
</div>

{#if filters.length}
  <div class="chips">
    {#each filters as f, i}
      <span class="chip" class:excluded={f.exclude}>
        <button onclick={() => toggleExclude(i)} title={f.exclude ? t("make_include", lang) : t("make_exclude", lang)}>{filterLabel(f)}</button>
        <button class="x" onclick={() => (filters = filters.filter((_, j) => j !== i))} aria-label={`${t("remove", lang)}: ${filterLabel(f)}`}>×</button>
      </span>
    {/each}
    <button class="link" onclick={() => (filters = [])}>{t("clear_filters", lang)}</button>
  </div>
{/if}

<p class="muted count tabular" aria-live="polite">
  {t("showing_members", lang).replace("{n}", nf.format(rows.length)).replace("{total}", nf.format(people.length))}
</p>

<div class="scroll">
  <table class="tabular">
    <thead>
      <tr>
        {#each columns as c}
          <th aria-sort={sortBy === c.id ? (descending ? "descending" : "ascending") : "none"}>
            <button class="sort" onclick={() => sortOn(c.id)}>
              {c.label[lang]}
              <span class="arrow" aria-hidden="true">{sortBy === c.id ? (descending ? "▼" : "▲") : ""}</span>
            </button>
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each rows as p (p.index)}
        <tr onclick={() => onselect(p)}>
          {#each columns as c}
            {#if c.id === "first_name"}
              <td class="name">
                <button class="link" onclick={(e) => { e.stopPropagation(); onselect(p); }}>{c.text(p)}</button>
              </td>
            {:else}
              <td class:muted={c.id === "index"}>{c.text(p)}</td>
            {/if}
          {/each}
        </tr>
      {:else}
        <tr><td colspan={columns.length} class="muted">{t("no_members", lang)}</td></tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .controls input {
    flex: 1 1 14rem;
    min-width: 0;
  }
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
  /* the values open beside their attribute, in reading direction */
  .sub {
    top: -0.3rem;
    inset-inline-start: 100%;
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
  /* no room beside it on a phone: the menu spans the card and values open in place, under
     the attribute */
  @media (max-width: 640px) {
    .menu {
      flex: 1 1 100%;
      position: static;
    }
    .controls {
      position: relative;
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
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
    margin-bottom: 0.25rem;
  }
  .chip {
    display: inline-flex;
    border: 1px solid;
    border-radius: 999px;
    font-size: 0.9rem;
    overflow: hidden;
  }
  .chip button {
    border: none;
    border-radius: 0;
    background: none;
    padding: 0.15rem 0.3rem 0.15rem 0.7rem;
  }
  :global([dir="rtl"]) .chip button {
    padding: 0.15rem 0.7rem 0.15rem 0.3rem;
  }
  .chip .x {
    padding-inline: 0.3rem 0.6rem;
  }
  /* show-only filters are tinted with the accent, exclusions with red */
  .chip {
    --tone: var(--accent);
    border-color: color-mix(in srgb, var(--tone) 55%, transparent);
    background: color-mix(in srgb, var(--tone) 14%, var(--surface-1));
  }
  .chip.excluded {
    --tone: var(--series-8);
  }
  .link {
    border: none;
    background: none;
    padding: 0;
    color: var(--accent);
    text-align: start;
  }
  .count {
    font-size: 0.85rem;
    margin: 0.25rem 0 0.5rem;
  }
  .scroll {
    overflow-x: auto;
    max-height: 70vh;
    overflow-y: auto;
  }
  th {
    position: sticky;
    top: 0;
    background: var(--surface-1);
    white-space: nowrap;
    padding: 0;
  }
  .sort {
    border: none;
    background: none;
    border-radius: 0;
    width: 100%;
    text-align: start;
    font-weight: 600;
    color: inherit;
    padding: 0.3rem 0.5rem;
  }
  .arrow {
    font-size: 0.7rem;
    display: inline-block;
    width: 0.7rem;
  }
  tbody tr {
    cursor: pointer;
  }
  tbody tr:hover {
    background: var(--surface-2);
  }
  td {
    font-size: 0.92rem;
  }
  .name {
    white-space: nowrap;
  }
</style>
