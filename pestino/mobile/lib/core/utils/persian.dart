/// Persian (Shamsi) calendar and digit helpers. No external dependency.
class Persian {
  const Persian._();

  static const _fa = '۰۱۲۳۴۵۶۷۸۹';
  static const _monthsFa = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
  ];

  /// Converts ASCII digits to Persian digits.
  static String digits(Object value) {
    final s = value.toString();
    final buf = StringBuffer();
    for (final ch in s.split('')) {
      final n = int.tryParse(ch);
      buf.write(n == null ? ch : _fa[n]);
    }
    return buf.toString();
  }

  /// Converts Persian/Arabic digits in user input to ASCII (for phone numbers, numeric fields).
  static String toAscii(String input) {
    const arabic = '٠١٢٣٤٥٦٧٨٩';
    final buf = StringBuffer();
    for (final ch in input.split('')) {
      final p = _fa.indexOf(ch);
      final a = arabic.indexOf(ch);
      buf.write(p >= 0 ? '$p' : (a >= 0 ? '$a' : ch));
    }
    return buf.toString();
  }

  /// Gregorian → Jalaali conversion. Returns [year, month, day].
  static List<int> toJalali(DateTime date) {
    final gy = date.year;
    final gm = date.month;
    final gd = date.day;
    const gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
    final gy2 = gm > 2 ? gy + 1 : gy;
    var days = 355666 +
        (365 * gy) +
        ((gy2 + 3) ~/ 4) -
        ((gy2 + 99) ~/ 100) +
        ((gy2 + 399) ~/ 400) +
        gd +
        gdm[gm - 1];
    var jy = -1595 + (33 * (days ~/ 12053));
    days %= 12053;
    jy += 4 * (days ~/ 1461);
    days %= 1461;
    if (days > 365) {
      jy += (days - 1) ~/ 365;
      days = (days - 1) % 365;
    }
    final jm = days < 186 ? 1 + days ~/ 31 : 7 + (days - 186) ~/ 30;
    final jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
    return [jy, jm, jd];
  }

  /// e.g. ۲۰ مهر ۱۴۰۵
  static String dateLong(DateTime date) {
    final j = toJalali(date.toLocal());
    return '${digits(j[2])} ${_monthsFa[j[1] - 1]} ${digits(j[0])}';
  }

  /// e.g. ۲۰ مهر ۱۴۰۵ ، ۱۴:۳۰
  static String dateTime(DateTime date) {
    final local = date.toLocal();
    final hh = local.hour.toString().padLeft(2, '0');
    final mm = local.minute.toString().padLeft(2, '0');
    return '${dateLong(local)} ، ${digits('$hh:$mm')}';
  }

  static String percent(num value) => '${digits(value.round())}٪';

  static String number(num value, {int decimals = 0}) {
    final fixed = decimals == 0 ? value.round().toString() : value.toStringAsFixed(decimals);
    return digits(fixed);
  }

  static String phoneDisplay(String phone) => digits(phone);

  /// Season code → Persian label.
  static String season(String code) => switch (code) {
        'spring' => 'بهار',
        'summer' => 'تابستان',
        'autumn' => 'پاییز',
        'winter' => 'زمستان',
        _ => code,
      };

  static String category(String code) => switch (code) {
        'leaf' => 'برگ',
        'fruit_cluster' => 'خوشه میوه',
        'trunk' => 'تنه / شاخه',
        'pest' => 'آفت',
        'soil' => 'خاک',
        _ => code,
      };

  static String irrigation(String? code) => switch (code) {
        'drip' => 'قطره‌ای',
        'flood' => 'غرقابی',
        'sprinkler' => 'بارانی',
        'micro_sprinkler' => 'میکرو بارانی',
        'rainfed' => 'دیم',
        'other' => 'سایر',
        _ => 'نامشخص',
      };
}
