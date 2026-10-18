#!/usr/bin/env bash
# ONLY fresh disposable CI emulators. Never run uninstall commands on an owner's phone.
set -euo pipefail
adb install --no-streaming native-test-output/keyvault-app.apk
adb install --no-streaming native-test-output/keyvault-tests.apk
result="$(adb shell am instrument -w ir.pestino.app.test/androidx.test.runner.AndroidJUnitRunner)"
printf '%s\n' "$result"
if ! grep -Eq 'OK \([0-9]+ tests?\)' <<< "$result" || grep -Eq 'FAILURES!!!|INSTRUMENTATION_FAILED' <<< "$result"; then
  message="$(tail -c 7000 <<< "$result")"
  message="${message//'%'/'%25'}"
  printf '::error title=AndroidKeyStore test diagnostics::%s\n' "${message//$'\n'/%0A}"
  exit 1
fi
printf '::notice title=Persistent encrypted provider keys::API %s: real AndroidKeyStore roundtrip, ciphertext and deletion tests passed with dummy keys.\n' "$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
# Discard only fixture data in this ephemeral test app before testing the signed release APK.
adb uninstall ir.pestino.app.test
adb uninstall ir.pestino.app
