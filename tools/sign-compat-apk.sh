#!/usr/bin/env bash
# A test key only: not the owner's stable production/store signing identity.
# Never publish or cache the private keystore or its password.
set -euo pipefail
mkdir -p apk-output
export PESTINO_SIGNING_PASSWORD="$(openssl rand -hex 24)"
printf '::add-mask::%s\n' "$PESTINO_SIGNING_PASSWORD"
key="${RUNNER_TEMP:-/tmp}/pestino-compat.keystore"
trap 'rm -f "$key"' EXIT
keytool -genkeypair -keystore "$key" -alias pestino-test -storetype JKS \
  -keyalg RSA -keysize 2048 -validity 3650 \
  -storepass:env PESTINO_SIGNING_PASSWORD -keypass:env PESTINO_SIGNING_PASSWORD \
  -dname 'CN=Pestino compatibility test,O=Pestino,C=IR' -noprompt
unsigned=android/app/build/outputs/apk/release/app-release-unsigned.apk
"$ANDROID_HOME/build-tools/36.0.0/zipalign" -P 16 -f 4 "$unsigned" apk-output/aligned.apk
"$ANDROID_HOME/build-tools/36.0.0/apksigner" sign \
  --ks "$key" --ks-key-alias pestino-test \
  --ks-pass env:PESTINO_SIGNING_PASSWORD --key-pass env:PESTINO_SIGNING_PASSWORD \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --v4-signing-enabled false --out apk-output/Pestino-0.1.1.apk apk-output/aligned.apk
rm apk-output/aligned.apk
