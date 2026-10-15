<script lang="ts">
  import type { Lang } from "../lib/i18n.ts";

  let { lang }: { lang: Lang } = $props();

  const text = {
    he: {
      heading: "על הפרויקט",
      intro: [
        "איך תיראה אספה אזרחית שבה 150 החברות והחברים מוגרלים מכלל אזרחי ישראל? הפרויקט בונה על בסיס נתונים פומביים מודל סטטיסטי של האוכלוסייה הזכאית – אזרחים ישראלים בני 18 ומעלה שחיים בישראל (6.45 מיליון איש) – מגריל ממנו 150 חברים פיקטיבים, ומתאר כל אחד מהם בפירוט.",
        "לכל חבר יש 54 מאפיינים: מקום מגורים, קבוצת אוכלוסייה, מין, גיל, דתיות, שם פרטי, מוצא, מצב משפחתי וילדים, עם מי גרים, השכלה ולימודים נוכחיים (עם תחומי לימוד), שירות צבאי או לאומי, עבודה (מצב תעסוקתי, מקצוע, ענף), הכנסה והכנסת משק בית (עם עשירונים), בעלות על דירה, בריאות, מוגבלות, ההצבעה ב-2022, הרגלי צריכת חדשות (באיזו תדירות הם מקבלים חדשות מטלוויזיה, רדיו, עיתונים מודפסים, אתרי חדשות, רשתות חברתיות, מנועי חיפוש ופודקאסטים; באילו רשתות חברתיות הם משתמשים וקוראים בהן חדשות; אילו ערוצי טלוויזיה ואתרי חדשות הם עוקבים אחריהם; מהו העיתון העיקרי שלהם; מהו מקור החדשות המועדף עליהם) וציון אוריינות.",
      ],
      howHeading: "איך זה עובד",
      how: [
        ["רשת בייסיאנית של טבלאות מותנות.", "המודל הוא שרשרת של טבלאות, וכל אחת מהן נותנת את התפלגות המאפיין בהינתן כמה מאפיינים אחרים. השורש הוא טבלה משותפת של יישוב × קבוצת אוכלוסייה × מין × גיל."],
        ["נבנה מנתונים פומביים בלבד.", "המקורות כוללים את הלמ\"ס, ועדת הבחירות המרכזית, סקרי הבחירות הישראליים, המל\"ג, המכון הישראלי לדמוקרטיה, ה-OECD ובנק ישראל ועוד. כולם מופיעים בעמוד המקורות עם גיבובי SHA-256."],
        ["מכויל ומאומת.", "הטבלאות משולבות בהתאמה פרופורציונלית איטרטיבית (IPF) ומכוילות לסכומים רשמיים. למשל, חלוקת הקולות הארצית ב-2022 תואמת את התוצאה הרשמית בטווח של 0.1 נקודות אחוז. 59 בדיקות אימות מושוות לנתונים שפורסמו."],
        ["דטרמיניסטי.", "כל מספר אקראי הוא גיבוב של (סיד, אדם, מאפיין), ולכן אותו סיד נותן את אותם אנשים בדיוק, בשרת ובדפדפן. הסיד של האספה הרשמית נלקח מאורקל הרנדומליות הציבורי drand."],
      ],
      note: "סימולציה בלבד: כל אדם כאן הוא דמות סינתטית, לא אדם אמיתי.",
      more: "המתודולוגיה המלאה",
      sources: "מקורות",
    },
    en: {
      heading: "About this project",
      intro: [
        "What would a citizens' assembly look like if its 150 members were drawn by lot from all Israeli citizens? This project builds a statistical model of the eligible population — Israeli citizens aged 18 and over living in Israel (6.45 million people) — from public data, draws 150 synthetic members from it, and describes each of them in detail.",
        "Every member has 54 attributes: place of residence, population group, sex, age, religiosity, first name, origin and ancestry, marital status and children, whom they live with, education and current studies (with fields of study), military or national service, work (status, occupation, industry), earnings and household income (with percentiles), home ownership, health, disability, the 2022 vote, media habits (how often they get news from TV, radio, printed newspapers, news sites, social media, search engines and podcasts; the social networks they use and read news on; the TV channels and news websites they follow; their main newspaper; their preferred news source), and a literacy score.",
      ],
      howHeading: "How it works",
      how: [
        ["A Bayesian network of conditional tables.", "The model is a chain of tables, each giving one attribute's distribution given a few others. The root is a joint table of locality × population group × sex × age band."],
        ["Built only from public data.", "Sources include the CBS, the Central Elections Committee, the Israel National Election Studies, the Council for Higher Education, the Israel Democracy Institute, the OECD and the Bank of Israel, among others. All are listed with checksums on the Sources page."],
        ["Calibrated and validated.", "Tables are combined with iterative proportional fitting and calibrated to official totals. For example, national 2022 vote shares match the official result within 0.1 points. 59 validation checks compare the model against published figures."],
        ["Deterministic.", "Every random number is a hash of (seed, person, attribute), so the same seed always gives the same people in Node and in the browser. The published assembly's seed comes from the drand public randomness beacon."],
      ],
      note: "Simulation only: every person shown is a synthetic character, not a real individual.",
      more: "Full methodology",
      sources: "Sources",
    },
  };
  let c = $derived(text[lang]);
</script>

<section class="about">
  <h2>{c.heading}</h2>
  {#each c.intro as p}<p>{p}</p>{/each}

  <h3>{c.howHeading}</h3>
  <ul>
    {#each c.how as [title, body]}
      <li><strong>{title}</strong> {body}</li>
    {/each}
  </ul>

  <p class="muted">{c.note}</p>
  <p class="links">
    <a href="#/method">{c.more}</a> ·
    <a href="#/sources">{c.sources}</a>
  </p>
</section>

<style>
  .about {
    max-width: 46rem;
  }
  h2 {
    margin-top: 0;
  }
  li {
    margin-bottom: 0.6rem;
  }
</style>
