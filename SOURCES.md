# Sources

Generated from `sources.yaml` and `sources.lock.json` by `popsim docs`. Do not edit by hand.

Access tiers: **A** = scripted download, no login; **B** = scripted with a headless browser; results committed with their query spec; **C** = free registration required; optional enrichment; **M** = manual transcription committed to data/manual with page references; **R** = restricted microdata; only derived aggregates are committed.

## CBS localities file 2024 ("bycode")

*קובץ היישובים 2024 של הלמ"ס*

- **id:** `cbs_localities_2024` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS)
- **page:** <https://www.cbs.gov.il/he/publications/Pages/2019/%D7%99%D7%99%D7%A9%D7%95%D7%91%D7%99%D7%9D-%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C.aspx>
- **data as of:** 2024-12-31
- **terms:** CBS publication; reuse with attribution
- **used by:** `frame`, `district`, `locality_type`, `sector`
- **planned for:** `locality`
- file `bycode2024.xlsx`: <https://www.cbs.gov.il/he/publications/doclib/2019/ishuvim/bycode2024.xlsx> — sha256 `a021c6a151863ded…`, retrieved 2026-10-13

One row per locality: CBS code, Hebrew/English name, district, sub-district, natural region, municipal status, religion of the locality, population (total, Jews and others, Jews, Arabs), coordinates.

## CBS first names of people born 1949-2024, by sector, sex and year of birth

*שמות פרטיים לפי שנת לידה, מגזר ומין (הלמ"ס, הודעה 391/2025)*

- **id:** `cbs_names` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS)
- **page:** <https://www.cbs.gov.il/he/mediarelease/Pages/2025/default.aspx>
- **data as of:** 2024
- **terms:** CBS publication; reuse with attribution
- **used by:** `birth_cohort`, `first_name`
- file `11_25_391t1.xlsx`: <https://www.cbs.gov.il/he/mediarelease/DocLib/2025/391/11_25_391t1.xlsx> — sha256 `37b9783487d5de49…`, retrieved 2026-10-13

Based on the Population Registry. Names given to fewer than 5 babies in a year are suppressed. Covers people born in Israel 1949-2024 only.

## Central Elections Committee - results of the 25th Knesset election (Nov 2022)

*ועדת הבחירות המרכזית - תוצאות הבחירות לכנסת ה-25*

- **id:** `cec_knesset25` · **tier:** A · **publisher:** Central Elections Committee (CEC)
- **page:** <https://votes25.bechirot.gov.il/>
- **data as of:** 2022-11-01
- **terms:** Official election results (public record)
- **used by:** `frame`, `locality_profile`, `religiosity`, `vote_area`, `vote_2022`, `vote_bloc`
- **planned for:** `vote`
- file `expc.csv`: <https://media25.bechirot.gov.il/files/expc.csv> — sha256 `412785ed46af1281…`, retrieved 2026-10-13
- file `expb.csv`: <https://media25.bechirot.gov.il/files/expb.csv> — sha256 `07c71db1bf844d40…`, retrieved 2026-10-13

expc = results by locality, expb = results by polling station. Columns: committee code, locality name, locality code, eligible voters (בזב), voters, invalid, valid, then one column per party ballot letter. Eligible voters include citizens living abroad.

## Israel National Election Studies (INES) 2022 - pre/post election panel

*הסקר הלאומי של הבחירות בישראל 2022*

- **id:** `ines_2022` · **tier:** A · **publisher:** Israel National Election Studies, Tel Aviv University
- **page:** <https://socsci4.tau.ac.il/mu2/ines/data/our-data/>
- **data as of:** 2022-11
- **terms:** Free for research use with citation (see INES "How to cite")
- **used by:** `locality_profile`, `religiosity`, `origin`, `ancestry`, `vote_age`, `vote_education`, `vote_origin`, `vote_2022`, `news_frequency`
- **planned for:** `vote`
- file `2022_SPSS.sav`: <https://socsci4.tau.ac.il/mu2/ines/wp-content/uploads/sites/4/2023/06/2022_SPSS.sav> — sha256 `30e0a5c1f1ba44f0…`, retrieved 2026-10-13
- file `2022_Questionnaire_Eng.pdf`: <https://socsci4.tau.ac.il/mu2/ines/wp-content/uploads/sites/4/2023/06/2022_Questionnaire_Eng.pdf> — sha256 `47e28ba8933cd56c…`, retrieved 2026-10-13
- file `2022_Appendix.pdf`: <https://socsci4.tau.ac.il/mu2/ines/wp-content/uploads/sites/4/2023/06/2022_Appendix-1.pdf> — sha256 `ab7503cc93216c10…`, retrieved 2026-10-13

## Israel National Election Studies (INES) 2025 off-cycle study

*הסקר הלאומי של הבחירות בישראל 2025*

- **id:** `ines_2025` · **tier:** A · **publisher:** Israel National Election Studies, Tel Aviv University
- **page:** <https://socsci4.tau.ac.il/mu2/ines/data/our-data/>
- **data as of:** 2025
- **terms:** Free for research use with citation (see INES "How to cite")
- **used by:** `news_tv`, `news_radio`, `news_print`, `news_sites`, `news_social`, `news_search`, `news_podcasts`, `tv_channels`
- **planned for:** `vote_2026`
- file `2025_SPSS.sav`: <https://socsci4.tau.ac.il/mu2/ines/wp-content/uploads/sites/4/2025/09/2025_SPSS.sav> — sha256 `a29d1dc241f07708…`, retrieved 2026-10-13
- file `2025_Questionnaire_Eng.pdf`: <https://socsci4.tau.ac.il/mu2/ines/wp-content/uploads/sites/4/2025/07/2025_Questionnaire_Eng.pdf> — sha256 `7ab3fd203212392e…`, retrieved 2026-10-13

## Agam Institute - Media Index, news consumption in Israel (Dec 2024)

*מכון אגם - מדד התקשורת, צריכת חדשות וסיקור אקטואלי בישראל (דצמבר 2024)*

- **id:** `agam_media_index_2024` · **tier:** M · **publisher:** Agam Institute (Nimrod Nir, Dr. Gayil Talshir, Assa Shapira)
- **page:** <https://agamlabs.com/>
- **data as of:** 2024-11
- **terms:** Published report; figures cited with attribution
- **used by:** `news_websites`, `newspaper`
- file `agam_media_index_2024.pdf`: <https://agamlabs.com/wp-content/uploads/2025/03/12-compressed.pdf> — sha256 `a5a7d1bd1fa685c3…`, retrieved 2026-10-13
- manual data: `data/manual/agam/`

iPanel online sample, 1,201 citizens aged 18+ (325 Arab respondents), 15-20 Nov 2024, weighted by sector, sex, age, origin, region, religion, religiosity and 2022 turnout. Values exist only as charts; they are hand-transcribed into data/manual/agam/ with page numbers. Used for named news websites (pages 14-15) only; TV channels come from INES 2025 respondent data (docs/decisions/0006-media-sources.md).

## Israel Internet Association (ISOC-IL) and the Technion - Media Consumption and Disinformation Survey (October 2024), respondent-level data

*איגוד האינטרנט הישראלי והטכניון - סקר צריכת חדשות ודיסאינפורמציה (אוקטובר 2024), נתוני משיבים*

- **id:** `isoc_media_survey_2024` · **tier:** A · **publisher:** Israel Internet Association (ISOC-IL) and the Technion - Israel Institute of Technology
- **page:** <https://www.isoc.org.il/sts-data/media-and-disinformation-survey-il>
- **data as of:** 2024-10
- **terms:** Publication and citation permitted with credit to the Israel Internet Association and a link to https://www.isoc.org.il/sts-data/media-and-disinformation-survey-il

- **used by:** `media_age`, `media_sector`, `news_tv`, `news_radio`, `news_print`, `news_sites`, `news_social`, `news_search`, `news_podcasts`, `social_networks`, `news_networks`, `preferred_source`
- file `jewish.csv`: <https://drive.usercontent.google.com/download?id=1C_K2YvnTeRWqYs0EEaMOCG4XM3-j_505&export=download&confirm=t> — sha256 `6f27d07aca53bc34…`, retrieved 2026-10-14
- file `arab.csv`: <https://drive.usercontent.google.com/download?id=1NfAzq9GgrZa-5sJ04mJ444kJmyTp2W8_&export=download&confirm=t> — sha256 `92f4c1689ba5a839…`, retrieved 2026-10-14
- file `questionnaire.docx`: <https://drive.usercontent.google.com/download?id=1WdA_DBrRw1d2-zPNj2Kb95YDFnUzLIY3&export=download&confirm=t> — sha256 `494c2f0a7de1dcfa…`, retrieved 2026-10-14
- file `about.txt`: <https://drive.usercontent.google.com/download?id=1UqGTgxMWpKjn0Vi21SyMEHLGsSdevoA5&export=download&confirm=t> — sha256 `d7e7ce532597a131…`, retrieved 2026-10-14

Online panel (iPanel), October 2024: 1,005 internet users aged 18+, 805 Jewish (Haredim over-sampled) and 200 Arab respondents; no weights are supplied. The files are shared from the survey's Google Drive folder, linked from the page. The first data row of each CSV holds the question wording.

## TGI Israel - newspaper readership (average-issue exposure), as published in press reports

*סקר TGI - שיעורי החשיפה לעיתונים, כפי שפורסמו בתקשורת*

- **id:** `tgi_readership` · **tier:** M · **publisher:** TGI Israel; figures reported by Arutz Sheva (22 July 2026) and ice.co.il (22 March 2018)
- **page:** <https://www.inn.co.il/news/702128>
- **data as of:** 2025-07/2026-06
- **terms:** Published survey figures, cited with attribution
- **used by:** `newspaper`
- manual data: `data/manual/tgi/`

General TGI: representative sample of Jewish adults aged 18+ (about 5,000 respondents); weekday and weekend exposure by title, July 2025 - June 2026 (https://www.inn.co.il/news/702128). Haredi TGI (a separate, smaller survey of the Haredi sector), 2017, the latest release found online (https://www.ice.co.il/media/news/article/738702). Transcribed into data/manual/tgi/.

## Knesset Research and Information Center - change in advertising expenditure and the age distribution of newspaper readers (7 November 2018)

*מרכז המחקר והמידע של הכנסת - השינוי בהוצאה לפרסום והתפלגות קוראי עיתונות כתובה לפי גיל (7 בנובמבר 2018)*

- **id:** `knesset_rc_newspapers_2018` · **tier:** M · **publisher:** Knesset Research and Information Center
- **page:** <https://fs.knesset.gov.il/globaldocs/MMM/f1176d84-d2d2-e811-80e7-00155d0aeea3/2_f1176d84-d2d2-e811-80e7-00155d0aeea3_11_13572.pdf>
- **data as of:** 2018-H1
- **terms:** Knesset publication, cited with attribution
- **used by:** `newspaper`
- file `newspapers_by_age_2018.pdf`: <https://fs.knesset.gov.il/globaldocs/MMM/f1176d84-d2d2-e811-80e7-00155d0aeea3/2_f1176d84-d2d2-e811-80e7-00155d0aeea3_11_13572.pdf> — sha256 `f051982f08636d64…`, retrieved 2026-10-14
- manual data: `data/manual/tgi/`

Tables 2 and 4: weekday exposure to newspapers overall and to each title by age group (18-34, 35-54, 55+), from TGI for the first half of 2018; transcribed into data/manual/tgi/age_profile_2018.csv.

## IGRA - given names in the Israel Population Registry, "Other" religion (Nov 2021 extract)

*האגודה הישראלית לחקר שורשי משפחה - שמות פרטיים במרשם האוכלוסין, דת "אחר"*

- **id:** `igra_registry_names` · **tier:** A · **publisher:** Israel Genealogy Research Association (IGRA), compiled by Philip Trauring
- **page:** <https://genealogy.org.il/pop/>
- **data as of:** 2021-11-17
- **terms:** Published web tables; cited with attribution
- **used by:** `first_name`
- file `other-female.json`: <https://genealogy.org.il/pop/other-female/> — sha256 `fa2f2c53c6270324…`, retrieved 2026-10-13
- file `other-male.json`: <https://genealogy.org.il/pop/other-male/> — sha256 `bd10254b801bfbc0…`, retrieved 2026-10-13

Counts of each given name among people registered with religion "Other" (not Jewish, Muslim, Christian or Druze) - mostly immigrants from the former USSR and their children. No birth-year breakdown; the CBS tables (which lack an "Other" sheet) supply age profiles.

## CBS Local Authorities in Israel 2024 - data file for processing (p_libud_24)

*הרשויות המקומיות בישראל 2024 - קובץ נתונים לעיבוד*

- **id:** `cbs_local_authorities_2024` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS)
- **page:** <https://www.cbs.gov.il/he/publications/Pages/2019/%D7%94%D7%A8%D7%A9%D7%95%D7%99%D7%95%D7%AA-%D7%94%D7%9E%D7%A7%D7%95%D7%9E%D7%99%D7%95%D7%AA-%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C-%D7%A7%D7%95%D7%91%D7%A6%D7%99-%D7%A0%D7%AA%D7%95%D7%A0%D7%99%D7%9D-%D7%9C%D7%A2%D7%99%D7%91%D7%95%D7%93-1999-2017.aspx>
- **data as of:** 2024
- **terms:** CBS publication; reuse with attribution
- **used by:** `frame`, `immigrant_bucket`, `origin`
- **planned for:** `locality`
- file `p_libud_24.xlsx`: <https://www.cbs.gov.il/he/publications/DocLib/2019/hamakomiot1999_2017/p_libud_24.xlsx> — sha256 `2593d2adf8f2aca7…`, retrieved 2026-10-13

One row per local authority (municipalities, local councils, regional councils): population by religion and age group, socio-economic cluster, education, wages and more.

## Statistical Abstract of Israel 2025, ch. 2 - population of Israelis by population group, religion, sex and age (table 2.3)

*שנתון סטטיסטי לישראל 2025, פרק 2 - אוכלוסיית הישראלים לפי קבוצת אוכלוסייה, דת, מין וגיל (לוח 2.3)*

- **id:** `cbs_abstract_2025_population` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS)
- **page:** <https://www.cbs.gov.il/he/publications/pages/2025/%D7%A9%D7%A0%D7%AA%D7%95%D7%9F-%D7%A1%D7%98%D7%98%D7%99%D7%A1%D7%98%D7%99-%D7%9C%D7%99%D7%A9%D7%A8%D7%90%D7%9C-2025-%D7%9E%D7%A1%D7%A4%D7%A8-76.aspx>
- **data as of:** 2024 (annual average)
- **terms:** CBS publication; reuse with attribution
- **used by:** `frame`, `age`, `origin`, `marital_status`
- file `st02_03.xlsx`: <https://www.cbs.gov.il/he/publications/doclib/2025/2.shnatonpopulation/st02_03.xlsx> — sha256 `543caa013f490488…`, retrieved 2026-10-13
- file `st02_07.xlsx`: <https://www.cbs.gov.il/he/publications/doclib/2025/2.shnatonpopulation/st02_07.xlsx> — sha256 `e7d08c918aeb17d5…`, retrieved 2026-10-13
- file `st02_06_2024.xlsx`: <https://www.cbs.gov.il/he/publications/doclib/2024/2.shnatonpopulation/st02_06.xlsx> — sha256 `77c8d2338e347b80…`, retrieved 2026-10-13

Thousands, 2024 average. Single years of age by sex for Arabs and for Jews and others; 5-year groups by sex for Jews, Muslims, Christians, Arab Christians, Druze and those not classified by religion. st02_07 gives Jews and others by continent of origin and birth.

## Statistical Abstract of Israel 2025, ch. 2 - persons marrying, by sex, age, previous marital status and religion (table 2.24, 2023)

*שנתון סטטיסטי לישראל 2025, פרק 2 - נישאים, לפי מין, גיל, מצב משפחתי קודם ודת (לוח 2.24, 2023)*

- **id:** `cbs_abstract_2025_marriages` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS)
- **page:** <https://www.cbs.gov.il/he/publications/pages/2025/%D7%A9%D7%A0%D7%AA%D7%95%D7%9F-%D7%A1%D7%98%D7%98%D7%99%D7%A1%D7%98%D7%99-%D7%9C%D7%99%D7%A9%D7%A8%D7%90%D7%9C-2025-%D7%9E%D7%A1%D7%A4%D7%A8-76.aspx>
- **data as of:** 2023
- **terms:** CBS publication; reuse with attribution
- **used by:** `marital_status`
- file `st02_24.xlsx`: <https://www.cbs.gov.il/he/publications/doclib/2025/2.shnatonpopulation/st02_24.xlsx> — sha256 `d99aa59c54bf7788…`, retrieved 2026-10-13

Marriages registered in 2023 by single year of age (up to 24) for Jews, Muslims, Christians and Druze. Used only to estimate how many 18-19-year-olds are married, an age the Social Survey (20+) does not cover.

## Statistical Abstract of Israel 2025, ch. 28 - public attitudes (Social Survey), persons aged 20+ by selected characteristics and by extent of religiosity

*שנתון סטטיסטי לישראל 2025, פרק 28 - עמדות ותחושות הציבור (הסקר החברתי), בני 20 ומעלה לפי תכונות נבחרות ולפי מידת דתיות*

- **id:** `cbs_abstract_2025_attitudes` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS) - Social Survey
- **page:** <https://www.cbs.gov.il/he/publications/Pages/2025/%D7%A2%D7%9E%D7%93%D7%95%D7%AA-%D7%95%D7%AA%D7%97%D7%95%D7%A9%D7%95%D7%AA-%D7%94%D7%A6%D7%99%D7%91%D7%95%D7%A8-%D7%A9%D7%A0%D7%AA%D7%95%D7%9F-%D7%A1%D7%98%D7%98%D7%99%D7%A1%D7%98%D7%99-%D7%9C%D7%99%D7%A9%D7%A8%D7%90%D7%9C-2025-%D7%9E%D7%A1%D7%A4%D7%A8-76.aspx>
- **data as of:** 2024 (Social Survey)
- **terms:** CBS publication; reuse with attribution
- **used by:** `religiosity`
- file `st28_01x.xlsx`: <https://www.cbs.gov.il/he/publications/DocLib/2025/28.ShnatonPublicAttitudesandPerceptions/st28_01x.xlsx> — sha256 `572c3569bd902e44…`, retrieved 2026-10-13
- file `st28_04x.xlsx`: <https://www.cbs.gov.il/he/publications/DocLib/2025/28.ShnatonPublicAttitudesandPerceptions/st28_04x.xlsx> — sha256 `66da1d4941592771…`, retrieved 2026-10-13

## Wikidata - given-name items with Hebrew labels (for English transliteration of names)

*ויקינתונים - פריטי שמות פרטיים עם תווית בעברית (לתעתיק שמות לאנגלית)*

- **id:** `wikidata_given_names` · **tier:** A · **publisher:** Wikidata (Wikimedia Foundation)
- **page:** <https://query.wikidata.org/>
- **terms:** CC0 1.0
- **planned for:** `first_name`
- file `given_names.json`: <https://query.wikidata.org/sparql> — sha256 `7e9d9b23d737da6a…`, retrieved 2026-10-13

Used only to display names in English. Results of a live query can change over time; the pinned checksum records exactly which snapshot the model used.

## Statistical Abstract of Israel 2021, table 2.8 - Jews by country of origin and age (2020 average)

*שנתון סטטיסטי לישראל 2021, לוח 2.8 - יהודים לפי ארץ מוצא וגיל (ממוצע 2020)*

- **id:** `cbs_abstract_2021_origin` · **tier:** A · **publisher:** Central Bureau of Statistics (CBS)
- **page:** <https://www.cbs.gov.il/he/publications/Pages/2021/%D7%90%D7%95%D7%9B%D7%9C%D7%95%D7%A1%D7%99%D7%99%D7%94-%D7%A9%D7%A0%D7%AA%D7%95%D7%9F-%D7%A1%D7%98%D7%98%D7%99%D7%A1%D7%98%D7%99-%D7%9C%D7%99%D7%A9%D7%A8%D7%90%D7%9C-2021-%D7%9E%D7%A1%D7%A4%D7%A8-72.aspx>
- **data as of:** 2020 (annual average)
- **terms:** CBS publication; reuse with attribution
- **used by:** `origin`, `generation`, `birth_region`
- file `st02_08.xls`: <https://www.cbs.gov.il/he/publications/doclib/2021/2.shnatonpopulation/st02_08.xls> — sha256 `4fc804bd9605b054…`, retrieved 2026-10-13

The last edition with the country-level breakdown. Origin = own country of birth for people born abroad, father's country of birth for people born in Israel; Israel-born of Israel-born fathers form their own category.

## OECD Survey of Adult Skills (PIAAC) 2023 - annex tables of chapters 2 and 3 (all participating countries, including Israel)

*סקר מיומנויות הבוגרים של ה-OECD (PIAAC) 2023 - לוחות הנספח לפרקים 2 ו-3 (כל המדינות המשתתפות, כולל ישראל)*

- **id:** `oecd_piaac_2023_tables` · **tier:** A · **publisher:** OECD
- **page:** <https://www.oecd.org/en/publications/survey-of-adults-skills-2023-country-notes_ab4f6b8c-en/israel_3915a641-en.html>
- **data as of:** 2022-23 (data collection)
- **terms:** OECD terms and conditions (reuse with attribution)
- **used by:** `literacy_level`, `literacy_score`, `literacy_percentile`
- file `piaac_2023_chapter2_tables.xlsx`: <https://stat.link/files/b263dc5d-en/eb8dxq.xlsx> — sha256 `c12ccf3e3f6a0bd0…`, retrieved 2026-10-14
- file `piaac_2023_chapter3_tables.xlsx`: <https://stat.link/files/b263dc5d-en/owiypl.xlsx> — sha256 `9274f8cf17e19387…`, retrieved 2026-10-14

StatLink workbooks of "Do Adults Have the Skills They Need to Thrive in a Changing World? Survey of Adult Skills 2023". Israel's sample: 6,092 adults aged 16-65 (61% response rate), assessed in Hebrew or Arabic. Used: literacy mean, standard deviation and percentiles (A.2.1), proficiency levels (A.2.2), by age (A.2.4), education (A.2.5), gender (A.2.7), and education by age (A.3.11).

## Bank of Israel Research Department, Skills of Israel's Population by International Comparison: Initial Findings of the 2022-2023 PIAAC Survey (Policy Analysis Note 2024.03)

*בנק ישראל, חטיבת המחקר - מיומנויות האוכלוסייה בישראל בהשוואה בין-לאומית: ממצאים ראשונים מסקר PIAAC 2022-2023 (סקירה 2024.03)*

- **id:** `boi_piaac_note_2024` · **tier:** M · **publisher:** Bank of Israel (Sefi Bahar and Elad DeMalach)
- **page:** <https://www.boi.org.il/media/1tgdsdvt/lm202403e.pdf>
- **data as of:** 2022-23
- **terms:** Bank of Israel publication; cited with attribution
- **used by:** `literacy_level`
- file `lm202403e.pdf`: <https://www.boi.org.il/media/1tgdsdvt/lm202403e.pdf> — sha256 `9e74cf12cd5f95ad…`, retrieved 2026-10-14
- manual data: `data/manual/piaac/`

Figure 2b gives mean scores of non-Haredi Jews, Arabs and Haredim (computed by the authors in the CBS research room); transcribed into data/manual/piaac/boi_group_means.csv.

## CBS Social Survey 2024 - custom cross-tabulations from the official table generator (persons aged 20+)

*הסקר החברתי 2024 של הלמ"ס - הצלבות מותאמות ממחולל הלוחות הרשמי (בני 20 ומעלה)*

- **id:** `cbs_social_survey_2024` · **tier:** B · **publisher:** Central Bureau of Statistics (CBS) - Social Survey
- **page:** <https://boardsgenerator.cbs.gov.il/pages/Seker/wizardpage.aspx>
- **data as of:** 2024
- **terms:** CBS publication (online table generator); reuse with attribution
- **used by:** `religiosity`, `marital_status`, `children`, `education`, `military_service`, `in_service`, `labour_status`, `occupation`, `industry`, `work_status`, `income`, `household_income`, `income_amount`, `income_percentile`, `household_income_amount`, `household_income_percentile`, `home_ownership`, `health`, `chronic`, `disability`, `online`
- **planned for:** `internet`
- manual data: `data/manual/cbs_ss/`

Weighted frequencies (persons) with relative standard errors, queried through the generator's own JSON handlers inside a headless browser (`popsim fetch-cbs-ss`). Each table's query spec is in data/manual/cbs_ss/queries/<id>.json and the result in data/manual/cbs_ss/<id>.csv. Variable and category codes: data/manual/cbs_ss/variables_2024.json. Arab tables exclude the Jerusalem district, whose Arab residents are mostly not citizens.

