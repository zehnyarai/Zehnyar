import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../domain/knowledge_entities.dart';
import '../domain/knowledge_repository.dart';

class KnowledgeRepositoryImpl implements KnowledgeRepository {
  KnowledgeRepositoryImpl(this._api);

  final ApiClient _api;

  Dio get _dio => _api.dio;

  @override
  Future<List<KnowledgeSummary>> list({String? kind, String? query}) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/knowledge',
        queryParameters: {
          if (kind != null) 'kind': kind,
          if (query != null && query.isNotEmpty) 'q': query,
        },
      );
      return (res.data!['items'] as List).map((e) => KnowledgeSummary.fromJson(e as Map<String, dynamic>)).toList();
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<KnowledgeArticle> get(String slug) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/knowledge/$slug');
      return KnowledgeArticle.fromJson(res.data!['article'] as Map<String, dynamic>);
    } catch (e) {
      throw AppFailure.from(e);
    }
  }
}
