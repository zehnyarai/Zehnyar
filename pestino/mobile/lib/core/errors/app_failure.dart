import 'package:dio/dio.dart';

/// Domain-friendly failure. Presentation layers show `message` (Persian) to users.
class AppFailure implements Exception {
  const AppFailure({
    required this.code,
    required this.message,
    this.statusCode,
    this.details,
  });

  final String code;
  final String message;
  final int? statusCode;
  final Object? details;

  bool get isNetwork => code == 'NETWORK_ERROR' || code == 'TIMEOUT';
  bool get isUnauthorized => statusCode == 401;

  static const _messages = <String, String>{
    'NETWORK_ERROR': 'اتصال به اینترنت برقرار نیست. لطفاً اتصال خود را بررسی کنید.',
    'TIMEOUT': 'پاسخ سرور دیر رسید. دوباره تلاش کنید.',
    'INVALID_PHONE': 'شماره موبایل معتبر نیست. نمونه درست: ۰۹۱۲۱۲۳۴۵۶۷',
    'OTP_INVALID': 'کد وارد شده صحیح نیست.',
    'OTP_EXPIRED': 'کد منقضی شده است. کد جدید درخواست کنید.',
    'OTP_COOLDOWN': 'لطفاً کمی صبر کنید و سپس کد جدید بگیرید.',
    'OTP_HOURLY_LIMIT': 'تعداد درخواست کد برای این شماره زیاد است. بعداً تلاش کنید.',
    'OTP_TOO_MANY_ATTEMPTS': 'تلاش‌های ناموفق زیاد بود. کد جدید درخواست کنید.',
    'TOKEN_INVALID': 'نشست شما منقضی شده است. دوباره وارد شوید.',
    'REFRESH_REUSED': 'نشست شما نامعتبر شد. دوباره وارد شوید.',
    'REFRESH_EXPIRED': 'نشست شما منقضی شده است. دوباره وارد شوید.',
    'REFRESH_INVALID': 'نشست شما نامعتبر است. دوباره وارد شوید.',
    'QUOTA_EXCEEDED': 'سهمیه تحلیل ماهانه شما تمام شده است. برای ادامه، طرح حرفه‌ای را فعال کنید.',
    'FARM_LIMIT_REACHED': 'حداکثر تعداد باغ در طرح شما تکمیل شده است.',
    'UNSUPPORTED_IMAGE': 'فقط تصاویر JPEG، PNG یا WEBP پذیرفته می‌شود.',
    'UPLOAD_LIMIT_FILE_SIZE': 'حجم تصویر بیش از حد مجاز است.',
    'PAYLOAD_TOO_LARGE': 'حجم تصویر بیش از حد مجاز است.',
    'ANALYZE_RATE_LIMIT': 'تحلیل‌های زیادی در زمان کوتاه انجام شده. چند دقیقه دیگر تلاش کنید.',
    'RATE_LIMITED': 'درخواست‌های زیادی ارسال شده است. کمی صبر کنید.',
    'AI_UPSTREAM_ERROR': 'سرویس هوش مصنوعی موقتاً در دسترس نیست. دوباره تلاش کنید.',
    'AI_INVALID_OUTPUT': 'پاسخ تحلیل قابل پردازش نبود. دوباره تلاش کنید.',
    'AI_BLOCKED': 'این تصویر قابل تحلیل نیست. تصویر دیگری ارسال کنید.',
    'PAYMENT_NOT_CONFIGURED': 'خرید درون‌برنامه‌ای به‌زودی فعال می‌شود.',
    'VALIDATION_FAILED': 'اطلاعات واردشده کامل یا معتبر نیست.',
    'INTERNAL_ERROR': 'خطای غیرمنتظره‌ای رخ داد. لطفاً دوباره تلاش کنید.',
  };

  /// Converts any thrown error into an [AppFailure] with a Persian message.
  static AppFailure from(Object error) {
    if (error is AppFailure) return error;
    if (error is DioException) return fromDio(error);
    return const AppFailure(code: 'UNKNOWN', message: 'خطای غیرمنتظره‌ای رخ داد.');
  }

  static AppFailure fromDio(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout) {
      return const AppFailure(code: 'TIMEOUT', message: 'پاسخ سرور دیر رسید. دوباره تلاش کنید.');
    }
    final status = e.response?.statusCode;
    final data = e.response?.data;
    if (data is Map && data['error'] is Map) {
      final err = data['error'] as Map;
      final code = (err['code'] as String?) ?? 'UNKNOWN';
      return AppFailure(
        code: code,
        message: _messages[code] ?? (err['message'] as String?) ?? 'خطا در ارتباط با سرور',
        statusCode: status,
        details: err['details'],
      );
    }
    if (e.type == DioExceptionType.connectionError || status == null) {
      return const AppFailure(code: 'NETWORK_ERROR', message: 'اتصال به اینترنت برقرار نیست. لطفاً اتصال خود را بررسی کنید.');
    }
    return AppFailure(code: 'HTTP_$status', message: _messages['INTERNAL_ERROR']!, statusCode: status);
  }

  @override
  String toString() => 'AppFailure($code, $statusCode): $message';
}
