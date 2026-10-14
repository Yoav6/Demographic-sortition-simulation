<script lang="ts">
  import type { PresentedPerson } from "@popsim/sampler";
  import { hemicycle } from "../lib/hemicycle.ts";
  import { groupColor, groupOf, type ColorOption } from "../lib/colorby.ts";
  import { t, type Lang } from "../lib/i18n.ts";

  let {
    people,
    option,
    lang,
    onselect,
  }: { people: PresentedPerson[]; option: ColorOption; lang: Lang; onselect: (p: PresentedPerson) => void } = $props();

  const W = 2.24;
  const H = 1.16;
  const CX = W / 2;
  const CY = 1.08;

  const layout = $derived(hemicycle(people.length));

  // people sorted by group (in the option's order), seats read left->right (right->left in Hebrew)
  const placed = $derived.by(() => {
    const order = new Map(option.groups.map((g, i) => [g.key, i]));
    const sorted = [...people].sort(
      (a, b) => (order.get(groupOf(option, a)) ?? 99) - (order.get(groupOf(option, b)) ?? 99) || a.index - b.index,
    );
    const seats = lang === "he" ? [...layout.seats].reverse() : layout.seats;
    return sorted.map((p, i) => {
      const s = seats[i];
      const gi = order.get(groupOf(option, p)) ?? 0;
      return { p, x: CX + s.x, y: CY - s.y, color: groupColor(option, gi), group: option.groups[gi] };
    });
  });

  let hover = $state<{ p: PresentedPerson; x: number; y: number; group: string } | null>(null);
  let box: HTMLDivElement;

  function show(e: MouseEvent | FocusEvent, item: (typeof placed)[number]) {
    const rect = box.getBoundingClientRect();
    const target = (e.currentTarget as SVGCircleElement).getBoundingClientRect();
    hover = {
      p: item.p,
      x: target.left + target.width / 2 - rect.left,
      y: target.top - rect.top,
      group: item.group.label[lang],
    };
  }
</script>

<div class="hemicycle" bind:this={box}>
  <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={lang === "he" ? "מושבי האספה" : "Assembly seats"}>
    {#each placed as item (item.p.index)}
      <circle
        cx={item.x}
        cy={item.y}
        r={layout.radius}
        fill={item.color}
        class="seat"
        role="button"
        tabindex="0"
        aria-label={`${item.p.labels[lang].first_name}, ${item.p.labels[lang].age} — ${item.group.label[lang]}`}
        onmouseenter={(e) => show(e, item)}
        onmouseleave={() => (hover = null)}
        onfocus={(e) => show(e, item)}
        onblur={() => (hover = null)}
        onclick={() => onselect(item.p)}
        onkeydown={(e) => (e.key === "Enter" || e.key === " ") && onselect(item.p)}
      />
    {/each}
    <text x={CX} y={CY - 0.12} text-anchor="middle" class="count">{people.length}</text>
    <text x={CX} y={CY - 0.02} text-anchor="middle" class="count-label">{t("seats", lang)}</text>
  </svg>
  {#if hover}
    <div class="tooltip" style:left={`${hover.x}px`} style:top={`${hover.y}px`} role="tooltip">
      <strong>{hover.p.labels[lang].first_name}</strong>, {hover.p.labels[lang].age}
      <div class="muted">{hover.p.labels[lang].locality}</div>
      <div>{hover.group}</div>
    </div>
  {/if}
</div>

<style>
  .hemicycle {
    position: relative;
    width: 100%;
  }
  svg {
    width: 100%;
    height: auto;
    display: block;
    overflow: visible;
  }
  .seat {
    stroke: var(--seat-ring);
    stroke-width: 0.006;
    cursor: pointer;
    transition: transform 0.12s ease;
    transform-box: fill-box;
    transform-origin: center;
  }
  /* The browser's default focus ring is drawn in SVG user units and gets scaled up by
     the viewBox (into a huge disc), so it is replaced by a stroke. */
  .seat:focus {
    outline: none;
  }
  .seat:hover,
  .seat:focus-visible {
    transform: scale(1.35);
    stroke: var(--text-primary);
    stroke-width: 0.01;
  }
  .count {
    font-size: 0.16px;
    font-weight: 700;
    fill: var(--text-primary);
  }
  .count-label {
    font-size: 0.06px;
    fill: var(--text-muted);
  }
  .tooltip {
    position: absolute;
    transform: translate(-50%, calc(-100% - 10px));
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.4rem 0.6rem;
    box-shadow: var(--shadow);
    pointer-events: none;
    white-space: nowrap;
    font-size: 0.9rem;
    z-index: 5;
  }
</style>
