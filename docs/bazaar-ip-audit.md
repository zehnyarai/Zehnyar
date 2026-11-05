# Cafe Bazaar intellectual-property review — preliminary

**Status: INCOMPLETE. This is an engineering evidence log, not legal advice or a claim of Cafe Bazaar approval.** Reviewed 2026-11-05 against the intellectual-property text supplied in this conversation. No Cafe Bazaar APK was built or inspected in this review.

## Requirements used

The supplied policy says public availability is not permission to republish; source attribution does not replace permission; protected works, fonts, imagery, code, libraries and marks must be used under applicable permission/licences; open-source terms and notices must be preserved; and a known app name/mark must not be used in a misleading or confusing way. Written approvals submitted to the store must identify the developer email and package name.

## Findings and evidence

### Brand assets and marks — ownership unresolved

The following files visibly use the Visayar globe-and-arrow design:

- `mobile/src/assets/icon.png`
- `mobile/src/assets/adaptive-icon.png`
- `mobile/src/assets/splash.png`
- `docs/branding/visayar-logo-source.png`
- `docs/branding/cafebazaar-icon-512.png`

The last filename is misleading: visual inspection shows the Visayar globe-and-arrow mark, not the Cafe Bazaar logo. The assets do not identify a creator, source, grant of rights, or licence. Repository history does not establish ownership or permission. Do not treat these assets as cleared until the developer confirms authorship/commission terms or provides the applicable licence/permission. Cafe Bazaar marks should not be added to the app icon or store artwork without documented permission. A developer-supplied Bazaar dashboard screenshot confirms the listing name `ویزایار` and package ID `ai.visayar.app`, matching the current project configuration; the screenshot does not establish ownership of the artwork or completion of publisher identity verification.

### App data and research content — permission/terms review outstanding

The data and source register are in `mobile/src/data/dataset.json`, `shared/dataset.json`, `mobile/src/data/researchSources.js`, `docs/data-and-sources.md`, and `docs/migration-research-methodology.md`. Records link to government and intergovernmental sources. Those citations support verification and attribution but do **not** by themselves authorize copying or republishing source text, tables, graphics, maps, or other protected material. No blanket reuse permission has been established for all sources. Before release, identify any verbatim/adapted third-party text, tables, images or datasets, check each source's reuse terms, and obtain permission where required. Keep factual values and original Visayar-written summaries distinct from copied source expression, and record source-specific attribution/permission.

No third-party photo or illustration has been positively identified by this limited source review; that is not proof that all dataset or listing content is original or cleared. Store screenshots, listing copy, ads, and publisher profile have not been reviewed here.

### Fonts and code licences — partial evidence

- Vazirmatn font files have `mobile/src/assets/Vazirmatn-OFL.txt` (SIL Open Font License 1.1). Preserve the licence with font redistribution and comply with its terms.
- The local `expo-cafebazaar-billing` fork has an MIT `LICENSE`; its README identifies upstream `ssshojaei/expo-cafebazaar-billing` version 1.0.4 and describes the local bridge change. Preserve the upstream copyright/licence notice and identify modifications where distributing that code.
- The Android billing module declares `com.github.cafebazaar.Poolakey:poolakey:2.2.0`. The Poolakey 2.2.0 tag identifies Apache-2.0; a copy of that tag's `LICENSE` is saved at `docs/third-party-licenses/Poolakey-2.2.0-LICENSE.txt`. Source: [Poolakey 2.2.0 LICENSE](https://github.com/cafebazaar/Poolakey/blob/2.2.0/LICENSE). This copy should be included with any distributable notices if Poolakey is present in the APK.
- Direct npm dependency metadata currently reports MIT for the Expo/React Native/navigation/storage dependencies and the local billing module, and Unlicense for `tweetnacl`. Metadata is a lead, not a substitute for checking the actual licence text and the packaged artifact.
- A preliminary scan of non-dev npm lock entries found 605 package entries; two metadata records (`qrcode-terminal`, `requireg`) did not declare a licence and `node-forge` declares `(BSD-3-Clause OR GPL-2.0)`. These are in the Expo CLI/tooling dependency chain and are not confirmed to be in the APK. This scan does **not** settle the final transitive npm or native/Maven dependency inventory.

**Not yet complete:** inspect the actual Bazaar APK's packaged JS/native dependencies, Android/Maven licences and notices; resolve relevant ambiguous or missing licence metadata; and prepare a complete distributable third-party notice set. Source files being present in the repository does not prove their licence texts reach users of the APK.

## Release blockers / evidence needed

1. Confirm who created or commissioned the Visayar logo and each image variant; provide the source/contract/licence or confirm that the developer owns sufficient distribution and adaptation rights. If a third-party or generative service was involved, identify the source/tool and applicable terms. If rights cannot be demonstrated, replace the affected assets with cleared originals before submission.
2. Confirm whether any data text, tables, images, maps or datasets were copied/adapted from external sources. For each such source, provide its reuse licence or written permission and the required attribution. Public availability or a source URL alone is insufficient.
3. Confirm the Cafe Bazaar publisher's legal/public name and public developer email, and whether the developer identity-verification process is complete. The dashboard screenshot confirms package ID `ai.visayar.app`; ensure the built APK continues to use it. Do not send passwords, identity documents, or private credentials in chat.
4. Confirm any written third-party approval that will be attached to the Cafe Bazaar submission includes that developer email and exact package ID. Do not use Cafe Bazaar or another party's logo/name as if Visayar were official or affiliated without permission.
5. Build the actual Bazaar variant and generate a complete dependency/licence inventory from that artifact before describing it as ready for publication.

Until these items are resolved, the Bazaar intellectual-property review remains **open**, and no compliance or release-readiness conclusion is made.
