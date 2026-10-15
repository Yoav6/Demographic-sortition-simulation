<script lang="ts">
  import type { PresentedPerson, VarMeta } from "@popsim/sampler";
  import { COLOR_OPTIONS, groupOf } from "../lib/colorby.ts";
  import { t, type Lang } from "../lib/i18n.ts";
  import AttributeMenu, { type MenuAttr, type Pick } from "./AttributeMenu.svelte";
  import FilterChips from "./FilterChips.svelte";

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
  const menuAttrs = $derived<MenuAttr[]>(
    COLOR_OPTIONS.map((o) => {
      const present = new Set(people.map((p) => groupOf(o, p)));
      const used = new Set(filters.filter((f) => f.option === o.id).map((f) => f.group));
      const values = o.groups.filter((g) => present.has(g.key) && !used.has(g.key)).map((g) => ({ id: g.key, label: g.label[lang] }));
      return { id: o.id, label: o.label[lang], values, excludable: true };
    }).filter((a) => a.values.length),
  );

  const addFilter = (p: Pick) => (filters = [...filters, { option: p.attr, group: p.value!, exclude: p.exclude }]);

  const filterLabel = (f: Filter) => {
    const o = optionFor.get(f.option)!;
    const g = o.groups.find((x) => x.key === f.group)?.label[lang] ?? f.group;
    return `${o.label[lang]}: ${f.exclude ? `${t("not", lang)} ${g}` : g}`;
  };

  const nf = $derived(new Intl.NumberFormat(lang === "he" ? "he-IL" : "en-US"));
</script>

<div class="controls">
  <AttributeMenu attrs={menuAttrs} {lang} label={t("add_filter", lang)} withMode onpick={addFilter} />
  <input type="search" bind:value={query} placeholder={t("search_name", lang)} aria-label={t("search_name", lang)} />
</div>

<FilterChips
  items={filters.map((f) => ({ label: filterLabel(f), exclude: f.exclude, toggleable: true }))}
  {lang}
  ontoggle={(i) => (filters = filters.map((f, j) => (j === i ? { ...f, exclude: !f.exclude } : f)))}
  onremove={(i) => (filters = filters.filter((_, j) => j !== i))}
  onclear={() => (filters = [])}
/>

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
