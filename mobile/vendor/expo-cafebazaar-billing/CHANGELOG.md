# Changelog

All notable changes to this project are documented in this file.

## [1.0.4] - 2026-06-29

### Added

- **`checkTrialSubscription()`** — Check whether the user is eligible for a trial subscription via Poolakey’s [`CheckTrialSubscriptionCallback`](https://github.com/cafebazaar/Poolakey).
- **`TrialSubscriptionInfo` type** — `{ isAvailable: boolean; trialPeriodDays: number }`.
- **`ERR_TRIAL` error code** — Returned when the trial check fails or Bazaar does not support the feature.

### Documentation

- README updated with usage example, API reference entry, and error code.

[1.0.4]: https://github.com/ssshojaei/expo-cafebazaar-billing/releases/tag/v1.0.4
