import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../domain/farm_entities.dart';
import '../domain/farm_repository.dart';

class FarmRepositoryImpl implements FarmRepository {
  FarmRepositoryImpl(this._api);

  final ApiClient _api;

  Dio get _dio => _api.dio;

  /// Runs [action] and converts any Dio error into an [AppFailure].
  Future<T> _guard<T>(Future<T> Function() action) async {
    try {
      return await action();
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<List<Farm>> list() => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/farms');
        return (res.data!['items'] as List).map((e) => Farm.fromJson(e as Map<String, dynamic>)).toList();
      });

  @override
  Future<Farm> get(String id) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/farms/$id');
        return Farm.fromJson(res.data!['farm'] as Map<String, dynamic>);
      });

  @override
  Future<Farm> create(FarmInput input) => _guard(() async {
        final res = await _dio.post<Map<String, dynamic>>('/farms', data: input.toJson());
        return Farm.fromJson(res.data!['farm'] as Map<String, dynamic>);
      });

  @override
  Future<Farm> update(String id, FarmInput input) => _guard(() async {
        final res = await _dio.patch<Map<String, dynamic>>('/farms/$id', data: input.toJson());
        return Farm.fromJson(res.data!['farm'] as Map<String, dynamic>);
      });

  @override
  Future<void> delete(String id) => _guard(() async {
        await _dio.delete<void>('/farms/$id');
      });

  @override
  Future<List<Tree>> trees(String farmId) => _guard(() async {
        final res = await _dio.get<Map<String, dynamic>>('/farms/$farmId/trees');
        return (res.data!['items'] as List).map((e) => Tree.fromJson(e as Map<String, dynamic>)).toList();
      });

  @override
  Future<Tree> addTree(String farmId, {required String label, int? plantedYear, String? variety}) => _guard(() async {
        final res = await _dio.post<Map<String, dynamic>>(
          '/farms/$farmId/trees',
          data: {'label': label, 'plantedYear': plantedYear, 'variety': variety},
        );
        return Tree.fromJson(res.data!['tree'] as Map<String, dynamic>);
      });

  @override
  Future<void> removeTree(String farmId, String treeId) => _guard(() async {
        await _dio.delete<void>('/farms/$farmId/trees/$treeId');
      });
}
