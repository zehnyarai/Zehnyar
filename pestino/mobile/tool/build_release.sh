#!/usr/bin/env bash
# Usage: API_BASE_URL=https://api.pestino.ir tool/build_release.sh [aab|apk|ipa]
# Store builds require android/key.properties and the store flag.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${API_BASE_URL:?Set API_BASE_URL, e.g. https://api.pestino.ir}"
TARGET="${1:-aab}"
DEFINES=(--dart-define="API_BASE_URL=${API_BASE_URL}" --obfuscate --split-debug-info=build/symbols)

flutter pub get
flutter analyze
flutter test

case "$TARGET" in
  aab)  flutter build appbundle --release -PpestinoStoreBuild=true "${DEFINES[@]}" ;;   # Google Play
  apk)  flutter build apk --release --split-per-abi -PpestinoStoreBuild=true "${DEFINES[@]}" ;; # Cafe Bazaar, Myket, direct download
  ipa)  flutter build ipa --release "${DEFINES[@]}" ;;                                   # App Store (macOS only)
  *)    echo "Unknown target: $TARGET"; exit 1 ;;
esac
echo "Artifacts are under build/ and must be uploaded to the store console. Keep the symbols in build/symbols for crash reports."
