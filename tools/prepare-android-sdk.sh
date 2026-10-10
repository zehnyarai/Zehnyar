#!/usr/bin/env bash
set -euo pipefail
root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
# sdkmanager is installed on hosted runners, but not necessarily on PATH.
# Avoid replacing a working SDK with an old command-line-tools bootstrap.
if [ -f "$root/platforms/android-36/android.jar" ] && [ -x "$root/build-tools/36.0.0/apksigner" ]; then
  echo "Android platform 36 and build-tools 36 are already installed."
  exit 0
fi
manager="$(find "$root" -maxdepth 5 -path '*/bin/sdkmanager' -type f 2>/dev/null | head -n 1)"
if [ -z "$manager" ]; then
  echo "::error title=Android SDK missing::No sdkmanager was found under $root; an actual SDK is required, not a source ZIP."
  find "$root" -maxdepth 3 -type d 2>/dev/null || true
  exit 1
fi
set +e
set +o pipefail
yes | "$manager" --sdk_root="$root" --licenses > sdk-licenses.log 2>&1
licenses=$?
set -o pipefail
if [ "$licenses" -eq 0 ]; then
  "$manager" --sdk_root="$root" "platforms;android-36" "build-tools;36.0.0" > sdk-install.log 2>&1
  result=$?
else
  result=$licenses
fi
set -e
if [ "$result" -ne 0 ]; then
  python3 - <<'PY'
from pathlib import Path
message = '\n'.join(p.read_text()[-12000:] for p in [Path('sdk-licenses.log'), Path('sdk-install.log')] if p.exists())
message = message.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
print('::error title=Android SDK diagnostics::' + message)
PY
  exit "$result"
fi
printf 'Android SDK 36 is ready.\n'
