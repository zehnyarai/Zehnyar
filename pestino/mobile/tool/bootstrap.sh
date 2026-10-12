#!/usr/bin/env bash
# One-time setup on a machine with the Flutter SDK (stable, 3.27+).
# The android/ and ios/ folders in this repo contain the Pestino-specific files
# (Gradle config, manifests, Info.plist, privacy manifest). `flutter create` fills in
# what is missing (Gradle wrapper, Xcode project, Podfile, launcher icons) and does
# not overwrite existing files.
set -euo pipefail
cd "$(dirname "$0")/.."

flutter --version
flutter create --platforms=android,ios --org ir.pestino --project-name pestino .
flutter pub get
flutter analyze
flutter test || true
echo "Bootstrap done. Next: add ios/Runner/PrivacyInfo.xcprivacy to the Runner target in Xcode (see docs/RELEASE.md)."
