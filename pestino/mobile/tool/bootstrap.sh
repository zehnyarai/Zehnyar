#!/usr/bin/env bash
# One-time setup on a machine with the Flutter SDK (stable).
# Pestino's Android/iOS files are kept as the source of truth: `flutter create` generates
# the template (Gradle wrapper, Xcode project, Podfile, icons), then our files are copied back on top,
# so signing config, manifests and Gradle version are never silently overwritten.
set -euo pipefail
cd "$(dirname "$0")/.."

SAVED="$(mktemp -d)"
cp -r android ios "$SAVED"/ 2>/dev/null || cp -r android "$SAVED"/

flutter --version
flutter create --platforms=android,ios --org ir.pestino --project-name pestino .
cp -r "$SAVED"/android/. android/
[ -d "$SAVED/ios" ] && cp -r "$SAVED"/ios/. ios/
rm -f test/widget_test.dart

flutter pub get
flutter analyze
flutter test
echo "Bootstrap done. Add ios/Runner/PrivacyInfo.xcprivacy to the Runner target in Xcode (see docs/RELEASE.md)."
