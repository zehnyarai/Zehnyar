#!/usr/bin/env bash
# ONLY fresh disposable CI emulators. Never run uninstall commands on an owner's phone.
set -euo pipefail
adb install --no-streaming native-test-output/keyvault-app.apk
adb install --no-streaming native-test-output/keyvault-tests.apk
result="$(adb shell am instrument -w ir.pestino.app.test/androidx.test.runner.AndroidJUnitRunner)"
printf '%s\n' "$result"
grep -Eq 'OK \([0-9]+ tests?\)' <<< "$result"
if grep -Eq 'FAILURES!!!|INSTRUMENTATION_FAILED' <<< "$result"; then exit 1; fi
printf '::notice title=Persistent encrypted provider keys::API %s: real AndroidKeyStore roundtrip, ciphertext and deletion tests passed with dummy keys.\n' "$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
# Discard only fixture data in this ephemeral test app before testing the signed release APK.
adb uninstall ir.pestino.app.test
adb uninstall ir.pestino.app
