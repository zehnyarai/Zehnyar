# منابع متنی، انتساب و شرایط بازنشر

این پوشه نگه‌دارندهٔ ورودی‌های محلی برای پیکرهٔ آفلاین «قرآن‌پژوهه» است. متنِ نمایشیِ ترجمه از منبع پین‌شده بازسازی می‌شود؛ جزئیات خروجی نیز در `static/offline-corpus.json` درج شده است.

## متن عربی

- `quran-uthmani.json`: از پروژهٔ [risan/quran-json](https://github.com/risan/quran-json)، مسیر منبع `data/tanzil/uthmani.json`؛ متن عثمانیِ Tanzil، با حفظ متن و انتساب.
- `chapters.json`: فرادادهٔ سوره‌ها از مسیر `data/tanzil/chapters.json` همان پروژه.
- مجوز بستهٔ Quran JSON: **CC BY-SA 4.0**؛ متن مجوز در `LICENSE-quran-json-CC-BY-SA-4.0.txt` است. این مجوز را نباید به ترجمهٔ فارسیِ زیر تعمیم داد.

## ترجمهٔ فارسی پایه

- مترجم: **محمدمهدی فولادوند** (Mohammad Mahdi Fooladvand).
- شناسهٔ ترجمه در Tanzil: **`fa.fooladvand`**.
- منبع رسمی و صفحهٔ ترجمه: [Tanzil — fa.fooladvand](https://tanzil.net/trans/fa.fooladvand).
- شرایط رسمی بازنشر: [Tanzil Translations](https://tanzil.net/trans/).
- شرایط Tanzil این ترجمه را برای **استفادهٔ غیرتجاری** مجاز می‌داند؛ استفادهٔ دیگر نیازمند اجازهٔ مترجم یا ناشر است. برای این ترجمه، مجوز CC BY یا مجوز تجاری ادعا نمی‌شود. مجوز کد یا مجوز یک آینهٔ داده نیز جای مجوز خودِ ترجمه را نمی‌گیرد.

### نسخهٔ داده و بازتولید

فایل `quran-fa-fooladvand.txt` یک snapshot دست‌نخورده از آینهٔ دادهٔ [app-furqan/quran_translations](https://github.com/app-furqan/quran_translations/blob/b46893686eabf1abf2157114e10fe5599bd42a2e/translations/fa.fooladvand.txt) است؛ این آینه برای دریافت فایل و پین‌کردن snapshot ثبت شده، نه به‌عنوان مرجع مجوز. مشخصات snapshot:

- مخزن: `app-furqan/quran_translations`
- commit: `b46893686eabf1abf2157114e10fe5599bd42a2e` (۱۵ اوت ۲۰۲۶)
- مسیر: `translations/fa.fooladvand.txt`
- Git blob: `222d65d4a476ff13ac9512f59ae7f69b790a46bf`
- اندازه: ۱٬۳۳۹٬۱۵۶ بایت
- SHA-256 فایل: `4d8cead0c9c7397e59adc4e773dd56b2da4c5700cda82d9ed648660fb190aa45`
- پوشش: ۶٬۲۳۶ ارجاع یکتا؛ هر سوره/آیه با متن عثمانی جفت می‌شود.

`translation_source.py` اعتبارسنجیِ SHA-256 و شمار رکوردها را انجام می‌دهد. برای ساخت دوبارهٔ `static/offline-corpus.json` از ریشهٔ این برنامه اجرا کنید:

```bash
python tools/build_offline_corpus.py
python tools/build_offline_corpus.py --check
```

خروجی شامل انتساب و فرادادهٔ منبع است. در رابط، پیوند صفحهٔ رسمی ترجمه و پیوند شرایط بازنشر نمایش داده می‌شود؛ متن فارسیِ هر آیه بدون بازنویسی منتقل شده است.

## شیوهٔ استفاده در برنامه

نسخهٔ فعلی برنامه به‌عنوان پروژهٔ پژوهشیِ غیرتجاری عرضه می‌شود. حمایت مالیِ صفحهٔ نخست اختیاری است و در برابر پرداخت، دسترسی یا قابلیت پولی نمی‌دهد. این توصیف، تفسیر حقوقیِ مستقل از شروط Tanzil نیست؛ پیش از هر مدل تجاری، تبلیغاتی، اشتراکی یا پرداخت در برابر دسترسی باید از مترجم/ناشر مجوز لازم گرفته شود.
