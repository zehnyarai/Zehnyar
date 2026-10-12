import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/token_store.dart';
import '../../auth/domain/auth_entities.dart';
import '../domain/admin_entities.dart';
import '../domain/admin_repository.dart';

class AdminRepositoryImpl implements AdminRepository {
  AdminRepositoryImpl({required ApiClient api, required TokenStore tokens})
      : _api = api,
        _tokens = tokens;

  final ApiClient _api;
  final TokenStore _tokens;

  Dio get _dio => _api.dio;

  Future<T> _guard<T>(Future<T> Function() action) async {
    try {
      return await action();
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<AuthUser> login({required String phone, required String password}) => _guard(() async {
        final res = await _dio.post<Map<String, dynamic>>(
          '/admin/auth/login',
          data: {'phone': phone, 'password': password},
          options: Options(extra: {'public': true}),
        );
        final data = res.data!;
        final tokens = data['tokens'] as Map<String, dynamic>;
        await _tokens.save(
          access: tokens['accessToken'] as String,
          refresh: tokens['refreshToken'] as String,
        );
        return AuthUser.fromJson(data['user'] as Map<String, dynamic>);
      });

  @override
  Future<AdminStats> stats() => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/admin/stats');
        return AdminStats.fromJson(res.data!['stats'] as Map<String, dynamic>);
      });

  @override
  Future<AiSettings> aiSettings() => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/admin/ai/settings');
        return AiSettings.fromJson(res.data!['settings'] as Map<String, dynamic>);
      });

  @override
  Future<AiSettings> updateAiSettings({
    String? apiKey,
    bool clearApiKey = false,
    String? defaultModel,
    int? timeoutMs,
    bool? aiEnabled,
  }) =>
      _guard(() async {
        final res = await _dio.put<Map<String, dynamic>>(
          '/admin/ai/settings',
          data: {
            if (apiKey != null) 'apiKey': apiKey,
            if (clearApiKey) 'clearApiKey': true,
            if (defaultModel != null) 'defaultModel': defaultModel,
            if (timeoutMs != null) 'timeoutMs': timeoutMs,
            if (aiEnabled != null) 'aiEnabled': aiEnabled,
          },
        );
        return AiSettings.fromJson(res.data!['settings'] as Map<String, dynamic>);
      });

  @override
  Future<AiConnectionTest> testAi() => _guard(() async {
        final res = await _dio.post<Map<String, dynamic>>('/admin/ai/settings/test');
        return AiConnectionTest.fromJson(res.data!['result'] as Map<String, dynamic>);
      });

  @override
  Future<List<AiFeature>> aiFeatures() => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/admin/ai/features');
        return (res.data!['items'] as List).map((e) => AiFeature.fromJson(e as Map<String, dynamic>)).toList();
      });

  @override
  Future<AiFeature> updateAiFeature(String key, Map<String, dynamic> changes) => _guard(() async {
        final res = await _dio.patch<Map<String, dynamic>>('/admin/ai/features/$key', data: changes);
        return AiFeature.fromJson(res.data!['item'] as Map<String, dynamic>);
      });

  @override
  Future<List<AiUsageRow>> aiUsage({int days = 7}) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/admin/ai/usage', queryParameters: {'days': days});
        return (res.data!['items'] as List).map((e) => AiUsageRow.fromJson(e as Map<String, dynamic>)).toList();
      });

  @override
  Future<List<AdminUser>> users({String query = ''}) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>(
          '/admin/users',
          queryParameters: {if (query.isNotEmpty) 'q': query, 'limit': 50},
        );
        return (res.data!['items'] as List).map((e) => AdminUser.fromJson(e as Map<String, dynamic>)).toList();
      });

  @override
  Future<void> setUserActive(String userId, {required bool active}) => _guard(() async {
        await _dio.patch<Map<String, dynamic>>('/admin/users/$userId', data: {'isActive': active});
      });

  @override
  Future<List<AuditEntry>> audit({int limit = 50}) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/admin/audit', queryParameters: {'limit': limit});
        return (res.data!['items'] as List).map((e) => AuditEntry.fromJson(e as Map<String, dynamic>)).toList();
      });
}
