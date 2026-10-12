import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/token_store.dart';
import '../../../core/utils/persian.dart';
import '../domain/auth_entities.dart';
import '../domain/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl({required ApiClient api, required TokenStore tokens})
      : _api = api,
        _tokens = tokens;

  final ApiClient _api;
  final TokenStore _tokens;

  Dio get _dio => _api.dio;

  @override
  Future<OtpChallenge> requestOtp(String phone) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/auth/otp/request',
        data: {'phone': _normalize(phone)},
        options: Options(extra: {'public': true}),
      );
      return OtpChallenge.fromJson(res.data ?? const {});
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<({AuthUser user, bool isNewUser})> verifyOtp({required String phone, required String code}) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/auth/otp/verify',
        data: {'phone': _normalize(phone), 'code': Persian.toAscii(code)},
        options: Options(extra: {'public': true}),
      );
      final data = res.data!;
      final tokens = data['tokens'] as Map<String, dynamic>;
      await _tokens.save(
        access: tokens['accessToken'] as String,
        refresh: tokens['refreshToken'] as String,
      );
      return (
        user: AuthUser.fromJson(data['user'] as Map<String, dynamic>),
        isNewUser: data['isNewUser'] as bool? ?? false,
      );
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<AuthUser?> restoreSession() async {
    final access = await _tokens.readAccess();
    final refresh = await _tokens.readRefresh();
    if (access == null && refresh == null) return null;
    try {
      final res = await _dio.get<Map<String, dynamic>>('/me');
      return AuthUser.fromJson(res.data!['user'] as Map<String, dynamic>);
    } catch (e) {
      final failure = AppFailure.from(e);
      if (failure.isUnauthorized) {
        await _tokens.clear();
        return null;
      }
      rethrow;
    }
  }

  @override
  Future<AuthUser> updateProfile({String? fullName, String? province, String? city}) async {
    try {
      final body = <String, dynamic>{
        if (fullName != null) 'fullName': fullName,
        if (province != null) 'province': province,
        if (city != null) 'city': city,
      };
      final res = await _dio.patch<Map<String, dynamic>>('/me', data: body);
      return AuthUser.fromJson(res.data!['user'] as Map<String, dynamic>);
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<void> logout() async {
    final refresh = await _tokens.readRefresh();
    try {
      if (refresh != null) {
        await _dio.post<void>('/auth/logout', data: {'refreshToken': refresh}, options: Options(extra: {'public': true}));
      }
    } catch (_) {
      // Logout must succeed locally even when offline.
    } finally {
      await _tokens.clear();
    }
  }

  static String _normalize(String phone) => Persian.toAscii(phone).replaceAll(RegExp(r'[\s\-]'), '');
}
