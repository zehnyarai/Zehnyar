#!/usr/bin/env bash
set -euo pipefail
report="$(adb install --no-streaming apk-output/Pestino-0.1.1.apk 2>&1)" || {
  printf '::error title=Android package installation failed::%s\n' "${report//$'\n'/%0A}"
  exit 1
}
printf '%s\n' "$report"
grep -q Success <<< "$report"
adb shell pm path ir.pestino.app | grep -q package:
adb logcat -c
launch="$(adb shell am start -W -n ir.pestino.app/.MainActivity 2>&1)"
printf '%s\n' "$launch"
grep -q 'Status: ok' <<< "$launch"
# Wait for the launch to settle; this is a bounded native test, not a dev server.
sleep 5
adb shell pidof ir.pestino.app | grep -q '[0-9]'
if adb logcat -d -b crash | grep -q 'Process: ir.pestino.app'; then
  message="$(adb logcat -d -b crash | tail -n 70)"
  printf '::error title=Native launch crash::%s\n' "${message//$'\n'/%0A}"
  exit 1
fi
printf '::notice title=Android install smoke test::API %s: APK installed and MainActivity launched without a native crash.\n' "$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
