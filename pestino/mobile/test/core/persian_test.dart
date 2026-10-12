import 'package:flutter_test/flutter_test.dart';
import 'package:pestino/core/utils/persian.dart';

void main() {
  group('Jalali calendar', () {
    // Reference values cross-checked against an independent Jalali implementation.
    test('Nowruz dates', () {
      expect(Persian.toJalali(DateTime(2024, 3, 20)), [1403, 1, 1]);
      expect(Persian.toJalali(DateTime(2025, 3, 21)), [1404, 1, 1]);
      expect(Persian.toJalali(DateTime(2026, 3, 21)), [1405, 1, 1]);
      expect(Persian.toJalali(DateTime(2000, 3, 20)), [1379, 1, 1]);
    });

    test('mid-year and year-end dates', () {
      expect(Persian.toJalali(DateTime(2026, 10, 12)), [1405, 7, 20]);
      expect(Persian.toJalali(DateTime(2025, 12, 31)), [1404, 10, 10]);
    });

    test('long date is formatted in Persian', () {
      expect(Persian.dateLong(DateTime(2026, 10, 12)), '۲۰ مهر ۱۴۰۵');
    });
  });

  group('digits and labels', () {
    test('ASCII to Persian digits', () {
      expect(Persian.digits(1405), '۱۴۰۵');
      expect(Persian.digits(0), '۰');
    });

    test('Persian and Arabic digits to ASCII', () {
      expect(Persian.toAscii('۰۹۱۲'), '0912');
      expect(Persian.toAscii('٠٩١٢'), '0912');
    });

    test('percent rounds and uses Persian digits', () {
      expect(Persian.percent(78), '۷۸٪');
      expect(Persian.percent(77.6), '۷۸٪');
    });

    test('season and category labels', () {
      expect(Persian.season('autumn'), 'پاییز');
      expect(Persian.category('fruit_cluster'), 'خوشه میوه');
      expect(Persian.category('unknown_code'), 'unknown_code');
    });
  });
}
