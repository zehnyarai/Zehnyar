"""همگام‌سازی داده و فونت از پوشه‌ی اصلی پروژه به assets اندروید.

خروجی (در .gitignore است و هر بار ساخته می‌شود):
  app/src/main/assets/www/data/bundle.js   داده‌ها به‌صورت window.RZ_DATA
  app/src/main/assets/www/fonts/...        فونت وزیرمتن
  app/src/main/assets/www/icon.png         آیکون
اجرای محلی: python3 android/scripts/sync_assets.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ANDROID = Path(__file__).resolve().parents[1]
PROJECT = ANDROID.parent  # پوشه‌ی reshteyar
WWW = ANDROID / "app" / "src" / "main" / "assets" / "www"
DATA_FILES = ["groups", "factors", "universities", "fields", "meta"]


def main() -> None:
    bundle = {}
    for name in DATA_FILES:
        with open(PROJECT / "data" / f"{name}.json", encoding="utf-8") as fh:
            bundle[name] = json.load(fh)

    (WWW / "data").mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    (WWW / "data" / "bundle.js").write_text(f"window.RZ_DATA = {payload};\n", encoding="utf-8")

    fonts_dst = WWW / "fonts"
    fonts_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(PROJECT / "app" / "static" / "fonts" / "Vazirmatn-Variable.woff2", fonts_dst)
    shutil.copy(PROJECT / "app" / "static" / "icons" / "icon-192.png", WWW / "icon.png")

    counts = {k: len(v) for k, v in bundle.items() if isinstance(v, list)}
    print("assets synced:", counts)


if __name__ == "__main__":
    main()
