<script lang="ts">
  import type { PresentedPerson, ValueDef } from "@popsim/sampler";
  import { groupColor, groupOf, type ColorOption } from "../lib/colorby.ts";
  import type { Lang } from "../lib/i18n.ts";

  let {
    people,
    option,
    localities,
    lang,
    onselect,
  }: {
    people: PresentedPerson[];
    option: ColorOption;
    localities: ValueDef[];
    lang: Lang;
    onselect: (p: PresentedPerson) => void;
  } = $props();

  // Equirectangular projection around Israel's mean latitude: x = lon * cos(lat0), y = -lat.
  const COS = Math.cos((31.5 * Math.PI) / 180);
  const H = 760;
  const PAD = 12;
  const PLACEHOLDER_W = 286;

  const coords = $derived(
    new Map(
      localities
        .filter((l) => typeof l.attrs?.lat === "number" && typeof l.attrs?.lon === "number")
        .map((l) => [l.id, { lat: l.attrs!.lat as number, lon: l.attrs!.lon as number, l }]),
    ),
  );
  const bounds = $derived.by(() => {
    let lat0 = Infinity, lat1 = -Infinity, lon0 = Infinity, lon1 = -Infinity;
    for (const c of coords.values()) {
      lat0 = Math.min(lat0, c.lat); lat1 = Math.max(lat1, c.lat);
      lon0 = Math.min(lon0, c.lon); lon1 = Math.max(lon1, c.lon);
    }
    const scale = (H - 2 * PAD) / (lat1 - lat0);
    return { lat1, lon0, scale, W: (lon1 - lon0) * COS * scale + 2 * PAD };
  });
  const project = (lat: number, lon: number) => ({
    x: PAD + (lon - bounds.lon0) * COS * bounds.scale,
    y: PAD + (bounds.lat1 - lat) * bounds.scale,
  });

  // members of the same locality are spread on a small golden-angle spiral around it
  const dots = $derived.by(() => {
    const seen = new Map<string, number>();
    const out: { p: PresentedPerson; x: number; y: number; color: string }[] = [];
    for (const p of people) {
      const c = coords.get(String(p.values.locality));
      if (!c) continue;
      const k = seen.get(c.l.id) ?? 0;
      seen.set(c.l.id, k + 1);
      const { x, y } = project(c.lat, c.lon);
      const r = k === 0 ? 0 : 4.2 * Math.sqrt(k);
      const a = k * 2.39996;
      const gi = option.groups.findIndex((g) => g.key === groupOf(option, p));
      out.push({ p, x: x + r * Math.cos(a), y: y + r * Math.sin(a), color: groupColor(option, Math.max(gi, 0)) });
    }
    return out;
  });

  // read from the members' own labels, so the list shows before the model's localities load
  const top = $derived.by(() => {
    const counts = new Map<string, { name: string; n: number }>();
    for (const p of people) {
      const id = String(p.values.locality);
      const c = counts.get(id) ?? { name: p.labels[lang].locality ?? id, n: 0 };
      c.n++;
      counts.set(id, c);
    }
    return [...counts.values()].sort((a, b) => b.n - a.n).slice(0, 12);
  });
  const nLocalities = $derived(new Set(people.map((p) => String(p.values.locality))).size);
</script>

<div class="map-wrap">
  {#if !coords.size}
    <!-- the localities come with the model, which loads a few seconds after the assembly; this
         keeps the map's place (its size at the time of writing) so nothing below it moves -->
    <div class="placeholder muted" style:width={`${PLACEHOLDER_W}px`} style:aspect-ratio={`${PLACEHOLDER_W} / ${H}`}>
      {lang === "he" ? "טוען את המפה…" : "Loading the map…"}
    </div>
  {:else}
  <svg viewBox={`0 0 ${bounds.W} ${H}`} width={bounds.W} height={H} role="img" aria-label={lang === "he" ? "מפת יישובי חברי האספה" : "Map of the members' localities"}>
    {#each [...coords.values()] as c (c.l.id)}
      {@const q = project(c.lat, c.lon)}
      <circle cx={q.x} cy={q.y} r="1.3" class="locality" />
    {/each}
    {#each dots as d (d.p.index)}
      <circle
        cx={d.x}
        cy={d.y}
        r="4"
        fill={d.color}
        class="member"
        role="button"
        tabindex="0"
        onclick={() => onselect(d.p)}
        onkeydown={(e) => (e.key === "Enter" || e.key === " ") && onselect(d.p)}
      >
        <title>{d.p.labels[lang].first_name} · {d.p.labels[lang].locality}</title>
      </circle>
    {/each}
  </svg>
  {/if}
  <div class="side">
    <p class="secondary">
      {lang === "he"
        ? `חברי האספה מתגוררים ב-${nLocalities} יישובים. הנקודות האפורות הן כל היישובים במודל; הצבעים כמו במושבי האספה.`
        : `The members live in ${nLocalities} localities. Grey dots are all the localities in the model; colours as in the seating chart.`}
    </p>
    <table class="tabular">
      <tbody>
        {#each top as row}
          <tr><td>{row.name}</td><td>{row.n}</td></tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .map-wrap {
    display: flex;
    gap: 1.5rem;
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .placeholder {
    max-width: 100%;
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: var(--surface-2);
    font-size: 0.9rem;
  }
  svg {
    max-width: 100%;
    height: auto;
    flex: 0 0 auto;
  }
  .locality {
    fill: var(--text-muted);
    opacity: 0.35;
  }
  .member {
    stroke: var(--seat-ring);
    stroke-width: 1.2;
    cursor: pointer;
  }
  .member:hover,
  .member:focus-visible {
    stroke: var(--text-primary);
    stroke-width: 1.6;
    outline: none;
  }
  .side {
    flex: 1 1 220px;
    min-width: 200px;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    max-width: 320px;
  }
  td {
    padding: 0.2rem 0.4rem;
    border-bottom: 1px solid var(--hairline);
  }
  td:last-child {
    text-align: end;
  }
</style>
