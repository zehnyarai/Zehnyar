#!/usr/bin/env bash
# ONLY fresh disposable CI emulators. Never run uninstall commands on an owner's phone.
set -euo pipefail
if [ "${GITHUB_ACTIONS:-}" != "true" ] || [ "$(adb shell getprop ro.kernel.qemu | tr -d '\r')" != "1" ]; then
  echo 'Refusing fixture install/cleanup: only a disposable GitHub Actions emulator is allowed.' >&2
  exit 1
fi
adb install --no-streaming native-test-output/keyvault-app.apk
adb install --no-streaming native-test-output/keyvault-tests.apk
instrument() {
  local result message
  result="$(adb shell am instrument -w "$@" ir.pestino.app.test/androidx.test.runner.AndroidJUnitRunner)"
  printf '%s\n' "$result"
  if ! grep -Eq 'OK \([0-9]+ tests?\)' <<< "$result" || grep -Eq 'FAILURES!!!|INSTRUMENTATION_FAILED' <<< "$result"; then
    message="$(tail -c 7000 <<< "$result")"
    message="${message//'%'/'%25'}"
    printf '::error title=AndroidKeyStore test diagnostics::%s\n' "${message//$'\n'/%0A}"
    exit 1
  fi
}
instrument
instrument -e class ir.pestino.app.DeviceKeyVaultUpgradeTest -e pestinoStage seed
adb shell am force-stop ir.pestino.app
# This is the essential update check: same package/signature, NO uninstall, NO data clear.
# It verifies package replacement with the same test APK, not compatibility with old releases.
adb install -r --no-streaming native-test-output/keyvault-app.apk
instrument -e class ir.pestino.app.DeviceKeyVaultUpgradeTest -e pestinoStage verify
printf '::notice title=Persistent encrypted provider keys::API %s: real AndroidKeyStore roundtrip, ciphertext, deletion and install -r retention (unchanged UID, both dummy keys) passed.\n' "$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
# Discard only fixture data in this ephemeral test app before testing the signed release APK.
adb uninstall ir.pestino.app.test
adb uninstall ir.pestino.app
