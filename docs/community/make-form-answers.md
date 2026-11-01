# فرم شرکت در «سناریوی ماه» — پاسخ‌های آمادهٔ امشب

سناریو: `Integration Telegram Bot` · Scenario ID `6844102` · حساب: eu1.make.com · پلن Free

> **قاعدهٔ طلایی:** هر عددی در فرم می‌نویسی باید از خود Make قابل اثبات باشد. تنها عددی که همین حالا از اسکرین‌شات داری و قابل دفاع است: **حدود ۲٬۰۰۰ عملیات از ۶ اوت ۲۰۲۶** و **سناریو از ۶ اوت عمومی (Shared) است**. همین دو، «کاربر واقعی داشتن» را اثبات می‌کند.

---

## گام ۰ (۳۰ ثانیه، مهم‌ترین کار امشب): نام سناریو را عوض کن

`Integration Telegram Bot` نام پیش‌فرض قالب Make است. داور اول همین را می‌بیند و فکر می‌کند کپیِ قالب است. تغییر نام **هیچ اعتباری مصرف نمی‌کند**:

> Scenarios → روی سناریو → کلیک روی نام بالای بوم → مثلاً: **`Visayar Telegram Assistant — {کاری که می‌کند}`**

مثال‌ها: `Visayar Visa-Update Broadcaster` / `Visayar Support Bot — FAQ + human handoff` / `Visayar Alert Relay`

---

## گام ۱: لینک سناریو (فیلد اول فرم)

۱. سناریو را باز کن → دکمهٔ **Share** بالا-راست.
۲. **Public scenario page** باید روشن باشد (برچسب `Shared` در داشبورد را داری، ولی خودت چک کن).
۳. در کادر توضیح، متن بخش «گام ۲» را بگذار.
۴. لینک را کپی کن و **در پنجرهٔ Incognito** باز کن؛ اگر بدون لاگین باز شد، سالم است.
۵. همان لینک را در فیلد اول فرم بچسبان.

---

## گام ۲: توضیح صفحهٔ عمومی (۱ تا ۳ خط انگلیسی — داور اول این را می‌خواند)

یکی را انتخاب کن و `{}`ها را با واقعیت پر کن:

**اگر خبر/تغییر قوانین را به کاربران می‌رساند:**
> Watches official immigration sources and pushes a short, readable Telegram update whenever a rule, fee or deadline actually changes — so {N} users hear about it from their own channel instead of noticing too late.

**اگر پاسخ‌دهنده/پشتیبان است:**
> Answers incoming Telegram questions instantly from the project's own knowledge base, and escalates anything it is not confident about to a human — so {N} users get an answer in seconds instead of waiting.

**اگر اعلان/فوروارد است:**
> Turns the events that matter to {project} into one tidy Telegram message the team actually reads — {what}, routed, formatted and deduplicated, so nothing important dies in an inbox.

**اگر هیچ‌کدام دقیق نیست، این قالب خنثی را پر کن:**
> A Telegram bot for {project} that {کار اصلی در یک عبارت}. Live since August 2026 with ~2,000 operations for real users.

---

## گام ۳: «چرا باید برنده شود» (فیلد دوم — انگلیسی، ۳ تا ۵ جمله)

### متن پایه (قابل چسباندن؛ فقط جملهٔ ۲ را از «کیت تعویض» انتخاب کن)

> I built this bot for {project}, where {مخاطب} need {اطلاع/پاسخ} quickly and the manual way was {کار دستی قبلی}. It has been live since August 2026 and has handled roughly 2,000 operations for real users — so the utility is measured, not promised.
>
> {جملهٔ ۲ — از کیت تعویض}
>
> The part I am proudest of is what the bot refuses to do: {محدودیت/دروازهٔ انسانی}. Most chat bots in this space optimise for volume of replies; this one optimises for being right, and hands off when it is not. It is small, it costs almost nothing to run, and it already saves real time every week.

### کیت تعویض جملهٔ ۲ (یکی را بردار)

- **اگر با AI جواب می‌دهد:** `The creativity is in the guardrails: the model only sees a curated answer set, it must say "I don't know" when confidence is low, and that case goes to a human instead of being guessed.`
- **اگر خبر می‌فرستد:** `Instead of forwarding everything, it verifies the source and rewrites the change into one short, plain-language message — the filter is the product, not the bot.`
- **اگر اعلان است:** `The clever bit is the routing table: one message shape, deduplicated and grouped, so a channel people muted for noise becomes the channel they actually read.`
- **اگر از فرم/سفارش می‌آید:** `Everything arrives already formatted and labelled, so the human step is a single tap instead of a copy-paste job.`

### اگر برنده نشد چیزی از دست نمی‌دهی، ولی اگر اغراق کنی همه‌چیز

- عدد ننویس مگر این‌که در Make یا کانال، قابل نشان دادن باشد.
- اگر بخشی از منطق از قالب پیش‌فرض Make آمده، همان را بگو («قالب را برداشتم و این سه چیز را اضافه کردم») — داوران قالب‌ها را می‌شناسند و صداقت امتیاز دارد.

---

## گام ۴: اسکرین‌شات‌ها (به‌جای ویدیو، چون گفتي وقت نداری)

سه تصویر، هر کدام یک کار:

| # | چه چیزی | چرا |
|---|---|---|
| ۱ | بوم سناریو با **نام‌های توصیفی ماژول‌ها** و یک بلوک Notes سه‌خطی | ثابت می‌کند ساختار مال خودت است |
| ۲ | **History / خروجی اجرا**: پیام واقعی ارسال‌شده در تلگرام + لاگ موفق | ثابت می‌کند واقعاً کار می‌کند |
| ۳ | پیام دریافتی از دید **کاربر** (اسکرین‌شات تلگرام) | ثابت می‌کند کاربر واقعی دارد |

**قبل از گرفتن عکس:** ایمیل، توکن، آیدی کانال/چت، شماره و نام کاربران را تار کن. در لینک عمومی هم هر متن هاردکدشده در ماژول‌ها دیده می‌شود — توکنی در فیلد ماژول نگذار، همه در Connections باشد.

> اسکرین‌شات‌ها را می‌توانی در همان پست لینکدین بگذاری و لینک پست را هم در فرم اضافه کنی (فرم می‌گوید «هر چیزی که نشان دهد چطور کار می‌کند»).

---

## گام ۵: فرم را پر کن (۶۰ ثانیه)

[فرم Tally — Scenario of the Month](https://tally.so/r/MePybX)

| فیلد فرم | چه بچسبانی |
|---|---|
| Link to the scenario | لینک Share از گام ۱ (+ لینک پست لینکدین اگر ساختی) |
| Short reason why it should win | متن گام ۳ (کامل، ۳ پاراگراف کوتاه) |
| Your email | ایمیل فعالی که هر روز چک می‌کنی |
| Creator's email | خالی — خودت سازنده‌ای |

**مهلت: ۳۰ نوامبر ۲۰۲۶** · ماهی یک ارسال → این ماه همین، ماه بعد «رادار تغییر قوانین ویزا» با شانس بیشتر.

---

## چک‌لیست ۵ دقیقه‌ای پیش از زدن دکمهٔ Submit

- [ ] نام سناریو دیگر `Integration Telegram Bot` نیست
- [ ] صفحهٔ عمومی Share روشن است و در Incognito باز می‌شود
- [ ] توضیح صفحهٔ عمومی انگلیسی و یک‌خطی است (گام ۲)
- [ ] لینک عمومی هیچ توکن/ایمیل/آیدی چتی را نشان نمی‌دهد
- [ ] «چرا باید برنده شود» انگلیسی است و **هر عددش قابل اثبات** است
- [ ] اسکرین‌شات‌ها تار‌سازی‌شده‌اند
- [ ] ایمیل را دقیق تایپ کردی (جایزه با همین ایمیل هماهنگ می‌شود)
- [ ] لاگ فرم (صفحهٔ تشکر Tally) را اسکرین‌شات گرفتی

---

## دو نکتهٔ عملی حساب Free

- **اعتبار:** ۳۱۱ از ۱۰۰۰ باقی مانده. برای عکس و لینک، اجرای تازه لازم نداری؛ اگر برای اسکرین‌شات History را لازم داری، همان اجراهای موجود کافی است.
- **سناریوی دوم:** ۱ از ۲ اسلات فعال آزاد است — برای ماه بعد نگهش دار (رادار ویزا با هش + دروازهٔ انسانی).
