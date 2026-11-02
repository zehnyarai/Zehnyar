# Migration research and data-update policy

**Status:** research inventory and maintenance policy, not a claim of exhaustive global coverage. The mobile directory is a curated entry point; it does not imply that every database, visa category, or country has been reviewed or integrated.

## Keep unlike evidence separate

| Evidence class | Preferred authority | Suitable use in Visayar | Not suitable for |
| --- | --- | --- | --- |
| Visa and permit rules | The destination country's competent immigration authority, legislation/gazette, and relevant embassy or consulate | Route requirements, required evidence, application steps, and official fees—only when a current, direct source supports the field | Replacing national rules with a regional summary or a third-party article |
| Regional legal guidance | European Commission legal-migration pages, followed by the relevant national authority | Orientation and links to national systems | Treating a general EU page as the operative national rule |
| Migration stock and flows | UN DESA International Migrant Stock; IOM Global Migration Data Portal; OECD migration reports and dashboards | Dated demographic and comparative context, with definitions and limitations | Individual visa eligibility, a personal approval probability, or current vacancies |
| Labour-market signals | EURES and the destination country's public employment/statistical service | Dated occupation/region context and links to vacancies | Inferring that a shortage occupation automatically grants a work permit or makes a person eligible |
| Forced displacement and protection | UNHCR Refugee Data Portal and applicable national protection authorities | Separate, clearly labeled humanitarian context | Mixing asylum/protection statistics into work, study, or family-route scoring |

The mobile app's existing eligibility assessment should continue to rely on route-specific, official requirements. Global datasets are context, not scoring rules. Do not turn a migration stock, forecast, labour shortage, or historical flow into a promise or individual probability.

## Reviewed reference inventory

The sources below were reviewed as research references and are now listed in the app's Profile → Migration research library. The inventory is selective; the directory itself is not evidence that each source's data has been imported into the app.

- **UN DESA — International Migrant Stock 2024:** estimates by origin and destination for 233 countries/areas, covering 1990–2024. A stock estimate is not an eligibility or vacancy measure. <https://www.un.org/development/desa/pd/content/international-migrant-stock>
- **IOM — Global Migration Data Portal:** its FAQ describes 70+ indicators from 20+ international data sources. Indicator years, methods, definitions, and limitations differ; follow through to the original data provider. <https://www.migrationdataportal.org/faqs>
- **OECD — International Migration Outlook 2025 and dashboard:** useful for migration movements, entry categories, and labour-market inclusion across OECD members. OECD coverage does not stand in for national immigration law. <https://www.oecd.org/en/publications/international-migration-outlook-2025_ae26c893-en.html> · <https://oecd.org/en/data/dashboards/international-migration-dashboard.html>
- **European Commission — Legal migration and resettlement:** regional orientation; confirm operative conditions with the relevant member state's official authority. <https://home-affairs.ec.europa.eu/policies/migration-and-asylum/legal-migration-and-resettlement_en>
- **EURES — Labour-market information:** country and regional context on vacancies and shortages/surpluses; evidence can be time- and geography-specific and is not a permit. <https://eures.europa.eu/living-and-working/labour-market-information_en>
- **UNHCR — Refugee Data Portal:** statistics on refugees, asylum-seekers, stateless people, and other forcibly displaced groups; keep protection data separate from regular migration-route scoring. <https://refugeedata.unhcr.org/en/>

## Field-level evidence standard

Before adding or changing a route, requirement, cost, labour-market figure, or date:

1. Record the exact destination, route, applicant category, and the meaning of the field. Do not generalize one permit subtype to all routes.
2. Prefer the competent national authority or the originating statistical provider. For a secondary portal, follow the citation to the original provider where possible.
3. Store a direct HTTPS source URL and the source's publication/effective/reference date. Distinguish a legal effective date from the date the app editor reviewed the record.
4. Record the review date only after a human actually checks the source. Never bulk-advance `lastVerified` because code or unrelated data changed.
5. If a fee is unknown, ambiguous, third-party, or not source-confirmed, do not display it as a confirmed government fee. Preserve the existing `verified: false` distinction and explain any estimate explicitly.
6. Capture the source's scope, definition, geography, year, and known limitations. Keep statistics, forecasts, job-market signals, and legal eligibility as separate evidence classes.
7. Have a second reviewer check material legal changes, uncertain translations, and high-impact amounts. Preserve a change log for review decisions.

Monthly review is a **review cadence**, not proof that every source changes monthly or that each record was checked. When a review is due, show that the user must verify the official source; do not fabricate newer values.

## Dataset delivery and regression controls

Mobile reference data is loaded in this order: validated bundled dataset → valid saved cache → optional HTTPS API refresh. The client should remain usable offline. Update delivery must preserve these controls:

- Reject a wrong schema, incomplete or malformed records, duplicate route identifiers, unsupported scoring rules, and unsafe/non-HTTPS source URLs.
- Honor ETags for conditional HTTP requests; a valid `304` reuses a valid cache.
- Validate the complete downloaded payload before saving it. A failed request or invalid payload must leave the last valid dataset available.
- Never accept a dataset-version rollback. An older server response or stale cache must not replace a newer bundled, cached, or active dataset. Content changes must advance the dataset version; same-version payload changes are rejected.
- Persist only validated data; include schema and data versions and keep cache format changes explicit.
- On accepted content changes, refresh the active dataset and recompute a saved assessment so its results are not silently stale.
- Expose last sync outcome and the dataset's recorded review date separately. A successful download is not the same as a fresh human source review.
- Run mobile tests, backend tests, bilingual parity checks, dataset validators, and a release build before publishing. A source edit or local-only diff is not a release verification.

The mobile sync code and focused tests were updated alongside this policy. They still require execution in the repository's installed dependency environment before the changes can be considered verified.
