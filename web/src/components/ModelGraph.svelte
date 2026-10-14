<script lang="ts">
  import type { GraphNode } from "../lib/worker-client.ts";
  import type { Lang } from "../lib/i18n.ts";

  let { nodes, lang }: { nodes: GraphNode[]; lang: Lang } = $props();

  const ROW = 64;
  const BOX_H = 30;
  const W = 1100;
  let hover = $state<string | null>(null);

  // depth = longest chain of dependencies from the frame; rows are depths
  const layout = $derived.by(() => {
    const producer = new Map<string, GraphNode>();
    for (const n of nodes) for (const v of n.produces) producer.set(v, n);
    const depth = new Map<string, number>();
    for (const n of nodes) {
      // nodes come in sampling order, so every dependency already has a depth
      depth.set(n.id, n.deps.length ? 1 + Math.max(...n.deps.map((d) => depth.get(producer.get(d)?.id ?? "") ?? 0)) : 0);
    }
    const rows: GraphNode[][] = [];
    for (const n of nodes) (rows[depth.get(n.id)!] ??= []).push(n);
    // order each row by the mean position of its parents (fewer crossings), then place evenly
    const x = new Map<string, number>();
    rows.forEach((row) => {
      const key = (n: GraphNode) => {
        const xs = n.deps.map((d) => x.get(producer.get(d)?.id ?? "")).filter((v): v is number => v !== undefined);
        return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : W / 2;
      };
      row.sort((a, b) => key(a) - key(b));
      const step = W / (row.length + 1);
      row.forEach((n, i) => x.set(n.id, step * (i + 1)));
    });
    const pos = new Map<string, { x: number; y: number }>();
    for (const n of nodes) pos.set(n.id, { x: x.get(n.id)!, y: depth.get(n.id)! * ROW + 24 });
    const edges: { from: string; to: string }[] = [];
    for (const n of nodes) {
      const seen = new Set<string>();
      for (const d of n.deps) {
        const p = producer.get(d);
        if (p && !seen.has(p.id)) {
          seen.add(p.id);
          edges.push({ from: p.id, to: n.id });
        }
      }
    }
    const width = Math.max(...rows.map((r) => r.length)) * 150;
    return { pos, edges, height: rows.length * ROW + 24, width: Math.max(W, width) };
  });

  const linked = $derived.by(() => {
    if (!hover) return null;
    const s = new Set([hover]);
    for (const e of layout.edges) {
      if (e.from === hover) s.add(e.to);
      if (e.to === hover) s.add(e.from);
    }
    return s;
  });

  const short = (n: GraphNode) => {
    const l = n.label[lang];
    const cut = l.replace(/\s*\(.*\)$/, "");
    return cut.length > 22 ? cut.slice(0, 21) + "…" : cut;
  };
  const href = (n: GraphNode) => (n.doc ? `#/method/${n.doc.replace(/^.*\//, "").replace(/\.md$/, "")}` : "#/method");
  const sx = (x: number) => (lang === "he" ? W - x : x) * (layout.width / W);
</script>

<figure class="graph">
  <div class="scroll">
    <svg viewBox={`0 0 ${layout.width} ${layout.height}`} width="100%" role="img"
         aria-label={lang === "he" ? "מבנה המודל: כל מאפיין והמאפיינים שהוא תלוי בהם" : "Model structure: each attribute and the attributes it depends on"}>
      {#each layout.edges as e (e.from + ">" + e.to)}
        {@const a = layout.pos.get(e.from)!}
        {@const b = layout.pos.get(e.to)!}
        <path
          d={`M ${sx(a.x)} ${a.y + BOX_H / 2} C ${sx(a.x)} ${(a.y + b.y) / 2 + BOX_H / 2}, ${sx(b.x)} ${(a.y + b.y) / 2 - BOX_H / 2}, ${sx(b.x)} ${b.y - BOX_H / 2}`}
          class="edge"
          class:on={linked?.has(e.from) && linked?.has(e.to) && (e.from === hover || e.to === hover)}
          class:off={linked && !(e.from === hover || e.to === hover)}
        />
      {/each}
      {#each nodes as n (n.id)}
        {@const p = layout.pos.get(n.id)!}
        <a href={href(n)} onmouseenter={() => (hover = n.id)} onmouseleave={() => (hover = null)} onfocus={() => (hover = n.id)} onblur={() => (hover = null)}>
          <g class="node" class:hidden-node={n.hidden} class:frame={n.type === "frame"} class:off={linked && !linked.has(n.id)}>
            <rect x={sx(p.x) - 68} y={p.y - BOX_H / 2} width="136" height={BOX_H} rx="8" />
            <text x={sx(p.x)} y={p.y + 4} text-anchor="middle">{short(n)}</text>
            <title>{n.label[lang]}{n.hidden ? (lang === "he" ? " (משתנה עזר)" : " (helper variable)") : ""}</title>
          </g>
        </a>
      {/each}
    </svg>
  </div>
  <figcaption class="muted">
    {lang === "he"
      ? "כל מאפיין נדגם בהינתן המאפיינים שמעליו שמחוברים אליו. מסגרות מקווקוות הן משתני עזר. ריחוף מדגיש את הקשרים; לחיצה פותחת את דף המתודולוגיה."
      : "Each attribute is drawn given the attributes above it that point to it. Dashed boxes are helper variables. Hover to highlight links; click for the methodology page."}
  </figcaption>
</figure>

<style>
  .graph {
    margin: 0;
  }
  .scroll {
    overflow-x: auto;
  }
  svg {
    display: block;
    min-width: 720px;
    height: auto;
  }
  .edge {
    fill: none;
    stroke: var(--text-muted);
    stroke-opacity: 0.35;
    stroke-width: 1.2;
  }
  .edge.on {
    stroke: var(--accent);
    stroke-opacity: 1;
    stroke-width: 2;
  }
  .edge.off {
    stroke-opacity: 0.08;
  }
  .node rect {
    fill: var(--surface-1);
    stroke: var(--accent);
    stroke-width: 1.3;
  }
  .node.frame rect {
    fill: var(--accent);
  }
  .node.frame text {
    fill: var(--surface-1);
    font-weight: 600;
  }
  .node.hidden-node rect {
    stroke: var(--text-muted);
    stroke-dasharray: 4 3;
  }
  .node text {
    font-size: 12px;
    fill: var(--text-primary);
  }
  .node.off {
    opacity: 0.25;
  }
  a:focus-visible .node rect {
    stroke-width: 3;
  }
  figcaption {
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }
</style>
