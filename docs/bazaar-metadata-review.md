# Cafe Bazaar deceptive-behavior and listing review — preliminary

**Status: source and draft-listing review only; Bazaar panel and final APK remain unverified.** Reviewed 2026-11-05 against the text supplied in this conversation.

## Changes made to reduce misleading claims

- The launcher name in `mobile/app.json` is `ویزایار`; the draft store title now uses exactly `ویزایار` rather than adding a tagline. The actual Cafe Bazaar listing and launcher label on a built device still need comparison.
- The Profile badge that said “کاملاً آفلاین / Fully offline” was too broad: payments, public stories, data updates and some entitlement checks need internet. It now says “محاسبه روی دستگاه / On-device scoring”. The store draft distinguishes offline assessment from network-dependent functions.
- The home headline no longer says “judge your migration odds”; it describes comparing pathways with data. The story-section subtitle now says stories are submitted by users and published after review, rather than asserting that submissions are true.
- The app and listing now state that Visayar is independent and is not affiliated with any government or immigration authority. Result copy distinguishes estimates from official decisions and legal advice.
- `docs/store-listing.md` now contains a separate concise Bazaar listing draft covering two free full assessments, one credit per assessment, Cafe Bazaar-only in-app package purchases, consumable/no-auto-renewal status, online requirements, estimates, optional moderated user stories and relevant data flows.

## Source findings

- No in-app Cafe Bazaar rating/review prompt, incentive for installs or ratings, giveaway/competition feature, or leaderboard was found in the reviewed app source. Do not add positive-rating incentives or repeated/forced review prompts.
- The source does not claim that Visayar is a government service. It links to destination-authority portals and labels those as sources; the independent-service disclaimer is now explicit in app copy.
- The app displays an estimated “chance” score with estimate disclaimers. The store copy calls the scores comparative estimates, not approval odds or guarantees.

## Still unresolved

1. A developer-supplied dashboard screenshot shows Bazaar title `ویزایار`, package ID `ai.visayar.app`, and a globe-and-arrow icon that appears consistent with the project icon; `mobile/app.json` uses the same title and package ID. The screenshot does not prove exact icon-file identity or rights. The actual description, category, age-rating answers, screenshots and video still need review in the panel; confirm the category matches the app and all creative is taken from the final build and suitable for the required audience.
2. The screenshot examples pasted with the policy are policy examples, not evidence of Visayar screenshots. No final Bazaar listing artwork was reviewed.
3. The app icon's rights remain unresolved in `docs/bazaar-ip-audit.md`; visual similarity does not establish ownership. Verify the icon used in the store is the same Visayar identity users see after installation and clear rights before publishing.
4. Store-side ratings, comments, install counts, developer replies, publisher profile and any ad/SDK tag cannot be audited here. No fabricated reviews or ratings should be added; publisher responses should address the reported issue without marketing or exposing personal data.
5. The draft lists a proposed category/rating only as items for publisher verification; select the actual values from Cafe Bazaar's current panel rather than treating the old direct-distribution metadata as authoritative.

Do not present the listing draft as a checked or submitted Cafe Bazaar listing. Validate title, icon, description, category, age suitability, payments and screenshots against the built Bazaar app before submission.

## Supplied policy-history note

The developer supplied the publishing-guidelines history, which lists historical updates: 1395/02/25 (spam and store ranking); 1397/11/07 (monetization and ads) and 1397/11/08 (restricted content and security); 1399/07/09 (content/quality, IP/deceptive behavior, security/privacy, monetization/ads, ratings/reviews); and 1400/05/06 (content), 1400/05/09 (quality), 1400/05/10 (security), 1400/05/12 (IP), 1400/05/13 (deceptive behavior and ads), and 1400/06/24 (privacy). These are the dates in the supplied history, not evidence that the live guidelines have had no later amendments. The official page was not accessible from this environment, so the review continues to rely on the text supplied by the developer; check the current Cafe Bazaar page and panel again before submission.
