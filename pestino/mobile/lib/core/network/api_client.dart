import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../storage/token_store.dart';

/// Authenticated HTTP client for the Pestino API.
///
/// - Attaches the access token to every request.
/// - On HTTP 401 it rotates the refresh token exactly once (concurrent requests share one refresh).
/// - If the refresh fails, the session is cleared and [onSessionExpired] is fired so the UI can
///   route the user back to login.
class ApiClient {
  ApiClient({
    required TokenStore tokens,
    required void Function() onSessionExpired,
    String baseUrl = AppConfig.apiBaseUrl,
    Dio? dio,
    Dio? refreshDio,
  })  : _tokens = tokens,
        _onSessionExpired = onSessionExpired,
        _baseUrl = '$baseUrl${AppConfig.apiPrefix}',
        dio = dio ?? Dio(_options('$baseUrl${AppConfig.apiPrefix}')),
        _refreshDio = refreshDio ?? Dio(_options('$baseUrl${AppConfig.apiPrefix}')) {
    this.dio.interceptors.add(InterceptorsWrapper(onRequest: _onRequest, onError: _onError));
  }

  final TokenStore _tokens;
  final void Function() _onSessionExpired;
  final String _baseUrl;
  final Dio _refreshDio;

  /// The main client. Use this for all authenticated requests.
  final Dio dio;

  Future<bool>? _refreshing;

  static BaseOptions _options(String baseUrl) => BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        sendTimeout: AppConfig.receiveTimeout,
        headers: {'Accept': 'application/json'},
        responseType: ResponseType.json,
      );

  String get baseUrl => _baseUrl;

  Future<void> _onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    if (options.extra['public'] != true) {
      final token = await _tokens.readAccess();
      if (token != null) options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _onError(DioException err, ErrorInterceptorHandler handler) async {
    final req = err.requestOptions;
    final code = _errorCode(err);
    final isAuthFailure = err.response?.statusCode == 401 && req.extra['public'] != true;
    final alreadyRetried = req.extra['retried'] == true;
    final isRefreshCall = req.path.endsWith('/auth/refresh');

    if (!isAuthFailure || alreadyRetried || isRefreshCall || code == 'REFRESH_REUSED') {
      if (isRefreshCall && isAuthFailure) _onSessionExpired();
      return handler.next(err);
    }

    final refreshed = await _refreshOnce();
    if (!refreshed) {
      await _tokens.clear();
      _onSessionExpired();
      return handler.next(err);
    }

    try {
      req.extra['retried'] = true;
      req.headers['Authorization'] = 'Bearer ${await _tokens.readAccess()}';
      final response = await dio.fetch<dynamic>(req);
      handler.resolve(response);
    } on DioException catch (retryErr) {
      handler.next(retryErr);
    }
  }

  /// Ensures only one refresh request runs at a time.
  Future<bool> _refreshOnce() {
    return _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);
  }

  Future<bool> _doRefresh() async {
    final refresh = await _tokens.readRefresh();
    if (refresh == null || refresh.isEmpty) return false;
    try {
      final res = await _refreshDio.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refreshToken': refresh},
        options: Options(extra: {'public': true}),
      );
      final tokens = (res.data?['tokens'] as Map?)?.cast<String, dynamic>();
      final access = tokens?['accessToken'] as String?;
      final newRefresh = tokens?['refreshToken'] as String?;
      if (access == null || newRefresh == null) return false;
      await _tokens.save(access: access, refresh: newRefresh);
      return true;
    } on DioException {
      return false;
    }
  }

  static String? _errorCode(DioException err) {
    final data = err.response?.data;
    if (data is Map && data['error'] is Map) return (data['error'] as Map)['code'] as String?;
    return null;
  }
}
