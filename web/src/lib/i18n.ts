export type Lang = "he" | "en";

const strings = {
  title: { he: "אספה אזרחית בהגרלה", en: "A citizens' assembly by lot" },
  subtitle: {
    he: "150 אזרחיות ואזרחי ישראל שנבחרו באקראי — סימולציה מבוססת נתונים",
    en: "150 Israeli citizens drawn at random — a data-driven simulation",
  },
  nav_assembly: { he: "האספה", en: "Assembly" },
  nav_random: { he: "אדם אקראי", en: "Random person" },
  nav_explore: { he: "מה הסיכוי?", en: "What are the odds?" },
  nav_method: { he: "מתודולוגיה", en: "Methodology" },
  nav_sources: { he: "מקורות", en: "Sources" },
  color_by: { he: "צביעה לפי", en: "Colour seats by" },
  seed: { he: "זרע הגרלה", en: "Seed" },
  model_version: { he: "גרסת מודל", en: "Model version" },
  default_assembly: { he: "האספה הרשמית (זהה לכל המבקרים)", en: "The published assembly (same for every visitor)" },
  custom_assembly: { he: "אספה חלופית", en: "Alternative assembly" },
  draw_other: { he: "הגרלה עם זרע אחר", en: "Draw with another seed" },
  draw: { he: "הגרל", en: "Draw" },
  back_default: { he: "חזרה לאספה הרשמית", en: "Back to the published assembly" },
  download_csv: { he: "הורדת CSV", en: "Download CSV" },
  download_json: { he: "הורדת JSON", en: "Download JSON" },
  in_assembly: { he: "באספה", en: "In the assembly" },
  in_population: { he: "באוכלוסייה", en: "In the population" },
  population: { he: "אוכלוסיית היעד", en: "Target population" },
  person: { he: "פרטי המשתתף/ת", en: "Member details" },
  close: { he: "סגירה", en: "Close" },
  attribute: { he: "מאפיין", en: "Attribute" },
  value: { he: "ערך", en: "Value" },
  how_estimated: { he: "איך זה חושב?", en: "How was this estimated?" },
  random_intro: {
    he: "כל לחיצה מגרילה אדם אחד מתוך אוכלוסיית האזרחים בני 18+ לפי המודל. הזרע מוצג כדי שאפשר יהיה לשחזר בדיוק את אותו אדם.",
    en: "Each click draws one person from the model of citizens aged 18+. The seed is shown so the exact same person can be reproduced.",
  },
  draw_person: { he: "הגרלת אדם", en: "Draw a person" },
  loading_model: { he: "טוען את המודל…", en: "Loading the model…" },
  copy_link: { he: "העתקת קישור", en: "Copy link" },
  copied: { he: "הועתק", en: "Copied" },
  sources_intro: {
    he: "כל המספרים במודל נובעים מהמקורות הבאים. הקבצים מורדים בסקריפט ונחתמים בגיבוב SHA-256 כדי שכל אחד יוכל לשחזר את העבודה.",
    en: "Every number in the model comes from the sources below. Files are downloaded by script and pinned by SHA-256 so anyone can reproduce the work.",
  },
  method_intro: {
    he: "המתודולוגיה המלאה מתועדת באנגלית; לכל מאפיין מוצג כאן תקציר בעברית.",
    en: "The full methodology is documented below; each attribute has its own section.",
  },
  tier: { he: "רמת גישה", en: "Access tier" },
  publisher: { he: "מפרסם", en: "Publisher" },
  terms: { he: "תנאי שימוש", en: "Terms" },
  files: { he: "קבצים", en: "Files" },
  share: { he: "חלק באספה", en: "Share of assembly" },
  people: { he: "אנשים", en: "people" },
  seats: { he: "מושבים", en: "seats" },
  explore_intro: {
    he: "בחרו מאפיינים, והמודל יחשב את ההתפלגות של כל שאר המאפיינים בקרב האנשים שעונים עליהם.",
    en: "Pick some characteristics and the model computes how everything else is distributed among people who match them.",
  },
  add_condition: { he: "הוספת תנאי", en: "Add condition" },
  run: { he: "חישוב", en: "Compute" },
  matching_share: { he: "שיעור באוכלוסייה", en: "Share of the population" },
  effective_n: { he: "מדגם אפקטיבי", en: "Effective sample" },
  expected_seats: { he: "מושבים צפויים באספה", en: "Expected seats in the assembly" },
  remove: { he: "הסרה", en: "Remove" },
  any: { he: "כלשהו", en: "any" },
  map: { he: "מפה", en: "Map" },
} as const;

export type Key = keyof typeof strings;

export function t(key: Key, lang: Lang): string {
  return strings[key][lang];
}
