import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../domain/ai_repository.dart';

class AiRepositoryImpl implements AiRepository {
  AiRepositoryImpl(this._api);

  final ApiClient _api;

  @override
  Future<AiAssistResult> assist({
    required String feature,
    required String field,
    required String value,
    AiAssistDetails? details,
  }) async {
    try {
      final res = await _api.dio.post<Map<String, dynamic>>(
        '/ai/assist',
        data: {
          'feature': feature,
          'field': field,
          'value': value,
          if (details != null) 'context': details.toJson(),
        },
      );
      return AiAssistResult.fromJson(res.data!);
    } on DioException catch (e) {
      throw AppFailure.from(e);
    }
  }
}
