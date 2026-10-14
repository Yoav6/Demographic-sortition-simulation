<script lang="ts">
  import { loadSources, type SourceInfo } from "../lib/data.ts";
  import { t, type Lang } from "../lib/i18n.ts";

  let { lang }: { lang: Lang } = $props();
  let sources = $state<SourceInfo[] | null>(null);
  loadSources().then((s) => (sources = s));

  const TIER: Record<string, { he: string; en: string }> = {
    A: { he: "הורדה בסקריפט", en: "scripted download" },
    B: { he: "דפדפן אוטומטי", en: "headless browser" },
    C: { he: "דורש הרשמה (אופציונלי)", en: "free registration (optional)" },
    M: { he: "העתקה ידנית מתועדת", en: "documented manual transcription" },
    R: { he: "מיקרו-נתונים מוגבלים (מצרפים בלבד)", en: "restricted microdata (aggregates only)" },
  };
</script>

<section>
  <p class="secondary">{t("sources_intro", lang)}</p>
  {#if sources}
    <div class="list">
      {#each sources as s}
        <article class="card source" id={`src-${s.id}`}>
          <h3>{lang === "he" ? s.title.he : s.title.en}</h3>
          <p class="muted small">
            <code>{s.id}</code> · {t("publisher", lang)}: {s.publisher} · {t("tier", lang)}: {s.tier} ({TIER[s.tier]?.[lang]})
            {#if s.as_of}· {s.as_of}{/if}
          </p>
          {#if s.url}<p class="small"><a href={s.url} target="_blank" rel="noreferrer">{s.url.length > 90 ? s.url.slice(0, 90) + "…" : s.url}</a></p>{/if}
          <p class="small">{t("terms", lang)}: {s.license}</p>
          {#if s.notes}<p class="small secondary" dir="ltr" lang="en">{s.notes}</p>{/if}
          {#if s.files.length}
            <details>
              <summary class="small">{t("files", lang)} ({s.files.length})</summary>
              <ul class="small" dir="ltr">
                {#each s.files as f}
                  <li><a href={f.url} target="_blank" rel="noreferrer">{f.path}</a>{#if f.sha256} — <code>sha256 {f.sha256.slice(0, 16)}…</code> ({f.retrieved}){/if}</li>
                {/each}
              </ul>
            </details>
          {/if}
        </article>
      {/each}
    </div>
  {:else}
    <p class="muted">…</p>
  {/if}
</section>

<style>
  .list {
    display: grid;
    gap: 0.75rem;
  }
  .source h3 {
    margin: 0 0 0.25rem;
    font-size: 1.05rem;
  }
  .small {
    font-size: 0.88rem;
    margin: 0.2rem 0;
  }
</style>
