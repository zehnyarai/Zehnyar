# ذهنیار · Zehnyar

این مخزن دو بخش مستقل دارد:

| بخش | مسیر | وضعیت |
| --- | --- | --- |
| **مهاجریار** — سامانه هوشمند انتخاب مسیر مهاجرت (FastAPI + PWA + اندروید) | [`mohajeryar/`](mohajeryar/README.md) | فعال و کامل |
| API قدیمی تشخیص بیماری پسته | [`main.py`](main.py) | میراثی (legacy) |

---

## مهاجریار

ارزیابی ۱۲ مسیر مهاجرتی در ۷ کشور با قواعد رسمی ۲۰۲۶؛ خروجی شامل امتیاز، شکاف‌ها، هزینه، زمان، نقشه‌ی راه و چک‌لیست مدارک است. رابط فارسی راست‌به‌چپ، نصب‌شدنی (PWA)، دارای پوستهٔ اندروید و قابل اجرا روی سرور شخصی.

```bash
cd mohajeryar
./install.sh
./run.sh          # http://127.0.0.1:8000
```

- مستندات کامل: [`mohajeryar/README.md`](mohajeryar/README.md)
- روش‌شناسی و منابع: صفحهٔ `/methodology` پس از اجرا
- آزمون‌ها: `cd mohajeryar && ../.venv/bin/python -m pytest -q` (۵۳ آزمون)
- نسخهٔ اندروید: workflow «Build Mohajeryar APK» → Release با برچسب `apk-mohajeryar`

### ساختار سریع

```text
mohajeryar/
├── app/             # FastAPI، مدل داده، موتور ۷ کشور، قالب‌ها، استاتیک
├── tests/           # آزمون موتور و API
├── mobile/android/  # پوستهٔ WebView با صفحهٔ اتصال به سرور
├── Dockerfile · docker-compose.yml · render.yaml
└── install.sh · run.sh · install.bat · run.bat
```

> مهاجریار جایگزین مشاورهٔ حقوقی یا بررسی سفارت نیست. اعداد با تاریخ بازبینی و پیوند منبع نمایش داده می‌شوند.
