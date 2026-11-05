# Cafe Bazaar advertising policy review — preliminary

**Status: source-level review; final APK verification pending.** Reviewed 2026-11-05 against the advertising-policy text supplied in this conversation. No Bazaar APK was built or inspected for this review.

## Current implementation findings

- `mobile/package.json` declares no advertising SDK or ad-network dependency. Searches of the app and local Android billing module found no ad placement/rendering, notification scheduling, push-notification API, overlay/window manager, lock-screen display, install shortcut, automatic ad click, or ad-attribution identifier implementation.
- The Android app config declares an empty explicit permissions list and blocks `RECORD_AUDIO` and `SYSTEM_ALERT_WINDOW`. The Android release workflow separately rejects a Cafe Bazaar APK that still contains `SYSTEM_ALERT_WINDOW`.
- The app opens destination-country official immigration pages, the curated research sources, and (from the admin screen) the secured payment-admin panel. The reviewed user-facing references are not ad placements or links to install another app. No reward-for-install, download incentive or unrelated-app promotion was found.
- `Alert.alert` is used for in-app validation, consent, errors and payment status; no app code was found scheduling promotional Android notifications. `expo-haptics` test mocks use a method named `notificationAsync`, but there is no production OS-notification integration in the declared dependencies or app source.
- Current monetization is the app's Cafe Bazaar in-app purchase flow in the Bazaar build, not advertising. The Bazaar payment screen does not show the manual card-transfer/receipt-upload path.

The screenshots supplied with the policy illustrate promotional notifications and fake antivirus/system-style dialogs. No analogous behavior was found in the reviewed source.

## Remaining checks

1. Build the Bazaar APK and inspect the **merged manifest and packaged native dependency tree** for advertising SDKs, ad-ID/location/notification/overlay permissions, or unexpected components. The present source search is not an APK SBOM.
2. Review the actual Cafe Bazaar listing and its detected “contains ads” label after upload. This repository review cannot see the publisher panel or store-side SDK scanner.
3. Keep the app accurately categorized for its intended audience. If any advertising SDK is added later, review its ad content and targeting for the audience, mark ads clearly, disclose relevant collection/use/sharing in the privacy notice, do not request precise location solely for advertising, and keep placements non-disruptive and inside the app. Do not permit notification, lock-screen, fake system/update UI, overlay, shortcut, hidden, automated-click or install-incentive ads.

**Conclusion:** no advertising behavior is intentionally implemented in the inspected source, so no ad creative or ad network needs remediation in source at this point. Do not make a final “no ads” or compliance claim until the built artifact and Bazaar listing are checked.
