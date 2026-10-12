import 'package:dio/dio.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/network/api_client.dart';
import '../domain/subscription_entities.dart';
import '../domain/subscription_repository.dart';

class SubscriptionRepositoryImpl implements SubscriptionRepository {
  SubscriptionRepositoryImpl(this._api);

  final ApiClient _api;

  Dio get _dio => _api.dio;

  @override
  Future<List<PlanInfo>> plans() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/subscriptions/plans',
        options: Options(extra: {'public': true}),
      );
      return (res.data!['items'] as List).map((e) => PlanInfo.fromJson(e as Map<String, dynamic>)).toList();
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<PlanInfo> currentPlan() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/subscriptions/me');
      return PlanInfo.fromJson(res.data!['plan'] as Map<String, dynamic>);
    } catch (e) {
      throw AppFailure.from(e);
    }
  }

  @override
  Future<void> checkout(String planCode) async {
    try {
      await _dio.post<void>('/subscriptions/checkout', data: {'plan': planCode});
    } catch (e) {
      throw AppFailure.from(e);
    }
  }
}
