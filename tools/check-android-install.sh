#!/usr/bin/env bash
set -euo pipefail
report="$(adb install --no-streaming apk-output/Pestino-0.7.9.apk 2>&1)" || {
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
sleep 8
adb shell pidof ir.pestino.app | grep -q '[0-9]'
if adb logcat -d -b crash | grep -q 'Process: ir.pestino.app'; then
  message="$(adb logcat -d -b crash | tail -n 70)"
  printf '::error title=Native launch crash::%s\n' "${message//$'\n'/%0A}"
  exit 1
fi
printf '::notice title=Android install smoke test::API %s: APK installed and MainActivity launched without a native crash.\n' "$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
# Do not confuse a running Activity with a rendered UI. Check visible WebView
# accessibility text as well; a JS boot failure must stop installer delivery.
rendered=0
# A first cold start of the WebView on a fresh emulator can take well over a minute
# (API 35 once missed a 16-second window while the same APK rendered on API 24). Waiting
# longer does not weaken the check: the real Persian hero and scan action must still appear.
for attempt in {1..30}; do
  adb shell uiautomator dump /sdcard/pestino-launch.xml >/dev/null 2>&1 || true
  adb pull /sdcard/pestino-launch.xml apk-output/launch-ui.xml >/dev/null 2>&1 || true
  if python3 - <<'PYUI'
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
p = Path('apk-output/launch-ui.xml')
if not p.exists(): sys.exit(1)
try:
    root = ET.fromstring(p.read_text())
    text = ' '.join(n.get('text', '') + ' ' + n.get('content-desc', '') for n in root.iter())
    sys.exit(0 if 'دستیار هوشمند باغداران پسته' in text and 'شروع اسکن آفت' in text else 1)
except ET.ParseError:
    sys.exit(1)
PYUI
  then
    rendered=1
    break
  fi
  sleep 3
done
adb exec-out screencap -p > apk-output/launch-screen.png
if [ "$rendered" -ne 1 ]; then
  message="$(adb logcat -d | grep -E 'chromium|Capacitor/Console' | tail -n 45 || true)"
  printf '::error title=Pestino frontend did not render::%s\n' "${message//$'\n'/%0A}"
  exit 1
fi
printf '::notice title=Pestino rendered UI check::API %s: actual self-contained APK displayed the Persian hero and scan action. No diagnosis or payment activated.\n' "$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
