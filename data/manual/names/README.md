# Name transliteration overrides (manual)

`english_overrides.csv` gives the conventional English spelling of common first names that
Wikidata ([`src:wikidata_given_names`](../../../SOURCES.md#src-wikidata_given_names)) does not cover (or covers ambiguously) — mostly Hebrew names (Shira, Eyal, Matan) and
Arabic names written in Hebrew script (Fatma, Khaled, Abir). The list was compiled for this
project from the most frequent names without a Wikidata form; spellings follow the most
common usage in English-language Israeli and Arab media. `en_f` (optional) is a different
feminine English form for a Hebrew spelling shared by both sexes. `style` (optional) limits a
row to names borne by Jews and "others" (`hebrew`) or by Arab and Druze citizens (`arabic`),
for spellings used in both communities but written differently in English (עומר: Omer /
Omar; יוסף: Yosef / Yusuf; מרים: Miriam / Maryam).

Priority when displaying a name in English: this file, then the Wikidata label closest to a
rule-based transliteration in the community's style (so Israeli forms such as Yehuda or Moshe
win over English biblical ones such as Judah or Moses), then the rule-based transliteration
itself (`pipeline/popsim/estimate/names.py`). Only the English display is affected;
the model samples the Hebrew registry spellings.
