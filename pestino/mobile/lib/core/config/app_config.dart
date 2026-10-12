/// Compile-time configuration. Override per build with:
///   flutter build apk --release --dart-define=API_BASE_URL=https://api.pestino.ir
///
/// The Gemini API key is NEVER part of the app. All AI calls go through the backend.
class AppConfig {
  const AppConfig._();

  static const String appName = 'پستینو';
  static const String appNameEn = 'Pestino';

  /// Android emulator maps 10.0.2.2 to the host machine's localhost.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8080',
  );

  static const String apiPrefix = '/api/v1';

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 90);

  static const String supportPhone = '';
  static const String privacyPolicyUrl = 'https://pestino.ir/privacy';
  static const String termsUrl = 'https://pestino.ir/terms';
}
