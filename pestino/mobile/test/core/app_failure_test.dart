import 'package:flutter_test/flutter_test.dart';
import 'package:pestino/core/errors/app_failure.dart';

void main() {
  test('AppFailure passes through unchanged', () {
    const f = AppFailure(code: 'QUOTA_EXCEEDED', message: 'x');
    expect(identical(AppFailure.from(f), f), isTrue);
  });

  test('unknown errors become a generic Persian message', () {
    final f = AppFailure.from(StateError('boom'));
    expect(f.code, 'UNKNOWN');
    expect(f.message, isNotEmpty);
  });
}
