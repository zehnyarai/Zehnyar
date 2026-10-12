import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../domain/analysis_entities.dart';
import '../domain/analysis_repository.dart';

class AnalysisRepositoryImpl implements AnalysisRepository {
  AnalysisRepositoryImpl(this._api);

  final ApiClient _api;

  Dio get _dio => _api.dio;

  Future<T> _guard<T>(Future<T> Function() action) async {
    try {
      return await action();
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<AnalysisUsage> usage() => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/analyses/usage');
        return AnalysisUsage.fromJson(res.data!['usage'] as Map<String, dynamic>);
      });

  @override
  Future<AnalysisPage> list({String? cursor, String? farmId, int limit = 20}) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>(
          '/analyses',
          queryParameters: {
            'limit': limit,
            if (cursor != null) 'cursor': cursor,
            if (farmId != null) 'farmId': farmId,
          },
        );
        final items = (res.data!['items'] as List)
            .map((e) => AnalysisSummary.fromJson(e as Map<String, dynamic>))
            .toList();
        return AnalysisPage(items: items, nextCursor: res.data!['nextCursor'] as String?);
      });

  @override
  Future<Analysis> get(String id) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/analyses/$id');
        return Analysis.fromJson(res.data!['analysis'] as Map<String, dynamic>);
      });

  @override
  Future<Analysis> create(NewAnalysisInput input) => _guard(() async {
        final form = FormData.fromMap({
          'category': input.category,
          'season': input.season,
          if (input.farmId != null) 'farmId': input.farmId,
          if (input.treeAgeYears != null) 'treeAgeYears': input.treeAgeYears.toString(),
          if (input.location != null) 'location': input.location,
          if (input.userNotes != null) 'userNotes': input.userNotes,
          'image': await MultipartFile.fromFile(input.filePath, filename: 'pistachio.jpg'),
        });
        final res = await _dio.post<Map<String, dynamic>>(
          '/analyses',
          data: form,
          options: Options(
            sendTimeout: const Duration(seconds: 60),
            receiveTimeout: const Duration(seconds: 120),
          ),
        );
        return Analysis.fromJson(res.data!['analysis'] as Map<String, dynamic>);
      });

  @override
  Future<void> delete(String id) => _guard(() async {
        await _dio.delete<void>('/analyses/$id');
      });
}
